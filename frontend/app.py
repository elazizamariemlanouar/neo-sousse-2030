"""
frontend/app.py — Neo-Sousse 2030  |  Smart City Analytics Platform
Semester 2: Compilation + IA Générative
Style inspired by Semester 1 work: maps, heatmaps, rich charts, light theme.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime
import random, json

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Neo-Sousse 2030",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# DESIGN SYSTEM
# Light theme, green accent (#16a34a), Sousse blue (#0284c7)
# Inherited from S1 aesthetic — clean, data-forward, map-centric
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"]      { font-family: 'Inter', sans-serif; }
.stApp                           { background: #f8fafc; }
#MainMenu, footer, header        { visibility: hidden; }
.block-container                 { padding: 1.8rem 2.4rem 4rem; max-width: 1400px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span { color: #64748b; }
section[data-testid="stSidebar"] .stRadio label {
    font-size: 0.86rem !important;
    color: #374151 !important;
    padding: 4px 0;
}

/* ── Page header ── */
.pg-title {
    font-size: 1.55rem; font-weight: 700; color: #0f172a;
    letter-spacing: -0.03em; margin-bottom: 2px;
}
.pg-sub { font-size: 0.82rem; color: #94a3b8; margin-bottom: 1.6rem; }
.sec-label {
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: .1em; color: #94a3b8;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 6px; margin-bottom: 12px;
}

/* ── KPI cards (S1 inspired — white cards, colored accent bar) ── */
.kpi {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px 20px;
    position: relative; overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}
.kpi::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: var(--a, #16a34a);
}
.kpi-v {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.95rem; font-weight: 600; color: #0f172a;
    line-height: 1; margin-bottom: 5px;
}
.kpi-l {
    font-size: 0.73rem; text-transform: uppercase;
    letter-spacing: .07em; color: #64748b; font-weight: 500;
}
.kpi-tag {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 0.69rem; font-weight: 600; margin-top: 8px;
}
.tag-green { background: #dcfce7; color: #15803d; }
.tag-red   { background: #fee2e2; color: #b91c1c; }
.tag-amber { background: #fef3c7; color: #b45309; }
.tag-blue  { background: #dbeafe; color: #1d4ed8; }

/* ── Alert strip (S1 inspired — left border) ── */
.alert-strip {
    padding: 9px 14px; border-radius: 7px; margin-bottom: 8px;
    font-size: 0.83rem; display: flex; align-items: center; gap: 10px;
}
.a-red   { background: #fff1f2; border-left: 3px solid #ef4444; color: #7f1d1d; }
.a-amber { background: #fffbeb; border-left: 3px solid #f59e0b; color: #78350f; }
.a-green { background: #f0fdf4; border-left: 3px solid #22c55e; color: #14532d; }
.a-blue  { background: #eff6ff; border-left: 3px solid #3b82f6; color: #1e3a8a; }

/* ── Map caption ── */
.map-caption {
    font-size: 0.75rem; color: #94a3b8; margin-top: 6px; text-align: center;
}

/* ── Code / SQL block ── */
.sql-box {
    background: #0f172a; border-radius: 8px; padding: 14px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem; color: #7dd3fc;
    white-space: pre-wrap; line-height: 1.65;
    border: 1px solid #1e293b;
}

/* ── FSM pills ── */
.pill {
    display: inline-block; padding: 3px 11px; border-radius: 20px;
    font-size: 0.74rem; font-weight: 500; margin: 2px 3px;
    border: 1px solid currentColor;
}
.p-green  { color: #15803d; background: #dcfce7; }
.p-grey   { color: #64748b; background: #f1f5f9; }
.p-amber  { color: #b45309; background: #fef3c7; }
.p-blue   { color: #1d4ed8; background: #dbeafe; }
.p-red    { color: #b91c1c; background: #fee2e2; }
.p-bold   { font-weight: 700; box-shadow: 0 0 0 2px currentColor; }

/* ── AI report box ── */
.report-box {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 24px;
    font-size: 0.88rem; line-height: 1.85; color: #334155;
    white-space: pre-wrap;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}

/* ── Divider ── */
hr.soft { border: none; border-top: 1px solid #e2e8f0; margin: 1.4rem 0; }

/* ── Buttons ── */
.stButton > button {
    background: #16a34a; color: #fff; border: none;
    border-radius: 7px; font-family: 'Inter', sans-serif;
    font-size: 0.84rem; font-weight: 500; padding: .44rem 1.2rem;
    transition: background .15s;
}
.stButton > button:hover { background: #15803d; }

/* ── Widget labels ── */
div[data-testid="stSelectbox"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stSlider"] label,
div[data-testid="stTextInput"] label {
    color: #64748b !important; font-size: 0.79rem !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] { font-size: 0.83rem; color: #64748b; }
.stTabs [aria-selected="true"] { color: #16a34a !important; font-weight: 600; }
.stTabs [data-baseweb="tab-border"] { background: #16a34a !important; }

/* ── Expander ── */
div[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    background: #ffffff !important;
}
div[data-testid="stExpander"] summary p {
    font-size: 0.83rem !important; color: #475569 !important;
}

/* ── Streamlit dataframe ── */
.stDataFrame { border-radius: 8px; border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# MODULE IMPORTS
# ─────────────────────────────────────────────────────────────
try:
    from backend.database import (
        get_dashboard_kpis, get_capteurs, get_mesures_recent,
        get_zone_pollution_stats, get_interventions, get_citoyens,
        get_vehicules, get_trajets, simulate_live_updates, execute_query,
    )
    DB_OK = True
except Exception:
    DB_OK = False

try:
    from compiler.nl_sql_compiler import compile_nl
    COMPILER_OK = True
except Exception:
    COMPILER_OK = False

try:
    from automata.fsm_engine import (
        create_sensor_fsm, create_intervention_fsm,
        create_vehicle_fsm, InvalidTransitionError,
    )
    FSM_OK = True
except Exception:
    FSM_OK = False

try:
    from ai_module.report_generator import (
        generate_air_quality_report, generate_sensor_status_report,
        suggest_sensor_action, generate_intervention_report, generate_eco_report,
    )
    AI_OK = True
except Exception:
    AI_OK = False

# ─────────────────────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────────────────────
random.seed(42)
SOUSSE_CENTER = [35.8256, 10.6369]
DISTRICTS = {
    "Sahloul":       (35.840, 10.637),
    "Médina":        (35.832, 10.638),
    "City Center":   (35.828, 10.633),
    "Port":          (35.822, 10.628),
    "Zone Ind.":     (35.817, 10.641),
    "Riadh":         (35.813, 10.631),
    "Corniche":      (35.825, 10.621),
}

def _mock_kpis():
    return dict(capteurs_actifs=160, capteurs_hors_service=8,
                capteurs_signales=15, capteurs_maintenance=12,
                total_capteurs=200, interventions_mois=80,
                co2_evite_mois=342.5, qualite_air_avg=64.3, total=47)

def _mock_zones():
    return [{"zone": d, "avg_pollution": round(random.uniform(25,180),1),
             "max_pollution": round(random.uniform(100,260),1),
             "nb_mesures": random.randint(15,80)} for d in DISTRICTS]

def _mock_capteurs():
    types = ["qualite_air","trafic","energie","dechets","eclairage"]
    statuts = ["active","active","active","maintenance","inactive"]
    rows = []
    for i, (dist, (lat, lon)) in enumerate(DISTRICTS.items()):
        for j in range(6):
            rows.append({
                "code_capteur": f"C-{100+i*6+j}",
                "type_capteur": random.choice(types),
                "statut": random.choice(statuts),
                "zone_nom": dist,
                "latitude": lat + random.uniform(-0.003, 0.003),
                "longitude": lon + random.uniform(-0.003, 0.003),
                "taux_erreur": round(random.uniform(0, 20), 1),
            })
    return rows

def _mock_mesures():
    from datetime import timedelta
    rows = []
    for i in range(120):
        d = DISTRICTS
        zone = random.choice(list(d.keys()))
        lat, lon = d[zone]
        rows.append({
            "latitude": lat + random.uniform(-0.005,0.005),
            "longitude": lon + random.uniform(-0.005,0.005),
            "valeur": round(random.uniform(10, 200), 1),
            "timestamp_mesure": datetime.now() - timedelta(hours=random.randint(0,24)),
            "zone_nom": zone,
            "type_capteur": "qualite_air",
        })
    return rows

def kpis():     return get_dashboard_kpis()         if DB_OK else _mock_kpis()
def zones():    return get_zone_pollution_stats()    if DB_OK else _mock_zones()
def capteurs(): return get_capteurs(limit=200)       if DB_OK else _mock_capteurs()
def mesures():  return get_mesures_recent(48, 300)   if DB_OK else _mock_mesures()

# ─────────────────────────────────────────────────────────────
# PLOTLY THEME  (light, S1-style)
# ─────────────────────────────────────────────────────────────
_PLOT = dict(
    paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
    font=dict(family="Inter", color="#64748b", size=11),
    margin=dict(l=0, r=0, t=36, b=0),
    xaxis=dict(gridcolor="#f1f5f9", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#f1f5f9", showgrid=True, zeroline=False),
)
GREEN  = "#16a34a"
BLUE   = "#0284c7"
AMBER  = "#d97706"
RED    = "#dc2626"
COLORS = [GREEN, BLUE, AMBER, RED, "#7c3aed", "#0891b2"]

def T(fig, h=None, title=None):
    fig.update_layout(**_PLOT)
    if h:     fig.update_layout(height=h)
    if title: fig.update_layout(title=dict(text=title, font_color="#0f172a",
                                            font_size=13, font_weight="bold"))
    return fig

def folium_base():
    return folium.Map(location=SOUSSE_CENTER, zoom_start=13,
                      tiles="cartodbpositron")

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:16px 4px 20px; border-bottom:1px solid #e2e8f0; margin-bottom:16px;'>
        <div style='font-size:1.05rem; font-weight:700; color:#0f172a;'>🌱 Neo-Sousse 2030</div>
        <div style='font-size:0.72rem; color:#94a3b8; margin-top:2px;'>Smart City Analytics Platform</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("Navigation", [
        "Dashboard Overview",
        "Air Quality Monitoring",
        "Analytics — NL→SQL",
        "Automation — FSM",
        "AI Insights",
        "Data Explorer",
    ], label_visibility="collapsed")

    st.markdown("<div style='height:1px;background:#e2e8f0;margin:14px 0;'></div>", unsafe_allow_html=True)

    # Time filter (like S1)
    time_filter = st.selectbox("Time Range", ["Last 24 hours","Last 7 days","Last 30 days"])
    interval = {"Last 24 hours":"24 hours","Last 7 days":"7 days","Last 30 days":"30 days"}[time_filter]

    st.markdown("<div style='height:1px;background:#e2e8f0;margin:14px 0;'></div>", unsafe_allow_html=True)

    # Module status
    st.markdown("<div style='font-size:0.7rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;'>Modules</div>", unsafe_allow_html=True)
    for lbl, ok in [("Database",DB_OK),("NL→SQL",COMPILER_OK),("FSM",FSM_OK),("AI",AI_OK)]:
        c, s = ("#16a34a","Online") if ok else ("#ef4444","Offline")
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:7px;margin-bottom:5px;'>
            <div style='width:6px;height:6px;border-radius:50%;background:{c};'></div>
            <span style='font-size:0.79rem;color:#64748b;'>{lbl}</span>
            <span style='font-size:0.74rem;color:{c};margin-left:auto;font-weight:500;'>{s}</span>
        </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  PAGE 1 — DASHBOARD OVERVIEW
# ═════════════════════════════════════════════════════════════
if page == "Dashboard Overview":

    st.markdown('<div class="pg-title">📊 City Performance Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Global indicators summarising urban services — Neo-Sousse metropolitan area</div>', unsafe_allow_html=True)

    K = kpis()

    # ── KPIs (4 cards like S1) ────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    for col, val, label, accent, tag_cls, tag_txt in [
        (c1, K.get("capteurs_actifs",0),          "Active Sensors",     GREEN, "tag-green", f"of {K.get('total_capteurs',200)} total"),
        (c2, K.get("capteurs_hors_service",0),    "Out of Service",     RED,   "tag-red",   "Requires action"),
        (c3, f"{K.get('qualite_air_avg',0):.1f}", "City AQI µg/m³",    AMBER, "tag-amber", "24h city average"),
        (c4, f"{K.get('co2_evite_mois',0):.0f} kg","CO₂ Saved",        BLUE,  "tag-blue",  f"Month total"),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi" style="--a:{accent};">
                <div class="kpi-v">{val}</div>
                <div class="kpi-l">{label}</div>
                <div class="kpi-tag {tag_cls}">{tag_txt}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='soft'>", unsafe_allow_html=True)

    # ── Heatmap + AQI time series (S1 layout) ────────────────
    st.markdown("#### 🌍 Pollution Spatial Distribution")
    st.caption("Heatmap showing air quality concentration across Sousse districts")

    df_m = pd.DataFrame(mesures())
    m_heat = folium_base()
    heat_data = df_m[["latitude","longitude","valeur"]].dropna().values.tolist()
    HeatMap(heat_data, radius=22, blur=18,
            gradient={"0.3":"#22c55e","0.6":"#f59e0b","1.0":"#ef4444"}).add_to(m_heat)
    st_folium(m_heat, use_container_width=True, height=400)
    st.markdown('<div class="map-caption">Green = clean air · Orange = moderate · Red = above regulatory threshold (50 µg/m³)</div>', unsafe_allow_html=True)

    st.markdown("<hr class='soft'>", unsafe_allow_html=True)

    # ── Two charts side by side (S1 pattern) ─────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        # AQI trend line with markers (S1 signature chart)
        df_m["timestamp_mesure"] = pd.to_datetime(df_m["timestamp_mesure"])
        df_trend = df_m[df_m["type_capteur"]=="qualite_air"].sort_values("timestamp_mesure")
        if not df_trend.empty:
            fig_line = px.line(df_trend, x="timestamp_mesure", y="valeur",
                               color="zone_nom", markers=True,
                               labels={"valeur":"AQI µg/m³","timestamp_mesure":"","zone_nom":"Zone"},
                               color_discrete_sequence=COLORS)
            fig_line.add_hline(y=50, line_dash="dot", line_color=RED,
                               annotation_text="Threshold 50", annotation_font_color=RED,
                               annotation_font_size=10)
            T(fig_line, h=310, title="AQI Evolution by Zone")
            fig_line.update_layout(legend=dict(orientation="h", y=-.18, x=0, font_size=10))
            st.plotly_chart(fig_line, use_container_width=True)

    with col_r:
        # Sensor availability by district (S1 bar chart)
        df_cap = pd.DataFrame(capteurs())
        if not df_cap.empty:
            df_dist = df_cap.groupby(["zone_nom","statut"]).size().reset_index(name="count")
            fig_bar = px.bar(df_dist, x="zone_nom", y="count", color="statut",
                             barmode="group",
                             color_discrete_map={
                                 "actif":"#16a34a","active":"#16a34a",
                                 "signale":"#f59e0b","maintenance":"#f59e0b",
                                 "hors_service":"#ef4444","inactive":"#ef4444","inactif":"#ef4444",
                             },
                             labels={"count":"Sensors","zone_nom":"","statut":"Status"})
            T(fig_bar, h=310, title="Sensor Availability by District")
            fig_bar.update_layout(legend=dict(orientation="h", y=-.18, x=0, font_size=10))
            st.plotly_chart(fig_bar, use_container_width=True)

    # ── Alerts strip ──────────────────────────────────────────
    st.markdown("<hr class='soft'>", unsafe_allow_html=True)
    st.markdown("#### System Alerts")
    col_a1, col_a2 = st.columns(2)
    hs  = K.get("capteurs_hors_service",0)
    sig = K.get("capteurs_signales",0)
    mnt = K.get("capteurs_maintenance",0)
    act = K.get("capteurs_actifs",0)
    with col_a1:
        cls1 = "a-red"   if hs  > 0 else "a-green"
        cls2 = "a-amber" if sig > 0 else "a-green"
        st.markdown(f'<div class="alert-strip {cls1}">{"🔴" if hs else "✅"} {hs} sensors out of service {"— action required" if hs else "— all critical sensors operational"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="alert-strip {cls2}">{"⚠️" if sig else "✅"} {sig} sensors flagged {"— inspection needed" if sig else "— no flagged sensors"}</div>', unsafe_allow_html=True)
    with col_a2:
        cls3 = "a-amber" if mnt > 0 else "a-green"
        st.markdown(f'<div class="alert-strip {cls3}">{"🔧" if mnt else "✅"} {mnt} sensors in maintenance {"— scheduled" if mnt else "— no pending maintenance"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="alert-strip a-blue">ℹ️ {act} sensors operational — uptime {round(100*act/max(K.get("total_capteurs",200),1),1)}%</div>', unsafe_allow_html=True)

    if DB_OK:
        if st.button("🔄 Refresh live readings"):
            n = simulate_live_updates()
            st.success(f"✅ {n} new sensor readings inserted")


# ═════════════════════════════════════════════════════════════
#  PAGE 2 — AIR QUALITY MONITORING
# ═════════════════════════════════════════════════════════════
elif page == "Air Quality Monitoring":

    st.markdown('<div class="pg-title">🌬️ Air Quality Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Detailed temporal and spatial analysis of PM2.5 air pollution indicators</div>', unsafe_allow_html=True)

    df_m = pd.DataFrame(mesures())
    df_air = df_m[df_m["type_capteur"]=="qualite_air"].copy()

    # ── 3 KPIs ───────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    avg_v = df_air["valeur"].mean() if not df_air.empty else 0
    max_v = df_air["valeur"].max()  if not df_air.empty else 0
    min_v = df_air["valeur"].min()  if not df_air.empty else 0
    for col, val, label, accent, tag_cls, tag_txt in [
        (c1, f"{avg_v:.1f}", "Average AQI",  AMBER, "tag-amber", "µg/m³"),
        (c2, f"{max_v:.1f}", "Peak AQI",     RED,   "tag-red",   "Highest recorded"),
        (c3, f"{min_v:.1f}", "Lowest AQI",   GREEN, "tag-green", "Best air quality"),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi" style="--a:{accent};">
                <div class="kpi-v">{val}</div>
                <div class="kpi-l">{label}</div>
                <div class="kpi-tag {tag_cls}">{tag_txt}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='soft'>", unsafe_allow_html=True)

    # ── Main AQI trend (S1 signature: line + markers) ────────
    if not df_air.empty:
        df_air["timestamp_mesure"] = pd.to_datetime(df_air["timestamp_mesure"])
        df_sorted = df_air.sort_values("timestamp_mesure")
        fig_main = px.line(df_sorted, x="timestamp_mesure", y="valeur",
                           color="zone_nom", markers=True,
                           labels={"valeur":"AQI µg/m³","timestamp_mesure":"Time","zone_nom":"Zone"},
                           color_discrete_sequence=COLORS)
        fig_main.add_hline(y=50, line_dash="dot", line_color=RED,
                           annotation_text="⚠ Regulatory threshold (50 µg/m³)",
                           annotation_font_color=RED, annotation_font_size=10)
        fig_main.add_hrect(y0=0, y1=50, fillcolor="#16a34a", opacity=.04, line_width=0)
        fig_main.add_hrect(y0=50, y1=300, fillcolor="#dc2626", opacity=.03, line_width=0)
        T(fig_main, h=320, title="AQI Trend Analysis")
        fig_main.update_layout(legend=dict(orientation="h", y=-.15, x=0, font_size=10))
        st.plotly_chart(fig_main, use_container_width=True)

    # ── Distribution + Box plot (S1 pattern) ─────────────────
    col1, col2 = st.columns(2)
    with col1:
        fig_hist = px.histogram(df_air, x="valeur", nbins=20,
                                color_discrete_sequence=[BLUE],
                                labels={"valeur":"AQI µg/m³","count":"Readings"})
        fig_hist.add_vline(x=50, line_dash="dot", line_color=RED,
                           annotation_text="Threshold", annotation_font_size=10)
        T(fig_hist, h=280, title="AQI Value Distribution")
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        fig_box = px.box(df_air, y="valeur", x="zone_nom",
                         color="zone_nom",
                         color_discrete_sequence=COLORS,
                         labels={"valeur":"AQI µg/m³","zone_nom":""})
        fig_box.add_hline(y=50, line_dash="dot", line_color=RED)
        T(fig_box, h=280, title="AQI Variability by Zone")
        fig_box.update_layout(showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

    # ── Pollution zone ranking bar ────────────────────────────
    st.markdown("<hr class='soft'>", unsafe_allow_html=True)
    df_z = pd.DataFrame(zones()).sort_values("avg_pollution", ascending=False)
    fig_rank = px.bar(df_z, x="zone", y="avg_pollution",
                      color="avg_pollution",
                      color_continuous_scale=[[0,GREEN],[.5,AMBER],[1,RED]],
                      text=df_z["avg_pollution"].round(1).astype(str) + " µg/m³",
                      labels={"avg_pollution":"Avg PM2.5 µg/m³","zone":""})
    fig_rank.add_hline(y=50, line_dash="dot", line_color=RED,
                       annotation_text="Threshold", annotation_font_size=10)
    fig_rank.update_traces(textposition="outside")
    fig_rank.update_coloraxes(showscale=False)
    T(fig_rank, h=310, title="Most Polluted Zones — Ranked")
    st.plotly_chart(fig_rank, use_container_width=True)


# ═════════════════════════════════════════════════════════════
#  PAGE 3 — ANALYTICS: NL → SQL COMPILER
# ═════════════════════════════════════════════════════════════
elif page == "Analytics — NL→SQL":

    st.markdown('<div class="pg-title">🔍 NL → SQL Compiler</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Type a query in French — Lexer → Parser → AST → SQL generation pipeline</div>', unsafe_allow_html=True)

    if not COMPILER_OK:
        st.error("Compiler module unavailable — check compiler/nl_sql_compiler.py"); st.stop()

    EXAMPLES = [
        "Affiche les 5 zones les plus polluées",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score écologique > 80 ?",
        "Donne-moi le trajet le plus économique en co2",
        "Liste les interventions en cours",
        "Montre les capteurs avec taux_erreur > 10",
        "Affiche les 10 mesures les plus récentes",
        "Combien d'interventions sont terminées ?",
    ]

    col_q, col_ex = st.columns([3,1], gap="large")
    with col_ex:
        st.markdown('<div class="sec-label">Load example</div>', unsafe_allow_html=True)
        chosen = st.selectbox("ex", ["— type manually —"] + EXAMPLES, label_visibility="collapsed")
    with col_q:
        default = chosen if chosen != "— type manually —" else ""
        query = st.text_area("Query in French", value=default, height=70,
                             placeholder="Ex: Affiche les capteurs hors service en zone industrielle")

    run = st.button("⚡ Compile & Execute", type="primary")

    if run and query.strip():
        result = compile_nl(query)
        t_tok, t_ast, t_sql = st.tabs(["🔤 Tokens (Lexer)", "🌲 AST (Parser)", "💾 SQL + Results"])

        with t_tok:
            if result.tokens:
                df_tok = pd.DataFrame([
                    {"#": i, "Type": t.type.name, "Value": str(t.value)}
                    for i, t in enumerate(result.tokens) if t.value is not None
                ])
                st.dataframe(df_tok, use_container_width=True, hide_index=True, height=220)
            st.caption(f"{len(result.tokens)} tokens produced")

        with t_ast:
            if result.ast:
                st.json({
                    "node": "SelectNode",
                    "entity": result.ast.entity,
                    "alias": result.ast.alias,
                    "is_count": result.ast.is_count,
                    "limit": result.ast.limit,
                    "order_by": result.ast.order_by,
                    "order_dir": result.ast.order_dir,
                    "where": {
                        "field": result.ast.where.field,
                        "operator": result.ast.where.comparator,
                        "value": result.ast.where.value,
                    } if result.ast.where else None,
                })

        with t_sql:
            if result.success:
                st.markdown(f'<div class="sql-box">{result.sql}</div>', unsafe_allow_html=True)
                st.success("✅ Compilation successful")
                if DB_OK:
                    try:
                        rows = execute_query(result.sql)
                        if rows:
                            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                            df_res = pd.DataFrame(rows)
                            st.dataframe(df_res, use_container_width=True, hide_index=True, height=260)
                            st.caption(f"{len(rows)} row(s) returned from PostgreSQL")

                            # Auto-visualise numeric results
                            num_cols = df_res.select_dtypes("number").columns.tolist()
                            str_cols = df_res.select_dtypes("object").columns.tolist()
                            if num_cols and str_cols:
                                with st.expander("📊 Auto-visualise results"):
                                    fig_r = px.bar(df_res, x=str_cols[0], y=num_cols[0],
                                                   color_discrete_sequence=[GREEN])
                                    T(fig_r, h=260)
                                    st.plotly_chart(fig_r, use_container_width=True)
                        else:
                            st.info("Query returned no results.")
                    except Exception as e:
                        st.warning(f"SQL execution error: {e}")
            else:
                st.markdown(f'<div class="sql-box" style="color:#fca5a5;">{result.error}</div>',
                            unsafe_allow_html=True)
                st.error("❌ Compilation failed")

    with st.expander("📖 Grammar Reference"):
        st.code("""
