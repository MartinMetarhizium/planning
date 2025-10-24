import json
import os
import streamlit as st
import pandas as pd

PLANNING = "bt_it_sprint_planning.json"
REPORT = "report_it.json"
KPIS = "kpis_it.json"

st.set_page_config(page_title="Sprint Dashboard IT/BT", layout="wide")

# ===== Utilidades =====
def load_json(path):
    if not os.path.exists(path):
        st.warning(f"No existe {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ===== Datos =====
planning = load_json(PLANNING)
report = load_json(REPORT)
kpis = load_json(KPIS)

if not kpis:
    st.stop()

# ===== Sidebar =====
st.sidebar.title("🏷️ Selección de Sprint")
sprints = sorted(kpis.keys(), reverse=True)
sprint_sel = st.sidebar.selectbox("Sprint", sprints)

kpi_sprint = kpis[sprint_sel]
dev_kpis = kpi_sprint["kpis_por_desarrollador"]
global_kpis = kpi_sprint["kpis_globales"]

st.title(f"📊 Indicadores del Sprint {sprint_sel}")

# ===== Métricas globales =====
col1, col2, col3 = st.columns(3)
col1.metric("% tareas replanificadas", f"{global_kpis.get('porc_tareas_replanificadas', 0)}%")
col2.metric("Predictibilidad", f"{global_kpis.get('predictibilidad_por_due_date', 0)}%")
col3.metric("Desarrolladores activos", len(dev_kpis))

st.markdown("---")

# ===== Tabla de KPIs por desarrollador =====
st.subheader("👨‍💻 KPIs por desarrollador")
df_dev = pd.DataFrame(dev_kpis).T.reset_index().rename(columns={"index": "Desarrollador"})
df_dev = df_dev[
    [
        "Desarrollador",
        "tarjetas_planificadas",
        "tarjetas_realizadas",
        "porc_tarjetas_completadas",
        "horas_planificadas",
        "horas_realizadas",
        "porc_horas_cumplidas",
        "desviacion_promedio_estimacion",
    ]
]
st.dataframe(df_dev, use_container_width=True)

# ===== Gráficos =====
st.subheader("📈 Cumplimiento por desarrollador")
st.bar_chart(df_dev.set_index("Desarrollador")[["porc_tarjetas_completadas", "porc_horas_cumplidas"]])

st.subheader("⚖️ Carga planificada por desarrollador")
carga = global_kpis.get("carga_planificada_por_dev", {})
if carga:
    carga_df = pd.DataFrame(list(carga.items()), columns=["Desarrollador", "Horas planificadas"])
    st.bar_chart(carga_df.set_index("Desarrollador"))

# ===== Detalle de tareas (opcional) =====
if sprint_sel in report:
    issues = report[sprint_sel]["issues"]
    st.markdown("### 🗂️ Detalle de tareas")
    issues_data = [
        {
            "Key": k,
            "Dev": v.get("developer"),
            "Summary": v.get("summary"),
            "Status": v.get("status"),
            "Done": v.get("done"),
            "Horas reales": v.get("real_hours_issue"),
            "Due": v.get("duedate"),
            "Antes del due": v.get("done_before_due"),
        }
        for k, v in issues.items()
    ]
    st.dataframe(pd.DataFrame(issues_data))

st.success("✅ Dashboard cargado correctamente")