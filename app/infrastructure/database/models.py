"""
Modèles SQLAlchemy - FasoSOS
Mapping ORM de la couche infrastructure. Le domaine métier (app/domain)
reste indépendant de ces modèles.
"""
import uuid
from datetime import datetime
from app import db


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(db.Model):
    """Utilisateur de la plateforme (citoyen, admin, personnel de santé)."""
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    nom = db.Column(db.String(150), nullable=False)
    telephone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="citoyen")
    # rôles possibles : citoyen | admin | personnel_sante
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contacts = db.relationship("EmergencyContact", backref="user", cascade="all, delete-orphan")
    sos_alerts = db.relationship("SosAlert", backref="user", cascade="all, delete-orphan")
    fiches_creees = db.relationship("FirstAidSheet", backref="auteur")


class EmergencyContact(db.Model):
    """Contact d'urgence d'un utilisateur (max 5, contrôlé en Service Layer)."""
    __tablename__ = "emergency_contacts"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    nom = db.Column(db.String(150), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    lien_parente = db.Column(db.String(100), nullable=True)
    priorite = db.Column(db.Integer, nullable=False, default=1)  # 1 = priorité la plus haute
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class HealthCenter(db.Model):
    """Centre de santé (CSPS, CMA, CHR, CHU, Clinique)."""
    __tablename__ = "health_centers"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    nom = db.Column(db.String(200), nullable=False)
    adresse = db.Column(db.String(255), nullable=True)
    telephone = db.Column(db.String(20), nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # CSPS | CMA | CHR | CHU | CLINIQUE
    urgence_24h = db.Column(db.Boolean, default=False)
    horaires = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    services = db.relationship("HealthCenterService", backref="health_center", cascade="all, delete-orphan")


class HealthCenterService(db.Model):
    """Service disponible dans un centre (maternité, chirurgie, pédiatrie...)."""
    __tablename__ = "health_center_services"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    health_center_id = db.Column(db.String(36), db.ForeignKey("health_centers.id"), nullable=False)
    service = db.Column(db.String(100), nullable=False)


class Pharmacy(db.Model):
    """Pharmacie."""
    __tablename__ = "pharmacies"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    nom = db.Column(db.String(200), nullable=False)
    adresse = db.Column(db.String(255), nullable=True)
    telephone = db.Column(db.String(20), nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    garde = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SosAlert(db.Model):
    """Alerte SOS déclenchée par un citoyen."""
    __tablename__ = "sos_alerts"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    type_urgence = db.Column(db.String(50), nullable=False)
    # Accident | AVC | Brulure | Fracture | Hemorragie | Morsure | Fievre | Autre
    type_centre_souhaite = db.Column(db.String(20), nullable=True)  # CSPS | CMA | CHR | CHU | CLINIQUE
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    statut = db.Column(db.String(20), default="en_cours")  # en_cours | resolue | annulee
    contact_urgence_id = db.Column(db.String(36), db.ForeignKey("emergency_contacts.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contact_urgence = db.relationship("EmergencyContact")


class FirstAidSheet(db.Model):
    """Fiche de premiers secours. Peut être créée/modifiée par un admin ou un personnel de santé."""
    __tablename__ = "first_aid_sheets"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    symptomes = db.Column(db.Text, nullable=True)
    gestes_a_faire = db.Column(db.Text, nullable=True)
    gestes_interdits = db.Column(db.Text, nullable=True)
    quand_consulter = db.Column(db.Text, nullable=True)
    illustration_url = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FirstAidRecommendedCenter(db.Model):
    """Table d'association : centres recommandés pour une fiche de premiers secours."""
    __tablename__ = "first_aid_recommended_centers"

    first_aid_sheet_id = db.Column(db.String(36), db.ForeignKey("first_aid_sheets.id"), primary_key=True)
    health_center_id = db.Column(db.String(36), db.ForeignKey("health_centers.id"), primary_key=True)


class ChatbotConversation(db.Model):
    """Une conversation entre un utilisateur et le chatbot d'orientation."""
    __tablename__ = "chatbot_conversations"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship(
        "ChatbotMessage", backref="conversation", cascade="all, delete-orphan",
        order_by="ChatbotMessage.created_at"
    )


class ChatbotMessage(db.Model):
    """Un message individuel dans une conversation avec le chatbot."""
    __tablename__ = "chatbot_messages"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    conversation_id = db.Column(db.String(36), db.ForeignKey("chatbot_conversations.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "user" ou "assistant"
    contenu = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    """Journal des événements de sécurité : connexions échouées, accès refusés,
    dépassements de limite de débit - pour détection et correction ultérieure."""
    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    type_evenement = db.Column(db.String(50), nullable=False)
    # connexion_echouee | acces_refuse | limite_debit_depassee | inscription | connexion_reussie
    details = db.Column(db.Text, nullable=True)
    adresse_ip = db.Column(db.String(45), nullable=True)
    telephone_cible = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
