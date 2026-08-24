from datetime import datetime
from typing import Dict

from core.models.feature_flag import FeatureFlag


ROOM_MAP_BUTTON_ENABLED = "room_map_button_enabled"
ROOM_MAP_CAPTION_ENABLED = "room_map_caption_enabled"
KNOWN_FEATURE_FLAGS = frozenset({
    ROOM_MAP_BUTTON_ENABLED,
    ROOM_MAP_CAPTION_ENABLED,
})


class FeatureFlagRepository:
    def __init__(self, session) -> None:
        self.session = session

    def get_all(self) -> Dict[str, bool]:
        values = {name: False for name in KNOWN_FEATURE_FLAGS}
        flags = self.session.query(FeatureFlag).filter(
            FeatureFlag.name.in_(KNOWN_FEATURE_FLAGS),
        ).all()
        values.update({flag.name: bool(flag.enabled) for flag in flags})
        return values

    def set(self, name: str, enabled: bool) -> FeatureFlag:
        if name not in KNOWN_FEATURE_FLAGS:
            raise ValueError("Unknown feature flag: {}".format(name))

        flag = self.session.query(FeatureFlag).filter(
            FeatureFlag.name == name,
        ).one_or_none()
        if flag is None:
            flag = FeatureFlag(name=name, enabled=enabled)
            self.session.add(flag)
        else:
            flag.enabled = enabled
            flag.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(flag)
        return flag
