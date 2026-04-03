"""Authentication forms."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    ValidationError,
)

from app.models.user import User


class LoginForm(FlaskForm):
    """User login form."""

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    """User registration form."""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=64)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[Length(max=64)])
    last_name = StringField("Last Name", validators=[Length(max=64)])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6, max=128)]
    )
    password2 = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
    )
    submit = SubmitField("Create Account")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")


class ProfileForm(FlaskForm):
    """User profile edit form."""

    first_name = StringField("First Name", validators=[Length(max=64)])
    last_name = StringField("Last Name", validators=[Length(max=64)])
    bio = TextAreaField("Bio", validators=[Length(max=500)])
    submit = SubmitField("Save Changes")


class AddressForm(FlaskForm):
    """Shipping address form."""

    label = StringField("Label", validators=[DataRequired(), Length(max=64)])
    street = StringField("Street Address", validators=[DataRequired(), Length(max=256)])
    city = StringField("City", validators=[DataRequired(), Length(max=128)])
    province = StringField("Province", validators=[DataRequired(), Length(max=128)])
    postal_code = StringField(
        "Postal Code", validators=[DataRequired(), Length(max=20)]
    )
    country = StringField("Country", validators=[Length(max=64)])
    is_default = BooleanField("Set as default address")
    submit = SubmitField("Save Address")
