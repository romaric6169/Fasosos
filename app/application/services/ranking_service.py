"""
Service de classement des centres de santé.
Retourne deux listes distinctes :
- les centres les plus proches (tous types), avec avertissement si le type diffère
- les centres du type exact demandé, même éloignés
"""
from typing import TypedDict
from app.domain.value_objects.gps_coordinates import GpsCoordinates
from app.infrastructure.database.models import HealthCenter


class CentreClasse(TypedDict):
    centre: HealthCenter
    distance_km: float
    type_correspond: bool


class RankingService:
    """Classe les centres de santé par proximité et par type demandé."""

    NB_RESULTATS_PROCHES = 5

    def classer_centres(
        self,
        position_utilisateur: GpsCoordinates,
        type_centre_souhaite: str | None,
        centres: list[HealthCenter],
    ) -> dict[str, list[CentreClasse]]:
        """
        Args:
            position_utilisateur: position GPS de l'utilisateur
            type_centre_souhaite: CSPS | CMA | CHR | CHU | CLINIQUE ou None
            centres: liste des centres de santé actifs

        Returns:
            dict avec deux clés :
            - "plus_proches" : les N centres les plus proches, tous types confondus
            - "type_demande" : les centres du type exact demandé, triés par distance
        """
        centres_avec_distance: list[CentreClasse] = []

        for centre in centres:
            position_centre = GpsCoordinates(centre.latitude, centre.longitude)
            distance = position_utilisateur.distance_to(position_centre)
            type_correspond = (
                type_centre_souhaite is None or centre.type == type_centre_souhaite
            )
            centres_avec_distance.append(
                {
                    "centre": centre,
                    "distance_km": distance,
                    "type_correspond": type_correspond,
                }
            )

        # Liste 1 : les plus proches, tous types confondus
        plus_proches = sorted(
            centres_avec_distance, key=lambda c: c["distance_km"]
        )[: self.NB_RESULTATS_PROCHES]

        # Liste 2 : uniquement le type demandé, triés par distance
        type_demande: list[CentreClasse] = []
        if type_centre_souhaite:
            type_demande = sorted(
                [c for c in centres_avec_distance if c["centre"].type == type_centre_souhaite],
                key=lambda c: c["distance_km"],
            )

        return {
            "plus_proches": plus_proches,
            "type_demande": type_demande,
        }
