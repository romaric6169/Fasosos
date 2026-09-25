#!/bin/bash
# ============================================
# Tests IDOR — FasoSOS
# Vérifie qu'un utilisateur A ne peut jamais lire/modifier/supprimer
# les données privées d'un utilisateur B (contacts, alertes SOS, profil).
# Usage : bash scripts_test_idor.sh
# ============================================

BASE_URL="http://127.0.0.1:5000"
VERT='\033[0;32m'
ROUGE='\033[0;31m'
NC='\033[0m'

reussis=0
echoues=0

pass() { echo -e "${VERT}✅ PASS${NC} — $1"; reussis=$((reussis+1)); }
fail() { echo -e "${ROUGE}❌ FAIL${NC} — $1"; echoues=$((echoues+1)); }

echo "============================================"
echo "  TESTS IDOR — FasoSOS"
echo "============================================"
echo ""

# --- Prépare deux comptes distincts : Alice et Bob ---
curl -s -X POST "$BASE_URL/api/v1/auth/register" -H "Content-Type: application/json" \
  -d '{"nom":"Alice Test","telephone":"+22670001111","mot_de_passe":"motdepasse123"}' > /dev/null

curl -s -X POST "$BASE_URL/api/v1/auth/register" -H "Content-Type: application/json" \
  -d '{"nom":"Bob Test","telephone":"+22670002222","mot_de_passe":"motdepasse123"}' > /dev/null

TOKEN_ALICE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" -H "Content-Type: application/json" \
  -d '{"telephone":"+22670001111","mot_de_passe":"motdepasse123"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

TOKEN_BOB=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" -H "Content-Type: application/json" \
  -d '{"telephone":"+22670002222","mot_de_passe":"motdepasse123"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

if [ -z "$TOKEN_ALICE" ] || [ -z "$TOKEN_BOB" ]; then
    echo "Impossible de créer/connecter les comptes de test. Arrêt."
    exit 1
fi

echo "--- 1. Alice crée un contact d'urgence ---"
ID_CONTACT_ALICE=$(curl -s -X POST "$BASE_URL/api/v1/emergency-contacts" \
  -H "Authorization: Bearer $TOKEN_ALICE" -H "Content-Type: application/json" \
  -d '{"nom":"Contact Alice","telephone":"+22670003333","priorite":1}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")

if [ -z "$ID_CONTACT_ALICE" ]; then
    echo "Échec de création du contact d'Alice. Arrêt de ce bloc de tests."
else
    echo "Contact d'Alice créé : $ID_CONTACT_ALICE"

    echo ""
    echo "--- 2. Bob tente de MODIFIER le contact d'Alice ---"
    STATUT=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/api/v1/emergency-contacts/$ID_CONTACT_ALICE" \
      -H "Authorization: Bearer $TOKEN_BOB" -H "Content-Type: application/json" \
      -d '{"nom":"Contact Pirate"}')

    if [ "$STATUT" == "404" ] || [ "$STATUT" == "403" ]; then
        pass "Bob ne peut pas modifier le contact d'Alice — statut $STATUT."
    else
        fail "Bob a pu modifier le contact d'Alice ! Statut reçu : $STATUT"
    fi

    echo ""
    echo "--- 3. Bob tente de SUPPRIMER le contact d'Alice ---"
    STATUT=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/emergency-contacts/$ID_CONTACT_ALICE" \
      -H "Authorization: Bearer $TOKEN_BOB")

    if [ "$STATUT" == "404" ] || [ "$STATUT" == "403" ]; then
        pass "Bob ne peut pas supprimer le contact d'Alice — statut $STATUT."
    else
        fail "Bob a pu supprimer le contact d'Alice ! Statut reçu : $STATUT"
    fi

    echo ""
    echo "--- 4. Bob liste SES PROPRES contacts : le contact d'Alice ne doit jamais apparaître ---"
    REPONSE=$(curl -s "$BASE_URL/api/v1/emergency-contacts" -H "Authorization: Bearer $TOKEN_BOB")
    if echo "$REPONSE" | grep -q "$ID_CONTACT_ALICE"; then
        fail "Le contact d'Alice apparaît dans la liste des contacts de Bob !"
    else
        pass "La liste des contacts de Bob ne contient pas le contact d'Alice."
    fi
fi

echo ""
echo "--- 5. Alice déclenche une alerte SOS ---"
ID_SOS_ALICE=$(curl -s -X POST "$BASE_URL/api/v1/sos" \
  -H "Authorization: Bearer $TOKEN_ALICE" -H "Content-Type: application/json" \
  -d '{"type_urgence":"Accident","latitude":12.37,"longitude":-1.51}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")

if [ -z "$ID_SOS_ALICE" ]; then
    echo "Échec de création du SOS d'Alice. Arrêt de ce bloc."
else
    echo "SOS d'Alice créé : $ID_SOS_ALICE"

    echo ""
    echo "--- 6. Bob consulte SON PROPRE historique SOS : celui d'Alice ne doit pas apparaître ---"
    REPONSE=$(curl -s "$BASE_URL/api/v1/sos/history" -H "Authorization: Bearer $TOKEN_BOB")
    if echo "$REPONSE" | grep -q "$ID_SOS_ALICE"; then
        fail "L'alerte SOS d'Alice apparaît dans l'historique de Bob !"
    else
        pass "L'historique SOS de Bob ne contient pas l'alerte d'Alice."
    fi
fi

echo ""
echo "--- 7. Bob tente de modifier le PROFIL d'Alice via son propre token ---"
# Le endpoint /auth/me modifie toujours l'utilisateur du token, donc Bob
# ne peut techniquement modifier QUE son propre profil - on vérifie que
# la modification de Bob n'affecte jamais Alice.
curl -s -X PUT "$BASE_URL/api/v1/auth/me" -H "Authorization: Bearer $TOKEN_BOB" \
  -H "Content-Type: application/json" -d '{"nom":"Bob Modifie"}' > /dev/null

PROFIL_ALICE=$(curl -s "$BASE_URL/api/v1/auth/me" -H "Authorization: Bearer $TOKEN_ALICE")
if echo "$PROFIL_ALICE" | grep -q "Bob Modifie"; then
    fail "La modification de Bob a affecté le profil d'Alice !"
else
    pass "Le profil d'Alice reste intact malgré la modification de Bob sur le sien."
fi

echo ""
echo "--- 8. Bob tente d'accéder au profil d'Alice en devinant/énumérant un ID utilisateur ---"
# Récupère l'ID d'Alice via son propre token, puis vérifie qu'aucune route
# ne permet à Bob de consulter le profil d'Alice par son ID.
ID_ALICE=$(curl -s "$BASE_URL/api/v1/auth/me" -H "Authorization: Bearer $TOKEN_ALICE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
STATUT=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/auth/users/$ID_ALICE" -H "Authorization: Bearer $TOKEN_BOB")

if [ "$STATUT" == "404" ]; then
    pass "Aucune route ne permet à Bob de consulter le profil d'Alice par ID (404 - route inexistante, comme attendu)."
elif [ "$STATUT" == "403" ]; then
    pass "Bob reçoit un accès refusé en tentant de consulter le profil d'Alice par ID."
else
    fail "Statut inattendu ($STATUT) — vérifier manuellement si une route expose les profils par ID."
fi

echo ""
echo "============================================"
echo "  RÉSULTAT : $reussis réussis / $((reussis+echoues)) tests"
echo "============================================"
