# Matrice des rôles et des droits

Trois profils : **anonyme** (pas de jeton, ou jeton invalide ou expiré),
**exploitant** (`exploitant01`) et **direction** (`direction01`).

Les contrôles sont faits dans `api/securite.py` :
- `utilisateur_courant()` : vérifie le jeton JWT, 401 sinon ;
- `exiger_exploitant()` : vérifie le rôle, 403 si ce n'est pas un exploitant.

## Routes de l'API

| Route | Anonyme | Exploitant | Direction |
|---|---|---|---|
| GET /sante | ✅ 200 | ✅ 200 | ✅ 200 |
| POST /auth/login | ✅ 200 (401 si identifiants faux) | ✅ 200 | ✅ 200 |
| GET /stations | ❌ 401 | ✅ 200 | ✅ 200 |
| GET /stations/{station_id} | ❌ 401 | ✅ 200 (404 si inconnue) | ✅ 200 (404 si inconnue) |
| GET /trajets | ❌ 401 | ✅ 200 | ✅ 200 |
| GET /incidents | ❌ 401 | ✅ 200 | ✅ 200 |
| PUT /incidents/{incident_id}/statut | ❌ 401 | ✅ 200 (404 si inconnu, 422 si transition interdite) | ❌ **403** |
| GET /indicateurs/activite-par-jour | ❌ 401 | ✅ 200 | ✅ 200 |
| GET /indicateurs/stations-actives | ❌ 401 | ✅ 200 | ✅ 200 |
| GET /indicateurs/incidents-par-statut | ❌ 401 | ✅ 200 | ✅ 200 |

Toutes les routes sauf `/sante` et `/auth/login` sont protégées par
`dependencies=[Depends(utilisateur_courant)]`, déclaré dans chaque routeur.
La route PUT ajoute `Depends(exiger_exploitant)`.

## Messages d'erreur de l'API

| Code | Cas | Message (`detail`) |
|---|---|---|
| 401 | login refusé (identifiant inconnu ou mot de passe faux, même message dans les deux cas) | `Identifiants invalides` |
| 401 | pas de jeton | `Authentification requise` |
| 401 | jeton invalide ou expiré | `Jeton invalide ou expire` |
| 403 | la direction essaie de modifier un incident | `Acces reserve au role exploitant` |
| 404 | station inconnue | `Station introuvable` |
| 404 | incident inconnu | `Incident introuvable` |
| 422 | transition de statut interdite | `Transition de statut non autorisee` |
| 422 | paramètre invalide (ex. `page=0`, `taille_page=101`) | erreur de validation FastAPI |

## Écrans du front

| Écran | Anonyme | Exploitant | Direction |
|---|---|---|---|
| Connexion (`app.py`) | formulaire | « Connecté en tant que … (rôle : exploitant) » | « Connecté en tant que … (rôle : direction) » |
| Stations | « Veuillez vous connecter. », aucun appel à l'API | tableau | tableau |
| Incidents (tableau) | « Veuillez vous connecter. » | tableau | tableau |
| Incidents (« Changer le statut d'un incident ») | — | formulaire affiché | formulaire **masqué**, remplacé par « La modification des incidents est réservée aux exploitants. » |
| Indicateurs | « Veuillez vous connecter. » | 3 métriques + 3 tableaux | 3 métriques + 3 tableaux |

La vérification « Veuillez vous connecter » est faite par
`verifier_connexion()` dans `front/commun.py`, appelée en haut de chaque page.
Si l'API renvoie quand même un 403 lors d'un changement de statut, l'écran
Incidents affiche « Vous n'avez pas le droit de modifier un incident. ».

## Données sensibles

| Donnée | Protection |
|---|---|
| Mots de passe | Stockés uniquement sous forme de hachage **bcrypt** dans la table `utilisateur` (`sql/comptes.sql`). Vérifiés avec `bcrypt.checkpw`, jamais affichés ni renvoyés par l'API. Le même message est renvoyé si l'identifiant ou le mot de passe est faux. |
| Jeton JWT | Signé en HS256 avec `JWT_SECRET` (stocké seulement dans `.env`), valable `JWT_EXPIRATION_MINUTES` (60 min). Il contient seulement l'identifiant (`sub`), le rôle et la date d'expiration. Dans le front, il est gardé dans `st.session_state` : il n'apparaît ni à l'écran ni dans l'URL, et il est effacé par « Se déconnecter ». |
| `usager_ref` | Pseudonyme de l'abonné (pas de nom ni de numéro d'abonné). Son format est vérifié à l'import (`U` + 8 caractères hexadécimaux). Il n'est affiché dans aucun écran du front. Les vieux trajets peuvent être purgés (`scripts/purger_trajets.py`, 13 mois par défaut). |
| Secrets (`DATABASE_URL`, `JWT_SECRET`) | Dans `.env`, ignoré par Git (`.gitignore`). `.env.example` est versionné sans valeur sensible (`JWT_SECRET` vide). |
| Sauvegardes | Dossier `sauvegardes/` et fichiers `*.dump` ignorés par Git. |
