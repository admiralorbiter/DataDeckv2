## Project Plan — DataDeck v2 (Flask Rewrite)

This is the actionable, task-oriented plan to deliver the Flask rewrite. It translates the high-level `docs/FLASK_REWRITE_PLAN.md` and `docs/WBS.md` into concrete, checkable tasks.

### Objectives
- Ship an MVP that reaches feature parity for core classroom flows: sessions, students, uploads, reactions, comments, observer view.
- Improve security (hashed PINs, CSRF, secure cookies), performance (pagination, indexes), and maintainability (blueprints + services, tests, CI).
- Migrate data from Django to Flask with minimal downtime.

### Milestones

#### M0 — Bootstrap & Tooling
- [x] App factory `create_app` with `Development/Testing/Production` configs
- [x] `.env` loading via python-dotenv
- [x] Extensions: SQLAlchemy, Flask-Login, Flask-WTF, CSRF
- [x] Pre-commit hooks (black, isort, flake8) and basic CI
- [x] Makefile tasks: run, test, lint, format, precommit, setup

Acceptance: `flask run` boots; `pytest` green on a clean DB; pre-commit enforced locally and in CI.

#### M1 — Data Model & Seed
- [x] Implement models (SQLAlchemy): `User`, `Observer`, `District`, `School`, `Session`, `Student`, `Media`, `Comment`, `StudentMediaInteraction`
- [x] Add indexes/constraints per `docs/FLASK_REWRITE_PLAN.md`
- [x] Schema creation via app startup (`db.create_all()`)
- [x] Dev seed script (teachers, session, students)
- [x] Pytest factories for core entities

Acceptance: Schema creates successfully via `db.create_all()`; seed creates demo teacher+session+students; factories generate valid objects.

#### M2 — Authentication & Roles
- [x] Teacher/Admin login/logout with Flask-Login
- [x] Observer login/logout (separate session namespace)
- [x] Decorators: `@observer_required`, `@student_required` (session-based)
- [x] Password change (admin/staff/teacher)
- [x] Role-based navbar and access checks
- [x] Document account types and creation paths (`docs/ACCOUNTS.md`)

Acceptance: Valid credentials redirect to dashboards; protected routes gated by role; password change persists.

#### M3 — Sessions Module 🔄 PARTIALLY COMPLETED
- [x] StartSessionForm (hour/section, module, character_set)
- [x] Uniqueness rule (teacher, section, active) enforced
- [x] Create session → generate 20 students (name + PIN + character)
- [x] Basic session list and detail pages
- [x] Archive/unarchive actions
- [x] Module system with admin-configurable curriculum modules
- [ ] Session filtering (by status, module, date)
- [ ] Session pagination for large datasets
- [ ] Session delete functionality
- [ ] Session pause/unpause functionality
- [ ] Select # of students to generate
- [ ] Media filtering within sessions (graph_tag, variable_tag)


Acceptance: ✅ Core session creation and management works; ❌ Advanced filtering and pagination still needed.

#### M3.5 — UI/Branding & Frontend Foundation
- Establish brand system and tokens
  - Define CSS custom properties (colors, spacing, typography) in `static/css/brand.css`
  - Document palette and type scale alignment with `docs/UI_UX_DESIGN.md`
- Normalize base layout and navigation
  - Ensure a single `templates/base.html` shell (skip-link, header, breadcrumb slot, container)
  - Refactor `templates/nav.html` for role-based items and active state styling
- Component library (Jinja macros) under `templates/_components/`
  - Buttons (primary/secondary/destructive/ghost)
  - Form controls (input/select/textarea) with error rendering
  - Cards, tables, badges, modals, pagination, flash/toasts
- Utilities and CSS architecture
  - Add lightweight utility classes (spacing, flex/grid, text) or adopt Bootstrap 5 (document decision)
  - Organize CSS: import order, file structure, and naming conventions (BEM/utility mix)
- Responsiveness and accessibility
  - Mobile-first breakpoints; responsive nav patterns
  - Focus outlines, skip-link, ARIA labels; keyboard navigation across core views
- Icons and assets
  - Choose icon set (Heroicons/Font Awesome) and integrate via static assets/CDN
  - Add logo placeholder and favicon; document asset locations
- Apply foundation to core pages
  - Update: `templates/login.html`, `templates/index.html`, `templates/sessions/list.html`, `templates/sessions/detail.html`, `templates/admin/dashboard.html`
- Style guide
  - Create `templates/styleguide.html` showcasing tokens and components (dev-only link)
- Non-functional targets
  - Accessibility (axe) critical issues = 0 on updated pages
  - Lighthouse: Accessibility ≥ 90, Best Practices ≥ 90; CSS bundle ≤ 200KB uncompressed

Acceptance: Base tokens load on all pages; component macros exist and are used in ≥3 pages; layouts are responsive without horizontal scroll at common breakpoints; axe reports no critical issues on key pages.

Progress Update:
- Completed: tokens in `brand.css`, base/nav refactor (two-row, sticky, centered), macros for buttons/forms/alerts/cards/pagination, style guide, refactor of `login.html`, `index.html`, `sessions/list.html`, `sessions/detail.html`, `admin/dashboard.html`, and `sessions/start.html`. Global flash messages wired in base; favicon added. Student login page added with district/school scoping and backend validation; logout link surfaces in header when applicable.
- Remaining for M3.5: accessibility/Lighthouse pass and fixes; optional teacher sessions dropdown in nav; sessions list pagination once backend paging lands.

