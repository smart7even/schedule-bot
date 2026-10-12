from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.sql import func

from db import Base


class RemoteConfigDocument(Base):
    """Current version of a remotely evaluated configuration document."""

    __tablename__ = "remote_config_documents"

    key = Column(String, primary_key=True)
    document = Column(JSON, nullable=False)
    revision = Column(Integer, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )


class RemoteConfigRevision(Base):
    """Immutable revision retained for inspection and rollback."""

    __tablename__ = "remote_config_revisions"
    __table_args__ = (
        UniqueConstraint("config_key", "revision", name="uq_remote_config_revision"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(
        String,
        ForeignKey("remote_config_documents.key", ondelete="CASCADE"),
        nullable=False,
    )
    revision = Column(Integer, nullable=False)
    document = Column(JSON, nullable=False)
    created_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )
