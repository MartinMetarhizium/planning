import json
from pathlib import Path
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Épicas cruzadas (BTP ↔ IT)", layout="wide")
st.title("📦 Épicas cruzadas (BTP ↔ IT)")
st.caption("Visualización de épicas y sus tarjetas relacionadas desde epicas_cruzadas.json")

# === Carga del JSON ===
DEFAULT_PATH = "projectos_bt.json"
with st.sidebar:
    st.header("Fuente de datos")
    json_path = st.text_input("Ruta del JSON", DEFAULT_PATH)
    uploaded = st.file_uploader("…o subí el JSON", type=["json"])

if uploaded is not None:
    data = json.load(uploaded)
else:
    if not Path(json_path).exists():
        st.error(f"No se encontró el archivo: {json_path}")
        st.stop()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

# === Aplanar datos: épicas y tarjetas ===
epic_rows, task_rows = [], []
for epic_key, info in data.items():
    due = info.get("due_date")
    epic_sum = info.get("summary", "")
    tasks = info.get("tasks", []) or []
    epic_rows.append({
        "epic_key": epic_key,
        "epic_summary": epic_sum,
        "epic_due_date": due,
        "num_tasks": len(tasks)
    })
    for t in tasks:
        task_rows.append({
            "epic_key": epic_key,
            "epic_summary": epic_sum,
            "epic_due_date": due,
            "issue_key": t.get("key"),
            "issue_summary": t.get("summary", ""),
            "status": t.get("status", ""),
            "story_points": t.get("story_points"),
            "assignee": t.get("assignee", "Sin asignar"),
        })

epics_df = pd.DataFrame(epic_rows)
tasks_df = pd.DataFrame(task_rows)
if tasks_df.empty:
    st.warning("No hay tarjetas para mostrar.")
    st.stop()

# Limpieza básica
tasks_df["story_points"] = pd.to_numeric(tasks_df["story_points"], errors="coerce")
epics_df = epics_df.sort_values(["epic_due_date", "epic_key"], na_position="last")

# === Filtros ===
with st.sidebar:
    st.header("Filtros")
    epics_opts = epics_df["epic_key"].tolist()
    selected_epics = st.multiselect("Épicas", options=epics_opts, default=epics_opts)

    assignees = sorted([a for a in tasks_df["assignee"].dropna().unique().tolist()])
    selected_assignees = st.multiselect("Asignados", options=assignees, default=assignees)

    statuses = sorted(tasks_df["status"].dropna().unique().tolist())
    selected_statuses = st.multiselect("Estados", options=statuses, default=statuses)

    q = st.text_input("Buscar en resumen (épica o tarjeta)")

filtered = tasks_df[
    tasks_df["epic_key"].isin(selected_epics)
    & tasks_df["assignee"].isin(selected_assignees)
    & tasks_df["status"].isin(selected_statuses)
]

if q:
    mask = (
        filtered["issue_summary"].str.contains(q, case=False, na=False)
        | filtered["epic_summary"].str.contains(q, case=False, na=False)
    )
    filtered = filtered[mask]

st.caption(f"Mostrando {filtered['issue_key'].nunique()} tarjetas en {filtered['epic_key'].nunique()} épicas.")

# === KPIs ===
c1, c2, c3, c4 = st.columns(4)
c1.metric("Épicas", int(filtered["epic_key"].nunique()))
c2.metric("Tarjetas", int(filtered["issue_key"].nunique()))
c3.metric("SP totales", float(filtered["story_points"].sum(skipna=True)))
prox_venc = (
    epics_df.loc[epics_df["epic_key"].isin(filtered["epic_key"].unique()), "epic_due_date"]
    .dropna()
    .min()
)
c4.metric("Venc. más cercano", prox_venc if pd.notna(prox_venc) else "—")

# === Gráficos de contexto ===
st.subheader("Distribución general")
colA, colB = st.columns(2)

with colA:
    status_counts = filtered.groupby("status", as_index=False).size()
    chart_status = (
        alt.Chart(status_counts)
        .mark_bar()
        .encode(
            x=alt.X("status:N", title="Estado", sort="-y"),
            y=alt.Y("size:Q", title="Cantidad"),
            tooltip=["status", "size"],
        )
        .properties(height=280)
    )
    st.altair_chart(chart_status, use_container_width=True)

with colB:
    ass_counts = (
        filtered.groupby("assignee", as_index=False).size().sort_values("size", ascending=False).head(20)
    )
    chart_ass = (
        alt.Chart(ass_counts)
        .mark_bar()
        .encode(
            y=alt.Y("assignee:N", title="Asignado a", sort="-x"),
            x=alt.X("size:Q", title="Cantidad"),
            tooltip=["assignee", "size"],
        )
        .properties(height=280)
    )
    st.altair_chart(chart_ass, use_container_width=True)

# === Tabla global opcional ===
with st.expander("🗂️ Ver tabla global (todas las tarjetas filtradas)"):
    st.dataframe(
        filtered[["epic_key", "epic_summary", "epic_due_date", "issue_key", "issue_summary", "status", "assignee", "story_points"]],
        use_container_width=True,
        height=400,
    )

# === Detalle por épica ===
st.subheader("Detalle por épica")
for _, e in epics_df[epics_df["epic_key"].isin(filtered["epic_key"].unique())].iterrows():
    ek, es, due = e["epic_key"], e["epic_summary"], e["epic_due_date"]
    df_e = filtered[filtered["epic_key"] == ek].sort_values(["status", "assignee", "issue_key"])
    with st.expander(f"{ek} — {es} | Vence: {due or '—'} | Tarjetas: {len(df_e)}", expanded=False):
        st.dataframe(
            df_e[["issue_key", "issue_summary", "status", "assignee", "story_points"]],
            use_container_width=True,
            height=300,
        )

# # === Descargas ===
# st.download_button(
#     "⬇️ Descargar tarjetas (CSV filtrado)",
#     data=filtered.to_csv(index=False),
#     file_name="tarjetas_filtradas.csv",
#     mime="text/csv",
# )
# st.download_button(
#     "⬇️ Descargar tarjetas (JSON filtrado)",
#     data=filtered.to_json(orient="records", force_ascii=False),
#     file_name="tarjetas_filtradas.json",
#     mime="application/json",
# )
