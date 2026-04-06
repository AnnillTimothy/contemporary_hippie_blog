"""Admin dashboard routes."""

import os
import re

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    jsonify,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models.user import User
from app.models.blog import Post, Category, Tag, Comment, Newsletter, ContactMessage
from app.models.store import (
    Product,
    Category as ProductCategory,
    Order,
)
from app.blueprints.blog.forms import PostForm, AIGenerateForm
from app.blueprints.store.forms import ProductForm
from app.utils.decorators import admin_required
from app.utils.ai import generate_article, generate_images

admin_bp = Blueprint("admin", __name__, template_folder="../../templates/admin")


def _save_upload(file_obj, subfolder="posts"):
    """Save an uploaded file and return relative path."""
    if not file_obj or not file_obj.filename:
        return ""
    filename = secure_filename(file_obj.filename)
    upload_dir = os.path.join(current_app.static_folder, "uploads", subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file_obj.save(filepath)
    return f"uploads/{subfolder}/{filename}"


def _slugify(text):
    """Create a URL-safe slug from text."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


# ─── Dashboard ────────────────────────────────────────


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    """Admin dashboard overview."""
    stats = {
        "total_posts": Post.query.count(),
        "published_posts": Post.query.filter_by(is_published=True).count(),
        "total_products": Product.query.count(),
        "total_orders": Order.query.count(),
        "pending_orders": Order.query.filter_by(status="pending").count(),
        "total_users": User.query.count(),
        "total_subscribers": Newsletter.query.filter_by(is_active=True).count(),
        "unread_messages": ContactMessage.query.filter_by(is_read=False).count(),
        "pending_comments": Comment.query.filter_by(is_approved=False).count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_orders=recent_orders,
        recent_posts=recent_posts,
    )


# ─── Blog Posts ───────────────────────────────────────


@admin_bp.route("/posts")
@login_required
@admin_required
def posts():
    """List all blog posts."""
    page = request.args.get("page", 1, type=int)
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template("admin/posts.html", posts=pagination.items, pagination=pagination)


@admin_bp.route("/posts/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_post():
    """Create a new blog post."""
    form = PostForm()
    form.categories.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        slug = _slugify(form.title.data)
        # Ensure unique slug
        existing = Post.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{Post.query.count() + 1}"

        post = Post(
            title=form.title.data,
            slug=slug,
            excerpt=form.excerpt.data or "",
            content=form.content.data,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data,
            meta_description=form.meta_description.data or "",
            author_id=current_user.id,
        )
        if form.is_published.data:
            post.publish()

        # Handle image upload
        if form.featured_image.data:
            post.featured_image = _save_upload(form.featured_image.data)

        # Handle categories
        selected_cats = Category.query.filter(
            Category.id.in_(form.categories.data)
        ).all()
        post.categories = selected_cats

        db.session.add(post)
        db.session.commit()
        flash("Post created!", "success")
        return redirect(url_for("admin.posts"))
    return render_template("admin/post_form.html", form=form, title="New Post")


@admin_bp.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_post(post_id):
    """Edit an existing blog post."""
    post = Post.query.get_or_404(post_id)
    form = PostForm(obj=post)
    form.categories.choices = [(c.id, c.name) for c in Category.query.all()]

    if request.method == "GET":
        form.categories.data = [c.id for c in post.categories]

    if form.validate_on_submit():
        post.title = form.title.data
        post.excerpt = form.excerpt.data or ""
        post.content = form.content.data
        post.is_featured = form.is_featured.data
        post.meta_description = form.meta_description.data or ""

        if form.is_published.data and not post.is_published:
            post.publish()
        post.is_published = form.is_published.data

        if form.featured_image.data:
            post.featured_image = _save_upload(form.featured_image.data)

        selected_cats = Category.query.filter(
            Category.id.in_(form.categories.data)
        ).all()
        post.categories = selected_cats

        db.session.commit()
        flash("Post updated!", "success")
        return redirect(url_for("admin.posts"))
    return render_template("admin/post_form.html", form=form, title="Edit Post", post=post)


@admin_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_post(post_id):
    """Delete a blog post."""
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("admin.posts"))


# ─── AI Content Generation ────────────────────────────


@admin_bp.route("/ai-generate", methods=["GET", "POST"])
@login_required
@admin_required
def ai_generate():
    """Generate a blog post using AI."""
    form = AIGenerateForm()
    article_data = None

    if form.validate_on_submit():
        try:
            article_data = generate_article(form.prompt.data)

            # Generate images if requested
            images = []
            if form.generate_images.data:
                try:
                    images = generate_images(form.prompt.data, count=3)
                except Exception as img_err:
                    flash(f"Image generation failed: {img_err}", "warning")

            article_data["images"] = images
            flash("Article generated! Review and publish below.", "success")
        except Exception as e:
            flash(f"AI generation failed: {e}", "danger")

    return render_template(
        "admin/ai_generate.html", form=form, article_data=article_data
    )


@admin_bp.route("/ai-publish", methods=["POST"])
@login_required
@admin_required
def ai_publish():
    """Publish an AI-generated article."""
    title = request.form.get("title", "")
    content = request.form.get("content", "")
    excerpt = request.form.get("excerpt", "")
    meta_desc = request.form.get("meta_description", "")
    tags_str = request.form.get("tags", "")
    reading_time = request.form.get("reading_time", 5, type=int)
    image_1 = request.form.get("image_1", "")
    image_2 = request.form.get("image_2", "")
    image_3 = request.form.get("image_3", "")

    if not title or not content:
        flash("Title and content are required.", "danger")
        return redirect(url_for("admin.ai_generate"))

    slug = _slugify(title)
    existing = Post.query.filter_by(slug=slug).first()
    if existing:
        slug = f"{slug}-{Post.query.count() + 1}"

    post = Post(
        title=title,
        slug=slug,
        excerpt=excerpt,
        content=content,
        featured_image=image_1,
        image_2=image_2,
        image_3=image_3,
        is_published=True,
        is_ai_generated=True,
        meta_description=meta_desc,
        reading_time=reading_time,
        author_id=current_user.id,
    )
    post.publish()

    # Handle tags
    if tags_str:
        for tag_name in tags_str.split(","):
            tag_name = tag_name.strip()
            if tag_name:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                post.tags.append(tag)

    db.session.add(post)
    db.session.commit()
    flash("AI article published!", "success")
    return redirect(url_for("admin.posts"))


# ─── Products ─────────────────────────────────────────


@admin_bp.route("/products")
@login_required
@admin_required
def products():
    """List all products."""
    page = request.args.get("page", 1, type=int)
    pagination = Product.query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template(
        "admin/products.html", products=pagination.items, pagination=pagination
    )


@admin_bp.route("/products/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_product():
    """Create a new product."""
    form = ProductForm()
    form.category_id.choices = [
        (c.id, c.name) for c in ProductCategory.query.all()
    ]
    if form.validate_on_submit():
        slug = _slugify(form.name.data)
        existing = Product.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{Product.query.count() + 1}"

        product = Product(
            name=form.name.data,
            slug=slug,
            description=form.description.data,
            short_description=form.short_description.data or "",
            price=form.price.data,
            sale_price=form.sale_price.data,
            sku=form.sku.data or None,
            stock=form.stock.data,
            category_id=form.category_id.data,
            is_active=form.is_active.data,
            is_featured=form.is_featured.data,
        )
        if form.image.data:
            product.image = _save_upload(form.image.data, "products")

        db.session.add(product)
        db.session.commit()
        flash("Product created!", "success")
        return redirect(url_for("admin.products"))
    return render_template("admin/product_form.html", form=form, title="New Product")


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_product(product_id):
    """Edit a product."""
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [
        (c.id, c.name) for c in ProductCategory.query.all()
    ]
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.short_description = form.short_description.data or ""
        product.price = form.price.data
        product.sale_price = form.sale_price.data
        product.sku = form.sku.data or None
        product.stock = form.stock.data
        product.category_id = form.category_id.data
        product.is_active = form.is_active.data
        product.is_featured = form.is_featured.data

        if form.image.data:
            product.image = _save_upload(form.image.data, "products")

        db.session.commit()
        flash("Product updated!", "success")
        return redirect(url_for("admin.products"))
    return render_template(
        "admin/product_form.html", form=form, title="Edit Product", product=product
    )


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_product(product_id):
    """Delete a product."""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "info")
    return redirect(url_for("admin.products"))


# ─── Orders ───────────────────────────────────────────


@admin_bp.route("/orders")
@login_required
@admin_required
def orders():
    """List all orders."""
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", None)
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template(
        "admin/orders.html", orders=pagination.items, pagination=pagination, status=status
    )


@admin_bp.route("/orders/<int:order_id>")
@login_required
@admin_required
def order_detail(order_id):
    """View order details."""
    order = Order.query.get_or_404(order_id)
    return render_template("admin/order_detail.html", order=order)


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
@admin_required
def update_order_status(order_id):
    """Update order status."""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", "pending")
    order.status = new_status
    db.session.commit()
    flash(f"Order #{order.order_number} status updated to {new_status}.", "success")
    return redirect(url_for("admin.order_detail", order_id=order.id))


# ─── Comments ─────────────────────────────────────────


@admin_bp.route("/comments")
@login_required
@admin_required
def comments():
    """List all comments."""
    pending = Comment.query.filter_by(is_approved=False).order_by(
        Comment.created_at.desc()
    ).all()
    approved = Comment.query.filter_by(is_approved=True).order_by(
        Comment.created_at.desc()
    ).limit(50).all()
    return render_template(
        "admin/comments.html", pending=pending, approved=approved
    )


@admin_bp.route("/comments/<int:comment_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_comment(comment_id):
    """Approve a comment."""
    comment = Comment.query.get_or_404(comment_id)
    comment.is_approved = True
    db.session.commit()
    flash("Comment approved.", "success")
    return redirect(url_for("admin.comments"))


@admin_bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_comment(comment_id):
    """Delete a comment."""
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", "info")
    return redirect(url_for("admin.comments"))


# ─── Messages ─────────────────────────────────────────


@admin_bp.route("/messages")
@login_required
@admin_required
def messages():
    """List contact messages."""
    msgs = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin/messages.html", messages=msgs)


@admin_bp.route("/messages/<int:message_id>/read", methods=["POST"])
@login_required
@admin_required
def mark_message_read(message_id):
    """Mark a message as read."""
    msg = ContactMessage.query.get_or_404(message_id)
    msg.is_read = True
    db.session.commit()
    return jsonify({"success": True})


# ─── Users ────────────────────────────────────────────


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    """List all users."""
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


# ─── Subscribers ──────────────────────────────────────


@admin_bp.route("/subscribers")
@login_required
@admin_required
def subscribers():
    """List newsletter subscribers."""
    subs = Newsletter.query.order_by(Newsletter.subscribed_at.desc()).all()
    return render_template("admin/subscribers.html", subscribers=subs)
