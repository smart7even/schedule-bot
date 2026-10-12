import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.exc import SQLAlchemyError

from core.repositories.feature_flag_repository import (
    FeatureFlagRepository,
    ROOM_MAP_BUTTON_ENABLED,
    ROOM_MAP_CAPTION_ENABLED,
)
from core.repositories.remote_config_repository import RemoteConfigRepository
from core.services.remote_config_service import (
    DEFAULT_REFRESH_INTERVAL_SECONDS,
    DEFAULT_REMOTE_CONFIG_DOCUMENT,
    DEFAULT_REMOTE_PAYLOAD,
    REMOTE_CONFIG_KEY,
    RemoteConfigValidationError,
    build_remote_config_context,
    evaluate_remote_config,
)
from db import Session


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppConfig:
    room_map_button_enabled: bool = False
    room_map_caption_enabled: bool = False
    schedule_auto_scroll_today: bool = True
    revision: int = 0
    refresh_interval_seconds: int = DEFAULT_REFRESH_INTERVAL_SECONDS
    payload: Dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULT_REMOTE_PAYLOAD)
    )

    def to_dict(self) -> dict:
        return {
            "version": 2,
            "revision": self.revision,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "room_map_button_enabled": self.room_map_button_enabled,
            "room_map_caption_enabled": self.room_map_caption_enabled,
            "schedule_auto_scroll_today": self.schedule_auto_scroll_today,
            "payload": dict(self.payload),
        }


def get_app_config(
    session_factory=Session,
    group_id: Optional[int] = None,
    platform: Optional[str] = None,
    app_version: Optional[str] = None,
    now: Optional[datetime] = None,
) -> AppConfig:
    """Evaluate current config on every call and fail safely if storage is down."""
    session = session_factory()
    try:
        values = FeatureFlagRepository(session).get_all()
        stored = RemoteConfigRepository(session).get(REMOTE_CONFIG_KEY)
        document = (
            stored.document if stored is not None else DEFAULT_REMOTE_CONFIG_DOCUMENT
        )
        context = build_remote_config_context(
            session,
            group_id=group_id,
            platform=platform,
            app_version=app_version,
            now=now,
        )
        evaluation = evaluate_remote_config(document, context)
        payload = dict(DEFAULT_REMOTE_PAYLOAD)
        payload.update(evaluation.payload)
        auto_scroll = payload.get("schedule_auto_scroll_today")
        if not isinstance(auto_scroll, bool):
            logger.warning(
                "Remote config schedule_auto_scroll_today is not boolean; using default"
            )
            auto_scroll = DEFAULT_REMOTE_PAYLOAD["schedule_auto_scroll_today"]

        return AppConfig(
            room_map_button_enabled=values[ROOM_MAP_BUTTON_ENABLED],
            room_map_caption_enabled=values[ROOM_MAP_CAPTION_ENABLED],
            schedule_auto_scroll_today=auto_scroll,
            revision=stored.revision if stored is not None else 0,
            refresh_interval_seconds=evaluation.refresh_interval_seconds,
            payload=payload,
        )
    except (SQLAlchemyError, RemoteConfigValidationError):
        session.rollback()
        logger.exception("App config is unavailable; using safe defaults")
        return AppConfig()
    finally:
        session.close()
