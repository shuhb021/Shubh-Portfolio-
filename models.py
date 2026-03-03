from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tech_stack = db.Column(db.String(500))  # comma-separated
    github_url = db.Column(db.String(500))
    live_url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    category = db.Column(db.String(100))
    featured = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def tech_list(self):
        return [t.strip() for t in self.tech_stack.split(',')] if self.tech_stack else []

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'tech_stack': self.tech_list(),
            'github_url': self.github_url,
            'live_url': self.live_url,
            'image_url': self.image_url,
            'category': self.category,
            'featured': self.featured,
        }


class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))  # Languages, Frameworks, Tools, etc.
    proficiency = db.Column(db.Integer, default=80)  # 0-100
    order = db.Column(db.Integer, default=0)


class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))  # "Present" if current
    location = db.Column(db.String(200))
    order = db.Column(db.Integer, default=0)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(300))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(300), unique=True, nullable=False)
    summary = db.Column(db.Text)
    content = db.Column(db.Text)
    cover_image = db.Column(db.String(500))
    tags = db.Column(db.String(500))  # comma-separated
    published = db.Column(db.Boolean, default=False)
    featured = db.Column(db.Boolean, default=False)
    read_time = db.Column(db.Integer, default=5)  # minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def tag_list(self):
        return [t.strip() for t in self.tags.split(',')] if self.tags else []

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'summary': self.summary,
            'tags': self.tag_list(),
            'published': self.published,
            'featured': self.featured,
            'read_time': self.read_time,
            'created_at': self.created_at.strftime('%d %b %Y'),
        }


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    issuer = db.Column(db.String(200))   # e.g. "Google", "HackerRank"
    date = db.Column(db.String(50))      # e.g. "Mar 2024"
    category = db.Column(db.String(100)) # Certificate, Award, Hackathon, etc.
    icon = db.Column(db.String(10), default='🏆')  # emoji icon
    link = db.Column(db.String(500))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)

    @staticmethod
    def get(key, default=''):
        s = SiteSettings.query.filter_by(key=key).first()
        return s.value if s else default

    @staticmethod
    def set(key, value):
        s = SiteSettings.query.filter_by(key=key).first()
        if s:
            s.value = value
        else:
            s = SiteSettings(key=key, value=value)
            db.session.add(s)
        db.session.commit()
