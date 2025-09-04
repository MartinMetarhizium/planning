import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
from constants import MIN_PROJECT_RATIO, DAILY_HOURS, PROJECT_MAP_BT, PROJECT_MAP, DEFAULT_END_DATE, DEFAULT_END_DATE_with_timezone, DEFAULT_START_DATE,DEFAULT_START_DATE_with_timezone
from streamlit_javascript import st_javascript

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
theme = st_javascript("""window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';""")
if not theme:

    theme = 'light'
def highlight_vencidas(row):        
    
    if row["Vencida"]:
        if theme != 'light':
            return ['background-color: #d1ab8e'] * len(row)
        return ['background-color: #fff9c4'] * len(row)
    
    if "type" in row and row["type"] == "reunion":
        return [''] * len(row)
    return [''] * len(row)


st.set_page_config(layout="wide")

st.title("📅 Planificación de Desarrolladores")
st.markdown("Este panel permite visualizar la carga de trabajo de los desarrolladores, el estado de sus tareas (con o sin épica), así como el progreso y vencimientos de proyectos.")



with open("planificacion.json") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Parseo de fechas
df["start"] = pd.to_datetime(df["start"], errors="coerce", format='mixed')
df["end"] = pd.to_datetime(df["end"], errors="coerce")
df["día"] = df["start"].dt.date
df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce", format='mixed')
df["note"] = df.get("note", "").fillna("").astype(str)

# Vencida parcial: si cualquier slot termina después del due_date (excluye reuniones)
df["vencida_parcial"] = (df["end"] > df["due_date"]) & (df["type"] != "reunion")

# Si alguna parte del mismo key está vencida, marcar todas las filas con ese key como vencidas
vencidas_keys = df.loc[df["vencida_parcial"], "key"].unique()
df["vencida"] = df["key"].isin(vencidas_keys)

if "epic_name" in df.columns:
    df["epic_name"] = df["epic_name"].fillna("— Sin épica —").astype(str)
else:
    # si todavía no lo agregaste al JSON, evitamos romper el UI
    df["epic_name"] = "— Sin épica —"



devs = sorted(df["developer"].unique())
dev_filter = st.multiselect("👨‍💻 Filtrar por developer", devs, default=devs)

# Radio: tiene épica / no tiene épica / todas
epic_mode = st.radio(
    "🧩 Épica",
    ["Todas", "Tiene épica", "No tiene épica"],
    index=0,
    horizontal=True,
)

epic_names = sorted(df["epic_name"].dropna().unique())
epic_filter = st.multiselect("🏷️ Nombre de la épica", epic_names, default=epic_names)

# Selector de vista
vista = st.radio("🗂️ Vista", ["Cronología", "Ver listado"], index=0, horizontal=True)


mask = df["developer"].isin(dev_filter) & df["epic_name"].isin(epic_filter)

if epic_mode == "Tiene épica":
    mask &= df["has_epic"] == True
elif epic_mode == "No tiene épica":
    mask &= df["has_epic"] == False

filtered_df = df[mask].copy()



if vista == "Cronología":
    st.subheader("📋 Tareas planificadas por desarrollador")
    st.caption("Esta tabla muestra todas las tareas programadas por cada developer, destacando en amarillo aquellas vencidas parcial o totalmente.")

    rename_dict = {
        "developer": "Desarrollador",
        "key": "Clave",
        "summary": "Resumen",
        "has_epic": "Tiene épica",
        "due_date": "Fecha límite",
        "epic_name": "Nombre épica", 
        "start": "Inicio",
        "end": "Fin",
        "duration_hours": "Duración (horas)",
        "vencida": "Vencida"
    }
    

    styled = (
        filtered_df[list(rename_dict.keys())]
        .rename(columns=rename_dict)
        .sort_values(by=["Desarrollador", "Inicio"])
        .reset_index(drop=True)
        .style.apply(highlight_vencidas, axis=1)
    )
    st.dataframe(styled, use_container_width=True)

