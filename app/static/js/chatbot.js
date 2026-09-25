/**
 * Gestion du widget de chat flottant : conversation active (réinitialisée
 * à chaque rechargement) + consultation de l'historique des conversations passées.
 */

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await appelApi("/api/v1/chatbot/new", { method: "POST" });
    } catch (erreur) {
        // silencieux
    }
});

document.getElementById("btn-chatbot").addEventListener("click", () => {
    document.getElementById("etiquette-chatbot").style.display = "none";
    const fenetre = document.getElementById("fenetre-chatbot");
    const estOuverte = fenetre.classList.toggle("ouverte");

    if (estOuverte && document.getElementById("chatbot-messages").children.length === 0) {
        afficherMessageAccueil();
    }
});

document.getElementById("btn-fermer-chatbot").addEventListener("click", () => {
    document.getElementById("fenetre-chatbot").classList.remove("ouverte");
});

document.getElementById("btn-nouvelle-conversation").addEventListener("click", async () => {
    try {
        await appelApi("/api/v1/chatbot/new", { method: "POST" });
    } catch (erreur) {
        return;
    }
    afficherVueConversationActive();
    document.getElementById("chatbot-messages").innerHTML = "";
    afficherMessageAccueil();
});

function afficherMessageAccueil() {
    ajouterMessageAffiche(
        "assistant",
        "Bonjour, je suis l'assistant FasoSOS. Je peux vous orienter et répondre à vos questions de santé générales, mais je ne remplace jamais un professionnel."
    );
}

function ajouterMessageAffiche(role, contenu) {
    const conteneur = document.getElementById("chatbot-messages");
    const bulle = document.createElement("div");
    bulle.className = `message-chatbot ${role}`;
    bulle.textContent = contenu;
    conteneur.appendChild(bulle);
    conteneur.scrollTop = conteneur.scrollHeight;
}

async function envoyerMessageChatbot() {
    const input = document.getElementById("chatbot-input");
    const texte = input.value.trim();
    if (!texte) return;

    ajouterMessageAffiche("user", texte);
    input.value = "";

    const conteneur = document.getElementById("chatbot-messages");
    const indicateur = document.createElement("div");
    indicateur.className = "message-chatbot assistant";
    indicateur.id = "indicateur-frappe";
    indicateur.textContent = "...";
    conteneur.appendChild(indicateur);
    conteneur.scrollTop = conteneur.scrollHeight;

    let reponse;
    try {
        reponse = await appelApi("/api/v1/chatbot/message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: texte }),
        });
    } catch (erreur) {
        indicateur.remove();
        return;
    }

    indicateur.remove();

    const donnees = await reponse.json();

    if (!reponse.ok) {
        ajouterMessageAffiche("assistant", donnees.erreur || "Une erreur est survenue.");
        return;
    }

    ajouterMessageAffiche("assistant", donnees.reponse);
}

document.getElementById("btn-envoyer-chatbot").addEventListener("click", envoyerMessageChatbot);
document.getElementById("chatbot-input").addEventListener("keypress", (e) => {
    if (e.key === "Enter") envoyerMessageChatbot();
});

/**
 * Navigation entre la conversation active et le panneau d'historique.
 */
function afficherVueHistorique() {
    document.getElementById("chatbot-messages").classList.add("d-none");
    document.getElementById("chatbot-input-zone").classList.add("d-none");
    document.getElementById("chatbot-historique").classList.remove("d-none");
    document.getElementById("chatbot-historique").classList.add("visible");
}

function afficherVueConversationActive() {
    document.getElementById("chatbot-messages").classList.remove("d-none");
    document.getElementById("chatbot-input-zone").classList.remove("d-none");
    document.getElementById("chatbot-historique").classList.add("d-none");
    document.getElementById("chatbot-historique").classList.remove("visible");
}

document.getElementById("btn-historique-chatbot").addEventListener("click", async () => {
    afficherVueHistorique();
    await chargerListeConversations();
});

async function chargerListeConversations() {
    const conteneur = document.getElementById("chatbot-historique");
    conteneur.innerHTML = '<p class="text-muted text-center small p-2">Chargement...</p>';

    let reponse;
    try {
        reponse = await appelApi("/api/v1/chatbot/conversations");
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) {
        conteneur.innerHTML = '<p class="text-muted text-center small p-2">Erreur de chargement.</p>';
        return;
    }

    const conversations = await reponse.json();

    if (conversations.length === 0) {
        conteneur.innerHTML = '<p class="text-muted text-center small p-2">Aucune conversation précédente.</p>';
        return;
    }

    conteneur.innerHTML = conversations
        .map((conv) => {
            const date = new Date(conv.created_at).toLocaleDateString("fr-FR", {
                day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
            });
            return `
                <div class="item-historique" data-id="${conv.id}">
                    <div class="date-conversation">${date}</div>
                    <div>${conv.apercu}</div>
                </div>
            `;
        })
        .join("");

    document.querySelectorAll(".item-historique").forEach((element) => {
        element.addEventListener("click", () => ouvrirConversationPassee(element.dataset.id));
    });
}

async function ouvrirConversationPassee(conversationId) {
    let reponse;
    try {
        reponse = await appelApi(`/api/v1/chatbot/conversations/${conversationId}/messages`);
    } catch (erreur) {
        return;
    }

    if (!reponse.ok) return;

    const messages = await reponse.json();

    afficherVueConversationActive();
    document.getElementById("chatbot-input-zone").classList.add("d-none");

    const conteneur = document.getElementById("chatbot-messages");
    conteneur.innerHTML = '<div class="alert alert-info py-1 px-2 small mb-2">Conversation archivée (lecture seule) — <a href="#" id="lien-retour-active">revenir à la conversation en cours</a></div>';

    messages.forEach((m) => ajouterMessageAffiche(m.role, m.contenu));

    document.getElementById("lien-retour-active").addEventListener("click", (e) => {
        e.preventDefault();
        document.getElementById("chatbot-input-zone").classList.remove("d-none");
        document.getElementById("chatbot-messages").innerHTML = "";
        afficherMessageAccueil();
    });
}
