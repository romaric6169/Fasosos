"""Routes API pour la consultation du journal de sécurité (admin uniquement)."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.infrastructure.database.models import AuditLog
from app.infrastructure.security.decorators import role_required

audit_bp = Blueprint("audit", __name__, url_prefix="/api/v1/audit")


@audit_bp.route("/logs", methods=["GET"])
@jwt_required()
@role_required("admin")
def lister_logs():
    """
    Liste les événements de sécurité, les plus récents en premier.
    Filtrable par type via ?type=connexion_echouee, et paginé via ?page=1&par_page=50.
    """
    type_filtre = request.args.get("type")
    page = request.args.get("page", 1, type=int)
    par_page = min(request.args.get("par_page", 50, type=int), 200)

    requete = AuditLog.query.order_by(AuditLog.created_at.desc())
    if type_filtre:
        requete = requete.filter_by(type_evenement=type_filtre)

    resultat_page = requete.paginate(page=page, per_page=par_page, error_out=False)

    return jsonify(
        {
            "total": resultat_page.total,
            "page": page,
            "par_page": par_page,
            "logs": [
                {
                    "id": log.id,
                    "type_evenement": log.type_evenement,
                    "details": log.details,
                    "adresse_ip": log.adresse_ip,
                    "telephone_cible": log.telephone_cible,
                    "user_id": log.user_id,
                    "created_at": log.created_at.isoformat(),
                }
                for log in resultat_page.items
            ],
        }
    )


@audit_bp.route("/logs/resume", methods=["GET"])
@jwt_required()
@role_required("admin")
def resume_securite():
    """Retourne un résumé rapide : nombre d'événements par type sur les dernières 24h/7j."""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from app import db

    il_y_a_24h = datetime.utcnow() - timedelta(hours=24)
    il_y_a_7j = datetime.utcnow() - timedelta(days=7)

    def compter_par_type(depuis):
        resultats = (
            db.session.query(AuditLog.type_evenement, func.count(AuditLog.id))
            .filter(AuditLog.created_at >= depuis)
            .group_by(AuditLog.type_evenement)
            .all()
        )
        return {type_evt: nombre for type_evt, nombre in resultats}

    return jsonify(
        {
            "derniere_24h": compter_par_type(il_y_a_24h),
            "derniers_7_jours": compter_par_type(il_y_a_7j),
        }
    )