else:
    st.subheader("🧾 Listado de tareas (agrupadas por clave)")
    st.caption("Se excluyen reuniones. Cada fila representa la tarea completa con su fecha de inicio real (primer slot) y fin real (último slot). Esto sirve para detectar (en base a lo filtrado arriba) cuando finalizaría cada tarjeta si se respetan las reglas de planificación definidas por criterios comerciales")

    work_df = filtered_df[filtered_df["type"] != "reunion"].copy()

    grouped = (
        work_df
        .sort_values(["key", "start"])
        .groupby("key", as_index=False)
        .agg({
            "developer": "first",
            "summary": "first",
            "has_epic": "first",
            "due_date": "max",
            "epic_name": "first", 
            "start": "min",
            "end": "max",
            "duration_hours": "sum",
            "vencida": "any",
            "note": lambda x: "\n".join([s for s in x.astype(str) if s.strip()]),
        })
        .rename(columns={
            "developer": "Desarrollador",
            "key": "Clave",
            "summary": "Resumen",
            "has_epic": "Tiene épica",
            "due_date": "Fecha límite",
            "start": "Inicio real",
            "epic_name": "Nombre épica", 
            "end": "Fin real",
            "duration_hours": "Duración total (horas)",
            "vencida": "Vencida",
            "note": "Nota",
        })
        .assign(Indicador=lambda d: d["Nota"].str.strip().apply(lambda s: "＋" if s else ""))
        .assign(**{"Ver nota": lambda d: d["Nota"].str.strip().astype(bool) & False})
        .drop(columns=["Nota"])
        .sort_values(by=["Desarrollador", "Inicio real"])
        .reset_index(drop=True)
        .style.apply(highlight_vencidas, axis=1)
    )

    

    edited = st.data_editor(
        grouped,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Indicador": st.column_config.TextColumn("Detalle", width="small"),
            "Ver nota": st.column_config.CheckboxColumn("Ver nota", help="Mostrar detalle de la fila"),
            "Tiene épica": st.column_config.CheckboxColumn("Tiene épica", disabled=True),
            "Vencida": st.column_config.CheckboxColumn("Vencida", disabled=True),
        },
        disabled=["Desarrollador","Clave","Resumen","Fecha límite","Inicio real", "Nombre épica","Fin real","Duración total (horas)","Indicador"],
        key="listado_editor",
    )

    sel = edited[edited["Ver nota"]]
    if not sel.empty:
        st.markdown("**📝 Detalle de notas seleccionadas**")
        # map clave -> nota original agrupada
        notes_by_key = (
        work_df
            .sort_values(["key", "start"])
            .groupby("key")["note"]
            .apply(lambda s: "\n".join(dict.fromkeys(x for x in s if x.strip())))  # elimina repetidos manteniendo orden
            .to_dict()
        )
        for _, r in sel.iterrows():
            txt = notes_by_key.get(r["Clave"], "")
            if txt:
                st.info(f"**{r['Clave']} – {r['Resumen']}**\n\n{txt}")

card_style = """
    background-color:#1976d2;
    padding:20px;
    border-radius:10px;
    margin-bottom:20px;
    min-height: 120px;
    color: white;
    text-align: center;
"""

