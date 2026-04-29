from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from markupsafe import Markup
from datetime import datetime, timedelta
from functools import wraps
import os
import csv
import io
import re
import sendgrid
from sendgrid.helpers.mail import Mail, To

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'aviagreene-dev-secret-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aviagreene.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', 'admin')
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'aviagreene2026')
app.config['WTF_CSRF_ENABLED'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SENDGRID_API_KEY'] = os.environ.get('SENDGRID_API_KEY', '')
app.config['SENDGRID_FROM_EMAIL'] = os.environ.get('SENDGRID_FROM_EMAIL', 'ops@aviagreene.com')
app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL', 'ops@aviagreene.com')

db = SQLAlchemy(app)
csrf = CSRFProtect(app)


# ─── Email helper ─────────────────────────────────────────────────────────────

def send_email(to, subject, html_content):
    api_key = app.config.get('SENDGRID_API_KEY', '')
    from_email = app.config.get('SENDGRID_FROM_EMAIL', 'ops@aviagreene.com')
    if not api_key:
        return
    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        message = Mail(from_email=from_email, to_emails=To(to),
                       subject=subject, html_content=html_content)
        sg.send(message)
    except Exception as e:
        app.logger.error(f'SendGrid error: {e}')


# ─── Models ───────────────────────────────────────────────────────────────────

class QuoteRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_type = db.Column(db.String(20), default='individual')
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40))
    company_name = db.Column(db.String(120))
    job_title = db.Column(db.String(80))
    country = db.Column(db.String(80))
    operator_name = db.Column(db.String(120))
    aircraft_type = db.Column(db.String(120))
    fleet_size = db.Column(db.String(20))
    base_airport = db.Column(db.String(20))
    service = db.Column(db.String(80))
    requirements = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='new')

    def __repr__(self):
        return f'<QuoteRequest {self.full_name}>'


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text)
    category = db.Column(db.String(60))
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<BlogPost {self.title}>'


class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ActivityLog {self.action}>'


class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120))
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def initials(self):
        parts = self.name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return parts[0][:2].upper() if parts else 'AN'

    def __repr__(self):
        return f'<Testimonial {self.name}>'


# ─── Helpers ──────────────────────────────────────────────────────────────────

def log_activity(action):
    try:
        entry = ActivityLog(action=action)
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        app.logger.error(f'Activity log error: {e}')


# ─── Data ─────────────────────────────────────────────────────────────────────

