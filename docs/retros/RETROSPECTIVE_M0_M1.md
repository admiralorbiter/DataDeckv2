## Retrospective — M0 (Bootstrap & Tooling) and M1 (Data Model & Seed)

Date: YYYY-MM-DD

### Executive summary

- **M0/M1 are largely complete and coherent**: App factory, blueprints, CSRF, auth scaffolding, and core models are implemented. Seed script, observer flow, and admin dashboard exist with basic operations.
- **Before M3, address a handful of correctness/clarity items**: session uniqueness enforcement, admin edit coercion, docs alignment for unified login, test reliability on Windows, and plan Alembic.
- **Action items** below capture pre-M3 must-do’s and nice-to-haves.

### M0 — Bootstrap & Tooling

- **What’s good**
  - `create_app` initializes `db`, `LoginManager`, `CSRF`, sets `login_view` to `auth.login` (`app.py`).
  - Blueprints registered centrally via `routes/__init__.py`; helper `create_blueprint` in `routes/base.py` keeps modules minimal.
  - CSRF enabled globally; disabled in tests via `TestingConfig`.
  - `.env` support via `python-dotenv` early in bootstrap.
  - Basic developer ergonomics via `Makefile` and `requirements.txt`.

- **Gaps / fixes**
  - Migrations not yet set up (using `db.create_all()`). Introduce Alembic before evolving schema in M3+.
  - Config safety:
    - Default `SECRET_KEY` is dev-safe only. Ensure production provides a strong secret.
    - `ProductionConfig.SQLALCHEMY_DATABASE_URI` may be `None` if `DATABASE_URL` is missing; fail-fast with a clear error.
  - Testing DB: `sqlite:///test_database.db` (file) can cause Windows locking/flake. Prefer `sqlite:///:memory:` or tmp files per run.
  - Logging: Plan structured logging and request IDs (M11), but minimal logger config now would help.

- **Future opportunities**
  - Friendly error handlers for 400/401/403/404/500 with JSON/HTML parity (planned M11).
  - Cookie settings for prod (Secure, HttpOnly, SameSite) and optional remember-me toggle.
  - CI workflow (lint + tests + coverage) as documented in README but not yet present.

### M1 — Data Model & Seed

- **What’s good**
  - Models implemented: `User` (+roles), `Observer` and `Student` via joined-table inheritance; `District`, `School`, `Session`, `Media`, `Comment`, `StudentMediaInteraction`.
  - Useful role helpers (`is_admin`, etc.), `requires_school_info()` and `validate()` enforcing teacher/observer school/district presence.
  - Indexes and constraints present for common access patterns (e.g., media/session, student-media unique interaction).
  - Seed script creates a realistic dev baseline: district, school, teacher, session, N students with hashed pins.

- **Gaps / fixes**
  - Session uniqueness (teacher + section + active) not enforced. There is an index (`ix_sessions_created_by_section_archived`), but no uniqueness or service-level check. Implement application-level validation; add a unique constraint in Postgres later if desired.
  - `Session.module` is a string enum of {"2","4"}. Clarify semantics and consider a Python Enum for portability and form validation.
  - Admin edit coercion: in `routes/admin.py`, `school_id`/`district_id` are taken from `request.form` (strings). Blank values should become `None`; non-blank should be coerced to `int` before `validate()` to avoid type issues.
  - Admin create flow uses manual parsing while rendering `FlaskForm`. Consider using the form for validation to surface errors nicely and keep consistency.
  - Students: `User.password_hash` is required and used as a PIN hash for students; document that student auth is session-only (PIN-based), not email+password.
  - `Media.submitted_password` presence is unclear; document or remove if legacy.

- **Future opportunities**
  - Add `__repr__` for `User`, `Session`, etc. to improve debugging/logs.
  - Denormalized `User.school`/`User.district` names are pragmatic now but can drift; plan a post-MVP strategy (sync or removal).

### Auth, routes, and templates

- **What’s good**
  - Unified `/login` handles email-first then username; observer session via `session["observer_id"]`; others via Flask-Login.
  - `/logout` clears both observer session and Flask-Login; redirects match expectations.
  - Observer dashboard enforces district isolation; school view lists teachers in-district.
  - Admin dashboard lists users and provides create/edit/delete (create/delete gated to admin).
  - Profile route supports password changes by role template.

- **Gaps / fixes**
  - Docs alignment: `docs/ACCOUNTS.md` mentions observer login at `/observer/login`; current code redirects legacy routes to `/login`. Update docs to reflect unified login.
  - Authorization clarity: Staff can view admin dashboard; only admins can create/delete users. Ensure policy is stated in docs.

### Testing and developer experience

- **What’s good**
  - Tests cover model uniqueness/relationships, observer auth, admin flows, profile password change, and a student-only route.
  - CSRF disabled for tests; fixtures handle schema lifecycle.

- **Gaps / fixes**
  - Windows test runner produced no output locally. Common causes: missing venv activation or dependencies; file-locked SQLite. Use venv, in-memory SQLite for tests, and re-run.
  - Add GitHub Actions workflow for lint/tests to prevent regressions.

### Security

- **Strengths**
  - Passwords and pins hashed with `werkzeug.security`.
  - CSRF protection globally enabled.

- **Fixes**
  - Enforce production `SECRET_KEY` and DB URI at startup.
  - Set secure cookie flags for production.

### Pre‑M3 readiness checklist (recommended)

- [ ] Implement session uniqueness validation for (created_by_id, section) when `is_archived=False` with user-friendly error.
- [ ] Define `module` semantics (Enum + form validation + help text).
- [ ] Fix admin edit coercion for `school_id`/`district_id` (blank→None, else `int`).
- [ ] Align `docs/ACCOUNTS.md` to unified login and clarify observer flow.
- [ ] Add note on student PIN hashing and session-only student auth to docs.
- [ ] Switch tests to in-memory SQLite (or tmp file) for reliability; document Windows guidance.
- [ ] Introduce Alembic (create baseline migration matching current schema).
- [ ] Add CI (lint + tests + coverage threshold).
- [ ] Decide fate of `Media.submitted_password` (document or remove).

### Questions for feedback

- **Session duplicates**: If a teacher starts a session for a section that already has an active one, should we block, auto-archive the old one, or prompt?
- **`module` values**: Are only "2" and "4" valid? Should we model these as a Python Enum with human-readable labels in the UI?
- **Student auth**: Confirm students use PIN-only (no email/password). Any need for self-service PIN reset, or always teacher-regenerated?
- **Observer profile**: Should observers have a password-change page? Currently they aren’t Flask-Login users; we’d need a separate flow or unify observers into Flask-Login.
- **Staff vs admin**: Should staff be able to create users, or is that admin-only as implemented?
- **Denormalized names**: Keep `User.school`/`User.district` strings long term? If yes, do we need sync to keep them aligned with FKs?
- **Windows dev target**: If Windows is primary, we’ll add a short section in README for PowerShell commands and testing tips.

### Environment note (Windows test runner)

- Activate venv and install:
  - PowerShell: `python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt`
- Prefer in-memory DB for tests: set `TestingConfig.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"`.
- Run tests: `pytest -q -rA -s`.

### Next steps

- After you confirm the feedback questions, we will:
  - Implement session uniqueness + `module` enum + Start Session form.
  - Fix admin edit coercion and update docs.
  - Add Alembic baseline and CI workflow.
