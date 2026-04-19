# 🌿 Contemporary Hippie

**Modern wellness, holistic health, and curated organic products — for the conscious consumer.**

Contemporary Hippie is a full-stack health & wellness information and e-commerce platform built with Flask. Inspired by sites like Goop and Poosh, it blends editorial health content with a curated product store, featuring GSAP scroll-driven storytelling animations and integrated PayFast checkout.

---

## ✨ Features

### 🏠 Public Site
- **Storytelling Homepage** — Cinematic hero, featured articles, product spotlights, and newsletter signup with GSAP scroll animations
- **Blog Engine** — Full blog with categories, tags, search, comments, and reading-time estimates
- **Integrated Store** — Products naturally woven into health content (editorial product recommendations within articles)
- **Product Catalog** — Category filtering, sorting (price, name, newest), search, sale badges, and stock tracking
- **Shopping Cart** — Add/update/remove items, quantity controls, order summary
- **PayFast Checkout** — Full South African payment gateway integration (sandbox + live) with ITN (Instant Transaction Notification) verification
- **Order Management** — Order history, order detail, status tracking for customers
- **Newsletter** — Email subscription with duplicate prevention
- **Contact Form** — Submissions stored in database for admin review
- **Global Search** — AJAX-powered live search across posts and products
- **Responsive Design** — Mobile-first with hamburger menu, adaptive grids, and touch-friendly UI

### 🛡️ Admin Dashboard
- **Overview Dashboard** — Stats cards (posts, products, orders, users, subscribers, messages, comments)
- **Blog Management** — Create, edit, delete, publish/unpublish posts with image uploads
- **AI Content Generation** — Generate articles using MistralAI and images using DALL-E 3
- **Product Management** — Full CRUD for products with image uploads, categories, pricing, stock
- **Order Management** — View orders, update status (pending → confirmed → shipped → delivered)
- **Comment Moderation** — Approve or delete user comments
- **Contact Messages** — Read and manage contact form submissions (AJAX mark-as-read)
- **User Management** — View all registered users
- **Subscriber Management** — View newsletter subscribers

