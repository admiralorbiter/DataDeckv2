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

#### M1 — Data Model & Seed ✅ COMPLETED
- [x] Implement models (SQLAlchemy): `User`, `Observer`, `District`, `School`, `Session`, `Student`, `Media`, `Comment`, `StudentMediaInteraction`
- [x] Add indexes/constraints per `docs/FLASK_REWRITE_PLAN.md`
- [x] Schema creation via app startup (`db.create_all()`)
- [x] Dev seed script (teachers, session, students)
- [x] Pytest factories for core entities

Acceptance: Schema creates successfully via `db.create_all()`; seed creates demo teacher+session+students; factories generate valid objects.

#### M2 — Authentication & Roles ✅ COMPLETED
- [x] Teacher/Admin login/logout with Flask-Login
- [x] Observer login/logout (separate session namespace)
- [x] Decorators: `@observer_required`, `@student_required` (session-based)
- [x] Password change (admin/staff/teacher)
- [x] Role-based navbar and access checks
- [x] Document account types and creation paths (`docs/ACCOUNTS.md`)

Acceptance: Valid credentials redirect to dashboards; protected routes gated by role; password change persists.

#### M3 — Sessions Module ✅ COMPLETED
- [x] StartSessionForm (hour/section, module, character_set)
- [x] Uniqueness rule (teacher, section, active) enforced
- [x] Create session → generate 20 students (name + PIN + character)
- [x] Basic session list and detail pages
- [x] Archive/unarchive actions
- [x] Module system with admin-configurable curriculum modules
- [x] Session filtering (by status, module, date)
- [x] Session pagination for large datasets
- [x] Session delete functionality
- [x] Session pause/unpause functionality
- [x] Select # of students to generate
- [x] Media filtering within sessions (graph_tag, variable_tag)


Acceptance: ✅ **COMPLETE** - All core session management features implemented: creation, filtering, pagination, delete, pause/unpause, student count selection, and advanced media filtering with robust UI.

#### M3.5 — UI/Branding & Frontend Foundation ✅ COMPLETED
- [x] Establish brand system and tokens
  - [x] Define CSS custom properties (colors, spacing, typography) in `static/css/brand.css`
  - [x] Document palette and type scale alignment with `docs/UI_UX_DESIGN.md`
- [x] Normalize base layout and navigation
  - [x] Ensure a single `templates/base.html` shell (skip-link, header, breadcrumb slot, container)
  - [x] Refactor `templates/nav.html` for role-based items and active state styling
- [x] Component library (Jinja macros) under `templates/_components/`
  - [x] Buttons (primary/secondary/destructive/ghost)
  - [x] Form controls (input/select/textarea) with error rendering
  - [x] Cards, tables, badges, modals, pagination, flash/toasts
- [x] Utilities and CSS architecture
  - [x] Adopted Bootstrap 5 + custom brand tokens in `static/css/brand.css`
  - [x] Organized CSS: import order, file structure, and naming conventions
- [x] Responsiveness and accessibility
  - [x] Mobile-first breakpoints; responsive nav patterns
  - [x] Focus outlines, skip-link, ARIA labels; keyboard navigation across core views
  - [x] **WCAG AA compliant** - 0 accessibility issues found
- [x] Icons and assets
  - [x] Font Awesome integrated via CDN
  - [x] Logo and favicon added; documented in `docs/ACCESSIBILITY.md`
- [x] Apply foundation to core pages
  - [x] Updated: `templates/login.html`, `templates/index.html`, `templates/sessions/list.html`, `templates/sessions/detail.html`, `templates/admin/dashboard.html`, `templates/sessions/start.html`
- [x] Style guide
  - [x] Created `templates/styleguide.html` showcasing tokens and components
- [x] Role-based navigation
  - [x] Two-row nav (logged-out: Student vs Teacher/Admin login)
  - [x] Dynamic dropdowns: teachers (their sessions), observers (district sessions), admin (multi-district view)
  - [x] Student login with district/school scoping
- [x] Non-functional targets
  - [x] Accessibility: **0 critical issues** across all core pages
  - [x] Color contrast: **Exceeds WCAG AA** (4.71:1 to 14.68:1 ratios)
  - [x] Responsive design: viewport meta tag, mobile-friendly navigation

**Acceptance: ✅ ACHIEVED** - Base tokens load on all pages; component macros used in 6+ pages; layouts are responsive; 0 accessibility issues found.

**Deferred to Future**: Sessions list pagination (depends on M3 backend paging implementation).

#### M4 — Students ✅ **COMPLETED**
- [x] Student list (per teacher) with session filtering ✅
- [x] Individual student detail/portfolio views ✅
- [x] Delete with ownership checks ✅
- [x] Bulk operations (delete, PIN reset) ✅
- [x] Export printable PIN cards (PDF) ✅
- [x] Student analytics and engagement reporting ✅

**Implementation Complete:**
- ✅ `StudentService` class with comprehensive business logic
- ✅ `PinCardsService` for PDF generation with ReportLab
- ✅ Full CRUD operations with ownership verification
- ✅ UI components (`student_card`, `student_table`, modals, analytics)
- ✅ Error handlers for 403/404 ownership violations
- ✅ JavaScript for interactive features (PIN reset, bulk operations)
- ✅ Student portfolio with media gallery and activity timeline
- ✅ Analytics dashboard with engagement metrics
- ✅ Navigation integration and responsive design
- ✅ Comprehensive test coverage (routes, services, PIN cards)

**Acceptance: ✅ ACHIEVED** - All CRUD operations work; PDF generation functional; Analytics display engagement data; Bulk operations provide smooth UX; Portfolio shows student work and progress.