SERVICES = [
    {
        'slug': 'ground-handling',
        'title': 'Ground Handling Setup & Supervision',
        'tagline': 'Turnaround precision, every rotation.',
        'blurb': 'Ramp, passenger and baggage operations executed to global standards across every Nigerian and partner airport.',
        'icon': 'wrench',
        'highlights': ['Ramp & apron services', 'Passenger & baggage handling', 'Load control & weight balance', 'GSE provision', 'Turnaround supervision'],
        'details': [
            'Our ground handling teams deliver IATA-aligned ramp, passenger and load-control services at all major Nigerian airports and through vetted partners across Africa, Europe and the Middle East.',
            'We coordinate every element of the turnaround — from marshalling and pushback to catering uplift and cabin readiness — so your aircraft departs on schedule, every time.',
        ],
    },
    {
        'slug': 'global-fuel',
        'title': 'Global Fuel Setup',
        'tagline': 'Uplift, guaranteed anywhere.',
        'blurb': 'Jet-A1 and AvGas sourced and delivered across Nigeria and partner territories — on time, on spec.',
        'icon': 'fuel',
        'highlights': ['Jet-A1 & AvGas supply', 'Into-plane fuelling', 'Fuel quality assurance', 'Tankering support', 'Global uplift coordination'],
        'details': [
            'AviaGreene procures and arranges delivery of aviation fuel across Nigeria and through an international partner network — eliminating the risk of uplift failure that can ground an operation.',
            'Our team monitors fuel quality, quantity and pricing to ensure your operation stays efficient and compliant, wherever your mission takes you.',
        ],
    },
    {
        'slug': 'overflight-permits',
        'title': 'Overflight & Landing Permits',
        'tagline': 'Clearances, secured swiftly.',
        'blurb': 'Overflight, landing and diplomatic clearances secured through our regulatory network — including short-notice requests.',
        'icon': 'clipboard',
        'highlights': ['Overflight permits', 'Landing clearances', 'Short-notice & emergency requests', 'Diplomatic & ad-hoc rights', 'Slot coordination'],
        'details': [
            'AviaGreene secures overflight, landing and diplomatic clearances on behalf of operators worldwide — leveraging long-standing relationships with the NCAA and international civil aviation authorities.',
            'Whether you need a same-day permit for a humanitarian mission or seasonal traffic rights for a scheduled programme, our regulatory team manages the paperwork, the politics and the deadlines.',
        ],
    },
    {
        'slug': 'flight-dispatch',
        'title': 'Flight Dispatch Services',
        'tagline': 'Every flight, planned to perfection.',
        'blurb': 'Operational flight planning, weather analysis, NOTAM briefings and ATC coordination — handled by FAA, GCAA & NCAA licensed dispatchers.',
        'icon': 'radio',
        'highlights': ['FAA, GCAA & NCAA Licensed dispatchers', 'Operational flight plans', 'Weather & NOTAM briefings', 'ATC slot filing', 'Weight & balance computation'],
        'details': [
            'Our licensed dispatchers produce ICAO-compliant operational flight plans, weather assessments and crew briefing packs — ensuring every departure is both legal and optimised.',
            'We file ATC slots, manage changes en-route and maintain continuous communication with crew and operations throughout the flight, so nothing is left to chance.',
        ],
    },
    {
        'slug': 'catering',
        'title': 'Catering Coordination',
        'tagline': 'Every palate, every altitude.',
        'blurb': 'Premium inflight catering coordinated with vetted suppliers across Nigeria and internationally — tailored to your crew and passengers.',
        'icon': 'star',
        'highlights': ['Inflight meal coordination', 'VIP & executive catering', 'Dietary & cultural requirements', 'Crew catering', 'International catering partners'],
        'details': [
            'AviaGreene coordinates inflight catering with a network of vetted airport caterers and suppliers, ensuring meals are prepared, delivered and loaded to specification and on time.',
            'From simple crew meals to multi-course executive dining, we handle the ordering and the quality check so your passengers are well served at every altitude.',
        ],
    },
    {
        'slug': 'hotac',
        'title': 'Hotel & Accommodation (HOTAC)',
        'tagline': 'Rest assured, wherever you land.',
        'blurb': 'Crew and passenger hotel accommodation arranged at preferred rates with trusted properties across Nigeria and internationally.',
        'icon': 'compass',
        'highlights': ['Crew hotel coordination', 'VIP passenger accommodation', 'Negotiated preferred rates', 'Airport-proximity properties', 'Transfer & transport included'],
        'details': [
            'AviaGreene manages all HOTAC requirements for crew and passengers — sourcing appropriate hotels, negotiating rates and coordinating transport between the airport and accommodation.',
            'Our partners include leading properties at all major Nigerian airports and international destinations, ensuring rest and comfort for crews on long-haul rotations.',
        ],
    },
    {
        'slug': 'ground-transportation',
        'title': 'Ground Transportation',
        'tagline': 'Seamless connections, kerb to kerb.',
        'blurb': 'VIP and crew ground transport coordinated with trusted operators across Nigeria — from tarmac to hotel and beyond.',
        'icon': 'globe',
        'highlights': ['VIP meet & assist transfers', 'Crew bus coordination', 'Airport-to-hotel transfers', 'Inter-city logistics', 'Protocol & diplomatic transport'],
        'details': [
            'Our ground transportation desk arranges vehicle fleets suited to every requirement — from luxury SUVs for VIP principals to crew coaches for airline operations.',
            'We coordinate timing, routes and contingency options so that every ground movement is executed on schedule and with full accountability.',
        ],
    },
    {
        'slug': 'pilgrimage',
        'title': 'Christian Pilgrimage Flights & Logistics',
        'tagline': 'Sacred journeys, expertly managed.',
        'blurb': 'End-to-end flight and logistics coordination for Christian pilgrimage groups travelling to Israel, Rome, and destinations worldwide.',
        'icon': 'heart',
        'highlights': ['Group charter sourcing', 'Pilgrimage route planning', 'Visa & permit assistance', 'HOTAC & ground transport', 'On-ground local coordination'],
        'details': [
            'AviaGreene specialises in the complex logistics of large pilgrimage group travel — coordinating charter aircraft, accommodation, ground transport and permits for groups travelling to sacred destinations.',
            'We work closely with church organisations and travel coordinators to ensure every element of the journey — from departure at Lagos to arrival at the holy site — is handled with care, precision and reverence.',
        ],
    },
]

