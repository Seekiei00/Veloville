-- Schéma de la base veloville (PostgreSQL 14+).
-- À compléter en respectant le contrat du sujet (types, clés, contraintes).
-- Le script doit être rejouable : prévoir les DROP ... IF EXISTS ou
-- CREATE TABLE IF NOT EXISTS.
BEGIN;

DROP TABLE IF EXISTS incident CASCADE;
DROP TABLE IF EXISTS trajet CASCADE;
DROP TABLE IF EXISTS station CASCADE;
DROP TABLE IF EXISTS utilisateur CASCADE;
-- ---------------------------------------------------------------
-- 1. Table station
-- ---------------------------------------------------------------
CREATE TABLE station (
    station_id VARCHAR(10) PRIMARY KEY, -- RG1
    nom VARCHAR(100) NOT NULL,
    commune VARCHAR(50) NOT NULL,
    capacite INTEGER NOT NULL,
    latitude NUMERIC(8,5) NOT NULL,
    longitude NUMERIC(8,5) NOT NULL,
    date_mise_en_service DATE NOT NULL,
    CONSTRAINT ck_station_capacite CHECK (capacite > 0) -- RG1
);


-- ---------------------------------------------------------------
-- 2. Table trajet
-- ---------------------------------------------------------------
CREATE TABLE trajet (
    trajet_id VARCHAR(12) PRIMARY KEY,
    velo_id VARCHAR(8) NOT NULL,
    depart_horodatage TIMESTAMP NOT NULL,
    station_depart VARCHAR(10) NOT NULL CONSTRAINT fk_trajet_station_depart REFERENCES station (station_id),   -- RG2
    station_arrivee VARCHAR(10)  NULL CONSTRAINT fk_trajet_station_arrivee REFERENCES station (station_id),  -- RG2, RG3
    duree_secondes INTEGER NOT NULL,
    type_usager VARCHAR(12) NOT NULL,
    usager_ref VARCHAR(12) NULL,

    CONSTRAINT ck_trajet_duree CHECK (duree_secondes > 0), -- RG4
    CONSTRAINT ck_trajet_type_usager CHECK (type_usager IN ('abonne', 'occasionnel')),
    CONSTRAINT ck_trajet_usager_ref CHECK (  -- RG5
        (type_usager = 'abonne' AND usager_ref IS NOT NULL)
        OR (type_usager = 'occasionnel' AND usager_ref IS NULL)
    )
);


-- ---------------------------------------------------------------
-- 3. Table incident
-- ---------------------------------------------------------------
CREATE TABLE incident (
    incident_id VARCHAR(12) PRIMARY KEY,
    date_signalement TIMESTAMP NOT NULL,
    cible VARCHAR(10) NOT NULL,
    velo_id VARCHAR(8) NULL,
    station_id VARCHAR(10) NULL CONSTRAINT fk_incident_station REFERENCES station (station_id), -- RG6
    type_incident VARCHAR(50) NOT NULL,
    statut VARCHAR(10) NOT NULL,
    date_resolution TIMESTAMP NULL,
    technicien VARCHAR(100) NULL, -- RG8 : absence tolérée
    CONSTRAINT ck_incident_cible CHECK ( -- RG6
        (cible = 'velo' AND velo_id IS NOT NULL AND station_id IS NULL)
        OR (cible = 'station' AND station_id IS NOT NULL AND velo_id IS NULL)
    ),
    CONSTRAINT ck_incident_statut CHECK (statut IN ('ouvert', 'en_cours', 'resolu')),  -- RG7
    CONSTRAINT ck_incident_resolution CHECK ( -- RG8
        (statut = 'resolu') = (date_resolution IS NOT NULL)
    ),
    CONSTRAINT ck_incident_dates CHECK (  -- RG8
        date_resolution IS NULL OR date_resolution >= date_signalement
    )
);


-- ---------------------------------------------------------------
-- 4. Table utilisateur
-- ---------------------------------------------------------------
CREATE TABLE utilisateur (
    id_utilisateur SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    mot_de_passe_hash VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    CONSTRAINT ck_utilisateur_role CHECK (role IN ('exploitant', 'direction'))
);


-- ---------------------------------------------------------------
-- 5. Index utiles aux filtres et aux indicateurs
-- ---------------------------------------------------------------
CREATE INDEX ix_station_commune ON station (commune);
CREATE INDEX ix_trajet_depart_horodatage ON trajet (depart_horodatage);
CREATE INDEX ix_trajet_station_depart ON trajet (station_depart);
CREATE INDEX ix_trajet_station_arrivee ON trajet (station_arrivee);
CREATE INDEX ix_incident_statut ON incident (statut);
CREATE INDEX ix_incident_date_signalement ON incident (date_signalement DESC);

COMMIT;
