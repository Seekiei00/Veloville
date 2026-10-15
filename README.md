# VéloVille — Plateforme de valorisation des données

Projet réalisé pour l'épreuve E2 (RNCP39103, bloc 2) — version **1.0.0** (en préparation).

L'application importe les exports CSV de VéloVille (stations, trajets,
incidents), les nettoie, les stocke dans PostgreSQL, les expose via une API
sécurisée (FastAPI) et les affiche dans un front Streamlit.

## Technologies

- **PostgreSQL** : base de données `veloville`
- **FastAPI** + SQLAlchemy : API REST, authentification JWT (PyJWT) et mots de passe hachés (bcrypt)
- **Streamlit** : front (tableaux et métriques, sans graphique)
- **pytest** + pytest-cov : tests et couverture

## Organisation du projet

```
api/            l'API (main.py, database.py, models.py, schemas.py, securite.py)
  routers/      auth, stations, trajets, incidents, indicateurs
  services/     fiabilisation.py, indicateurs.py, consultation.py (logique métier)
front/          app.py (connexion), api_client.py, commun.py, pages/ (Stations, Incidents, Indicateurs)
scripts/        importer.py, sauvegarde.sh, purger_trajets.py
sql/            schema.sql, comptes.sql
tests/          unit/ et integration/
docs/           schéma de données, droits, déploiement, recette, journal d'import
data/           les 3 fichiers CSV
```

## Prérequis

- Python 3.12 ou plus (testé avec 3.14.7)
- PostgreSQL 14 ou plus (testé avec 18)
- Git, et bash pour la sauvegarde (Git Bash sous Windows)

## Installation

La procédure détaillée est dans [docs/procedure-deploiement.md](docs/procedure-deploiement.md).

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux / Mac : source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env              # puis remplir JWT_SECRET et MOT_DE_PASSE_RECETTE

psql -U postgres -c "CREATE ROLE veloville LOGIN PASSWORD 'veloville';"
psql -U postgres -c "CREATE DATABASE veloville OWNER veloville;"
psql -U veloville -d veloville -f sql/schema.sql
psql -U veloville -d veloville -f sql/comptes.sql
```

Comptes de test (créés par `sql/comptes.sql`, mots de passe hachés en bcrypt) :

| Identifiant | Mot de passe | Rôle |
|---|---|---|
| exploitant01 | Formation2026! | exploitant |
| direction01 | Formation2026! | direction |

## Variables d'environnement (`.env`)

Le modèle est [`.env.example`](.env.example).

| Variable | Rôle | Valeur dans `.env.example` |
|---|---|---|
| `DATABASE_URL` | connexion à PostgreSQL | `postgresql+psycopg://veloville:veloville@localhost:5432/veloville` |
| `DATABASE_TEST_URL` | prévue pour une base de test séparée (pas encore utilisée par le code) | `postgresql+psycopg://veloville:veloville@localhost:5432/veloville_test` |
| `JWT_SECRET` | clé secrète pour signer les jetons, à générer avec `python -c "import secrets; print(secrets.token_hex(32))"` | vide |
| `JWT_ALGORITHM` | algorithme de signature | `HS256` |
| `JWT_EXPIRATION_MINUTES` | durée de validité du jeton | `60` |
| `API_URL` | adresse de l'API utilisée par le front | `http://127.0.0.1:8000` |
| `API_TIMEOUT_SECONDES` | délai maximum d'un appel du front | `5` |
| `MOT_DE_PASSE_RECETTE` | mot de passe des comptes de test, utilisé par les tests | vide |

Le fichier `.env` n'est jamais commité (il est dans `.gitignore`).

## Import des données

```bash
python scripts/importer.py
```

Le script lit les 3 CSV, applique les règles de nettoyage
(`api/services/fiabilisation.py`), vide puis recharge les tables (on peut donc
le relancer sans créer de doublons) et écrit le journal des rejets dans
**`docs/journal-import.csv`** (colonnes : fichier, identifiant, colonne,
valeur, motif, decision).

Résultat :

```
stations.csv : 120 lues = 120 importées + 0 rejetées + 0 doublons
trajets.csv : 2030 lues = 2002 importées + 16 rejetées + 12 doublons
incidents.csv : 180 lues = 177 importées + 3 rejetées + 0 doublons
Journal : docs/journal-import.csv (190 lignes)
```

## Lancement

