"""Blog models."""

from datetime import datetime, timezone

from app import db


# Many-to-many relationship table
post_categories = db.Table(
    "post_categories",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id"), primary_key=True),
    db.Column(
        "category_id", db.Integer, db.ForeignKey("blog_categories.id"), primary_key=True
    ),
)

post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class Category(db.Model):
    """Blog post category."""

    __tablename__ = "blog_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    posts = db.relationship(
        "Post", secondary=post_categories, back_populates="categories"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = self.name.lower().replace(" ", "-")

    def __repr__(self):
        return f"<Category {self.name}>"


class Tag(db.Model):
    """Blog post tag."""

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    def __repr__(self):
        return f"<Tag {self.name}>"


class Post(db.Model):
    """Blog post."""

    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    slug = db.Column(db.String(300), unique=True, nullable=False, index=True)
    excerpt = db.Column(db.Text, default="")
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(512), default="")
    image_2 = db.Column(db.String(512), default="")
    image_3 = db.Column(db.String(512), default="")
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_ai_generated = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    reading_time = db.Column(db.Integer, default=5)
    meta_description = db.Column(db.String(320), default="")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    published_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Foreign keys
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    categories = db.relationship(
        "Category", secondary=post_categories, back_populates="posts"
    )
    tags = db.relationship("Tag", secondary=post_tags, backref="posts")
    comments = db.relationship(
        "Comment", backref="post", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def snippet(self):
        if self.excerpt:
            return self.excerpt
        return self.content[:200] + "..." if len(self.content) > 200 else self.content

    def publish(self):
        self.is_published = True
        self.published_at = datetime.now(timezone.utc)

    def increment_views(self):
        self.views += 1
        db.session.commit()

    def __repr__(self):
        return f"<Post {self.title}>"


class Comment(db.Model):
    """Blog post comment."""

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(128), nullable=False)
    author_email = db.Column(db.String(120), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Foreign keys
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Comment by {self.author_name}>"


class Newsletter(db.Model):
    """Newsletter subscriber."""

    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Subscriber {self.email}>"


class ContactMessage(db.Model):
    """Contact form submission."""

    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    reason = db.Column(db.String(64), default="General Question")
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Message from {self.name}>"
