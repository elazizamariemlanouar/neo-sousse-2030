-- ============================================================
-- SMART CITY NEO-SOUSSE 2030 — Database Schema
-- PostgreSQL | Normalized to 3NF / BCNF
-- ============================================================

-- Drop in reverse dependency order
DROP TABLE IF EXISTS mesures CASCADE;
DROP TABLE IF EXISTS trajets CASCADE;
DROP TABLE IF EXISTS vehicules CASCADE;
DROP TABLE IF EXISTS participation_consultations CASCADE;
DROP TABLE IF EXISTS consultations CASCADE;
DROP TABLE IF EXISTS citoyens CASCADE;
DROP TABLE IF EXISTS intervention_techniciens CASCADE;
DROP TABLE IF EXISTS interventions CASCADE;
DROP TABLE IF EXISTS techniciens CASCADE;
DROP TABLE IF EXISTS capteurs CASCADE;
DROP TABLE IF EXISTS proprietaires CASCADE;
DROP TABLE IF EXISTS zones CASCADE;

-- ============================================================
-- 1. ZONES (arrondissements de Neo-Sousse)
-- ============================================================
CREATE TABLE zones (
    zone_id     SERIAL PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL,
    superficie  NUMERIC(10,2),         -- km²
    population  INTEGER,
    latitude    NUMERIC(9,6),
    longitude   NUMERIC(9,6)
);

-- ============================================================
-- 2. PROPRIETAIRES (municipalité ou partenaire privé)
-- ============================================================
CREATE TABLE proprietaires (
    proprietaire_id SERIAL PRIMARY KEY,
    type_proprietaire VARCHAR(20) NOT NULL CHECK (type_proprietaire IN ('municipalite','prive')),
    nom             VARCHAR(150) NOT NULL,
    adresse         TEXT,
    telephone       VARCHAR(20),
    email           VARCHAR(100)
);

