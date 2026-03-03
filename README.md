# Shubh Shrivastava — Portfolio

A full-stack personal portfolio built with **Flask + SQLAlchemy**, featuring an admin CMS, contact form, and a dark luxury editorial design.

---

## Features

- **Public Portfolio** — hero, about, experience timeline, projects grid with filter, skills with animated bars, contact form
- **Admin Dashboard** — `/admin` — manage all content: projects, skills, experience, messages, settings
- **Contact Form** — stores messages in DB + optional email notification
- **Database-driven** — all content editable via admin panel, no redeploy needed
- **One-command seed** — sample data pre-loaded on first run

---

## Quick Start (Local)

```bash
# 1. Clone / unzip the project
cd shubh-portfolio

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your values (SECRET_KEY, admin password, etc.)

# 5. Initialize database (creates tables + sample data)
python init_db.py

# 6. Run the development server
python app.py
---
## Deployment

### Render (Free tier)
1. Push to GitHub
2. New Web Service → connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add environment variables from `.env.example`
6. Add a one-off command: `python init_db.py`

### Railway
1. Push to GitHub, import in Railway
2. Set env vars in the dashboard
3. Run `python init_db.py` as a one-off job

### Heroku
```bash
heroku create your-portfolio
heroku config:set SECRET_KEY=xxx ADMIN_PASSWORD=xxx
git push heroku main
heroku run python init_db.py
```

### VPS (Nginx + Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
Point Nginx to `localhost:8000`.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session secret | `change-me` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///portfolio.db` |
| `ADMIN_USERNAME` | Admin login username | `admin` |
| `ADMIN_PASSWORD` | Admin login password | `admin123` |
| `SMTP_HOST` | Email SMTP host | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | Your email address | — |
| `SMTP_PASS` | Gmail App Password | — |
| `OWNER_EMAIL` | Where to receive contact notifications | — |

> **Gmail tip**: Use an [App Password](https://myaccount.google.com/apppasswords), not your regular password.

---

## Project Structure

```
shubh-portfolio/
├── app.py              # Flask routes & app factory
├── models.py           # SQLAlchemy models
├── init_db.py          # One-time DB seed script
├── requirements.txt
├── Procfile            # For Heroku/Railway/Render
├── .env.example
├── static/
│   ├── css/style.css   # All styles
│   └── js/main.js      # Scroll animations, interactivity
└── templates/
    ├── base.html
    ├── index.html      # Public portfolio page
    └── admin/
        ├── base_admin.html
        ├── login.html
        ├── dashboard.html
        ├── projects.html
        ├── project_form.html
        ├── skills.html
        ├── experience.html
        ├── messages.html
        └── settings.html
```

---

## Customising

All content is editable from `/admin`, but you can also:
- Change colours — edit CSS variables at the top of `style.css`
- Add new sections — extend `index.html` and add a route in `app.py`
- Switch to PostgreSQL — just change `DATABASE_URL` in `.env`
