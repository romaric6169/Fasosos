"""
Service de génération des liens Google Maps.
Ne stocke rien en base : les liens sont générés à la volée à partir
des coordonnées GPS, pour toujours rester exacts même si les coordonnées
d'un centre sont modifiées.
"""
from app.domain.value_objects.gps_coordinates import GpsCoordinates


class MapLinkService:
    """Génère les liens Google Maps (fiche centre + itinéraire)."""

    # Google Maps ne propose pas nativement de mode "moto" universel.
    # On mappe "moto" sur "driving" (le plus proche fonctionnellement),
    # avec une information affichée côté frontend pour prévenir l'utilisateur.
    MODES_TRANSPORT = {
        "voiture": "driving",
        "moto": "driving",
        "marche": "walking",
    }

    def lien_fiche_centre(self, position: GpsCoordinates) -> str:
        """Génère le lien Google Maps affichant simplement l'emplacement d'un centre."""
        return f"https://www.google.com/maps?q={position.latitude},{position.longitude}"

    def lien_itineraire(
        self,
        origine: GpsCoordinates,
        destination: GpsCoordinates,
        mode_transport: str = "voiture",
    ) -> str:
        """
        Génère un lien d'itinéraire Google Maps prêt à ouvrir,
        avec navigation immédiate depuis la position de l'utilisateur.
        """
        travelmode = self.MODES_TRANSPORT.get(mode_transport, "driving")

        return (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={origine.latitude},{origine.longitude}"
            f"&destination={destination.latitude},{destination.longitude}"
            f"&travelmode={travelmode}"
        )