REGIONS = [
    {'name': 'West Africa', 'body': 'Lagos, Abuja, Port Harcourt, Accra, Dakar, Abidjan, Monrovia.'},
    {'name': 'Africa-wide', 'body': 'Cairo, Nairobi, Johannesburg, Addis Ababa, Kigali, Luanda, Casablanca.'},
    {'name': 'Europe', 'body': 'London, Paris, Geneva, Frankfurt, Amsterdam, Lisbon, Istanbul.'},
    {'name': 'Middle East', 'body': 'Dubai, Doha, Riyadh, Jeddah, Abu Dhabi, Muscat, Bahrain.'},
    {'name': 'Americas', 'body': 'New York, Miami, Houston, Toronto, São Paulo, Mexico City.'},
    {'name': 'Asia & Oceania', 'body': 'Singapore, Hong Kong, Mumbai, Beijing, Tokyo, Sydney.'},
]

STATS = [
    {'k': '20+', 'v': 'Years of combined experience'},
    {'k': '60+', 'v': 'Countries reached'},
    {'k': '24/7', 'v': 'Operations desk'},
    {'k': '8', 'v': 'Service lines'},
]

VALUES = [
    {'icon': 'shield', 'title': 'Integrity', 'body': 'Transparent pricing, honest counsel and full regulatory compliance — without exception.'},
    {'icon': 'heart', 'title': 'Service', 'body': 'Discretion, attentiveness and a single point of accountability from quote to wheels-up.'},
    {'icon': 'compass', 'title': 'Excellence', 'body': 'Operational standards aligned with IATA and ICAO best practice on every mission.'},
    {'icon': 'sparkles', 'title': 'Partnership', 'body': 'We invest in long-term relationships with operators, regulators, suppliers and clients.'},
]

SERVICE_IMAGES = {
    'ground-handling': '/static/images/service-ground-handling.jpg',
    'global-fuel': '/static/images/service-global-fuel.jpg',
    'overflight-permits': '/static/images/service-overflight-permits.jpg',
    'flight-dispatch': '/static/images/service-flight-dispatch.jpg',
    'catering': '/static/images/service-catering.jpg',
    'hotac': '/static/images/service-hotac.jpg',
    'ground-transportation': '/static/images/service-ground-transportation.jpg',
    'pilgrimage': '/static/images/service-pilgrimage.jpg',
}

FAQS = [
    {
        'category': 'Overflight & Permits',
        'questions': [
            {'q': 'How quickly can you process an overflight permit?', 'a': 'In most cases, standard permits are processed within 24–48 hours. For short-notice and emergency requests, we can often secure clearances within hours depending on the territory.'},
            {'q': 'Do you handle permits for all African countries?', 'a': 'Yes. We have established relationships with civil aviation authorities across all 54 African countries, as well as key authorities in Europe, the Middle East and beyond.'},
            {'q': 'What information do you need to process a permit?', 'a': 'We typically need your aircraft registration, operator details, routing (origin, destination, overflight countries), flight date and time, and purpose of flight. Our team will guide you through the specifics.'},
        ]
    },
    {
        'category': 'Charter & Flights',
        'questions': [
            {'q': 'Can you arrange a charter flight on short notice?', 'a': 'Yes. Our operations desk is available 24/7 and we regularly handle same-day and next-day charter requests. Contact us directly for urgent requirements.'},
            {'q': 'What types of aircraft do you have access to?', 'a': 'Through our network of vetted operators, we can source light jets, mid-size jets, heavy jets, turboprops, and helicopters depending on your route and passenger requirements.'},
        ]
    },
    {
        'category': 'Ground Handling',
        'questions': [
            {'q': 'Which airports do you provide ground handling at?', 'a': 'We operate at all major Nigerian airports including Lagos (DNMM), Abuja (DNAA), Port Harcourt (DNPO) and Kano (DNKN), with partner handlers at airports across Africa, Europe and the Middle East.'},
            {'q': 'Do you handle both commercial and private aircraft?', 'a': 'Yes. We provide ground handling services for private jets, charter aircraft, corporate aviation, and commercial airline operations.'},
        ]
    },
    {
        'category': 'General',
        'questions': [
            {'q': 'Is AviaGreene available outside of office hours?', 'a': 'Our operations desk operates 24 hours a day, 7 days a week, 365 days a year. Office administration hours are Monday to Friday, 09:00–18:00 WAT.'},
            {'q': 'How do I get a quote?', 'a': 'Simply fill out the request form on our Contact page, or reach us directly by phone or email. We provide tailored proposals within hours.'},
            {'q': 'Do you work with international operators?', 'a': 'Yes. A significant portion of our clients are international operators, airlines and corporates who require support when operating into, out of, or through Nigerian and African airspace.'},
        ]
    },
]


