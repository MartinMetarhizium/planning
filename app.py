import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
from constants import PROJECT_MAP_BT, PROJECT_MAP, DEFAULT_END_DATE, DEFAULT_END_DATE_with_timezone, DEFAULT_START_DATE,DEFAULT_START_DATE_with_timezone
 

def highlight_vencidas(row):        
    
    if row["vencida"]:
        return ['background-color: #fff9c4'] * len(row)
    if "type" in row and row["type"] == "reunion":
        return [''] * len(row)
    return [''] * len(row)


st.set_page_config(layout="wide")

st.title("📅 Planificación de Desarrolladores")
st.markdown("Este panel permite visualizar la carga de trabajo de los desarrolladores, el estado de sus tareas (con o sin épica), así como el progreso y vencimientos de proyectos.")




st.subheader("📋 Tareas planificadas por desarrollador")
st.caption("Esta tabla muestra todas las tareas programadas por cada developer, destacando en amarillo aquellas vencidas parcial o totalmente.")
# Cargar el archivo planificado
with open("planificacion.json") as f:
    data = json.load(f)

df = pd.DataFrame(data)
df["start"] = pd.to_datetime(df["start"], errors="coerce",format='mixed')
df["end"] = pd.to_datetime(df["end"], errors="coerce")
df["día"] = df["start"].dt.date
df["due_date"] = pd.to_datetime(df["due_date"],format='mixed')
df["vencida_parcial"] = (df["end"] > df["due_date"]) & (df["type"] != "reunion")

# Paso 2: Si alguna parte del mismo key está vencida, marcar todas las filas con ese key como vencidas
vencidas_keys = df[df["vencida_parcial"]]["key"].unique()
df["vencida"] = df["key"].isin(vencidas_keys)

# Filtros
devs = sorted(df["developer"].unique())
dev_filter = st.multiselect("👨‍💻 Filtrar por developer", devs, default=devs)

filtered_df = df[df["developer"].isin(dev_filter)]

rename_dict = {
    "developer": "Desarrollador",
    "key": "Clave",
    "summary": "Resumen",
    "has_epic": "Tiene épica",
    "due_date": "Fecha límite",
    "start": "Inicio",
    "end": "Fin",
    "duration_hours": "Duración (horas)",
    "vencida": "Vencida"
}


# Mostrar tabla
styled = (
    filtered_df[list(rename_dict.keys())]
    .rename(columns=rename_dict)
    .sort_values(by=["Desarrollador", "Inicio"])
    .reset_index(drop=True)
    .style.apply(highlight_vencidas, axis=1)
)

st.dataframe(styled, use_container_width=True)

# Agregar gráfico de barras por día
st.subheader("📊 Horas asignadas por día")
st.caption("Distribución de las horas de trabajo planificadas por desarrollador a lo largo del tiempo.")

grouped = (
    filtered_df.groupby(["developer", "día"])["duration_hours"]
    .sum()
    .unstack(fill_value=0)
    .T
)

st.bar_chart(grouped)






# Filtrar tareas en el rango
df_rango = df[(df["start"] >= DEFAULT_START_DATE) & (df["start"] <= DEFAULT_END_DATE)]

epic_stats = defaultdict(lambda: {"con_epica": 0.0, "sin_epica": 0.0})


for _, row in df_rango.iterrows():
    if row.get("type") == "reunion":
        continue  # Ignorar reuniones

    dev = row["developer"]
    horas = row["duration_hours"]

    if row["has_epic"]:
        epic_stats[dev]["con_epica"] += horas
    else:
        epic_stats[dev]["sin_epica"] += horas



epic_df = pd.DataFrame([
    {
        "developer": dev,
        "Con épica": stats["con_epica"],
        "Sin épica": stats["sin_epica"]
    }
    for dev, stats in epic_stats.items()
])


