from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.sql import func

from db import Base


class FeatureFlag(Base):
    """Runtime switch that can be changed without restarting the API."""

    __tablename__ = "feature_flags"

    name = Column(String, primary_key=True)
    enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )
