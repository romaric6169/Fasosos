/**
 * Utilitaire centralisé pour les appels API.
 * Gère automatiquement l'expiration du token (401) en redirigeant
 * vers la connexion avec un message clair pour l'utilisateur.
 */

async function appelApi(url, options = {}) {
    const token = sessionStorage.getItem("access_token");

    const entetes = {
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`,
    };

    const reponse = await fetch(url, { ...options, headers: entetes });

    if (reponse.status === 401) {
        sessionStorage.clear();
        sessionStorage.setItem(
            "message_reconnexion",
            "Votre session a expiré. Veuillez vous reconnecter."
        );
        window.location.href = "/connexion";
        throw new Error("Session expirée");
    }

    return reponse;
}

/**
 * Nettoie une coordonnée GPS saisie par l'utilisateur : supprime les espaces
 * et le symbole °, remplace la virgule décimale par un point, convertit en nombre.
 * Retourne null si la valeur est invalide (à valider ensuite par appelant).
 */
function nettoyerCoordonnee(valeurBrute) {
    if (valeurBrute === null || valeurBrute === undefined) return null;

    let texte = String(valeurBrute).trim();
    texte = texte.replace(/°/g, "");
    texte = texte.replace(/\s/g, "");
    texte = texte.replace(",", ".");

    if (texte === "") return null;

    const nombre = parseFloat(texte);
    return isNaN(nombre) ? null : nombre;
}

function validerLatitude(latitude) {
    return latitude !== null && latitude >= -90 && latitude <= 90;
}

function validerLongitude(longitude) {
    return longitude !== null && longitude >= -180 && longitude <= 180;
}

/**
 * Échappe les caractères HTML dangereux avant insertion dans le DOM
 * via innerHTML. À utiliser systématiquement pour toute donnée provenant
 * de l'utilisateur ou de l'API (noms de contacts, de centres, descriptions...).
 */
function echapperHtml(texte) {
    if (texte === null || texte === undefined) return "";
    const div = document.createElement("div");
    div.textContent = String(texte);
    return div.innerHTML;
}
