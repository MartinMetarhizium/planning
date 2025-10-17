import time
import json
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth

# ================== CONFIG ==================
JIRA_DOMAIN = "team-1583163151751.atlassian.net"
EMAIL = "martinhorn@biamex.com"

API_TOKEN = st.secrets.get("API_TOKEN")
st.write("🔍 API Token presente:", bool(API_TOKEN))
st.write("🔍 API Token length:", len(API_TOKEN) if API_TOKEN else 0)


AUTH = HTTPBasicAuth(EMAIL, API_TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
me = requests.get(f"https://{JIRA_DOMAIN}/rest/api/3/myself", auth=AUTH, headers=HEADERS)
st.write("🔍 Status code:", me.status_code)
st.write("🔍 Raw response text:", me.text[:500]) 
DEST_PROJECT_KEY = "IT"                      
FIX_FIELD_ID = "customfield_10134"           
FIX_FIELD_VALUE = "nicox-it-testing"


TESTING_FIELD_VISIBLE_NAME = "Canal de TESTING"
TESTING_OPTION_VISIBLE_LABEL = "nicox-it-testing"


DEST_STATUS_NAME = "Pendiente de estimación"


TECH_LEAD_FIELD_ID = "customfield_10208"



def get_issue(issue_key_or_id):
    url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_key_or_id}"
    r = requests.get(url, auth=AUTH, headers=HEADERS)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

@st.cache_data(show_spinner=False, ttl=300)
def get_issue_types_for_project(project_key):
    try:
        url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/createmeta"
        r = requests.get(url, params={"projectKeys": project_key}, auth=AUTH, headers=HEADERS)
        st.write("🔎 Status:", r.status_code)
        st.write("🔎 Response:", r.text)
        r.raise_for_status()
        data = r.json()
        types = []
        for p in data.get("projects", []):
            for it in p.get("issuetypes", []):
                types.append({"id": it["id"], "name": it["name"]})
        types.sort(key=lambda x: x["name"].lower())
        return types
    except Exception as e:
        st.error(f"❌ Error en get_issue_types_for_project: {e}")
        return []

def search_field_id_by_name(field_name_or_id):
    """Devuelve el fieldId (customfield_xxx) por nombre visible (o lo retorna tal cual si ya viene como id)."""
    if field_name_or_id.startswith("customfield_"):
        return field_name_or_id
    url = f"https://{JIRA_DOMAIN}/rest/api/3/field/search"
    r = requests.get(url, params={"query": field_name_or_id}, auth=AUTH, headers=HEADERS)
    r.raise_for_status()
    for f in r.json().get("values", []):
        if f.get("name", "").strip().lower() == field_name_or_id.strip().lower():
            return f["id"]
    return None

def try_get_option_id_from_createmeta(project_key, issue_type_id, field_id, desired_label):
    """
    Intenta leer allowedValues del campo desde createmeta (si el campo está en el create screen).
    NO usa /field/{id}/context (evita permisos de admin).
    """
    url = (f"https://{JIRA_DOMAIN}/rest/api/3/issue/createmeta"
           f"?projectKeys={project_key}&issuetypeIds={issue_type_id}"
           f"&expand=projects.issuetypes.fields")
    r = requests.get(url, auth=AUTH, headers=HEADERS)
    r.raise_for_status()
    data = r.json()

    fields = {}
    for p in data.get("projects", []):
        for it in p.get("issuetypes", []):
            if it.get("id") == issue_type_id:
                fields = it.get("fields", {})
                break

    fdef = fields.get(field_id)
    if not fdef:
        # Fallback por nombre visible del campo
        for fid, fd in fields.items():
            if fd.get("name", "").strip().lower() == TESTING_FIELD_VISIBLE_NAME.strip().lower():
                fdef, field_id = fd, fid
                break

    if not fdef:
        return None

    allowed = fdef.get("allowedValues") or []
    desired = desired_label.strip().lower()
    for opt in allowed:
        label = (opt.get("value") or opt.get("name") or "").strip().lower()
        if label == desired:
            return str(opt.get("id") or opt.get("optionId") or "")
    return None


