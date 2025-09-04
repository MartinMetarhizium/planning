import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
from constants import MIN_PROJECT_RATIO, DAILY_HOURS, PROJECT_MAP_BT, PROJECT_MAP, DEFAULT_END_DATE, DEFAULT_END_DATE_with_timezone, DEFAULT_START_DATE,DEFAULT_START_DATE_with_timezone
from streamlit_javascript import st_javascript

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(layout="wide")
with open("planificacion.json") as f:
    data = json.load(f)
df = pd.DataFrame(data)

theme = st_javascript("""window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';""")
if not theme:

    theme = 'light'
# ---------- ESTILOS ----------
st.markdown("""
    <style>
    body, .stApp {
        background-color: white !important;
        color: black !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* ===== Títulos de filtros en dark mode (Developer, Área, Épica, Hasta fecha) ===== */
@media (prefers-color-scheme: dark){

  /* 1) Forzar color y opacidad del contenedor de label */
  .stApp [data-testid="stWidgetLabel"]{
    color:#0f172a !important;
    opacity:1 !important;
  }

  /* 2) Forzar color/opacity de los nodos internos habituales */
  .stApp [data-testid="stWidgetLabel"] > div > p,
  .stApp [data-testid="stWidgetLabel"] > label,
  .stApp [data-testid="stWidgetLabel"] p,
  .stApp [data-testid="stWidgetLabel"] label{
    color:#0f172a !important;
    opacity:1 !important;
  }

  /* 3) Por si Streamlit usa <label for="..."> suelto */
  .stApp label[for^=""]{
    color:#0f172a !important;
    opacity:1 !important;
  }
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* ====== 1) Forzar tema claro SIEMPRE, aunque el browser esté en dark ====== */
:root { color-scheme: light !important; }
html, body, .stApp { background:#ffffff !important; }
/* ===== Fuente global Montserrat ===== */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap');

html, body, .stApp, div, span, label, section, p, h1, h2, h3, h4, h5, h6 {
    font-family: 'Montserrat', sans-serif !important;
}
/* ====== Forzar light mode ====== */
:root { color-scheme: light !important; }
html, body, .stApp { background: #ffffff !important; color: #111 !important; }

/* ====== Multiselect tags (chips) ======
   Reemplaza el rojo por azul en las etiquetas seleccionadas */
.stApp [data-baseweb="tag"] {
    background-color: #1976d2 !important;   /* azul */
    border-color: #1976d2 !important;
    color: #fff !important;
}
.stApp [data-baseweb="tag"] span { color: #fff !important; }
.stApp [data-baseweb="tag"] svg { fill: #fff !important; }
.stApp [data-baseweb="tag"]:hover {
    background-color: #1565c0 !important;   /* hover azul más oscuro */
    border-color: #1565c0 !important;
}

/* Borde/focus del contenedor del select a azul */
.stApp div[data-baseweb="select"] div[role="combobox"] {
    border-color: #1976d2 !important;
    box-shadow: 0 0 0 1px #1976d2 !important;
}

/* Radios / checkboxes (el “tick” rojo por defecto) */
.stApp input[type="radio"],
.stApp input[type="checkbox"] {
    accent-color: #1976d2 !important;
}

/* Botones primarios en azul */
.stApp .stButton button {
    background-color: #1976d2 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px;
}
.stApp .stButton button:hover { background-color: #1565c0 !important; }

/* Tus badges personalizados a azul (si los usás) */
.badge, .badge2525 { background-color: #1976d2 !important; }
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* === Radios y checkboxes en azul === */
.stApp input[type="radio"],
.stApp input[type="checkbox"] {
    accent-color: #1976d2 !important;   /* azul */
}

/* También cambiar el circulito rojo del radio seleccionado */
.stApp div[role="radiogroup"] > label > div:first-child {
    background-color: #1976d2 !important;   /* azul relleno */
    border-color: #1976d2 !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
div.block-container{max-width:1400px; padding-top:12px;}

/* KPIs */
.kpi-card{ display:flex; align-items:center; gap:14px; min-height:86px; }
.kpi-ico{ font-size:22px; background:#eaf2fd; color:#1976d2; width:44px; height:44px; border-radius:12px;
          display:flex; align-items:center; justify-content:center; flex:0 0 44px; }
.kpi-text h3{ margin:0; font-size:22px; line-height:1.1; font-weight:700; color:#0f172a; }
.kpi-text p{ margin:0; font-size:13px; color:#64748b; }

/* Títulos de bloque */
.block-title{ display:flex; align-items:center; gap:8px; font-weight:700; color:#0f172a; margin-bottom:10px; }
.block-title .dot{ width:18px; height:18px; border-radius:6px; background:#eaf2fd; display:inline-flex;
                   align-items:center; justify-content:center; color:#1976d2; }

/* Tabla compacta */
.table-wrap{ max-height:min(48vh,520px); overflow:auto; border:1px solid #eef2f7; border-radius:10px; position:relative; z-index:2; }
.table-wrap table{ width:100%; border-collapse:separate; border-spacing:0; font-size:13px; }
.table-wrap thead th{ position:sticky; top:0; z-index:3; background:rgba(248,250,252,.92)!important;
                      color:#334155!important; font-size:12px; border-bottom:1px solid #e2e8f0; }
.table-wrap tbody tr:nth-child(odd) td{ background:rgba(255,255,255,.55)!important; }

/* Pills estado */
.status-pill{ display:inline-flex; align-items:center; gap:6px; padding:2px 8px; border-radius:999px;
              font-size:12px; border:1px solid #e2e8f0; white-space:nowrap; }
.status-ok{ background:#ecfdf5; color:#047857; border-color:#a7f3d0; }
.status-warn{ background:#fff7ed; color:#c2410c; border-color:#fed7aa; }
.status-bad{ background:#fef2f2; color:#b91c1c; border-color:#fecaca; }
.dot-s{ width:8px; height:8px; border-radius:999px; background:currentColor; display:inline-block; }

/* Charts */
.chart-title{ display:flex; align-items:center; gap:8px; font-weight:700; color:#0f172a; margin:4px 0 12px; }
.chart-title .dot{ width:18px; height:18px; border-radius:6px; background:#eaf2fd; display:inline-flex;
                   align-items:center; justify-content:center; color:#1976d2; }

/* Panel de fondo aplicado al contenedor con sentinel */
:root{
  --panel-bg:#f7faff;      /* azul muy suave */
  --panel-br:#dbeafe;      /* borde celeste */
  --panel-shadow:0 8px 24px rgba(25,118,210,.08);
}
.block-container div:has(> .panel-sentinel){
  position:relative; padding:18px 20px; border-radius:14px; margin-bottom:18px;
}
.block-container div:has(> .panel-sentinel)::before{
  content:""; position:absolute; inset:0; background:var(--panel-bg);
  border:1px solid var(--panel-br); border-radius:14px; box-shadow:var(--panel-shadow); z-index:0;
}
.block-container div:has(> .panel-sentinel) > *{ position:relative; z-index:1; }

/* Selects transparentes para que se vea el panel detrás */
.stApp [data-baseweb="select"] > div{ background:transparent!important; }
.stApp [data-baseweb="select"] div[role="combobox"]{
  background:transparent!important; box-shadow:0 0 0 1px var(--panel-br)!important; border-color:var(--panel-br)!important;
}
.stApp div[data-baseweb="select"] div[role="combobox"]:focus-within{
  border-color:#1976d2!important; box-shadow:0 0 0 1px #1976d2!important;
}

/* Responsive */
@media (max-width:1100px){ .hide-on-narrow{ display:none; } }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
/* ===== Fix filtros cuando el navegador está en oscuro ===== */
@media (prefers-color-scheme: dark){
  /* Multiselect / Select (BaseWeb) */
  .stApp [data-baseweb="select"] > div,
  .stApp [data-baseweb="select"] div[role="combobox"]{
    background:#ffffff !important;
    color:#0f172a !important;
    box-shadow:0 0 0 1px #dbeafe !important;
    border-color:#dbeafe !important;
  }

  /* Chips siguen en azul */
  .stApp [data-baseweb="tag"]{
    background-color:#1976d2 !important;
    border-color:#1976d2 !important;
    color:#ffffff !important;
  }

  /* Date input (contenedor + input) */
  .stApp [data-testid="stDateInput"] > div > div,
  .stApp [data-testid="stDateInput"] input{
    background:#ffffff !important;
    color:#0f172a !important;
    box-shadow:0 0 0 1px #dbeafe !important;
    border:1px solid #dbeafe !important;
  }

  /* Placeholder del date input */
  .stApp [data-testid="stDateInput"] input::placeholder{
    color:#475569 !important;
    opacity:1 !important;
  }

  /* Íconos dentro de los selects (chevron/clear) mejor contraste */
  .stApp [data-baseweb="select"] svg{
    opacity:0.8 !important;
  }
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* ===== Labels de filtros en dark mode (Developer, Área, Épica, Hasta fecha) ===== */
@media (prefers-color-scheme: dark){
  /* Limito el cambio al contenedor que usa el sentinel (tu panel de filtros) */
  .block-container div:has(> .panel-sentinel) label{
    color:#0f172a !important;        /* texto bien oscuro sobre fondo blanco */
  }

  /* En algunas versiones, la etiqueta es un <p> interno: cúbrelo también */
  .block-container div:has(> .panel-sentinel) [data-testid="stWidgetLabel"] p{
    color:#0f172a !important;
  }

  /* Por si el label cae dentro de wrappers distintos (select/date) */
  .block-container div:has(> .panel-sentinel) [data-baseweb="select"] label,
  .block-container div:has(> .panel-sentinel) [data-testid="stDateInput"] label{
    color:#0f172a !important;
  }
}
            
.table-wrap thead th{
  text-align:center !important;
  vertical-align:middle !important;
}

/* si alguna vez hay varias filas de header, centramos solo la primera */
.table-wrap thead tr:first-child th{
  text-align:center !important;
  vertical-align:middle !important;
}
</style>
""", unsafe_allow_html=True)