selected_project = epic_filter[0] if len(epic_filter) == 1 else None
if len(dev_filter) == 1:
    selected_dev = dev_filter[0]
    
    
    # Horas totales asignadas
    total_hours = filtered_df["duration_hours"].sum()

    # Horas en tareas con épica (proyectos)
    epic_hours = filtered_df[filtered_df["has_epic"] == True]["duration_hours"].sum()

    # Ratio de horas en proyectos
    ratio = epic_hours / total_hours if total_hours > 0 else 0

    min_ratio = MIN_PROJECT_RATIO.get(selected_dev, MIN_PROJECT_RATIO["Default"])
    daily_hours = DAILY_HOURS.get(selected_dev, DAILY_HOURS["Default"])

    col1, col3 = st.columns(2)


    # with col1:
    #     st.markdown(f"""
    #     <div style="{card_style}">
    #         <h3>{total_hours:.1f}h</h3>
    #         <p>Horas Totales a planificar</p>
    #     </div>
    #     """, unsafe_allow_html=True)

    # with col2:
    #     st.markdown(f"""
    #     <div style="{card_style}">
    #         <h3>{ratio:.0%}</h3>
    #         <p>Ratio de proyectos</p>
    #     </div>
    #     """, unsafe_allow_html=True)

    with col1:
    
        if len(epic_filter) == 1:
            selected_project = epic_filter[0]
            project_hours = filtered_df[filtered_df["epic_name"] == selected_project]["duration_hours"].sum()

            st.markdown(f"""
            <div style="{card_style}">
                <h3>{project_hours:.1f}h</h3>
                <p>Horas estimadas para el proyecto seleccionado</p>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="{card_style}">
            <h3>📅 {daily_hours:.1f}h</h3>
            <p>Horas efectivas esperadas</p>
        </div>
        """, unsafe_allow_html=True)


    col5, col6 = st.columns(2)
    
    with col5:
        # 🔒 Evitá NameError usando el mismo guardia
        if selected_project:
            project_dates = filtered_df.loc[filtered_df["epic_name"] == selected_project, "end"]
            if not project_dates.empty:
                project_end = pd.to_datetime(project_dates).max().date()
                st.markdown(f"""
                <div style="{card_style}">
                    <h3>{project_end}</h3>
                    <p>Fin del proyecto seleccionado</p>
                </div>
                """, unsafe_allow_html=True)
    with col6:
    
        dev_dates = pd.to_datetime(filtered_df["end"])
        if not dev_dates.empty:
            dev_start = dev_dates.min().date()
            dev_end = dev_dates.max().date()
            sprint_days = 14
            sprint_count = ((dev_end - dev_start).days + 1) // sprint_days + 1

            st.markdown(f"""
            <div style="{card_style}">
                <h3>{sprint_count} sprints</h3>
                <p>Cobertura de planificación hasta el {dev_end}</p>
            </div>
            """, unsafe_allow_html=True)
    


# Agregar gráfico de barras por día
# st.subheader("📊 Horas asignadas por día")
# st.caption("Distribución de las horas de trabajo planificadas por desarrollador a lo largo del tiempo.")

# grouped = (
#     filtered_df.groupby(["developer", "día"])["duration_hours"]
#     .sum()
#     .unstack(fill_value=0)
#     .T
# )

# st.bar_chart(grouped)






# # Filtrar tareas en el rango
# df_rango = df[(df["start"] >= DEFAULT_START_DATE) & (df["start"] <= DEFAULT_END_DATE)]

# epic_stats = defaultdict(lambda: {"con_epica": 0.0, "sin_epica": 0.0})


# for _, row in df_rango.iterrows():
#     if row.get("type") == "reunion":
#         continue  # Ignorar reuniones

#     dev = row["developer"]
#     horas = row["duration_hours"]

#     if row["has_epic"]:
#         epic_stats[dev]["con_epica"] += horas
#     else:
#         epic_stats[dev]["sin_epica"] += horas



# epic_df = pd.DataFrame([
#     {
#         "developer": dev,
#         "Con épica": stats["con_epica"],
#         "Sin épica": stats["sin_epica"]
#     }
#     for dev, stats in epic_stats.items()
# ])


# if not epic_df.empty and "developer" in epic_df.columns:
#     epic_df = epic_df.set_index("developer")

#     st.subheader("📊 Horas con y sin épica ")
#     st.bar_chart(epic_df)

#     st.subheader("📈 Porcentaje de horas con y sin épica")
#     porcentaje_df = epic_df.copy()
#     porcentaje_df["Total"] = porcentaje_df["Con épica"] + porcentaje_df["Sin épica"]
#     porcentaje_df["% Con épica"] = (porcentaje_df["Con épica"] / porcentaje_df["Total"] * 100).round(1)
#     porcentaje_df["% Sin épica"] = (porcentaje_df["Sin épica"] / porcentaje_df["Total"] * 100).round(1)

