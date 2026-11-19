"""
seed_data.py — Generate realistic seed data for Neo-Sousse 2030
Run: python database/seed_data.py
"""
import random
import uuid
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values
import os

# ─── Config ───────────────────────────────────────────────────
DB_CONFIG = {
    "dbname":   os.getenv("DB_NAME", "smart_city"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "postgres"),
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
}

random.seed(42)

# ─── Helpers ──────────────────────────────────────────────────
def rand_date(start_days_ago=730, end_days_ago=0):
    offset = random.randint(end_days_ago, start_days_ago)
    return datetime.now() - timedelta(days=offset)

def rand_ts(start_hours_ago=720, end_hours_ago=0):
    offset = random.randint(end_hours_ago * 60, start_hours_ago * 60)
    return datetime.now() - timedelta(minutes=offset)

# ─── Data pools ───────────────────────────────────────────────
ZONE_DATA = [
    ("Médina Nord",      12.5, 45000, 35.8288, 10.6350),
    ("Corniche Ouest",   8.3,  32000, 35.8200, 10.6200),
    ("Zone Industrielle",22.1, 15000, 35.7900, 10.6500),
    ("Quartier Vert",    15.7, 67000, 35.8400, 10.6450),
    ("Centre Technopole",9.4,  28000, 35.8350, 10.6300),
    ("Port Sousse",      5.2,  11000, 35.8100, 10.6150),
    ("Cité Universitaire",6.8, 22000, 35.8500, 10.6400),
]

SENSOR_TYPES = ["qualite_air", "trafic", "energie", "dechets", "eclairage"]
SENSOR_STATUSES = ["actif", "actif", "actif", "actif", "signale", "en_maintenance", "hors_service", "inactif"]

FIRST_NAMES = ["Ahmed","Sami","Youssef","Mohamed","Ines","Fatma","Amel","Nadia","Omar","Khalil",
               "Rania","Leila","Karim","Houda","Tarek","Sirine","Malek","Dorra","Bilel","Wafa"]
LAST_NAMES  = ["Ben Ali","Trabelsi","Chahed","Bouazizi","Mansouri","Khedher","Sfar","Jebali",
               "Hamdi","Belhaj","Znaidia","Meddeb","Lahbib","Oueslati","Ghannouchi"]

