"""SQLAlchemy models for SkillSwap.

All models are imported here so Alembic can discover them for migrations.
Import from this module, not from individual model files.

Example:
    from app.db.models import User, MentorProfile
"""

from app.db.models.mentor_profile import MentorProfile
from app.db.models.user import User

__all__ = ["User", "MentorProfile"]
