#!/usr/bin/env python3
import os
import io
import sys
from urllib.parse import urlparse, parse_qs, unquote_plus

import pandas as pd
import tableauserverclient as TSC

# ========= CONFIG =========
# =========================================================
from datetime import date, timedelta
# Tableau (Tableau Cloud)
SERVER_URL = os.getenv("TABLEAU_SERVER_URL", "https://us-east-1.online.tableau.com")
SITE_ID = os.getenv("TABLEAU_SITE_ID", "carestino")  # contentUrl (lo que aparece en /#/site/<...>/...)  # noqa

# Auth recomendado: PAT (Personal Access Token)
TOKEN_NAME  = os.getenv("TABLEAU_TOKEN_NAME", "integracion_cares")
TOKEN_VALUE  = os.getenv("TABLEAU_TOKEN_SECRET", "5sL4q+2WRWGahc+Ex3ocsg==:snQBPFyA6ik0hKWljOkE098SbWgSrk1K")

VIEW_ID = os.getenv("VIEW_ID", "981ac22e-5fd1-4c4a-bdf8-e11e5e583fdf")
def last_month_range():
    today = date.today()
    first_this_month = today.replace(day=1)
    last_prev_month = first_this_month - timedelta(days=1)
    first_prev_month = last_prev_month.replace(day=1)
    return first_prev_month, last_prev_month
start_date, end_date = last_month_range()
VIEW_FILTERS = {
    "Fecha Carga Externa": f"{start_date},{end_date}",
    "Tipo de Venta": "VENTA",
    "Canal": "Mercado Libre,Ventas Web",  # multiselect → coma
}

# Si alguno de estos fuera PARAMETER
VIEW_PARAMETERS = {
    "Fecha Carga Externa": f"{start_date},{end_date}",
    "Tipo de Venta": "VENTA",
    "Canal": "Mercado Libre,Ventas Web",  # multiselect → coma
}

# =========================================================
# CSV FETCH (SEGURO, NO BLOQUEA)



def fetch_view_csv(
    view_id: str,
    filters: dict,
    parameters: dict,
    maxage: int = 1,
    parameter_workaround: bool = True,
) -> pd.DataFrame:
    if not TOKEN_NAME or not TOKEN_VALUE:
        raise RuntimeError("Faltan TABLEAU_TOKEN_NAME / TABLEAU_TOKEN_SECRET")

    auth = TSC.PersonalAccessTokenAuth(
        TOKEN_NAME,
        TOKEN_VALUE,
        site_id=SITE_ID,
    )
    server = TSC.Server(SERVER_URL, use_server_version=True)

    with server.auth.sign_in(auth):
        view = server.views.get_by_id(view_id)

        print("\n== Tableau CSV Fetch ==")
        print("View name :", view.name)
        print("View ID   :", view.id)
        print("URL       :", view.content_url)
        print("Filters   :", filters)
        print("Params    :", parameters)
        print()

        csv_opts = TSC.CSVRequestOptions(maxage=maxage)
        start_date, end_date = last_month_range()

        csv_opts.vf(
            "Fecha Carga Externa",
            f"{start_date},{end_date}"
        )

        # ---- filtros de vista ----
        for k, v in filters.items():
            if v is None or str(v).strip() == "":
                continue
            csv_opts.vf(str(k), str(v))

        # ---- parámetros ----
        for k, v in parameters.items():
            if v is None or str(v).strip() == "":
                continue
            csv_opts.parameter(str(k), str(v))
            if parameter_workaround:
                csv_opts.vf(f"Parameters.{k}", str(v))

        # ---- DESCARGA CSV (NO UI, NO IMAGE) ----
        server.views.populate_csv(view, csv_opts)
        csv_bytes = b"".join(view.csv or [])

    print("CSV bytes:", len(csv_bytes))

    if not csv_bytes.strip():
        print("⚠️ CSV vacío (0 registros con esos filtros)")
        return pd.DataFrame()

    try:
        df = pd.read_csv(io.BytesIO(csv_bytes))
    except pd.errors.EmptyDataError:
        print("⚠️ CSV sin columnas (0 registros)")
        return pd.DataFrame()

    print(f"OK → filas={len(df)} columnas={len(df.columns)}")
    print(df.head(5).to_string(index=False))
    return df

# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    try:
        df = fetch_view_csv(
            view_id=VIEW_ID,
            filters=VIEW_FILTERS,
            parameters=VIEW_PARAMETERS,
            maxage=1,
            parameter_workaround=True,
        )

        if df.empty:
            print("\n❌ Resultado final: 0 filas")
        else:
            print("\n✅ Datos obtenidos correctamente")

    except Exception as e:
        print("\n❌ ERROR:", e)
        sys.exit(1)