# ---------- FECHAS BASE ----------
_hoy = pd.Timestamp.today().normalize()
DEFAULT_END = pd.to_datetime(DEFAULT_END_DATE, errors="coerce") if 'DEFAULT_END_DATE' in globals() else _hoy

# ---------- ENCABEZADO + KPIs (placeholders) ----------
with st.container():
    st.markdown('<span class="panel-sentinel"></span>', unsafe_allow_html=True)
    st.markdown("### Planificación de Desarrolladores")

    st.caption("Visualización de carga, progreso y vencimientos de proyectos")

    k0, k1, k2, k3 = st.columns(4)  # ← ahora 4 columnas
    k0_box = k0.empty()             # ← NUEVA: horas totales
    k1_box = k1.empty()             # horas vencidas (tu KPI actual)
    k2_box = k2.empty()
    k3_box = k3.empty()

# ---------- GRID PRINCIPAL (filtros + tabla/charts) ----------
# (quitamos las columnas y mostramos los filtros arriba de la tabla)
with st.container():
    st.markdown('<span class="panel-sentinel"></span>', unsafe_allow_html=True)
    st.markdown('<div class="block-title"><span class="dot">📂</span> Filtros</div>', unsafe_allow_html=True)

    # Opciones ordenadas (case-insensitive)
    _devs_dash = sorted(df["developer"].dropna().unique(), key=str.casefold)
    _areas_col = "cf10209" if "cf10209" in df.columns else None
    _areas_dash = sorted(df[_areas_col].dropna().unique(), key=str.casefold) if _areas_col else []
    _epic_options = sorted(df["epic_name"].fillna("— Sin épica —").unique(), key=str.casefold)

    # Sentinels para "seleccionar todo"
    dev_opts  = ["(Todos)"] + _devs_dash
    area_opts = (["(Todas)"] + _areas_dash) if _areas_col else []
    epic_opts = ["(Todas)"] + _epic_options

    # Layout en columnas
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1.6, 1.0, 1.1])

    with c1:
        dash_dev = st.multiselect(
            "Developer",
            dev_opts,
            default=["(Todos)"],           # ← todos por defecto
            key="dash_dev"
        )

    with c2:
        dash_area = st.multiselect(
            "Área",
            area_opts,
            default=area_opts[:1] if area_opts else [],  # "(Todas)" si existe
            key="dash_area"
        ) if _areas_col else []

    with c3:
        dash_epic = st.multiselect(
            "Epic",
            epic_opts,
            default=["(Todas)"],
            key="dash_epic"
        )

    with c4:
        _cutoff_default = (pd.to_datetime(DEFAULT_END_DATE).date()
                           if 'DEFAULT_END_DATE' in globals() else pd.Timestamp.today().date())
        cutoff_date = st.date_input("Hasta fecha", value=_cutoff_default, key="dash_cutoff")


    with c5:
      entrega_opts = ["(Todas)", "En plazo", "Se entrega vencido"]
      dash_entrega = st.multiselect("Entrega", entrega_opts, default=["(Todas)"], key="dash_entrega")

