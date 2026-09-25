/**
 * Gestion de la page profil : affichage et modification des informations
 * de l'utilisateur connecté.
 */

const token = sessionStorage.getItem("access_token");
if (!token) {
    window.location.href = "/connexion";
}

document.getElementById("nom-utilisateur").textContent = sessionStorage.getItem("user_nom") || "";

document.getElementById("btn-deconnexion").addEventListener("click", () => {
    sessionStorage.clear();
    window.location.href = "/connexion";
});

function afficherAlerte(message, type = "success") {
    const zone = document.getElementById("alerte-profil");
    zone.textContent = message;
    zone.className = `alert alert-${type}`;
}

const libellesRole = {
    admin: "Administrateur",
    personnel_sante: "Personnel de santé",
    citoyen: "Citoyen",
};

async function chargerProfil() {
    let reponse;
    try {
        reponse = await appelApi("/api/v1/auth/me");
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) {
        afficherAlerte("Erreur lors du chargement du profil.", "danger");
        return;
    }

    const profil = await reponse.json();

    document.getElementById("profil-nom").value = profil.nom;
    document.getElementById("profil-telephone").value = profil.telephone;
    document.getElementById("profil-email").value = profil.email || "";
    document.getElementById("profil-role").value = libellesRole[profil.role] || profil.role;

    const dateInscription = new Date(profil.created_at).toLocaleDateString("fr-FR", {
        day: "2-digit", month: "long", year: "numeric",
    });
    document.getElementById("profil-date").value = dateInscription;
}

document.getElementById("form-profil").addEventListener("submit", async (e) => {
    e.preventDefault();

    const corps = {
        nom: document.getElementById("profil-nom").value,
        email: document.getElementById("profil-email").value,
    };

    let reponse;
    try {
        reponse = await appelApi("/api/v1/auth/me", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(corps),
        });
    } catch (erreur) {
        return;
    }

    const donnees = await reponse.json();

    if (!reponse.ok) {
        afficherAlerte(donnees.erreur || "Erreur lors de la mise à jour.", "danger");
        return;
    }

    sessionStorage.setItem("user_nom", donnees.nom);
    document.getElementById("nom-utilisateur").textContent = donnees.nom;

    afficherAlerte("Profil mis à jour avec succès.", "success");
});

document.addEventListener("DOMContentLoaded", chargerProfil);
