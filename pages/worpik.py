import os
import re
import json
import base64
import platform
import shutil
from io import BytesIO
from typing import List, Dict

import streamlit as st
from openai import OpenAI
from PIL import Image


import pytesseract
import platform
import os
import streamlit as st


def _discover_poppler_path() -> str:
    if platform.system() != "Windows":
        return ""  # en Linux/Mac no lo uses (pdf2image lo encuentra en PATH)
    # 1) Si está en PATH del sistema:
    if shutil.which("pdftoppm"):
        return ""  # no hace falta path explícito
    # 2) Si estás en conda, suele estar en <CONDA_PREFIX>\Library\bin
    conda_prefix = os.environ.get("CONDA_PREFIX") or os.environ.get("PREFIX")
    if conda_prefix:
        cand = os.path.join(conda_prefix, "Library", "bin")
        if os.path.exists(os.path.join(cand, "pdftoppm.exe")):
            return cand
    # 3) Tus rutas conocidas (ajusta si hace falta)
    candidates = [
        r"C:\Users\Martin\anaconda3\Library\bin",
        r"C:\Users\Martin\anaconda3\pkgs\poppler-23.12.0-hc2f3c52_0\Library\bin",
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files\poppler-24.07.0\Library\bin",
    ]
    for cand in candidates:
        if os.path.exists(os.path.join(cand, "pdftoppm.exe")):
            return cand
    return ""  # si no encontramos nada, pdf2image tirará un error útil

POPPLER_PATH = _discover_poppler_path()

API_KEY = st.secrets.get("API_KEY")

# ---------- 3) Parámetros de API (OpenRouter mediante cliente de OpenAI) ----------
# Guardá tu clave como secreto OPENROUTER_API_KEY en .streamlit/secrets.toml o variable de entorno.
# API_KEY = st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
HTTP_REFERER = "https://planning-carestino.streamlit.app/"
X_TITLE =  "CarestinoApp"







def need_api_key() -> bool:
    if not API_KEY:
        st.error("Falta `OPENROUTER_API_KEY` (secrets.toml o variable de entorno).")
        return True
    return False

# =============================
# Poppler (Windows) para pdf2image
# =============================
def _discover_poppler_path() -> str:
    if platform.system() != "Windows":
        return ""
    if shutil.which("pdftoppm"):
        return ""
    conda_prefix = os.environ.get("CONDA_PREFIX") or os.environ.get("PREFIX")
    if conda_prefix:
        cand = os.path.join(conda_prefix, "Library", "bin")
        if os.path.exists(os.path.join(cand, "pdftoppm.exe")):
            return cand
    candidates = [
        r"C:\Users\Martin\anaconda3\Library\bin",
        r"C:\Users\Martin\anaconda3\pkgs\poppler-23.12.0-hc2f3c52_0\Library\bin",
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files\poppler-24.07.0\Library\bin",
    ]
    for cand in candidates:
        if os.path.exists(os.path.join(cand, "pdftoppm.exe")):
            return cand
    return ""

POPPLER_PATH = _discover_poppler_path()

# =============================
# Página
# =============================
st.set_page_config(page_title="Consulta de carreras", page_icon="🎓", layout="wide")
st.title("🎓 Consulta de carreras en archivos (visión con fallback a texto)")

CARRERAS = [
    "Ingeniería en Sistemas", "Ciencia de Datos", "Ingeniería Industrial", "Administración de Empresas",
    "Contador Público", "Economía", "Marketing", "Recursos Humanos",
    "Diseño Gráfico", "Diseño UX/UI", "Comunicación Social",
    "Psicología", "Abogacía (Derecho)", "Arquitectura", "Ingeniería Agronómica",
    "Medicina", "Enfermería", "Farmacia", "Bioquímica",
    "Ingeniería Civil", "Ingeniería Electrónica", "Ingeniería Mecánica",
    "Ingeniería en Informática",
]
col_a, col_b = st.columns([1.3, 1])
with col_a:
    carrera = st.selectbox("Carrera a buscar", CARRERAS, index=0)
