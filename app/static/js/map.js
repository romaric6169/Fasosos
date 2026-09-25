/**
 * Gestion de la carte Leaflet, géolocalisation HTML5, affichage des centres,
 * et du panneau coulissant (bottom sheet) sur mobile.
 */

const token = sessionStorage.getItem("access_token");
if (!token) {
    window.location.href = "/connexion";
}
document.getElementById("nom-utilisateur-texte").textContent = sessionStorage.getItem("user_nom") || "Profil";

let carte;
let marqueurUtilisateur;
let positionUtilisateur = null;
const marqueursCentres = [];
const marqueursParId = {};

function initCarte(lat, lng) {
    carte = L.map("carte").setView([lat, lng], 14);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(carte);

    const iconeUtilisateur = L.divIcon({
        className: "",
        html: '<div style="background:#2563eb;width:18px;height:18px;border-radius:50%;border:3px solid white;box-shadow:0 0 6px rgba(0,0,0,0.5);"></div>',
    });

    marqueurUtilisateur = L.marker([lat, lng], { icon: iconeUtilisateur })
        .addTo(carte)
        .bindPopup("Vous êtes ici")
        .openPopup();
}

function actualiserPositionUtilisateur(lat, lng) {
    positionUtilisateur = { lat, lng };
    if (!carte) {
        initCarte(lat, lng);
    } else {
        marqueurUtilisateur.setLatLng([lat, lng]);
    }
}

function demarrerGeolocalisation() {
    if (!navigator.geolocation) {
        alert("La géolocalisation n'est pas supportée par ce navigateur.");
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const { latitude, longitude } = position.coords;
            actualiserPositionUtilisateur(latitude, longitude);
            chargerCentresProches(latitude, longitude);
        },
        (erreur) => {
            alert("Impossible d'obtenir votre position : " + erreur.message);
        },
        { enableHighAccuracy: true }
    );

    navigator.geolocation.watchPosition(
        (position) => {
            const { latitude, longitude } = position.coords;
            actualiserPositionUtilisateur(latitude, longitude);
        },
        (erreur) => console.warn("Erreur de suivi GPS :", erreur.message),
        { enableHighAccuracy: true }
    );
}

function iconeParType(type, correspond) {
    const couleurs = {
        CSPS: "#16a34a",
        CMA: "#0891b2",
        CHR: "#7c3aed",
        CHU: "#dc2626",
        CLINIQUE: "#ea580c",
    };
    const couleur = correspond ? (couleurs[type] || "#64748b") : "#f59e0b";
    return L.divIcon({
        className: "",
        html: `<div style="background:${couleur};width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 0 4px rgba(0,0,0,0.5);"></div>`,
    });
}

async function chargerCentresProches(lat, lng, typeCentreSouhaite = "") {
    marqueursCentres.forEach((m) => carte.removeLayer(m));
    marqueursCentres.length = 0;
    Object.keys(marqueursParId).forEach((cle) => delete marqueursParId[cle]);

    let url = `/api/v1/health-centers/nearby?lat=${lat}&lng=${lng}`;
    if (typeCentreSouhaite) url += `&type_centre_souhaite=${typeCentreSouhaite}`;

    let reponse;
    try {
        reponse = await appelApi(url);
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) {
        console.error("Erreur lors du chargement des centres.");
        return;
    }

    const donnees = await reponse.json();
    const tousLesCentres = [...donnees.plus_proches, ...donnees.type_demande];
    const idsAffiches = new Set();
    const centresUniques = [];

    tousLesCentres.forEach((centre) => {
        if (idsAffiches.has(centre.id)) return;
        idsAffiches.add(centre.id);
        centresUniques.push(centre);

        const marqueur = L.marker([centre.latitude, centre.longitude], {
            icon: iconeParType(centre.type, centre.type_correspond),
        });

        marqueur.bindPopup(`<b>${echapperHtml(centre.nom)}</b><br>${echapperHtml(centre.type)} - ${centre.distance_km} km`);
        marqueur.bindTooltip(`${echapperHtml(centre.nom)} · ${centre.distance_km} km`, { permanent: true, interactive: true, direction: "top", offset: [0, -8], className: "etiquette-centre-carte" });
        marqueur.on("click", () => afficherFicheCentre(centre));

        if (carte) marqueur.addTo(carte);
        marqueursCentres.push(marqueur);
        marqueursParId[centre.id] = marqueur;
    });

    centresUniques.sort((a, b) => a.distance_km - b.distance_km);
    afficherListeCentres(centresUniques);
    mettreAJourApercuPanneau(centresUniques);
}

