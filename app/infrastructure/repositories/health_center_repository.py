"""Repository pour l'accès aux données des centres de santé."""
from app.infrastructure.database.models import HealthCenter
from app import db


class HealthCenterRepository:
    """Isole l'accès aux données HealthCenter (Repository Pattern)."""

    def get_all_actifs(self) -> list[HealthCenter]:
        """Retourne tous les centres de santé enregistrés."""
        return HealthCenter.query.all()

    def get_by_id(self, centre_id: str) -> HealthCenter | None:
        return HealthCenter.query.get(centre_id)

    def create(self, **kwargs) -> HealthCenter:
        centre = HealthCenter(**kwargs)
        db.session.add(centre)
        db.session.commit()
        return centre

    def update(self, centre_id: str, **kwargs) -> "HealthCenter | None":
        """Met à jour un centre existant. Retourne None si introuvable."""
        centre = self.get_by_id(centre_id)
        if not centre:
            return None

        for champ, valeur in kwargs.items():
            if valeur is not None and hasattr(centre, champ):
                setattr(centre, champ, valeur)

        db.session.commit()
        return centre

    def delete(self, centre_id: str) -> bool:
        """Supprime un centre. Retourne False si introuvable."""
        centre = self.get_by_id(centre_id)
        if not centre:
            return False

        db.session.delete(centre)
        db.session.commit()
        return True
