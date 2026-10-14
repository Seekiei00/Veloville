#!/usr/bin/env bash
# Sauvegarde horodatée de la base veloville avec pg_dump.
# À compléter :
#   - charger les variables de connexion depuis .env (sans les afficher) ;
#   - produire sauvegardes/veloville_AAAAMMJJ_HHMMSS.dump (format custom -Fc)
#     ou .sql.gz ;
#   - quitter avec un code de retour non nul en cas d'échec ;
#   - documenter la commande de restauration dans docs/procedure-deploiement.md.
set -euo pipefail


# Si pg_dump n'est pas dans le PATH (Windows), on peut indiquer son dossier dans PG_BIN
if [ -n "${PG_BIN:-}" ]; then
PATH="$PG_BIN:$PATH"
fi

# On lit DATABASE_URL dans le .env si elle n'est pas déjà définie
if [ -z "${DATABASE_URL:-}" ]; then
DATABASE_URL=$(grep '^DATABASE_URL=' .env | cut -d= -f2- | tr -d '\r')
fi
# pg_dump ne connaît pas le préfixe SQLAlchemy "postgresql+psycopg://"
URL=${DATABASE_URL/+psycopg/}

mkdir -p sauvegardes
FICHIER="sauvegardes/veloville_$(date +%Y%m%d_%H%M%S).dump"

if pg_dump --format=custom --file="$FICHIER" "$URL"; then
echo "Sauvegarde créée : $FICHIER"
else
echo "Erreur : la sauvegarde a échoué" >&2
rm -f "$FICHIER"
exit 1
fi
