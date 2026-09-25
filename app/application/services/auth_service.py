"""
Service d'authentification : inscription, connexion, génération de tokens JWT.
"""
import re
from flask_jwt_extended import create_access_token, create_refresh_token

from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.password_hasher import PasswordHasher
from app.infrastructure.security.audit_logger import AuditLogger
from app.infrastructure.database.models import User


class AuthService:
    """Gère l'inscription et la connexion des utilisateurs."""

    TELEPHONE_REGEX = re.compile(r"^\+?226?\d{8}$")

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def inscrire(
        self,
        nom: str,
        telephone: str,
        mot_de_passe: str,
        email: str | None = None,
        role: str = "citoyen",
    ) -> User:
        """Crée un nouvel utilisateur après validation des règles métier."""
        if not self.TELEPHONE_REGEX.match(telephone):
            raise ValueError("Numéro de téléphone invalide.")

        if self._user_repository.exists_telephone(telephone):
            AuditLogger.enregistrer(
                "inscription_refusee",
                details="Tentative d'inscription avec un numéro déjà utilisé.",
                telephone_cible=telephone,
            )
            raise ValueError("Ce numéro de téléphone est déjà utilisé.")

        if len(mot_de_passe) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")

        if role not in ("citoyen", "admin", "personnel_sante"):
            raise ValueError("Rôle invalide.")

        mot_de_passe_hash = PasswordHasher.hash(mot_de_passe)

        user = self._user_repository.create(
            nom=nom,
            telephone=telephone,
            email=email,
            mot_de_passe_hash=mot_de_passe_hash,
            role=role,
        )

        AuditLogger.enregistrer(
            "inscription",
            details=f"Nouveau compte créé : {nom}",
            telephone_cible=telephone,
            user_id=user.id,
        )

        return user

    def connecter(self, telephone: str, mot_de_passe: str) -> dict:
        """Authentifie un utilisateur et retourne ses tokens JWT."""
        user = self._user_repository.get_by_telephone(telephone)

        if not user or not PasswordHasher.verifier(mot_de_passe, user.mot_de_passe_hash):
            AuditLogger.enregistrer(
                "connexion_echouee",
                details="Téléphone ou mot de passe incorrect.",
                telephone_cible=telephone,
            )
            raise ValueError("Téléphone ou mot de passe incorrect.")

        if not user.is_active:
            AuditLogger.enregistrer(
                "connexion_refusee",
                details="Tentative de connexion sur un compte désactivé.",
                telephone_cible=telephone,
                user_id=user.id,
            )
            raise ValueError("Ce compte a été désactivé.")

        AuditLogger.enregistrer(
            "connexion_reussie",
            telephone_cible=telephone,
            user_id=user.id,
        )

        claims = {"role": user.role, "nom": user.nom}
        access_token = create_access_token(identity=user.id, additional_claims=claims)
        refresh_token = create_refresh_token(identity=user.id, additional_claims=claims)

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
