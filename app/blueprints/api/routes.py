"""API routes for AJAX calls and PayFast notifications."""

import logging

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFProtect

from app import db, csrf
from app.models.store import Order

api_bp = Blueprint("api", __name__)
logger = logging.getLogger(__name__)


@api_bp.route("/payfast/notify", methods=["POST"])
@csrf.exempt
def payfast_notify():
    """Handle PayFast ITN (Instant Transaction Notification)."""
    from app.utils.payfast import verify_payment

    data = request.form.to_dict()
    logger.info("PayFast ITN received: %s", data)

    if not verify_payment(data):
        logger.warning("PayFast signature verification failed")
        return "INVALID", 400

    order_number = data.get("m_payment_id", "")
    payment_status = data.get("payment_status", "")

    order = Order.query.filter_by(order_number=order_number).first()
    if not order:
        logger.warning("Order not found: %s", order_number)
        return "NOT FOUND", 404

    order.payment_id = data.get("pf_payment_id", "")

    if payment_status == "COMPLETE":
        order.payment_status = "paid"
        order.status = "confirmed"
    elif payment_status == "CANCELLED":
        order.payment_status = "cancelled"
        order.status = "cancelled"
    else:
        order.payment_status = payment_status.lower()

    db.session.commit()
    logger.info(
        "Order %s payment updated: %s", order.order_number, order.payment_status
    )
    return "OK", 200


@api_bp.route("/search")
def search():
    """Global search endpoint for AJAX."""
    from app.models.blog import Post
    from app.models.store import Product

    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify({"posts": [], "products": []})

    posts = (
        Post.query.filter(
            Post.is_published.is_(True),
            db.or_(
                Post.title.ilike(f"%{q}%"),
                Post.excerpt.ilike(f"%{q}%"),
            ),
        )
        .limit(5)
        .all()
    )

    products = (
        Product.query.filter(
            Product.is_active.is_(True),
            db.or_(
                Product.name.ilike(f"%{q}%"),
                Product.short_description.ilike(f"%{q}%"),
            ),
        )
        .limit(5)
        .all()
    )

    return jsonify(
        {
            "posts": [
                {
                    "title": p.title,
                    "slug": p.slug,
                    "excerpt": p.snippet[:100],
                }
                for p in posts
            ],
            "products": [
                {
                    "name": p.name,
                    "slug": p.slug,
                    "price": f"R{p.current_price:.2f}",
                    "image": p.image,
                }
                for p in products
            ],
        }
    )