-- ============================================================
-- 3. CAPTEURS
-- ============================================================
CREATE TABLE capteurs (
    capteur_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_capteur    VARCHAR(20) UNIQUE NOT NULL,  -- ex: C-452
    type_capteur    VARCHAR(30) NOT NULL CHECK (type_capteur IN ('qualite_air','trafic','energie','dechets','eclairage')),
    zone_id         INTEGER REFERENCES zones(zone_id),
    proprietaire_id INTEGER REFERENCES proprietaires(proprietaire_id),
    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6),
    statut          VARCHAR(20) NOT NULL DEFAULT 'inactif'
                    CHECK (statut IN ('inactif','actif','signale','en_maintenance','hors_service')),
    date_installation DATE NOT NULL,
    modele          VARCHAR(100),
    firmware_version VARCHAR(20),
    taux_erreur     NUMERIC(5,2) DEFAULT 0.0,     -- %
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 4. MESURES (time-series data from sensors)
-- ============================================================
CREATE TABLE mesures (
    mesure_id       BIGSERIAL PRIMARY KEY,
    capteur_id      UUID REFERENCES capteurs(capteur_id) ON DELETE CASCADE,
    timestamp_mesure TIMESTAMP NOT NULL DEFAULT NOW(),
    valeur          NUMERIC(12,4) NOT NULL,
    unite           VARCHAR(20),                  -- µg/m³, km/h, kWh, …
    qualite_signal  NUMERIC(5,2),                 -- 0-100%
    anomalie        BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_mesures_capteur_time ON mesures(capteur_id, timestamp_mesure DESC);
CREATE INDEX idx_mesures_time ON mesures(timestamp_mesure DESC);

-- ============================================================
-- 5. TECHNICIENS
-- ============================================================
CREATE TABLE techniciens (
    technicien_id   SERIAL PRIMARY KEY,
    matricule       VARCHAR(20) UNIQUE NOT NULL,
    nom             VARCHAR(100) NOT NULL,
    prenom          VARCHAR(100) NOT NULL,
    specialite      VARCHAR(50),
    certification   VARCHAR(100),
    telephone       VARCHAR(20),
    email           VARCHAR(100),
    disponible      BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- 6. INTERVENTIONS
-- ============================================================
CREATE TABLE interventions (
    intervention_id SERIAL PRIMARY KEY,
    capteur_id      UUID REFERENCES capteurs(capteur_id),
    date_debut      TIMESTAMP NOT NULL,
    date_fin        TIMESTAMP,
    nature          VARCHAR(20) NOT NULL CHECK (nature IN ('predictive','corrective','curative')),
    statut          VARCHAR(30) NOT NULL DEFAULT 'demande'
                    CHECK (statut IN ('demande','tech1_assigne','tech2_valide','ia_valide','termine')),
    description     TEXT,
    cout            NUMERIC(10,2),
    duree_heures    NUMERIC(6,2),
    impact_co2      NUMERIC(10,4),               -- kg CO₂ évités
    ia_validation_score NUMERIC(5,2),            -- 0-100
    ia_commentaire  TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 7. INTERVENTION ↔ TECHNICIENS (many-to-many)
-- ============================================================
CREATE TABLE intervention_techniciens (
    intervention_id INTEGER REFERENCES interventions(intervention_id) ON DELETE CASCADE,
    technicien_id   INTEGER REFERENCES techniciens(technicien_id),
    role            VARCHAR(20) NOT NULL CHECK (role IN ('intervenant','validateur')),
    date_assignation TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (intervention_id, technicien_id)
);

-- ============================================================
-- 8. CITOYENS
-- ============================================================
CREATE TABLE citoyens (
    citoyen_id      SERIAL PRIMARY KEY,
    identifiant     UUID UNIQUE DEFAULT gen_random_uuid(),
    nom             VARCHAR(100) NOT NULL,
    prenom          VARCHAR(100) NOT NULL,
    adresse         TEXT,
    telephone       VARCHAR(20),
    email           VARCHAR(100) UNIQUE,
    score_ecolo     NUMERIC(5,2) DEFAULT 0 CHECK (score_ecolo BETWEEN 0 AND 100),
    preference_mobilite VARCHAR(50),             -- velo, transport_commun, marche…
    zone_id         INTEGER REFERENCES zones(zone_id),
    date_inscription DATE DEFAULT CURRENT_DATE
);

-- ============================================================
-- 9. CONSULTATIONS CITOYENNES
-- ============================================================
CREATE TABLE consultations (
    consultation_id SERIAL PRIMARY KEY,
    titre           VARCHAR(200) NOT NULL,
    date_debut      DATE NOT NULL,
    date_fin        DATE,
    sujet           VARCHAR(100),
    zone_id         INTEGER REFERENCES zones(zone_id)
);

CREATE TABLE participation_consultations (
    participation_id SERIAL PRIMARY KEY,
    citoyen_id      INTEGER REFERENCES citoyens(citoyen_id),
    consultation_id INTEGER REFERENCES consultations(consultation_id),
    date_participation TIMESTAMP DEFAULT NOW(),
    avis            TEXT,
    UNIQUE(citoyen_id, consultation_id)
);

-- ============================================================
-- 10. VEHICULES AUTONOMES MUNICIPAUX
-- ============================================================
CREATE TABLE vehicules (
    vehicule_id     SERIAL PRIMARY KEY,
    immatriculation VARCHAR(20) UNIQUE NOT NULL,
    type_vehicule   VARCHAR(50),                 -- bus, camion_dechets, voiture_inspection
    energie         VARCHAR(30) CHECK (energie IN ('electrique','hybride','hydrogene')),
    statut          VARCHAR(20) DEFAULT 'stationne'
                    CHECK (statut IN ('stationne','en_route','en_panne','arrive')),
    capacite        INTEGER,
    zone_base_id    INTEGER REFERENCES zones(zone_id)
);

-- ============================================================
-- 11. TRAJETS
-- ============================================================
CREATE TABLE trajets (
    trajet_id       SERIAL PRIMARY KEY,
    vehicule_id     INTEGER REFERENCES vehicules(vehicule_id),
    origine         VARCHAR(150),
    destination     VARCHAR(150),
    date_depart     TIMESTAMP NOT NULL,
    date_arrivee    TIMESTAMP,
    duree_minutes   INTEGER,
    distance_km     NUMERIC(8,2),
    economie_co2    NUMERIC(8,4),               -- kg CO₂ économisés vs voiture thermique
    energie_consommee NUMERIC(8,4),             -- kWh
    statut_trajet   VARCHAR(20) DEFAULT 'planifie'
                    CHECK (statut_trajet IN ('planifie','en_cours','termine','annule'))
);

-- ============================================================
-- VIEWS (for business questions)
-- ============================================================

-- Zones les plus polluées (dernières 24h)
CREATE OR REPLACE VIEW v_zones_polluees AS
SELECT
    z.nom AS zone,
    AVG(m.valeur) AS pollution_moyenne,
    COUNT(m.mesure_id) AS nb_mesures,
    MAX(m.timestamp_mesure) AS derniere_mesure
FROM mesures m
JOIN capteurs c ON m.capteur_id = c.capteur_id
JOIN zones z ON c.zone_id = z.zone_id
WHERE c.type_capteur = 'qualite_air'
  AND m.timestamp_mesure >= NOW() - INTERVAL '24 hours'
GROUP BY z.zone_id, z.nom
ORDER BY pollution_moyenne DESC;

-- Taux de disponibilité capteurs par zone
CREATE OR REPLACE VIEW v_disponibilite_capteurs AS
SELECT
    z.nom AS zone,
    COUNT(*) AS total_capteurs,
    SUM(CASE WHEN c.statut = 'actif' THEN 1 ELSE 0 END) AS capteurs_actifs,
    ROUND(100.0 * SUM(CASE WHEN c.statut = 'actif' THEN 1 ELSE 0 END) / COUNT(*), 2) AS taux_disponibilite
FROM capteurs c
JOIN zones z ON c.zone_id = z.zone_id
GROUP BY z.zone_id, z.nom
ORDER BY taux_disponibilite DESC;

-- Citoyens les plus engagés
CREATE OR REPLACE VIEW v_citoyens_engages AS
SELECT
    c.nom, c.prenom, c.score_ecolo,
    COUNT(p.participation_id) AS nb_consultations,
    c.preference_mobilite
FROM citoyens c
LEFT JOIN participation_consultations p ON c.citoyen_id = p.citoyen_id
GROUP BY c.citoyen_id, c.nom, c.prenom, c.score_ecolo, c.preference_mobilite
ORDER BY c.score_ecolo DESC;

-- Trajets avec plus grande réduction CO₂
CREATE OR REPLACE VIEW v_trajets_eco AS
SELECT
    t.trajet_id, v.immatriculation, v.type_vehicule,
    t.origine, t.destination,
    t.economie_co2, t.distance_km, t.duree_minutes
FROM trajets t
JOIN vehicules v ON t.vehicule_id = v.vehicule_id
WHERE t.statut_trajet = 'termine'
ORDER BY t.economie_co2 DESC;

-- Statistiques interventions du mois
CREATE OR REPLACE VIEW v_interventions_mois AS
SELECT
    nature,
    COUNT(*) AS nb_interventions,
    SUM(cout) AS cout_total,
    SUM(impact_co2) AS co2_evite_total,
    AVG(duree_heures) AS duree_moyenne
FROM interventions
WHERE DATE_TRUNC('month', date_debut) = DATE_TRUNC('month', NOW())
GROUP BY nature;
