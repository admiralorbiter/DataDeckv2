# DataDeck v2 (Flask Rewrite)

DataDeck v2 is a Flask rewrite of the original Django-based DataDeck classroom app. It enables teachers to run classroom sessions where students upload data visualizations (images), react with badges, and comment. District-level observers can browse activity across teachers in their district.

This repository currently contains a runnable Flask outline (starter) plus planning docs for the full rewrite and migration.

## Key Features (target)
- Sessions lifecycle (create, list, pause, archive/unarchive, delete)
- Student generation with printable PIN cards
- Media uploads (single image and multi-image projects)
- Reactions/badges and comments
- Observer dashboard (district-scoped visibility)
- Admin dashboard (districts, observers, teacher management)

See `docs/features.md` and `docs/FLASK_REWRITE_PLAN.md` for full scope.

## Accounts

See `docs/ACCOUNTS.md` for roles, permissions, and account creation.
All roles use a unified login at `/login`:
- Admin/Staff/Teacher authenticate via Flask-Login
- Observer authenticates via the same form; on success, an observer session is established and redirected to `/observer/dashboard`
- Logout at `/logout` clears both Flask-Login user and observer session

## Repository Layout (current)
- `app.py` — Flask app bootstrap (dev server)
- `config.py` — Config classes for dev/test/prod
- `models/` — SQLAlchemy models (`User`, `Student`, `School`, `District`)
- `routes/` — Blueprints (`auth`, `main`, `admin`, `profile`)
- `forms.py` — Flask-WTF forms
- `templates/`, `static/` — HTML/CSS
- `docs/` — Architecture, migration and execution plans
- `tests/` — Model tests (early draft)

## Prerequisites
- Python 3.10+ (3.11 recommended)
- Windows, macOS, or Linux

## Quickstart (Development)
1) Create and activate a virtual environment
   - Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - macOS/Linux:
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Configure environment
- Create a `.env` file (optional, recommended):
  - `SECRET_KEY=change-me`
  - `FLASK_ENV=development` (or leave unset for default dev config)
  - `DATABASE_URL=postgresql://user:pass@localhost:5432/datadeck` (optional; defaults to local SQLite in dev)

4) Initialize the database
- The app uses `db.create_all()` on startup. Simply run the app once to create tables automatically.

5) Run the app
```bash
python app.py
```
App will start on `http://localhost:5000`.

6) Create an admin user (interactive)
```bash
python create_admin.py
```

## Testing
```bash
pytest -q
```

## Development Tools

### Test Data
Create sample data for testing:
```bash
make test-data
# Creates admin (jonlane/nihilism), teachers, observers, and sessions
```

### Accessibility Audit
Run WCAG AA compliance check:
```bash
make a11y-audit
# Checks forms, color contrast, semantic HTML, and ARIA attributes
```

### Available Make Commands
```bash
make run          # Start Flask server
make test         # Run pytest
make test-data    # Create test database
make a11y-audit   # Accessibility audit
make lint         # Run pre-commit on all files
make format       # Format code (black + isort)
```

## Pre-commit hooks
Install and enable pre-commit to auto-format and lint on commit.

Setup (once):
```bash
pip install pre-commit
pre-commit install
```

Run on all files:
```bash
pre-commit run --all-files
```

The configured hooks include Black, isort, Flake8, and basic whitespace/YAML/TOML/JSON checks. See `.pre-commit-config.yaml`.

Flake8 uses `max-line-length=88` (Black-compatible) as configured in `.flake8`.

## Configuration
- `DevelopmentConfig` uses SQLite via `SQLALCHEMY_DATABASE_URI = 'sqlite:///your_database.db'`.
- `ProductionConfig` reads `DATABASE_URL` and normalizes `postgres://` → `postgresql://`.

## Migration & Rewrite Docs
- Architecture (current Django): `docs/ARCHITECTURE.md`
- Flask rewrite plan: `docs/FLASK_REWRITE_PLAN.md`
- Work breakdown (epics → stories → subtasks): `docs/WBS.md`
- Data migration plan: `docs/DATA_MIGRATION.md`
- Future opportunities: `docs/FUTURE_OPPORTUNITIES.md`
- Sequence flows: `docs/SEQUENCE_FLOWS.md`

## Roadmap & Execution
- The day-to-day, actionable task plan lives in `docs/PROJECT_PLAN.md` (milestones with checklists).
- High-level scope and decisions live in the docs above.

## Notes
- Database: Schema is managed via `db.create_all()` for simplicity. Tables are created automatically on app startup.
- Storage: local filesystem in dev; S3-compatible storage planned for prod.

## License
TBD.
