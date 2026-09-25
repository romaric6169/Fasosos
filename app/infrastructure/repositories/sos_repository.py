"""Repository pour l'accès aux données SosAlert."""
from app.infrastructure.database.models import SosAlert
from app import db


class SosRepository:
    """Isole l'accès aux données SosAlert (Repository Pattern)."""

    def create(self, **kwargs) -> SosAlert:
        alerte = SosAlert(**kwargs)
        db.session.add(alerte)
        db.session.commit()
        return alerte

    def get_by_id(self, alerte_id: str) -> SosAlert | None:
        return SosAlert.query.get(alerte_id)

    def get_history_by_user(self, user_id: str) -> list[SosAlert]:
        return (
            SosAlert.query.filter_by(user_id=user_id)
            .order_by(SosAlert.created_at.desc())
            .all()
        )
