"""Blog forms."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    BooleanField,
    SubmitField,
    SelectMultipleField,
)
from wtforms.validators import DataRequired, Length, Email


class PostForm(FlaskForm):
    """Blog post form."""

    title = StringField("Title", validators=[DataRequired(), Length(max=256)])
    excerpt = TextAreaField("Excerpt", validators=[Length(max=500)])
    content = TextAreaField("Content", validators=[DataRequired()])
    featured_image = FileField(
        "Featured Image",
        validators=[FileAllowed(["jpg", "jpeg", "png", "gif", "webp"])],
    )
    categories = SelectMultipleField("Categories", coerce=int)
    is_published = BooleanField("Publish Now")
    is_featured = BooleanField("Featured Post")
    meta_description = StringField("Meta Description", validators=[Length(max=320)])
    submit = SubmitField("Save Post")


class CommentForm(FlaskForm):
    """Blog comment form."""

    author_name = StringField("Name", validators=[DataRequired(), Length(max=128)])
    author_email = StringField("Email", validators=[DataRequired(), Email()])
    body = TextAreaField("Comment", validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField("Post Comment")


class ContactForm(FlaskForm):
    """Contact us form."""

    name = StringField("Full Name", validators=[DataRequired(), Length(max=128)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    reason = StringField("Reason", validators=[Length(max=64)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=5000)])
    submit = SubmitField("Send Message")


class NewsletterForm(FlaskForm):
    """Newsletter subscription form."""

    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Subscribe")


class AIGenerateForm(FlaskForm):
    """AI content generation form."""

    prompt = TextAreaField(
        "Prompt",
        validators=[DataRequired(), Length(min=10, max=1000)],
        render_kw={"placeholder": "Describe the health topic you want an article about..."},
    )
    generate_images = BooleanField("Generate Images (DALL-E)", default=True)
    submit = SubmitField("Generate Article")
