"""Routes API pour l'authentification."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt, get_jwt_identity

from app.application.services.auth_service import AuthService
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.database.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


def _get_auth_service() -> AuthService:
    return AuthService(UserRepository())


@auth_bp.route("/register", methods=["POST"])
def register():
    """Inscrit un nouvel utilisateur (citoyen par défaut)."""
    donnees = request.get_json() or {}

    champs_requis = ["nom", "telephone", "mot_de_passe"]
    manquants = [champ for champ in champs_requis if champ not in donnees]
    if manquants:
        return jsonify({"erreur": f"Champs manquants : {', '.join(manquants)}"}), 400

    service = _get_auth_service()
    try:
        user = service.inscrire(
            nom=donnees["nom"],
            telephone=donnees["telephone"],
            mot_de_passe=donnees["mot_de_passe"],
            email=donnees.get("email"),
            # le rôle "admin"/"personnel_sante" ne doit jamais être auto-attribuable
            # à l'inscription publique -> forcé à "citoyen"
            role="citoyen",
        )
    except ValueError as erreur:
        return jsonify({"erreur": str(erreur)}), 400

    return (
        jsonify(
            {
                "id": user.id,
                "nom": user.nom,
                "telephone": user.telephone,
                "role": user.role,
            }
        ),
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authentifie un utilisateur et retourne les tokens JWT."""
    donnees = request.get_json() or {}

    if "telephone" not in donnees or "mot_de_passe" not in donnees:
        return jsonify({"erreur": "Téléphone et mot de passe requis."}), 400

    service = _get_auth_service()
    try:
        resultat = service.connecter(donnees["telephone"], donnees["mot_de_passe"])
    except ValueError as erreur:
        return jsonify({"erreur": str(erreur)}), 401

    user = resultat["user"]
    return jsonify(
        {
            "access_token": resultat["access_token"],
            "refresh_token": resultat["refresh_token"],
            "user": {
                "id": user.id,
                "nom": user.nom,
                "telephone": user.telephone,
                "role": user.role,
            },
        }
    )


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Génère un nouveau access_token à partir d'un refresh_token valide."""
    identity = get_jwt_identity()
    claims = get_jwt()
    nouveau_token = create_access_token(
        identity=identity,
        additional_claims={"role": claims.get("role"), "nom": claims.get("nom")},
    )
    return jsonify({"access_token": nouveau_token})


@auth_bp.route("/users", methods=["GET"])
@jwt_required()
def lister_utilisateurs():
    """Liste tous les utilisateurs inscrits (réservé aux administrateurs)."""
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"erreur": "Accès refusé : permissions insuffisantes."}), 403

    utilisateurs = User.query.order_by(User.created_at.desc()).all()

    return jsonify(
        [
            {
                "id": u.id,
                "nom": u.nom,
                "telephone": u.telephone,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
            }
            for u in utilisateurs
        ]
    )


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def mon_profil():
    """Retourne le profil de l'utilisateur actuellement connecté."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"erreur": "Utilisateur introuvable."}), 404

    return jsonify(
        {
            "id": user.id,
            "nom": user.nom,
            "telephone": user.telephone,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
        }
    )


@auth_bp.route("/me", methods=["PUT"])
@jwt_required()
def modifier_mon_profil():
    """Permet à l'utilisateur connecté de modifier son nom et son email."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"erreur": "Utilisateur introuvable."}), 404

    donnees = request.get_json() or {}

    if "nom" in donnees:
        nom = donnees["nom"].strip()
        if not nom:
            return jsonify({"erreur": "Le nom ne peut pas être vide."}), 400
        user.nom = nom

    if "email" in donnees:
        user.email = donnees["email"].strip() or None

    from app import db
    db.session.commit()

    return jsonify(
        {
            "id": user.id,
            "nom": user.nom,
            "telephone": user.telephone,
            "email": user.email,
            "role": user.role,
        }
    )
