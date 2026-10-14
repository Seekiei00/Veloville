# Schéma de données

À compléter : MLD textuel ou image, description des tables, clés et contraintes,
règles de gestion portées par le schéma.


# Schéma de données

La base `veloville` est créée par `sql/schema.sql`. Le script peut être
relancé : il supprime puis recrée les tables.

## MLD

```
station (station_id PK, nom, commune, capacite, latitude, longitude, date_mise_en_service)

trajet (trajet_id PK, velo_id, depart_horodatage,
        #station_depart -> station, #station_arrivee -> station (peut être vide),
        duree_secondes, type_usager, usager_ref)

incident (incident_id PK, date_signalement, cible, velo_id, #station_id -> station,
          type_incident, statut, date_resolution, technicien)

utilisateur (id_utilisateur PK, username UNIQUE, mot_de_passe_hash, role)
```

Liens : une station a plusieurs trajets (au départ et à l'arrivée) et
plusieurs incidents. La table `utilisateur` est indépendante.

## Tables

### station
| Colonne | Type | Contrainte |
|---|---|---|
| station_id | VARCHAR(10) | clé primaire |
| nom, commune | VARCHAR | obligatoires |
| capacite | INTEGER | > 0 |
| latitude, longitude | NUMERIC(8,5) | obligatoires |
| date_mise_en_service | DATE | obligatoire |

### trajet
| Colonne | Type | Contrainte |
|---|---|---|
| trajet_id | VARCHAR(12) | clé primaire |
| velo_id | VARCHAR(8) | obligatoire |
| depart_horodatage | TIMESTAMP | obligatoire |
| station_depart | VARCHAR(10) | clé étrangère vers station, obligatoire |
| station_arrivee | VARCHAR(10) | clé étrangère vers station, peut être vide |
| duree_secondes | INTEGER | > 0 |
| type_usager | VARCHAR(12) | `abonne` ou `occasionnel` |
| usager_ref | VARCHAR(12) | rempli seulement pour un abonné |

### incident
| Colonne | Type | Contrainte |
|---|---|---|
| incident_id | VARCHAR(12) | clé primaire |
| date_signalement | TIMESTAMP | obligatoire |
| cible | VARCHAR(10) | `velo` ou `station` |
| velo_id | VARCHAR(8) | rempli seulement si cible = velo |
| station_id | VARCHAR(10) | clé étrangère, rempli seulement si cible = station |
| type_incident | VARCHAR(50) | obligatoire |
| statut | VARCHAR(10) | `ouvert`, `en_cours` ou `resolu` |
| date_resolution | TIMESTAMP | remplie seulement si résolu, et après le signalement |
| technicien | VARCHAR(100) | peut être vide |

### utilisateur
| Colonne | Type | Contrainte |
|---|---|---|
| id_utilisateur | SERIAL | clé primaire |
| username | VARCHAR(50) | unique |
| mot_de_passe_hash | VARCHAR(100) | hachage bcrypt (jamais le mot de passe en clair) |
| role | VARCHAR(20) | `exploitant` ou `direction` |

Des index sont ajoutés sur les colonnes utilisées dans les filtres
(`commune`, `depart_horodatage`, stations de départ et d'arrivée, `statut`,
`date_signalement`).

## Règles de gestion

Chaque règle est vérifiée deux fois : par l'import (la ligne est rejetée et
notée dans le journal) et par la base (contrainte SQL).

| Règle | Dans la base | Dans l'import (`fiabilisation.py`) |
|---|---|---|
| RG1 : station unique, capacité > 0 | clé primaire, `CHECK (capacite > 0)` | `normaliser_station_id`, `normaliser_entier_positif` |
| RG2 : les stations d'un trajet existent | clés étrangères | `station_existe` |
| RG3 : l'arrivée peut être inconnue | `station_arrivee` peut être NULL | arrivée vide acceptée |
| RG4 : durée > 0 | `CHECK (duree_secondes > 0)` | `normaliser_entier_positif` |
| RG5 : pseudonyme seulement pour un abonné | `CHECK` sur `type_usager` / `usager_ref` | `usager_ref_valide` |
| RG6 : un incident vise un vélo OU une station | `CHECK` sur `cible` | `cible_valide`, `station_existe` |
| RG7 : 3 statuts, transitions limitées | `CHECK statut IN (...)` | `normaliser_statut` ; transitions vérifiées par l'API |
| RG8 : date de résolution cohérente | 2 `CHECK` sur `date_resolution` | `dates_incident_valides`, `technicien_manquant` |

## Audit des fichiers CSV

J'ai comparé chaque colonne au format attendu (dictionnaire des données),
cherché les doublons et vérifié que les stations citées existent.

### stations.csv (120 lignes)
Aucun problème : 120 stations importées.

### trajets.csv (2 030 lignes)
| Problème | Lignes | Traitement |
|---|---:|---|
| lignes strictement identiques | 12 | gardées une seule fois (doublon écarté) |
| station d'arrivée `S999` inexistante | 7 | rejet (RG2) |
| durée égale à 0, −45 ou −120 | 9 | rejet (RG4) |
| `velo_id` en minuscules (`v1281`) | 6 | mis en majuscules, importé |
| date au format `24/08/2026 11:01` | 5 | convertie, importée (une de ces lignes est rejetée pour `S999`) |
| station d'arrivée vide | 23 | importé (RG3 : vélo pas encore rendu) |

Bilan : 2 030 = 2 002 importées + 16 rejetées + 12 doublons.

### incidents.csv (180 lignes)
| Problème | Lignes | Traitement |
|---|---:|---|
| statut mal écrit (`Ouvert`, `en cours`, `RESOLU`, `Resolu`, `En cours`) | 125 | corrigé, importé |
| date de résolution avant la date de signalement | 3 | rejet (RG8) |
| technicien vide alors que l'incident est en cours ou résolu | 25 | importé avec un avertissement |

Bilan : 180 = 177 importées + 3 rejetées.

### Règles de traitement
- Une valeur mal écrite mais facile à corriger (majuscules, format de date)
  est corrigée, et une ligne « normalisation » est ajoutée au journal.
- Une ligne qui ne respecte pas une règle de gestion est rejetée, et une
  ligne « rejet » est ajoutée au journal.
- Une ligne identique à une ligne déjà lue n'est importée qu'une fois.
- Une donnée facultative vide (arrivée, technicien d'un incident ouvert)
  n'entraîne pas de rejet.

Tout est tracé dans `docs/journal-import.csv` (190 lignes).
