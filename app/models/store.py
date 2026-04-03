"""Store models."""

from datetime import datetime, timezone

from app import db


class Category(db.Model):
    """Product category."""

    __tablename__ = "product_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    image = db.Column(db.String(256), default="")
    products = db.relationship("Product", backref="category", lazy="dynamic")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = self.name.lower().replace(" ", "-")

    def __repr__(self):
        return f"<ProductCategory {self.name}>"


class Product(db.Model):
    """Store product."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    slug = db.Column(db.String(300), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(512), default="")
    price = db.Column(db.Float, nullable=False)
    sale_price = db.Column(db.Float, nullable=True)
    sku = db.Column(db.String(64), unique=True, nullable=True)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(512), default="")
    image_2 = db.Column(db.String(512), default="")
    image_3 = db.Column(db.String(512), default="")
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    weight = db.Column(db.Float, default=0.0)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Foreign keys
    category_id = db.Column(
        db.Integer, db.ForeignKey("product_categories.id"), nullable=False
    )

    @property
    def current_price(self):
        return self.sale_price if self.sale_price else self.price

    @property
    def is_on_sale(self):
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def in_stock(self):
        return self.stock > 0

    def __repr__(self):
        return f"<Product {self.name}>"


class CartItem(db.Model):
    """Shopping cart item."""

    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    # Relationships
    product = db.relationship("Product", backref="cart_items")

    @property
    def subtotal(self):
        return self.product.current_price * self.quantity

    def __repr__(self):
        return f"<CartItem {self.product.name} x{self.quantity}>"


class Order(db.Model):
    """Customer order."""

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(32), unique=True, nullable=False)
    status = db.Column(db.String(32), default="pending")
    subtotal = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    payment_id = db.Column(db.String(128), nullable=True)
    payment_status = db.Column(db.String(32), default="unpaid")
    notes = db.Column(db.Text, default="")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    items = db.relationship(
        "OrderItem", backref="order", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(db.Model):
    """Individual item in an order."""

    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(256), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    # Foreign keys
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)

    def __repr__(self):
        return f"<OrderItem {self.product_name} x{self.quantity}>"
