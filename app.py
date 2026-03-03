import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from models import db, Project, Skill, Experience, Message, SiteSettings, BlogPost, Achievement
import re
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///portfolio.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
OWNER_EMAIL = os.environ.get('OWNER_EMAIL', '')

db.init_app(app)

# ─── Helpers ───────────────────────────────────────────────────────────────────
def send_notification(message_obj):
    if not SMTP_USER or not OWNER_EMAIL:
        return
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'[Portfolio] New message from {message_obj.name}'
        msg['From'] = SMTP_USER
        msg['To'] = OWNER_EMAIL
        body = f"""
New contact form submission:

Name: {message_obj.name}
Email: {message_obj.email}
Subject: {message_obj.subject}

Message:
{message_obj.message}

Received: {message_obj.created_at.strftime('%d %b %Y, %H:%M')}
"""
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e:
        print(f'Email error: {e}')


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ─── Public Routes ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    projects = Project.query.order_by(Project.order, Project.created_at.desc()).all()
    skills = Skill.query.order_by(Skill.category, Skill.order).all()
    experience = Experience.query.order_by(Experience.order).all()
    blogs = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).limit(6).all()
    achievements = Achievement.query.order_by(Achievement.order, Achievement.created_at.desc()).all()
    settings = {s.key: s.value for s in SiteSettings.query.all()}

    skill_categories = {}
    for skill in skills:
        cat = skill.category or 'Other'
        skill_categories.setdefault(cat, []).append(skill)

    return render_template('index.html',
        projects=projects,
        skill_categories=skill_categories,
        experience=experience,
        blogs=blogs,
        achievements=achievements,
        settings=settings
    )


@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    subject = request.form.get('subject', '').strip()
    message_text = request.form.get('message', '').strip()

    if not all([name, email, message_text]):
        return jsonify({'success': False, 'error': 'Please fill in all required fields.'}), 400

    msg = Message(name=name, email=email, subject=subject, message=message_text)
    db.session.add(msg)
    db.session.commit()
    send_notification(msg)

    return jsonify({'success': True, 'message': "Thanks! I'll get back to you soon."})


@app.route('/api/projects')
def api_projects():
    category = request.args.get('category')
    q = Project.query
    if category and category != 'All':
        q = q.filter_by(category=category)
    projects = q.order_by(Project.order, Project.created_at.desc()).all()
    return jsonify([p.to_dict() for p in projects])


# ─── Admin Auth ────────────────────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))


# ─── Admin Dashboard ───────────────────────────────────────────────────────────
@app.route('/admin')
@login_required
def admin_dashboard():
    stats = {
        'projects': Project.query.count(),
        'skills': Skill.query.count(),
        'experience': Experience.query.count(),
        'messages': Message.query.count(),
        'unread': Message.query.filter_by(is_read=False).count(),
        'blogs': BlogPost.query.count(),
        'published_blogs': BlogPost.query.filter_by(published=True).count(),
        'achievements': Achievement.query.count(),
    }
    recent_messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, recent_messages=recent_messages)


# ─── Admin: Projects ───────────────────────────────────────────────────────────
@app.route('/admin/projects')
@login_required
def admin_projects():
    projects = Project.query.order_by(Project.order, Project.created_at.desc()).all()
    return render_template('admin/projects.html', projects=projects)


@app.route('/admin/projects/new', methods=['GET', 'POST'])
@login_required
def admin_project_new():
    if request.method == 'POST':
        p = Project(
            title=request.form['title'],
            description=request.form['description'],
            tech_stack=request.form.get('tech_stack', ''),
            github_url=request.form.get('github_url', ''),
            live_url=request.form.get('live_url', ''),
            image_url=request.form.get('image_url', ''),
            category=request.form.get('category', ''),
            featured='featured' in request.form,
            order=int(request.form.get('order', 0)),
        )
        db.session.add(p)
        db.session.commit()
        flash('Project added!', 'success')
        return redirect(url_for('admin_projects'))
    return render_template('admin/project_form.html', project=None)


