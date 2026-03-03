"""Run once to create tables and seed sample data."""
from app import app, seed_data
from models import db

with app.app_context():
    db.create_all()
    seed_data()
    print("✓ Database initialized with sample data.")
    print("✓ Admin login: username=admin  password=admin123")
    print("✓ Visit http://localhost:5000/admin to manage your portfolio")
