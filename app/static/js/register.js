/**
 * Gestion du formulaire d'inscription.
 */
document.getElementById("form-inscription").addEventListener("submit", async (e) => {
    e.preventDefault();

    const zoneErreur = document.getElementById("erreur-inscription");
    const zoneSucces = document.getElementById("succes-inscription");
    zoneErreur.classList.add("d-none");
    zoneSucces.classList.add("d-none");

    const motDePasse = document.getElementById("mot_de_passe").value;
    const confirmation = document.getElementById("confirmation_mot_de_passe").value;

    if (motDePasse !== confirmation) {
        zoneErreur.textContent = "Les mots de passe ne correspondent pas.";
        zoneErreur.classList.remove("d-none");
        return;
    }

    const corps = {
        nom: document.getElementById("nom").value,
        telephone: document.getElementById("telephone").value,
        mot_de_passe: motDePasse,
    };

    const email = document.getElementById("email").value;
    if (email) corps.email = email;

    try {
        const reponse = await fetch("/api/v1/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(corps),
        });

        const donnees = await reponse.json();

        if (!reponse.ok) {
            zoneErreur.textContent = donnees.erreur || "Erreur lors de l'inscription.";
            zoneErreur.classList.remove("d-none");
            return;
        }

        zoneSucces.textContent = "Compte créé avec succès. Redirection vers la connexion...";
        zoneSucces.classList.remove("d-none");

        setTimeout(() => {
            window.location.href = "/connexion";
        }, 1500);
    } catch (erreur) {
        zoneErreur.textContent = "Impossible de contacter le serveur.";
        zoneErreur.classList.remove("d-none");
    }
});
