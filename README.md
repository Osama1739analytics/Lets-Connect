# Peer-2-Professional Guidance App ("Let's Connect")

A Django web application that connects students (mentees) with professionals (mentors). It includes custom authentication, role-based views, and an enhanced admin dashboard.

## Overview
- Framework: Django (project: `p2p`, app: `home`)
- Database: SQLite (default `db.sqlite3`)
- Time zone: Asia/Karachi
- Custom user model: `home.CustomUser` (with role: mentee/mentor)

## Features / Modules
Working now
- Admin module
  - Custom admin site at `/admin/` with statistics on users and sessions
  - Manage users and mentoring sessions
- Authentication module
  - Sign up (`/signup/`) with role selection (mentee/mentor)
  - Login (`/login/`), Logout (`/logout/`)
- Profile module
  - Profile page (`/profile/`) with role badges and basic info
- Home module
  - Role-aware landing page at `/` (different content for mentee vs mentor)

Present but not yet user-facing
- Mentor module (role exists; no dedicated public UI)
- Mentee (student) module (role exists; no dedicated public UI)
- Session management public UI (model and admin exist; no end-user pages yet)

## Project structure
```
Peer-2-Professional Guidance App/
├─ manage.py
├─ db.sqlite3
├─ p2p/
│  ├─ settings.py
│  ├─ urls.py
│  ├─ views.py
│  ├─ wsgi.py / asgi.py
├─ home/
│  ├─ admin.py        # custom admin site and registrations
│  ├─ apps.py
│  ├─ forms.py        # signup & login forms
│  ├─ models.py       # CustomUser, Session
│  ├─ urls.py         # not wired into root urls by default
│  ├─ views.py        # currently empty
│  ├─ migrations/
├─ templates/
│  ├─ index.html
│  ├─ login.html
│  ├─ signup.html
│  ├─ profile.html
│  └─ admin/          # admin templates
└─ static/            # static assets (referenced via STATIC_URL)
```

## Tech stack
- Python 3.x
- Django 5.x

## Getting started
1) Clone or open the project folder `Peer-2-Professional Guidance App`

2) Create and activate a virtual environment
- Windows (PowerShell)
  ```pwsh
  py -m venv .venv
  .\.venv\Scripts\Activate
  ```
- macOS/Linux
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

3) Install dependencies
- If you don't have a requirements file, install Django directly:
  ```bash
  pip install "Django>=5,<6"
  ```

4) Database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

5) Create a superuser (to access the admin)
```bash
python manage.py createsuperuser
```

6) Run the development server
```bash
python manage.py runserver
```

Visit:
- Home: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Configuration notes
- Settings module: `p2p.settings`
- Installed apps include `home.apps.HomeConfig`
- Custom user model: `AUTH_USER_MODEL = 'home.CustomUser'`
- Templates directory is set to `templates/` at project root
- Static URL: `/static/` (ensure your static files are under `static/`)
- For production, set `DEBUG = False` and configure `ALLOWED_HOSTS`

## URL routes (public)
Defined in `p2p/urls.py`:
- `/` → Home (role-aware landing page)
- `/login/` → Login
- `/signup/` → Sign up (select mentee/mentor)
- `/profile/` → Profile (requires login)
- `/logout/` → Logout
- `/admin/` → Custom admin site

Note: `home/urls.py` exists but is not included in the root URLConf by default.

## Data models (summary)
`home.models.CustomUser` (extends `AbstractUser`)
- `full_name`, `contact_number`, `age`
- `user_type` ∈ {`mentee`, `mentor`}
- Helper methods: `is_mentee()`, `is_mentor()` and session accessors

`home.models.Session`
- `mentor` → `CustomUser` (limit to mentors)
- `mentee` → `CustomUser` (limit to mentees)
- `title`, `description`, `session_type`, `status`, `scheduled_date`, `duration_minutes`
- Status: scheduled/completed/cancelled/in_progress
- Type: one_on_one/group/workshop/consultation

## Admin site
A custom admin site is registered in `home.admin` and exposed at `/admin/`.
It provides:
- Quick stats (mentee count, mentor count, sessions, recent sessions)
- User admin with role badges and session stats per user
- Session admin with filters and search

## Templates
- `templates/index.html`: landing page; adjusts content based on `user.is_mentee` / `user.is_mentor`
- `templates/login.html`: login form (uses `home.forms.LoginForm`)
- `templates/signup.html`: sign-up form (uses `home.forms.CustomUserCreationForm`)
- `templates/profile.html`: profile with role badges and basic info

## Development tips
- Because a custom user model is used, run migrations before creating the superuser
- If you change user fields, make and apply new migrations
- To add a public UI for sessions, create views and templates around `home.models.Session` and wire URLs in `p2p/urls.py`

## Roadmap / Next steps
- Public session management UI (list, create, join sessions)
- Dedicated mentor/mentee dashboards
- Email verification and password reset flows
- Pagination and search for users/sessions
- Static files pipeline and deployment settings

---
If you need additional docs (API reference, diagrams, or deployment guide), let me know and I can add them under a `docs/` folder.