function afficherListeCentres(centres) {
    const conteneur = document.getElementById("liste-centres");

    if (centres.length === 0) {
        conteneur.innerHTML = '<p class="text-muted text-center p-3">Aucun centre trouvé à proximité.</p>';
        return;
    }

    conteneur.innerHTML = centres
        .map(
            (centre) => `
        <div class="carte-centre-liste" data-centre-id="${centre.id}">
            <div class="d-flex justify-content-between align-items-start">
                <span class="nom-centre">${echapperHtml(centre.nom)}</span>
                <span class="distance-centre">${centre.distance_km} km</span>
            </div>
            <div>
                <span class="badge bg-secondary">${echapperHtml(centre.type)}</span>
                ${centre.urgence_24h ? '<span class="badge bg-danger">Urgence 24h</span>' : ""}
                ${!centre.type_correspond ? '<span class="badge badge-type-mismatch">Type différent</span>' : ""}
            </div>
        </div>
    `
        )
        .join("");

    document.querySelectorAll(".carte-centre-liste").forEach((element) => {
        element.addEventListener("click", () => {
            const id = element.dataset.centreId;
            const marqueur = marqueursParId[id];
            if (!marqueur) return;

            carte.setView(marqueur.getLatLng(), 15);
            marqueur.openPopup();
            fermerPanneau();

            const centre = centres.find((c) => c.id === id);
            if (centre) afficherFicheCentre(centre);
        });
    });
}

function afficherFicheCentre(centre) {
    document.getElementById("titre-centre").textContent = centre.nom;

    const avertissement = !centre.type_correspond
        ? `<div class="alert alert-warning py-1 px-2">⚠️ Ce centre n'est pas du type demandé</div>`
        : "";

    const servicesTexte = centre.services && centre.services.length
        ? centre.services.map(echapperHtml).join(", ")
        : "Non renseignés";

    document.getElementById("corps-fiche-centre").innerHTML = `
        ${avertissement}
        <p><b>Type :</b> ${echapperHtml(centre.type)} ${centre.urgence_24h ? "— Urgence 24h/24" : ""}</p>
        <p><b>Adresse :</b> ${echapperHtml(centre.adresse) || "Non renseignée"}</p>
        <p><b>Téléphone :</b> ${echapperHtml(centre.telephone) || "Non renseigné"}</p>
        <p><b>Distance :</b> ${centre.distance_km} km</p>
        <p><b>Services :</b> ${servicesTexte}</p>
    `;

    document.getElementById("footer-fiche-centre").innerHTML = `
        <div class="btn-group w-100">
            <button class="btn btn-outline-primary" onclick="ouvrirItineraire('${centre.id}', 'voiture')">🚗 Voiture</button>
            <button class="btn btn-outline-primary" onclick="ouvrirItineraire('${centre.id}', 'moto')">🏍️ Moto</button>
            <button class="btn btn-outline-primary" onclick="ouvrirItineraire('${centre.id}', 'marche')">🚶 Marche</button>
        </div>
    `;

    new bootstrap.Modal(document.getElementById("modalCentre")).show();
}

async function ouvrirItineraire(centreId, mode) {
    if (!positionUtilisateur) {
        alert("Position GPS non disponible.");
        return;
    }

    const url = `/api/v1/health-centers/${centreId}/itineraire?lat=${positionUtilisateur.lat}&lng=${positionUtilisateur.lng}&mode=${mode}`;

    let reponse;
    try {
        reponse = await appelApi(url);
    } catch (erreur) {
        return;
    }

    const donnees = await reponse.json();
    if (!reponse.ok) {
        alert(donnees.erreur || "Erreur lors de la génération de l'itinéraire.");
        return;
    }

    if (donnees.info) console.info(donnees.info);
    window.open(donnees.lien_itineraire, "_blank");
}

/**
 * Panneau coulissant (mobile uniquement) : ouverture/fermeture au tap
 * sur la poignée, glissement tactile, et aperçu du centre le plus proche
 * visible même quand le panneau est replié.
 */
const panneau = document.getElementById("panneau-centres");
const poignee = document.getElementById("poignee-panneau");
const texteApercu = document.getElementById("texte-apercu");

function mettreAJourApercuPanneau(centres) {
    if (!texteApercu) return;

    if (panneau.classList.contains("etat-ouvert")) return;

    if (centres.length === 0) {
        texteApercu.textContent = "▲ Aucun centre trouvé à proximité";
        return;
    }

    const plusProche = centres[0];
    texteApercu.textContent = `▲ ${plusProche.nom} — ${plusProche.distance_km} km`;
}

function ouvrirPanneau() {
    panneau.classList.remove("etat-ferme");
    panneau.classList.add("etat-ouvert");
    document.body.classList.add("panneau-ouvert");
    if (texteApercu) texteApercu.textContent = "▼ Masquer la liste";
}

function fermerPanneau() {
    panneau.classList.remove("etat-ouvert");
    panneau.classList.add("etat-ferme");
    document.body.classList.remove("panneau-ouvert");
}

function basculerPanneau() {
    if (panneau.classList.contains("etat-ouvert")) {
        fermerPanneau();
    } else {
        ouvrirPanneau();
    }
}

if (poignee) {
    poignee.addEventListener("click", basculerPanneau);

    let positionDepart = null;

    poignee.addEventListener("touchstart", (e) => {
        positionDepart = e.touches[0].clientY;
    }, { passive: true });

    poignee.addEventListener("touchend", (e) => {
        if (positionDepart === null) return;
        const positionFin = e.changedTouches[0].clientY;
        const delta = positionDepart - positionFin;

        if (delta > 30) {
            ouvrirPanneau();
        } else if (delta < -30) {
            fermerPanneau();
        }
        positionDepart = null;
    }, { passive: true });
}

document.addEventListener("DOMContentLoaded", demarrerGeolocalisation);
