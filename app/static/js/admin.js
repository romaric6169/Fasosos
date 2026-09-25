/**
 * Gestion du dashboard admin : vérification du rôle, ajout, édition,
 * suppression et recherche des centres, plus gestion des utilisateurs.
 */

const role = sessionStorage.getItem("user_role");
const token = sessionStorage.getItem("access_token");

if (!token) {
    window.location.href = "/connexion";
} else if (role !== "admin") {
    alert("Accès réservé aux administrateurs.");
    window.location.href = "/";
}

document.getElementById("nom-admin").textContent = sessionStorage.getItem("user_nom") || "";

document.getElementById("btn-deconnexion").addEventListener("click", () => {
    sessionStorage.clear();
    window.location.href = "/connexion";
});

function afficherAlerte(message, type = "success") {
    const zone = document.getElementById("alerte-admin");
    zone.textContent = message;
    zone.className = `alert alert-${type}`;
}

let tousLesCentres = [];

async function chargerCentres() {
    let reponse;
    try {
        reponse = await appelApi("/api/v1/health-centers");
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) {
        afficherAlerte("Erreur lors du chargement des centres.", "danger");
        return;
    }

    tousLesCentres = await reponse.json();
    afficherTableau(tousLesCentres);
}

function afficherTableau(centres) {
    const corps = document.getElementById("tableau-centres");
    corps.innerHTML = "";

    centres.forEach((centre) => {
        const ligne = document.createElement("tr");
        ligne.innerHTML = `
            <td>${echapperHtml(centre.nom)}</td>
            <td><span class="badge bg-secondary">${echapperHtml(centre.type)}</span></td>
            <td>${centre.urgence_24h ? "✅" : "—"}</td>
            <td>${echapperHtml(centre.horaires) || "—"}</td>
            <td><button class="btn btn-sm btn-outline-primary btn-modifier" data-id="${centre.id}">Modifier</button></td>
        `;
        corps.appendChild(ligne);
    });

    document.querySelectorAll(".btn-modifier").forEach((bouton) => {
        bouton.addEventListener("click", () => ouvrirEdition(bouton.dataset.id));
    });
}

document.getElementById("recherche-centre").addEventListener("input", (e) => {
    const terme = e.target.value.trim().toLowerCase();
    const filtres = tousLesCentres.filter(
        (c) => c.nom.toLowerCase().includes(terme) || c.type.toLowerCase().includes(terme)
    );
    afficherTableau(filtres);
});

function ouvrirEdition(centreId) {
    const centre = tousLesCentres.find((c) => c.id === centreId);
    if (!centre) return;

    document.getElementById("edition-id").value = centre.id;
    document.getElementById("edition-nom").value = centre.nom;
    document.getElementById("edition-adresse").value = centre.adresse || "";
    document.getElementById("edition-telephone").value = centre.telephone || "";
    document.getElementById("edition-latitude").value = centre.latitude;
    document.getElementById("edition-longitude").value = centre.longitude;
    document.getElementById("edition-type").value = centre.type;
    document.getElementById("edition-horaires").value = centre.horaires || "";
    document.getElementById("edition-urgence24h").checked = centre.urgence_24h;

    new bootstrap.Modal(document.getElementById("modalEdition")).show();
}