### 🎨 Design & UX
- **GSAP Animations** — ScrollTrigger parallax, staggered reveals, text animations, and cinematic transitions throughout
- **Playfair Display + Montserrat** — Premium typography pairing
- **Nature-inspired palette** — Forest green (#4CAF50), warm gold (#C9A54E), cream (#f9f6f0), dark (#1a1a1a)
- **Yoga loading overlay** — Branded loading animation on first visit
- **Editorial product integration** — Products appear as curated recommendations within articles, not banner ads

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, Flask 3.1 |
| **Database** | SQLAlchemy + SQLite (easily swappable to PostgreSQL) |
| **Auth** | Flask-Login with session management |
| **Forms** | Flask-WTF + WTForms with CSRF protection |
| **Migrations** | Flask-Migrate (Alembic) |
| **Email** | Flask-Mail (SMTP) |
| **Payments** | PayFast (South Africa) with MD5 signature verification |
| **AI** | MistralAI (article generation), OpenAI DALL-E 3 (image generation) |
| **Frontend** | Jinja2 templates, vanilla CSS, vanilla JS |
| **Animations** | GSAP 3 + ScrollTrigger |
| **Icons** | Font Awesome 6 |
| **Fonts** | Google Fonts (Playfair Display, Montserrat) |
| **Server** | Gunicorn (production) |

---

## 📁 Project Structure

```
contemporary_hippie_blog/
├── app/
│   ├── __init__.py              # App factory, extensions, seed data
│   ├── blueprints/
│   │   ├── admin/               # Admin dashboard routes
│   │   ├── api/                 # API routes (search, PayFast ITN)
│   │   ├── auth/                # Authentication routes & forms
│   │   ├── blog/                # Blog routes & forms
│   │   └── store/               # Store routes & forms
│   ├── models/
│   │   ├── user.py              # User, Address models
│   │   ├── blog.py              # Post, Category, Tag, Comment, Newsletter, ContactMessage
│   │   └── store.py             # Product, Category, CartItem, Order, OrderItem
│   ├── templates/
│   │   ├── base.html            # Master layout with header, footer, nav, GSAP
│   │   ├── blog/                # Blog templates (index, list, detail, category, about, contact)
│   │   ├── store/               # Store templates (shop, product, cart, checkout, orders)
│   │   ├── auth/                # Auth templates (login, register, profile, addresses)
│   │   ├── admin/               # Admin templates (dashboard, CRUD pages)
│   │   └── errors/              # 404, 500 error pages
│   ├── static/
│   │   ├── images/              # Static images and placeholders
│   │   └── uploads/             # User-uploaded content (posts, products, avatars)
│   └── utils/
│       ├── ai.py                # MistralAI & DALL-E integration
│       ├── decorators.py        # @admin_required decorator
│       └── payfast.py           # PayFast payment utilities
├── config.py                    # Configuration classes
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AnnillTimothy/contemporary_hippie_blog.git
   cd contemporary_hippie_blog
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your keys:
   ```env
   SECRET_KEY=your-secret-key-here
   FLASK_CONFIG=development
   
   # AI (optional — needed for AI content generation)
   MISTRAL_API_KEY=your-mistral-api-key
   OPENAI_API_KEY=your-openai-api-key
   
   # PayFast (required for checkout)
   PAYFAST_MERCHANT_ID=your-merchant-id
   PAYFAST_MERCHANT_KEY=your-merchant-key
   PAYFAST_PASSPHRASE=your-passphrase
   PAYFAST_SANDBOX=true
   
   # Email (optional — for mail features)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

5. **Run the application**
   ```bash
   python run.py
   ```
   The app will be available at `http://localhost:5000`

### Default Admin Account

On first run, a default admin user is created:
- **Email:** `admin@contemporaryhippie.com`
- **Password:** `admin123`

> ⚠️ **Change the default admin password immediately in production!**

---

## 💳 PayFast Integration

The store uses [PayFast](https://www.payfast.co.za/) for payment processing (South Africa's leading payment gateway).

### How it works:

1. Customer adds products to cart
2. At checkout, an `Order` is created with items and shipping address
3. Customer is redirected to PayFast with a signed payment form
4. PayFast processes the payment and sends an ITN (Instant Transaction Notification) to `/api/payfast/notify`
5. The ITN handler verifies the MD5 signature and updates the order status

### Sandbox Testing

Set `PAYFAST_SANDBOX=true` in your `.env` to use the PayFast sandbox environment. Use PayFast's [sandbox test credentials](https://developers.payfast.co.za/docs#step_1_test_on_sandbox) for testing.

### Going Live

1. Set `PAYFAST_SANDBOX=false`
2. Use your live PayFast merchant credentials
3. Ensure your `notify_url` is publicly accessible (PayFast needs to reach it)

---

## 🤖 AI Content Generation

The admin panel includes AI-powered content generation:

- **Article Generation** — Uses MistralAI to generate well-structured health & wellness articles with title, excerpt, content, tags, and reading time
- **Image Generation** — Uses OpenAI DALL-E 3 to generate matching article images

To enable, add your API keys to `.env`:
```env
MISTRAL_API_KEY=your-key
OPENAI_API_KEY=your-key
```

---

## 🏗️ Deployment

### Using Gunicorn (Production)

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"
```

### Environment Variables for Production

```env
SECRET_KEY=<strong-random-secret>
FLASK_CONFIG=production
DATABASE_URL=postgresql://user:pass@localhost/contemporary_hippie
PAYFAST_SANDBOX=false
PAYFAST_MERCHANT_ID=<live-id>
PAYFAST_MERCHANT_KEY=<live-key>
PAYFAST_PASSPHRASE=<live-passphrase>
```

### Database

The app defaults to SQLite for development. For production, set `DATABASE_URL` to a PostgreSQL connection string:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/contemporary_hippie
```

Install the PostgreSQL driver:
```bash
pip install psycopg2-binary
```

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

<p align="center">
  🌿 <strong>Contemporary Hippie</strong> — Nourish Your Body, Free Your Mind 🌿
</p>