# ---------- APLICAR FILTROS GLOBALES ----------
# Resolver selección efectiva según sentinel "(Todos)/(Todas)"
_sel_dev  = _devs_dash if ("(Todos)" in dash_dev or not dash_dev) else [x for x in dash_dev if x != "(Todos)"]
_sel_epic = _epic_options if ("(Todas)" in dash_epic or not dash_epic) else [x for x in dash_epic if x != "(Todas)"]
if _areas_col:
    _sel_area = _areas_dash if (not dash_area or "(Todas)" in dash_area) else [x for x in dash_area if x != "(Todas)"]

# Aplicar
_mask_base = df["developer"].isin(_sel_dev)
if _areas_col and _areas_dash:
    _mask_base &= df[_areas_col].isin(_sel_area)
_mask_base &= df["epic_name"].fillna("— Sin épica —").isin(_sel_epic)

df_base = df[_mask_base].copy()

_end_dt = pd.to_datetime(df_base["end"], errors="coerce")
_due_dt = pd.to_datetime(df_base["due_date"], errors="coerce")
_ok_series = _end_dt <= _due_dt                      # False si falta end/due_date
_venc_series = df_base["vencida"].fillna(False) if "vencida" in df_base.columns else False

df_base["entrega_status"] = "En plazo"
df_base.loc[(~_ok_series) | (_venc_series), "entrega_status"] = "Se entrega vencido"

