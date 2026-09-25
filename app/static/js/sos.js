/**
 * Gestion du déclenchement d'une alerte SOS.
 */
document.getElementById("btn-sos").addEventListener("click", async () => {
    if (!positionUtilisateur) {
        alert("Position GPS non disponible. Veuillez autoriser la géolocalisation.");
        return;
    }
    await chargerContactsPourSos();
    new bootstrap.Modal(document.getElementById("modalSos")).show();
});

async function chargerContactsPourSos() {
    const select = document.getElementById("select-contact-urgence");
    if (!select) return;

    let reponse;
    try {
        reponse = await appelApi("/api/v1/emergency-contacts");
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) return;

    const contacts = await reponse.json();
    select.innerHTML = '<option value="">Aucun</option>';
    contacts.forEach((contact) => {
        const option = document.createElement("option");
        option.value = contact.id;
        option.textContent = `${contact.nom} (Priorité ${contact.priorite})`;
        select.appendChild(option);
    });
}

document.getElementById("btn-confirmer-sos").addEventListener("click", async () => {
    const typeUrgence = document.getElementById("select-type-urgence").value;
    const typeCentre = document.getElementById("select-type-centre").value;
    const description = document.getElementById("input-description").value;
    const contactSelect = document.getElementById("select-contact-urgence");
    const contactId = contactSelect ? contactSelect.value : "";

    const corps = {
        type_urgence: typeUrgence,
        latitude: positionUtilisateur.lat,
        longitude: positionUtilisateur.lng,
        description: description || null,
    };
    if (typeCentre) corps.type_centre_souhaite = typeCentre;
    if (contactId) corps.contact_urgence_id = contactId;

    let reponse;
    try {
        reponse = await appelApi("/api/v1/sos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(corps),
        });
    } catch (erreur) {
        return;
    }

    const donnees = await reponse.json();

    if (!reponse.ok) {
        alert(donnees.erreur || "Erreur lors du déclenchement de l'alerte.");
        return;
    }

    bootstrap.Modal.getInstance(document.getElementById("modalSos")).hide();

    if (donnees.lien_sms) {
        if (confirm("Alerte SOS enregistrée. Envoyer le SMS d'urgence maintenant ?")) {
            window.location.href = donnees.lien_sms;
        }
    } else {
        alert("Alerte SOS enregistrée.");
    }

    chargerCentresProches(positionUtilisateur.lat, positionUtilisateur.lng, typeCentre);
});