#     st.dataframe(porcentaje_df[["% Con épica", "% Sin épica"]])
# else:
#     st.warning(f"⚠️ No se encontraron datos de planificación con y sin épica para mostrar. {df_rango.columns}")
# ===================== Cálculo de avance de épicas =====================
# st.subheader("🚀 Avance de Proyectos (Épicas)")

# # Cargar epics con tareas desde archivo
# try:
#     with open("epics_due_lookup.json") as f:
#         epics_data = json.load(f)
# except FileNotFoundError:
#     st.warning("⚠️ No se encontró el archivo epics_due_lookup.json")
#     epics_data = {}

# epic_progress_rows = []
# for epic_key, info in epics_data.items():
#     tasks = info.get("tasks", [])
#     if not tasks:
#         continue

#     total_sp = 0
#     completed_sp = 0
#     pending_hours = 0

#     for task in tasks:
#         sp = task.get("story_points")
#         if sp is None:
#             continue
#         total_sp += sp
#         if task.get("status", "").upper() == "FINISH":
#             completed_sp += sp
#         else:
#             pending_hours += sp  # Asumimos 1 SP = 1 hora estimada

#     if total_sp == 0:
#         continue

#     epic_progress_rows.append({
#         "Épica": epic_key,
#         "Resumen": info.get("summary", ""),
#         "Vencimiento": info.get("due_date", ""),
#         "Total SP": total_sp,
#         "Completados": completed_sp,
#         "Avance %": round(completed_sp / total_sp * 100, 1),
#         "Horas pendientes": pending_hours
#     })

# # Mostrar tabla
# if epic_progress_rows:
#     epic_progress_df = pd.DataFrame(epic_progress_rows)
#     st.dataframe(epic_progress_df)
# else:
#     st.info("No se encontraron tareas asociadas a las épicas.")


# ===================== Avance por Épica con gráfico =====================
# st.subheader("Avance de Proyectos (Épicas)")
# st.caption("Resumen del progreso en las épicas, basado en Story Points completados y pendientes. Puedes seleccionar una épica para ver su detalle.")


# # Cargar archivo de épicas con tareas
# try:
#     with open("epics_due_lookup.json") as f:
#         epics_data = json.load(f)
# except FileNotFoundError:
#     st.warning("⚠️ No se encontró el archivo epics_due_lookup.json")
#     epics_data = {}

# # Procesar datos de avance
# epic_progress_rows = []
# for epic_key, info in epics_data.items():
#     tasks = info.get("tasks", [])
#     if not tasks:
#         continue

#     total_sp = 0
#     completed_sp = 0
#     pending_hours = 0

#     for task in tasks:
#         sp = task.get("story_points")
#         if sp is None:
#             continue
#         total_sp += sp
#         if task.get("status", "").upper() == "FINISH":
#             completed_sp += sp
#         else:
#             pending_hours += sp

#     if total_sp == 0:
#         continue

#     epic_progress_rows.append({
#         "Épica": epic_key,
#         "Resumen": info.get("summary", ""),
#         "Vencimiento": info.get("due_date", ""),
#         "Total SP": total_sp,
#         "Completados": completed_sp,
#         "Pendientes": total_sp - completed_sp,
#         "Avance %": round(completed_sp / total_sp * 100, 1),
#     })

# if epic_progress_rows:
#     epic_progress_df = pd.DataFrame(epic_progress_rows)

#     selected_epica = st.selectbox("🎯 Seleccionar épica para ver detalle", ["Todas"] + list(epic_progress_df["Épica"]))

#     if selected_epica == "Todas":
#         # Filtrar solo épicas con tareas pendientes
#         filtered = epic_progress_df[epic_progress_df["Pendientes"] > 0]

#         # 📊 Gráfico de barras (solo para "Todas")
#         chart_data = filtered.set_index("Épica")[["Completados", "Pendientes"]]
#         st.subheader("📊 Avance de todas las épicas con pendientes")
#         st.bar_chart(chart_data)
#     else:
#         filtered = epic_progress_df[epic_progress_df["Épica"] == selected_epica]

#         if not filtered.empty:
#             row = filtered.iloc[0]
#             pie_data = pd.Series({
#                 "Completados": row["Completados"],
#                 "Pendientes": row["Pendientes"]
#             })