# === Aplicar filtro "Entrega" si corresponde ===
if "(Todas)" not in dash_entrega and len(dash_entrega) > 0:
    df_base = df_base[df_base["entrega_status"].isin(dash_entrega)]

# ---------- KPIs (respetan ÉPICA; 'vencidas' usa FECHA seleccionada) ----------
cutoff_ts = pd.to_datetime(cutoff_date)
_kpi_df = df_base[(df_base["type"] != "reunion") & (pd.to_datetime(df_base["due_date"]) < cutoff_ts)]
horas_vencidas_top = float(_kpi_df["duration_hours"].sum()) if not _kpi_df.empty else 0.0



_kpi_df_all = df_base[
    (df_base["type"] != "reunion") 
    # & (pd.to_datetime(df_base["due_date"]) <= cutoff_ts)
]
horas_totales_top = float(_kpi_df_all["duration_hours"].sum()) if not _kpi_df_all.empty else 0.0


proyectos_activos = int(
    df_base.loc[df_base["has_epic"] == True, "epic_name"]
          .replace("— Sin épica —", pd.NA).dropna().nunique()
)
developers_totales = int(df_base["developer"].dropna().nunique())

# Render KPIs (mantenemos tu lógica actual con los placeholders k1_box/k2_box/k3_box)
k0_box.markdown(f"""
<div class="kpi-card">
  <div class="kpi-ico">⏱️</div>
  <div class="kpi-text">
    <h3>{horas_totales_top:.0f} h totales</h3>
    <p>Hasta el {cutoff_date.strftime('%d-%b-%y')}</p>
  </div>
</div>""", unsafe_allow_html=True)


k1_box.markdown(f"""
<div class="kpi-card">
  <div class="kpi-ico">⏱️</div>
  <div class="kpi-text">
    <h3>{horas_vencidas_top:.0f} h vencidas</h3>
    <p>Hasta el {cutoff_date.strftime('%d-%b-%y')}</p>
  </div>
</div>""", unsafe_allow_html=True)

