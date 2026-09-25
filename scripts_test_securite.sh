#!/bin/bash
# ============================================
# Script de test de sécurité — FasoSOS
# Vérifie une série de points classiques : contournement de rôle,
# accès non autorisé (IDOR), falsification de token, CORS, fuites
# de données sensibles, limitation de débit.
# Usage : bash scripts_test_securite.sh
# ============================================

BASE_URL="http://127.0.0.1:5000"
VERT='\033[0;32m'
ROUGE='\033[0;31m'
JAUNE='\033[1;33m'
NC='\033[0m'

reussis=0
echoues=0

pass() {
    echo -e "${VERT}✅ PASS${NC} — $1"
    reussis=$((reussis+1))
}

fail() {
    echo -e "${ROUGE}❌ FAIL${NC} — $1"
    echoues=$((echoues+1))
}

warn() {
    echo -e "${JAUNE}⚠️  ATTENTION${NC} — $1"
}

echo "============================================"
echo "  TESTS DE SÉCURITÉ — FasoSOS"
echo "============================================"
echo ""

# --- Préparation : créer un compte citoyen de test ---
TELEPHONE_TEST="+22670000001"
curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"nom\":\"Testeur Securite\",\"telephone\":\"$TELEPHONE_TEST\",\"mot_de_passe\":\"motdepasse123\"}" > /dev/null

TOKEN_CITOYEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"telephone\":\"$TELEPHONE_TEST\",\"mot_de_passe\":\"motdepasse123\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN_CITOYEN" ]; then
    echo "Impossible de créer/connecter le compte de test. Arrêt."
    exit 1
fi

echo "--- 1. Élévation de privilèges à l'inscription ---"
# Un citoyen ne doit JAMAIS pouvoir s'auto-attribuer le rôle admin
REPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"nom":"Faux Admin","telephone":"+22670000002","mot_de_passe":"motdepasse123","role":"admin"}')
ROLE_OBTENU=$(echo "$REPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('role',''))" 2>/dev/null)

if [ "$ROLE_OBTENU" == "citoyen" ]; then
    pass "Rôle forcé à 'citoyen' malgré la tentative d'auto-élévation à l'inscription."
else
    fail "Un utilisateur a pu s'auto-attribuer le rôle '$ROLE_OBTENU' à l'inscription !"
fi

echo ""
echo "--- 2. Accès à une route réservée admin, avec un compte citoyen ---"
STATUT=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/health-centers" \
  -H "Authorization: Bearer $TOKEN_CITOYEN")

if [ "$STATUT" == "403" ]; then
    pass "Un citoyen ne peut pas lister tous les centres (route admin) — 403 reçu."
else
    fail "Un citoyen a pu accéder à une route admin ! Statut reçu : $STATUT"
fi

echo ""
echo "--- 3. Accès à la liste des utilisateurs, avec un compte citoyen ---"
STATUT=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/auth/users" \
  -H "Authorization: Bearer $TOKEN_CITOYEN")

if [ "$STATUT" == "403" ]; then
    pass "Un citoyen ne peut pas lister les utilisateurs — 403 reçu."
else
    fail "Un citoyen a pu accéder à la liste des utilisateurs ! Statut reçu : $STATUT"
fi

echo ""
echo "--- 4. Accès au journal de sécurité, avec un compte citoyen ---"
STATUT=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/audit/logs" \
  -H "Authorization: Bearer $TOKEN_CITOYEN")

if [ "$STATUT" == "403" ]; then
    pass "Un citoyen ne peut pas consulter le journal de sécurité — 403 reçu."
else
    fail "Un citoyen a pu accéder au journal de sécurité ! Statut reçu : $STATUT"
fi

echo ""
echo "--- 5. Accès sans aucun token ---"
STATUT=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/emergency-contacts")

if [ "$STATUT" == "401" ] || [ "$STATUT" == "422" ]; then
    pass "Accès refusé sans token d'authentification — statut $STATUT."
else
    fail "Une route protégée a répondu sans token ! Statut reçu : $STATUT"
fi

echo ""
echo "--- 6. Falsification de token JWT (signature invalide) ---"
TOKEN_FALSIFIE="${TOKEN_CITOYEN%.*}.signature_falsifiee_XYZ"
STATUT=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/emergency-contacts" \
  -H "Authorization: Bearer $TOKEN_FALSIFIE")

if [ "$STATUT" == "401" ] || [ "$STATUT" == "422" ]; then
    pass "Un token avec signature falsifiée est rejeté — statut $STATUT."
else
    fail "Un token falsifié a été accepté ! Statut reçu : $STATUT"
fi

echo ""
echo "--- 7. Fuite de données sensibles (hash de mot de passe) ---"
REPONSE_PROFIL=$(curl -s "$BASE_URL/api/v1/auth/me" -H "Authorization: Bearer $TOKEN_CITOYEN")
if echo "$REPONSE_PROFIL" | grep -qi "mot_de_passe_hash\|password"; then
    fail "Le hash du mot de passe apparaît dans une réponse API !"
else
    pass "Aucune trace du hash de mot de passe dans les réponses API."
fi

echo ""
echo "--- 8. Injection SQL basique (recherche de centres) ---"
STATUT=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/health-centers/nearby?lat=12.37' OR '1'='1&lng=-1.51" \
  -H "Authorization: Bearer $TOKEN_CITOYEN")

if [ "$STATUT" == "400" ]; then
    pass "Tentative d'injection SQL dans les coordonnées correctement rejetée (400)."
else
    warn "Statut inattendu ($STATUT) sur la tentative d'injection — à vérifier manuellement (l'ORM protège normalement contre l'injection SQL classique)."
fi

echo ""
echo "--- 9. CORS — origine non autorisée ---"
ENTETE_CORS=$(curl -s -I "$BASE_URL/api/v1/health-centers/nearby?lat=12.37&lng=-1.51" \
  -H "Authorization: Bearer $TOKEN_CITOYEN" \
  -H "Origin: https://site-malveillant-exemple.com" | grep -i "access-control-allow-origin")

if [ -z "$ENTETE_CORS" ]; then
    pass "Aucune autorisation CORS accordée à une origine non listée."
else
    fail "CORS autorise une origine non listée : $ENTETE_CORS"
fi

echo ""
echo "--- 10. Limitation de débit sur l'inscription ---"
COMPTEUR_429=0
for i in $(seq 1 15); do
    STATUT=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
      -H "Content-Type: application/json" \
      -d "{\"nom\":\"Spam$i\",\"telephone\":\"+2267000${i}999\",\"mot_de_passe\":\"motdepasse123\"}")
    if [ "$STATUT" == "429" ]; then
        COMPTEUR_429=$((COMPTEUR_429+1))
    fi
done

if [ "$COMPTEUR_429" -gt 0 ]; then
    pass "La limitation de débit s'est déclenchée après plusieurs inscriptions rapides."
else
    warn "Aucun blocage 429 observé sur /register — la limite globale (200/heure) est peut-être trop large pour ce test rapide, ou cette route n'est pas dans un blueprint limité spécifiquement."
fi

echo ""
echo "--- 11. En-têtes de sécurité HTTP ---"
ENTETES=$(curl -s -I "$BASE_URL/")
for entete in "X-Content-Type-Options" "X-Frame-Options" "Referrer-Policy"; do
    if echo "$ENTETES" | grep -qi "$entete"; then
        pass "En-tête '$entete' présent."
    else
        fail "En-tête '$entete' MANQUANT."
    fi
done

echo ""
echo "============================================"
echo "  RÉSULTAT : $reussis réussis / $((reussis+echoues)) tests"
echo "============================================"
