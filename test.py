#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import pandas as pd

TABLEAU_SERVER_URL = os.getenv("TABLEAU_SERVER_URL", "https://us-east-1.online.tableau.com")
TABLEAU_SITE_ID = os.getenv("TABLEAU_SITE_ID", "carestino")  # contentUrl (lo que aparece en /#/site/<...>/...)  # noqa

# Auth recomendado: PAT (Personal Access Token)
TABLEAU_TOKEN_NAME = os.getenv("TABLEAU_TOKEN_NAME", "integracion_cares")
TABLEAU_TOKEN_SECRET = os.getenv("TABLEAU_TOKEN_SECRET", "5sL4q+2WRWGahc+Ex3ocsg==:snQBPFyA6ik0hKWljOkE098SbWgSrk1K")


TABLEAU_USERNAME = os.getenv("TABLEAU_USERNAME", "")
TABLEAU_PASSWORD = os.getenv("TABLEAU_PASSWORD", "")

OUT_CSV = os.getenv("OUT_CSV", "tableautest.csv")  # si seteás un path, guarda CSV (ej: OUT_CSV=tableau_views.csv)

def sign_in():
    import tableauserverclient as TSC

    if TABLEAU_TOKEN_NAME and TABLEAU_TOKEN_SECRET:
        auth = TSC.PersonalAccessTokenAuth(TABLEAU_TOKEN_NAME, TABLEAU_TOKEN_SECRET, site_id=TABLEAU_SITE_ID)
    elif TABLEAU_USERNAME and TABLEAU_PASSWORD:
        auth = TSC.TableauAuth(TABLEAU_USERNAME, TABLEAU_PASSWORD, site_id=TABLEAU_SITE_ID)
    else:
        raise RuntimeError(
            "Faltan credenciales. Seteá TABLEAU_TOKEN_NAME + TABLEAU_TOKEN_SECRET (recomendado) "
            "o TABLEAU_USERNAME + TABLEAU_PASSWORD."
        )

    server = TSC.Server(TABLEAU_SERVER_URL, use_server_version=True)
    return TSC, server, auth

def main():
    TSC, server, auth = sign_in()

    with server.auth.sign_in(auth):
        # Mapas útiles: project_id -> project_name, workbook_id -> (name, project_id)
        projects = {p.id: p.name for p in TSC.Pager(server.projects)}
        workbooks = {}
        for wb in TSC.Pager(server.workbooks):
            workbooks[wb.id] = {"name": wb.name, "project_id": wb.project_id}

        rows = []
        for v in TSC.Pager(server.views):
            wb_info = workbooks.get(getattr(v, "workbook_id", None), {})
            wb_name = wb_info.get("name", "")
            project_name = projects.get(wb_info.get("project_id"), "")

            rows.append({
                "view_id": v.id,
                "view_name": v.name,
                "content_url": getattr(v, "content_url", ""),   # MUY útil para matchear con la URL
                "workbook_id": getattr(v, "workbook_id", ""),
                "workbook_name": wb_name,
                "project_name": project_name,
            })

    df = pd.DataFrame(rows).sort_values(["workbook_name", "view_name"], kind="stable")

    # Imprime un resumen para buscar rápido
    print(f"Total views: {len(df)}")
    print(df.head(25).to_string(index=False))

    # Opcional: guardar CSV para buscar con Ctrl+F
    if OUT_CSV:
        df.to_csv(OUT_CSV, index=False, encoding="utf-8")
        print(f"\nGuardado en: {OUT_CSV}")

    # Tip: si querés filtrar por algo (ej 'VENTAS_SIN_FACTURAR'), podés hacerlo acá
    # needle = "ventas_sin_facturar".lower()
    # print(df[df["view_name"].str.lower().str.contains(needle, na=False)].to_string(index=False))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
