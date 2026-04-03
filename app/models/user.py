"""User model."""

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    """User account model."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), default="")
    last_name = db.Column(db.String(64), default="")
    avatar = db.Column(db.String(256), default="")
    bio = db.Column(db.Text, default="")
    is_admin = db.Column(db.Boolean, default=False)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    posts = db.relationship("Post", backref="author", lazy="dynamic")
    orders = db.relationship("Order", backref="customer", lazy="dynamic")
    cart_items = db.relationship(
        "CartItem", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    addresses = db.relationship(
        "Address", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.username

    def __repr__(self):
        return f"<User {self.username}>"


class Address(db.Model):
    """User shipping address."""

    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    label = db.Column(db.String(64), default="Home")
    street = db.Column(db.String(256), nullable=False)
    city = db.Column(db.String(128), nullable=False)
    province = db.Column(db.String(128), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(64), default="South Africa")
    is_default = db.Column(db.Boolean, default=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
