"""Routes API pour la recherche et la gestion des centres de santé."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.application.services.ranking_service import RankingService
from app.application.services.map_link_service import MapLinkService
from app.infrastructure.repositories.health_center_repository import HealthCenterRepository
from app.domain.value_objects.gps_coordinates import GpsCoordinates
from app.domain.value_objects.coordinate_parser import CoordinateParser
from app.infrastructure.security.decorators import role_required

health_center_bp = Blueprint("health_centers", __name__, url_prefix="/api/v1/health-centers")


def _serialiser_centre(item: dict, map_service: MapLinkService) -> dict:
    """Transforme un résultat de classement en JSON exposable côté API."""
    centre = item["centre"]
    position = GpsCoordinates(centre.latitude, centre.longitude)

    return {
        "id": centre.id,
        "nom": centre.nom,
        "adresse": centre.adresse,
        "telephone": centre.telephone,
        "latitude": centre.latitude,
        "longitude": centre.longitude,
        "type": centre.type,
        "urgence_24h": centre.urgence_24h,
        "horaires": centre.horaires,
        "distance_km": item["distance_km"],
        "type_correspond": item["type_correspond"],
        "lien_fiche_maps": map_service.lien_fiche_centre(position),
        "services": [s.service for s in centre.services],
    }


@health_center_bp.route("/nearby", methods=["GET"])
@jwt_required()
def centres_proximite():
    """
    Retourne les centres de santé classés par proximité.
    Query params : lat, lng, type_centre_souhaite (optionnel)
    """
    try:
        latitude = CoordinateParser.nettoyer_et_valider_latitude(request.args["lat"])
        longitude = CoordinateParser.nettoyer_et_valider_longitude(request.args["lng"])
    except KeyError:
        return jsonify({"erreur": "Paramètres lat et lng requis."}), 400
    except ValueError as erreur:
        return jsonify({"erreur": str(erreur)}), 400

    type_centre_souhaite = request.args.get("type_centre_souhaite")

    position_utilisateur = GpsCoordinates(latitude, longitude)
    repository = HealthCenterRepository()
    centres = repository.get_all_actifs()

    ranking_service = RankingService()
    resultats = ranking_service.classer_centres(
        position_utilisateur=position_utilisateur,
        type_centre_souhaite=type_centre_souhaite,
        centres=centres,
    )

    map_service = MapLinkService()

    return jsonify(
        {
            "plus_proches": [_serialiser_centre(c, map_service) for c in resultats["plus_proches"]],
            "type_demande": [_serialiser_centre(c, map_service) for c in resultats["type_demande"]],
        }
    )


@health_center_bp.route("/<centre_id>/itineraire", methods=["GET"])
@jwt_required()
def itineraire_vers_centre(centre_id: str):
    """
    Génère le lien Google Maps d'itinéraire vers un centre.
    Query params : lat, lng (position actuelle utilisateur), mode (voiture|moto|marche)
    """
    try:
        latitude = CoordinateParser.nettoyer_et_valider_latitude(request.args["lat"])
        longitude = CoordinateParser.nettoyer_et_valider_longitude(request.args["lng"])
    except KeyError:
        return jsonify({"erreur": "Paramètres lat et lng requis."}), 400
    except ValueError as erreur:
        return jsonify({"erreur": str(erreur)}), 400

    mode = request.args.get("mode", "voiture")
    if mode not in ("voiture", "moto", "marche"):
        return jsonify({"erreur": "Mode invalide. Valeurs acceptées : voiture, moto, marche."}), 400

    repository = HealthCenterRepository()
    centre = repository.get_by_id(centre_id)
    if not centre:
        return jsonify({"erreur": "Centre introuvable."}), 404

    origine = GpsCoordinates(latitude, longitude)
    destination = GpsCoordinates(centre.latitude, centre.longitude)

    map_service = MapLinkService()
    lien = map_service.lien_itineraire(origine, destination, mode)

    reponse = {"lien_itineraire": lien, "mode": mode}
    if mode == "moto":
        reponse["info"] = "Google Maps ne propose pas de mode moto dédié ; l'itinéraire voiture est utilisé."

    return jsonify(reponse)


@health_center_bp.route("", methods=["POST"])
@jwt_required()
@role_required("admin")
def creer_centre():
    """Crée un centre de santé (réservé aux administrateurs)."""
    donnees = request.get_json() or {}

    champs_requis = ["nom", "latitude", "longitude", "type"]
    manquants = [champ for champ in champs_requis if champ not in donnees]
    if manquants:
        return jsonify({"erreur": f"Champs manquants : {', '.join(manquants)}"}), 400

    types_valides = ("CSPS", "CMA", "CHR", "CHU", "CLINIQUE")
    if donnees["type"] not in types_valides:
        return jsonify({"erreur": f"Type invalide. Valeurs acceptées : {', '.join(types_valides)}"}), 400

    try:
        latitude = CoordinateParser.nettoyer_et_valider_latitude(donnees["latitude"])
        longitude = CoordinateParser.nettoyer_et_valider_longitude(donnees["longitude"])
    except ValueError as erreur:
        return jsonify({"erreur": str(erreur)}), 400

    repository = HealthCenterRepository()
    centre = repository.create(
        nom=donnees["nom"],
        adresse=donnees.get("adresse"),
        telephone=donnees.get("telephone"),
        latitude=latitude,
        longitude=longitude,
        type=donnees["type"],
        urgence_24h=donnees.get("urgence_24h", False),
        horaires=donnees.get("horaires"),
    )

    map_service = MapLinkService()
    position = GpsCoordinates(centre.latitude, centre.longitude)

    return (
        jsonify(
            {
                "id": centre.id,
                "nom": centre.nom,
                "type": centre.type,
                "latitude": centre.latitude,
                "longitude": centre.longitude,
                "lien_fiche_maps": map_service.lien_fiche_centre(position),
            }
        ),
        201,
    )


@health_center_bp.route("", methods=["GET"])
@jwt_required()
@role_required("admin")
def lister_centres():
    """Liste tous les centres de santé (réservé aux administrateurs)."""
    repository = HealthCenterRepository()
    centres = repository.get_all_actifs()

    return jsonify(
        [
            {
                "id": c.id,
                "nom": c.nom,
                "adresse": c.adresse,
                "telephone": c.telephone,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "type": c.type,
                "urgence_24h": c.urgence_24h,
                "horaires": c.horaires,
            }
            for c in centres
        ]
    )


@health_center_bp.route("/<centre_id>", methods=["GET"])
@jwt_required()
@role_required("admin")
def obtenir_centre(centre_id: str):
    """Retourne le détail d'un centre (pour pré-remplir le formulaire d'édition)."""
    repository = HealthCenterRepository()
    centre = repository.get_by_id(centre_id)
    if not centre:
        return jsonify({"erreur": "Centre introuvable."}), 404

    return jsonify(
        {
            "id": centre.id,
            "nom": centre.nom,
            "adresse": centre.adresse,
            "telephone": centre.telephone,
            "latitude": centre.latitude,
            "longitude": centre.longitude,
            "type": centre.type,
            "urgence_24h": centre.urgence_24h,
            "horaires": centre.horaires,
        }
    )


@health_center_bp.route("/<centre_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def modifier_centre(centre_id: str):
    """Modifie un centre de santé existant (réservé aux administrateurs)."""
    donnees = request.get_json() or {}

    champs_a_mettre_a_jour = {}

    if "nom" in donnees:
        champs_a_mettre_a_jour["nom"] = donnees["nom"]
    if "adresse" in donnees:
        champs_a_mettre_a_jour["adresse"] = donnees["adresse"]
    if "telephone" in donnees:
        champs_a_mettre_a_jour["telephone"] = donnees["telephone"]
    if "horaires" in donnees:
        champs_a_mettre_a_jour["horaires"] = donnees["horaires"]
    if "urgence_24h" in donnees:
        champs_a_mettre_a_jour["urgence_24h"] = donnees["urgence_24h"]

    if "type" in donnees:
        types_valides = ("CSPS", "CMA", "CHR", "CHU", "CLINIQUE")
        if donnees["type"] not in types_valides:
            return jsonify({"erreur": f"Type invalide. Valeurs acceptées : {', '.join(types_valides)}"}), 400
        champs_a_mettre_a_jour["type"] = donnees["type"]

    if "latitude" in donnees:
        try:
            champs_a_mettre_a_jour["latitude"] = CoordinateParser.nettoyer_et_valider_latitude(donnees["latitude"])
        except ValueError as erreur:
            return jsonify({"erreur": str(erreur)}), 400

    if "longitude" in donnees:
        try:
            champs_a_mettre_a_jour["longitude"] = CoordinateParser.nettoyer_et_valider_longitude(donnees["longitude"])
        except ValueError as erreur:
            return jsonify({"erreur": str(erreur)}), 400

    repository = HealthCenterRepository()
    centre = repository.update(centre_id, **champs_a_mettre_a_jour)

    if not centre:
        return jsonify({"erreur": "Centre introuvable."}), 404

    return jsonify(
        {
            "id": centre.id,
            "nom": centre.nom,
            "type": centre.type,
            "latitude": centre.latitude,
            "longitude": centre.longitude,
        }
    )


@health_center_bp.route("/<centre_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def supprimer_centre(centre_id: str):
    """Supprime un centre de santé (réservé aux administrateurs)."""
    repository = HealthCenterRepository()
    succes = repository.delete(centre_id)

    if not succes:
        return jsonify({"erreur": "Centre introuvable."}), 404

    return jsonify({"message": "Centre supprimé avec succès."})
