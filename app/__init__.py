"""Contemporary Hippie – Flask application factory."""

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

from config import config_by_name

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
mail = Mail()

login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


def create_app(config_name="default"):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Ensure required directories exist
    os.makedirs(app.config.get("UPLOAD_FOLDER", "app/static/uploads"), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, "uploads", "posts"), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, "uploads", "products"), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, "uploads", "avatars"), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)

    # Register blueprints
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.blog.routes import blog_bp
    from app.blueprints.store.routes import store_bp
    from app.blueprints.admin.routes import admin_bp
    from app.blueprints.api.routes import api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(blog_bp)
    app.register_blueprint(store_bp, url_prefix="/store")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Context processors
    @app.context_processor
    def inject_globals():
        from app.models.store import Category as ProductCategory, CartItem
        from flask_login import current_user

        cart_count = 0
        if current_user.is_authenticated:
            cart_count = CartItem.query.filter_by(user_id=current_user.id).count()

        product_categories = ProductCategory.query.order_by(
            ProductCategory.name
        ).all()
        return {
            "cart_count": cart_count,
            "product_categories": product_categories,
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template

        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template

        return render_template("errors/500.html"), 500

    # Create tables
    with app.app_context():
        from app.models import user, blog, store  # noqa: F401

        db.create_all()
        _seed_defaults(app)

    return app


def _seed_defaults(app):
    """Seed default admin user and categories if they don't exist."""
    from app.models.user import User
    from app.models.blog import Category as BlogCategory
    from app.models.store import Category as ProductCategory

    if not User.query.filter_by(is_admin=True).first():
        admin = User(
            username="admin",
            email="admin@contemporaryhippie.com",
            is_admin=True,
        )
        admin.set_password("admin123")
        db.session.add(admin)

    default_blog_cats = [
        "Wellness",
        "Nutrition",
        "Fitness",
        "Mental Health",
        "Yoga",
        "Natural Remedies",
    ]
    for name in default_blog_cats:
        if not BlogCategory.query.filter_by(name=name).first():
            db.session.add(BlogCategory(name=name))

    default_product_cats = [
        "Supplements",
        "Skincare",
        "Fitness Gear",
        "Essential Oils",
        "Tea & Herbs",
        "Books",
    ]
    for name in default_product_cats:
        if not ProductCategory.query.filter_by(name=name).first():
            db.session.add(ProductCategory(name=name))

    db.session.commit()
