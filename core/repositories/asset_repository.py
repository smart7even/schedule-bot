from core.models.asset import Asset
from db import Session


class AssetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, asset_id: str) -> Asset:
        return self.session.query(Asset).filter_by(id=asset_id).first()
