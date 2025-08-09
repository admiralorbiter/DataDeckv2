## DataDeck Architecture (Flask v2 Implementation)

### Purpose
DataDeck enables teachers to run classroom “sessions” where students upload data visualizations (images), react with badges (Graph/Eye/Read), and add comments. District-level observers can browse activity across teachers in their district.

### Roles
- **Teacher/Admin (`CustomAdmin`)**: Creates sessions, generates students, uploads/moderates media, manages districts and observers.
- **Student**: Logs in with PIN, uploads media or final projects, reacts with badges, comments.
- **Observer**: Logs in with email/password, views sessions and media for their district.

### Tech Stack (Flask v2)
- Flask 3.0 with app factory pattern (server-rendered HTML via Jinja2 templates)
- Database: SQLite (dev/tests) / PostgreSQL (planned prod)
- SQLAlchemy ORM with relationship modeling
- Flask-Login for authentication and session management
- Flask-WTF for forms and CSRF protection
- Pytest for comprehensive testing
- Background jobs planned (RQ/Celery for future milestones)

### Key Features (Current Implementation Status)

#### ✅ Completed (M0-M3)
- **Session lifecycle**: create, list, detail view, archive/unarchive (delete planned)
- **Student generation**: unique character name + PIN, 20 students per session
- **Admin-configurable modules**: database-driven curriculum modules with CRUD
- **User management**: full CRUD for all user types with role-based permissions
- **Authentication**: unified login system with Flask-Login
- **Session uniqueness**: conflict detection with auto-archive option
- **Comprehensive testing**: 100% passing test suite

#### 📋 Planned (M4+)
- **Media uploads**: image upload with validation and tagging
- **Reactions/badges**: Graph guru, Expert engager, Supreme storyteller
- **Comments**: nested replies with admin/student attribution
- **Observer dashboard**: district-wide activity monitoring
- **Student export**: PDF cards with names and PINs
- **Advanced session management**: pause functionality, enhanced filtering

### Data Model
Mermaid ER diagram of the Flask SQLAlchemy entities and relationships:

```mermaid
erDiagram
  "District" {
    BIGINT id PK
    VARCHAR name "unique"
    VARCHAR code "unique"
    BOOLEAN is_active
    DATETIME created_at
  }
  "User" {
    BIGINT id PK
    VARCHAR username
    VARCHAR email "unique"
    VARCHAR password_hash
    BIGINT school_id FK
    BIGINT district_id FK
    VARCHAR first_name
    VARCHAR last_name
    ENUM role "ADMIN,STAFF,TEACHER,OBSERVER,STUDENT"
    DATETIME created_at
    DATETIME updated_at
  }
  "Observer" {
    BIGINT user_id PK FK
    TEXT additional_info "nullable"
  }
  "Student" {
    BIGINT user_id PK FK
    TEXT character_description "nullable"
    VARCHAR avatar_image_path "nullable"
  }
  "School" {
    BIGINT id PK
    VARCHAR name
    BIGINT district_id FK
    DATETIME created_at
  }
  "Module" {
    BIGINT id PK
    VARCHAR name "unique"
    TEXT description "nullable"
    BOOLEAN is_active
    INT sort_order
    DATETIME created_at
  }
  "Session" {
    BIGINT id PK
    VARCHAR name
    VARCHAR original_name "nullable"
    CHAR session_code "8, unique"
    INT section
    BIGINT module_id FK
    DATETIME created_at
    BOOLEAN is_paused
    BOOLEAN is_archived
    DATETIME archived_at "nullable"
    BIGINT created_by_id FK
    VARCHAR character_set
  }

  "Media" {
    BIGINT id PK
    BIGINT session_id FK
    VARCHAR title
    TEXT description "nullable"
    ENUM media_type "{'video','image','comment'}"
    VARCHAR video_file "nullable"
    VARCHAR image_file "nullable"
    DATETIME uploaded_at
    INT graph_likes
    INT eye_likes
    INT read_likes
    ENUM graph_tag "subset"
    BOOLEAN is_graph
    ENUM variable_tag "subset"
    VARCHAR submitted_password "nullable"
    BIGINT student_id FK "nullable"
    BIGINT posted_by_admin_id FK "nullable"
    UUID project_group "nullable"
    JSON project_images "nullable"
    BOOLEAN is_project
  }
  "StudentMediaInteraction" {
    BIGINT id PK
    BIGINT student_id FK
    BIGINT media_id FK
    BOOLEAN liked_graph
    BOOLEAN liked_eye
    BOOLEAN liked_read
    INT comment_count
    DATETIME created_at
    DATETIME updated_at
  }
  "Comment" {
    BIGINT id PK
    BIGINT media_id FK
    BIGINT parent_id FK "nullable, self"
    TEXT text
    DATETIME created_at
    DATETIME updated_at
    VARCHAR name
    VARCHAR device_id "nullable"
    BOOLEAN is_admin
    BIGINT student_id FK "nullable"
    VARCHAR admin_avatar "nullable"
  }

  "District" ||--o{ "School" : "district"
  "District" ||--o{ "User" : "district"
  "School" ||--o{ "User" : "school"
  "User" ||--|| "Observer" : "user"
  "User" ||--|| "Student" : "user"
  "User" ||--o{ "Session" : "created_by"
  "Module" ||--o{ "Session" : "module"
  "Session" ||--o{ "User" : "session_students"
  "Session" ||--o{ "Media" : "session"
  "User" ||--o{ "Media" : "posted_by"
  "Media" ||--o{ "Comment" : "comments"
  "Comment" ||--o| "Comment" : "replies"
  "User" ||--o{ "StudentMediaInteraction" : "student"
  "Media" ||--o{ "StudentMediaInteraction" : "media"
  "User" ||--o{ "Comment" : "student"
```

