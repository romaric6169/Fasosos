"""Journalisation centralisée des événements de sécurité."""
from flask import request
from app.infrastructure.database.models import AuditLog
from app import db


class AuditLogger:
    """Enregistre les événements de sécurité pour consultation ultérieure."""

    @staticmethod
    def enregistrer(type_evenement: str, details: str = None, telephone_cible: str = None, user_id: str = None) -> None:
        """
        Enregistre un événement de sécurité en base.
        Ne lève jamais d'exception : une erreur de journalisation ne doit
        jamais faire échouer la requête principale.
        """
        try:
            adresse_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            if adresse_ip and "," in adresse_ip:
                adresse_ip = adresse_ip.split(",")[0].strip()

            entree = AuditLog(
                type_evenement=type_evenement,
                details=details,
                adresse_ip=adresse_ip,
                telephone_cible=telephone_cible,
                user_id=user_id,
            )
            db.session.add(entree)
            db.session.commit()
        except Exception:
            db.session.rollback()