@st.cache_data(show_spinner=False, ttl=300)
def get_assignable_users(project_key, query=None, max_results=1000):
    """
    Devuelve los usuarios asignables al proyecto (para selects de Assignee/Tech Lead).
    """
    url = f"https://{JIRA_DOMAIN}/rest/api/3/user/assignable/search"
    params = {"project": project_key, "maxResults": max_results}
    if query:
        params["query"] = query
    r = requests.get(url, params=params, auth=AUTH, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def update_fix_field_by_issue_id(issue_id, value):
    """Setea el customfield del Fix por ID (sirve aunque cambie el key)."""
    url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_id}"
    payload = {"fields": {FIX_FIELD_ID: {"value": value}}}
    r = requests.put(url, auth=AUTH, headers=HEADERS, json=payload)
    r.raise_for_status()

def update_assignee_and_techlead(issue_id, assignee_account_id=None, techlead_account_id=None):
    """
    Actualiza Assignee y/o Tech Lead en el issue por ID.
    - 'assignee' es un único usuario (objeto).
    - 'customfield_10208' (Tech Lead) en tu instancia es múltiple → array de objetos.
    """
    base_fields = {}

    if assignee_account_id:
        base_fields["assignee"] = {"accountId": assignee_account_id}

    if techlead_account_id:
       
        base_fields[TECH_LEAD_FIELD_ID] = [{"accountId": techlead_account_id}]

    if not base_fields:
        return

    url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_id}"
    payload = {"fields": base_fields}
    r = requests.put(url, auth=AUTH, headers=HEADERS, json=payload)
    r.raise_for_status()

# ---------- Transiciones (post-move) ----------
def list_transitions(issue_id):
    url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_id}/transitions"
    r = requests.get(url, auth=AUTH, headers=HEADERS)
    r.raise_for_status()
    return r.json().get("transitions", [])

def get_transition_id(issue_id, target_status_name):
    """Busca una transición disponible cuyo 'to.name' coincida con el estado deseado."""
    target = target_status_name.strip().lower()
    for t in list_transitions(issue_id):
        if (t.get("to", {}).get("name", "") or "").strip().lower() == target:
            return t.get("id")
    return None

def do_transition(issue_id, transition_id):
    url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_id}/transitions"
    payload = {"transition": {"id": str(transition_id)}}
    r = requests.post(url, auth=AUTH, headers=HEADERS, json=payload)
    r.raise_for_status()



