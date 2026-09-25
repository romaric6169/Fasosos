/**
 * Gestion des contacts d'urgence : liste, ajout, modification, suppression,
 * et actions rapides (appeler, envoyer un SMS).
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
    const zone = document.getElementById("alerte-contacts");
    zone.textContent = message;
    zone.className = `alert alert-${type}`;
}

let tousLesContacts = [];

async function chargerContacts() {
    let reponse;
    try {
        reponse = await appelApi("/api/v1/emergency-contacts");
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) {
        afficherAlerte("Erreur lors du chargement des contacts.", "danger");
        return;
    }

    tousLesContacts = await reponse.json();
    document.getElementById("compteur-contacts").textContent = tousLesContacts.length;
    afficherListeContacts();

    const formulaireVisible = tousLesContacts.length < 5;
    document.getElementById("carte-formulaire-contact").classList.toggle("d-none", !formulaireVisible);
}

function afficherListeContacts() {
    const conteneur = document.getElementById("liste-contacts");

    if (tousLesContacts.length === 0) {
        conteneur.innerHTML = '<p class="text-muted">Aucun contact enregistré pour le moment.</p>';
        return;
    }

    conteneur.innerHTML = tousLesContacts
        .map(
            (contact) => `
        <div class="card mb-2">
            <div class="card-body py-2">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <span class="badge bg-secondary me-2">Priorité ${contact.priorite}</span>
                        <strong>${echapperHtml(contact.nom)}</strong>
                        <div class="text-muted small">${echapperHtml(contact.telephone)}${contact.lien_parente ? " · " + echapperHtml(contact.lien_parente) : ""}</div>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-outline-primary btn-modifier-contact" data-id="${contact.id}">Modifier</button>
                        <button class="btn btn-sm btn-outline-danger btn-supprimer-contact" data-id="${contact.id}">Supprimer</button>
                    </div>
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

    document.querySelectorAll(".btn-modifier-contact").forEach((bouton) => {
        bouton.addEventListener("click", () => remplirFormulairePourEdition(bouton.dataset.id));
    });

    document.querySelectorAll(".btn-supprimer-contact").forEach((bouton) => {
        bouton.addEventListener("click", () => supprimerContact(bouton.dataset.id));
    });
}

function remplirFormulairePourEdition(contactId) {
    const contact = tousLesContacts.find((c) => c.id === contactId);
    if (!contact) return;

    document.getElementById("contact-id").value = contact.id;
    document.getElementById("contact-nom").value = contact.nom;
    document.getElementById("contact-telephone").value = contact.telephone;
    document.getElementById("contact-lien-parente").value = contact.lien_parente || "";
    document.getElementById("contact-priorite").value = contact.priorite;

    document.getElementById("btn-soumettre-contact").textContent = "Enregistrer les modifications";
    document.getElementById("btn-annuler-edition").classList.remove("d-none");
    document.getElementById("carte-formulaire-contact").classList.remove("d-none");
    document.getElementById("carte-formulaire-contact").scrollIntoView({ behavior: "smooth" });
}

function reinitialiserFormulaire() {
    document.getElementById("form-contact").reset();
    document.getElementById("contact-id").value = "";
    document.getElementById("btn-soumettre-contact").textContent = "Ajouter le contact";
    document.getElementById("btn-annuler-edition").classList.add("d-none");
}

document.getElementById("btn-annuler-edition").addEventListener("click", reinitialiserFormulaire);

async function supprimerContact(contactId) {
    const contact = tousLesContacts.find((c) => c.id === contactId);
    if (!confirm(`Supprimer le contact "${contact.nom}" ?`)) return;

    let reponse;
    try {
        reponse = await appelApi(`/api/v1/emergency-contacts/${contactId}`, { method: "DELETE" });
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) {
        afficherAlerte("Erreur lors de la suppression.", "danger");
        return;
    }

    afficherAlerte("Contact supprimé.", "success");
    chargerContacts();
}

document.getElementById("form-contact").addEventListener("submit", async (e) => {
    e.preventDefault();

    const id = document.getElementById("contact-id").value;
    const corps = {
        nom: document.getElementById("contact-nom").value,
        telephone: document.getElementById("contact-telephone").value,
        lien_parente: document.getElementById("contact-lien-parente").value || null,
        priorite: parseInt(document.getElementById("contact-priorite").value, 10),
    };

    const estModification = Boolean(id);
    const url = estModification ? `/api/v1/emergency-contacts/${id}` : "/api/v1/emergency-contacts";
    const methode = estModification ? "PUT" : "POST";

    let reponse;
    try {
        reponse = await appelApi(url, {
            method: methode,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(corps),
        });
    } catch (erreur) {
        return;
    }

    const donnees = await reponse.json();

    if (!reponse.ok) {
        afficherAlerte(donnees.erreur || "Erreur lors de l'enregistrement.", "danger");
        return;
    }

    afficherAlerte(estModification ? "Contact modifié avec succès." : "Contact ajouté avec succès.", "success");
    reinitialiserFormulaire();
    chargerContacts();
});

document.addEventListener("DOMContentLoaded", chargerContacts);