@app.route('/admin/projects/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
def admin_project_edit(pid):
    p = Project.query.get_or_404(pid)
    if request.method == 'POST':
        p.title = request.form['title']
        p.description = request.form['description']
        p.tech_stack = request.form.get('tech_stack', '')
        p.github_url = request.form.get('github_url', '')
        p.live_url = request.form.get('live_url', '')
        p.image_url = request.form.get('image_url', '')
        p.category = request.form.get('category', '')
        p.featured = 'featured' in request.form
        p.order = int(request.form.get('order', 0))
        db.session.commit()
        flash('Project updated!', 'success')
        return redirect(url_for('admin_projects'))
    return render_template('admin/project_form.html', project=p)


@app.route('/admin/projects/<int:pid>/delete', methods=['POST'])
@login_required
def admin_project_delete(pid):
    p = Project.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash('Project deleted.', 'success')
    return redirect(url_for('admin_projects'))


# ─── Admin: Skills ─────────────────────────────────────────────────────────────
@app.route('/admin/skills')
@login_required
def admin_skills():
    skills = Skill.query.order_by(Skill.category, Skill.order).all()
    return render_template('admin/skills.html', skills=skills)


@app.route('/admin/skills/new', methods=['POST'])
@login_required
def admin_skill_new():
    s = Skill(
        name=request.form['name'],
        category=request.form.get('category', ''),
        proficiency=int(request.form.get('proficiency', 80)),
        order=int(request.form.get('order', 0)),
    )
    db.session.add(s)
    db.session.commit()
    flash('Skill added!', 'success')
    return redirect(url_for('admin_skills'))


@app.route('/admin/skills/<int:sid>/delete', methods=['POST'])
@login_required
def admin_skill_delete(sid):
    s = Skill.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    flash('Skill removed.', 'success')
    return redirect(url_for('admin_skills'))


# ─── Admin: Experience ─────────────────────────────────────────────────────────
@app.route('/admin/experience')
@login_required
def admin_experience():
    experience = Experience.query.order_by(Experience.order).all()
    return render_template('admin/experience.html', experience=experience)


@app.route('/admin/experience/new', methods=['POST'])
@login_required
def admin_experience_new():
    e = Experience(
        company=request.form['company'],
        role=request.form['role'],
        description=request.form.get('description', ''),
        start_date=request.form.get('start_date', ''),
        end_date=request.form.get('end_date', ''),
        location=request.form.get('location', ''),
        order=int(request.form.get('order', 0)),
    )
    db.session.add(e)
    db.session.commit()
    flash('Experience added!', 'success')
    return redirect(url_for('admin_experience'))


@app.route('/admin/experience/<int:eid>/delete', methods=['POST'])
@login_required
def admin_experience_delete(eid):
    e = Experience.query.get_or_404(eid)
    db.session.delete(e)
    db.session.commit()
    flash('Entry removed.', 'success')
    return redirect(url_for('admin_experience'))


# ─── Admin: Messages ───────────────────────────────────────────────────────────
@app.route('/admin/messages')
@login_required
def admin_messages():
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)


@app.route('/admin/messages/<int:mid>/read', methods=['POST'])
@login_required
def admin_message_read(mid):
    m = Message.query.get_or_404(mid)
    m.is_read = True
    db.session.commit()
    return redirect(url_for('admin_messages'))


@app.route('/admin/messages/<int:mid>/delete', methods=['POST'])
@login_required
def admin_message_delete(mid):
    m = Message.query.get_or_404(mid)
    db.session.delete(m)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin_messages'))


@app.route('/blog/<slug>')
def blog_post(slug):
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    settings = {s.key: s.value for s in SiteSettings.query.all()}
    return render_template('blog_post.html', post=post, settings=settings)


# ─── Admin: Blog ───────────────────────────────────────────────────
@app.route('/admin/blog')
@login_required
def admin_blog():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog.html', posts=posts)


def make_slug(title):
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s_-]+', '-', slug).strip('-')
    base = slug
    counter = 1
    while BlogPost.query.filter_by(slug=slug).first():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


@app.route('/admin/blog/new', methods=['GET', 'POST'])
@login_required
def admin_blog_new():
    if request.method == 'POST':
        title = request.form['title']
        action = request.form.get('published_action', 'draft')
        p = BlogPost(
            title=title,
            slug=make_slug(title),
            summary=request.form.get('summary', ''),
            content=request.form.get('content', ''),
            cover_image=request.form.get('cover_image', ''),
            tags=request.form.get('tags', ''),
            read_time=int(request.form.get('read_time', 5)),
            published=(action == 'publish') or ('published' in request.form),
            featured='featured' in request.form,
        )
        db.session.add(p)
        db.session.commit()
        flash('Blog post created!', 'success')
        return redirect(url_for('admin_blog'))
    return render_template('admin/blog_form.html', post=None)


