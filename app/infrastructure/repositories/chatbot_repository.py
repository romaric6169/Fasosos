"""Repository pour l'accès aux données du chatbot."""
from app.infrastructure.database.models import ChatbotConversation, ChatbotMessage
from app import db


class ChatbotRepository:
    """Isole l'accès aux données ChatbotConversation/ChatbotMessage."""

    def get_or_create_conversation(self, user_id: str) -> ChatbotConversation:
        conversation = (
            ChatbotConversation.query.filter_by(user_id=user_id)
            .order_by(ChatbotConversation.created_at.desc())
            .first()
        )
        if conversation:
            return conversation

        conversation = ChatbotConversation(user_id=user_id)
        db.session.add(conversation)
        db.session.commit()
        return conversation

    def ajouter_message(self, conversation_id: str, role: str, contenu: str) -> ChatbotMessage:
        message = ChatbotMessage(conversation_id=conversation_id, role=role, contenu=contenu)
        db.session.add(message)
        db.session.commit()
        return message

    def get_historique(self, conversation_id: str, limite: int = 20) -> list[ChatbotMessage]:
        messages = (
            ChatbotMessage.query.filter_by(conversation_id=conversation_id)
            .order_by(ChatbotMessage.created_at.desc())
            .limit(limite)
            .all()
        )
        return list(reversed(messages))

    def nouvelle_conversation(self, user_id: str) -> ChatbotConversation:
        conversation = ChatbotConversation(user_id=user_id)
        db.session.add(conversation)
        db.session.commit()
        return conversation

    def get_all_by_user(self, user_id: str) -> list[ChatbotConversation]:
        """Retourne toutes les conversations de l'utilisateur, la plus récente en premier."""
        return (
            ChatbotConversation.query.filter_by(user_id=user_id)
            .order_by(ChatbotConversation.created_at.desc())
            .all()
        )

    def get_conversation_by_id(self, conversation_id: str, user_id: str) -> ChatbotConversation | None:
        """Récupère une conversation précise, uniquement si elle appartient bien à l'utilisateur."""
        conversation = ChatbotConversation.query.get(conversation_id)
        if not conversation or conversation.user_id != user_id:
            return None
        return conversation
