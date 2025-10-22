import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Planificación JSON API", layout="centered")
st.title("🧠 API pública — planificacion.json")
st.caption("Sirve el contenido del JSON como endpoint para tu agente GPT o integraciones externas.")

DEFAULT_PATH = "planificacion.json"

# === Selector ===
with st.sidebar:
    st.header("Configuración")
    json_path = st.text_input("Ruta del JSON a servir", DEFAULT_PATH)
    st.info("Podés apuntar a un archivo local o mantener el valor por defecto.")

# === Cargar archivo ===
path = Path(json_path)
if not path.exists():
    st.error(f"No se encontró el archivo {json_path}")
    st.stop()

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# === Mostrar vista previa ===
st.subheader("📋 Vista previa (primeras claves)")
if isinstance(data, dict):
    keys = list(data.keys())[:10]
    st.write({k: data[k] for k in keys})
else:
    st.json(data[:10] if isinstance(data, list) else data)

# === Servir contenido como endpoint ===
st.subheader("🌐 URL pública del JSON")
st.markdown(
    """
    Una vez desplegado el dashboard, podés acceder al JSON directamente con:
    ```bash
    curl https://<tu-dominio-o-render-url>/planificacion.json
    ```
    """
)

# === Opción de descarga directa ===
st.download_button(
    "⬇️ Descargar planificacion.json",
    data=json.dumps(data, ensure_ascii=False, indent=2),
    file_name="planificacion.json",
    mime="application/json",
)

# === Servir JSON "en vivo" ===
st.subheader("🧩 Endpoint JSON embebido")
st.json(data)