k2_box.markdown(f"""
<div class="kpi-card">
  <div class="kpi-ico">📦</div>
  <div class="kpi-text">
    <h3>{proyectos_activos}</h3>
    <p>Proyectos activos</p>
  </div>
</div>""", unsafe_allow_html=True)

k3_box.markdown(f"""
<div class="kpi-card">
  <div class="kpi-ico">👥</div>
  <div class="kpi-text">
    <h3>{developers_totales}</h3>
    <p>Developers</p>
  </div>
</div>""", unsafe_allow_html=True)

# ---- TABLA + CHARTS (con filtros arriba) ----
st.markdown('<span class="panel-sentinel"></span>', unsafe_allow_html=True)
st.markdown('<div class="block-title"><span class="dot">🗂️</span> Tareas planificadas por desarrollador</div>', unsafe_allow_html=True)

# Subset tablero (ya con filtros dev/área/épica aplicados)
tablero_df = (
    df_base[df_base["type"] != "reunion"].copy()
    .assign(_Estado=lambda d: pd.to_datetime(d["end"]) <= pd.to_datetime(d["due_date"]))
)
test = tablero_df.copy()

# ====== TABLA: AGREGO "Desarrollador" (faltante) ======
mini_cols = [c for c in ["developer","summary","epic_name","due_date","_Estado","vencida"] if c in tablero_df.columns]
tabla_compacta = (
    tablero_df.sort_values("due_date", na_position="last")[mini_cols]
              .rename(columns={"developer":"Desarrollador","summary":"Resumen","epic_name":"Proyecto",
                               "due_date":"Vencimiento","_Estado":"Estado"})
)

def _estado_pill(ok, vencida):
    if pd.isna(ok):
        return '<span class="status-pill status-warn"><span class="dot-s"></span> Se entrega vencido</span>'
    if (not bool(ok)) or bool(vencida):
        return '<span class="status-pill status-bad"><span class="dot-s"></span> Se entrega vencido</span>'
    return '<span class="status-pill status-ok"><span class="dot-s"></span> En plazo</span>'

if not tabla_compacta.empty:
    _t = tabla_compacta.copy()
    _t["Vencimiento"] = pd.to_datetime(_t["Vencimiento"]).dt.strftime("%d-%b-%y")
    _t["Estado"] = [_estado_pill(ok=row.get("Estado"), vencida=row.get("vencida", False))
                    for _, row in _t.iterrows()]
    if "vencida" in _t.columns:
        _t = _t.drop(columns=["vencida"])
    html_tabla = _t.to_html(escape=False, index=False)
    st.markdown(f'<div class="table-wrap">{html_tabla}</div>', unsafe_allow_html=True)
else:
    st.info("No hay tareas con los filtros seleccionados.")

    # CHARTS fila inferior
    c_bar, c_pie = st.columns([1.6, 1])
    with c_bar:
        st.markdown('<div class="block-title chart-title"><span class="dot">📊</span> Horas por Developer</div>', unsafe_allow_html=True)
        _bars = (test.groupby("developer")["duration_hours"].sum().sort_values(ascending=True))
        if not _bars.empty:
            fig, ax = plt.subplots(figsize=(7.0, 3.2), dpi=120)
            ax.barh(_bars.index, _bars.values)
            ax.set_xlabel("Horas", fontsize=9); ax.set_ylabel("")
            ax.tick_params(axis="both", labelsize=9)
            for s in ["top","right"]: ax.spines[s].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
        else:
            st.caption("Sin datos para graficar.")

    with c_pie:
        st.markdown('<div class="block-title chart-title"><span class="dot">🧩</span> Tareas con/sin épica</div>', unsafe_allow_html=True)
        # Donut: mantiene ventana por DEFAULT_END (no por cutoff_date)
        end_s = pd.to_datetime(tablero_df["end"], errors="coerce")
        window_df = tablero_df[end_s.notna() & (end_s.dt.date <= pd.to_datetime(DEFAULT_END).date())].copy()
        _counts = window_df["has_epic"].fillna(False).value_counts()
        tot = int(_counts.sum()); con = int(_counts.get(True, 0)); sin = int(_counts.get(False, 0))
        pct = (con / tot * 100) if tot else 0
        st.markdown(f"<div style='font-size:22px;font-weight:700;color:#0f172a;margin:-2px 0 8px;'>Con épica {pct:.0f}%</div>",
                    unsafe_allow_html=True)
        if tot > 0:
            fig, ax = plt.subplots(figsize=(4.6, 3.2), dpi=120)
            ax.pie([con, sin], labels=["Con épica","Sin épica"], autopct="%1.0f%%", startangle=90,
                   textprops={"fontsize":9})
            centre = plt.Circle((0, 0), 0.55, fc="white"); fig.gca().add_artist(centre)
            ax.axis("equal"); plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
        else:
            st.caption("Sin datos para graficar (hasta la fecha límite).")
