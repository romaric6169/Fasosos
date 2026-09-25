"""
Script utilitaire : récupère les centres de santé (hôpitaux, CSPS, CMA,
CHU, cliniques, cabinets médicaux) référencés sur OpenStreetMap pour
l'ensemble du Burkina Faso, via l'API Overpass.
Inclut les points (node) ET les zones/bâtiments (way, relation) pour
maximiser la récupération des noms. Exclut explicitement les pharmacies.

Usage : python3 scripts_recuperation_centres.py
"""
import requests
import json
import time

OVERPASS_URLS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

HEADERS = {
    "User-Agent": "FasoSOS-App/1.0 (projet sante Burkina Faso; contact: exemple@fasosos.bf)",
    "Accept": "application/json",
}

# "out center" permet de récupérer un point représentatif (centroïde)
# pour les éléments de type way/relation (bâtiments, enceintes hospitalières),
# en plus des simples points (node).
REQUETE = """
[out:json][timeout:180];
area["ISO3166-1"="BF"][admin_level=2]->.burkina;
(
  node["amenity"="hospital"](area.burkina);
  way["amenity"="hospital"](area.burkina);
  relation["amenity"="hospital"](area.burkina);

  node["amenity"="clinic"](area.burkina);
  way["amenity"="clinic"](area.burkina);

  node["amenity"="doctors"](area.burkina);
  way["amenity"="doctors"](area.burkina);

  node["healthcare"="hospital"](area.burkina);
  way["healthcare"="hospital"](area.burkina);

  node["healthcare"="clinic"](area.burkina);
  way["healthcare"="clinic"](area.burkina);

  node["healthcare"="centre"](area.burkina);
  way["healthcare"="centre"](area.burkina);

  node["healthcare"="doctor"](area.burkina);
);
out body center;
"""


def recuperer_centres():
    derniere_erreur = None

    for url in OVERPASS_URLS:
        try:
            print(f"Tentative sur {url} ...")
            reponse = requests.post(
                url,
                data={"data": REQUETE},
                headers=HEADERS,
                timeout=180,
            )
            reponse.raise_for_status()
            donnees = reponse.json()
            print(f"Succès avec {url}")
            return _extraire_centres(donnees)

        except requests.exceptions.RequestException as erreur:
            derniere_erreur = erreur
            print(f"Échec sur {url} : {erreur}")
            time.sleep(2)
            continue

    raise RuntimeError(
        f"Tous les miroirs Overpass ont échoué. Dernière erreur : {derniere_erreur}"
    )


def _obtenir_coordonnees(element: dict) -> tuple[float, float] | None:
    """
    Retourne (latitude, longitude) d'un élément Overpass.
    Pour un node : directement lat/lon.
    Pour un way/relation : utilise le centre calculé par 'out center'.
    """
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]

    centre = element.get("center")
    if centre:
        return centre.get("lat"), centre.get("lon")

    return None


def _extraire_centres(donnees: dict) -> list[dict]:
    centres = []
    vus = set()  # évite les doublons entre requêtes node/way qui se chevauchent
    mots_cles_pharmacie = ("pharmac",)

    for element in donnees.get("elements", []):
        tags = element.get("tags", {})
        nom = tags.get("name")
        if not nom:
            continue

        type_osm = (tags.get("amenity") or tags.get("healthcare") or "").lower()
        nom_lower = nom.lower()
        if any(mot in type_osm for mot in mots_cles_pharmacie) or any(
            mot in nom_lower for mot in mots_cles_pharmacie
        ):
            continue

        coordonnees = _obtenir_coordonnees(element)
        if not coordonnees or coordonnees[0] is None:
            continue

        latitude, longitude = coordonnees

        # Déduplication approximative par nom + coordonnées arrondies
        cle_unicite = (nom_lower, round(latitude, 4), round(longitude, 4))
        if cle_unicite in vus:
            continue
        vus.add(cle_unicite)

        centres.append({
            "nom": nom,
            "latitude": latitude,
            "longitude": longitude,
            "type_osm": type_osm,
            "adresse": tags.get("addr:full") or tags.get("addr:street", ""),
            "telephone": tags.get("phone", ""),
        })

    return centres


if __name__ == "__main__":
    centres = recuperer_centres()
    print(f"\n{len(centres)} centres de santé nommés trouvés au Burkina Faso (pharmacies exclues).\n")

    for centre in centres:
        print(json.dumps(centre, ensure_ascii=False, indent=2))

    with open("centres_burkina_faso_osm.json", "w", encoding="utf-8") as f:
        json.dump(centres, f, ensure_ascii=False, indent=2)

    print("\nRésultats sauvegardés dans centres_burkina_faso_osm.json")
