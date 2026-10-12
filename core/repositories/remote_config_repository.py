import copy
from typing import List, Optional

from core.models.remote_config import RemoteConfigDocument, RemoteConfigRevision
from core.services.remote_config_service import validate_remote_config_document


class RemoteConfigRepository:
    def __init__(self, session) -> None:
        self.session = session

    def get(self, key: str) -> Optional[RemoteConfigDocument]:
        return self.session.query(RemoteConfigDocument).filter(
            RemoteConfigDocument.key == key,
        ).one_or_none()

    def set(self, key: str, document: dict) -> RemoteConfigDocument:
        validated = validate_remote_config_document(document)
        current = self.get(key)
        if current is None:
            current = RemoteConfigDocument(
                key=key,
                document=copy.deepcopy(validated),
                revision=1,
            )
            self.session.add(current)
        else:
            current.document = copy.deepcopy(validated)
            current.revision += 1

        self.session.flush()
        self.session.add(
            RemoteConfigRevision(
                config_key=key,
                revision=current.revision,
                document=copy.deepcopy(validated),
            )
        )
        self.session.commit()
        self.session.refresh(current)
        return current

    def history(self, key: str, limit: int = 20) -> List[RemoteConfigRevision]:
        return (
            self.session.query(RemoteConfigRevision)
            .filter(RemoteConfigRevision.config_key == key)
            .order_by(RemoteConfigRevision.revision.desc())
            .limit(limit)
            .all()
        )

    def get_revision(self, key: str, revision: int) -> Optional[RemoteConfigRevision]:
        return self.session.query(RemoteConfigRevision).filter(
            RemoteConfigRevision.config_key == key,
            RemoteConfigRevision.revision == revision,
        ).one_or_none()

    def rollback(self, key: str, revision: int) -> RemoteConfigDocument:
        historical = self.get_revision(key, revision)
        if historical is None:
            raise ValueError("Unknown {} revision {}".format(key, revision))
        return self.set(key, historical.document)