```bash
uvicorn api.main:app --reload       # API : http://127.0.0.1:8000 (doc : /docs)
streamlit run front/app.py          # Front : http://localhost:8501
```

## Tests

```bash
pytest --cov=api/services --cov-report=term-missing
```

- `tests/unit/` : règles de fiabilisation, indicateurs, client HTTP du front
- `tests/integration/test_api.py` : appels à l'API avec `TestClient` (login, 401, 403, pagination, indicateurs)
- `tests/integration/test_front.py` : écrans Streamlit testés avec `AppTest` (connexion, stations, incidents, indicateurs, API arrêtée)

Les tests ont besoin de la base importée : lancer `python scripts/importer.py`
avant. Les tests qui modifient un incident le remettent dans son état initial.

**Résultat : 57 tests, couverture de `api/services` : 94 %.**

## Audit des données

Le détail est dans [docs/schema-donnees.md](docs/schema-donnees.md).

| Fichier | Problèmes trouvés | Traitement |
|---|---|---|
| stations.csv | aucun | 120 importées |
| trajets.csv | 12 lignes en double | doublons écartés |
| | 7 arrivées vers une station `S999` qui n'existe pas | rejetées (RG2) |
| | 9 durées nulles ou négatives | rejetées (RG4) |
| | 6 `velo_id` en minuscules, 5 dates au format `JJ/MM/AAAA` | corrigés et importés |
| incidents.csv | 125 statuts mal écrits (`Ouvert`, `En cours`, `RESOLU`…) | corrigés et importés |
| | 3 dates de résolution avant la date de signalement | rejetées (RG8) |
| | 25 incidents pris en charge sans technicien | importés avec avertissement |

## Choix écoresponsables

- **Pagination côté serveur** : l'API ne renvoie qu'une page (20 lignes par
  défaut, 100 au maximum). On ne transfère jamais toute une table.
- **Pas de rafraîchissement automatique** : le front n'appelle l'API que
  lorsque l'utilisateur agit. Sur l'écran Indicateurs, les calculs ne sont
  relancés qu'au clic sur « Actualiser ».
- **Cache** : la liste des communes (qui change rarement) est gardée une
  heure avec `st.cache_data(ttl=3600)`.
- **Calculs en SQL** : les indicateurs sont calculés par PostgreSQL
  (`GROUP BY`, `count`, `avg`) ; seul le résultat est envoyé.
- **Index** : 6 index sur les colonnes utilisées dans les filtres et les indicateurs.
- **Dépendances limitées** : `requirements.txt` ne contient que les paquets
  nécessaires au projet, avec leurs versions figées.
- **Purge** des vieux trajets avec `scripts/purger_trajets.py` (RGPD,
  13 mois par défaut), ce qui limite aussi la taille de la base.

## Écarts au sujet

- Développé avec Python 3.14, car c'est la version installée sur mon poste
  (le sujet indique Python 3.12).
- Fichiers ajoutés :
  - `api/services/consultation.py` : requêtes paginées et changement de
    statut, pour que les routeurs ne contiennent pas de logique métier ;
  - `front/commun.py` : vérification de connexion et barre latérale,
    communes aux trois pages ;
  - `scripts/purger_trajets.py` : bonus, purge des vieux trajets ;
  - `tests/integration/test_front.py` : tests des écrans du front.

## Limites connues

- Recharger la page du navigateur (F5) déconnecte l'utilisateur, car le
  jeton n'est gardé qu'en session Streamlit.
- Relancer l'import remet les incidents dans leur état d'origine : les
  changements de statut faits dans l'application sont perdus.
- Le jeton expire au bout de 60 minutes ; il faut alors se reconnecter.
- Pas de HTTPS : à prévoir pour une mise en production.

## Documentation

- [docs/schema-donnees.md](docs/schema-donnees.md) : schéma de la base, règles de gestion, audit
- [docs/matrice-roles-droits.md](docs/matrice-roles-droits.md) : droits par rôle, données sensibles
- [docs/procedure-deploiement.md](docs/procedure-deploiement.md) : installation, sauvegarde, restauration
- [docs/recette/resultats-recette.md](docs/recette/resultats-recette.md) : résultats de la recette
- [docs/journal-import.csv](docs/journal-import.csv) : journal des rejets et avertissements de l'import
- [CHANGELOG.md](CHANGELOG.md) : historique des versions
