# AviaGreene Solutions — Flask Web Application

A full-stack Flask web application for AviaGreene Solutions Ltd., converted from the original React/Vite project.

## Structure

```
aviagreene_flask/
├── app.py                    # Main Flask application + SQLAlchemy models + routes
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── instance/                 # SQLite database (auto-created)
├── static/
│   ├── css/style.css         # Full design system (navy + green brand)
│   └── js/main.js            # Sticky header, mobile menu, scroll animations
└── templates/
    ├── base.html             # Base layout with header/footer
    ├── home.html             # Homepage with hero, stats, services preview
    ├── about.html            # About page with story, values, standards
    ├── services.html         # Services listing
    ├── service_detail.html   # Individual service page with quote form
    ├── global_reach.html     # Global reach map and regions
    ├── training.html         # Training Academy page
    ├── enroll.html           # Student enrollment form
    ├── blog.html             # Blog/insights listing
    ├── contact.html          # Contact page with quote form
    ├── _cta_band.html        # Reusable CTA component
    ├── _quote_form.html      # Reusable quote form component
    └── admin/
        ├── base.html         # Admin sidebar layout
        ├── dashboard.html    # Admin dashboard with stats
        ├── quotes.html       # Quote requests management
        ├── enrollments.html  # Student enrollments management
        ├── blog.html         # Blog post listing
        └── blog_form.html    # Create/edit blog posts
```

## Database Models

| Model | Fields |
|-------|--------|
| `QuoteRequest` | full_name, company, email, phone, service, requirements, status, created_at |
| `StudentEnrollment` | full_name, email, phone, course, experience_level, message, status, created_at |
| `BlogPost` | title, slug, excerpt, content, category, is_published, published_at |

## Pages / Routes

| Route | Description |
|-------|-------------|
| `/` | Homepage |
| `/about` | About page |
| `/services` | Services listing |
| `/services/<slug>` | Individual service detail |
| `/global-reach` | Global reach page |
| `/training` | Training Academy |
| `/training/enroll` | Enrollment form (POST saves to DB) |
| `/blog` | Blog & insights |
| `/contact` | Contact / quote form (POST saves to DB) |
| `/admin` | Admin dashboard |
| `/admin/quotes` | Manage quote requests |
| `/admin/enrollments` | Manage student enrollments |
| `/admin/blog` | Manage blog posts |
| `/admin/blog/new` | Create new blog post |
| `/admin/blog/<id>/edit` | Edit existing blog post |

## Setup & Run

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy .env to .env and set values
cp .env .env

# 4. Run development server
python app.py

# 5. Open http://localhost:5000
```

## Production

```bash
gunicorn app:app --bind 0.0.0.0:8000 --workers 4
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | dev key | Flask session secret (change in production!) |
| `DATABASE_URL` | `sqlite:///aviagreene.db` | Database connection string |
| `PORT` | `5000` | Server port |