#             st.subheader("📘 Distribución de Story Points")

#             # Crear figura pequeña
#             fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
#             ax.pie(
#                 pie_data.values,
#                 labels=pie_data.index,
#                 autopct='%1.1f%%',
#                 textprops={'fontsize': 7},
#                 startangle=90
#             )
#             ax.set_title(f"Distribución SP - {row['Resumen'] or selected_epica}", fontsize=9)
#             ax.axis('equal')
#             fig.tight_layout()

#             # Convertir a imagen
#             buf = BytesIO()
#             fig.savefig(buf, format="png", bbox_inches="tight")
#             buf.seek(0)

#             # Mostrar imagen en tamaño real
#             st.image(buf, use_container_width=False)


#     st.subheader("📋 Detalle de épicas")
#     st.dataframe(filtered.reset_index(drop=True))
# else:
#     st.info("No se encontraron tareas asociadas a las épicas.")







# if st.button("Guardar resumen de planificación"):
#     resumen = [
#         {
#             "dev": dev,
#             "horas_epicas": stats["con_epica"],
#             "horas_no_epicas": stats["sin_epica"]
#         }
#         for dev, stats in epic_stats.items()
#     ]

#     fecha_str = DEFAULT_START_DATE.strftime("%Y-%m-%d")
#     filename = f"S{fecha_str}.json"
#     with open(filename, "w", encoding="utf-8") as f:
#         json.dump(resumen, f, indent=4, ensure_ascii=False)

#     st.success(f"Resumen guardado como {filename}")





from datetime import date
from constants import PROJECT_MAP







def _opt_value(v):
    if isinstance(v, dict):
        return v.get("value") or v.get("name")
    if isinstance(v, list):
        vals = []
        for x in v:
            if isinstance(x, dict):
                vals.append(x.get("value") or x.get("name"))
            else:
                vals.append(x)
        # si es lista, devolvemos como texto join para poder filtrar
        return ", ".join([str(x) for x in vals if x is not None])
    return v

if "cf10209" in df.columns:
    df["cf10209"] = df["cf10209"].apply(_opt_value)
    df["cf10209"] = df["cf10209"].fillna("— Sin área —")
else:
    # si no existe, creamos la columna para evitar errores en el UI
    df["cf10209"] = "— Sin área —"


st.subheader("Filtros")

c1, c2 = st.columns([2, 2])

with c1:
    devs = sorted(df["developer"].dropna().unique())
    selected_devs = st.multiselect("👨‍💻 Developer  ", devs, default=devs)

with c2:
    reporters = sorted(df["reporter"].dropna().unique())
    selected_reporters = st.multiselect("📝 Reporter  ", reporters, default=reporters)


c3, c4 = st.columns([1, 2])
with c3:
    epic_mode = st.radio("🧩 Épica", ["Todas", "Con épica", "Sin épica"], index=0, horizontal=True)

with c4:
    areas = sorted(df["cf10209"].dropna().unique().tolist())
    selected_areas = st.multiselect("🏷️ Área solicitante", areas, default=areas)
# Selector de vista principal
vista = st.radio("🗂️ Vista", ["Cronología  ", "Ver listado  "], index=0, horizontal=True, key="vista_principal")

# =========================
# 🧮 Filtrado base
# =========================
filtered_df = df[
    df["developer"].isin(selected_devs) &
    df["reporter"].isin(selected_reporters) 
    & df["cf10209"].isin(selected_areas)
].copy()

# Aplicar filtro de épica
if epic_mode == "Con épica":
    filtered_df = filtered_df[filtered_df["has_epic"] == True]
elif epic_mode == "Sin épica":
    filtered_df = filtered_df[filtered_df["has_epic"] == False]

# =========================
# ⏱️ Cálculo “vencidas” (badge)
# =========================
# Excluir reuniones para el cálculo y comparar con DEFAULT_END_DATE
calc_df = filtered_df[(filtered_df["type"] != "reunion") & (filtered_df["due_date"] < DEFAULT_END_DATE)].copy()
horas_vencidas = calc_df["duration_hours"].sum()

