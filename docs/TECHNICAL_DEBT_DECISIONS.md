# Technical Debt Decisions

This document records decisions made about technical debt items during development.

## Media.submitted_password Field (Removed - 2024)

**Decision**: Removed the `submitted_password` field from the Media model.

**Rationale**:
- Field was identified as "likely legacy" in M0/M1 retrospective
- No usage found in current Flask codebase (comprehensive grep search showed zero references)
- Django migration plan mentioned it as `media_password` field that should "consider deprecating"
- Field added complexity to the model without serving any purpose
- Removal simplifies the data model before M4-M5 media upload implementation

**Migration Impact**:
- If migrating from Django version, this field would need to be dropped during migration
- No impact on current Flask development since field was never used

**Files Changed**:
- `models/media.py`: Removed `submitted_password` column, added explanatory comment