document.getElementById("btn-enregistrer-edition").addEventListener("click", async () => {
    const id = document.getElementById("edition-id").value;

    const latitude = nettoyerCoordonnee(document.getElementById("edition-latitude").value);
    const longitude = nettoyerCoordonnee(document.getElementById("edition-longitude").value);

    if (!validerLatitude(latitude)) {
        afficherAlerte("Latitude invalide. Elle doit être comprise entre -90 et 90.", "danger");
        return;
    }
    if (!validerLongitude(longitude)) {
        afficherAlerte("Longitude invalide. Elle doit être comprise entre -180 et 180.", "danger");
        return;
    }

    const corps = {
        nom: document.getElementById("edition-nom").value,
        adresse: document.getElementById("edition-adresse").value || null,
        telephone: document.getElementById("edition-telephone").value || null,
        latitude: latitude,
        longitude: longitude,
        type: document.getElementById("edition-type").value,
        horaires: document.getElementById("edition-horaires").value || null,
        urgence_24h: document.getElementById("edition-urgence24h").checked,
    };

    let reponse;
    try {
        reponse = await appelApi(`/api/v1/health-centers/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(corps),
        });
    } catch (erreur) {
        return;
    }

    const donnees = await reponse.json();

    if (!reponse.ok) {
        afficherAlerte(donnees.erreur || "Erreur lors de la modification.", "danger");
        return;
    }

    bootstrap.Modal.getInstance(document.getElementById("modalEdition")).hide();
    afficherAlerte(`Centre "${donnees.nom}" modifié avec succès.`, "success");
    chargerCentres();
});

document.getElementById("btn-supprimer-centre").addEventListener("click", async () => {
    const id = document.getElementById("edition-id").value;
    const nom = document.getElementById("edition-nom").value;

    if (!confirm(`Supprimer définitivement "${nom}" ? Cette action est irréversible.`)) {
        return;
    }

    let reponse;
    try {
        reponse = await appelApi(`/api/v1/health-centers/${id}`, { method: "DELETE" });
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) {
        const donnees = await reponse.json();
        afficherAlerte(donnees.erreur || "Erreur lors de la suppression.", "danger");
        return;
    }

    bootstrap.Modal.getInstance(document.getElementById("modalEdition")).hide();
    afficherAlerte(`Centre "${nom}" supprimé.`, "success");
    chargerCentres();
});

document.getElementById("form-centre").addEventListener("submit", async (e) => {
    e.preventDefault();

    const latitude = nettoyerCoordonnee(document.getElementById("centre-latitude").value);
    const longitude = nettoyerCoordonnee(document.getElementById("centre-longitude").value);

    if (!validerLatitude(latitude)) {
        afficherAlerte("Latitude invalide. Elle doit être comprise entre -90 et 90.", "danger");
        return;
    }
    if (!validerLongitude(longitude)) {
        afficherAlerte("Longitude invalide. Elle doit être comprise entre -180 et 180.", "danger");
        return;
    }

    const corps = {
        nom: document.getElementById("centre-nom").value,
        adresse: document.getElementById("centre-adresse").value || null,
        telephone: document.getElementById("centre-telephone").value || null,
        latitude: latitude,
        longitude: longitude,
        type: document.getElementById("centre-type").value,
        horaires: document.getElementById("centre-horaires").value || null,
        urgence_24h: document.getElementById("centre-urgence24h").checked,
    };

    let reponse;
    try {
        reponse = await appelApi("/api/v1/health-centers", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(corps),
        });
    } catch (erreur) {
        return;
    }

    const donnees = await reponse.json();

    if (!reponse.ok) {
        afficherAlerte(donnees.erreur || "Erreur lors de l'ajout du centre.", "danger");
        return;
    }

    afficherAlerte(`Centre "${donnees.nom}" ajouté avec succès.`, "success");
    document.getElementById("form-centre").reset();
    chargerCentres();
});

document.addEventListener("DOMContentLoaded", chargerCentres);

/**
 * Gestion de l'onglet Utilisateurs.
 */
let tousLesUtilisateurs = [];

async function chargerUtilisateurs() {
    let reponse;
    try {
        reponse = await appelApi("/api/v1/auth/users");
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) {
        afficherAlerte("Erreur lors du chargement des utilisateurs.", "danger");
        return;
    }

    tousLesUtilisateurs = await reponse.json();
    document.getElementById("compteur-utilisateurs").textContent = tousLesUtilisateurs.length;
    afficherTableauUtilisateurs(tousLesUtilisateurs);
}

function afficherTableauUtilisateurs(utilisateurs) {
    const corps = document.getElementById("tableau-utilisateurs");
    corps.innerHTML = "";

    const badgesRole = {
        admin: '<span class="badge bg-danger">Admin</span>',
        personnel_sante: '<span class="badge bg-info text-dark">Personnel de santé</span>',
        citoyen: '<span class="badge bg-secondary">Citoyen</span>',
    };

    utilisateurs.forEach((utilisateur) => {
        const dateInscription = new Date(utilisateur.created_at).toLocaleDateString("fr-FR", {
            day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit"
        });

        const ligne = document.createElement("tr");
        ligne.innerHTML = `
            <td>${echapperHtml(utilisateur.nom)}</td>
            <td>${echapperHtml(utilisateur.telephone)}</td>
            <td>${echapperHtml(utilisateur.email) || "—"}</td>
            <td>${badgesRole[utilisateur.role] || echapperHtml(utilisateur.role)}</td>
            <td>${utilisateur.is_active ? '<span class="badge bg-success">Actif</span>' : '<span class="badge bg-secondary">Inactif</span>'}</td>
            <td>${dateInscription}</td>
        `;
        corps.appendChild(ligne);
    });
}

document.getElementById("recherche-utilisateur").addEventListener("input", (e) => {
    const terme = e.target.value.trim().toLowerCase();
    const filtres = tousLesUtilisateurs.filter(
        (u) =>
            u.nom.toLowerCase().includes(terme) ||
            u.telephone.toLowerCase().includes(terme) ||
            (u.email || "").toLowerCase().includes(terme)
    );
    afficherTableauUtilisateurs(filtres);
});

document.getElementById("onglet-utilisateurs").addEventListener("shown.bs.tab", () => {
    chargerUtilisateurs();
});

/**
 * Gestion de l'onglet Sécurité : résumé des événements + journal détaillé.
 */
let pageLogsActuelle = 1;
let totalPagesLogs = 1;

const libellesEvenements = {
    connexion_echouee: "🔴 Connexion échouée",
    connexion_reussie: "🟢 Connexion réussie",
    connexion_refusee: "🟠 Compte désactivé (tentative)",
    acces_refuse: "🟡 Accès refusé (permissions)",
    inscription: "🆕 Inscription",
    inscription_refusee: "⚠️ Inscription refusée",
};

async function chargerResumeSecurite() {
    let reponse;
    try {
        reponse = await appelApi("/api/v1/audit/logs/resume");
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) return;

    const resume = await reponse.json();
    const stats24h = resume.derniere_24h || {};

    document.getElementById("stat-connexions-echouees-24h").textContent = stats24h.connexion_echouee || 0;
    document.getElementById("stat-acces-refuses-24h").textContent = stats24h.acces_refuse || 0;
    document.getElementById("stat-connexions-reussies-24h").textContent = stats24h.connexion_reussie || 0;
    document.getElementById("stat-inscriptions-24h").textContent = stats24h.inscription || 0;
}

async function chargerLogs(page = 1) {
    const typeFiltre = document.getElementById("filtre-type-log").value;
    let url = `/api/v1/audit/logs?page=${page}&par_page=30`;
    if (typeFiltre) url += `&type=${typeFiltre}`;

    let reponse;
    try {
        reponse = await appelApi(url);
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) {
        afficherAlerte("Erreur lors du chargement du journal de sécurité.", "danger");
        return;
    }

    const donnees = await reponse.json();
    pageLogsActuelle = donnees.page;
    totalPagesLogs = Math.max(1, Math.ceil(donnees.total / donnees.par_page));

    const corps = document.getElementById("tableau-logs");
    corps.innerHTML = "";

    if (donnees.logs.length === 0) {
        corps.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Aucun événement trouvé.</td></tr>';
    }

    donnees.logs.forEach((log) => {
        const date = new Date(log.created_at).toLocaleString("fr-FR", {
            day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit",
        });

        const ligne = document.createElement("tr");
        ligne.innerHTML = `
            <td>${libellesEvenements[log.type_evenement] || echapperHtml(log.type_evenement)}</td>
            <td class="small">${echapperHtml(log.details) || "—"}</td>
            <td class="small text-muted">${echapperHtml(log.adresse_ip) || "—"}</td>
            <td class="small">${echapperHtml(log.telephone_cible) || "—"}</td>
            <td class="small text-muted">${date}</td>
        `;
        corps.appendChild(ligne);
    });

    document.getElementById("info-pagination").textContent = `Page ${pageLogsActuelle} / ${totalPagesLogs} (${donnees.total} événements)`;
    document.getElementById("btn-page-precedente").disabled = pageLogsActuelle <= 1;
    document.getElementById("btn-page-suivante").disabled = pageLogsActuelle >= totalPagesLogs;
}

document.getElementById("filtre-type-log").addEventListener("change", () => chargerLogs(1));

document.getElementById("btn-page-precedente").addEventListener("click", () => {
    if (pageLogsActuelle > 1) chargerLogs(pageLogsActuelle - 1);
});

document.getElementById("btn-page-suivante").addEventListener("click", () => {
    if (pageLogsActuelle < totalPagesLogs) chargerLogs(pageLogsActuelle + 1);
});

document.getElementById("onglet-securite").addEventListener("shown.bs.tab", () => {
    chargerResumeSecurite();
    chargerLogs(1);
});
