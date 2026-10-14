# Procédure de déploiement

Toutes les commandes se lancent **depuis la racine du projet**. Sous Windows,
si `psql` n'est pas reconnu, utiliser le chemin complet
(`& "C:\Program Files\PostgreSQL\18\bin\psql.exe"`) ou ajouter ce dossier au PATH.

## 1. Prérequis

- Python 3.12 ou plus (testé avec 3.14.7)
- PostgreSQL 14 ou plus (testé avec 18), serveur démarré
- Git, et bash pour la sauvegarde (Git Bash sous Windows)

## 2. Récupérer le projet et installer Python

```bash
git clone <url-du-depot> veloville
cd veloville
python -m venv .venv
.venv\Scripts\activate              # Linux / Mac : source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configurer le `.env`

```bash
cp .env.example .env                # PowerShell : Copy-Item .env.example .env
```

Dans `.env`, remplir :
- `JWT_SECRET` : générer une valeur avec
  `python -c "import secrets; print(secrets.token_hex(32))"` ;
- `MOT_DE_PASSE_RECETTE` : le mot de passe des comptes de test (voir README),
  utilisé par les tests.

Les autres valeurs de `.env.example` conviennent. Vérifier avec `git status`
que `.env` n'apparaît pas.

## 4. Créer la base

```bash
psql -U postgres -h localhost -c "CREATE ROLE veloville LOGIN PASSWORD 'veloville';"
psql -U postgres -h localhost -c "CREATE DATABASE veloville OWNER veloville;"
psql -U veloville -h localhost -d veloville -f sql/schema.sql
psql -U veloville -h localhost -d veloville -f sql/comptes.sql
```

`sql/schema.sql` peut être relancé : il supprime puis recrée les tables. Il
faut ensuite relancer `sql/comptes.sql` et l'import.

Si le rôle ou la base existent déjà :
```bash
psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS veloville WITH (FORCE);"
psql -U postgres -h localhost -c "DROP ROLE IF EXISTS veloville;"
```

## 5. Importer les données

```bash
python scripts/importer.py
```

Résultat attendu (identique à chaque exécution) :
```
Comptages en base : station = 120 | trajet = 2002 | incident = 177
stations.csv : 120 lues = 120 importées + 0 rejetées + 0 doublons
trajets.csv : 2030 lues = 2002 importées + 16 rejetées + 12 doublons
incidents.csv : 180 lues = 177 importées + 3 rejetées + 0 doublons
Journal : docs/journal-import.csv (190 lignes)
```

## 6. Lancer les tests

```bash
pytest --cov=api/services --cov-report=term-missing
```

Attendu : 57 tests réussis, couverture de `api/services` : 94 %. Les tests
ont besoin de la base importée (étape 5) et de `MOT_DE_PASSE_RECETTE` dans
le `.env`.

## 7. Lancer l'API et vérifier

```bash
uvicorn api.main:app --reload
```

Dans un autre terminal :
```bash
curl http://127.0.0.1:8000/sante
# {"statut":"ok"}
```
Sous PowerShell : `Invoke-RestMethod http://127.0.0.1:8000/sante`.
Documentation interactive : http://127.0.0.1:8000/docs.

## 8. Lancer le front

```bash
streamlit run front/app.py
```

Ouvrir http://localhost:8501 et se connecter avec `exploitant01` ou `direction01`.

## 9. Vérifications après déploiement

| Vérification | Attendu |
|---|---|
| `GET /sante` | `{"statut":"ok"}` |
| `GET /stations` sans jeton | 401 |
| `POST /auth/login` avec `direction01` | 200, `"role":"direction"` |
| `GET /stations` avec le jeton | `"total":120` |
| `PUT /incidents/I2026-0002/statut` avec le jeton direction | 403 |
| `streamlit run front/app.py` | écran de connexion |

## 10. Sauvegarde

```bash
bash scripts/sauvegarde.sh
# Sauvegarde créée : sauvegardes/veloville_AAAAMMJJ_HHMMSS.dump
```

- Le script doit être lancé depuis la racine du projet (il lit `DATABASE_URL`
  dans `.env`, sans l'afficher).
- Format `pg_dump` custom, dans le dossier `sauvegardes/` (ignoré par Git).
- Code de retour 1 si la sauvegarde échoue (le fichier incomplet est supprimé).
- Sous Windows, si `pg_dump` n'est pas dans le PATH :
  ```bash
  PG_BIN="/c/Program Files/PostgreSQL/18/bin" bash scripts/sauvegarde.sh
  ```

Vérifier qu'une sauvegarde est lisible :
```bash
pg_restore --list sauvegardes/veloville_AAAAMMJJ_HHMMSS.dump
```

## 11. Restauration

```bash
pg_restore --clean --if-exists -d "postgresql://veloville:veloville@localhost:5432/veloville" sauvegardes/veloville_AAAAMMJJ_HHMMSS.dump
```

Sur un poste neuf : créer d'abord le rôle et la base (étape 4, sans
`schema.sql` ni `comptes.sql`), car la sauvegarde contient déjà les tables,
les données et les comptes.

Contrôle après restauration :
```bash
psql -U veloville -h localhost -d veloville -c "SELECT (SELECT count(*) FROM station), (SELECT count(*) FROM trajet), (SELECT count(*) FROM incident), (SELECT count(*) FROM utilisateur);"
```

## 12. Purge des vieux trajets (bonus)

```bash
python scripts/purger_trajets.py --jours 395               # simulation, ne supprime rien
python scripts/purger_trajets.py --jours 395 --appliquer   # supprime vraiment
```

## Problèmes fréquents

| Problème | Solution |
|---|---|
| `psql` n'est pas reconnu | utiliser le chemin complet ou ajouter `C:\Program Files\PostgreSQL\18\bin` au PATH |
| `le rôle « veloville » existe déjà` | voir les commandes `DROP` de l'étape 4 |
| `password authentication failed for user "veloville"` | refaire l'étape 4 |
| Erreur au login / jeton | vérifier que `JWT_SECRET` est rempli dans `.env` |
| Tests « skipped » | remplir `MOT_DE_PASSE_RECETTE` dans `.env` |
| `test_incidents_par_statut` échoue | un incident a été modifié dans l'application : relancer l'import (étape 5) |
| Front : « L'API est injoignable » | lancer l'API (étape 7) |
| `sauvegarde.sh` : `pg_dump: command not found` | renseigner `PG_BIN` (étape 10) |