### Route Inventory (Flask v2 - Current Implementation)
Key Flask routes organized by blueprints:

#### Auth Blueprint (`/`)
- **Login/Logout**: `/login`, `/logout` (unified for all user types)
- **Profile**: `/profile` (password change and user info)

#### Main Blueprint (`/`)
- **Home**: `/` (role-based dashboard routing)
- **Main Dashboard**: `/main` (role-specific landing pages)

#### Sessions Blueprint (`/sessions`)
- **Session Management**: `/sessions/start`, `/sessions`, `/sessions/<id>`
- **Session Actions**: `/sessions/<id>/archive`, `/sessions/<id>/unarchive`
- **API Endpoints**: `/api/sessions/check-section` (AJAX validation)

#### Admin Blueprint (`/admin`)
- **Admin Dashboard**: `/admin` (user and system management)
- **User Management**: `/admin/create_user`, `/admin/edit_user/<id>`, `/admin/delete_user/<id>`
- **Module Management**: `/admin/create_module`, `/admin/edit_module/<id>`

#### Observer Blueprint (`/observer`) - Planned
- **Observer Dashboard**: `/observer/dashboard` (district activity view)
- **School Details**: `/observer/school/<id>` (school-specific activity)

#### Planned Routes (M4+)
- **Students**: `/students`, `/students/<id>/delete`, `/students/export-pins`
- **Media**: `/media/upload`, `/media/<id>/edit`, `/media/<id>/delete`
- **Reactions**: `/api/media/<id>/react/<type>` (AJAX reactions)
- **Comments**: `/api/media/<id>/comment` (AJAX comments)

### Core Flows (Flask v2 Implementation)

#### ✅ Implemented Flows
- **Teacher Session Creation**: Teacher creates session → conflict detection → auto-archive option → generate 20 students → redirect to session detail
- **User Authentication**: Unified login (email-first, username fallback) → Flask-Login session → role-based dashboard
- **Session Management**: List sessions → view details → archive/unarchive with conflict checking
- **Admin User Management**: Create/edit/delete users → school/district assignment → role-based permissions
- **Module Management**: Admin creates/edits modules → teachers select from active modules in session creation

#### 📋 Planned Flows (M4+)
- **Student Login**: PIN-based authentication → join session → media upload/interaction
- **Media Upload**: File validation → tag extraction → title generation → save to session
- **Reactions**: Student badges (Graph/Eye/Read) → update interaction counts → real-time feedback
- **Comments**: Nested comment threads → admin/student attribution → notification system
- **Observer Monitoring**: District-scoped session viewing → activity reports → engagement metrics

### Security Model (Flask v2)

#### ✅ Current Security Features
- **Password Hashing**: All passwords hashed with Werkzeug security (bcrypt-based)
- **CSRF Protection**: Flask-WTF provides global CSRF protection for all forms
- **Session Management**: Flask-Login handles secure session management
- **Role-Based Access**: Decorators and permission checks for route authorization
- **Input Validation**: Flask-WTF form validation with sanitization
- **Student PIN Security**: PINs are hashed (not plaintext) and stored securely

#### 📋 Planned Security Enhancements
- **Production Secret Management**: Environment-based secret key configuration
- **Secure Cookie Settings**: HTTPOnly, Secure, SameSite cookie attributes
- **Rate Limiting**: Protection against brute force and abuse
- **File Upload Security**: Virus scanning and content type validation
- **Audit Logging**: Track admin actions and sensitive operations

### Background Jobs (Planned)
- **Session Cleanup**: Automated deletion of expired sessions (RQ/Celery)
- **Media Processing**: Image resizing, optimization, thumbnail generation
- **Analytics Updates**: Periodic calculation of engagement metrics
- **Notification System**: Email/SMS notifications for important events

### Static & Media (Current/Planned)
- **Static Assets**: Flask static file serving for CSS, JS, images
- **Media Storage**: Local filesystem (dev) → S3-compatible storage (prod)
- **File Organization**: Structured directory layout with CDN support
- **Image Processing**: Planned automatic resizing and optimization

### Flask v2 Architecture Improvements

#### ✅ Completed Improvements
- **Unified Authentication**: Single login system for all user types
- **Normalized Data Model**: Proper foreign key relationships (school_id, district_id)
- **Service Layer**: Business logic separated from route handlers
- **Comprehensive Testing**: Full test coverage with fixtures and factories
- **Modern Flask Patterns**: App factory, blueprints, proper configuration management

#### 📋 Remaining Technical Debt
- **CI/CD Pipeline**: Automated testing and deployment
- **Error Handling**: User-friendly error pages and API responses
- **Logging System**: Structured logging with correlation IDs
- **Performance Optimization**: Query optimization, caching, pagination
- **API Documentation**: OpenAPI spec for future API endpoints

### Migration Considerations

#### Data Migration Strategy
- **Export Scripts**: Extract data from Django models to JSON/CSV
- **Import Scripts**: Transform and load data into Flask SQLAlchemy models
- **Validation**: Referential integrity checks and data verification
- **Rollback Plan**: Ability to revert to Django version if needed

#### Feature Parity Checklist
- [x] User authentication and management
- [x] Session creation and lifecycle management
- [x] Student generation and management
- [x] Admin dashboard and user CRUD
- [x] Module system configuration
- [ ] Media upload and management (M5)
- [ ] Reaction and badge system (M6-M7)
- [ ] Comment system with threading (M6)
- [ ] Observer dashboard and reporting (M8)
- [ ] Background job processing (M10)