if not epic_df.empty and "developer" in epic_df.columns:
    epic_df = epic_df.set_index("developer")

    st.subheader("📊 Horas con y sin épica ")
    st.bar_chart(epic_df)

    st.subheader("📈 Porcentaje de horas con y sin épica")
    porcentaje_df = epic_df.copy()
    porcentaje_df["Total"] = porcentaje_df["Con épica"] + porcentaje_df["Sin épica"]
    porcentaje_df["% Con épica"] = (porcentaje_df["Con épica"] / porcentaje_df["Total"] * 100).round(1)
    porcentaje_df["% Sin épica"] = (porcentaje_df["Sin épica"] / porcentaje_df["Total"] * 100).round(1)

    st.dataframe(porcentaje_df[["% Con épica", "% Sin épica"]])
else:
    st.warning(f"⚠️ No se encontraron datos de planificación con y sin épica para mostrar. {df_rango.columns}")
# ===================== Cálculo de avance de épicas =====================
st.subheader("🚀 Avance de Proyectos (Épicas)")

# Cargar epics con tareas desde archivo
try:
    with open("epics_due_lookup.json") as f:
        epics_data = json.load(f)
except FileNotFoundError:
    st.warning("⚠️ No se encontró el archivo epics_due_lookup.json")
    epics_data = {}

epic_progress_rows = []
for epic_key, info in epics_data.items():
    tasks = info.get("tasks", [])
    if not tasks:
        continue

    total_sp = 0
    completed_sp = 0
    pending_hours = 0

    for task in tasks:
        sp = task.get("story_points")
        if sp is None:
            continue
        total_sp += sp
        if task.get("status", "").upper() == "FINISH":
            completed_sp += sp
        else:
            pending_hours += sp  # Asumimos 1 SP = 1 hora estimada

    if total_sp == 0:
        continue

    epic_progress_rows.append({
        "Épica": epic_key,
        "Resumen": info.get("summary", ""),
        "Vencimiento": info.get("due_date", ""),
        "Total SP": total_sp,
        "Completados": completed_sp,
        "Avance %": round(completed_sp / total_sp * 100, 1),
        "Horas pendientes": pending_hours
    })

# Mostrar tabla
if epic_progress_rows:
    epic_progress_df = pd.DataFrame(epic_progress_rows)
    st.dataframe(epic_progress_df)
else:
    st.info("No se encontraron tareas asociadas a las épicas.")


# ===================== Avance por Épica con gráfico =====================
st.subheader("Avance de Proyectos (Épicas)")
st.caption("Resumen del progreso en las épicas, basado en Story Points completados y pendientes. Puedes seleccionar una épica para ver su detalle.")


# Cargar archivo de épicas con tareas
try:
    with open("epics_due_lookup.json") as f:
        epics_data = json.load(f)
except FileNotFoundError:
    st.warning("⚠️ No se encontró el archivo epics_due_lookup.json")
    epics_data = {}

# Procesar datos de avance
epic_progress_rows = []
for epic_key, info in epics_data.items():
    tasks = info.get("tasks", [])
    if not tasks:
        continue

    total_sp = 0
    completed_sp = 0
    pending_hours = 0

    for task in tasks:
        sp = task.get("story_points")
        if sp is None:
            continue
        total_sp += sp
        if task.get("status", "").upper() == "FINISH":
            completed_sp += sp
        else:
            pending_hours += sp

    if total_sp == 0:
        continue

    epic_progress_rows.append({
        "Épica": epic_key,
        "Resumen": info.get("summary", ""),
        "Vencimiento": info.get("due_date", ""),
        "Total SP": total_sp,
        "Completados": completed_sp,
        "Pendientes": total_sp - completed_sp,
        "Avance %": round(completed_sp / total_sp * 100, 1),
    })

