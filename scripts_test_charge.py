"""
Test de charge léger pour FasoSOS - simule des utilisateurs réels
naviguant sur l'app (connexion, recherche de centres proches).

Usage :
    locust -f scripts_test_charge.py --host=http://127.0.0.1:5000
Puis ouvrir http://localhost:8089 dans le navigateur pour lancer le test
et voir les résultats en temps réel (temps de réponse, taux d'erreur).
"""
from locust import HttpUser, task, between
import random


class UtilisateurFasoSOS(HttpUser):
    wait_time = between(1, 3)  # pause réaliste entre les actions d'un utilisateur
    token = None

    def on_start(self):
        """Chaque utilisateur simulé se connecte au démarrage."""
        telephone = f"+2267{random.randint(1000000, 9999999)}"
        self.client.post(
            "/api/v1/auth/register",
            json={"nom": "Charge Test", "telephone": telephone, "mot_de_passe": "motdepasse123"},
        )
        reponse = self.client.post(
            "/api/v1/auth/login",
            json={"telephone": telephone, "mot_de_passe": "motdepasse123"},
        )
        if reponse.status_code == 200:
            self.token = reponse.json().get("access_token")

    def _entetes(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def rechercher_centres_proches(self):
        """L'action la plus fréquente : chercher les centres proches (comme au chargement de l'app)."""
        lat = 12.37 + random.uniform(-0.05, 0.05)
        lng = -1.51 + random.uniform(-0.05, 0.05)
        self.client.get(
            f"/api/v1/health-centers/nearby?lat={lat}&lng={lng}",
            headers=self._entetes(),
            name="/health-centers/nearby",
        )

    @task(1)
    def declencher_sos(self):
        """Action plus rare mais critique : le bouton SOS."""
        self.client.post(
            "/api/v1/sos",
            json={"type_urgence": "Accident", "latitude": 12.37, "longitude": -1.51},
            headers=self._entetes(),
        )

    @task(2)
    def consulter_profil(self):
        self.client.get("/api/v1/auth/me", headers=self._entetes())
