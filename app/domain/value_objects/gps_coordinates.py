"""Value Object représentant des coordonnées GPS et le calcul de distance."""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class GpsCoordinates:
    """Coordonnées GPS immuables (latitude, longitude)."""
    latitude: float
    longitude: float

    def distance_to(self, other: "GpsCoordinates") -> float:
        """
        Calcule la distance en kilomètres entre deux points GPS
        via la formule de Haversine.
        """
        rayon_terre_km = 6371.0

        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return round(rayon_terre_km * c, 2)
