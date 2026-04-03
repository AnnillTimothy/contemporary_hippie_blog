"""Store forms."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    FloatField,
    IntegerField,
    BooleanField,
    SelectField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class ProductForm(FlaskForm):
    """Product form for admin."""

    name = StringField("Product Name", validators=[DataRequired(), Length(max=256)])
    description = TextAreaField("Description", validators=[DataRequired()])
    short_description = StringField(
        "Short Description", validators=[Length(max=512)]
    )
    price = FloatField("Price (ZAR)", validators=[DataRequired(), NumberRange(min=0)])
    sale_price = FloatField("Sale Price (ZAR)", validators=[Optional(), NumberRange(min=0)])
    sku = StringField("SKU", validators=[Optional(), Length(max=64)])
    stock = IntegerField("Stock Quantity", validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    image = FileField(
        "Main Image",
        validators=[FileAllowed(["jpg", "jpeg", "png", "gif", "webp"])],
    )
    is_active = BooleanField("Active", default=True)
    is_featured = BooleanField("Featured Product")
    submit = SubmitField("Save Product")


class CheckoutForm(FlaskForm):
    """Checkout form."""

    shipping_address = SelectField("Shipping Address", coerce=int)
    notes = TextAreaField("Order Notes", validators=[Length(max=500)])
    submit = SubmitField("Place Order")
