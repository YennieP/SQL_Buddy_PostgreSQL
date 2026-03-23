# SQL Buddy 🧠

> **[中文文档](README.zh.md)** | English

An AI-powered SQL learning platform where students practice SQL through interactive problems, scenario-based challenges, and a natural language query assistant.

**Live Demo:** [your-app.railway.app](https://your-app.railway.app)

> **Original MySQL version:** [SQL_Buddy (MySQL + GCP)](https://github.com/YennieP/SQL_Buddy)

---

## Features

- **Role-based system** — Students, Mentors, and Admins each have dedicated dashboards and permissions
- **AI-generated problems** — Mentors generate SQL problems from custom real-world scenarios using GPT-4o-mini
- **Natural language SQL assistant** — Students ask questions in plain English; the AI generates and executes safe read-only SQL queries against the live database
- **Structural SQL evaluator** — Submissions are scored using an F1 algorithm across FROM / SELECT / WHERE clauses, giving partial credit for partially correct answers
- **Mentor feedback system** — Mentors review student attempts and leave targeted written feedback
- **Resource library** — Mentors upload articles, videos, and tutorials tagged by SQL topic
- **Admin panel** — Full user management with role assignment, ban/unban, and account editing

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Django 4.2 |
| Database | PostgreSQL (Railway) |
| AI | OpenAI GPT-4o-mini API |
| Frontend | Django Templates, Bootstrap 5 |
| Deployment | Railway |
| Auth | Session-based with Django password hashing (`make_password` / `check_password`) |

---

## Project Structure

```
SQL_Buddy/
│
├── sqlbuddy/                      # Django project config
│   ├── settings.py                # Environment-based settings (dev / prod)
│   ├── urls.py                    # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                          # Main Django application
│   ├── models.py                  # 15 models (managed=False, maps to existing schema)
│   │
│   ├── views/                     # Views split by role
│   │   ├── auth_views.py          # Login, logout, register
│   │   ├── student_views.py       # Dashboard, problems, attempts, scenarios, NL query
│   │   ├── mentor_views.py        # Problem management, feedback, resources, analytics
│   │   ├── admin_views.py         # User management (ban / unban / create)
│   │   └── notification_views.py  # Notification center
│   │
│   ├── utils/                     # Business logic
│   │   ├── nl2sql.py              # Natural language → SQL via OpenAI (SELECT-only enforced)
│   │   ├── sql_evaluator.py       # F1-based structural scoring algorithm
│   │   └── scenario_generator.py  # AI problem generation from student scenarios
│   │
│   ├── templates/core/            # HTML templates (Bootstrap 5)
│   │   ├── base.html
│   │   ├── base_dashboard.html
│   │   ├── student_dashboard.html
│   │   ├── mentor_dashboard.html
│   │   ├── admin_dashboard.html
│   │   ├── browse_problems.html
│   │   ├── problem_detail.html
│   │   ├── nl_query.html          # Chatbot UI
│   │   └── ...
│   │
│   ├── static/                    # CSS, JS, images
│   ├── urls.py                    # App-level routing (30+ routes)
│   ├── context_processors.py      # Injects session data into all templates
│   └── apps.py
│
├── db/                            # Database scripts (PostgreSQL)
│   ├── dbDDL.sql                  # Schema: 15 tables, 3 views, 5 triggers
│   ├── dbDML.sql                  # Seed data: 22 users, 10 problems, 30 attempts
│   ├── dbSQL.sql                  # 8 analytical queries (JOIN, CTE, subquery, window fn)
│   └── dbDROP.sql                 # Full teardown script
│
├── staticfiles/                   # Collected static files (auto-generated, git-ignored)
├── manage.py
├── requirements.txt
├── Procfile                       # Gunicorn start command for Railway
├── railway.json                   # Railway deployment config
├── .env.example                   # Environment variable template
├── .gitignore
├── README.md                      # English documentation (this file)
└── README.zh.md                   # 中文文档
```

---

## Database Schema

15 tables with a User inheritance pattern (User → Student / Mentor / Admin):

```
User ──┬── Student ──── Scenario ──── Problem ──── Have_topic ── Topic
       ├── Mentor  ──────────────────────────┘
       └── Admin                      └────── Attempt

Mentor ──── Resource ──── ResourceTopic ── Topic
                      └── Access ── Student

User ──── Send ──── Notification ──── Receive ──── User
```

Key design decisions:
- `managed=False` on all models — Django reads from the schema without managing migrations
- `Attempt` uses a composite primary key `(student_id, problem_id, attempt_no)`
- 3 database Views power the dashboards: `StudentPerformanceSummary`, `MentorActivityDashboard`, `ProblemStatistics`
- 5 triggers enforce data integrity: feedback requirement, cascade counts, high-score notifications, deletion guard

---

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 15+

### Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/your-username/sql-buddy.git
cd sql-buddy

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate.bat       # Windows CMD
venv\Scripts\Activate.ps1       # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env — fill in DB credentials and OpenAI API key

# 5. Initialize the database
psql -U postgres -c "CREATE DATABASE sqlbuddy;"
psql -U postgres -d sqlbuddy -f db/dbDDL.sql
psql -U postgres -d sqlbuddy -f db/dbDML.sql

# 6. Start the development server
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000)

### Demo Accounts

Register a new account at `/register/` to get started immediately, or use the seed data accounts after running the password migration script.

| Role | Email |
|------|-------|
| Student | pizza4life@email.com |
| Mentor | copypaste@email.com |
| Admin | dank.memes@email.com |

---

## Environment Variables

Copy `.env.example` to `.env`:

```env
# Django
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL (local)
DB_NAME=sqlbuddy
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

> In production, Railway automatically injects `DATABASE_URL` — individual `DB_*` variables are not needed.

---

## Deployment (Railway)

1. Push code to GitHub
2. Create a Railway project → **Add PostgreSQL** service
3. Connect your GitHub repo — Railway auto-detects `Procfile`
4. Set variables in Railway dashboard: `OPENAI_API_KEY`, `SECRET_KEY`, `DEBUG=False`
5. `DATABASE_URL` is injected automatically — no manual DB config needed
6. Initialize the schema via Railway's PostgreSQL shell:
   ```sql
   \i db/dbDDL.sql
   \i db/dbDML.sql
   ```

---

## AI Features

### Natural Language Query (`/student/nl_query/`)
Students type plain English questions (e.g. *"Show my last 5 attempts"*). The system sends the query + schema context to GPT-4o-mini, receives a validated SQL statement, executes it, and returns results in a chat-style UI. Only `SELECT` statements are permitted — a keyword blocklist and schema whitelist enforce read-only access.

### Scenario Problem Generator (`/student/scenarios/<id>/generate/`)
Students describe a real-world scenario; GPT-4o-mini generates difficulty-appropriate SQL problems with correct reference answers tailored to that context.

---

## Design Decisions

**Why `managed=False`?**
The schema was designed first as a database course project. Django models map to existing tables without owning migrations, keeping the SQL schema as the single source of truth.

**Why session-based auth instead of Django's built-in?**
The `User` table is custom (not `auth_user`), so we use manual session management with Django's `make_password` / `check_password` for secure password handling.

**Why F1 scoring for SQL evaluation?**
String comparison fails on semantically equivalent queries. The F1 evaluator scores FROM (40%), SELECT (30%), and WHERE (30%) independently, giving partial credit and avoiding false negatives from trivial differences like column ordering.