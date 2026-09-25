"""Routes web (rendu de templates HTML) - séparées des routes API JSON."""
from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def accueil():
    """Page principale : carte + géolocalisation + bouton SOS."""
    return render_template("index.html")


@web_bp.route("/connexion")
def connexion():
    """Page de connexion."""
    return render_template("login.html")


@web_bp.route("/inscription")
def inscription():
    """Page d'inscription."""
    return render_template("register.html")


@web_bp.route("/admin")
def admin_dashboard():
    """Dashboard admin. Le contrôle du rôle est fait côté JS (token) et vérifié
    à nouveau par chaque appel API protégé (@role_required('admin'))."""
    return render_template("admin.html")


@web_bp.route("/profil")
def profil():
    """Page de profil de l'utilisateur connecté."""
    return render_template("profil.html")


@web_bp.route("/contacts")
def contacts_apercu():
    """Vue rapide (lecture seule) des contacts d'urgence : appeler/SMS uniquement.
    Accessible depuis l'accueil pour une action rapide en situation d'urgence."""
    return render_template("contacts_apercu.html")


@web_bp.route("/contacts/gerer")
def contacts_gestion():
    """Page complète de gestion des contacts d'urgence (ajout/modification/suppression).
    Accessible uniquement depuis le profil."""
    return render_template("contacts.html")