with col_b:
    VISION_MODELS = {
        "deepseek/deepseek-chat-v3.1:free": "deepseek free",
        "openai/gpt-oss-20b:free": "gpt free",
        # "qwen/qwen2.5-vl-7b-instruct":  "Qwen2.5-VL 7B (visión)",
        # "meta-llama/llama-3.2-11b-vision-instruct:free": "Llama 3.2 11B Vision (free)",
        # "openai/gpt-4o-mini": "GPT-4o mini (visión)",
    }
    modelo_vision = st.selectbox(
        "Modelo de visión (primero intenta con esto)",
        list(VISION_MODELS.keys()),
        index=0,
        format_func=lambda k: VISION_MODELS[k],
    )

# Modelo texto-solo de fallback
TEXT_FALLBACK_MODEL = st.selectbox(
    "Modelo texto (fallback)",
    ["deepseek/deepseek-chat-v3.1:free", 
     "openai/gpt-oss-20b:free",
    #  "openai/gpt-4o-mini"
     ],  # gpt-4o-mini también sirve como texto
    index=0,
)

st.markdown("#### Archivos")
st.caption("Soportado: **.pdf**, **.png**, **.jpg**, **.jpeg**, **.webp**, **.docx**, **.txt**, **.md**, **.csv**")
uploads = st.file_uploader(
    "Arrastrá o elegí archivos",
    type=["pdf", "png", "jpg", "jpeg", "webp", "docx", "txt", "md", "csv"],
    accept_multiple_files=True,
)

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    max_pages_per_file = st.number_input("Máx. páginas por archivo (PDF/Imagen→visión)", 1, 20, 6, 1)
with col2:
    dpi = st.number_input("DPI (PDF→imagen)", 100, 300, 150, 25)
with col3:
    preview = st.toggle("Previsualizar primeras imágenes", value=False)

st.divider()

# =============================
# Utilidades (visión)
# =============================
def pdf_to_b64_images(file_bytes: bytes, dpi: int = 150, max_pages: int = 6) -> List[str]:
    try:
        from pdf2image import convert_from_bytes
    except Exception:
        st.error("Falta `pdf2image` (pip install pdf2image).")
        raise
    if POPPLER_PATH:
        pages = convert_from_bytes(file_bytes, dpi=dpi, poppler_path=POPPLER_PATH)
    else:
        pages = convert_from_bytes(file_bytes, dpi=dpi)
    urls = []
    for im in pages[:max_pages]:
        buf = BytesIO()
        im.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        urls.append(f"data:image/png;base64,{b64}")
    return urls

def image_file_to_data_url(upload) -> str:
    img = Image.open(upload)
    buf = BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

