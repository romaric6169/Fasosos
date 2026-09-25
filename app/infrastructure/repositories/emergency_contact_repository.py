"""Repository pour l'accès aux contacts d'urgence."""
from app.infrastructure.database.models import EmergencyContact
from app import db


class EmergencyContactRepository:
    """Isole l'accès aux données EmergencyContact."""

    MAX_CONTACTS_PAR_UTILISATEUR = 5

    def get_by_user(self, user_id: str) -> list[EmergencyContact]:
        return (
            EmergencyContact.query.filter_by(user_id=user_id)
            .order_by(EmergencyContact.priorite.asc())
            .all()
        )

    def get_by_id(self, contact_id: str) -> EmergencyContact | None:
        return EmergencyContact.query.get(contact_id)

    def count_by_user(self, user_id: str) -> int:
        return EmergencyContact.query.filter_by(user_id=user_id).count()

    def create(self, **kwargs) -> EmergencyContact:
        if self.count_by_user(kwargs["user_id"]) >= self.MAX_CONTACTS_PAR_UTILISATEUR:
            raise ValueError("Nombre maximum de contacts d'urgence atteint (5).")
        contact = EmergencyContact(**kwargs)
        db.session.add(contact)
        db.session.commit()
        return contact

    def update(self, contact_id: str, user_id: str, **kwargs) -> "EmergencyContact | None":
        """Met à jour un contact, uniquement s'il appartient bien à l'utilisateur."""
        contact = self.get_by_id(contact_id)
        if not contact or contact.user_id != user_id:
            return None

        for champ, valeur in kwargs.items():
            if valeur is not None and hasattr(contact, champ):
                setattr(contact, champ, valeur)

        db.session.commit()
        return contact

    def delete(self, contact_id: str, user_id: str) -> bool:
        """Supprime un contact, uniquement s'il appartient bien à l'utilisateur."""
        contact = self.get_by_id(contact_id)
        if not contact or contact.user_id != user_id:
            return False

        db.session.delete(contact)
        db.session.commit()
        return True
