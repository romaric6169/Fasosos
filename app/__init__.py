import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config_by_name

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])


def create_app(config_name: str | None = None) -> Flask:
    """Application factory FasoSOS."""
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    # CORS restreint : seules les origines explicitement autorisées peuvent
    # appeler l'API depuis un navigateur (protège contre les appels croisés
    # non désirés depuis un site tiers).
    origines_autorisees = app.config.get("ORIGINES_AUTORISEES", ["http://127.0.0.1:5000", "http://localhost:5000"])
    CORS(app, resources={r"/api/*": {"origins": origines_autorisees}})

    # En-têtes de sécurité HTTP sur chaque réponse
    @app.after_request
    def ajouter_entetes_securite(reponse):
        reponse.headers["X-Content-Type-Options"] = "nosniff"
        reponse.headers["X-Frame-Options"] = "DENY"
        reponse.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        reponse.headers["Permissions-Policy"] = "geolocation=(self)"
        if not app.debug:
            reponse.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return reponse

    # Import des modèles pour que Flask-Migrate les détecte
    from app.infrastructure.database import models  # noqa: F401

    # Blueprints API
    from app.interfaces.api.v1.sos_routes import sos_bp
    app.register_blueprint(sos_bp)

    from app.interfaces.api.v1.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.interfaces.api.v1.health_center_routes import health_center_bp
    app.register_blueprint(health_center_bp)

    from app.interfaces.api.v1.emergency_contact_routes import emergency_contact_bp
    app.register_blueprint(emergency_contact_bp)

    from app.interfaces.api.v1.chatbot_routes import chatbot_bp
    app.register_blueprint(chatbot_bp)

    from app.interfaces.api.v1.audit_routes import audit_bp
    app.register_blueprint(audit_bp)

    # Limitation de débit ciblée sur les routes sensibles (anti brute-force)
    limiter.limit("10 per minute")(auth_bp)
    limiter.limit("5 per minute")(sos_bp)

    # Blueprint web (pages HTML)
    from app.interfaces.web.routes import web_bp
    app.register_blueprint(web_bp)

    return app