# Color del badge
if horas_vencidas < 5:
    color = "#4CAF50"   # verde
elif horas_vencidas < 30:
    color = "#FFC107"   # amarillo
else:
    color = "#F44336"   # rojo

st.markdown(f"""
<style>
.badge {{
  display: inline-block;
  padding: 12px 24px;
  font-size: 24px;
  font-weight: bold;
  color: white;
  background-color: {color};
  border-radius: 8px;
}}
</style>
<div class="badge">⏱️ {horas_vencidas:.1f} horas vencidas</div>
""", unsafe_allow_html=True)

st.caption("Horas de tareas que vencen antes del fin del rango (excluye reuniones). El filtro de épica afecta este cálculo.")

# =========================
# 🔍 Detalle (respeta la vista y los filtros)
# =========================
def _arrow_fix(tmp):
    # Si alguna columna te mezcla tipos y rompe Arrow, casteala a str acá
    if "Última tarea planificable" in tmp.columns:
        tmp["Última tarea planificable"] = tmp["Última tarea planificable"].astype(str)
    return tmp

if st.checkbox("🔍 Ver detalle de tareas vencidas  "):
    if vista == "Cronología":
        tmp_detalle = (
            calc_df[["developer", "reporter", "key", "summary", "due_date", "start", "end", "duration_hours"]]
            .sort_values(by=["developer", "due_date", "start"])
            .reset_index(drop=True)
        )
        st.dataframe(_arrow_fix(tmp_detalle), use_container_width=True)

    else:  # Ver listado
        work_df = calc_df.copy()  # ya excluye reuniones
        grouped_detalle = (
            work_df
            .sort_values(["key", "start"])
            .groupby("key", as_index=False)
            .agg({
                "developer": lambda x: ", ".join(sorted(set(x))),
                "reporter": "first",
                "summary": "first",
                "due_date": "max",
                "start": "min",   # inicio real
                "end": "max",     # fin real
                "duration_hours": "sum"
            })
        )
        grouped_detalle = (
            grouped_detalle.rename(columns={
                "developer": "Developer(s)",
                "reporter": "Reporter",
                "key": "Clave",
                "summary": "Resumen",
                "due_date": "Fecha límite",
                "start": "Inicio real",
                "end": "Fin real",
                "duration_hours": "Duración total (horas)"
            })
            .sort_values(["Developer(s)", "Inicio real"])
            .reset_index(drop=True)
        )
        st.dataframe(_arrow_fix(grouped_detalle), use_container_width=True)


calc_df_2525 = filtered_df[
    (filtered_df["type"] != "reunion") &
    (filtered_df["due_date"] < datetime(2525, 8, 18))
].copy()

# Si querés que este cálculo también respete el filtro de épica:
# (Ya está respetado porque filtered_df ya filtró por epic_mode)

horas_planificables = calc_df_2525["duration_hours"].sum()

# Color del badge
if horas_planificables < 5:
    color_2525 = "#4CAF50"   # verde
elif horas_planificables < 30:
    color_2525 = "#FFC107"   # amarillo
else:
    color_2525 = "#F44336"   # rojo

st.markdown(f"""
<style>
.badge2525 {{
  display: inline-block;
  padding: 12px 24px;
  font-size: 24px;
  font-weight: bold;
  color: white;
  background-color: {color_2525};
  border-radius: 8px;
}}
</style>
<div class="badge2525">⏱️ {horas_planificables:.1f} horas planificables</div>
""", unsafe_allow_html=True)

st.caption("Horas de tareas que vencen antes del final de los tiempos.")

