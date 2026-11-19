"""
backend/database.py
Database connection and data access layer for Smart City Neo-Sousse 2030.
Uses psycopg2 directly for simplicity (no ORM overhead).
"""

import os
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

# ─── Config ───────────────────────────────────────────────────
DB_CONFIG = {
    "dbname":   os.getenv("DB_NAME", "smart_city"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "postgres"),
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
}

def get_conn():
    """Get a fresh DB connection."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)

def execute_query(sql: str, params=None) -> List[Dict]:
    """Execute a SQL query and return rows as list of dicts."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description:
                    return [dict(r) for r in cur.fetchall()]
                return []
    except psycopg2.Error as e:
        raise RuntimeError(f"DB error: {e}")

def execute_write(sql: str, params=None) -> Optional[Any]:
    """Execute INSERT/UPDATE/DELETE. Returns lastrowid if available."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                conn.commit()
                try:
                    return cur.fetchone()
                except Exception:
                    return None
    except psycopg2.Error as e:
        raise RuntimeError(f"DB write error: {e}")


# ══════════════════════════════════════════════════════════════
# DATA ACCESS FUNCTIONS
# ══════════════════════════════════════════════════════════════

# ── Dashboard KPIs ───────────────────────────────────────────
def get_dashboard_kpis() -> dict:
    """Main KPI summary for the dashboard."""
    rows = execute_query("""
        SELECT
            COUNT(*) FILTER (WHERE statut = 'actif')          AS capteurs_actifs,
            COUNT(*) FILTER (WHERE statut = 'hors_service')   AS capteurs_hors_service,
            COUNT(*) FILTER (WHERE statut = 'signale')        AS capteurs_signales,
            COUNT(*) FILTER (WHERE statut = 'en_maintenance') AS capteurs_maintenance,
            COUNT(*)                                           AS total_capteurs
        FROM capteurs
    """)
    sensor_kpis = rows[0] if rows else {}

    rows2 = execute_query("""
        SELECT
            COUNT(*) FILTER (WHERE statut != 'termine' AND date_debut >= NOW() - INTERVAL '24h') AS interventions_actives,
            COUNT(*) FILTER (WHERE date_debut >= NOW() - INTERVAL '30d')                         AS interventions_mois,
            ROUND(COALESCE(SUM(impact_co2) FILTER (WHERE date_debut >= NOW() - INTERVAL '30d'), 0)::numeric, 2) AS co2_evite_mois
        FROM interventions
    """)
    interv_kpis = rows2[0] if rows2 else {}

    rows3 = execute_query("""
        SELECT ROUND(AVG(valeur)::numeric, 2) AS qualite_air_avg
        FROM mesures
        WHERE timestamp_mesure >= NOW() - INTERVAL '24h'
    """)
    air_kpi = rows3[0] if rows3 else {}

    rows4 = execute_query("SELECT COUNT(*) AS total FROM citoyens WHERE score_ecolo > 70")
    citoyen_kpi = rows4[0] if rows4 else {}

    rows5 = execute_query("""
        SELECT
            COUNT(*) FILTER (WHERE statut = 'en_route') AS en_route,
            COUNT(*) AS total
        FROM vehicules
    """)
    veh_kpi = rows5[0] if rows5 else {}

    return {**sensor_kpis, **interv_kpis, **air_kpi, **citoyen_kpi, **veh_kpi}


# ── Sensors ──────────────────────────────────────────────────
def get_capteurs(limit: int = 100, statut: str = None) -> List[Dict]:
    base = """
        SELECT c.capteur_id, c.code_capteur, c.type_capteur,
               c.statut, c.taux_erreur, c.date_installation,
               z.nom AS zone_nom,
               p.nom AS proprietaire,
               c.latitude, c.longitude
        FROM capteurs c
        LEFT JOIN zones z ON c.zone_id = z.zone_id
        LEFT JOIN proprietaires p ON c.proprietaire_id = p.proprietaire_id
    """
    if statut:
        return execute_query(base + " WHERE c.statut = %s LIMIT %s", (statut, limit))
    return execute_query(base + " ORDER BY c.taux_erreur DESC LIMIT %s", (limit,))


def update_capteur_statut(capteur_id: str, new_statut: str):
    execute_write(
        "UPDATE capteurs SET statut = %s, updated_at = NOW() WHERE capteur_id = %s::uuid",
        (new_statut, capteur_id)
    )


# ── Measures ─────────────────────────────────────────────────
def get_mesures_recent(hours: int = 24, limit: int = 500) -> List[Dict]:
    return execute_query("""
        SELECT m.mesure_id, m.timestamp_mesure, m.valeur, m.unite,
               m.anomalie, c.code_capteur, c.type_capteur,
               z.nom AS zone_nom
        FROM mesures m
        JOIN capteurs c ON m.capteur_id = c.capteur_id
        LEFT JOIN zones z ON c.zone_id = z.zone_id
        WHERE m.timestamp_mesure >= NOW() - INTERVAL '%s hours'
        ORDER BY m.timestamp_mesure DESC
        LIMIT %s
    """, (hours, limit))


def get_zone_pollution_stats() -> List[Dict]:
    return execute_query("""
        SELECT z.nom AS zone,
               ROUND(AVG(m.valeur)::numeric, 2) AS avg_pollution,
               ROUND(MAX(m.valeur)::numeric, 2) AS max_pollution,
               COUNT(m.mesure_id) AS nb_mesures,
               SUM(CASE WHEN m.anomalie THEN 1 ELSE 0 END) AS nb_anomalies
        FROM mesures m
        JOIN capteurs c ON m.capteur_id = c.capteur_id
        JOIN zones z ON c.zone_id = z.zone_id
        WHERE c.type_capteur = 'qualite_air'
          AND m.timestamp_mesure >= NOW() - INTERVAL '24 hours'
        GROUP BY z.zone_id, z.nom
        ORDER BY avg_pollution DESC
    """)


def get_time_series(capteur_code: str, hours: int = 48) -> List[Dict]:
    return execute_query("""
        SELECT m.timestamp_mesure AS ts, m.valeur, m.anomalie
        FROM mesures m
        JOIN capteurs c ON m.capteur_id = c.capteur_id
        WHERE c.code_capteur = %s
          AND m.timestamp_mesure >= NOW() - INTERVAL '%s hours'
        ORDER BY m.timestamp_mesure
    """, (capteur_code, hours))


# ── Interventions ────────────────────────────────────────────
def get_interventions(statut: str = None, limit: int = 50) -> List[Dict]:
    sql = """
        SELECT i.intervention_id, i.nature, i.statut,
               i.date_debut, i.date_fin, i.cout,
               i.duree_heures, i.impact_co2,
               i.ia_validation_score, i.ia_commentaire,
               c.code_capteur, z.nom AS zone_nom
        FROM interventions i
        JOIN capteurs c ON i.capteur_id = c.capteur_id
        LEFT JOIN zones z ON c.zone_id = z.zone_id
    """
    if statut:
        return execute_query(sql + " WHERE i.statut = %s ORDER BY i.date_debut DESC LIMIT %s",
                             (statut, limit))
    return execute_query(sql + " ORDER BY i.date_debut DESC LIMIT %s", (limit,))


def update_intervention_statut(interv_id: int, new_statut: str,
                                ia_score: float = None, ia_comment: str = None):
    if ia_score is not None:
        execute_write("""
            UPDATE interventions
            SET statut = %s, ia_validation_score = %s, ia_commentaire = %s
            WHERE intervention_id = %s
        """, (new_statut, ia_score, ia_comment, interv_id))
    else:
        execute_write(
            "UPDATE interventions SET statut = %s WHERE intervention_id = %s",
            (new_statut, interv_id)
        )


# ── Citoyens ─────────────────────────────────────────────────
def get_citoyens(min_score: float = 0, limit: int = 50) -> List[Dict]:
    return execute_query("""
        SELECT c.citoyen_id, c.nom, c.prenom, c.score_ecolo,
               c.preference_mobilite, z.nom AS zone_nom,
               COUNT(p.participation_id) AS nb_consultations
        FROM citoyens c
        LEFT JOIN zones z ON c.zone_id = z.zone_id
        LEFT JOIN participation_consultations p ON c.citoyen_id = p.citoyen_id
        WHERE c.score_ecolo >= %s
        GROUP BY c.citoyen_id, c.nom, c.prenom, c.score_ecolo,
                 c.preference_mobilite, z.nom
        ORDER BY c.score_ecolo DESC
        LIMIT %s
    """, (min_score, limit))


# ── Vehicles ─────────────────────────────────────────────────
def get_vehicules() -> List[Dict]:
    return execute_query("""
        SELECT v.vehicule_id, v.immatriculation, v.type_vehicule,
               v.energie, v.statut, z.nom AS zone_base
        FROM vehicules v
        LEFT JOIN zones z ON v.zone_base_id = z.zone_id
        ORDER BY v.statut, v.immatriculation
    """)


def get_trajets(limit: int = 50) -> List[Dict]:
    return execute_query("""
        SELECT t.trajet_id, t.origine, t.destination,
               t.distance_km, t.duree_minutes,
               t.economie_co2, t.energie_consommee,
               t.statut_trajet, t.date_depart,
               v.immatriculation, v.type_vehicule
        FROM trajets t
        JOIN vehicules v ON t.vehicule_id = v.vehicule_id
        ORDER BY t.economie_co2 DESC
        LIMIT %s
    """, (limit,))


# ── Live data refresh (called every 2 min by scheduler) ──────
def simulate_live_updates():
    """
    Simulate real-time sensor readings — called every 2 minutes.
    Inserts new mesures and randomly updates sensor statuses.
    """
    capteurs = execute_query("""
        SELECT capteur_id, type_capteur FROM capteurs
        WHERE statut = 'actif'
        ORDER BY RANDOM() LIMIT 30
    """)

    type_ranges = {
        "qualite_air": (5, 250),
        "trafic":      (0, 120),
        "energie":     (0.5, 50),
        "dechets":     (0, 100),
        "eclairage":   (0, 1),
    }
    unite_map = {
        "qualite_air":"µg/m³","trafic":"veh/min",
        "energie":"kWh","dechets":"%","eclairage":"bool"
    }

    rows = []
    for cap in capteurs:
        lo, hi = type_ranges.get(cap["type_capteur"], (0, 100))
        val = round(random.uniform(lo, hi), 4)
        anom = val > hi * 0.85
        rows.append((
            cap["capteur_id"],
            datetime.now(),
            val,
            unite_map.get(cap["type_capteur"], "unit"),
            round(random.uniform(70, 100), 2),
            anom
        ))

    if rows:
        with get_conn() as conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(cur, """
                    INSERT INTO mesures
                    (capteur_id, timestamp_mesure, valeur, unite, qualite_signal, anomalie)
                    VALUES %s
                """, rows)
                conn.commit()

    return len(rows)