def get_service(slug):
    return next((s for s in SERVICES if s['slug'] == slug), None)


# ─── Template helpers ─────────────────────────────────────────────────────────

SVG_ICONS = {
    'plane': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21 4 19 2c-2-2-4-2-5.5-.5L10 5 1.8 6.2c-.5.1-.9.6-.6 1.1l1.5 2.5c.3.4.8.6 1.3.6L8 10l-6.3 3.6c-.4.3-.5.9-.2 1.3l2.1 2.1 2.1 2.1c.4.4 1 .3 1.3-.2L11 13l-.1 3.9c0 .5.2 1 .6 1.3l2.5 1.5c.5.3 1-.1 1.1-.6z"/></svg>',
    'wrench': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
    'clipboard': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/></svg>',
    'fuel': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 22V6l6-4 6 4v16"/><path d="M3 22h12"/><path d="M9 22V12h6v10"/><path d="m19 2 2 2-2 2"/><path d="M19 4h-4"/><path d="M21 10v5a2 2 0 0 1-2 2"/></svg>',
    'radio': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9"/><path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"/><circle cx="12" cy="12" r="2"/><path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5"/><path d="M19.1 4.9C23 8.8 23 15.1 19.1 19"/></svg>',
    'star': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    'shield': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    'heart': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>',
    'compass': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>',
    'sparkles': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>',
    'shield-check': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>',
    'award': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/></svg>',
    'clock': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    'globe': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" x2="22" y1="12" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
}


@app.context_processor
def utility_functions():
    def icon_svg(name):
        return Markup(SVG_ICONS.get(name, ''))
    def trust_icon(name):
        return Markup(SVG_ICONS.get(name, ''))
    def value_icon(name):
        return Markup(SVG_ICONS.get(name, ''))
    def service_image(slug):
        return SERVICE_IMAGES.get(slug, 'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=900&q=80')
    return dict(icon_svg=icon_svg, trust_icon=trust_icon, value_icon=value_icon,
                service_image=service_image, now=datetime.utcnow())


@app.context_processor
def inject_admin_counts():
    try:
        unread = QuoteRequest.query.filter_by(status='new').count()
        pending_t = Testimonial.query.filter_by(status='pending').count()
    except Exception:
        unread = 0
        pending_t = 0
    return dict(unread_count=unread, pending_testimonials_count=pending_t)


# ─── Admin auth ───────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.path))
        return f(*args, **kwargs)
    return decorated


# ─── Public routes ────────────────────────────────────────────────────────────

@app.route('/')
def home():
    home_testimonials = Testimonial.query.filter_by(status='approved').order_by(Testimonial.created_at.desc()).limit(3).all()
    return render_template('home.html', stats=STATS, services=SERVICES, home_testimonials=home_testimonials)


@app.route('/about')
def about():
    return render_template('about.html', values=VALUES, stats=STATS)


@app.route('/services')
def services():
    return render_template('services.html', services=SERVICES)


@app.route('/services/<slug>')
def service_detail(slug):
    service = get_service(slug)
    if not service:
        return redirect(url_for('services'))
    others = [s for s in SERVICES if s['slug'] != slug][:4]
    return render_template('service_detail.html', service=service, others=others, services=SERVICES)


@app.route('/global-reach')
def global_reach():
    return render_template('global_reach.html', regions=REGIONS)


@app.route('/blog')
def blog():
    posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).all()
    return render_template('blog.html', posts=posts)


