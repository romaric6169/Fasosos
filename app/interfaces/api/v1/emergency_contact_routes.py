"""Routes API pour la gestion des contacts d'urgence."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.infrastructure.repositories.emergency_contact_repository import (
    EmergencyContactRepository,
)

emergency_contact_bp = Blueprint(
    "emergency_contacts", __name__, url_prefix="/api/v1/emergency-contacts"
)


def _serialiser_contact(contact) -> dict:
    return {
        "id": contact.id,
        "nom": contact.nom,
        "telephone": contact.telephone,
        "lien_parente": contact.lien_parente,
        "priorite": contact.priorite,
    }


@emergency_contact_bp.route("", methods=["GET"])
@jwt_required()
def lister_contacts():
    """Liste les contacts d'urgence de l'utilisateur connecté, triés par priorité."""
    user_id = get_jwt_identity()
    repository = EmergencyContactRepository()
    contacts = repository.get_by_user(user_id)

    return jsonify([_serialiser_contact(c) for c in contacts])


@emergency_contact_bp.route("", methods=["POST"])
@jwt_required()
def creer_contact():
    """Ajoute un nouveau contact d'urgence (maximum 5 par utilisateur)."""
    user_id = get_jwt_identity()
    donnees = request.get_json() or {}

    champs_requis = ["nom", "telephone"]
    manquants = [champ for champ in champs_requis if champ not in donnees]
    if manquants:
        return jsonify({"erreur": f"Champs manquants : {', '.join(manquants)}"}), 400

    repository = EmergencyContactRepository()
    try:
        contact = repository.create(
            user_id=user_id,
            nom=donnees["nom"],
            telephone=donnees["telephone"],
            lien_parente=donnees.get("lien_parente"),
            priorite=donnees.get("priorite", 1),
        )
    except ValueError as erreur:
        return jsonify({"erreur": str(erreur)}), 400

    return jsonify(_serialiser_contact(contact)), 201


@emergency_contact_bp.route("/<contact_id>", methods=["PUT"])
@jwt_required()
def modifier_contact(contact_id: str):
    """Modifie un contact d'urgence appartenant à l'utilisateur connecté."""
    user_id = get_jwt_identity()
    donnees = request.get_json() or {}

    repository = EmergencyContactRepository()
    contact = repository.update(
        contact_id,
        user_id,
        nom=donnees.get("nom"),
        telephone=donnees.get("telephone"),
        lien_parente=donnees.get("lien_parente"),
        priorite=donnees.get("priorite"),
    )

    if not contact:
        return jsonify({"erreur": "Contact introuvable."}), 404

    return jsonify(_serialiser_contact(contact))


@emergency_contact_bp.route("/<contact_id>", methods=["DELETE"])
@jwt_required()
def supprimer_contact(contact_id: str):
    """Supprime un contact d'urgence appartenant à l'utilisateur connecté."""
    user_id = get_jwt_identity()
    repository = EmergencyContactRepository()
    succes = repository.delete(contact_id, user_id)

    if not succes:
        return jsonify({"erreur": "Contact introuvable."}), 404

    return jsonify({"message": "Contact supprimé avec succès."})
