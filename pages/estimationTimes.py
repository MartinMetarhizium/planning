# app.py
import os
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
from datetime import timedelta
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Cycle Times (CSV)", page_icon="📄", layout="wide")

# ========= Config =========
DEFAULT_CSV = "cycle_times.csv"
CSV_PATH = os.getenv("CSV_PATH", DEFAULT_CSV)
AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")

st.title("📄 Visualizador de tiempos entre estados (desde CSV)")

# ========= Sidebar =========
st.sidebar.header("⚙️ Fuente de datos")
st.sidebar.write("El archivo se carga automáticamente desde disco.")
csv_override = st.sidebar.text_input("Ruta del CSV (opcional)", value=CSV_PATH)
uploaded = st.sidebar.file_uploader("…o subir un CSV distinto", type=["csv"])
reload_btn = st.sidebar.button("🔄 Recargar")

# ========= Carga de datos =========
@st.cache_data(show_spinner=False)
def load_csv_from_path(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

@st.cache_data(show_spinner=False)
def load_csv_from_bytes(file) -> pd.DataFrame:
    return pd.read_csv(file)

df_raw, error = None, None
try:
    if uploaded is not None:
        df_raw = load_csv_from_bytes(uploaded)
        source_label = f"Archivo subido: **{uploaded.name}**"
    else:
        path = csv_override.strip() or DEFAULT_CSV
        df_raw = load_csv_from_path(path)
        source_label = f"Archivo local: **{path}**"
except Exception as e:
    error = str(e)

if reload_btn:
    st.cache_data.clear()
    st.rerun()

if error:
    st.error(f"No se pudo leer el CSV. Detalle: {error}")
    st.stop()

st.caption(source_label)

# ========= Preparación =========
expected_cols = {"issueKey", "issueType", "assignee", "summary", "from_date", "to_date", "hours"}
missing = expected_cols - set(df_raw.columns)
if missing:
    st.error(f"El CSV debe contener las columnas: {sorted(expected_cols)}. Faltan: {sorted(missing)}")
    st.stop()

def parse_dt(s: str):
    return pd.to_datetime(s, format="%Y-%m-%dT%H:%M:%S.%f%z", errors="coerce")

df = df_raw.copy()
df["hours"] = pd.to_numeric(df["hours"], errors="coerce")
df["from_dt"] = df["from_date"].apply(parse_dt)
df["to_dt"] = df["to_date"].apply(parse_dt)
df["from_local"] = df["from_dt"].dt.tz_convert(AR_TZ)
df["to_local"] = df["to_dt"].dt.tz_convert(AR_TZ)
df["to_day"] = df["to_local"].dt.date
df["days"] = df["hours"] / 24.0

# ========= Filtros =========
st.sidebar.header("🔍 Filtros")

# Fecha
min_day, max_day = df["to_day"].min(), df["to_day"].max()
default_start = max_day - timedelta(days=30) if pd.notna(max_day) else None
date_sel = st.sidebar.date_input(
    "Rango por fecha de to_date",
    value=(default_start, max_day) if default_start else None,
    min_value=min_day if pd.notna(min_day) else None,
    max_value=max_day if pd.notna(max_day) else None,
)

# Horas
min_h = float(np.nan_to_num(df["hours"].min(), nan=0.0))
max_h = float(np.nan_to_num(df["hours"].max(), nan=0.0))
h_sel = st.sidebar.slider("Rango de horas", min_value=0.0, max_value=max(1.0, round(max_h + 0.5, 1)),
                          value=(0.0, max(1.0, round(max_h + 0.5, 1))), step=0.1)

# Texto
q = st.sidebar.text_input("Buscar en issueKey/summary", "").strip().lower()

# Nuevo: Filtros de asignado y tipo
assignees = sorted(df["assignee"].dropna().unique().tolist())
issue_types = sorted(df["issueType"].dropna().unique().tolist())

selected_assignees = st.sidebar.multiselect("Persona asignada", options=assignees, default=assignees)
selected_types = st.sidebar.multiselect("Tipo de tarea", options=issue_types, default=issue_types)

# Aplicar filtros
f = df.copy()
if isinstance(date_sel, (list, tuple)) and len(date_sel) == 2:
    a, b = date_sel
    if pd.notna(a) and pd.notna(b):
        f = f[(f["to_day"] >= a) & (f["to_day"] <= b)]
f = f[(f["hours"] >= h_sel[0]) & (f["hours"] <= h_sel[1])]
if q:
    f = f[f["issueKey"].str.lower().str.contains(q) | f["summary"].str.lower().str.contains(q)]
f = f[f["assignee"].isin(selected_assignees) & f["issueType"].isin(selected_types)]

# ========= KPIs =========
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Issues", len(f))
c2.metric("Promedio (h)", round(f["hours"].mean(), 2) if len(f) else 0)
c3.metric("Mediana (h)", round(f["hours"].median(), 2) if len(f) else 0)
c4.metric("P90 (h)", round(f["hours"].quantile(0.9), 2) if len(f) else 0)
c5.metric("Máximo (h)", round(f["hours"].max(), 2) if len(f) else 0)

st.markdown("---")

# ========= Gráficos =========
st.subheader("Distribución de horas")
hist = alt.Chart(f).mark_bar().encode(
    x=alt.X("hours:Q", bin=alt.Bin(maxbins=30), title="Horas"),
    y=alt.Y("count()", title="Cantidad"),
    tooltip=["count()"]
).properties(height=260)
st.altair_chart(hist, use_container_width=True)

st.subheader("Promedio por día (horas)")
daily = f.groupby("to_day", as_index=False)["hours"].mean().rename(columns={"hours": "avg_hours"})
line = alt.Chart(daily).mark_line(point=True).encode(
    x=alt.X("to_day:T", title="Fecha"),
    y=alt.Y("avg_hours:Q", title="Horas promedio"),
    tooltip=["to_day", "avg_hours"]
).properties(height=260)
st.altair_chart(line, use_container_width=True)

st.subheader("Promedio por día (días)")
daily_days = f.groupby("to_day", as_index=False)["days"].mean().rename(columns={"days": "avg_days"})
line_days = alt.Chart(daily_days).mark_line(point=True, color="green").encode(
    x=alt.X("to_day:T", title="Fecha"),
    y=alt.Y("avg_days:Q", title="Días promedio"),
    tooltip=["to_day", "avg_days"]
).properties(height=260)
st.altair_chart(line_days, use_container_width=True)

st.subheader("Horas promedio por persona asignada")
bar_assignee = alt.Chart(f).mark_bar().encode(
    x=alt.X("assignee:N", title="Persona"),
    y=alt.Y("hours:Q", aggregate="mean", title="Horas promedio"),
    color="assignee:N",
    tooltip=["assignee", "mean(hours)"]
).properties(height=300)
st.altair_chart(bar_assignee, use_container_width=True)

st.subheader("Horas promedio por tipo de tarea")
bar_type = alt.Chart(f).mark_bar().encode(
    x=alt.X("issueType:N", title="Tipo"),
    y=alt.Y("hours:Q", aggregate="mean", title="Horas promedio"),
    color="issueType:N",
    tooltip=["issueType", "mean(hours)"]
).properties(height=300)
st.altair_chart(bar_type, use_container_width=True)

st.markdown("---")

# ========= Tabla =========
st.subheader("Tabla (filtrada)")
show_cols = ["issueKey", "issueType", "assignee", "summary", "from_date", "to_date", "hours"]
st.dataframe(f[show_cols].reset_index(drop=True), use_container_width=True)

# ========= Descarga =========
st.download_button(
    "⬇️ Descargar CSV filtrado",
    data=f[show_cols].to_csv(index=False).encode("utf-8"),
    file_name="cycle_times_filtered.csv",
    mime="text/csv"
)