@app.route('/blog/<slug>')
def blog_post(slug):
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template('blog_post.html', post=post)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    success = False
    preselected_service = request.args.get('service', '')
    if request.method == 'POST':
        quote = QuoteRequest(
            client_type=request.form.get('client_type', 'individual').strip(),
            full_name=request.form.get('full_name', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            company_name=request.form.get('company_name', '').strip(),
            job_title=request.form.get('job_title', '').strip(),
            country=request.form.get('country', '').strip(),
            operator_name=request.form.get('operator_name', '').strip(),
            aircraft_type=request.form.get('aircraft_type', '').strip(),
            fleet_size=request.form.get('fleet_size', '').strip(),
            base_airport=request.form.get('base_airport', '').strip(),
            service=request.form.get('service', '').strip(),
            requirements=request.form.get('requirements', '').strip(),
        )
        db.session.add(quote)
        db.session.commit()
        admin_html = render_template('emails/admin_new_quote.html', quote=quote)
        send_email(to=app.config['ADMIN_EMAIL'],
                   subject=f'New Quote Request — {quote.full_name}',
                   html_content=admin_html)
        client_html = render_template('emails/client_confirmation.html', quote=quote)
        send_email(to=quote.email,
                   subject='Your Request Has Been Received — AviaGreene Solutions',
                   html_content=client_html)
        success = True
    return render_template('contact.html', success=success, services=SERVICES,
                           preselected_service=preselected_service)


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/faq')
def faq():
    return render_template('faq.html', faqs=FAQS)


@app.route('/testimonials')
def testimonials():
    approved = Testimonial.query.filter_by(status='approved').order_by(Testimonial.created_at.desc()).all()
    return render_template('testimonials.html', testimonials=approved)


@app.route('/testimonials/submit', methods=['GET', 'POST'])
def testimonial_submit():
    success = False
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        title = request.form.get('title', '').strip()
        body = request.form.get('body', '').strip()
        if name and body:
            t = Testimonial(name=name, title=title, body=body, status='pending')
            db.session.add(t)
            db.session.commit()
            log_activity(f'Testimonial submitted by {name} — awaiting approval')
            success = True
    return render_template('testimonial_submit.html', success=success)


# ─── Admin auth routes ────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    error = None
    next_url = request.args.get('next', '')
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        next_url = request.form.get('next_url', '')
        if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
            session.permanent = True
            session['admin_logged_in'] = True
            log_activity('Admin logged in')
            return redirect(next_url if next_url and next_url.startswith('/admin') else url_for('admin_dashboard'))
        error = 'Invalid credentials.'
    return render_template('admin/login.html', error=error, next_url=next_url)


@app.route('/admin/logout')
def admin_logout():
    log_activity('Admin logged out')
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


# ─── Admin routes ─────────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
def admin_dashboard():
    quotes = QuoteRequest.query.order_by(QuoteRequest.created_at.desc()).all()
    posts = BlogPost.query.order_by(BlogPost.published_at.desc()).all()
    activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(20).all()
    stats = {
        'total_quotes': QuoteRequest.query.count(),
        'new_quotes': QuoteRequest.query.filter_by(status='new').count(),
        'total_posts': BlogPost.query.count(),
        'published_posts': BlogPost.query.filter_by(is_published=True).count(),
    }
    return render_template('admin/dashboard.html', quotes=quotes, posts=posts,
                           stats=stats, activity=activity)


@app.route('/admin/quotes')
@login_required
def admin_quotes():
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('client_type', '')
    search = request.args.get('search', '').strip()
    q = QuoteRequest.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    if type_filter:
        q = q.filter_by(client_type=type_filter)
    if search:
        q = q.filter(db.or_(
            QuoteRequest.full_name.ilike(f'%{search}%'),
            QuoteRequest.email.ilike(f'%{search}%'),
            QuoteRequest.company_name.ilike(f'%{search}%'),
            QuoteRequest.operator_name.ilike(f'%{search}%'),
            QuoteRequest.service.ilike(f'%{search}%'),
        ))
    quotes = q.order_by(QuoteRequest.created_at.desc()).all()
    return render_template('admin/quotes.html', quotes=quotes,
                           status_filter=status_filter, type_filter=type_filter, search=search)


@app.route('/admin/quotes/<int:quote_id>')
@login_required
def admin_quote_detail(quote_id):
    quote = QuoteRequest.query.get_or_404(quote_id)
    return render_template('admin/quote_detail.html', quote=quote)


@app.route('/admin/quotes/<int:quote_id>/status', methods=['POST'])
@login_required
def admin_quote_status(quote_id):
    quote = QuoteRequest.query.get_or_404(quote_id)
    old_status = quote.status
    quote.status = request.form.get('status', quote.status)
    db.session.commit()
    log_activity(f'Quote #{quote_id} ({quote.full_name}) status: "{old_status}" → "{quote.status}"')
    return redirect(request.referrer or url_for('admin_quotes'))


@app.route('/admin/quotes/<int:quote_id>/delete', methods=['POST'])
@login_required
def admin_quote_delete(quote_id):
    quote = QuoteRequest.query.get_or_404(quote_id)
    name = quote.full_name
    db.session.delete(quote)
    db.session.commit()
    log_activity(f'Quote #{quote_id} ({name}) deleted')
    flash('Quote request deleted.', 'success')
    return redirect(url_for('admin_quotes'))


@app.route('/admin/quotes/export', methods=['GET', 'POST'])
@login_required
def admin_quotes_export():
    if request.method == 'GET':
        return render_template('admin/export.html')

    period = request.form.get('period', 'all')
    status_filter = request.form.get('status', '')
    client_type_filter = request.form.get('client_type', '')
    custom_from = request.form.get('date_from', '')
    custom_to = request.form.get('date_to', '')

    q = QuoteRequest.query
    now = datetime.utcnow()

    if period == 'today':
        q = q.filter(QuoteRequest.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0))
    elif period == 'week':
        q = q.filter(QuoteRequest.created_at >= now - timedelta(days=7))
    elif period == 'month':
        q = q.filter(QuoteRequest.created_at >= now.replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    elif period == 'year':
        q = q.filter(QuoteRequest.created_at >= now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0))
    elif period == 'custom':
        if custom_from:
            q = q.filter(QuoteRequest.created_at >= datetime.strptime(custom_from, '%Y-%m-%d'))
        if custom_to:
            end = datetime.strptime(custom_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            q = q.filter(QuoteRequest.created_at <= end)

    if status_filter:
        q = q.filter_by(status=status_filter)
    if client_type_filter:
        q = q.filter_by(client_type=client_type_filter)

    quotes = q.order_by(QuoteRequest.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Reference', 'Client Type', 'Full Name', 'Email', 'Phone',
                     'Company Name', 'Job Title', 'Country', 'Operator Name', 'Aircraft Type',
                     'Fleet Size', 'Base Airport', 'Service', 'Requirements', 'Status', 'Date Submitted'])
    for q in quotes:
        writer.writerow([q.id, f'AVG-{q.id:05d}', q.client_type or 'individual', q.full_name,
                         q.email, q.phone or '', q.company_name or '', q.job_title or '',
                         q.country or '', q.operator_name or '', q.aircraft_type or '',
                         q.fleet_size or '', q.base_airport or '', q.service or '',
                         q.requirements or '', q.status, q.created_at.strftime('%d %b %Y %H:%M')])

    period_label = period.replace('_', ' ').title()
    filename = f'aviagreene-quotes-{period_label.lower().replace(" ", "-")}.csv'
    log_activity(f'CSV export: {len(quotes)} quotes ({period_label} / {status_filter or "all statuses"} / {client_type_filter or "all types"})')
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@app.route('/admin/blog')
@login_required
def admin_blog():
    posts = BlogPost.query.order_by(BlogPost.published_at.desc()).all()
    return render_template('admin/blog.html', posts=posts)