# ===================== FIN DASHBOARD SUPERIOR (optimizado) =====================















st.set_page_config(layout="wide")
with open("planificacion_bt.json") as f:
    data_bt = json.load(f)
df_bt = pd.DataFrame(data_bt)



# ---------- ENCABEZADO + KPIs (placeholders) ----------
with st.container():
    st.markdown('<span class="panel-sentinel"></span>', unsafe_allow_html=True)
    st.markdown("### Planificación de Analistas")

    st.caption("Visualización de carga, progreso y vencimientos de proyectos")

    k0, k1, k2, k3 = st.columns(4)  # ← ahora 4 columnas
    k0_box = k0.empty()             # ← NUEVA: horas totales
    k1_box = k1.empty()             # horas vencidas (tu KPI actual)
    k2_box = k2.empty()
    k3_box = k3.empty()

# ---------- GRID PRINCIPAL (filtros + tabla/charts) ----------
# (quitamos las columnas y mostramos los filtros arriba de la tabla)
with st.container():
    st.markdown('<span class="panel-sentinel"></span>', unsafe_allow_html=True)
    st.markdown('<div class="block-title"><span class="dot">📂</span> Filtros</div>', unsafe_allow_html=True)

    # Opciones ordenadas (case-insensitive)
    _devs_dash = sorted(df_bt["developer"].dropna().unique(), key=str.casefold)
    _areas_col = "cf10209" if "cf10209" in df.columns else None
    _areas_dash = sorted(df_bt[_areas_col].dropna().unique(), key=str.casefold) if _areas_col else []
    _epic_options = sorted(df_bt["epic_name"].fillna("— Sin épica —").unique(), key=str.casefold)

    # Sentinels para "seleccionar todo"
    dev_opts  = ["(Todos)"] + _devs_dash
    area_opts = (["(Todas)"] + _areas_dash) if _areas_col else []
    epic_opts = ["(Todas)"] + _epic_options

    # Layout en columnas
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1.6, 1.0, 1.1])

    with c1:
        dash_bt = st.multiselect(
            "Developer",
            dev_opts,
            default=["(Todos)"],           # ← todos por defecto
            key="dash_bt"
        )

    with c2:
        dash_area_bt = st.multiselect(
            "Área",
            area_opts,
            default=area_opts[:1] if area_opts else [],  # "(Todas)" si existe
            key="dash_area_bt"
        ) if _areas_col else []

    with c3:
        dash_epic_bt = st.multiselect(
            "Epic",
            epic_opts,
            default=["(Todas)"],
            key="dash_epic_bt"
        )

    with c4:
        _cutoff_default = (pd.to_datetime(DEFAULT_END_DATE).date()
                           if 'DEFAULT_END_DATE' in globals() else pd.Timestamp.today().date())
        cutoff_date = st.date_input("Hasta fecha", value=_cutoff_default, key="dash_cutoff_bt")


    with c5:
      entrega_opts = ["(Todas)", "En plazo", "Se entrega vencido"]
      dash_entrega = st.multiselect("Entrega", entrega_opts, default=["(Todas)"], key="dash_entrega_bt")