@app.route('/admin/blog/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
def admin_blog_edit(pid):
    p = BlogPost.query.get_or_404(pid)
    if request.method == 'POST':
        p.title = request.form['title']
        p.summary = request.form.get('summary', '')
        p.content = request.form.get('content', '')
        p.cover_image = request.form.get('cover_image', '')
        p.tags = request.form.get('tags', '')
        p.read_time = int(request.form.get('read_time', 5))
        p.published = 'published' in request.form
        p.featured = 'featured' in request.form
        p.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Post updated!', 'success')
        return redirect(url_for('admin_blog'))
    return render_template('admin/blog_form.html', post=p)


@app.route('/admin/blog/<int:pid>/delete', methods=['POST'])
@login_required
def admin_blog_delete(pid):
    p = BlogPost.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash('Post deleted.', 'success')
    return redirect(url_for('admin_blog'))


# ─── Admin: Achievements ───────────────────────────────────────────
@app.route('/admin/achievements')
@login_required
def admin_achievements():
    achievements = Achievement.query.order_by(Achievement.order, Achievement.created_at.desc()).all()
    return render_template('admin/achievements.html', achievements=achievements)


@app.route('/admin/achievements/new', methods=['POST'])
@login_required
def admin_achievement_new():
    a = Achievement(
        title=request.form['title'],
        description=request.form.get('description', ''),
        issuer=request.form.get('issuer', ''),
        date=request.form.get('date', ''),
        category=request.form.get('category', ''),
        icon=request.form.get('icon', '🏆'),
        link=request.form.get('link', ''),
        order=int(request.form.get('order', 0)),
    )
    db.session.add(a)
    db.session.commit()
    flash('Achievement added!', 'success')
    return redirect(url_for('admin_achievements'))


@app.route('/admin/achievements/<int:aid>/edit', methods=['GET', 'POST'])
@login_required
def admin_achievement_edit(aid):
    a = Achievement.query.get_or_404(aid)
    if request.method == 'POST':
        a.title = request.form['title']
        a.description = request.form.get('description', '')
        a.issuer = request.form.get('issuer', '')
        a.date = request.form.get('date', '')
        a.category = request.form.get('category', '')
        a.icon = request.form.get('icon', '🏆')
        a.link = request.form.get('link', '')
        a.order = int(request.form.get('order', 0))
        db.session.commit()
        flash('Achievement updated!', 'success')
        return redirect(url_for('admin_achievements'))
    return render_template('admin/achievement_form.html', achievement=a)


@app.route('/admin/achievements/<int:aid>/delete', methods=['POST'])
@login_required
def admin_achievement_delete(aid):
    a = Achievement.query.get_or_404(aid)
    db.session.delete(a)
    db.session.commit()
    flash('Achievement removed.', 'success')
    return redirect(url_for('admin_achievements'))


# ─── Admin: Settings ───────────────────────────────────────────────────────────
@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        for key in ['hero_title', 'hero_subtitle', 'about_text', 'github_url',
                    'linkedin_url', 'twitter_url', 'resume_url', 'email', 'hero_photo']:
            SiteSettings.set(key, request.form.get(key, ''))
        flash('Settings saved!', 'success')
        return redirect(url_for('admin_settings'))
    settings = {s.key: s.value for s in SiteSettings.query.all()}
    return render_template('admin/settings.html', settings=settings)


# ─── Seed & Init ───────────────────────────────────────────────────────────────
def seed_data():
    """Seed with sample data if DB is empty."""
    if Project.query.count() == 0:
        projects = [
            Project(title='E-Commerce Platform', description='A full-featured online store with payment integration, inventory management, and real-time analytics dashboard.', tech_stack='Python, Django, PostgreSQL, Redis, Stripe', category='Web App', featured=True, order=1, github_url='https://github.com/shubh', live_url='#'),
            Project(title='AI Chat Assistant', description='Conversational AI chatbot built with OpenAI GPT-4, featuring context retention and multi-modal support.', tech_stack='Python, FastAPI, OpenAI, React, WebSocket', category='AI/ML', featured=True, order=2, github_url='https://github.com/shubh'),
            Project(title='Portfolio CMS', description='A headless CMS for managing portfolio content with REST API and real-time preview functionality.', tech_stack='Flask, SQLAlchemy, SQLite, JavaScript', category='Web App', order=3, github_url='https://github.com/shubh'),
        ]
        db.session.add_all(projects)

    if Skill.query.count() == 0:
        skills = [
            Skill(name='Python', category='Languages', proficiency=92, order=1),
            Skill(name='JavaScript', category='Languages', proficiency=85, order=2),
            Skill(name='TypeScript', category='Languages', proficiency=78, order=3),
            Skill(name='SQL', category='Languages', proficiency=80, order=4),
            Skill(name='Flask', category='Frameworks', proficiency=90, order=1),
            Skill(name='Django', category='Frameworks', proficiency=85, order=2),
            Skill(name='React', category='Frameworks', proficiency=80, order=3),
            Skill(name='FastAPI', category='Frameworks', proficiency=82, order=4),
            Skill(name='PostgreSQL', category='Databases', proficiency=80, order=1),
            Skill(name='Redis', category='Databases', proficiency=75, order=2),
            Skill(name='MongoDB', category='Databases', proficiency=72, order=3),
            Skill(name='Docker', category='Tools', proficiency=78, order=1),
            Skill(name='Git', category='Tools', proficiency=90, order=2),
            Skill(name='AWS', category='Tools', proficiency=70, order=3),
            Skill(name='Linux', category='Tools', proficiency=82, order=4),
        ]
        db.session.add_all(skills)

    if Experience.query.count() == 0:
        exp = [
            Experience(company='Tech Startup', role='Backend Developer', description='Built scalable REST APIs serving 50k+ daily users. Led migration from monolith to microservices architecture. Reduced API response times by 40%.', start_date='Jan 2024', end_date='Present', location='Remote', order=1),
            Experience(company='Freelance', role='Full-Stack Developer', description='Delivered 10+ client projects spanning e-commerce, dashboards, and automation tools. Maintained long-term relationships with 5 recurring clients.', start_date='Jun 2022', end_date='Dec 2023', location='Remote', order=2),
        ]
        db.session.add_all(exp)

    if BlogPost.query.count() == 0:
        posts = [
            BlogPost(title='Building Scalable REST APIs with Flask', slug='building-scalable-rest-apis-flask', summary='A deep dive into designing production-ready REST APIs using Flask, SQLAlchemy, and Redis for caching.', content='Full article content goes here...', tags='Flask, Python, API, Backend', read_time=8, published=True, featured=True),
            BlogPost(title='PostgreSQL vs MongoDB: When to Use Which', slug='postgresql-vs-mongodb', summary='A practical guide to choosing the right database for your project based on data structure and scale.', content='Full article content goes here...', tags='Database, PostgreSQL, MongoDB', read_time=6, published=True, featured=False),
            BlogPost(title='Docker for Python Developers', slug='docker-for-python-developers', summary='How to containerize your Flask or Django apps with Docker for consistent development and deployment.', content='Full article content goes here...', tags='Docker, Python, DevOps', read_time=10, published=True, featured=False),
        ]
        db.session.add_all(posts)

    if Achievement.query.count() == 0:
        achievements = [
            Achievement(title='Python Developer Certification', description='Completed advanced Python programming certification covering OOP, concurrency, and design patterns.', issuer='HackerRank', date='Jan 2024', category='Certificate', icon='🏅', order=1),
            Achievement(title='Best Hack — College Hackathon', description='Won 1st place at the annual college hackathon with an AI-powered study assistant built in 24 hours.', issuer='College Tech Fest', date='Nov 2023', category='Award', icon='🏆', order=2),
            Achievement(title='Open Source Contributor', description='Contributed bug fixes and features to 3 open-source Flask extensions with 500+ GitHub stars.', issuer='GitHub', date='2023', category='Open Source', icon='⭐', order=3),
            Achievement(title='AWS Cloud Practitioner', description='Passed the AWS Cloud Practitioner certification exam, demonstrating foundational cloud knowledge.', issuer='Amazon Web Services', date='Aug 2023', category='Certificate', icon='☁️', order=4),
        ]
        db.session.add_all(achievements)

    if SiteSettings.query.count() == 0:
        defaults = {
            'hero_title': 'Shubh Shrivastava',
            'hero_subtitle': 'Backend Developer & Software Engineer crafting scalable systems and elegant solutions.',
            'about_text': "I'm a passionate developer with a love for building things that matter. I specialize in Python backends, REST APIs, and full-stack web development. When I'm not coding, I'm exploring new technologies and contributing to open-source projects.",
            'github_url': 'https://github.com/shubhshrivastava',
            'linkedin_url': 'https://linkedin.com/in/shubhshrivastava',
            'email': 'shubh@example.com',
            'resume_url': '#',
        }
        for k, v in defaults.items():
            db.session.add(SiteSettings(key=k, value=v))

    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)
