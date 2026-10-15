# Journal des versions

Format : une section par version, les changements regroupés en « Ajouté »,
« Modifié », « Corrigé ». Chaque version correspond à un tag Git `vX.Y.Z`.

## [1.0.1] - 2026-10-15

Version après la recette.

### Ajouté
- Résultats de recette (`docs/recette/resultats-recette.md`) : relevé du
  premier passage et du rejeu, preuves, captures d'écran du front, synthèse,
  procès-verbal et axes d'amélioration.
- Fiche d'anomalie `docs/recette/anomalies/ANO-001.md`.
- Test de non-régression `test_ano_001_api_url_en_ipv4`.

### Modifié
- README : valeur d'`API_URL` mise à jour.
- `docs/schema-donnees.md` : suppression du texte du squelette resté en tête
  du document.

### Corrigé
- ANO-001 : chaque appel à l'API prenait environ 2 s, car `localhost` est
  d'abord résolu en IPv6 sous Windows alors que l'API écoute en IPv4.
  `API_URL` passe à `http://127.0.0.1:8000` : les appels prennent maintenant
  quelques millisecondes.

## [1.0.0] - 2026-10-14

Version livrée en recette.

### Ajouté
- Schéma de la base `sql/schema.sql` : tables `station`, `trajet`,
  `incident`, `utilisateur`, clés primaires et étrangères, contraintes
  `CHECK` des règles RG1 à RG8, index.
- Règles de fiabilisation des données (`api/services/fiabilisation.py`) et
  leurs tests unitaires.
- Connexion à la base (`api/database.py`), modèles des tables
  (`api/models.py`) et import idempotent des trois CSV
  (`scripts/importer.py`), avec le journal des rejets et avertissements
  (`docs/journal-import.csv`).
- Services métier : trois indicateurs calculés en SQL
  (`api/services/indicateurs.py`) et consultation paginée
  (`api/services/consultation.py`).
- API FastAPI : route `/sante`, connexion JWT (`POST /auth/login`), routes
  stations, trajets, incidents et indicateurs, changement de statut d'un
  incident réservé à l'exploitant.
- Front Streamlit : client HTTP centralisé, écran de connexion, écrans
  Stations, Incidents et Indicateurs, fichier commun `front/commun.py`.
- Tests : tests unitaires des indicateurs et du client HTTP, tests
  d'intégration de l'API et tests des écrans du front (57 tests, couverture
  de `api/services` : 94 %).
- Script de sauvegarde `scripts/sauvegarde.sh` (pg_dump horodaté) et script
  de purge des trajets de plus de 13 mois `scripts/purger_trajets.py`.
- Documentation : README, matrice des rôles et des droits, procédure de
  déploiement.

### Modifié
- `requirements.txt` : versions des dépendances figées.

### Corrigé
- Erreur au lancement des tests : `api/main.py` incluait des routeurs encore
  vides. Seule la route `/sante` a été gardée, puis les routeurs ont été
  ajoutés une fois écrits.

## [0.1.0] - 2026-10-07

### Ajouté
- Initialisation du projet à partir du squelette fourni.
