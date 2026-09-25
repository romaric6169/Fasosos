"""Décorateurs de contrôle d'accès par rôle."""
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity

from app.infrastructure.security.audit_logger import AuditLogger


def role_required(*roles_autorises: str):
    """
    Restreint l'accès à une route aux utilisateurs possédant l'un des rôles
    passés en argument. Doit être utilisé après @jwt_required().

    Exemple : @role_required("admin", "personnel_sante")
    """

    def decorateur(fonction):
        @wraps(fonction)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role_utilisateur = claims.get("role")

            if role_utilisateur not in roles_autorises:
                AuditLogger.enregistrer(
                    "acces_refuse",
                    details=f"Rôle '{role_utilisateur}' a tenté d'accéder à {request.path} (rôles requis : {', '.join(roles_autorises)}).",
                    user_id=get_jwt_identity(),
                )
                return jsonify({"erreur": "Accès refusé : permissions insuffisantes."}), 403

            return fonction(*args, **kwargs)

        return wrapper

    return decorateur
