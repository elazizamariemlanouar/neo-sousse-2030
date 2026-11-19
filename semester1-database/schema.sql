-- Table propriétaires
CREATE TABLE proprietaire (
    id_proprietaire SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    adresse VARCHAR(200),
    telephone VARCHAR(20),
    email VARCHAR(100)
);

-- Table capteurs
CREATE TABLE capteur (
    id_capteur SERIAL PRIMARY KEY,
    type_capteur VARCHAR(50),
    latitude NUMERIC(10,7),
    longitude NUMERIC(10,7),
    statut VARCHAR(20),
    id_proprietaire INT REFERENCES proprietaire(id_proprietaire),
    date_installation DATE
);

-- Table mesures
CREATE TABLE mesure (
    id_mesure SERIAL PRIMARY KEY,
    id_capteur INT REFERENCES capteur(id_capteur),
    date_mesure TIMESTAMP,
    type_mesure VARCHAR(50),
    valeur NUMERIC(10,2)
);

-- Table techniciens
CREATE TABLE technicien (
    id_technicien SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    email VARCHAR(100),
    certification VARCHAR(50)
);

-- Table interventions
CREATE TABLE intervention (
    id_intervention SERIAL PRIMARY KEY,
    id_capteur INT REFERENCES capteur(id_capteur),
    date_intervention TIMESTAMP,
    type_intervention VARCHAR(50),
    duree INT, -- minutes
    cout NUMERIC(10,2),
    economie_co2 NUMERIC(10,2)
);

-- Table n-n interventions-techniciens
CREATE TABLE intervention_technicien (
    id_intervention INT REFERENCES intervention(id_intervention),
    id_technicien INT REFERENCES technicien(id_technicien),
    role VARCHAR(20), -- 'intervenant' ou 'validateur'
    PRIMARY KEY (id_intervention, id_technicien)
);

-- Table citoyens
CREATE TABLE citoyen (
    id_citoyen SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    adresse VARCHAR(200),
    email VARCHAR(100),
    score_ecologique NUMERIC(5,2),
    preference_mobilite VARCHAR(50)
);

-- Table véhicules
CREATE TABLE vehicule (
    id_vehicule SERIAL PRIMARY KEY,
    plaque VARCHAR(20),
    type_vehicule VARCHAR(50),
    energie VARCHAR(50)
);

-- Table trajets
CREATE TABLE trajet (
    id_trajet SERIAL PRIMARY KEY,
    id_vehicule INT REFERENCES vehicule(id_vehicule),
    origine VARCHAR(100),
    destination VARCHAR(100),
    date_trajet TIMESTAMP,
    economie_co2 NUMERIC(10,2)
);