# =============================
# Utilidades (texto)
# =============================
def read_text_from_upload(upload) -> str:
    """Extrae texto de TXT, DOCX, PDF o usa OCR para imágenes/PDF escaneados."""
    name = (upload.name or "").lower()
    data = upload.read()
    upload.seek(0)

    # TXT / CSV
    if name.endswith((".txt", ".md", ".csv")):
        return data.decode("utf-8", errors="ignore")

    # DOCX
    if name.endswith(".docx"):
        from docx import Document
        doc = Document(BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)

    # PDF: primero intentar texto embebido
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(data))
            pages = [p.extract_text() or "" for p in reader.pages]
            text = "\n".join(pages).strip()
            if text:
                return text
        except Exception:
            pass

        # Si no hay texto → OCR con pdf2image + pytesseract
        from pdf2image import convert_from_bytes
        import pytesseract

        pages = convert_from_bytes(data, dpi=150, poppler_path=POPPLER_PATH)
        texts = []
        for im in pages:
            txt = pytesseract.image_to_string(im, lang="spa+eng")  # podés cambiar idiomas
            if txt.strip():
                texts.append(txt)
        return "\n".join(texts).strip()

    # Imagen → OCR directo
    if any(name.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp")):
        import pytesseract
        img = Image.open(BytesIO(data))
        return pytesseract.image_to_string(img, lang="spa+eng")

    return ""

def have_tesseract() -> bool:
    try:
        import pytesseract  # noqa
    except Exception:
        return False
    # En Windows podés configurar ruta si no está en PATH:
    if platform.system() == "Windows":
        import pytesseract as pt
        if not shutil.which("tesseract"):
            guesses = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            for g in guesses:
                if os.path.exists(g):
                    pt.pytesseract.tesseract_cmd = g
                    return True
            return False
    return True

def ocr_images_locally(image_urls: List[str]) -> str:
    """OCR con pytesseract si está disponible. image_urls = data URLs PNG."""
    try:
        import pytesseract
    except Exception:
        return ""  # no hay OCR local
    texts = []
    for url in image_urls:
        if not url.startswith("data:image/"):
            continue
        b64 = url.split(",", 1)[1]
        img = Image.open(BytesIO(base64.b64decode(b64)))
        try:
            txt = pytesseract.image_to_string(img)  # (opcional) lang='spa'
        except Exception:
            txt = ""
        if txt and txt.strip():
            texts.append(txt)
    return "\n".join(texts).strip()

# =============================
# Prompts / mensajes
# =============================
def build_prompt_vision(carrera: str) -> str:
    alias_map = {
        "ingeniería en sistemas": [
            "ingenieria en sistemas", "ingeniería en informática", "ingenieria en informatica",
            "ingeniería en computación", "ingenieria en computacion",
            "ingeniería en sistemas de información", "ingeniería de sistemas",
            "ing. en sistemas", "ing sistemas", "ing en informatica",
            "computer engineering",
        ],
        "ingeniería en informática": [
            "ingeniería informática", "ingenieria informatica", "ingeniería en sistemas",
            "ingeniería en computación", "computer engineering",
        ],
        "ciencia de datos": [
            "data science", "ciencias de datos", "analítica de datos", "data analytics",
        ],
    }
    sinonimos = alias_map.get(carrera.strip().lower(), [])
    sinonimos_str = ", ".join(f"\"{s}\"" for s in sinonimos)
    return f"""
Actuá como verificador. ¿Aparece la carrera pedida en el documento (incluso escaneado)?
CARRERA_BASE: "{carrera}"
TRATAR COMO SINÓNIMOS EQUIVALENTES: [{sinonimos_str}]
Devolvé SOLO JSON:
{{"encontrada": true/false, "alias_detectado": "<string|null>", "evidencia": "<frase>", "motivo": "<opcional>"}}
""".strip()

def build_messages_for_verification(carrera: str, image_urls: List[str]):
    parts = [{"type": "text", "text": build_prompt_vision(carrera)}]
    for url in image_urls:
        parts.append({"type": "image_url", "image_url": {"url": url}})
    parts.append({"type": "text", "text": "Respondé SOLO el JSON solicitado."})
    return [
        {"role": "system", "content": "Eres un verificador muy preciso y conciso."},
        {"role": "user", "content": parts},
    ]

def build_text_prompt(carrera: str, texts: List[str]) -> str:
    joined = "\n\n---\n\n".join(texts)
    if len(joined) > 120_000:
        joined = joined[:120_000] + "\n\n[TRUNCADO]\n"
    return f"""
Analizá el/los texto(s) (extraídos de archivos subidos).
¿Aparece "{carrera}" (o sinónimos obvios) como carrera/título/programa?
Devolvé SOLO JSON:
{{"encontrada": true/false, "evidencia": "<línea o frase>", "motivo": "<opcional>"}}

Textos:
{joined}
""".strip()

def parse_json_safely(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text), None
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0)), None
            except Exception as e:
                return None, f"No se pudo parsear JSON: {e}"
    return None, "No se encontró JSON en la respuesta."

# =============================
# Llamadas API y fallback
# =============================
def call_chat(client: OpenAI, model: str, messages: list):
    return client.chat.completions.create(
        model=model,
        temperature=0.0,
        extra_headers={"HTTP-Referer": HTTP_REFERER, "X-Title": X_TITLE},
        messages=messages,
    )

