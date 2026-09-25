"""Utilitaires de hashage et vérification de mot de passe (bcrypt)."""
import bcrypt


class PasswordHasher:
    """Encapsule le hashage sécurisé des mots de passe."""

    @staticmethod
    def hash(mot_de_passe: str) -> str:
        """Retourne le hash bcrypt d'un mot de passe en clair."""
        sel = bcrypt.gensalt()
        return bcrypt.hashpw(mot_de_passe.encode("utf-8"), sel).decode("utf-8")

    @staticmethod
    def verifier(mot_de_passe: str, mot_de_passe_hash: str) -> bool:
        """Vérifie qu'un mot de passe en clair correspond au hash stocké."""
        return bcrypt.checkpw(
            mot_de_passe.encode("utf-8"), mot_de_passe_hash.encode("utf-8")
        )
