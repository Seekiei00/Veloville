# Résultats de recette — VéloVille V1

Plan déroulé : [`plan-de-recette.md`](plan-de-recette.md) (REC-01 à REC-10),
dans l'ordre, à partir d'un état connu, sans correction pendant le passage.

## Conditions d'exécution

| Élément | Valeur |
|---|---|
| Version testée | `v1.0.0` (commit `dad729c`) |
| Date de la campagne | 15/10/2026 |
| Poste | Windows 11, Python 3.14.7, PostgreSQL 18 |
| État de départ | base recréée avec `sql/schema.sql`, comptes chargés avec `sql/comptes.sql`, aucun import exécuté |
| API | `uvicorn api.main:app --reload` |
| Front | `streamlit run front/app.py` |
| Outils | `psql` pour les requêtes SQL, `curl` / `Invoke-RestMethod` pour l'API |
| Comptes | `exploitant01`, `direction01` |

## Relevé d'exécution

| Cas | Date et heure | Version testée | Statut | Preuve | Anomalie |
|---|---|---|---|---|---|
| REC-01 | 15/10/2026 08:57 | v1.0.0 (`dad729c`) | OK | [§ REC-01](#rec-01--import-idempotent--ok) | — |
| REC-02 | 15/10/2026 09:00 | v1.0.0 (`dad729c`) | OK | [§ REC-02](#rec-02--rejets-journalisés-et-cohérence-des-volumes--ok) | — |
| REC-03 | 15/10/2026 09:11 | v1.0.0 (`dad729c`) | OK | [§ REC-03](#rec-03--connexion-acceptée--ok) | ANO-001 (lenteur) |
| REC-04 | 15/10/2026 09:11 | v1.0.0 (`dad729c`) | OK | [§ REC-04](#rec-04--connexion-refusée--ok) | ANO-001 (lenteur) |
| REC-05 | 15/10/2026 09:11 | v1.0.0 (`dad729c`) | OK | [§ REC-05](#rec-05--route-protégée-sans-jeton--ok) | ANO-001 (lenteur) |
| REC-06 | 15/10/2026 09:11 | v1.0.0 (`dad729c`) | OK | [§ REC-06](#rec-06--rôle-direction-refusé-sur-la-modification-dun-incident--ok) | ANO-001 (lenteur) |
| REC-07 | 15/10/2026 09:11 | v1.0.0 (`dad729c`) | OK | [§ REC-07](#rec-07--pagination--ok) | ANO-001 (lenteur) |
| REC-08 | 15/10/2026 09:11 | v1.0.0 (`dad729c`) | OK | [§ REC-08](#rec-08--station-introuvable--ok) | ANO-001 (lenteur) |
| REC-09 | 15/10/2026 09:11 | v1.0.0 (`dad729c`) | OK | [§ REC-09](#rec-09--cohérence-de-lindicateur--activité-par-jour--avec-la-base--ok) | ANO-001 (lenteur) |
| REC-10 | 15/10/2026 09:25 | v1.0.0 (`dad729c`) | OK | [§ REC-10](#rec-10--front--état-vide-et-état-derreur--ok) | — |

## Résultats obtenus et preuves

### REC-01 — Import idempotent : OK

**Objectif :** vérifier qu'une seconde exécution de l'import ne modifie pas la base.

**Attendu :** les deux exécutions se terminent sans erreur ; les trois
comptages sont identiques entre les étapes 2 et 4 ; `count(*) FROM station`
vaut 120.

**Obtenu :** les deux exécutions se terminent sans erreur (code retour 0),
les comptages sont identiques (120 / 2002 / 177) et la table `station`
contient 120 lignes.

**Preuve :**

État de départ (après `schema.sql` et `comptes.sql`) :
```
 station | trajet | incident
---------+--------+----------
       0 |      0 |        0
```

Étape 1 — `python scripts/importer.py` :
```
Comptages en base : station = 120 | trajet = 2002 | incident = 177
stations.csv : 120 lues = 120 importées + 0 rejetées + 0 doublons
trajets.csv : 2030 lues = 2002 importées + 16 rejetées + 12 doublons
incidents.csv : 180 lues = 177 importées + 3 rejetées + 0 doublons
Journal : docs/journal-import.csv (190 lignes)
code retour : 0
```

Étape 2 — `SELECT count(*)` sur les trois tables :
```
 station | trajet | incident
---------+--------+----------
     120 |   2002 |      177
```

Étape 3 — `python scripts/importer.py` (2e exécution) :
```
Comptages en base : station = 120 | trajet = 2002 | incident = 177
stations.csv : 120 lues = 120 importées + 0 rejetées + 0 doublons
trajets.csv : 2030 lues = 2002 importées + 16 rejetées + 12 doublons
incidents.csv : 180 lues = 177 importées + 3 rejetées + 0 doublons
Journal : docs/journal-import.csv (190 lignes)
code retour : 0
```

Étape 4 — `SELECT count(*)` sur les trois tables :
```
 station | trajet | incident
---------+--------+----------
     120 |   2002 |      177
```

Comparaison étapes 2 et 4 : identiques ✅

### REC-02 — Rejets journalisés et cohérence des volumes : OK

**Objectif :** vérifier que chaque ligne écartée est tracée avec son motif et
que rien n'est perdu silencieusement.

**Attendu :** pour chaque fichier, importées + rejetées + doublons écartés =
lignes du CSV. Chaque ligne du journal porte les six informations. La requête
de l'étape 4 renvoie 0.

**Obtenu :** les volumes sont cohérents pour les trois fichiers, les
190 lignes du journal portent toutes les six informations, et la requête de
l'étape 4 renvoie 0.

**Preuve :**

Étape 1 — journal ouvert : `docs/journal-import.csv`, en-tête :
```
fichier,identifiant,colonne,valeur,motif,decision
```

Étape 2 — comptages :

| Fichier | Lignes du CSV (hors en-tête) | Importées (`count(*)`) | Rejets journalisés | Doublons écartés journalisés | Importées + rejets + doublons |
|---|---:|---:|---:|---:|---:|
| stations.csv | 120 | 120 | 0 | 0 | 120 ✅ |
| trajets.csv | 2 030 | 2 002 | 16 | 12 | 2 030 ✅ |
| incidents.csv | 180 | 177 | 3 | 0 | 180 ✅ |

Détail du journal par fichier et par décision :
```
  25  incidents.csv, avertissement
 124  incidents.csv, normalisation
   3  incidents.csv, rejet
  12  trajets.csv, doublon écarté
  10  trajets.csv, normalisation
  16  trajets.csv, rejet
```
Les normalisations et les avertissements concernent des lignes importées :
ils n'entrent pas dans le calcul des volumes.

Étape 3 — lignes du journal avec un des six champs vide : `0`. Exemples :
```
trajets.csv,T480030,station_arrivee,S999,station d'arrivée inconnue,rejet
trajets.csv,T480073,(ligne entière),"T480073,V1712,2026-08-24 18:09:36,S092,S043,1423,occasionnel,",ligne identique à une ligne déjà lue,doublon écarté
trajets.csv,T480086,velo_id,v1281,identifiant de vélo mis en majuscules,normalisation
incidents.csv,I2026-0028,date_resolution,2026-07-22 06:00,date de résolution incohérente,rejet
```

Étape 4 — trajets dont la station d'arrivée n'existe pas :
```sql
SELECT count(*) FROM trajet t LEFT JOIN station s ON s.station_id = t.station_arrivee
WHERE t.station_arrivee IS NOT NULL AND s.station_id IS NULL;
```
```
 count
-------
     0
```

Pour REC-03 à REC-09, les appels sont faits avec `httpx` vers
`http://localhost:8000`, l'adresse de `API_URL` dans `.env`. Le temps de
réponse de chaque appel est noté entre parenthèses.

### REC-03 — Connexion acceptée : OK

**Attendu :** 200 ; corps contenant `access_token` non vide, `token_type` =
`bearer`, `role` = `exploitant` (puis `direction`).

**Obtenu :** 200 pour les deux comptes, jeton non vide, `token_type` =
`bearer`, rôle correct.

**Preuve :**
```
POST /auth/login {"username":"exploitant01", ...} -> 200 (2335 ms)
  access_token non vide = True ; token_type = bearer ; role = exploitant
POST /auth/login {"username":"direction01", ...}  -> 200 (2238 ms)
  access_token non vide = True ; token_type = bearer ; role = direction
```

### REC-04 — Connexion refusée : OK

**Attendu :** 401 dans les deux cas, corps `{"detail": "Identifiants invalides"}`,
message identique pour un identifiant inconnu et un mot de passe erroné.

**Obtenu :** 401 et même message dans les deux cas.

**Preuve :**
```
1. POST /auth/login {"username":"exploitant01","password":"mauvais"}  -> 401 (2234 ms) {"detail":"Identifiants invalides"}
2. POST /auth/login {"username":"inconnu", ...}                      -> 401 (2048 ms) {"detail":"Identifiants invalides"}
```

### REC-05 — Route protégée sans jeton : OK

**Attendu :** étapes 1 et 2 : 401 ; étape 3 : 200 `{"statut": "ok"}`.

**Obtenu :** conforme.

**Preuve :**
```
1. GET /stations (sans en-tête Authorization)              -> 401 (2057 ms) {"detail":"Authentification requise"}
2. GET /stations (Authorization: Bearer jeton.invalide.xyz) -> 401 (2040 ms) {"detail":"Jeton invalide ou expire"}
3. GET /sante                                              -> 200 (2079 ms) {"statut":"ok"}
```

### REC-06 — Rôle direction refusé sur la modification d'un incident : OK

**Attendu :** étape 1 : 403 `{"detail": "Acces reserve au role exploitant"}` ;
étape 2 : statut inchangé `ouvert` ; étape 3 : 200 avec `statut` = `en_cours` ;
étape 4 : `en_cours` en base ; étape 5 : 422
`{"detail": "Transition de statut non autorisee"}`.

**Obtenu :** conforme, sur l'incident `I2026-0002` (premier incident `ouvert`).

**Preuve :**
```
1. PUT /incidents/I2026-0002/statut {"statut":"en_cours"} (jeton direction)   -> 403 (2051 ms) {"detail":"Acces reserve au role exploitant"}
2. SELECT statut FROM incident WHERE incident_id='I2026-0002'                -> ouvert
3. PUT /incidents/I2026-0002/statut {"statut":"en_cours"} (jeton exploitant)  -> 200 (2066 ms) {"incident_id":"I2026-0002",...,"statut":"en_cours",...}
4. SELECT statut ...                                                         -> en_cours
5. PUT /incidents/I2026-0002/statut {"statut":"en_cours"} (jeton exploitant)  -> 422 (2068 ms) {"detail":"Transition de statut non autorisee"}
```

### REC-07 — Pagination : OK

**Attendu :** étape 1 : 200, `total` = 120, `page` = 1, `taille_page` = 50,
50 résultats, premier `station_id` = `S001` ; étape 2 : 200, 20 résultats ;
étape 3 : 200, `total` = 46, tous les résultats ont `commune` = `Lille` ;
étapes 4 et 5 : 422.

**Obtenu :** conforme.

**Preuve :**
```
1. GET /stations?taille_page=50&page=1         -> 200 (2049 ms) total=120 page=1 taille_page=50, 50 résultats, premier S001
2. GET /stations?taille_page=50&page=3         -> 200 (2041 ms) 20 résultats
3. GET /stations?commune=Lille&taille_page=100 -> 200 (2046 ms) total=46, communes présentes : ['Lille']
4. GET /stations?page=0                        -> 422 (2047 ms) "Input should be greater than or equal to 1"
5. GET /stations?taille_page=101               -> 422 (2023 ms) "Input should be less than or equal to 100"
```

### REC-08 — Station introuvable : OK

**Attendu :** étape 1 : 200, `station_id` = `S001`, `nom` = `Lille - Gare` ;
étape 2 : 404 `{"detail": "Station introuvable"}`.

**Obtenu :** conforme.

**Preuve :**
```
1. GET /stations/S001 -> 200 (2030 ms) {"station_id":"S001","nom":"Lille - Gare",...}
2. GET /stations/S999 -> 404 (2031 ms) {"detail":"Station introuvable"}
```

### REC-09 — Cohérence de l'indicateur « activité par jour » avec la base : OK

**Attendu :** les lignes de la réponse et de la requête SQL sont identiques
(mêmes jours, mêmes comptages, ordre croissant) ; la somme des `nb_trajets`
est égale au `total` de `GET /trajets` sur la même période.

**Obtenu :** lignes identiques et égalité vérifiée (2 002 = 2 002).

**Preuve :**

1. `GET /indicateurs/activite-par-jour?date_debut=2026-08-24&date_fin=2026-08-30` → 200 (2073 ms)
2. Requête SQL du plan :
   `SELECT depart_horodatage::date AS jour, count(*) AS nb_trajets FROM trajet WHERE depart_horodatage::date BETWEEN '2026-08-24' AND '2026-08-30' GROUP BY jour ORDER BY jour;`
3. Comparaison ligne à ligne :

| Jour | API | SQL |
|---|---:|---:|
| 2026-08-24 | 329 | 329 |
| 2026-08-25 | 311 | 311 |
| 2026-08-26 | 306 | 306 |
| 2026-08-27 | 300 | 300 |
| 2026-08-28 | 315 | 315 |
| 2026-08-29 | 219 | 219 |
| 2026-08-30 | 222 | 222 |

4. `GET /trajets?date_debut=2026-08-24&date_fin=2026-08-30` → 200 (2042 ms),
   `total` = 2002 ; somme des `nb_trajets` = 2002 → égalité vérifiée.

### Observation pendant REC-03 à REC-09 : temps de réponse d'environ 2 s

Tous les résultats attendus sont obtenus, mais **chaque appel prend environ
2 secondes**, même `GET /sante`, qui ne fait aucun calcul. Le cahier des
charges (§ 7.1) demande qu'une consultation paginée réponde en moins de 2 s.
Conformément au plan, rien n'est corrigé pendant le passage : l'écart est
relevé et fera l'objet de la fiche [ANO-001](anomalies/ANO-001.md).

Mesure complémentaire (15/10/2026 09:13) :
```
localhost se résout en : ['::1', '127.0.0.1']
http://localhost:8000/sante -> 2066 ms
http://127.0.0.1:8000/sante -> 8 ms
http://localhost:8000/sante -> 2046 ms
http://127.0.0.1:8000/sante -> 8 ms
API à l'écoute sur : 127.0.0.1:8000 (pas sur ::1)
.env : API_URL=http://localhost:8000
```

### REC-10 — Front : état vide et état d'erreur : OK

**Attendu :** étape 1 : message « Aucun résultat pour ces critères. » (ou
équivalent), pas d'erreur. Étapes 3 et 4 : un message d'erreur en français
indiquant que l'API est injoignable, sans trace Python ni code source.
Étape 5 : le tableau s'affiche de nouveau.

**Obtenu :** conforme. Test fait dans le navigateur, connecté avec
`direction01`. Les écrans ont été rechargés avec le menu latéral (un
rechargement F5 du navigateur ferme la session Streamlit).

**Preuve :**

| Étape | Action | Résultat obtenu | Capture |
|---|---|---|---|
| 1 | Écran Incidents, filtre sur chaque statut | les trois statuts (`ouvert`, `en_cours`, `resolu`) renvoient des résultats : aucun statut vide, donc variante du plan | [incidents](captures/rec10-etape1-incidents-statuts.png) |
| 1 (variante) | Écran Stations, page 7 (il y a 6 pages de 20) | « 120 stations au total », « Aucun résultat pour ces critères. », « Page 7 sur 6 », pas d'erreur | [stations page 7](captures/rec10-etape1-stations-page7-vide.png) |
| 2 | Arrêt de l'API (`Ctrl+C` dans le terminal d'uvicorn) | « Shutting down », « Application shutdown complete. », « Finished server process » : API arrêtée | [terminal uvicorn](captures/rec10-etape2-api-arretee.png) |
| 3 | Écran Stations rechargé | « L'API est injoignable. Vérifiez qu'elle est démarrée. », aucune trace Python | [stations API arrêtée](captures/rec10-etape3-stations-api-arretee.png) |
| 4 | Écran Indicateurs rechargé | « L'API est injoignable. Vérifiez qu'elle est démarrée. », aucune trace Python | [indicateurs API arrêtée](captures/rec10-etape4-indicateurs-api-arretee.png) |
| 5 | API relancée (`uvicorn api.main:app --reload`), écran Stations rechargé | « 120 stations au total », tableau affiché, « Page 1 sur 6 » | [stations API relancée](captures/rec10-etape5-stations-api-relancee.png) |

Observation : sur l'écran Incidents, les dates s'affichent au format
`2026-08-30T18:00:00` (avec un « T »), alors que la maquette montre
`2026-08-30 18:00`. Cela ne change pas le résultat attendu du cas.

## Synthèse

À compléter à la fin de la campagne : N cas exécutés sur 10 ; N OK, N KO,
N NT ; N anomalies ouvertes, N corrigées.

## Procès-verbal de recette

À compléter à la fin de la campagne (modèle dans le plan de recette).

## Axes d'amélioration

À compléter à la fin de la campagne (au moins trois propositions argumentées).