# Detalle opcional
if st.checkbox("🔍 Ver detalle de tareas planificables hasta el final"):
    if vista == "Cronología  ":
        # Cronología: mostramos filas (una por tramo planificado) ordenadas por dev y due
        cols_exist = [c for c in ["developer","reporter","key","summary","due_date","start","end","duration_hours"] if c in calc_df_2525.columns]
        tmp_detalle_2525 = (
            calc_df_2525[cols_exist]
            .sort_values(by=[c for c in ["developer","due_date","start"] if c in cols_exist])
            .reset_index(drop=True)
        )
        st.dataframe(_arrow_fix(tmp_detalle_2525), use_container_width=True)
    else:
        # Ver listado: agrupamos por tarjeta (key)
        work_df = calc_df_2525.copy()
        # Si no existieran start/end en tu dataset, este bloque igual funciona
        agg_dict = {
            "developer": lambda x: ", ".join(sorted(set(x))),
            "reporter": "first",
            "summary": "first",
            "due_date": "max",
            "duration_hours": "sum",
        }
        if "start" in work_df.columns:
            agg_dict["start"] = "min"  # inicio real
        if "end" in work_df.columns:
            agg_dict["end"] = "max"    # fin real

        grouped_detalle_2525 = (
            work_df
            .sort_values(["key"] + ([ "start" ] if "start" in work_df.columns else []))
            .groupby("key", as_index=False)
            .agg(agg_dict)
        )

        # Renombrado prolijo
        rename_map = {
            "developer": "Developer(s)",
            "reporter": "Reporter",
            "key": "Clave",
            "summary": "Resumen",
            "due_date": "Fecha límite",
            "duration_hours": "Duración total (horas)"
        }
        if "start" in grouped_detalle_2525.columns:
            rename_map["start"] = "Inicio real"
        if "end" in grouped_detalle_2525.columns:
            rename_map["end"] = "Fin real"

        grouped_detalle_2525 = (
            grouped_detalle_2525
            .rename(columns=rename_map)
            .sort_values([col for col in ["Developer(s)", "Inicio real", "Fecha límite"] if col in rename_map.values()])
            .reset_index(drop=True)
        )
        st.dataframe(_arrow_fix(grouped_detalle_2525), use_container_width=True)








st.subheader("🧾 Proyectos planificados por desarrollador")
st.caption("Se muestra la última tarea planificada y los días restantes para el vencimiento de cada proyecto. Útil para verificar si un proyecto necesita planificación adicional.")


# 1. Última fecha sin épica por developer
sin_epica_df = df[(~df["has_epic"]) & (df["type"] != "reunion")]
ultima_fecha_por_dev = (
    sin_epica_df.groupby("developer")["end"]
    .max()
    .dropna()
    .reset_index()
    .rename(columns={"end": "Última tarea planificable"})
)
ultima_fecha_por_dev["Última tarea planificable"] = ultima_fecha_por_dev["Última tarea planificable"].dt.date

# 2. Mapear proyectos y fechas de vencimiento
proyecto_vencimiento = []
hoy = date.today()

for dev, proyectos in PROJECT_MAP.items():
    last_date = ultima_fecha_por_dev[ultima_fecha_por_dev["developer"] == dev]["Última tarea planificable"]
    last_date = last_date.values[0] if not last_date.empty else "No planificado"

    for proyecto, venc in proyectos.items():
        venc_date = datetime.strptime(venc, "%Y-%m-%d").date()

        if isinstance(last_date, date):
            dias_restantes = (venc_date - last_date).days
        else:
            dias_restantes = None

        # Color de semáforo
        if dias_restantes is None:
            color = "🟫"  # no planificado
        elif dias_restantes < 0:
            color = "🔴"
        elif dias_restantes <= 5:
            color = "🟠"
        else:
            color = "🟢"

        proyecto_vencimiento.append({
            "developer": dev,
            "Proyecto": proyecto,
            "Vencimiento": venc,
            "Última tarea planificable": last_date,
            "Días de margen": dias_restantes,
            "Estado": color
        })





proyecto_df = pd.DataFrame(proyecto_vencimiento)


developers = sorted(proyecto_df["developer"].unique())

selected_devs = st.multiselect("👨‍💻 Filtrar developers", developers, default=developers)


proyecto_df_filtrado = proyecto_df[proyecto_df["developer"].isin(selected_devs)]

st.dataframe(proyecto_df_filtrado.sort_values(["developer", "Vencimiento"]))
    