@app.route('/admin/blog/new', methods=['GET', 'POST'])
@login_required
def admin_blog_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        base_slug = slug
        counter = 1
        while BlogPost.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1
        post = BlogPost(title=title, slug=slug,
                        excerpt=request.form.get('excerpt', '').strip(),
                        content=request.form.get('content', '').strip(),
                        category=request.form.get('category', '').strip(),
                        is_published=bool(request.form.get('is_published')))
        db.session.add(post)
        db.session.commit()
        log_activity(f'Blog post created: "{title}"')
        flash('Post created.', 'success')
        return redirect(url_for('admin_blog'))
    return render_template('admin/blog_form.html', post=None)


@app.route('/admin/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_blog_edit(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if request.method == 'POST':
        new_title = request.form.get('title', '').strip()
        if new_title != post.title:
            new_slug = re.sub(r'[^a-z0-9]+', '-', new_title.lower()).strip('-')
            base_slug = new_slug
            counter = 1
            while BlogPost.query.filter(BlogPost.slug == new_slug, BlogPost.id != post.id).first():
                new_slug = f'{base_slug}-{counter}'
                counter += 1
            post.slug = new_slug
        post.title = new_title
        post.excerpt = request.form.get('excerpt', '').strip()
        post.content = request.form.get('content', '').strip()
        post.category = request.form.get('category', '').strip()
        post.is_published = bool(request.form.get('is_published'))
        db.session.commit()
        log_activity(f'Blog post updated: "{post.title}"')
        flash('Post updated.', 'success')
        return redirect(url_for('admin_blog'))
    return render_template('admin/blog_form.html', post=post)


@app.route('/admin/blog/<int:post_id>/delete', methods=['POST'])
@login_required
def admin_blog_delete(post_id):
    post = BlogPost.query.get_or_404(post_id)
    log_activity(f'Blog post deleted: "{post.title}"')
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'success')
    return redirect(url_for('admin_blog'))


