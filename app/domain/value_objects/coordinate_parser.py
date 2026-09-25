"""
Utilitaire de nettoyage et validation des coordonnées GPS saisies manuellement.
Accepte des formats variés (avec °, virgule, espaces) et les normalise
en float strict avant tout enregistrement en base.
"""
import re


class CoordinateParser:
    """Nettoie et valide une chaîne de coordonnée GPS (latitude ou longitude)."""

    @staticmethod
    def nettoyer(valeur) -> float:
        """
        Nettoie une valeur de coordonnée GPS saisie par un utilisateur.

        Accepte : "12.37479", "12.37479°", "12,37479", " 12.37479 ° "
        Retourne : un float propre.

        Raises:
            ValueError: si la valeur ne peut pas être convertie en nombre.
        """
        if valeur is None:
            raise ValueError("La coordonnée ne peut pas être vide.")

        if isinstance(valeur, (int, float)):
            return float(valeur)

        texte = str(valeur).strip()
        texte = texte.replace("°", "")
        texte = texte.replace(" ", "")
        texte = texte.replace(",", ".")

        if texte == "":
            raise ValueError("La coordonnée ne peut pas être vide.")

        try:
            return float(texte)
        except ValueError:
            raise ValueError(f"Coordonnée invalide : '{valeur}'.")

    @staticmethod
    def valider_latitude(latitude: float) -> None:
        """Vérifie que la latitude est dans l'intervalle valide [-90, 90]."""
        if not -90 <= latitude <= 90:
            raise ValueError(
                f"Latitude invalide ({latitude}) : doit être comprise entre -90 et 90."
            )

    @staticmethod
    def valider_longitude(longitude: float) -> None:
        """Vérifie que la longitude est dans l'intervalle valide [-180, 180]."""
        if not -180 <= longitude <= 180:
            raise ValueError(
                f"Longitude invalide ({longitude}) : doit être comprise entre -180 et 180."
            )

    @classmethod
    def nettoyer_et_valider_latitude(cls, valeur) -> float:
        """Nettoie puis valide une latitude en une seule étape."""
        latitude = cls.nettoyer(valeur)
        cls.valider_latitude(latitude)
        return latitude

    @classmethod
    def nettoyer_et_valider_longitude(cls, valeur) -> float:
        """Nettoie puis valide une longitude en une seule étape."""
        longitude = cls.nettoyer(valeur)
        cls.valider_longitude(longitude)
        return longitude
