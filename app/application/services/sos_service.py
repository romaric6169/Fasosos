"""
Service métier pour la gestion des alertes SOS.
Orchestre la création de l'alerte, la sélection du contact d'urgence
et la génération du message pré-rempli à envoyer par SMS.
"""
from urllib.parse import quote

from app.infrastructure.database.models import SosAlert
from app.infrastructure.repositories.sos_repository import SosRepository
from app.infrastructure.repositories.emergency_contact_repository import (
    EmergencyContactRepository,
)


class SosService:
    """Gère le cycle de vie d'une alerte SOS."""

    def __init__(
        self,
        sos_repository: SosRepository,
        contact_repository: EmergencyContactRepository,
    ) -> None:
        self._sos_repository = sos_repository
        self._contact_repository = contact_repository

    def declencher_alerte(
        self,
        user_id: str,
        user_nom: str,
        type_urgence: str,
        type_centre_souhaite: str | None,
        latitude: float,
        longitude: float,
        description: str | None,
        contact_urgence_id: str | None,
    ) -> dict:
        """
        Crée une alerte SOS et génère le message d'urgence prêt à envoyer.

        Returns:
            dict contenant l'alerte créée et le lien SMS pré-rempli
            (sms:NUMERO?body=MESSAGE), prêt à être ouvert côté client.
        """
        alerte: SosAlert = self._sos_repository.create(
            user_id=user_id,
            type_urgence=type_urgence,
            type_centre_souhaite=type_centre_souhaite,
            description=description,
            latitude=latitude,
            longitude=longitude,
            contact_urgence_id=contact_urgence_id,
            statut="en_cours",
        )

        lien_sms = None
        if contact_urgence_id:
            contact = self._contact_repository.get_by_id(contact_urgence_id)
            if contact:
                message = self._generer_message_urgence(
                    user_nom=user_nom,
                    type_urgence=type_urgence,
                    latitude=latitude,
                    longitude=longitude,
                    description=description,
                    date_heure=alerte.created_at,
                )
                lien_sms = self._generer_lien_sms(contact.telephone, message)

        return {
            "alerte": alerte,
            "lien_sms": lien_sms,
        }

    def _generer_message_urgence(
        self,
        user_nom: str,
        type_urgence: str,
        latitude: float,
        longitude: float,
        description: str | None,
        date_heure,
    ) -> str:
        """Construit le message d'urgence pré-rempli."""
        lien_maps = f"https://www.google.com/maps?q={latitude},{longitude}"
        date_str = date_heure.strftime("%d/%m/%Y à %H:%M")

        message = (
            f"URGENCE FasoSOS - {user_nom}\n"
            f"Type : {type_urgence}\n"
            f"Date : {date_str}\n"
            f"Position : {lien_maps}"
        )
        if description:
            message += f"\nDétails : {description}"

        return message

    def _generer_lien_sms(self, telephone: str, message: str) -> str:
        """
        Génère un lien sms: standard (compatible Android/iOS)
        avec le message déjà encodé, prêt à être ouvert côté client.
        """
        message_encode = quote(message)
        return f"sms:{telephone}?body={message_encode}"

    def obtenir_historique(self, user_id: str) -> list[SosAlert]:
        return self._sos_repository.get_history_by_user(user_id)
