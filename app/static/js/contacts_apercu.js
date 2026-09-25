/**
 * Vue rapide en lecture seule des contacts d'urgence : appeler ou envoyer
 * un SMS directement, sans possibilité de modifier/ajouter/supprimer.
 */

const token = sessionStorage.getItem("access_token");
if (!token) {
    window.location.href = "/connexion";
}
document.getElementById("nom-utilisateur").textContent = sessionStorage.getItem("user_nom") || "";

function afficherAlerte(message, type = "danger") {
    const zone = document.getElementById("alerte-contacts");
    zone.textContent = message;
    zone.className = `alert alert-${type}`;
}

async function chargerContactsApercu() {
    let reponse;
    try {
        reponse = await appelApi("/api/v1/emergency-contacts");
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) {
        afficherAlerte("Erreur lors du chargement des contacts.");
        return;
    }

    const contacts = await reponse.json();
    const conteneur = document.getElementById("liste-contacts-apercu");

    if (contacts.length === 0) {
        conteneur.innerHTML = `
            <div class="alert alert-warning">
                Aucun contact d'urgence enregistré.
                <a href="/profil">Ajoutez-en un depuis votre profil.</a>
            </div>
        `;
        return;
    }

    conteneur.innerHTML = contacts
        .map(
            (contact) => `
        <div class="card mb-2">
            <div class="card-body py-2">
                <div class="mb-2">
                    <span class="badge bg-secondary me-2">Priorité ${contact.priorite}</span>
                    <strong>${echapperHtml(contact.nom)}</strong>
                    <div class="text-muted small">${echapperHtml(contact.telephone)}${contact.lien_parente ? " · " + echapperHtml(contact.lien_parente) : ""}</div>
                </div>
                <div class="d-flex gap-2">
                    <a href="tel:${encodeURIComponent(contact.telephone)}" class="btn btn-sm btn-success flex-fill">📞 Appeler</a>
                    <a href="sms:${encodeURIComponent(contact.telephone)}" class="btn btn-sm btn-outline-success flex-fill">💬 SMS</a>
                </div>
            </div>
        </div>
    `
        )
        .join("");
}

document.addEventListener("DOMContentLoaded", chargerContactsApercu);
