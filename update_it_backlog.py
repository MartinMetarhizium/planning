#!/usr/bin/env python3
# coding: utf-8
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# CONFIG — adaptá si cambia
JIRA_DOMAIN = "https://team-1583163151751.atlassian.net"
BOARD_ID = 1
EMAIL = "martinhorn@biamex.com"
API_TOKEN = "<TU_TOKEN_AQUI>"

SHEET_ID = "1qP_7gFcgA0q4kb8sgfdQyu-LzzapsfI4SRKvOBqG1Cg"
WORKSHEET_GID = 0
CREDS_PATH = "./service_account.json"

RESPONSIBLE_COL = "Responsable"
KEY_COL = "Clave"

REVIEW_STATES = [
    "REVIEWING",
    "PENDING REVIEW",
    "REVIEW ON HOLD",
    "ON HOLD",
    "TO DEPLOY QA",
]

DRY_RUN = True  # cambiar a False para que aplique cambios en Jira

HEADERS = {"Content-Type": "application/json"}

def log(msg):
    print(f"[{datetime.now().isoformat()}] {msg}")

def jira_get(path, params=None):
    url = JIRA_DOMAIN + path
    r = requests.get(url, auth=HTTPBasicAuth(EMAIL, API_TOKEN), headers=HEADERS, params=params)
    if r.status_code >= 400:
        log(f"ERROR GET {url} → {r.status_code} {r.text}")
        return None
    return r.json()

def jira_post(path, payload):
    url = JIRA_DOMAIN + path
    if DRY_RUN:
        log(f"[DRY RUN] POST {url} → {payload}")
        return None
    r = requests.post(url, auth=HTTPBasicAuth(EMAIL, API_TOKEN), headers=HEADERS, json=payload)
    if r.status_code >= 400:
        log(f"ERROR POST {url} → {r.status_code} {r.text}")
        return None
    log(f"OK POST {url}")
    return r.json()

def fetch_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets.readonly",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(SHEET_ID)
    ws = sh.get_worksheet_by_id(WORKSHEET_GID)
    data = ws.get_all_records()
    return pd.DataFrame(data)

def detect_sprints():
    res = jira_get(f"/rest/agile/1.0/board/{BOARD_ID}/sprint", params={"state": "future,active"})
    if res is None:
        raise RuntimeError("No se pudo obtener sprints del board.")
    sprints = res.get("values", [])
    if len(sprints) < 2:
        raise RuntimeError("No hay suficientes sprints (activo + siguiente) detectados.")
    # ordenar por startDate (puede ser None)
    def key_fn(s): return s.get("startDate") or ""
    sprints_sorted = sorted(sprints, key=key_fn)
    current = sprints_sorted[0]
    next_sp = sprints_sorted[1]
    log(f"Sprint actual: {current['name']} (id {current['id']})")
    log(f"Sprint siguiente: {next_sp['name']} (id {next_sp['id']})")
    return current['id'], next_sp['id']

def fetch_issues_for_dev(dev):
    # trae todas las issues no Done asignadas al dev
    jql = f'assignee = "{dev}" AND project = IT AND statusCategory != Done'
    params = {"jql": jql, "maxResults": 500}
    res = jira_get("/rest/api/3/search", params=params)
    if res is None:
        return []
    issues = res.get("issues", [])
    return [{"key": i["key"], "status": i["fields"]["status"]["name"]} for i in issues]

def rank_issues(issue_keys):
    # rankea en orden dado
    for i in range(1, len(issue_keys)):
        prev = issue_keys[i-1]
        cur = issue_keys[i]
        payload = {
            "issues": [cur],
            "rankAfterIssue": prev
        }
        jira_post("/rest/agile/1.0/issue/rank", payload)
        time.sleep(0.2)

def move_to_sprint(sprint_id, issue_keys):
    if not issue_keys:
        return
    payload = {"issues": issue_keys}
    jira_post(f"/rest/agile/1.0/sprint/{sprint_id}/issue", payload)

def process():
    log("=== Iniciando proceso de backlog ===")
    df = fetch_sheet()
    if df.empty:
        log("La hoja está vacía → abortando.")
        return

    # Filter only rows that have a key
    df = df[df.get(KEY_COL, "").astype(str).str.strip() != ""]
    # Agrupar por dev
    dev_groups = df.groupby(RESPONSIBLE_COL)

    current_sprint, next_sprint = detect_sprints()

    for dev, sub in dev_groups:
        log(f"--- DEV: {dev} ---")
        excel_keys = list(sub[KEY_COL].astype(str).str.strip())
        log(f"Issues en sheet para dev: {excel_keys}")

        jira_issues = fetch_issues_for_dev(dev)
        jira_keys = [i["key"] for i in jira_issues]
        log(f"Issues en Jira asignadas al dev: {jira_keys}")

        # Issues en revisión -> no mover, siempre arriba
        review = [i["key"] for i in jira_issues if i["status"] in REVIEW_STATES]
        log(f"Issues en revisión (se preservan): {review}")

        # Issues que están en Jira pero no en sheet ni revisión → mover al próximo sprint
        to_move = [k for k in jira_keys if k not in excel_keys and k not in review]
        log(f"Issues a mover a próximo sprint: {to_move}")

        # Nuevo orden backlog = review + sheet order (solo los que existen en Jira)
        ordered = review + [k for k in excel_keys if k in jira_keys]
        log(f"Nueva orden de backlog para dev: {ordered}")

        # Aplicar rank
        rank_issues(ordered)

        # Mover sobrantes
        move_to_sprint(next_sprint, to_move)

    log("=== Proceso finalizado ===")

if __name__ == "__main__":
    log(f"DRY_RUN = {DRY_RUN}")
    process()
