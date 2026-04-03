"""Blog routes."""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import current_user

from app import db
from app.models.blog import Post, Category, Comment, Newsletter, ContactMessage
from app.models.store import Product
from app.blueprints.blog.forms import CommentForm, ContactForm, NewsletterForm

blog_bp = Blueprint("blog", __name__, template_folder="../../templates")


@blog_bp.route("/")
def index():
    """Home page with featured posts and products."""
    featured_posts = (
        Post.query.filter_by(is_published=True, is_featured=True)
        .order_by(Post.published_at.desc())
        .limit(3)
        .all()
    )
    latest_posts = (
        Post.query.filter_by(is_published=True)
        .order_by(Post.published_at.desc())
        .limit(6)
        .all()
    )
    featured_products = (
        Product.query.filter_by(is_active=True, is_featured=True).limit(4).all()
    )
    categories = Category.query.all()
    return render_template(
        "blog/index.html",
        featured_posts=featured_posts,
        latest_posts=latest_posts,
        featured_products=featured_products,
        categories=categories,
    )


@blog_bp.route("/blog")
def blog_list():
    """Blog listing with pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("POSTS_PER_PAGE", 6)
    category_slug = request.args.get("category", None)
    search_query = request.args.get("q", None)

    query = Post.query.filter_by(is_published=True)

    if category_slug:
        query = query.join(Post.categories).filter(Category.slug == category_slug)

    if search_query:
        query = query.filter(
            db.or_(
                Post.title.ilike(f"%{search_query}%"),
                Post.content.ilike(f"%{search_query}%"),
            )
        )

    pagination = query.order_by(Post.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    categories = Category.query.all()
    sidebar_products = (
        Product.query.filter_by(is_active=True, is_featured=True).limit(3).all()
    )

    return render_template(
        "blog/blog_list.html",
        posts=pagination.items,
        pagination=pagination,
        categories=categories,
        sidebar_products=sidebar_products,
        current_category=category_slug,
        search_query=search_query,
    )


@blog_bp.route("/post/<slug>", methods=["GET", "POST"])
def post_detail(slug):
    """Single blog post with comments and product suggestions."""
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
    post.increment_views()

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            body=form.body.data,
            author_name=form.author_name.data,
            author_email=form.author_email.data,
            post_id=post.id,
            user_id=current_user.id if current_user.is_authenticated else None,
        )
        db.session.add(comment)
        db.session.commit()
        flash("Comment submitted for review!", "success")
        return redirect(url_for("blog.post_detail", slug=slug))

    comments = (
        Comment.query.filter_by(post_id=post.id, is_approved=True)
        .order_by(Comment.created_at.desc())
        .all()
    )

    # Related posts
    related_posts = (
        Post.query.filter(Post.id != post.id, Post.is_published.is_(True))
        .order_by(db.func.random())
        .limit(3)
        .all()
    )

    # Product suggestions for ads
    suggested_products = (
        Product.query.filter_by(is_active=True)
        .order_by(db.func.random())
        .limit(4)
        .all()
    )

    return render_template(
        "blog/post_detail.html",
        post=post,
        form=form,
        comments=comments,
        related_posts=related_posts,
        suggested_products=suggested_products,
    )


@blog_bp.route("/category/<slug>")
def category(slug):
    """Posts filtered by category."""
    cat = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("POSTS_PER_PAGE", 6)

    pagination = (
        Post.query.filter(Post.is_published.is_(True))
        .join(Post.categories)
        .filter(Category.id == cat.id)
        .order_by(Post.published_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template(
        "blog/category.html",
        category=cat,
        posts=pagination.items,
        pagination=pagination,
    )


@blog_bp.route("/about")
def about():
    """About us page."""
    return render_template("blog/about.html")


@blog_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact us page."""
    form = ContactForm()
    if form.validate_on_submit():
        message = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            reason=form.reason.data or "General Question",
            message=form.message.data,
        )
        db.session.add(message)
        db.session.commit()
        flash("Message sent! We'll get back to you soon.", "success")
        return redirect(url_for("blog.contact"))
    return render_template("blog/contact.html", form=form)


@blog_bp.route("/newsletter", methods=["POST"])
def newsletter_subscribe():
    """Newsletter subscription."""
    form = NewsletterForm()
    if form.validate_on_submit():
        existing = Newsletter.query.filter_by(email=form.email.data).first()
        if existing:
            flash("You're already subscribed!", "info")
        else:
            subscriber = Newsletter(email=form.email.data)
            db.session.add(subscriber)
            db.session.commit()
            flash("Subscribed! Welcome to the tribe. ✌️", "success")
    else:
        flash("Please enter a valid email.", "danger")
    return redirect(request.referrer or url_for("blog.index"))
