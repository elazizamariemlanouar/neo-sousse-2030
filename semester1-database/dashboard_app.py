# app.py
# Neo Sousse 2030 – Smart City Analytics Dashboard (Fully Organized – IA Version)

import os
import streamlit as st
import psycopg2
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from folium.plugins import HeatMap

# ============================
# Database utility
# ============================

def get_data(query):
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "smart_city"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# ============================
# Page config
# ============================

st.set_page_config(
    page_title="Neo Sousse 2030",
    page_icon="🌱",
    layout="wide"
)

# ============================
# Sidebar
# ============================

st.sidebar.title("Neo Sousse 2030")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard Overview",
        "Air Quality Monitoring",
        "Smart Sensors Management",
        "Predictive Maintenance",
        "Citizen Engagement",
        "Autonomous Vehicles"
    ]
)

time_filter = st.sidebar.selectbox(
    "Time Range",
    ["Last 24 hours", "Last 7 days", "Last 30 days"]
)

interval = {
    "Last 24 hours": "24 hours",
    "Last 7 days": "7 days",
    "Last 30 days": "30 days"
}[time_filter]

# ============================
# DASHBOARD OVERVIEW
# ============================

if page == "Dashboard Overview":

    st.title("📊 City Performance Overview")
    st.caption("Global indicators summarizing urban services performance and sustainability.")

    # KPIs
    c1, c2, c3, c4 = st.columns(4)

    aqi = get_data(f"""
        SELECT ROUND(AVG(valeur)) FROM mesure
        WHERE type_mesure='AQI'
        AND date_mesure >= NOW() - INTERVAL '{interval}'
    """)

    active = get_data("""
        SELECT ROUND(100.0 *
        SUM(CASE WHEN statut='active' THEN 1 ELSE 0 END)/COUNT(*),1)
        FROM capteur
    """)

    co2 = get_data(f"""
        SELECT ROUND(SUM(economie_co2)) FROM intervention
        WHERE date_intervention >= NOW() - INTERVAL '{interval}'
    """)

    predictive = get_data(f"""
        SELECT COUNT(*) FROM intervention
        WHERE type_intervention='predictive'
        AND date_intervention >= NOW() - INTERVAL '{interval}'
    """)

    c1.metric("Average AQI", aqi.iloc[0,0])
    c2.metric("Active Sensors (%)", active.iloc[0,0])
    c3.metric("CO₂ Reduction (kg)", co2.iloc[0,0])
    c4.metric("Predictive Interventions", predictive.iloc[0,0])

    st.divider()

    st.subheader("🌍 Pollution Spatial Distribution")
    st.caption("Heatmap showing air quality concentration based on AQI sensors.")

    df_map = get_data(f"""
        SELECT c.latitude, c.longitude, m.valeur
        FROM mesure m
        JOIN capteur c ON m.id_capteur = c.id_capteur
        WHERE m.type_mesure='AQI'
        AND m.date_mesure >= NOW() - INTERVAL '{interval}'
    """)

    m = folium.Map(location=[35.8256, 10.6369], zoom_start=13, tiles="cartodbpositron")
    HeatMap(df_map[['latitude', 'longitude', 'valeur']].values, radius=20).add_to(m)
    st_folium(m, use_container_width=True, height=420)

    st.divider()

    col1, col2 = st.columns(2)

    df_aqi = get_data(f"""
        SELECT date_mesure, valeur
        FROM mesure
        WHERE type_mesure='AQI'
        AND date_mesure >= NOW() - INTERVAL '{interval}'
        ORDER BY date_mesure
    """)

    fig_line = px.line(df_aqi, x="date_mesure", y="valeur", markers=True,
                       title="AQI Evolution Over Time")
    col1.plotly_chart(fig_line, use_container_width=True)

    df_sensor = get_data("""
        SELECT
            CASE
                WHEN latitude BETWEEN 35.83 AND 35.84 THEN 'Medina'
                WHEN latitude BETWEEN 35.82 AND 35.83 THEN 'Port'
                WHEN latitude BETWEEN 35.81 AND 35.82 THEN 'Industrial'
                ELSE 'Other'
            END AS district,
            statut,
            COUNT(*) AS nb
        FROM capteur
        GROUP BY district, statut
        ORDER BY district;

    """)

    fig_bar = px.bar(df_sensor, x="district", y="nb", color="statut",
                     barmode="group",
                     title="Sensor Availability by District")
    col2.plotly_chart(fig_bar, use_container_width=True)