@app.route('/admin/testimonials')
@login_required
def admin_testimonials():
    pending = Testimonial.query.filter_by(status='pending').order_by(Testimonial.created_at.desc()).all()
    approved = Testimonial.query.filter_by(status='approved').order_by(Testimonial.created_at.desc()).all()
    return render_template('admin/testimonials.html', pending=pending, approved=approved)


@app.route('/admin/testimonials/<int:t_id>/approve', methods=['POST'])
@login_required
def admin_testimonial_approve(t_id):
    t = Testimonial.query.get_or_404(t_id)
    t.status = 'approved'
    db.session.commit()
    log_activity(f'Testimonial approved: {t.name}')
    flash(f'Testimonial from {t.name} approved.', 'success')
    return redirect(url_for('admin_testimonials'))


@app.route('/admin/testimonials/<int:t_id>/unapprove', methods=['POST'])
@login_required
def admin_testimonial_reject(t_id):
    t = Testimonial.query.get_or_404(t_id)
    t.status = 'pending'
    db.session.commit()
    log_activity(f'Testimonial unapproved: {t.name}')
    flash(f'Testimonial from {t.name} moved back to pending.', 'success')
    return redirect(url_for('admin_testimonials'))


@app.route('/admin/testimonials/<int:t_id>/delete', methods=['POST'])
@login_required
def admin_testimonial_delete(t_id):
    t = Testimonial.query.get_or_404(t_id)
    name = t.name
    db.session.delete(t)
    db.session.commit()
    log_activity(f'Testimonial deleted: {name}')
    flash(f'Testimonial from {name} deleted.', 'success')
    return redirect(url_for('admin_testimonials'))


@app.route('/admin/activity')
@login_required
def admin_activity():
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).all()
    return render_template('admin/activity.html', logs=logs)


@app.route('/admin/settings')
@login_required
def admin_settings():
    return render_template('admin/settings.html',
        admin_username=app.config['ADMIN_USERNAME'],
        total_quotes=QuoteRequest.query.count(),
        total_posts=BlogPost.query.count(),
        total_testimonials=Testimonial.query.count(),
    )


# ─── Error handlers ──────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500


# ─── SEO routes ───────────────────────────────────────────────────────────────

@app.route('/sitemap.xml')
def sitemap():
    base = 'https://www.aviagreene.com'
    today = datetime.utcnow().strftime('%Y-%m-%d')
    static_urls = [
        ('/', '1.0', 'weekly'), ('/about', '0.8', 'monthly'),
        ('/services', '0.9', 'weekly'), ('/services/ground-handling', '0.8', 'monthly'),
        ('/services/global-fuel', '0.8', 'monthly'), ('/services/overflight-permits', '0.8', 'monthly'),
        ('/services/flight-dispatch', '0.8', 'monthly'), ('/services/catering', '0.8', 'monthly'),
        ('/services/hotac', '0.8', 'monthly'), ('/services/ground-transportation', '0.8', 'monthly'),
        ('/services/pilgrimage', '0.8', 'monthly'), ('/global-reach', '0.7', 'monthly'),
        ('/blog', '0.7', 'weekly'), ('/contact', '0.8', 'monthly'),
        ('/faq', '0.7', 'monthly'), ('/testimonials', '0.6', 'monthly'),
    ]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, priority, freq in static_urls:
        xml.append(f'  <url><loc>{base}{path}</loc><lastmod>{today}</lastmod><changefreq>{freq}</changefreq><priority>{priority}</priority></url>')
    for post in BlogPost.query.filter_by(is_published=True).all():
        xml.append(f'  <url><loc>{base}/blog/{post.slug}</loc><lastmod>{post.published_at.strftime("%Y-%m-%d")}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>')
    xml.append('</urlset>')
    response = make_response('\n'.join(xml))
    response.headers['Content-Type'] = 'application/xml'
    return response