def bulk_move_issue(
    issue_id_or_key,
    target_project_key,
    target_issue_type_id,
    include_testing_field=False,      # True si es Fix
    show_debug_payload=False
):
    """
    POST /rest/api/3/bulk/issues/move
    - Si include_testing_field=True: enviamos targetMandatoryFields y ponemos inferFieldDefaults=False.
    - Si NO: no enviamos targetMandatoryFields y usamos inferFieldDefaults=True.
    - Dejamos que el move elija estado inicial; si hace falta, transicionamos después.
    """
    testing_field_block = None
    infer_field_defaults = True

    if include_testing_field:
        testing_field_id = search_field_id_by_name(TESTING_FIELD_VISIBLE_NAME)
        if not testing_field_id:
            raise RuntimeError(f"No se encontró el fieldId para '{TESTING_FIELD_VISIBLE_NAME}'")

        
        opt_id = try_get_option_id_from_createmeta(
            project_key=target_project_key,
            issue_type_id=target_issue_type_id,
            field_id=testing_field_id,
            desired_label=TESTING_OPTION_VISIBLE_LABEL
        )
        value_payload = [opt_id] if opt_id else [TESTING_OPTION_VISIBLE_LABEL]

        testing_field_block = [
            {
                "fields": {
                    testing_field_id: {
                        "retain": False,
                        "type": "raw",
                        "value": value_payload
                    }
                }
            }
        ]
        infer_field_defaults = False  

    target_key = f"{target_project_key},{target_issue_type_id}"

    mapping = {
        "issueIdsOrKeys": [issue_id_or_key],
        "inferClassificationDefaults": True,
        "inferFieldDefaults": infer_field_defaults,
        "inferStatusDefaults": True,   
        "inferSubtaskTypeDefault": True,
    }
    if testing_field_block:
        mapping["targetMandatoryFields"] = testing_field_block

    payload = {
        "sendBulkNotification": True,
        "targetToSourcesMapping": { target_key: mapping }
    }

    if show_debug_payload:
        st.code(json.dumps(payload, indent=2, ensure_ascii=False), language="json")

    url = f"https://{JIRA_DOMAIN}/rest/api/3/bulk/issues/move"
    r = requests.post(url, auth=AUTH, headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json() if r.text else {}

modo = st.selectbox(
    "Elegí qué querés hacer",
    ["Mover BTP → IT", "Crear actividad BTP desde SD", "Crear actividad IT desde SD"]
)

if modo == "Mover BTP → IT":
    st.title("Mover tarjeta de BTP → IT")

    src_key = st.text_input("Número de tarjeta origen (ej: BTP-3818)", value="")
    show_debug = st.checkbox("Mostrar payload de Bulk Move (debug)", value=False)

    with st.spinner("Cargando tipos de issue del proyecto IT..."):
        try:
            it_types = get_issue_types_for_project(DEST_PROJECT_KEY)
        except Exception as e:
            it_types = []
            st.error(f"No se pudieron obtener los tipos de issue de {DEST_PROJECT_KEY}: {e}")

    if not it_types:
        st.stop()

    type_name_to_id = {t["name"]: t["id"] for t in it_types}
    selected_type_name = st.selectbox(
        "Tipo de issue destino en IT",
        list(type_name_to_id.keys())
    )
    selected_type_id = type_name_to_id[selected_type_name]
    is_fix = selected_type_name.strip().lower() == "fix"


    with st.spinner("Cargando usuarios asignables en IT..."):
        try:
            assignable_users = get_assignable_users(DEST_PROJECT_KEY)
        except Exception as e:
            assignable_users = []
            st.error(f"No se pudieron cargar los usuarios asignables: {e}")

    label_to_account = {}
    labels = ["(No cambiar)"]
    if assignable_users:
        for u in assignable_users:
            name = u.get("displayName") or u.get("name") or "Usuario"
            acc = u.get("accountId")
            label = f"{name} · {acc[-6:]}" if acc else name
            label_to_account[label] = acc
            labels.append(label)

    DEFAULT_TECHLEAD_NAME = "Diego Martin Gogorza"
    DEFAULT_TECHLEAD_SUFFIX = "811b4c"

    default_techlead_index = 0
    for i, lbl in enumerate(labels):
        if DEFAULT_TECHLEAD_NAME.lower() in lbl.lower():
            default_techlead_index = i
            if DEFAULT_TECHLEAD_SUFFIX and DEFAULT_TECHLEAD_SUFFIX in lbl:
                break

    colA, colB = st.columns(2)
    with colA:
        assignee_label = st.selectbox("Assignee (IT)", labels, index=0)
    with colB:
        techlead_label = st.selectbox("Tech Lead (IT)", labels, index=default_techlead_index)

    assignee_account_id = label_to_account.get(assignee_label)
    techlead_account_id = label_to_account.get(techlead_label)

    if st.button("Mover a IT"):
        if not src_key.strip():
            st.error("Ingresá la tarjeta de origen (por ejemplo BTP-3818).")
            st.stop()

        with st.spinner("Verificando issue origen..."):
            src_issue = get_issue(src_key.strip())
            if not src_issue:
                st.error("⚠️ No se encontró el issue o faltan permisos (Browse issues).")
                st.stop()
            issue_id = src_issue["id"]

        with st.spinner("Ejecutando Bulk Move hacia IT..."):
            try:
                move_res = bulk_move_issue(
                    issue_id_or_key=issue_id,
                    target_project_key=DEST_PROJECT_KEY,
                    target_issue_type_id=selected_type_id,
                    include_testing_field=is_fix,
                    show_debug_payload=show_debug
                )
            except requests.HTTPError as e:
                st.error(f"Error en Bulk Move: {e}\n\n{e.response.text if e.response is not None else ''}")
                st.stop()
            except Exception as e:
                st.error(f"Error en Bulk Move: {e}")
                st.stop()

        new_key = None
        current_status_name = None
        for _ in range(8):
            try:
                moved_issue = get_issue(issue_id)  
                if moved_issue:
                    k = moved_issue.get("key", "")
                    if k.startswith(f"{DEST_PROJECT_KEY}-"):
                        new_key = k
                    current_status_name = (moved_issue.get("fields", {})
                                                    .get("status", {})
                                                    .get("name", None))
                    if new_key and current_status_name:
                        break
            except Exception:
                pass
            time.sleep(0.7)


        if assignee_account_id or techlead_account_id:
            with st.spinner("Actualizando Assignee / Tech Lead..."):
                try:
                    update_assignee_and_techlead(
                        issue_id,
                        assignee_account_id=assignee_account_id,
                        techlead_account_id=techlead_account_id
                    )
                except requests.HTTPError as e:
                    st.error(f"Se movió, pero falló actualizar Assignee/Tech Lead: {e}\n\n{e.response.text if e.response is not None else ''}")
                except Exception as e:
                    st.error(f"Se movió, pero falló actualizar Assignee/Tech Lead: {e}")

        if is_fix:
            with st.spinner("Aplicando campo de Fix en el issue movido..."):
                try:
                    update_fix_field_by_issue_id(issue_id, FIX_FIELD_VALUE)
                except requests.HTTPError as e:
                    st.error(f"Se movió, pero falló setear {FIX_FIELD_ID}: {e}\n\n{e.response.text if e.response is not None else ''}")
                except Exception as e:
                    st.error(f"Se movió, pero falló setear {FIX_FIELD_ID}: {e}")

        if (current_status_name or "").strip().lower() != DEST_STATUS_NAME.strip().lower():
            from_status = current_status_name or "desconocido"
            with st.spinner(f"Transicionando a '{DEST_STATUS_NAME}'..."):
                t_id = get_transition_id(issue_id, DEST_STATUS_NAME)
                if t_id:
                    try:
                        do_transition(issue_id, t_id)
                        st.success(f"✅ Estado actualizado a **{DEST_STATUS_NAME}**")
                    except requests.HTTPError as e:
                        st.error(f"⚠️ Falló la transición a '{DEST_STATUS_NAME}': {e}\n\n{e.response.text if e.response is not None else ''}")
                else:
                    pass

        if new_key:
            st.success(
                f"Movido a **{DEST_PROJECT_KEY}** como **{selected_type_name}** → "
                f"[{new_key}](https://{JIRA_DOMAIN}/browse/{new_key})"
            )
        else:
            st.success(
                f" Movido a **{DEST_PROJECT_KEY}** como **{selected_type_name}** "
                f"(no se pudo recuperar el nuevo key automáticamente; ID={issue_id})."
            )



# ================== FUNCIONES AUXILIARES ==================

def create_issue_from_sd(sd_key: str, issue_type_id: str, assignee: str = None, tech_lead: str = None, project: str = None):
    """
    Crea una nueva issue en un proyecto solicitda copiando summary, description, duedate, priority desde la SD original.
    Devuelve la key de la nueva issue creada.
    """
    # 1️⃣ Obtener datos de la SD original
    sd_issue = get_issue(sd_key)
    if not sd_issue:
        raise ValueError("No se pudo obtener la SD original.")

    fields = sd_issue.get("fields", {})
    summary = fields.get("summary")
    description = fields.get("description")  # ✅ copiamos con formato ADF completo
    due_date = fields.get("duedate")
    priority = fields.get("priority", {}).get("id")

    # 2️⃣ Crear nueva issue en BTP
    create_url = f"https://{JIRA_DOMAIN}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": project},
            "issuetype": {"id": issue_type_id},
            "summary": summary,
            "reporter": {"accountId": tech_lead},
            "description": description
        }
    }

    if due_date:
        payload["fields"]["duedate"] = due_date
    if priority:
        payload["fields"]["priority"] = {"id": priority}
    if assignee:
        payload["fields"]["assignee"] = {"accountId": assignee}
    

    r = requests.post(create_url, auth=AUTH, headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json().get("key")

def link_issues_causes(sd_key: str, new_btp_key: str):
    """
    Crea un vínculo 'Problem/Incident' con relación 'causes' entre la nueva issue de BTP y la SD original.
    - new_btp_key ➡️ causes ➡️ sd_key
    """
    url = f"https://{JIRA_DOMAIN}/rest/api/3/issueLink"
    payload = {
        "type": {"name": "Problem/Incident"},  # ✅ nombre correcto
        "inwardIssue": {"key": new_btp_key},         # la SD original
        "outwardIssue": {"key": sd_key}    # la nueva actividad BTP
    }

    r = requests.post(url, auth=AUTH, headers=HEADERS, json=payload)
    r.raise_for_status()

# ================== UI DEL NUEVO FLUJO ==================

if modo == "Crear actividad BTP desde SD":

    st.header("Crear actividad en BTP a partir de una SD")

    sd_key = st.text_input("Número de SD (ej: SD-1234)")

    # Obtener tipos de issue de BTP
    with st.spinner("Cargando tipos de issue de BTP..."):
        try:
            btp_types = get_issue_types_for_project("BTP")
        except Exception as e:
            btp_types = []
            st.error(f"No se pudieron obtener los tipos de issue: {e}")

    if not btp_types:
        st.stop()

    type_name_to_id_btp = {t["name"]: t["id"] for t in btp_types}
    selected_btp_type = st.selectbox("Tipo de actividad en BTP", list(type_name_to_id_btp.keys()))
    selected_btp_type_id = type_name_to_id_btp[selected_btp_type]

    # Usuarios asignables en BTP
    with st.spinner("Cargando usuarios asignables..."):
        try:
            assignable_users_btp = get_assignable_users("BTP")
        except Exception as e:
            assignable_users_btp = []
            st.error(f"No se pudieron cargar usuarios: {e}")

    label_to_account_btp = {}
    labels_btp = ["(No asignar)"]
    if assignable_users_btp:
        for u in assignable_users_btp:
            name = u.get("displayName") or u.get("name") or "Usuario"
            acc = u.get("accountId")
            label = f"{name} · {acc[-6:]}" if acc else name
            label_to_account_btp[label] = acc
            labels_btp.append(label)

    # Tech Lead por defecto
    DEFAULT_TECHLEAD_NAME = "Thiago Cabrera"
    DEFAULT_TECHLEAD_SUFFIX = "ae45ae"
    default_techlead_index = 0
    for i, lbl in enumerate(labels_btp):
        if DEFAULT_TECHLEAD_NAME.lower() in lbl.lower() and DEFAULT_TECHLEAD_SUFFIX in lbl:
            default_techlead_index = i
            break

    col1, col2 = st.columns(2)
    with col1:
        assignee_label_btp = st.selectbox("Assignee (BTP)", labels_btp, index=0)
    with col2:
        techlead_label_btp = st.selectbox("Informador (BTP)", labels_btp, index=default_techlead_index)

    assignee_id_btp = label_to_account_btp.get(assignee_label_btp)
    techlead_id_btp = label_to_account_btp.get(techlead_label_btp)

    if st.button("Crear actividad vinculada en BTP"):
        if not sd_key.strip():
            st.error("⚠️ Ingresá el número de SD (por ejemplo SD-1234).")
            st.stop()

        try:
            with st.spinner("Creando actividad en BTP..."):
                new_btp_key = create_issue_from_sd(
                    sd_key=sd_key.strip(),
                    issue_type_id=selected_btp_type_id,
                    assignee=assignee_id_btp,
                    tech_lead=techlead_id_btp,
                    project="BTP"
                )

            with st.spinner("Vinculando con SD original..."):
                link_issues_causes(sd_key.strip(), new_btp_key)

            st.success(
                f"✅ Actividad creada correctamente en **BTP** → "
                f"[{new_btp_key}](https://{JIRA_DOMAIN}/browse/{new_btp_key}) y vinculada a {sd_key.strip()} con relación **Causes**."
            )

        except requests.HTTPError as e:
            st.error(f"❌ Error creando actividad: {e}\n\n{e.response.text if e.response is not None else ''}")
        except Exception as e:
            st.error(f"❌ Error inesperado: {e}")



if modo == "Crear actividad IT desde SD":

    st.header("Crear actividad en IT a partir de una SD")

    sd_key = st.text_input("Número de SD (ej: SD-1234)")

    # Obtener tipos de issue de BTP
    with st.spinner("Cargando tipos de issue de IT..."):
        try:
            btp_types = get_issue_types_for_project("IT")
        except Exception as e:
            btp_types = []
            st.error(f"No se pudieron obtener los tipos de issue: {e}")

    if not btp_types:
        st.stop()

    type_name_to_id_btp = {t["name"]: t["id"] for t in btp_types}
    selected_btp_type = st.selectbox("Tipo de actividad en IT", list(type_name_to_id_btp.keys()))
    selected_btp_type_id = type_name_to_id_btp[selected_btp_type]

    # Usuarios asignables en BTP
    with st.spinner("Cargando usuarios asignables..."):
        try:
            assignable_users_btp = get_assignable_users("IT")
        except Exception as e:
            assignable_users_btp = []
            st.error(f"No se pudieron cargar usuarios: {e}")

    label_to_account_btp = {}
    labels_btp = ["(No asignar)"]
    if assignable_users_btp:
        for u in assignable_users_btp:
            name = u.get("displayName") or u.get("name") or "Usuario"
            acc = u.get("accountId")
            label = f"{name} · {acc[-6:]}" if acc else name
            label_to_account_btp[label] = acc
            labels_btp.append(label)

    # Tech Lead por defecto
    DEFAULT_TECHLEAD_NAME = "Diego Martin Gogorza"
    DEFAULT_TECHLEAD_SUFFIX = "811b4c"
    default_techlead_index = 0
    for i, lbl in enumerate(labels_btp):
        if DEFAULT_TECHLEAD_NAME.lower() in lbl.lower() and DEFAULT_TECHLEAD_SUFFIX in lbl:
            default_techlead_index = i
            break

    col1, col2 = st.columns(2)
    with col1:
        assignee_label_btp = st.selectbox("Assignee (IT)", labels_btp, index=0)
    with col2:
        techlead_label_btp = st.selectbox("Tech lead (IT)", labels_btp, index=default_techlead_index)

    assignee_id_btp = label_to_account_btp.get(assignee_label_btp)
    techlead_id_btp = label_to_account_btp.get(techlead_label_btp)

    if st.button("Crear actividad vinculada en IT"):
        if not sd_key.strip():
            st.error("⚠️ Ingresá el número de SD (por ejemplo SD-1234).")
            st.stop()

        try:
            with st.spinner("Creando actividad en IT..."):
                new_btp_key = create_issue_from_sd(
                    sd_key=sd_key.strip(),
                    issue_type_id=selected_btp_type_id,
                    assignee=assignee_id_btp,
                    tech_lead=techlead_id_btp,
                    project="IT"
                )

            with st.spinner("Vinculando con SD original..."):
                link_issues_causes(sd_key.strip(), new_btp_key)

            st.success(
                f"✅ Actividad creada correctamente en **IT** → "
                f"[{new_btp_key}](https://{JIRA_DOMAIN}/browse/{new_btp_key}) y vinculada a {sd_key.strip()} con relación **Causes**."
            )

        except requests.HTTPError as e:
            st.error(f"❌ Error creando actividad: {e}\n\n{e.response.text if e.response is not None else ''}")
        except Exception as e:
            st.error(f"❌ Error inesperado: {e}")