if epic_progress_rows:
    epic_progress_df = pd.DataFrame(epic_progress_rows)

    selected_epica = st.selectbox("🎯 Seleccionar épica para ver detalle", ["Todas"] + list(epic_progress_df["Épica"]))

    if selected_epica == "Todas":
        # Filtrar solo épicas con tareas pendientes
        filtered = epic_progress_df[epic_progress_df["Pendientes"] > 0]

        # 📊 Gráfico de barras (solo para "Todas")
        chart_data = filtered.set_index("Épica")[["Completados", "Pendientes"]]
        st.subheader("📊 Avance de todas las épicas con pendientes")
        st.bar_chart(chart_data)
    else:
        filtered = epic_progress_df[epic_progress_df["Épica"] == selected_epica]

        if not filtered.empty:
            row = filtered.iloc[0]
            pie_data = pd.Series({
                "Completados": row["Completados"],
                "Pendientes": row["Pendientes"]
            })

            st.subheader("📘 Distribución de Story Points")

            # Crear figura pequeña
            fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
            ax.pie(
                pie_data.values,
                labels=pie_data.index,
                autopct='%1.1f%%',
                textprops={'fontsize': 7},
                startangle=90
            )
            ax.set_title(f"Distribución SP - {row['Resumen'] or selected_epica}", fontsize=9)
            ax.axis('equal')
            fig.tight_layout()

            # Convertir a imagen
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)

            # Mostrar imagen en tamaño real
            st.image(buf, use_container_width=False)


    st.subheader("📋 Detalle de épicas")
    st.dataframe(filtered.reset_index(drop=True))
else:
    st.info("No se encontraron tareas asociadas a las épicas.")







if st.button("Guardar resumen de planificación"):
    resumen = [
        {
            "dev": dev,
            "horas_epicas": stats["con_epica"],
            "horas_no_epicas": stats["sin_epica"]
        }
        for dev, stats in epic_stats.items()
    ]

    fecha_str = DEFAULT_START_DATE.strftime("%Y-%m-%d")
    filename = f"S{fecha_str}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=4, ensure_ascii=False)

    st.success(f"Resumen guardado como {filename}")





from datetime import date
from constants import PROJECT_MAP

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





# devs = sorted(df["developer"].dropna().unique())

# # Filtro multiselect por developer (con todos seleccionados por defecto)
# selected_devs = st.multiselect("👨‍💻 Filtrar developer", devs, default=devs)

# # Filtrar tickets sin épica, con due_date < DEFAULT_END_DATE y developer seleccionado
# vencidas_sin_epica = df[
#     (df["has_epic"] == False) &
#     (df["type"] != "reunion") &
#     (df["due_date"] < DEFAULT_END_DATE) &
#     (df["developer"].isin(selected_devs))
# ]

# # Sumar duración
# horas_vencidas = vencidas_sin_epica["duration_hours"].sum()

# # Mostrar gadget
# st.subheader("Horas de tareas que venceran al cierre de la proxima planning")
# st.metric(label="Horas totales", value=f"{horas_vencidas:.1f} h")

# # (Opcional) Mostrar detalle
# if st.checkbox("🔍 Ver detalle de tareas vencidas"):
#     st.dataframe(
#         vencidas_sin_epica[["developer", "key", "summary", "due_date", "duration_hours"]]
#         .sort_values(by=["developer", "due_date"])
#         .reset_index(drop=True)
#     )


# devs = sorted(df["developer"].dropna().unique())
# selected_devs = st.multiselect("👨‍💻 Filtrar developer", devs, default=devs)

# # Tareas sin épica y vencidas
# vencidas_sin_epica = df[
#     (df["has_epic"] == False) &
#     (df["type"] != "reunion") &
#     (df["due_date"] < DEFAULT_END_DATE) &
#     (df["developer"].isin(selected_devs))
# ]

# # Total de horas
# horas_vencidas = vencidas_sin_epica["duration_hours"].sum()

# # Determinar color
# if horas_vencidas < 5:
#     color = "#4CAF50"  # verde
# elif horas_vencidas < 30:
#     color = "#FFC107"  # amarillo
# else:
#     color = "#F44336"  # rojo

# # Mostrar como badge estilizado
# st.markdown(f"""
# <style>
# .badge {{
#   display: inline-block;
#   padding: 12px 24px;
#   font-size: 24px;
#   font-weight: bold;
#   color: white;
#   background-color: {color};
#   border-radius: 8px;
# }}
# </style>
# <div class="badge">⏱️ {horas_vencidas:.1f} horas vencidas</div>
# """, unsafe_allow_html=True)