#### M4 — Students
- [ ] Student list (per teacher)
- [ ] Delete with ownership checks
- [ ] Export printable PIN cards (PDF)

Acceptance: CRUD works; PDF opens with correct layout.

#### M5 — Media
- [ ] Upload image (validate type/size), generate title from tags
- [ ] Edit tags and recompute title
- [ ] Delete media (permission + file removal)
- [ ] Project upload (min 3 images) with gallery view

Acceptance: Upload persists; edit updates title; delete removes DB row and file; gallery renders.

#### M6 — Posts & Comments
- [ ] Post detail shows media, poster, counts
- [ ] Nested comments (replies), attribution (admin/student)
- [ ] Increment `StudentMediaInteraction.comment_count` on student comment

Acceptance: Replies render nested; counts are accurate after actions.

#### M7 — Reactions/Badges
- [ ] Decide reaction semantics (toggle vs single-select) and implement consistently
- [ ] Endpoint: `POST /media/<id>/react/<type>` returns `{success, counts, user_like}`
- [ ] UI updates without full reload

Acceptance: Consistent behavior across session grid and post; counts update live.

#### M8 — Admin & Observer Dashboards
- [ ] Admin: District CRUD + toggle; Observer management (create/deactivate/password)
- [ ] Teacher district assignment/update
- [ ] Observer dashboard: district overview (teachers, sessions, recent media)

Acceptance: Admin operations succeed with flash messages; observer sees only their district.

#### M9 — Storage & Static
- [ ] Storage abstraction (local dev, S3-compatible prod)
- [ ] URL builder that returns absolute media URLs for templates
- [ ] Optional: image resizing/thumbnail pipeline hooks

Acceptance: Files saved/retrieved via unified API; templates render with absolute URLs.

#### M10 — Background Jobs
- [ ] Clear expired sessions daily (not paused, >7 days)
- [ ] Job wiring (RQ/Celery) with schedule
- [ ] Unit test selection logic

Acceptance: Job logs and deletes; test covers selection logic.

#### M11 — Observability & Errors
- [ ] JSON/structured logging with request IDs
- [ ] Error handlers for 400/401/403/404/500 (HTML + JSON shape)
- [ ] Optional: Sentry integration

Acceptance: Logs include route, latency, status, correlation ID; friendly HTML pages and consistent JSON errors.

#### M12 — Testing & CI
- [ ] Model tests (constraints, methods, relationships)
- [ ] Route tests (auth, sessions, media, posts, reactions, admin, observer)
- [ ] File upload tests (tmp storage)
- [ ] GitHub Actions: lint + test + coverage gate (≥80%)

Acceptance: 80%+ global coverage; CI is green.

#### M13 — Migration & Cutover
- [ ] Export scripts from Django DB → NDJSON/CSV
- [ ] Import scripts into Flask DB via SQLAlchemy
- [ ] File migration (copy/upload) and URL rewrite
- [ ] Verification (row counts, referential integrity, sample UI smoke tests)
- [ ] Go/No-Go checklist and rollback plan

Acceptance: Staging migration passes verification; cutover window executed safely.

### Execution Order (high level)
M0 → M1 → M2 → M3 → M3.5 → M4 → M5 → M6 → M7 → M8 → M9 → M10 → M11 → M12 → M13. Parallelize where safe (tests/CI can start early).

### Weekly Next Actions (updated post-M3)
- [x] Convert to app factory (`create_app`) and relocate config loading
- [x] Fix `login_view` endpoint; verify auth redirect works
- [x] Add observer auth blueprint stub with routes and templates (implemented with unified login)
- [x] Implement `Session` model + uniqueness logic (service + form validation)
- [x] Implement `Student` generation service (name, PIN hash, avatar path)
- [x] Seed CLI to create demo teacher + session + 20 students
- [x] Session page scaffold with pagination and filters
- [x] Module system with admin CRUD operations
- [x] Comprehensive test suite with 100% passing tests
- [x] Set up pre-commit (black, isort, flake8); wire basic GitHub Actions
  - How-to: `pip install pre-commit && pre-commit install && pre-commit run --all-files`

### UI/UX Considerations for Future Milestones

#### Design System & Consistency
- Establish consistent color palette, typography, and spacing
- Create reusable component patterns for forms, buttons, cards
- Implement responsive design principles for mobile/tablet support
- Consider accessibility (WCAG AA compliance) from the start

#### User Experience Flow
- Streamlined session creation with progressive disclosure
- Intuitive navigation with clear breadcrumbs and context
- Real-time feedback for user actions (loading states, success/error messages)
- Keyboard navigation support for accessibility

#### Visual Hierarchy & Information Architecture
- Clear visual distinction between roles (teacher, admin, observer, student)
- Logical grouping of related actions and information
- Consistent iconography and visual cues
- Effective use of white space and visual breathing room

### Definition of Done
- Unit and integration tests written and green
- Linting and type checks pass (where applicable)
- Accessible, responsive templates for primary flows
- Logs/errors are structured; sensitive data not logged
- Documentation updated (`README.md`, `docs/*`)

### Risks & Mitigations
- Data migration complexity → start scripts early, verify on staging, keep rollback plan
- Media storage variance → standardize via storage abstraction and deterministic keys
- Classroom performance → paginate, index, and limit payloads; consider caching hot lists
- Auth boundary clarity → separate observer auth/session; explicit decorators

### References
- `docs/ARCHITECTURE.md`
- `docs/FLASK_REWRITE_PLAN.md`
- `docs/WBS.md`
- `docs/DATA_MIGRATION.md`
- `docs/SEQUENCE_FLOWS.md`
