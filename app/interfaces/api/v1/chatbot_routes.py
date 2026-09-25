"""Routes API pour le chatbot d'orientation."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.application.services.chatbot_service import ChatbotService
from app.infrastructure.repositories.chatbot_repository import ChatbotRepository

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/v1/chatbot")


def _get_chatbot_service() -> ChatbotService:
    return ChatbotService(ChatbotRepository())


@chatbot_bp.route("/message", methods=["POST"])
@jwt_required()
def envoyer_message():
    """Envoie un message au chatbot et retourne sa réponse."""
    user_id = get_jwt_identity()
    donnees = request.get_json() or {}

    message = donnees.get("message", "").strip()
    if not message:
        return jsonify({"erreur": "Le message ne peut pas être vide."}), 400

    service = _get_chatbot_service()
    resultat = service.envoyer_message(user_id, message)

    return jsonify(resultat)


@chatbot_bp.route("/history", methods=["GET"])
@jwt_required()
def historique():
    """Retourne l'historique de la conversation active de l'utilisateur."""
    user_id = get_jwt_identity()
    service = _get_chatbot_service()
    messages = service.obtenir_historique(user_id)

    return jsonify(messages)


@chatbot_bp.route("/new", methods=["POST"])
@jwt_required()
def nouvelle_conversation():
    """Démarre une nouvelle conversation (efface le contexte précédent)."""
    user_id = get_jwt_identity()
    service = _get_chatbot_service()
    service.demarrer_nouvelle_conversation(user_id)

    return jsonify({"message": "Nouvelle conversation démarrée."})


@chatbot_bp.route("/conversations", methods=["GET"])
@jwt_required()
def lister_conversations():
    """Liste toutes les conversations passées de l'utilisateur connecté."""
    user_id = get_jwt_identity()
    service = _get_chatbot_service()
    conversations = service.obtenir_liste_conversations(user_id)

    return jsonify(conversations)


@chatbot_bp.route("/conversations/<conversation_id>/messages", methods=["GET"])
@jwt_required()
def messages_conversation(conversation_id: str):
    """Retourne les messages d'une conversation passée précise."""
    user_id = get_jwt_identity()
    service = _get_chatbot_service()
    messages = service.obtenir_messages_conversation(user_id, conversation_id)

    if messages is None:
        return jsonify({"erreur": "Conversation introuvable."}), 404

    return jsonify(messages)
