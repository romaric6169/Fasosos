"""
Script d'import des centres de santé récupérés via OpenStreetMap
(centres_burkina_faso_osm.json) dans la base FasoSOS.

Filtre les entrées non pertinentes (départements internes d'hôpitaux,
entrées non médicales), déduit le type burkinabè (CSPS/CMA/CHR/CHU/CLINIQUE)
à partir du nom en priorité, puis du type OSM en repli. Nettoie les champs
trop longs pour respecter les limites des colonnes PostgreSQL.

Usage : python3 scripts_import_centres.py [--dry-run]
"""
import json
import re
import sys

from app import create_app, db
from app.infrastructure.database.models import HealthCenter
from app.domain.value_objects.coordinate_parser import CoordinateParser

FICHIER_SOURCE = "centres_burkina_faso_osm.json"

NOMS_EXCLUS = {
    "consultation externe", "urgence", "urgences", "pédiatrie", "pédiatrie 1",
    "pédiatrie 2", "pediatria", "pediatria 1", "pediatria 2", "maternité",
    "laboratoire", "bloc opératoire", "bloque cirurgical", "cardiologie",
    "radiologie", "pneumologie", "ophtalmologie", "oftalmologia", "caisse",
    "accueil service renseignement", "consultation", "consultation orl",
    "ecographie general", "salle des urgences", "salle de isolement",
    "salle de recuperacion post-operatoire", "sala de observação / urgência",
    "service tuberculose", "service d'urgence", "picu",
    "madame voyante", "monreé hors bouls", "reboutair", "h",
    "mutuelle sante afrique",
}

REGLES_NOM = [
    (r"\bCHU\b", "CHU"),
    (r"\bCHR\b", "CHR"),
    (r"centre hospitalier r[ée]gional", "CHR"),
    (r"centre hospitalier universitaire", "CHU"),
    (r"\bCMA\b", "CMA"),
    (r"\bCSPS\b", "CSPS"),
    (r"clinique|cabinet m[ée]dical|polyclinique|cabinet de soins", "CLINIQUE"),
    (r"h[oô]pital", "CHR"),
]

MAPPING_TYPE_OSM_PAR_DEFAUT = {
    "hospital": "CMA",
    "clinic": "CLINIQUE",
    "doctors": "CLINIQUE",
    "centre": "CLINIQUE",
    "doctor": "CLINIQUE",
}


def deduire_type(nom: str, type_osm: str) -> str:
    for motif, type_resultat in REGLES_NOM:
        if re.search(motif, nom, re.IGNORECASE):
            return type_resultat
    return MAPPING_TYPE_OSM_PAR_DEFAUT.get(type_osm, "CLINIQUE")


def nom_est_exclu(nom: str) -> bool:
    return nom.strip().lower() in NOMS_EXCLUS


def dedupliquer_par_proximite(centres: list[dict], seuil_metres: float = 100) -> list[dict]:
    import math

    def distance_approx_m(lat1, lon1, lat2, lon2):
        dlat = (lat2 - lat1) * 111_000
        dlon = (lon2 - lon1) * 111_000 * math.cos(math.radians(lat1))
        return math.sqrt(dlat**2 + dlon**2)

    resultat = []
    for centre in centres:
        doublon = False
        for existant in resultat:
            if existant["nom"].strip().lower() == centre["nom"].strip().lower():
                if distance_approx_m(
                    existant["latitude"], existant["longitude"],
                    centre["latitude"], centre["longitude"]
                ) < seuil_metres:
                    doublon = True
                    break
        if not doublon:
            resultat.append(centre)

    return resultat


def preparer_centres():
    with open(FICHIER_SOURCE, "r", encoding="utf-8") as f:
        centres_bruts = json.load(f)

    centres_valides = []
    exclus_count = 0

    for centre in centres_bruts:
        nom = centre.get("nom", "").strip()
        if not nom or nom_est_exclu(nom):
            exclus_count += 1
            continue

        # OSM concatène parfois plusieurs variantes de nom séparées par ';'
        # (multi-langue, historique de renommage) -> on ne garde que la première.
        nom = nom.split(";")[0].strip()

        # Sécurité dure : respecte la limite de la colonne (String(200)).
        if len(nom) > 200:
            nom = nom[:197] + "..."

        adresse = (centre.get("adresse") or "").strip() or None
        if adresse and len(adresse) > 255:
            adresse = adresse[:255]

        telephone = (centre.get("telephone") or "").strip() or None
        if telephone:
            telephone = telephone.split(";")[0].strip()
            if len(telephone) > 20:
                telephone = telephone[:20]

        try:
            latitude = CoordinateParser.nettoyer_et_valider_latitude(centre["latitude"])
            longitude = CoordinateParser.nettoyer_et_valider_longitude(centre["longitude"])
        except (ValueError, KeyError):
            exclus_count += 1
            continue

        type_burkinabe = deduire_type(nom, centre.get("type_osm", ""))

        centres_valides.append({
            "nom": nom,
            "latitude": latitude,
            "longitude": longitude,
            "type": type_burkinabe,
            "adresse": adresse,
            "telephone": telephone,
            "urgence_24h": False,
            "horaires": None,
        })

    print(f"{exclus_count} entrées exclues (départements internes ou non-médicales).")

    avant_dedup = len(centres_valides)
    centres_valides = dedupliquer_par_proximite(centres_valides)
    print(f"{avant_dedup - len(centres_valides)} doublons proches supprimés.")

    return centres_valides


def importer(centres: list[dict], dry_run: bool = False):
    app = create_app()
    with app.app_context():
        deja_en_base = {c.nom.strip().lower() for c in HealthCenter.query.all()}

        crees = 0
        ignores_deja_presents = 0

        for centre in centres:
            if centre["nom"].strip().lower() in deja_en_base:
                ignores_deja_presents += 1
                continue

            if dry_run:
                crees += 1
                continue

            nouveau = HealthCenter(
                nom=centre["nom"],
                adresse=centre["adresse"],
                telephone=centre["telephone"],
                latitude=centre["latitude"],
                longitude=centre["longitude"],
                type=centre["type"],
                urgence_24h=centre["urgence_24h"],
                horaires=centre["horaires"],
            )
            db.session.add(nouveau)
            crees += 1

            # Commit par lot de 50 plutôt qu'en un seul bloc géant :
            # si une entrée pose problème, on perd moins de travail
            # et l'erreur est plus facile à isoler.
            if not dry_run and crees % 50 == 0:
                db.session.commit()

        if not dry_run:
            db.session.commit()

        print(f"\n{'[DRY-RUN] ' if dry_run else ''}{crees} centres {'seraient créés' if dry_run else 'créés'}.")
        print(f"{ignores_deja_presents} centres ignorés (déjà présents en base par nom identique).")

        from collections import Counter
        repartition = Counter(c["type"] for c in centres)
        print("\nRépartition par type :")
        for type_centre, nombre in repartition.most_common():
            print(f"  {type_centre} : {nombre}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    centres = preparer_centres()
    print(f"\n{len(centres)} centres prêts à être importés.\n")

    importer(centres, dry_run=dry_run)
