import json
import time
from typing import Any, Dict, Optional

import requests
import streamlit as st


# ==========================================================
# CONFIG
# ==========================================================
st.set_page_config(
    page_title="Actualización ecommerce por país",
    page_icon="🌎",
    layout="wide",
)

COUNTRY_ENDPOINTS: Dict[str, str] = {
    "Chile": "https://ventas.carestino.cl/CRONS/update_store_sale_is_available_via_ecommerce.php",

    "Argentina": "https://ventas.carestino.com/CRONS/update_store_sale_is_available_via_ecommerce.php",
    "Uruguay": "https://ventas.carestino.com.uy/CRONS/update_store_sale_is_available_via_ecommerce.php",
    "Perú": "https://ventas.carestino.com.pe/CRONS/update_store_sale_is_available_via_ecommerce.php",
    "Colombia": "https://ventas.carestino.com.co/CRONS/update_store_sale_is_available_via_ecommerce.php",
    "Mexico": "https://ventas.carestino.com.mx/CRONS/update_store_sale_is_available_via_ecommerce.php",
    "Paraguay": "https://ventas.carestino.com.py/CRONS/update_store_sale_is_available_via_ecommerce.php",
    "Panama": "https://ventas.carestino.com.pa/CRONS/update_store_sale_is_available_via_ecommerce.php",
    "Ecuador": "https://ventas.carestino.com.com.ec/CRONS/update_store_sale_is_available_via_ecommerce.php",
}

REQUEST_TIMEOUT_SECONDS = 180


# ==========================================================
# HELPERS
# ==========================================================
def normalize_response(response: requests.Response, elapsed_seconds: float) -> Dict[str, Any]:
    content_type = (response.headers.get("Content-Type") or "").lower()
    raw_text = response.text or ""

    parsed_json: Optional[Any] = None
    if "json" in content_type:
        try:
            parsed_json = response.json()
        except Exception:
            parsed_json = None
    else:
        try:
            parsed_json = response.json()
        except Exception:
            parsed_json = None

    return {
        "ok": response.ok,
        "status_code": response.status_code,
        "reason": response.reason,
        "content_type": content_type,
        "headers": dict(response.headers),
        "elapsed_seconds": round(elapsed_seconds, 2),
        "raw_text": raw_text.strip(),
        "json": parsed_json,
    }


def call_country_endpoint(url: str) -> Dict[str, Any]:
    started = time.perf_counter()

    try:
        response = requests.post(url, timeout=REQUEST_TIMEOUT_SECONDS)
        elapsed = time.perf_counter() - started
        return normalize_response(response, elapsed)

    except requests.exceptions.Timeout:
        elapsed = time.perf_counter() - started
        return {
            "ok": False,
            "status_code": None,
            "reason": "Timeout",
            "content_type": None,
            "headers": {},
            "elapsed_seconds": round(elapsed, 2),
            "raw_text": f"La request excedió el tiempo de espera de {REQUEST_TIMEOUT_SECONDS} segundos.",
            "json": None,
        }
    except requests.exceptions.RequestException as exc:
        elapsed = time.perf_counter() - started
        return {
            "ok": False,
            "status_code": None,
            "reason": exc.__class__.__name__,
            "content_type": None,
            "headers": {},
            "elapsed_seconds": round(elapsed, 2),
            "raw_text": f"Error ejecutando el POST: {exc}",
            "json": None,
        }


# ==========================================================
# ESTILOS
# ==========================================================
st.markdown(
    """
    <style>
        .main-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }
        .subtitle {
            color: #6b7280;
            margin-bottom: 1.2rem;
        }
        .result-card {
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 1rem 1rem 0.8rem 1rem;
            background: #ffffff;
            margin-top: 0.5rem;
        }
        .metric-pill {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: #f3f4f6;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 0.92rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# STATE
# ==========================================================
if "country_endpoint_result" not in st.session_state:
    st.session_state["country_endpoint_result"] = None


# ==========================================================
# UI
# ==========================================================
st.markdown('<div class="main-title">Actualizar ecommerce por país</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Seleccioná un país para ejecutar el endpoint y ver la respuesta devuelta por el servidor.</div>',
    unsafe_allow_html=True,
)

if not COUNTRY_ENDPOINTS:
    st.warning("No hay países configurados todavía en COUNTRY_ENDPOINTS.")
    st.stop()

country_items = list(COUNTRY_ENDPOINTS.items())
columns = st.columns(min(4, max(1, len(country_items))))

for index, (country_name, country_url) in enumerate(country_items):
    with columns[index % len(columns)]:
        if st.button(f"🌎 {country_name}", use_container_width=True, key=f"country_btn_{country_name}"):
            with st.spinner(f"Ejecutando actualización para {country_name}..."):
                result = call_country_endpoint(country_url)

            st.session_state["country_endpoint_result"] = {
                "country": country_name,
                "url": country_url,
                "result": result,
                "executed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

saved = st.session_state.get("country_endpoint_result")

if saved:
    result = saved["result"]

    st.divider()
    st.subheader(f"Resultado de {saved['country']}")

    if result["ok"]:
        st.success(f"Request completada correctamente. Status code: {result['status_code']}")
    else:
        st.error(
            f"La request falló"
            f"{f' con status {result['status_code']}' if result['status_code'] is not None else ''}."
        )

    st.markdown(
        f"""
        <div class="result-card">
            <div class="metric-pill"><strong>País:</strong> {saved['country']}</div>
            <div class="metric-pill"><strong>Ejecutado en:</strong> {saved['executed_at']}</div>
            <div class="metric-pill"><strong>Tiempo:</strong> {result['elapsed_seconds']} s</div>
            <div class="metric-pill"><strong>Status:</strong> {result['status_code'] or 'Sin respuesta HTTP'}</div>
            <div class="metric-pill"><strong>Content-Type:</strong> {result['content_type'] or 'No informado'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # st.write("**URL ejecutada**")
    # st.code(saved["url"], language="text")

    if result.get("json") is not None:
        st.write("**Respuesta JSON**")
        st.json(result["json"])

        with st.expander("Ver JSON como texto"):
            st.code(json.dumps(result["json"], indent=2, ensure_ascii=False), language="json")
    else:
        st.write("**Respuesta cruda del endpoint**")
        st.text_area(
            "output",
            value=result.get("raw_text", ""),
            height=320,
            key="endpoint_raw_output",
        )

    with st.expander("Ver headers de la respuesta"):
        st.json(result.get("headers", {}))
else:
    st.info("Todavía no ejecutaste ningún país.")