"""Authentication routes."""

from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models.user import User, Address
from app.blueprints.auth.forms import (
    LoginForm,
    RegistrationForm,
    ProfileForm,
    AddressForm,
)

auth_bp = Blueprint("auth", __name__, template_folder="../../templates/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("blog.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user, remember=form.remember_me.data)
            flash("Welcome back!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("blog.index"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("blog.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data or "",
            last_name=form.last_name.data or "",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created! You can now log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("blog.index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for("auth.profile"))
    return render_template("auth/profile.html", form=form, user=current_user)


@auth_bp.route("/addresses")
@login_required
def addresses():
    user_addresses = Address.query.filter_by(user_id=current_user.id).all()
    return render_template("auth/addresses.html", addresses=user_addresses)


@auth_bp.route("/addresses/add", methods=["GET", "POST"])
@login_required
def add_address():
    form = AddressForm()
    if form.validate_on_submit():
        address = Address(
            user_id=current_user.id,
            label=form.label.data,
            street=form.street.data,
            city=form.city.data,
            province=form.province.data,
            postal_code=form.postal_code.data,
            country=form.country.data or "South Africa",
            is_default=form.is_default.data,
        )
        if address.is_default:
            Address.query.filter_by(
                user_id=current_user.id, is_default=True
            ).update({"is_default": False})
        db.session.add(address)
        db.session.commit()
        flash("Address added!", "success")
        return redirect(url_for("auth.addresses"))
    return render_template("auth/address_form.html", form=form, title="Add Address")


@auth_bp.route("/addresses/<int:address_id>/edit", methods=["GET", "POST"])
@login_required
def edit_address(address_id):
    address = Address.query.get_or_404(address_id)
    if address.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("auth.addresses"))
    form = AddressForm(obj=address)
    if form.validate_on_submit():
        form.populate_obj(address)
        if address.is_default:
            Address.query.filter(
                Address.user_id == current_user.id, Address.id != address.id
            ).update({"is_default": False})
        db.session.commit()
        flash("Address updated!", "success")
        return redirect(url_for("auth.addresses"))
    return render_template("auth/address_form.html", form=form, title="Edit Address")


@auth_bp.route("/addresses/<int:address_id>/delete", methods=["POST"])
@login_required
def delete_address(address_id):
    address = Address.query.get_or_404(address_id)
    if address.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("auth.addresses"))
    db.session.delete(address)
    db.session.commit()
    flash("Address removed.", "info")
    return redirect(url_for("auth.addresses"))