# ---------- APLICAR FILTROS GLOBALES ----------
# Resolver selección efectiva según sentinel "(Todos)/(Todas)"
_sel_dev  = _devs_dash if ("(Todos)" in dash_bt or not dash_bt) else [x for x in dash_bt if x != "(Todos)"]
_sel_epic = _epic_options if ("(Todas)" in dash_epic_bt or not dash_epic_bt) else [x for x in dash_epic_bt if x != "(Todas)"]
if _areas_col:
    _sel_area = _areas_dash if (not dash_area_bt or "(Todas)" in dash_area_bt) else [x for x in dash_area_bt if x != "(Todas)"]

# Aplicar
_mask_base = df_bt["developer"].isin(_sel_dev)
if _areas_col and _areas_dash:
    _mask_base &= df_bt[_areas_col].isin(_sel_area)
_mask_base &= df_bt["epic_name"].fillna("— Sin épica —").isin(_sel_epic)

df_base = df_bt[_mask_base].copy()

_end_dt = pd.to_datetime(df_base["end"], errors="coerce")
_due_dt = pd.to_datetime(df_base["due_date"], errors="coerce")
_ok_series = _end_dt <= _due_dt                      # False si falta end/due_date
_venc_series = df_base["vencida"].fillna(False) if "vencida" in df_base.columns else False

df_base["entrega_status"] = "En plazo"
df_base.loc[(~_ok_series) | (_venc_series), "entrega_status"] = "Se entrega vencido"

# === Aplicar filtro "Entrega" si corresponde ===
if "(Todas)" not in dash_entrega and len(dash_entrega) > 0:
    df_base = df_base[df_base["entrega_status"].isin(dash_entrega)]

# ---------- KPIs (respetan ÉPICA; 'vencidas' usa FECHA seleccionada) ----------
cutoff_ts = pd.to_datetime(cutoff_date)
_kpi_df = df_base[(df_base["type"] != "reunion") & (pd.to_datetime(df_base["due_date"]) < cutoff_ts)]
horas_vencidas_top = float(_kpi_df["duration_hours"].sum()) if not _kpi_df.empty else 0.0



_kpi_df_all = df_base[
    (df_base["type"] != "reunion") 
    # & (pd.to_datetime(df_base["due_date"]) <= cutoff_ts)
]
horas_totales_top = float(_kpi_df_all["duration_hours"].sum()) if not _kpi_df_all.empty else 0.0


proyectos_activos = int(
    df_base.loc[df_base["has_epic"] == True, "epic_name"]
          .replace("— Sin épica —", pd.NA).dropna().nunique()
)
developers_totales = int(df_base["developer"].dropna().nunique())

# Render KPIs (mantenemos tu lógica actual con los placeholders k1_box/k2_box/k3_box)
k0_box.markdown(f"""
<div class="kpi-card">
  <div class="kpi-ico">⏱️</div>
  <div class="kpi-text">
    <h3>{horas_totales_top:.0f} h totales</h3>
    <p>Hasta el {cutoff_date.strftime('%d-%b-%y')}</p>
  </div>
</div>""", unsafe_allow_html=True)


k1_box.markdown(f"""
<div class="kpi-card">
  <div class="kpi-ico">⏱️</div>
  <div class="kpi-text">
    <h3>{horas_vencidas_top:.0f} h vencidas</h3>
    <p>Hasta el {cutoff_date.strftime('%d-%b-%y')}</p>
  </div>
</div>""", unsafe_allow_html=True)

k2_box.markdown(f"""
<div class="kpi-card">
  <div class="kpi-ico">📦</div>
  <div class="kpi-text">
    <h3>{proyectos_activos}</h3>
    <p>Proyectos activos</p>
  </div>
</div>""", unsafe_allow_html=True)

k3_box.markdown(f"""
<div class="kpi-card">
  <div class="kpi-ico">👥</div>
  <div class="kpi-text">
    <h3>{developers_totales}</h3>
    <p>Developers</p>
  </div>
</div>""", unsafe_allow_html=True)

# ---- TABLA + CHARTS (con filtros arriba) ----
st.markdown('<span class="panel-sentinel"></span>', unsafe_allow_html=True)
st.markdown('<div class="block-title"><span class="dot">🗂️</span> Tareas planificadas por desarrollador</div>', unsafe_allow_html=True)

