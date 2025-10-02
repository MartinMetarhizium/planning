import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Diferencia entre estados", layout="wide")

st.title("⏱️ Diferencia en horas entre estados")

# === Cargar CSV desde archivo local ===
CSV_PATH = "review_times.csv"   # <-- poné acá el nombre correcto de tu archivo
df = pd.read_csv(CSV_PATH)

# Normalizar columnas de fechas y agregar día base
df["from_date"] = pd.to_datetime(df["from_date"], errors="coerce")
df["to_date"] = pd.to_datetime(df["to_date"], errors="coerce")
df["to_day"] = df["to_date"].dt.date
df["days"] = df["hours"] / 24  # versión en días

# === Filtros ===
st.sidebar.header("Filtros")
assignees = df["assignee"].dropna().unique().tolist()
issue_types = df["issueType"].dropna().unique().tolist()

selected_assignees = st.sidebar.multiselect("Filtrar por persona asignada", options=assignees, default=assignees)
selected_types = st.sidebar.multiselect("Filtrar por tipo de tarea", options=issue_types, default=issue_types)

filtered = df[df["assignee"].isin(selected_assignees) & df["issueType"].isin(selected_types)]

st.write(f"Mostrando {len(filtered)} issues filtrados")

# === Tabla de datos ===
st.dataframe(filtered[["issueKey", "issueType", "assignee", "summary", "from_date", "to_date", "hours"]])

# === Gráfico: Horas promedio por día ===
st.subheader("Promedio de horas por día (to_date)")
daily_hours = filtered.groupby("to_day", as_index=False)["hours"].mean().rename(columns={"hours": "avg_hours"})

chart_hours = alt.Chart(daily_hours).mark_line(point=True).encode(
    x=alt.X("to_day:T", title="Fecha"),
    y=alt.Y("avg_hours:Q", title="Horas promedio"),
    tooltip=["to_day", "avg_hours"]
).properties(height=300)

st.altair_chart(chart_hours, use_container_width=True)

# === Gráfico: Promedio en días ===
st.subheader("Promedio en días por día (to_date)")
daily_days = filtered.groupby("to_day", as_index=False)["days"].mean().rename(columns={"days": "avg_days"})

chart_days = alt.Chart(daily_days).mark_line(point=True, color="green").encode(
    x=alt.X("to_day:T", title="Fecha"),
    y=alt.Y("avg_days:Q", title="Días promedio"),
    tooltip=["to_day", "avg_days"]
).properties(height=300)

st.altair_chart(chart_days, use_container_width=True)

# === Gráfico: Distribución por persona asignada ===
st.subheader("Distribución de horas por persona asignada")
bar = alt.Chart(filtered).mark_bar().encode(
    x=alt.X("assignee:N", title="Persona asignada"),
    y=alt.Y("hours:Q", aggregate="mean", title="Horas promedio"),
    color="assignee:N",
    tooltip=["assignee", "mean(hours)"]
).properties(height=400)

st.altair_chart(bar, use_container_width=True)