def try_vision_then_text(
    client: OpenAI,
    modelo_vision: str,
    image_urls: List[str],
    carrera: str,
    text_fallback_model: str,
    uploads_for_text: List
):
    """Primero intenta VISIÓN; si falla/no soporta imágenes → convierte a texto y usa modelo TEXT."""
    # 1) VISIÓN
    try:
        messages_v = build_messages_for_verification(carrera, image_urls)
        completion = call_chat(client, modelo_vision, messages_v)
        raw = completion.choices[0].message.content or ""
        data, err = parse_json_safely(raw)
        return ("vision", data, err, raw)
    except Exception as e:
        msg = str(e)
        # Típico en OpenRouter cuando no acepta imagen para tu cuenta:
        if ("No endpoints found that support image input" in msg) or ("does not support image input" in msg):
            st.warning(f"El modelo de visión '{modelo_vision}' no acepta imágenes en tu cuenta. Fallback a texto…")
        else:
            st.info(f"Fallo visión: {e}. Fallback a texto…")

    # 2) TEXTO (fallback): extraer texto localmente
    texts = []
    for up in uploads_for_text:
        name = (up.name or "").lower()
        if any(name.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp")):
            # intentar OCR local si existe
            txt_ocr = ocr_images_locally([image_file_to_data_url(up)])
            if txt_ocr:
                texts.append(f"[{up.name}]\n{txt_ocr}")
            else:
                texts.append(f"[{up.name}] (sin texto legible; instala Tesseract+pytesseract para OCR local)")
        else:
            t = read_text_from_upload(up)
            if t.strip():
                texts.append(f"[{up.name}]\n{t}")
            else:
                # último recurso: si es PDF escaneado sin OCR local, avisar
                texts.append(f"[{up.name}] (sin texto extraíble)")

    if not texts:
        return ("text", None, "No se pudo obtener texto para el fallback.", "")

    prompt_txt = build_text_prompt(carrera, texts)
    try:
        completion_t = call_chat(client, text_fallback_model, [{"role": "user", "content": prompt_txt}])
        raw_t = completion_t.choices[0].message.content or ""
        data_t, err_t = parse_json_safely(raw_t)
        return ("text", data_t, err_t, raw_t)
    except Exception as e2:
        return ("text", None, f"Error en fallback de texto: {e2}", "")

# =============================
# Acciones
# =============================
col_run1, col_run2 = st.columns([1, 1])
with col_run1:
    run = st.button("🔎 Verificar (visión → texto)", type="primary", use_container_width=True)
with col_run2:
    clear = st.button("Limpiar", use_container_width=True)

if clear:
    st.rerun()

if run:
    if need_api_key():
        st.stop()
    if not uploads:
        st.warning("Subí al menos un archivo.")
        st.stop()

    # Preparar imágenes para VISIÓN
    all_imgs: List[str] = []
    with st.spinner("Preparando entradas para visión…"):
        for up in uploads:
            name = (up.name or "").lower()
            if name.endswith(".pdf"):
                try:
                    urls = pdf_to_b64_images(up.getvalue(), dpi=dpi, max_pages=max_pages_per_file)
                    all_imgs.extend(urls)
                except Exception as e:
                    st.error(f"Error convirtiendo {up.name}: {e}")
            elif any(name.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp")):
                try:
                    all_imgs.append(image_file_to_data_url(up))
                except Exception as e:
                    st.error(f"No se pudo procesar imagen {up.name}: {e}")
            # docx/txt/md/csv solo van al fallback de texto

    if preview and all_imgs:
        st.markdown("**Previsualización (primeras imágenes):**")
        for url in all_imgs[:min(4, len(all_imgs))]:
            st.image(url, use_container_width=True)

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)

    mode, data, err, raw = try_vision_then_text(
        client=client,
        modelo_vision=modelo_vision,
        image_urls=all_imgs,
        carrera=carrera,
        text_fallback_model=TEXT_FALLBACK_MODEL,
        uploads_for_text=uploads,
    )

    st.subheader("Resultado")
    st.caption(f"Ruta usada: **{('Visión' if mode=='vision' else 'Texto (fallback)')}**")

    if data:
        colr1, colr2 = st.columns([1, 2])
        with colr1:
            ok = bool(data.get("encontrada"))
            st.metric("Encontrada", "Sí ✅" if ok else "No ❌")
            if "alias_detectado" in data:
                st.caption(f"Alias: {data.get('alias_detectado')}")
        with colr2:
            st.markdown("**Evidencia**")
            st.info(data.get("evidencia") or "—")
            if data.get("motivo"):
                st.markdown("**Motivo**")
                st.write(data.get("motivo"))
        with st.expander("JSON devuelto"):
            st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")
    else:
        st.warning(err or "No se pudo interpretar la salida.")
        if raw:
            with st.expander("Salida cruda"):
                st.code(raw)