# # Subtítulo explicativo
# st.caption("Horas de tareas sin épica que vencen antes del final de la próxima planificación.")

# # Detalle opcional
# if st.checkbox("🔍 Ver detalle de tareas vencidas"):
#     st.dataframe(
#         vencidas_sin_epica[["developer", "key", "summary", "due_date", "duration_hours"]]
#         .sort_values(by=["developer", "due_date"])
#         .reset_index(drop=True)
#     )



# === Developer Filter ===
devs = sorted(df["developer"].dropna().unique())
selected_devs = st.multiselect("👨‍💻 Filtrar developer", devs, default=devs)

# === Reporter Filter ===
reporters = sorted(df["reporter"].dropna().unique())
selected_reporters = st.multiselect("📝 Filtrar por reporter", reporters, default=reporters)

# === Filter vencidas_sin_epica ===
vencidas_sin_epica = df[
    (df["has_epic"] == False) &
    (df["type"] != "reunion") &
    (df["due_date"] < DEFAULT_END_DATE) &
    (df["developer"].isin(selected_devs)) &
    (df["reporter"].isin(selected_reporters))
]

# === Total horas vencidas ===
horas_vencidas = vencidas_sin_epica["duration_hours"].sum()

# === Determinar color ===
if horas_vencidas < 5:
    color = "#4CAF50"  # verde
elif horas_vencidas < 30:
    color = "#FFC107"  # amarillo
else:
    color = "#F44336"  # rojo

# === Mostrar como badge estilizado ===
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

# === Subtítulo explicativo ===
st.caption("Horas de tareas sin épica que vencen antes del final de la próxima planificación.")

# === Detalle opcional ===
if st.checkbox("🔍 Ver detalle de tareas vencidas"):
    st.dataframe(
        vencidas_sin_epica[["developer", "reporter", "key", "summary", "due_date", "duration_hours"]]
        .sort_values(by=["developer", "due_date"])
        .reset_index(drop=True)
    )









st.subheader("🧠 Proyectos asignados a analistas de BT")
st.caption("Resumen de los proyectos en los que trabaja cada analista del equipo de BT, su fecha de vencimiento, si están finalizados y el estado actual.")



bt_analistas = sorted(PROJECT_MAP_BT.keys())
selected_analistas = st.multiselect("🔍 Filtrar por analista", bt_analistas, default=bt_analistas)

# Armar tabla con vencimientos
bt_rows = []
for analista in selected_analistas:
    proyectos = PROJECT_MAP_BT.get(analista, {})
    for nombre_proyecto, info in proyectos.items():
        # Soportar string (estructura vieja)
        if isinstance(info, str):
            venc = datetime.strptime(info, "%Y-%m-%d").date()
            completado = None
            estado = "pendiente"
        else:
            venc = datetime.strptime(info.get("vencimiento", "2100-01-01"), "%Y-%m-%d").date()
            completado = info.get("completado")
            if completado:
                completado = datetime.strptime(completado, "%Y-%m-%d").date()
            estado = info.get("estado", "pendiente")

        # Determinar días restantes solo si no está finalizado
        if estado == "finalizado":
            dias_restantes = 0
            semaforo = "✅"
        else:
            dias_restantes = (venc - datetime.today().date()).days
            if dias_restantes < 0:
                semaforo = "🔴"
            elif dias_restantes <= 5:
                semaforo = "🟠"
            else:
                semaforo = "🟢"

        bt_rows.append({
            "Analista": analista,
            "Proyecto": nombre_proyecto,
            "Vencimiento": venc,
            "Días restantes": dias_restantes,
            "Estado": estado,
            "Finalizado el": completado.strftime("%Y-%m-%d") if completado else "-",
            "Semáforo": semaforo
        })

# Mostrar tabla ordenada por fecha
if bt_rows:
    bt_df = pd.DataFrame(bt_rows).sort_values(by=["Analista", "Vencimiento"])
    st.dataframe(bt_df, use_container_width=True)
else:
    st.info("No hay proyectos para los analistas seleccionados.")