"""Routes API pour la gestion des alertes SOS."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.application.services.sos_service import SosService
from app.infrastructure.repositories.sos_repository import SosRepository
from app.infrastructure.repositories.emergency_contact_repository import (
    EmergencyContactRepository,
)
from app.infrastructure.database.models import User

sos_bp = Blueprint("sos", __name__, url_prefix="/api/v1/sos")


def _get_sos_service() -> SosService:
    return SosService(SosRepository(), EmergencyContactRepository())


@sos_bp.route("", methods=["POST"])
@jwt_required()
def declencher_sos():
    """Déclenche une alerte SOS pour l'utilisateur connecté."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"erreur": "Utilisateur introuvable."}), 404

    donnees = request.get_json() or {}

    champs_requis = ["type_urgence", "latitude", "longitude"]
    manquants = [champ for champ in champs_requis if champ not in donnees]
    if manquants:
        return jsonify({"erreur": f"Champs manquants : {', '.join(manquants)}"}), 400

    service = _get_sos_service()
    resultat = service.declencher_alerte(
        user_id=user_id,
        user_nom=user.nom,
        type_urgence=donnees["type_urgence"],
        type_centre_souhaite=donnees.get("type_centre_souhaite"),
        latitude=donnees["latitude"],
        longitude=donnees["longitude"],
        description=donnees.get("description"),
        contact_urgence_id=donnees.get("contact_urgence_id"),
    )

    alerte = resultat["alerte"]
    return (
        jsonify(
            {
                "id": alerte.id,
                "type_urgence": alerte.type_urgence,
                "statut": alerte.statut,
                "created_at": alerte.created_at.isoformat(),
                "lien_sms": resultat["lien_sms"],
            }
        ),
        201,
    )


@sos_bp.route("/history", methods=["GET"])
@jwt_required()
def historique_sos():
    """Retourne l'historique des alertes SOS de l'utilisateur connecté."""
    user_id = get_jwt_identity()
    service = _get_sos_service()
    alertes = service.obtenir_historique(user_id)

    return jsonify(
        [
            {
                "id": a.id,
                "type_urgence": a.type_urgence,
                "statut": a.statut,
                "created_at": a.created_at.isoformat(),
            }
            for a in alertes
        ]
    )
