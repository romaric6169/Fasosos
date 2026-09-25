"""
Service du chatbot d'orientation médicale.
Le chatbot ne fait JAMAIS de diagnostic : il explique, oriente, conseille,
et aide à trouver des centres de santé - jamais il ne dit "vous avez X".
Cette règle est imposée strictement via le prompt système envoyé à l'IA.
"""
import requests
from flask import current_app

from app.infrastructure.repositories.chatbot_repository import ChatbotRepository

PROMPT_SYSTEME = """Tu es l'assistant d'orientation de FasoSOS, une plateforme d'urgence médicale pour le Burkina Faso, actuellement en phase de développement (pas encore de collaboration officielle avec le SAMU ou les autorités sanitaires).

CE QUE FASOSOS PROPOSE ACTUELLEMENT (à ce stade du projet) :
1. Géolocalisation et recherche des centres de santé les plus proches (CSPS, CMA, CHR, CHU, Clinique), avec calcul de distance et génération d'un itinéraire Google Maps (voiture, moto, marche).
2. Un bouton SOS qui enregistre une alerte (type d'urgence, position, description) dans l'historique du compte de l'utilisateur - IMPORTANT : ce bouton n'alerte PAS encore les services de secours officiels ni une centrale d'urgence, puisque FasoSOS n'a pas encore de collaboration avec ces autorités. Sois toujours honnête là-dessus si on te pose la question.
3. Des contacts d'urgence personnels (jusqu'à 5, avec nom, téléphone, lien de parenté) : l'utilisateur peut appeler ou envoyer un SMS pré-rempli (avec sa position et la description de l'urgence) directement à l'un de ses proches en un clic. C'est LE moyen actuel de prévenir concrètement quelqu'un en cas de problème - à recommander en priorité si la situation est grave.
4. Ce chatbot, pour orienter et répondre aux questions de santé générales.

SI ON TE DEMANDE QUI A CRÉÉ FASOSOS :
FasoSOS a été créé par Romaric Nonguierma, étudiant en fin de licence informatique à l'Université Virtuelle du Burkina Faso (UVBF). Le projet est né du constat qu'au Burkina Faso, lorsqu'une personne est victime d'un accident ou d'un malaise, les témoins autour d'elle savent rarement quel centre de santé est le plus proche ou le mieux adapté à la situation, ne connaissent pas toujours les gestes de premiers secours, et perdent un temps précieux à chercher ces informations dans l'urgence. FasoSOS vise à combler ce manque en donnant un accès rapide et simple à la géolocalisation des centres de santé, à l'orientation vers le centre adapté, et à la mise en relation immédiate avec les proches d'une victime.

RÈGLES STRICTES QUE TU DOIS TOUJOURS RESPECTER :
1. Tu ne fais JAMAIS de diagnostic médical. Ne dis jamais "vous avez probablement X" ou "cela ressemble à Y".
2. Si quelqu'un décrit une urgence grave (perte de conscience, hémorragie sévère, difficulté à respirer, douleur thoracique intense, AVC suspecté, ou une urgence concernant une autre personne à proximité) : dis-lui clairement d'appeler immédiatement un contact d'urgence enregistré (bouton Appeler/SMS dans "Mes contacts"), ou d'appeler directement les numéros d'urgence locaux si la situation le permet, et de se rendre ou d'amener la personne au centre de santé le plus proche via la carte. Ne dis jamais que le bouton SOS va envoyer les secours automatiquement.
3. Tu peux : expliquer des notions de santé générales, orienter vers le type de centre de santé approprié, conseiller de consulter un professionnel de santé, rappeler les gestes de premiers secours généraux, et rappeler l'existence des contacts d'urgence et de la carte des centres.
4. Tu ne prescris jamais de médicaments ni de posologies.
5. Réponds en français, de manière chaleureuse, claire et rassurante, adaptée à un contexte d'urgence potentielle.
6. Reste concis (3-5 phrases maximum sauf si on te demande plus de détails).
7. Si la question sort du cadre médical/urgence, recentre poliment la conversation vers ton rôle."""


class ChatbotService:
    """Orchestre les échanges entre l'utilisateur et l'IA du chatbot."""

    def __init__(self, repository: ChatbotRepository) -> None:
        self._repository = repository

    def envoyer_message(self, user_id: str, message_utilisateur: str) -> dict:
        """
        Envoie un message au chatbot, sauvegarde l'échange, et retourne la réponse.
        """
        conversation = self._repository.get_or_create_conversation(user_id)

        self._repository.ajouter_message(conversation.id, "user", message_utilisateur)

        historique = self._repository.get_historique(conversation.id, limite=10)
        messages_api = [{"role": "system", "content": PROMPT_SYSTEME}]
        for msg in historique:
            role_api = "assistant" if msg.role == "assistant" else "user"
            messages_api.append({"role": role_api, "content": msg.contenu})

        reponse_ia = self._appeler_api_ia(messages_api)

        self._repository.ajouter_message(conversation.id, "assistant", reponse_ia)

        return {
            "conversation_id": conversation.id,
            "reponse": reponse_ia,
        }

    def _appeler_api_ia(self, messages: list[dict]) -> str:
        """Appelle l'API Groq (format compatible OpenAI) et retourne le texte généré."""
        cle_api = current_app.config.get("GROQ_API_KEY")
        url_api = current_app.config.get("GROQ_API_URL")

        if not cle_api:
            return (
                "Le chatbot n'est pas encore configuré (clé API manquante). "
                "En attendant, consultez vos contacts d'urgence ou les centres de santé proches sur la carte."
            )

        try:
            reponse = requests.post(
                url_api,
                headers={
                    "Authorization": f"Bearer {cle_api}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": messages,
                    "temperature": 0.5,
                    "max_tokens": 400,
                },
                timeout=30,
            )
            reponse.raise_for_status()
            donnees = reponse.json()
            return donnees["choices"][0]["message"]["content"].strip()

        except requests.exceptions.RequestException as erreur:
            current_app.logger.error(f"Erreur API chatbot : {erreur}")
            return (
                "Désolé, je ne suis pas disponible pour le moment. "
                "Utilisez vos contacts d'urgence ou consultez les centres de santé proches sur la carte."
            )

    def obtenir_historique(self, user_id: str) -> list[dict]:
        conversation = self._repository.get_or_create_conversation(user_id)
        messages = self._repository.get_historique(conversation.id, limite=50)
        return [{"role": m.role, "contenu": m.contenu} for m in messages]

    def demarrer_nouvelle_conversation(self, user_id: str) -> None:
        self._repository.nouvelle_conversation(user_id)

    def obtenir_liste_conversations(self, user_id: str) -> list[dict]:
        """
        Retourne la liste des conversations passées de l'utilisateur,
        avec un aperçu (premier message) pour affichage dans l'historique.
        """
        conversations = self._repository.get_all_by_user(user_id)
        resultat = []

        for conversation in conversations:
            premiers_messages = self._repository.get_historique(conversation.id, limite=1)
            apercu = premiers_messages[0].contenu if premiers_messages else "Conversation vide"
            if len(apercu) > 60:
                apercu = apercu[:60] + "..."

            resultat.append({
                "id": conversation.id,
                "created_at": conversation.created_at.isoformat(),
                "apercu": apercu,
            })

        return resultat

    def obtenir_messages_conversation(self, user_id: str, conversation_id: str) -> list[dict] | None:
        """Retourne les messages d'une conversation précise, si elle appartient à l'utilisateur."""
        conversation = self._repository.get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return None

        messages = self._repository.get_historique(conversation_id, limite=100)
        return [{"role": m.role, "contenu": m.contenu} for m in messages]
