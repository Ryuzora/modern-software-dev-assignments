from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


# Many-to-many link table: each action item can have many tags; each tag can label many items.
action_item_tags = Table(
    "action_item_tags",
    Base.metadata,
    Column(
        "action_item_id",
        Integer,
        ForeignKey("action_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Note(Base, TimestampMixin):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)


class Tag(Base, TimestampMixin):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    # Short, unique label for filtering and display (normalized in API layer).
    name = Column(String(80), unique=True, nullable=False, index=True)

    action_items = relationship(
        "ActionItem",
        secondary=action_item_tags,
        back_populates="tags",
    )


class ActionItem(Base, TimestampMixin):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)

    tags = relationship(
        "Tag",
        secondary=action_item_tags,
        back_populates="action_items",
    )
