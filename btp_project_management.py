import json
import requests
from requests.auth import HTTPBasicAuth
from constants import JQL, FIELDS, BASE_URL, JIRA_DOMAIN,EMAIL, MAX_RESULTS, MODULE_DEVS, VALID_STATUSES, MAIL_MAP, DAILY_HOURS,MIN_PROJECT_RATIO,PROJECT_MAP, DEFAULT_END_DATE, DEFAULT_END_DATE_with_timezone, DEFAULT_START_DATE,DEFAULT_START_DATE_with_timezone
from token_hidden import API_TOKEN
EMAIL = EMAIL
API_TOKEN = API_TOKEN

AUTH = HTTPBasicAuth(EMAIL, API_TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

JIRA_API_ROOT = "https://team-1583163151751.atlassian.net/rest/api/3"
SEARCH_JQL_URL = f"{JIRA_API_ROOT}/search/jql"  


def _post_search_jql(jql, fields, next_token=None):
    payload = {
        "jql": jql,
        "fields": fields,
        "maxResults": 100,
    }
    if next_token:
        payload["nextPageToken"] = next_token
    r = requests.post(
        SEARCH_JQL_URL, headers=HEADERS, auth=AUTH, json=payload, timeout=30
    )
    r.raise_for_status()
    return r.json()


def fetch_issues(epic_key):
    """Devuelve todas las tareas hijas de una épica dada."""
    tasks = []
    jql_stories = f'(parent = {epic_key} OR "Epic Link" = {epic_key})'
    next_story = None
    while True:
        story_data = _post_search_jql(
            jql_stories,
            ["key", "summary", "status", "customfield_10016", "assignee", "project"],
            next_token=next_story,
        )
        for st in story_data.get("issues", []):
            sf = st["fields"]
            assignee = sf.get("assignee") or {}
            project = sf.get("project", {}).get("key", "N/A")
            tasks.append(
                {
                    "key": st["key"],
                    "summary": sf.get("summary", ""),
                    "status": (sf.get("status") or {}).get("name", "Sin estado"),
                    "story_points": sf.get("customfield_10016"),
                    "assignee": assignee.get("displayName", "Sin asignar"),
                    "project": project,
                }
            )

        next_story = story_data.get("nextPageToken")
        if not next_story:
            break
    return tasks


def fetch_epics_cross_project():
    all_epics = {}

    # === 1️⃣ Épicas IT ===
    jql_it = "project = IT AND issuetype = Epic"
    token = None
    epics_it = {}
    while True:
        data_it = _post_search_jql(jql_it, ["key", "summary", "duedate"], next_token=token)
        for issue in data_it.get("issues", []):
            epics_it[issue["fields"]["summary"]] = issue["key"]
        token = data_it.get("nextPageToken")
        if not token:
            break

    # === 2️⃣ Buscar épicas en BTP con los mismos nombres ===
    if not epics_it:
        print("⚠️ No se encontraron épicas en IT.")
        return {}

    joined = " OR ".join([f'summary ~ "{name}"' for name in epics_it.keys() if name])
    jql_btp = f"project = BTP AND issuetype = Epic AND ({joined})"

    token = None
    while True:
        data_btp = _post_search_jql(
            jql_btp, ["key", "summary", "duedate"], next_token=token
        )
        for issue in data_btp.get("issues", []):
            epic_key = issue["key"]
            f = issue["fields"]
            summary = f.get("summary")

            all_epics[epic_key] = {
                "due_date": f.get("duedate"),
                "summary": summary,
                "tasks": [],
            }

            # === 3️⃣ Tareas de la épica BTP ===
            tasks_btp = fetch_issues(epic_key)
            all_epics[epic_key]["tasks"].extend(tasks_btp)

            # === 4️⃣ Tareas de la épica IT (mismo nombre)
            if summary in epics_it:
                it_epic_key = epics_it[summary]
                tasks_it = fetch_issues(it_epic_key)
                all_epics[epic_key]["tasks"].extend(tasks_it)

        token = data_btp.get("nextPageToken")
        if not token:
            break

    return all_epics


if __name__ == "__main__":
    result = fetch_epics_cross_project()
    print(f"✅ Épicas cruzadas: {len(result)}")

    output_file = "projectos_bt.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"📁 Archivo guardado: {output_file}")