# ============================
# AIR QUALITY MONITORING
# ============================

elif page == "Air Quality Monitoring":

    st.title("🌬️ Air Quality Analytics")
    st.caption("Detailed temporal and statistical analysis of air pollution indicators.")

    c1, c2, c3 = st.columns(3)
    avg_aqi = get_data("SELECT ROUND(AVG(valeur)) FROM mesure WHERE type_mesure='AQI'")
    max_aqi = get_data("SELECT MAX(valeur) FROM mesure WHERE type_mesure='AQI'")
    min_aqi = get_data("SELECT MIN(valeur) FROM mesure WHERE type_mesure='AQI'")

    c1.metric("Average AQI", avg_aqi.iloc[0,0])
    c2.metric("Peak AQI", max_aqi.iloc[0,0])
    c3.metric("Lowest AQI", min_aqi.iloc[0,0])

    st.divider()

    df = get_data(f"""
        SELECT date_mesure, valeur
        FROM mesure
        WHERE type_mesure='AQI'
        AND date_mesure >= NOW() - INTERVAL '{interval}'
        ORDER BY date_mesure
    """)

    fig_main = px.line(df, x="date_mesure", y="valeur", markers=True,
                       title="AQI Trend Analysis")
    st.plotly_chart(fig_main, use_container_width=True)

    col1, col2 = st.columns(2)

    fig_hist = px.histogram(df, x="valeur", title="AQI Value Distribution")
    col1.plotly_chart(fig_hist, use_container_width=True)

    fig_box = px.box(df, y="valeur", title="AQI Variability")
    col2.plotly_chart(fig_box, use_container_width=True)



# ============================
# SMART SENSORS MANAGEMENT
# ============================

elif page == "Smart Sensors Management":

    st.title("📡 Smart Sensors Management")
    st.caption("Operational monitoring and inventory of urban IoT sensors.")

    c1, c2, c3 = st.columns(3)
    active = get_data("SELECT COUNT(*) FROM capteur WHERE statut='active'")
    maintenance = get_data("SELECT COUNT(*) FROM capteur WHERE statut='maintenance'")
    inactive = get_data("SELECT COUNT(*) FROM capteur WHERE statut NOT IN ('active','maintenance')")

    c1.metric("Active Sensors", active.iloc[0,0])
    c2.metric("In Maintenance", maintenance.iloc[0,0])
    c3.metric("Inactive Sensors", inactive.iloc[0,0])

    st.divider()

    st.subheader("📍 Sensor Deployment Map")
    st.caption("Geographical distribution and operational status of sensors.")

    df_map = get_data("""
        SELECT id_capteur, type_capteur, latitude, longitude, statut
        FROM capteur
    """)

    m = folium.Map(location=[35.8256, 10.6369], zoom_start=13, tiles="cartodbpositron")

    for _, r in df_map.iterrows():
        color = "green" if r.statut == "active" else "orange" if r.statut == "maintenance" else "red"
        folium.CircleMarker(
            [r.latitude, r.longitude],
            radius=6,
            color=color,
            fill=True,
            fill_opacity=0.9,
            popup=f"ID: {r.id_capteur}<br>Type: {r.type_capteur}<br>Status: {r.statut}"
        ).add_to(m)

    st_folium(m, use_container_width=True, height=420)

    st.divider()

    col1, col2 = st.columns(2)

    df_type = get_data("""
        SELECT type_capteur, COUNT(*) AS nb
        FROM capteur
        GROUP BY type_capteur
    """)
    fig_type = px.bar(df_type, x="type_capteur", y="nb", title="Sensors by Type")
    col1.plotly_chart(fig_type, use_container_width=True)

    df_status = get_data("""
        SELECT statut, COUNT(*) AS nb
        FROM capteur
        GROUP BY statut
    """)
    fig_status = px.pie(df_status, names="statut", values="nb", hole=0.4,
                        title="Sensor Status Distribution")
    col2.plotly_chart(fig_status, use_container_width=True)

    st.divider()

    # ✅ SENSOR INVENTORY (NOW IN THE RIGHT PLACE)
    st.subheader("📋 Sensor Inventory")

    df_all = get_data("""
        SELECT
            id_capteur,
            type_capteur,
            statut,
            CASE
                WHEN latitude BETWEEN 35.835 AND 35.845 THEN 'Sahloul'
                WHEN latitude BETWEEN 35.830 AND 35.835 THEN 'Medina'
                WHEN latitude BETWEEN 35.825 AND 35.830 THEN 'City Center'
                WHEN latitude BETWEEN 35.820 AND 35.825 THEN 'Port'
                WHEN latitude BETWEEN 35.815 AND 35.820 THEN 'Industrial Zone'
                WHEN latitude BETWEEN 35.810 AND 35.815 THEN 'Riadh'
                ELSE 'Peripheral Area'
            END AS district,
            date_installation
        FROM capteur
        ORDER BY district, id_capteur
    """)

    st.dataframe(df_all, use_container_width=True)