# Subset tablero (ya con filtros dev/área/épica aplicados)
tablero_df = (
    df_base[df_base["type"] != "reunion"].copy()
    .assign(_Estado=lambda d: pd.to_datetime(d["end"]) <= pd.to_datetime(d["due_date"]))
)
test = tablero_df.copy()

# ====== TABLA: AGREGO "Desarrollador" (faltante) ======
mini_cols = [c for c in ["developer","summary","epic_name","due_date","_Estado","vencida"] if c in tablero_df.columns]
tabla_compacta = (
    tablero_df.sort_values("due_date", na_position="last")[mini_cols]
              .rename(columns={"developer":"Desarrollador","summary":"Resumen","epic_name":"Proyecto",
                               "due_date":"Vencimiento","_Estado":"Estado"})
)

def _estado_pill(ok, vencida):
    if pd.isna(ok):
        return '<span class="status-pill status-warn"><span class="dot-s"></span> Se entrega vencido</span>'
    if (not bool(ok)) or bool(vencida):
        return '<span class="status-pill status-bad"><span class="dot-s"></span> Se entrega vencido</span>'
    return '<span class="status-pill status-ok"><span class="dot-s"></span> En plazo</span>'

if not tabla_compacta.empty:
    _t = tabla_compacta.copy()
    _t["Vencimiento"] = pd.to_datetime(_t["Vencimiento"]).dt.strftime("%d-%b-%y")
    _t["Estado"] = [_estado_pill(ok=row.get("Estado"), vencida=row.get("vencida", False))
                    for _, row in _t.iterrows()]
    if "vencida" in _t.columns:
        _t = _t.drop(columns=["vencida"])
    html_tabla = _t.to_html(escape=False, index=False)
    st.markdown(f'<div class="table-wrap">{html_tabla}</div>', unsafe_allow_html=True)
else:
    st.info("No hay tareas con los filtros seleccionados.")

    # CHARTS fila inferior
    c_bar, c_pie = st.columns([1.6, 1])
    with c_bar:
        st.markdown('<div class="block-title chart-title"><span class="dot">📊</span> Horas por Developer</div>', unsafe_allow_html=True)
        _bars = (test.groupby("developer")["duration_hours"].sum().sort_values(ascending=True))
        if not _bars.empty:
            fig, ax = plt.subplots(figsize=(7.0, 3.2), dpi=120)
            ax.barh(_bars.index, _bars.values)
            ax.set_xlabel("Horas", fontsize=9); ax.set_ylabel("")
            ax.tick_params(axis="both", labelsize=9)
            for s in ["top","right"]: ax.spines[s].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
        else:
            st.caption("Sin datos para graficar.")

    with c_pie:
        st.markdown('<div class="block-title chart-title"><span class="dot">🧩</span> Tareas con/sin épica</div>', unsafe_allow_html=True)
        # Donut: mantiene ventana por DEFAULT_END (no por cutoff_date)
        end_s = pd.to_datetime(tablero_df["end"], errors="coerce")
        window_df = tablero_df[end_s.notna() & (end_s.dt.date <= pd.to_datetime(DEFAULT_END).date())].copy()
        _counts = window_df["has_epic"].fillna(False).value_counts()
        tot = int(_counts.sum()); con = int(_counts.get(True, 0)); sin = int(_counts.get(False, 0))
        pct = (con / tot * 100) if tot else 0
        st.markdown(f"<div style='font-size:22px;font-weight:700;color:#0f172a;margin:-2px 0 8px;'>Con épica {pct:.0f}%</div>",
                    unsafe_allow_html=True)
        if tot > 0:
            fig, ax = plt.subplots(figsize=(4.6, 3.2), dpi=120)
            ax.pie([con, sin], labels=["Con épica","Sin épica"], autopct="%1.0f%%", startangle=90,
                   textprops={"fontsize":9})
            centre = plt.Circle((0, 0), 0.55, fc="white"); fig.gca().add_artist(centre)
            ax.axis("equal"); plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
        else:
            st.caption("Sin datos para graficar (hasta la fecha límite).")
# ===================== FIN DASHBOARD SUPERIOR (optimizado) =====================

