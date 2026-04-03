"""Store routes."""

import uuid

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

from app import db
from app.models.store import Product, Category, CartItem, Order, OrderItem
from app.models.user import Address
from app.blueprints.store.forms import CheckoutForm
from app.utils.payfast import get_payfast_url, build_payment_data, generate_signature

store_bp = Blueprint("store", __name__, template_folder="../../templates/store")


@store_bp.route("/")
def shop():
    """Main store page."""
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("PRODUCTS_PER_PAGE", 12)
    category_slug = request.args.get("category", None)
    sort_by = request.args.get("sort", "newest")
    search_query = request.args.get("q", None)

    query = Product.query.filter_by(is_active=True)

    if category_slug:
        query = query.join(Category).filter(Category.slug == category_slug)

    if search_query:
        query = query.filter(
            db.or_(
                Product.name.ilike(f"%{search_query}%"),
                Product.description.ilike(f"%{search_query}%"),
            )
        )

    if sort_by == "price_low":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_high":
        query = query.order_by(Product.price.desc())
    elif sort_by == "name":
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.all()

    return render_template(
        "store/shop.html",
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        current_category=category_slug,
        sort_by=sort_by,
        search_query=search_query,
    )


@store_bp.route("/product/<slug>")
def product_detail(slug):
    """Single product page."""
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = (
        Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.is_active.is_(True),
        )
        .limit(4)
        .all()
    )
    return render_template(
        "store/product_detail.html", product=product, related_products=related
    )


@store_bp.route("/cart")
@login_required
def cart():
    """Shopping cart page."""
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.subtotal for item in items)
    return render_template("store/cart.html", items=items, total=total)


@store_bp.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    """Add item to cart."""
    product = Product.query.get_or_404(product_id)
    quantity = request.form.get("quantity", 1, type=int)

    if quantity < 1:
        quantity = 1

    if not product.in_stock:
        flash("Sorry, this product is out of stock.", "warning")
        return redirect(url_for("store.product_detail", slug=product.slug))

    existing = CartItem.query.filter_by(
        user_id=current_user.id, product_id=product_id
    ).first()

    if existing:
        existing.quantity += quantity
    else:
        item = CartItem(
            user_id=current_user.id, product_id=product_id, quantity=quantity
        )
        db.session.add(item)

    db.session.commit()
    flash(f"{product.name} added to cart!", "success")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
        return jsonify({"success": True, "cart_count": cart_count})

    return redirect(request.referrer or url_for("store.shop"))


@store_bp.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def update_cart(item_id):
    """Update cart item quantity."""
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("store.cart"))

    quantity = request.form.get("quantity", 1, type=int)
    if quantity < 1:
        db.session.delete(item)
    else:
        item.quantity = quantity
    db.session.commit()
    flash("Cart updated.", "success")
    return redirect(url_for("store.cart"))


@store_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_from_cart(item_id):
    """Remove item from cart."""
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("store.cart"))
    db.session.delete(item)
    db.session.commit()
    flash("Item removed from cart.", "info")
    return redirect(url_for("store.cart"))


@store_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """Checkout page with PayFast integration."""
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("store.shop"))

    user_addresses = Address.query.filter_by(user_id=current_user.id).all()
    form = CheckoutForm()
    form.shipping_address.choices = [
        (a.id, f"{a.label}: {a.street}, {a.city}")
        for a in user_addresses
    ]

    if not user_addresses:
        flash("Please add a shipping address first.", "info")
        return redirect(url_for("auth.add_address"))

    subtotal = sum(item.subtotal for item in items)
    shipping = 99.00 if subtotal < 500 else 0.0
    total = subtotal + shipping

    if form.validate_on_submit():
        address = Address.query.get(form.shipping_address.data)
        address_str = (
            f"{address.street}, {address.city}, "
            f"{address.province}, {address.postal_code}, {address.country}"
        )

        order = Order(
            order_number=f"CH-{uuid.uuid4().hex[:8].upper()}",
            user_id=current_user.id,
            subtotal=subtotal,
            shipping_cost=shipping,
            total=total,
            shipping_address=address_str,
            notes=form.notes.data or "",
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product.name,
                product_price=item.product.current_price,
                quantity=item.quantity,
                subtotal=item.subtotal,
            )
            db.session.add(order_item)
            # Decrease stock
            item.product.stock = max(0, item.product.stock - item.quantity)

        # Clear cart
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        # Build PayFast payment data
        payment_data = build_payment_data(
            order,
            return_url=url_for("store.order_success", order_id=order.id, _external=True),
            cancel_url=url_for("store.order_cancelled", order_id=order.id, _external=True),
            notify_url=url_for("api.payfast_notify", _external=True),
        )
        payment_data["signature"] = generate_signature(payment_data)

        return render_template(
            "store/payfast_redirect.html",
            payment_data=payment_data,
            payfast_url=get_payfast_url(),
            order=order,
        )

    return render_template(
        "store/checkout.html",
        form=form,
        items=items,
        subtotal=subtotal,
        shipping=shipping,
        total=total,
    )


@store_bp.route("/order/success/<int:order_id>")
@login_required
def order_success(order_id):
    """Order success page after PayFast payment."""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("store.shop"))
    return render_template("store/order_success.html", order=order)


@store_bp.route("/order/cancelled/<int:order_id>")
@login_required
def order_cancelled(order_id):
    """Order cancelled page."""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("store.shop"))
    order.status = "cancelled"
    db.session.commit()
    flash("Order was cancelled.", "warning")
    return redirect(url_for("store.orders"))


@store_bp.route("/orders")
@login_required
def orders():
    """User's past orders."""
    user_orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("store/orders.html", orders=user_orders)


@store_bp.route("/order/<int:order_id>")
@login_required
def order_detail(order_id):
    """Single order detail."""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized.", "danger")
        return redirect(url_for("store.orders"))
    return render_template("store/order_detail.html", order=order)