query     ::= afficher | compter | donner

afficher  ::= ("affiche"|"montre"|"liste"|"quels") [limit] entity [where] [order]
compter   ::= ("combien"|"nombre") ["de"] entity [where]
donner    ::= ("donne"|"trouve") [limit] entity [where] [order]

entity    ::= capteurs | mesures | interventions | citoyens
            | véhicules | trajets | zones | techniciens

where     ::= ("où"|"qui"|"avec"|"ayant"|"dont"|"ont") field cmp value
cmp       ::= ">" | "<" | ">=" | "<=" | "=" | "supérieur" | "inférieur"
limit     ::= "les" NUMBER
field     ::= pollution | statut | score | co2 | taux_erreur | cout | durée | nom
""", language="text")


# ═════════════════════════════════════════════════════════════
#  PAGE 4 — AUTOMATION: FSM
# ═════════════════════════════════════════════════════════════
elif page == "Automation — FSM":

    st.markdown('<div class="pg-title">⚙️ Finite State Machines</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Simulate and validate entity lifecycle transitions with deterministic automata</div>', unsafe_allow_html=True)

    if not FSM_OK:
        st.error("FSM module unavailable — check automata/fsm_engine.py"); st.stop()

    fsm_choice = st.selectbox("Select automaton", [
        "🔵 Sensor Lifecycle",
        "🟡 Intervention Workflow",
        "🟢 Vehicle Journey",
    ], label_visibility="collapsed")

    _STATE_PILL = {
        "inactif":"p-grey","actif":"p-green","signale":"p-amber",
        "en_maintenance":"p-blue","hors_service":"p-red",
        "stationne":"p-grey","en_route":"p-green","en_panne":"p-red","arrive":"p-green",
        "demande":"p-grey","tech1_assigne":"p-blue","tech2_valide":"p-amber",
        "ia_valide":"p-blue","termine":"p-green",
    }

    FSM_DEF = {
        "🔵 Sensor Lifecycle": dict(
            create=create_sensor_fsm,
            states=["inactif","actif","signale","en_maintenance","hors_service"],
            transitions=[
                ("inactif","installation","actif"),
                ("actif","detection_anomalie","signale"),
                ("actif","panne","hors_service"),
                ("signale","reparation","en_maintenance"),
                ("signale","panne","hors_service"),
                ("en_maintenance","reparation","actif"),
                ("en_maintenance","panne","hors_service"),
                ("hors_service","reparation","en_maintenance"),
            ],
            id_lbl="Sensor code", id_val="C-452", extra=None,
            desc="Models the full lifecycle of an IoT sensor from installation to decommission.",
        ),
        "🟡 Intervention Workflow": dict(
            create=create_intervention_fsm,
            states=["demande","tech1_assigne","tech2_valide","ia_valide","termine"],
            transitions=[
                ("demande","assigner_tech1","tech1_assigne"),
                ("tech1_assigne","valider_tech2","tech2_valide"),
                ("tech1_assigne","rejeter","demande"),
                ("tech2_valide","valider_ia","ia_valide"),
                ("tech2_valide","rejeter","tech1_assigne"),
                ("ia_valide","cloturer","termine"),
                ("ia_valide","rejeter","tech2_valide"),
            ],
            id_lbl="Intervention ID", id_val="INT-001", extra="ia_score",
            desc="Two-technician + AI validation workflow for every maintenance intervention.",
        ),
        "🟢 Vehicle Journey": dict(
            create=create_vehicle_fsm,
            states=["stationne","en_route","en_panne","arrive"],
            transitions=[
                ("stationne","depart","en_route"),
                ("en_route","arrivee","arrive"),
                ("en_route","panne","en_panne"),
                ("en_panne","reparation","en_route"),
                ("en_panne","remorquage","stationne"),
                ("arrive","retour_base","stationne"),
            ],
            id_lbl="Vehicle plate", id_val="TUN-2030", extra=None,
            desc="Tracks the real-time journey state of autonomous municipal vehicles.",
        ),
    }

    meta = FSM_DEF[fsm_choice]
    st.caption(meta["desc"])
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    col_ctrl, col_tbl = st.columns([1,2], gap="large")

    with col_ctrl:
        st.markdown('<div class="sec-label">Simulator</div>', unsafe_allow_html=True)
        entity_id = st.text_input(meta["id_lbl"], value=meta["id_val"])
        current   = st.selectbox("Current state", meta["states"])

        fsm = meta["create"]()
        fsm.current_state = current
        avail = fsm.available_events()

        # State diagram (pills)
        st.markdown('<div class="sec-label" style="margin-top:14px;">State diagram</div>', unsafe_allow_html=True)
        pills = ""
        for i, s in enumerate(meta["states"]):
            cls  = _STATE_PILL.get(s, "p-grey")
            bold = " p-bold" if s == current else ""
            arrow = " → " if i < len(meta["states"])-1 else ""
            pills += f'<span class="pill {cls}{bold}">{s}</span>{arrow}'
        st.markdown(f"<div style='line-height:2.2;'>{pills}</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        ia_score = None
        if meta["extra"] == "ia_score" and "valider_ia" in avail:
            ia_score = st.slider("AI validation score", 0, 100, 85)

        event = st.selectbox("Fire event", ["— select event —"] + avail)

        if st.button("▶ Trigger transition") and event != "— select event —":
            try:
                md = {meta["id_lbl"].lower().replace(" ",""): entity_id}
                if ia_score: md["score"] = ia_score
                new_s = fsm.trigger(event, md)
                st.success(f"✅  **{current}**  →  **{new_s}**")
                for a in fsm.get_alerts():
                    st.warning(a)
            except InvalidTransitionError as e:
                st.error(str(e))

    with col_tbl:
        st.markdown('<div class="sec-label">Transition table (δ)</div>', unsafe_allow_html=True)
        df_t = pd.DataFrame(meta["transitions"], columns=["From State (q)","Event (σ)","Next State (δ)"])
        # highlight rows involving current state
        st.dataframe(df_t, use_container_width=True, hide_index=True, height=290)

        # Transitions bar chart (visual summary)
        state_counts = {}
        for f,_,t in meta["transitions"]:
            state_counts[f] = state_counts.get(f,0)+1
        df_sc = pd.DataFrame({"State":list(state_counts.keys()),
                               "Out-degree":list(state_counts.values())})
        fig_sc = px.bar(df_sc, x="State", y="Out-degree",
                        color="State", color_discrete_sequence=COLORS,
                        labels={"Out-degree":"# transitions out"})
        T(fig_sc, h=200, title="Transitions per State")
        fig_sc.update_layout(showlegend=False)
        st.plotly_chart(fig_sc, use_container_width=True)

    with st.expander("🔎 Sequence Validator"):
        default_seq = ", ".join(t[1] for t in meta["transitions"][:4])
        seq_in = st.text_input("Comma-separated events to validate",
                               value=default_seq, label_visibility="collapsed")
        if st.button("Validate sequence"):
            events = [e.strip() for e in seq_in.split(",") if e.strip()]
            chk = meta["create"]()
            valid, final, path = chk.validate_sequence(events)
            if valid:
                st.success(f"✅ Valid — final state: **{final}**")
            else:
                st.error(f"❌ Invalid — blocked at: **{final}**")
            path_html = " → ".join(
                f'<span class="pill {_STATE_PILL.get(s,"p-grey")}">{s}</span>' for s in path
            )
            st.markdown(path_html, unsafe_allow_html=True)
            rows = [{"Step":i+1,"From":fs,"Event":ev,"To":ts,"":"✓"}
                    for i,(ev,fs,ts) in enumerate(zip(events,path[:-1],path[1:]))]
            if not valid and len(path)<=len(events):
                for ev in events[len(path)-1:]:
                    rows.append({"Step":"—","From":path[-1],"Event":ev,"To":"BLOCKED","":"✗"})
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════════════════════
#  PAGE 5 — AI INSIGHTS
# ═════════════════════════════════════════════════════════════
elif page == "AI Insights":

    st.markdown('<div class="pg-title">🧠 AI Generative Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Claude-powered urban analytics — structured reports in French for city managers</div>', unsafe_allow_html=True)

    REPORTS = {
        "Air Quality Report":        "Daily air quality summary with zone analysis and regulatory alerts",
        "Sensor Fleet Status":       "Fleet health overview with priority maintenance recommendations",
        "Sensor Action Suggestion":  "Targeted diagnosis and action plan for a specific sensor",
        "Intervention Report":       "Status and cost performance of recent maintenance operations",
        "Ecological Performance":    "Monthly CO₂ savings, vehicle fleet impact, and citizen engagement",
    }

    col_sel, col_preview = st.columns([1,2], gap="large")

    with col_sel:
        st.markdown('<div class="sec-label">Report type</div>', unsafe_allow_html=True)
        report_type = st.selectbox("rtype", list(REPORTS.keys()), label_visibility="collapsed")

        ctx = {}
        if report_type == "Air Quality Report":
            ctx["threshold"] = st.slider("Regulatory threshold µg/m³", 20, 100, 50)
        elif report_type == "Sensor Action Suggestion":
            ctx["code"]   = st.text_input("Sensor code", "C-452")
            ctx["type"]   = st.selectbox("Type", ["qualite_air","trafic","energie","dechets","eclairage"])
            ctx["zone"]   = st.text_input("Zone", "Zone Industrielle")
            ctx["statut"] = st.selectbox("Status", ["signale","en_maintenance","hors_service"])
            ctx["taux"]   = st.slider("Error rate (%)", 0.0, 100.0, 15.3)

        generate = st.button("🤖 Generate Report", type="primary")

    with col_preview:
        st.markdown('<div class="sec-label">Description</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                    padding:14px 18px;font-size:.84rem;color:#475569;line-height:1.75;'>
            {REPORTS[report_type]}
        </div>""", unsafe_allow_html=True)

        if not AI_OK:
            st.markdown("""
            <div style='margin-top:12px;background:#fffbeb;border:1px solid #fde68a;
                        border-radius:8px;padding:14px 18px;font-size:.82rem;color:#92400e;'>
                <strong>AI module offline</strong><br>
                Add <code>ANTHROPIC_API_KEY=sk-ant-…</code> to your <code>.env</code> file.<br>
                Get a key at <code>console.anthropic.com</code>
            </div>""", unsafe_allow_html=True)

    if generate:
        if not AI_OK:
            st.error("AI module offline — add ANTHROPIC_API_KEY to .env")
        else:
            K = kpis(); Z = zones()
            with st.spinner("Generating report…"):
                try:
                    if report_type == "Air Quality Report":
                        nb_crit = sum(1 for z in Z if z.get("avg_pollution",0) > ctx["threshold"])
                        txt = generate_air_quality_report({
                            "date": datetime.now().strftime("%d/%m/%Y"),
                            "zones": Z, "threshold": ctx["threshold"], "nb_zones_critical": nb_crit,
                        })
                    elif report_type == "Sensor Fleet Status":
                        top_err = get_capteurs(limit=5) if DB_OK else []
                        txt = generate_sensor_status_report({
                            "total": K.get("total_capteurs",200),
                            "actif": K.get("capteurs_actifs",0),
                            "signale": K.get("capteurs_signales",0),
                            "en_maintenance": K.get("capteurs_maintenance",0),
                            "hors_service": K.get("capteurs_hors_service",0),
                            "inactif": 0,
                            "top_error": [{"code":c.get("code_capteur","?"),
                                           "taux":c.get("taux_erreur",0)} for c in top_err],
                        })
                    elif report_type == "Sensor Action Suggestion":
                        txt = suggest_sensor_action({
                            "code":ctx["code"],"type":ctx["type"],"zone":ctx["zone"],
                            "statut":ctx["statut"],"taux_erreur":ctx["taux"],
                            "derniere_mesure":datetime.now().strftime("%Y-%m-%d %H:%M"),
                        })
                    elif report_type == "Intervention Report":
                        intervs = get_interventions(limit=10) if DB_OK else []
                        items = [{"id":i.get("intervention_id"),"nature":i.get("nature"),
                                  "capteur":i.get("code_capteur"),"statut":i.get("statut"),
                                  "cout":i.get("cout",0)} for i in intervs] \
                                or [{"id":1,"nature":"corrective","capteur":"C-100","statut":"en_cours","cout":1200}]
                        txt = generate_intervention_report(items)
                    elif report_type == "Ecological Performance":
                        txt = generate_eco_report({
                            "co2_trajets":145.3,"co2_interventions":K.get("co2_evite_mois",0),
                            "citoyens_engages":K.get("total",0),"score_moyen":65.4,"capteurs_energie":38,
                        })
                    st.markdown(f'<div class="report-box">{txt}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Generation error: {e}")


# ═════════════════════════════════════════════════════════════
#  PAGE 6 — DATA EXPLORER
# ═════════════════════════════════════════════════════════════
elif page == "Data Explorer":

    st.markdown('<div class="pg-title">🗂️ Data Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Browse, map and visualise all urban datasets</div>', unsafe_allow_html=True)

    dataset = st.selectbox("Dataset", [
        "📡 Sensors","🛠️ Interventions","🚌 Vehicles & Trips","👥 Citizens",
    ], label_visibility="collapsed")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Sensors ──────────────────────────────────────────────
    if dataset == "📡 Sensors":
        col_f, _ = st.columns([1,3])
        with col_f:
            sf = st.selectbox("Status filter",
                              ["all","actif","active","signale","en_maintenance","hors_service","inactive"])
        df = pd.DataFrame(capteurs())
        if sf != "all":
            df = df[df["statut"]==sf]

        c1,c2,c3 = st.columns(3)
        c1.metric("Active",    int((df["statut"].isin(["actif","active"])).sum()))
        c2.metric("Maintenance",int((df["statut"].isin(["maintenance","en_maintenance","signale"])).sum()))
        c3.metric("Inactive",   int((df["statut"].isin(["inactive","inactif","hors_service"])).sum()))

        st.markdown("<hr class='soft'>", unsafe_allow_html=True)

        # Interactive sensor map (S1 CircleMarker pattern)
        st.markdown("#### 📍 Sensor Deployment Map")
        st.caption("Geographical distribution and operational status of all IoT sensors")
        m_sensor = folium_base()
        STATUS_COLOR = {
            "active":"green","actif":"green",
            "maintenance":"orange","en_maintenance":"orange","signale":"orange",
            "inactive":"red","inactif":"red","hors_service":"red",
        }
        for _, r in df.iterrows():
            if pd.notna(r.get("latitude")) and pd.notna(r.get("longitude")):
                color = STATUS_COLOR.get(r.get("statut",""),"gray")
                folium.CircleMarker(
                    [r["latitude"], r["longitude"]],
                    radius=7, color=color, fill=True, fill_opacity=0.85,
                    popup=folium.Popup(
                        f"<b>{r.get('code_capteur','?')}</b><br>"
                        f"Type: {r.get('type_capteur','?')}<br>"
                        f"Status: {r.get('statut','?')}<br>"
                        f"Zone: {r.get('zone_nom','?')}<br>"
                        f"Error rate: {r.get('taux_erreur','?')}%",
                        max_width=200
                    )
                ).add_to(m_sensor)
        st_folium(m_sensor, use_container_width=True, height=420)
        st.markdown('<div class="map-caption">🟢 Active &nbsp;·&nbsp; 🟠 Maintenance / Flagged &nbsp;·&nbsp; 🔴 Out of Service</div>', unsafe_allow_html=True)

        st.markdown("<hr class='soft'>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            df_type = df.groupby("type_capteur").size().reset_index(name="count")
            fig_t = px.bar(df_type, x="type_capteur", y="count",
                           color_discrete_sequence=[BLUE],
                           labels={"count":"Sensors","type_capteur":""})
            T(fig_t, h=250, title="Sensors by Type")
            st.plotly_chart(fig_t, use_container_width=True)
        with col_b:
            df_stat = df.groupby("statut").size().reset_index(name="count")
            fig_s = px.pie(df_stat, names="statut", values="count", hole=0.45,
                           color_discrete_map={
                               "active":"#16a34a","actif":"#16a34a",
                               "maintenance":"#f59e0b","en_maintenance":"#f59e0b","signale":"#f59e0b",
                               "inactive":"#ef4444","inactif":"#ef4444","hors_service":"#ef4444",
                           })
            T(fig_s, h=250, title="Status Distribution")
            st.plotly_chart(fig_s, use_container_width=True)

        with st.expander("📋 Full Sensor Inventory"):
            st.dataframe(df, use_container_width=True, hide_index=True, height=300)

    # ── Interventions ─────────────────────────────────────────
    elif dataset == "🛠️ Interventions":
        if not DB_OK:
            st.warning("Connect the database to view interventions."); st.stop()
        col_f, _ = st.columns([1,3])
        with col_f:
            if_ = st.selectbox("Status", ["all","demande","tech1_assigne",
                                          "tech2_valide","ia_valide","termine"])
        rows = get_interventions(statut=None if if_=="all" else if_, limit=80)
        df_i = pd.DataFrame(rows) if rows else pd.DataFrame()

        if not df_i.empty:
            c1,c2,c3 = st.columns(3)
            c1.metric("Total", len(df_i))
            c2.metric("Avg Cost (TND)", f"{df_i['cout'].mean():.0f}" if "cout" in df_i else "—")
            c3.metric("CO₂ Impact (kg)", f"{df_i['impact_co2'].sum():.1f}" if "impact_co2" in df_i else "—")

            st.markdown("<hr class='soft'>", unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                df_n = df_i.groupby("nature").size().reset_index(name="count")
                fig_n = px.pie(df_n, names="nature", values="count", hole=0.45,
                               color_discrete_sequence=[GREEN,BLUE,AMBER],
                               title="Maintenance Strategy Distribution")
                T(fig_n, h=250); fig_n.update_layout(showlegend=True)
                st.plotly_chart(fig_n, use_container_width=True)
            with col_b:
                if "cout" in df_i and "nature" in df_i:
                    df_cost = df_i.groupby("nature")["cout"].sum().reset_index()
                    fig_c = px.bar(df_cost, x="nature", y="cout",
                                   color="nature", color_discrete_sequence=[GREEN,BLUE,AMBER],
                                   labels={"cout":"Total Cost TND","nature":""})
                    T(fig_c, h=250, title="Maintenance Cost by Strategy")
                    fig_c.update_layout(showlegend=False)
                    st.plotly_chart(fig_c, use_container_width=True)

            with st.expander("📋 Intervention History"):
                st.dataframe(df_i, use_container_width=True, hide_index=True, height=300)

    # ── Vehicles & Trips ──────────────────────────────────────
    elif dataset == "🚌 Vehicles & Trips":
        if not DB_OK:
            st.warning("Connect the database to view vehicle data."); st.stop()

        t_fleet, t_routes = st.tabs(["Fleet Status","Route Performance"])

        with t_fleet:
            vehs = get_vehicules()
            if vehs:
                df_v = pd.DataFrame(vehs)
                c1,c2 = st.columns(2)
                c1.metric("Total Fleet", len(df_v))
                c2.metric("En Route", int((df_v["statut"]=="en_route").sum()) if "statut" in df_v else "—")

                col_a, col_b = st.columns(2)
                with col_a:
                    fig_vs = px.pie(df_v, names="statut", hole=0.45,
                                    color_discrete_map={
                                        "stationne":"#64748b","en_route":GREEN,
                                        "en_panne":RED,"arrive":BLUE},
                                    title="Fleet Status")
                    T(fig_vs, h=250); st.plotly_chart(fig_vs, use_container_width=True)
                with col_b:
                    fig_ve = px.pie(df_v, names="energie", hole=0.45,
                                    color_discrete_sequence=[GREEN,BLUE,AMBER],
                                    title="Energy Mix")
                    T(fig_ve, h=250); st.plotly_chart(fig_ve, use_container_width=True)

                with st.expander("📋 Fleet Inventory"):
                    st.dataframe(df_v, use_container_width=True, hide_index=True)

        with t_routes:
            trips = get_trajets(limit=50)
            if trips:
                df_t = pd.DataFrame(trips)
                c1,c2 = st.columns(2)
                c1.metric("Total Routes", len(df_t))
                c2.metric("Total CO₂ Saved (kg)", f"{df_t['economie_co2'].sum():.1f}" if "economie_co2" in df_t else "—")

                # CO₂ by route (S1 pattern: color=destination)
                if "origine" in df_t and "economie_co2" in df_t:
                    fig_co2 = px.bar(df_t.head(20),
                                     x="origine", y="economie_co2",
                                     color="destination",
                                     color_discrete_sequence=COLORS,
                                     labels={"economie_co2":"kg CO₂ saved","origine":"Origin"},
                                     title="CO₂ Savings by Route")
                    T(fig_co2, h=300)
                    fig_co2.update_layout(legend=dict(orientation="h",y=-.2,x=0,font_size=10))
                    st.plotly_chart(fig_co2, use_container_width=True)

                with st.expander("📋 Route Performance Table"):
                    cols = ["trajet_id","immatriculation","origine","destination",
                            "distance_km","economie_co2","duree_minutes"]
                    st.dataframe(df_t[[c for c in cols if c in df_t.columns]],
                                 use_container_width=True, hide_index=True)

    # ── Citizens ──────────────────────────────────────────────
    elif dataset == "👥 Citizens":
        if not DB_OK:
            st.warning("Connect the database to view citizen data."); st.stop()
        min_sc = st.slider("Minimum ecological score", 0, 100, 0)
        rows = get_citoyens(min_score=min_sc, limit=100)
        if rows:
            df_c = pd.DataFrame(rows)
            c1,c2,c3 = st.columns(3)
            c1.metric("Citizens shown", len(df_c))
            c2.metric("Avg Eco Score", f"{df_c['score_ecolo'].mean():.1f}" if "score_ecolo" in df_c else "—")
            c3.metric("Consultations", int(df_c["nb_consultations"].sum()) if "nb_consultations" in df_c else "—")

            st.markdown("<hr class='soft'>", unsafe_allow_html=True)

            # Bar chart colored by mobility (S1 pattern)
            if "score_ecolo" in df_c and "preference_mobilite" in df_c:
                df_sorted = df_c.sort_values("score_ecolo", ascending=False).head(30)
                fig_bar = px.bar(df_sorted,
                                 x="nom", y="score_ecolo",
                                 color="preference_mobilite",
                                 color_discrete_sequence=COLORS,
                                 labels={"score_ecolo":"Eco Score","nom":"Citizen",
                                         "preference_mobilite":"Mobility"},
                                 title="Ecological Score by Citizen (top 30)")
                T(fig_bar, h=320)
                fig_bar.update_layout(xaxis_tickangle=-40,
                                      legend=dict(orientation="h",y=-.25,x=0,font_size=10))
                st.plotly_chart(fig_bar, use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                fig_mob = px.pie(df_c, names="preference_mobilite", hole=0.45,
                                 color_discrete_sequence=COLORS,
                                 title="Mobility Preferences")
                T(fig_mob, h=250); st.plotly_chart(fig_mob, use_container_width=True)
            with col_b:
                fig_h = px.histogram(df_c, x="score_ecolo", nbins=15,
                                     color_discrete_sequence=[GREEN],
                                     labels={"score_ecolo":"Eco Score"},
                                     title="Score Distribution")
                T(fig_h, h=250); st.plotly_chart(fig_h, use_container_width=True)

            with st.expander("📋 Full Citizen Table"):
                show_cols = [c for c in ["nom","prenom","score_ecolo","preference_mobilite",
                                          "zone_nom","nb_consultations"] if c in df_c.columns]
                st.dataframe(df_c[show_cols], use_container_width=True, hide_index=True)