# ============================
# PREDICTIVE MAINTENANCE
# ============================

elif page == "Predictive Maintenance":

    st.title("🛠️ Maintenance Operations Analysis")
    st.caption("Evaluation of preventive, corrective and curative maintenance strategies.")

    df_kpi = get_data(f"""
        SELECT
            COUNT(*) FILTER (WHERE type_intervention='predictive') AS predictive,
            COUNT(*) FILTER (WHERE type_intervention='corrective') AS corrective,
            COUNT(*) FILTER (WHERE type_intervention='curative') AS curative,
            ROUND(SUM(economie_co2),2) AS total_co2,
            ROUND(SUM(cout),2) AS total_cost
        FROM intervention
        WHERE date_intervention >= NOW() - INTERVAL '{interval}'
    """)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Predictive", df_kpi.iloc[0,0])
    c2.metric("Corrective", df_kpi.iloc[0,1])
    c3.metric("Curative", df_kpi.iloc[0,2])
    c4.metric("CO₂ Saved (kg)", df_kpi.iloc[0,3])
    c5.metric("Total Cost (TND)", df_kpi.iloc[0,4])

    st.divider()

    col1, col2 = st.columns(2)

    df_type = get_data("SELECT type_intervention, COUNT(*) AS nb FROM intervention GROUP BY type_intervention")
    fig_type = px.pie(df_type, names="type_intervention", values="nb", hole=0.4,
                      title="Maintenance Strategy Distribution")
    col1.plotly_chart(fig_type, use_container_width=True)

    df_cost = get_data("SELECT type_intervention, SUM(cout) AS cost FROM intervention GROUP BY type_intervention")
    fig_cost = px.bar(df_cost, x="type_intervention", y="cost",
                      title="Maintenance Cost by Strategy")
    col2.plotly_chart(fig_cost, use_container_width=True)

    st.subheader("📋 Intervention History")
    df_log = get_data("""
        SELECT i.id_intervention, c.type_capteur, i.type_intervention,
               i.duree, i.cout, i.economie_co2, i.date_intervention
        FROM intervention i JOIN capteur c ON i.id_capteur = c.id_capteur
        ORDER BY i.date_intervention DESC
    """)
    st.dataframe(df_log, use_container_width=True)

# ============================
# CITIZEN ENGAGEMENT
# ============================

elif page == "Citizen Engagement":

    st.title("👥 Citizen Engagement Analytics")
    st.caption("Analysis of citizen participation and ecological engagement indicators.")

    df = get_data("SELECT nom, score_ecologique, preference_mobilite FROM citoyen")

    col1, col2 = st.columns(2)

    fig_bar = px.bar(df.sort_values("score_ecologique", ascending=False),
                     x="nom", y="score_ecologique",
                     color="preference_mobilite",
                     title="Ecological Engagement Score by Citizen")
    col1.plotly_chart(fig_bar, use_container_width=True)

    col2.dataframe(df.sort_values("score_ecologique", ascending=False),
                   use_container_width=True)

# ============================
# AUTONOMOUS VEHICLES
# ============================

elif page == "Autonomous Vehicles":

    st.title("🛣️ Smart Mobility Analytics")
    st.caption("Environmental and operational analysis of municipal autonomous vehicles.")

    df_routes = get_data(f"""
        SELECT origine, destination,
               COUNT(*) AS nb_trajets,
               ROUND(SUM(economie_co2),2) AS total_co2
        FROM trajet
        WHERE date_trajet >= NOW() - INTERVAL '{interval}'
        GROUP BY origine, destination
        ORDER BY total_co2 DESC
    """)

    c1, c2 = st.columns(2)
    c1.metric("Active Routes", df_routes.shape[0])
    c2.metric("Total CO₂ Saved (kg)", df_routes.total_co2.sum())

    st.divider()

    fig_bar = px.bar(df_routes, x="origine", y="total_co2",
                     color="destination",
                     title="CO₂ Savings by Route")
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📋 Route Performance Table")
    st.dataframe(df_routes, use_container_width=True)
