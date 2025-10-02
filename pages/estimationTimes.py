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
CSV_PATH = os.getenv("CSV_PATH", DEFAULT_CSV)  # opcional: export CSV_PATH=/ruta/archivo.csv
AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")

st.title("📄 Visualizador de tiempos entre estados (desde CSV)")

# ========= Sidebar =========
st.sidebar.header("⚙️ Fuente de datos")
st.sidebar.write("El archivo se carga automáticamente desde disco.")
csv_override = st.sidebar.text_input("Ruta del CSV (opcional)", value=CSV_PATH, help="Dejá vacío para usar cycle_times.csv")
uploaded = st.sidebar.file_uploader("…o subir un CSV distinto", type=["csv"])
reload_btn = st.sidebar.button("🔄 Recargar")

# ========= Carga de datos =========
@st.cache_data(show_spinner=False)
def load_csv_from_path(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df

@st.cache_data(show_spinner=False)
def load_csv_from_bytes(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    return df

df_raw = None
error = None

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
    # Formato Jira: 2025-08-01T10:06:58.847-0300
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
min_day, max_day = df["to_day"].min(), df["to_day"].max()
default_start = max_day - timedelta(days=30) if pd.notna(max_day) else None
date_sel = st.sidebar.date_input(
    "Rango por fecha de to_date",
    value=(default_start, max_day) if default_start else None,
    min_value=min_day if pd.notna(min_day) else None,
    max_value=max_day if pd.notna(max_day) else None,
)

min_h = float(np.nan_to_num(df["hours"].min(), nan=0.0))
max_h = float(np.nan_to_num(df["hours"].max(), nan=0.0))
h_sel = st.sidebar.slider("Rango de horas", min_value=0.0, max_value=max(1.0, round(max_h + 0.5, 1)),
                          value=(0.0, max(1.0, round(max_h + 0.5, 1))), step=0.1)

q = st.sidebar.text_input("Buscar en issueKey/summary", "").strip().lower()

f = df.copy()
if isinstance(date_sel, (list, tuple)) and len(date_sel) == 2:
    a, b = date_sel
    if pd.notna(a) and pd.notna(b):
        f = f[(f["to_day"] >= a) & (f["to_day"] <= b)]
f = f[(f["hours"] >= h_sel[0]) & (f["hours"] <= h_sel[1])]
if q:
    f = f[f["issueKey"].str.lower().str.contains(q) | f["summary"].str.lower().str.contains(q)]

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
    y=alt.Y("count()", title="Cantidad")
).properties(height=260)
st.altair_chart(hist, use_container_width=True)

st.subheader("Promedio por día (to_date)")
daily = f.groupby("to_day", as_index=False)["hours"].mean().rename(columns={"hours": "avg_hours"})
line = alt.Chart(daily).mark_line(point=True).encode(
    x=alt.X("to_day:T", title="Fecha"),
    y=alt.Y("avg_hours:Q", title="Horas promedio")
).properties(height=260)
st.altair_chart(line, use_container_width=True)

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

st.caption("Sugerencia: definí CSV_PATH en el entorno para apuntar a otro archivo por defecto.")
