/**
 * Gestion du formulaire de connexion.
 * Stocke le token JWT et le rôle, puis redirige selon le rôle.
 */
document.addEventListener("DOMContentLoaded", () => {
    const message = sessionStorage.getItem("message_reconnexion");
    if (message) {
        const zone = document.getElementById("message-info");
        if (zone) {
            zone.textContent = message;
            zone.classList.remove("d-none");
        }
        sessionStorage.removeItem("message_reconnexion");
    }
});

document.getElementById("form-connexion").addEventListener("submit", async (e) => {
    e.preventDefault();

    const telephone = document.getElementById("telephone").value;
    const motDePasse = document.getElementById("mot_de_passe").value;
    const zoneErreur = document.getElementById("erreur-connexion");
    zoneErreur.classList.add("d-none");

    try {
        const reponse = await fetch("/api/v1/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ telephone, mot_de_passe: motDePasse }),
        });

        const donnees = await reponse.json();

        if (!reponse.ok) {
            zoneErreur.textContent = donnees.erreur || "Erreur de connexion.";
            zoneErreur.classList.remove("d-none");
            return;
        }

        sessionStorage.setItem("access_token", donnees.access_token);
        sessionStorage.setItem("user_nom", donnees.user.nom);
        sessionStorage.setItem("user_role", donnees.user.role);

        if (donnees.user.role === "admin") {
            window.location.href = "/admin";
        } else {
            window.location.href = "/";
        }
    } catch (erreur) {
        zoneErreur.textContent = "Impossible de contacter le serveur.";
        zoneErreur.classList.remove("d-none");
    }
});
