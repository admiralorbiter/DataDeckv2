# Accounts, Roles, and Creation

This document describes account types in DataDeck v2, how they authenticate, what they can access, and how to create them in development and via the Admin UI.

## Roles

- Admin
  - Auth: Email + password via teacher/admin login
  - Access: All districts, schools, users; Admin dashboard; user management
- Staff
  - Auth: Email + password via teacher/admin login
  - Access: Similar to Admin but limited where enforced (e.g., cannot change roles or delete users if restricted)
- Teacher
  - Auth: Email + password via teacher/admin login
  - Access: Their own sessions, students, media; can start sessions and generate students
- Observer
  - Auth: Email + password via observer login (`/observer/login`); session stored under `observer_id`
  - Access: Read-only views for their district: observer dashboard and drill-down by school to see teachers
- Student
  - Auth: PIN-based login (session-only `student_id`), not Flask-Login; used to upload/react/comment

## Creation Paths

- Admin via CLI
  - `python create_admin.py` and follow prompts (email/password); creates `User` with role `ADMIN`
- Specific Admin example (dev only)
  - `python create_jonlane.py` (predefined credentials)
- Seed script
  - `python seed_dev.py` resets DB and creates: one district, one school, one teacher, one session, and N students with PINs.
- Admin UI (`/admin`)
  - Create users of any role. When selecting role `observer`, the system creates an `Observer` subclass row to support the observer session and dashboard.

## Observer Dashboard

- After logging in, observers land on `/observer/dashboard` which shows their district and schools.
- Clicking a school navigates to `/observer/schools/<id>` showing the teachers at that school.

## Notes

- Teacher/Admin login uses email+password (with backward-compatible username fallback for tests).
- Observer auth uses a separate session namespace and decorators (`@observer_required`).
- Student routes are protected with `@student_required` leveraging session `student_id`.
