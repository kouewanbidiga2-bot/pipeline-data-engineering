"""
Dashboard Streamlit — Monitoring du Pipeline Data Engineering

Lancer avec : streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import json
import yaml

# Configuration de la page
st.set_page_config(
    page_title="Pipeline Data Engineering — Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre
st.title("📊 Pipeline Data Engineering — Dashboard")
st.markdown("Monitoring en temps réel du pipeline ETL")

# Sidebar
st.sidebar.header("Configuration")
config_path = st.sidebar.text_input("Fichier de config", "config.yaml")

# Fonctions de chargement
@st.cache_data(ttl=60)
def load_raw_data():
    """Charge les données brutes"""
    raw_path = Path("data/raw")
    if not raw_path.exists():
        return pd.DataFrame()
    csv_files = list(raw_path.glob("*.csv"))
    if not csv_files:
        return pd.DataFrame()
    dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            df['source_file'] = f.name
            dfs.append(df)
        except Exception:
            pass
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

@st.cache_data(ttl=60)
def load_logs():
    """Charge les logs d'exécution"""
    logs_path = Path("logs")
    if not logs_path.exists():
        return []
    log_files = sorted(logs_path.glob("*.log"), reverse=True)[:5]
    logs = []
    for f in log_files:
        try:
            with open(f, 'r') as fh:
                content = fh.read()
                logs.append({
                    'file': f.name,
                    'content': content,
                    'date': datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        except Exception:
            pass
    return logs

@st.cache_data(ttl=60)
def load_quality_results():
    """Charge les résultats de qualité"""
    results_path = Path("data/quality_results.json")
    if not results_path.exists():
        return {}
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

# Métriques principales
st.header("Métriques principales")

col1, col2, col3, col4 = st.columns(4)

with col1:
    raw_data = load_raw_data()
    st.metric("Lignes extraites", len(raw_data))

with col2:
    if not raw_data.empty and 'station' in raw_data.columns:
        st.metric("Stations", raw_data['station'].nunique())
    else:
        st.metric("Stations", "N/A")

with col3:
    if not raw_data.empty and 'consommation_kwh' in raw_data.columns:
        total_conso = raw_data['consommation_kwh'].sum()
        st.metric("Consommation totale", f"{total_conso:,.0f} kWh")
    else:
        st.metric("Consommation", "N/A")

with col4:
    if not raw_data.empty and 'date' in raw_data.columns:
        date_range = f"{raw_data['date'].min()} à {raw_data['date'].max()}"
        st.metric("Période", date_range)
    else:
        st.metric("Période", "N/A")

# Graphiques
st.header("Visualisations")

if not raw_data.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Consommation par station")
        if 'station' in raw_data.columns and 'consommation_kwh' in raw_data.columns:
            fig = px.bar(
                raw_data.groupby('station')['consommation_kwh'].sum().reset_index(),
                x='station',
                y='consommation_kwh',
                title="Consommation totale par station (kWh)",
                color='station'
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Niveau d'eau moyen")
        if 'station' in raw_data.columns and 'niveau_eau' in raw_data.columns:
            fig = px.line(
                raw_data.groupby('date')['niveau_eau'].mean().reset_index(),
                x='date',
                y='niveau_eau',
                title="Niveau d'eau moyen dans le temps"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Tableau des données
    st.subheader("Données brutes")
    st.dataframe(raw_data, use_container_width=True)

    # Export
    st.subheader("Export")
    csv = raw_data.to_csv(index=False)
    st.download_button(
        label="Télécharger en CSV",
        data=csv,
        file_name="donnees_pipeline.csv",
        mime="text/csv"
    )
else:
    st.warning("Aucune donnée trouvée. Lancez le pipeline d'abord avec `make run`.")

# Logs
st.header("Logs d'exécution")
logs = load_logs()
if logs:
    selected_log = st.selectbox("Sélectionner un log", [l['file'] for l in logs])
    for log in logs:
        if log['file'] == selected_log:
            st.text(f"Dernière modification : {log['date']}")
            st.code(log['content'], language='log')
            break
else:
    st.info("Aucun log disponible. Les logs apparaîtront après la première exécution du pipeline.")

# Qualité des données
st.header("Qualité des données")
quality = load_quality_results()
if quality:
    for table, metrics in quality.items():
        st.subheader(f"Table: {table}")
        cols = st.columns(len(metrics))
        for idx, (metric, result) in enumerate(metrics.items()):
            with cols[idx]:
                status = "✓" if result.get('passed', False) else "✗"
                st.metric(
                    label=f"{status} {metric}",
                    value=result.get('value', 'N/A'),
                    delta=f"Seuil: {result.get('threshold', 'N/A')}"
                )
else:
    st.info("Aucun résultat de qualité disponible.")

# Footer
st.sidebar.markdown("---")
st.sidebar.info(
    "Pipeline Data Engineering\n"
    "BIDIGA Imrane — 2026\n\n"
    "Lancer le pipeline : `make run`"
)