#### M5 — Media ✅ **COMPLETED**
- [x] Upload image (validate type/size), generate title from tags ✅
- [x] Edit tags and recompute title ✅
- [x] Delete media (permission + file removal) ✅
- [x] Project upload (1-10 images) with gallery view ✅
- [x] Student-centric upload interfaces with Data Deck branding ✅
- [x] Image carousel navigation with thumbnails ✅
- [x] Comprehensive media management (view, edit, delete) ✅
- [x] Upload statistics and portfolio views ✅
- [x] Robust file validation and security checks ✅

**Implementation Complete:**
- ✅ `MediaService` class with comprehensive business logic
- ✅ Student upload forms (single image + Data Deck projects)
- ✅ Media routes blueprint with full CRUD operations
- ✅ Beautiful, responsive templates with image carousels
- ✅ Integration with existing student/teacher workflows
- ✅ Navigation enhancements and portfolio views
- ✅ Security and validation (file types, sizes, ownership)
- ✅ Enhanced user experience with progress indicators

**Acceptance: ✅ ACHIEVED** - Upload persists with validation; edit updates title and tags; delete removes with permissions; gallery renders with navigation; Data Deck projects support 1-10 images; student-friendly interfaces integrated.

#### M6 — Posts & Comments ✅ **COMPLETED**
- [x] Post detail shows media, poster, counts ✅
- [x] Nested comments (replies), attribution (admin/student) ✅
- [x] Increment `StudentMediaInteraction.comment_count` on student comment ✅

**Implementation Complete:**
- ✅ `PostsBlueprint` with routes for post detail and comment functionality
- ✅ `CommentForm` for adding comments and replies with validation
- ✅ Comprehensive post detail template with media display, poster info, and stats
- ✅ Nested comment system with admin/student attribution and reply threading
- ✅ Comment count increment logic in `StudentMediaInteraction` model
- ✅ Navigation links from media detail and session views to post views
- ✅ Template filters and UI components for rich comment display
- ✅ Proper permission checking for both authenticated and student users

**Acceptance: ✅ ACHIEVED** - Replies render nested with proper attribution; comment counts update accurately; post views integrate seamlessly with existing media workflow.

#### M7 — Reactions/Badges ✅ **COMPLETED**
- [x] Behavior: single-select per student per media (`graph`, `eye`, `read`)
- [x] Endpoint: `POST /media/<id>/react/<badge_type>` returns `{ success, counts, user_like }`
- [x] AuthZ: student must belong to the media's session (403 otherwise)
- [x] UI: `templates/_components/reactions.html` macro renders icons, counts, tooltips
- [x] UX rule: badges clickable only on the post/media detail page; read-only in session grid
- [x] JS: `static/js/reactions.js` (tooltips init, CSRF header, single-select UI update)
- [x] Styling: `static/css/components.css` with selected/hover states and count overlays
- [x] Data: counts denormalized on `Media`; per-student selection in `StudentMediaInteraction`

**Acceptance: ✅ ACHIEVED**
- Badges are clickable for students on the post detail page only; session grid is non-interactive
- Single-select enforced; switching badges updates selection and counts live via AJAX
- Tooltip help text appears on hover/focus; counts and selected state persist on refresh

#### M7.5 — Session Analytics & Teacher Controls ✅ **COMPLETED**
- [x] Session analytics on session detail (teacher-only):
  - Total reactions by badge (graph/eye/read) and grand total
  - Participation: # students reacted, # students commented, total comments
  - Top media by reactions (top 3)
- [x] Per-student participation table (teacher-only): uploads, reacted?, comments, quick links
- [x] Bulk control: Reset all reactions for a session (`POST /sessions/<id>/reactions/reset`)
- [x] Inline control: Reset reactions for a single student in a session (`POST /sessions/<id>/students/<student_id>/reactions/reset`)
- [x] Per-media control: Reset reactions for a single post (`POST /media/<id>/reactions/reset`)

Acceptance: Analytics render without page errors; resets update denormalized counts and UI on refresh; permissions enforced (teacher owner/admin/staff only).

#### M8 — Admin & Observer Dashboards
- [x] Admin: District CRUD + toggle; Observer management (create/deactivate/password)
- [x] Teacher district assignment/update
- [x] Observer dashboard: district overview (teachers, sessions, recent media)

Status (complete):
- ✅ District CRUD implemented in admin dashboard (create, edit, delete with safety checks)
- ✅ School CRUD implemented in admin dashboard (create, edit, delete with safety checks)
- ✅ Observer management controls (deactivate/reactivate, reset password, assign district)
- ✅ Teacher reassignment tools (inline update of school/district) with dependent school dropdown
- ✅ Observer dashboard stats and drill-down (teachers, sessions, recent media)

Acceptance: Admin operations succeed with flash messages; observer sees only their district; observer dashboard shows district-wide stats and links to teacher drill-down views.

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

### Technical Debt Completion (Pre-M4)
**Status**: ✅ **COMPLETE** - All high-impact technical debt resolved

- [x] **Model debugging improvements**: Added `__repr__` methods to User, Student models
- [x] **Legacy code cleanup**: Removed `routes/observer_auth.py`, cleaned imports
- [x] **Data model cleanup**: Removed unused `Media.submitted_password` field
- [x] **Service documentation**: Enhanced `SessionService` with comprehensive docstrings
- [x] **StudentService creation**: Complete service layer with 6 methods for M4 operations
- [x] **Error handlers**: Added 403/404/500 handlers with role-aware templates
- [x] **UI component library**: Extended with student cards, tables, modals, JavaScript

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