MOBILITIES = ["velo","transport_commun","marche","covoiturage","teletravail"]
VEHICLE_TYPES = ["bus_electrique","camion_dechets","voiture_inspection","navette_port"]
ENERGIES = ["electrique","hybride","hydrogene"]
INTERVENTION_NATURES = ["predictive","corrective","curative"]

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("🏙️  Seeding Neo-Sousse 2030 database...")

    # ── Zones ────────────────────────────────────────────────
    zone_ids = []
    for (nom, sup, pop, lat, lon) in ZONE_DATA:
        cur.execute("""
            INSERT INTO zones (nom, superficie, population, latitude, longitude)
            VALUES (%s,%s,%s,%s,%s) RETURNING zone_id
        """, (nom, sup, pop, lat, lon))
        zone_ids.append(cur.fetchone()[0])
    print(f"  ✓ {len(zone_ids)} zones")

    # ── Propriétaires ────────────────────────────────────────
    prop_data = [
        ("municipalite","Municipalité de Sousse","Av. Bourguiba, Sousse","73 210 000","mairie@sousse.tn"),
        ("prive","TechSens Tunisie","Rue du Lac, Tunis","71 900 100","contact@techsens.tn"),
        ("prive","EcoMonitor SARL","Zone Industrielle Sousse","73 450 200","info@ecomonitor.tn"),
        ("municipalite","Agence Urbaine Sousse","Bd de la République","73 210 050","agence@sousse.tn"),
    ]
    prop_ids = []
    for row in prop_data:
        cur.execute("""
            INSERT INTO proprietaires (type_proprietaire,nom,adresse,telephone,email)
            VALUES (%s,%s,%s,%s,%s) RETURNING proprietaire_id
        """, row)
        prop_ids.append(cur.fetchone()[0])
    print(f"  ✓ {len(prop_ids)} propriétaires")

    # ── Capteurs (200) ───────────────────────────────────────
    capteur_ids = []
    sensor_rows = []
    for i in range(200):
        ctype = random.choice(SENSOR_TYPES)
        zone  = random.choice(zone_ids)
        prop  = random.choice(prop_ids)
        statut = random.choice(SENSOR_STATUSES)
        code  = f"C-{1000+i}"
        lat   = 35.82 + random.uniform(-0.05, 0.05)
        lon   = 10.63 + random.uniform(-0.05, 0.05)
        inst  = rand_date(730, 30).date()
        taux_erreur = round(random.uniform(0, 20), 2) if statut != "actif" else round(random.uniform(0, 5), 2)
        cid   = str(uuid.uuid4())
        capteur_ids.append(cid)
        sensor_rows.append((cid, code, ctype, zone, prop, lat, lon, statut, inst, f"Model-{random.randint(1,5)}", "v2.1", taux_erreur))

    execute_values(cur, """
        INSERT INTO capteurs (capteur_id,code_capteur,type_capteur,zone_id,proprietaire_id,
            latitude,longitude,statut,date_installation,modele,firmware_version,taux_erreur)
        VALUES %s
    """, sensor_rows)
    print(f"  ✓ {len(capteur_ids)} capteurs")

    # ── Mesures (1500+) ──────────────────────────────────────
    mesure_rows = []
    for _ in range(1500):
        cid   = random.choice(capteur_ids)
        ts    = rand_ts(720)
        # realistic value ranges per type
        type_map = {
            "qualite_air": (5, 250),    # µg/m³ PM2.5
            "trafic":      (0, 120),    # vehicles/min
            "energie":     (0.5, 50),   # kWh
            "dechets":     (0, 100),    # % fill
            "eclairage":   (0, 1),      # 0=off 1=on
        }
        # find type for this capteur_id
        idx = capteur_ids.index(cid)
        ctype = sensor_rows[idx][2]
        lo, hi = type_map[ctype]
        val = round(random.uniform(lo, hi), 4)
        unite_map = {"qualite_air":"µg/m³","trafic":"veh/min","energie":"kWh","dechets":"%","eclairage":"bool"}
        unite = unite_map[ctype]
        sig   = round(random.uniform(60, 100), 2)
        anom  = val > hi * 0.85
        mesure_rows.append((cid, ts, val, unite, sig, anom))

    execute_values(cur, """
        INSERT INTO mesures (capteur_id,timestamp_mesure,valeur,unite,qualite_signal,anomalie)
        VALUES %s
    """, mesure_rows)
    print(f"  ✓ {len(mesure_rows)} mesures")

    # ── Techniciens (20) ────────────────────────────────────
    tech_ids = []
    specs = ["Electronique","Réseaux","Mécatronique","Informatique","Energétique"]
    for i in range(20):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        cur.execute("""
            INSERT INTO techniciens (matricule,nom,prenom,specialite,certification,telephone,email,disponible)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING technicien_id
        """, (f"T-{100+i}", ln, fn, random.choice(specs),
              f"CERT-{random.randint(1000,9999)}", f"2X XXX {1000+i}",
              f"{fn.lower()}.{ln.lower()}@sousse-city.tn", random.random() > 0.2))
        tech_ids.append(cur.fetchone()[0])
    print(f"  ✓ {len(tech_ids)} techniciens")

    # ── Interventions (80) ───────────────────────────────────
    interv_ids = []
    statuts_interv = ["demande","tech1_assigne","tech2_valide","ia_valide","termine"]
    for _ in range(80):
        cid    = random.choice(capteur_ids)
        nature = random.choice(INTERVENTION_NATURES)
        statut = random.choice(statuts_interv)
        dd     = rand_ts(2160)  # last 90 days
        df     = dd + timedelta(hours=random.uniform(1, 48)) if statut == "termine" else None
        duree  = round((df - dd).total_seconds() / 3600, 2) if df else None
        cout   = round(random.uniform(200, 5000), 2)
        co2    = round(random.uniform(0, 50), 4)
        ia_score = round(random.uniform(60, 100), 2) if statut in ("ia_valide","termine") else None
        ia_comm  = f"Validation IA: score {ia_score}/100 — intervention {'recommandée' if ia_score and ia_score>75 else 'à surveiller'}" if ia_score else None

        cur.execute("""
            INSERT INTO interventions (capteur_id,date_debut,date_fin,nature,statut,
                description,cout,duree_heures,impact_co2,ia_validation_score,ia_commentaire)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING intervention_id
        """, (cid, dd, df, nature, statut, f"Intervention {nature} sur capteur", cout, duree, co2, ia_score, ia_comm))
        interv_ids.append(cur.fetchone()[0])

    # assign 2 techniciens to each intervention
    for iid in interv_ids:
        techs = random.sample(tech_ids, 2)
        cur.execute("""
            INSERT INTO intervention_techniciens (intervention_id,technicien_id,role)
            VALUES (%s,%s,'intervenant'),(%s,%s,'validateur')
        """, (iid, techs[0], iid, techs[1]))
    print(f"  ✓ {len(interv_ids)} interventions")

    # ── Citoyens (300) ───────────────────────────────────────
    citoyen_ids = []
    for i in range(300):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        cur.execute("""
            INSERT INTO citoyens (nom,prenom,adresse,telephone,email,score_ecolo,
                preference_mobilite,zone_id,date_inscription)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING citoyen_id
        """, (ln, fn, f"{random.randint(1,99)} Rue {random.choice(['de la Paix','du Lac','Verte'])}",
              f"+216 XX XXX {1000+i}", f"{fn.lower()}{i}@mail.tn",
              round(random.uniform(10, 100), 2),
              random.choice(MOBILITIES), random.choice(zone_ids),
              rand_date(365).date()))
        citoyen_ids.append(cur.fetchone()[0])
    print(f"  ✓ {len(citoyen_ids)} citoyens")

    # ── Consultations (10) ───────────────────────────────────
    consult_ids = []
    sujets = ["Mobilité","Qualité de l'air","Déchets","Éclairage","Transports","Énergie"]
    for i in range(10):
        dd = rand_date(180, 10).date()
        cur.execute("""
            INSERT INTO consultations (titre,date_debut,date_fin,sujet,zone_id)
            VALUES (%s,%s,%s,%s,%s) RETURNING consultation_id
        """, (f"Consultation citoyenne — {sujets[i%len(sujets)]} #{i+1}",
              dd, dd + timedelta(days=14), sujets[i%len(sujets)], random.choice(zone_ids)))
        consult_ids.append(cur.fetchone()[0])

    # participations
    part_rows = set()
    for _ in range(400):
        cid = random.choice(citoyen_ids)
        coid = random.choice(consult_ids)
        if (cid, coid) not in part_rows:
            part_rows.add((cid, coid))
    execute_values(cur, """
        INSERT INTO participation_consultations (citoyen_id,consultation_id,date_participation)
        VALUES %s
    """, [(c, co, rand_ts(180)) for c, co in part_rows])
    print(f"  ✓ {len(consult_ids)} consultations, {len(part_rows)} participations")

    # ── Véhicules (15) ───────────────────────────────────────
    veh_ids = []
    veh_statuts = ["stationne","en_route","en_route","arrive","en_panne"]
    for i in range(15):
        cur.execute("""
            INSERT INTO vehicules (immatriculation,type_vehicule,energie,statut,capacite,zone_base_id)
            VALUES (%s,%s,%s,%s,%s,%s) RETURNING vehicule_id
        """, (f"TUN-{2030+i}", random.choice(VEHICLE_TYPES),
              random.choice(ENERGIES), random.choice(veh_statuts),
              random.randint(4, 80), random.choice(zone_ids)))
        veh_ids.append(cur.fetchone()[0])
    print(f"  ✓ {len(veh_ids)} véhicules")

    # ── Trajets (200) ────────────────────────────────────────
    trajet_rows = []
    zone_noms = [z[0] for z in ZONE_DATA]
    for _ in range(200):
        vid  = random.choice(veh_ids)
        orig = random.choice(zone_noms)
        dest = random.choice([z for z in zone_noms if z != orig])
        dd   = rand_ts(720)
        dur  = random.randint(10, 120)
        da   = dd + timedelta(minutes=dur)
        dist = round(random.uniform(0.5, 20), 2)
        eco  = round(dist * random.uniform(0.1, 0.25), 4)
        nrj  = round(dist * random.uniform(0.15, 0.3), 4)
        trajet_rows.append((vid, orig, dest, dd, da, dur, dist, eco, nrj, "termine"))

    execute_values(cur, """
        INSERT INTO trajets (vehicule_id,origine,destination,date_depart,date_arrivee,
            duree_minutes,distance_km,economie_co2,energie_consommee,statut_trajet)
        VALUES %s
    """, trajet_rows)
    print(f"  ✓ {len(trajet_rows)} trajets")

    conn.commit()
    cur.close()
    conn.close()
    print("\n✅ Database seeded successfully!")
    print(f"   Total records: ~{200+1500+20+80+300+10+400+15+200}")

if __name__ == "__main__":
    main()