@app.route('/robots.txt')
def robots():
    lines = ['User-agent: *', 'Allow: /', 'Disallow: /admin/', 'Disallow: /admin/login',
             '', 'Sitemap: https://www.aviagreene.com/sitemap.xml']
    response = make_response('\n'.join(lines))
    response.headers['Content-Type'] = 'text/plain'
    return response


# ─── Init ─────────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    if BlogPost.query.count() == 0:
        sample_posts = [
            BlogPost(title='AviaGreene Expands Ground Handling Network to East Africa',
                slug='ground-handling-east-africa',
                excerpt='AviaGreene Solutions announces a strategic expansion of its ground handling operations to key East African hubs including Nairobi, Entebbe and Dar es Salaam.',
                content='AviaGreene Solutions is proud to announce a major expansion of our ground handling capabilities across East Africa.\n\nOur teams are now operational at Jomo Kenyatta International Airport (Nairobi), Entebbe International Airport and Julius Nyerere International Airport (Dar es Salaam).\n\nThis expansion means that airline operators and charter clients can now enjoy seamless, IATA-aligned ground handling services from Lagos all the way to East Africa — under one trusted brand.',
                category='News', is_published=True),
            BlogPost(title='Understanding Overflight & Landing Permits: A Guide for Operators',
                slug='overflight-permits-guide',
                excerpt='Navigating overflight permits, landing clearances and diplomatic rights can be complex. Our experts break it down.',
                content="For operators, securing the right permits at the right time can make or break a mission.\n\nOverflight permits are required when your aircraft transits through a foreign country's airspace. Landing clearances are needed for any technical or commercial stop.\n\nAt AviaGreene, our regulatory team maintains active relationships with civil aviation authorities across Africa, the Middle East, Europe and beyond.",
                category='Insights', is_published=True),
            BlogPost(title='Excellence in Motion: The AviaGreene Commitment',
                slug='aviagreene-commitment',
                excerpt='What sets AviaGreene apart is not just what we do — it is how we do it.',
                content="At AviaGreene Solutions, our tagline is not a marketing slogan — it is a daily operational standard. Excellence in Motion. Trust in Every Flight.\n\nFrom the moment a client contacts our operations desk to wheels-down at the destination, every touchpoint is managed with precision, discretion and accountability.",
                category='Company', is_published=True),
        ]
        for p in sample_posts:
            db.session.add(p)
        db.session.commit()

    if Testimonial.query.count() == 0:
        sample_testimonials = [
            Testimonial(name='Oluwaseun Adeyemi', title='VP Operations, Pan-African Holdings',
                body='AviaGreene handled our executive charter from Lagos to Nairobi with flawless precision. Permits cleared, ground crew ready, catering loaded — all before we arrived at the terminal. That is the standard we expect and they delivered it without a single call from our side.',
                status='approved'),
            Testimonial(name='Capt. Emeka Nwosu', title='Flight Operations Manager',
                body='The permit team is in a class of their own. What would take our internal team weeks to coordinate, AviaGreene resolves in 48 hours. Their relationships with African aviation authorities are genuinely unmatched.',
                status='approved'),
            Testimonial(name='Aisha Mahmoud', title='Director, Diplomatic Affairs',
                body='We rely on AviaGreene for all our diplomatic flight logistics. The discretion, the reliability and the quality of their concierge arrangements have made them our exclusive partner for government travel.',
                status='approved'),
            Testimonial(name='Pastor David Okonkwo', title='Senior Pastor, Covenant Assembly',
                body='Our pilgrimage group of 200 members travelled to Israel without a single logistical issue. AviaGreene coordinated everything — flights, accommodation, ground transport — and our congregation felt truly cared for throughout.',
                status='approved'),
        ]
        for t in sample_testimonials:
            db.session.add(t)
        db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
