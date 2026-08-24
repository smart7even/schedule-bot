import logging
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError

from core.repositories.feature_flag_repository import (
    FeatureFlagRepository,
    ROOM_MAP_BUTTON_ENABLED,
    ROOM_MAP_CAPTION_ENABLED,
)
from db import Session


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppConfig:
    room_map_button_enabled: bool = False
    room_map_caption_enabled: bool = False

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "room_map_button_enabled": self.room_map_button_enabled,
            "room_map_caption_enabled": self.room_map_caption_enabled,
        }


def get_app_config(session_factory=Session) -> AppConfig:
    """Read current flags on every call and fail closed if storage is down."""
    session = session_factory()
    try:
        values = FeatureFlagRepository(session).get_all()
        return AppConfig(
            room_map_button_enabled=values[ROOM_MAP_BUTTON_ENABLED],
            room_map_caption_enabled=values[ROOM_MAP_CAPTION_ENABLED],
        )
    except SQLAlchemyError:
        session.rollback()
        logger.exception("Feature flags are unavailable; using safe defaults")
        return AppConfig()
    finally:
        session.close()
