"""SQLAlchemy models for SkillSwap.

All models are imported here so Alembic can discover them for migrations.
Import from this module, not from individual model files.

Example:
    from app.db.models import User, MentorProfile, Topic
"""

from app.db.models.mentor_embedding import MentorEmbedding
from app.db.models.mentor_profile import MentorProfile
from app.db.models.mentor_topic import MentorTopic
from app.db.models.topic import Topic
from app.db.models.topic_embedding import TopicEmbedding
from app.db.models.user import User

__all__ = [
    "User",
    "MentorProfile",
    "Topic",
    "MentorTopic",
    "MentorEmbedding",
    "TopicEmbedding",
]
