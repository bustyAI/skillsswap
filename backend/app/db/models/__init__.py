"""SQLAlchemy models for SkillSwap.

All models are imported here so Alembic can discover them for migrations.
Import from this module, not from individual model files.

Example:
    from app.db.models import User, MentorProfile, Topic
"""

from app.db.models.block import Block
from app.db.models.meeting import Meeting, MeetingStatus
from app.db.models.mentor_embedding import MentorEmbedding
from app.db.models.mentor_profile import MentorProfile
from app.db.models.mentor_topic import MentorTopic
from app.db.models.mentorship import Mentorship, MentorshipStatus
from app.db.models.message import Message
from app.db.models.message_thread import MessageThread
from app.db.models.report import Report, ReportStatus
from app.db.models.review import Review
from app.db.models.topic import Topic
from app.db.models.topic_embedding import TopicEmbedding
from app.db.models.user import User

__all__ = [
    # Core entities
    "User",
    "MentorProfile",
    "Topic",
    "MentorTopic",
    "MentorEmbedding",
    "TopicEmbedding",
    # Mentorship and meetings
    "Mentorship",
    "MentorshipStatus",
    "Meeting",
    "MeetingStatus",
    # Messaging
    "MessageThread",
    "Message",
    # Reviews
    "Review",
    # Moderation
    "Report",
    "ReportStatus",
    "Block",
]
