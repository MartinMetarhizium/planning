import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
from constants import MIN_PROJECT_RATIO, DAILY_HOURS, PROJECT_MAP_BT, PROJECT_MAP, DEFAULT_END_DATE, DEFAULT_END_DATE_with_timezone, DEFAULT_START_DATE,DEFAULT_START_DATE_with_timezone
from streamlit_javascript import st_javascript

def setup_navigation():
 
    if hasattr(st, "Page") and hasattr(st, "navigation"):
        alan   = st.Page("pages/alan.py",   title="Alan")
        martin = st.Page("pages/martin.py", title="Martin")
        martinBt = st.Page("pages/martin_bt.py", title="martin BT")
        worpik = st.Page("pages/worpik.py", title="Worpik")
        nav = st.navigation([alan, martinBt, martin, worpik])
        nav.run()
        return True

    
    if hasattr(st, "page_link"):
        st.page_link("pages/alan.py",   label="Alan")
        st.page_link("pages/martin.py", label="Martin")
        st.page_link("pages/martin_bt.py", label="martin BT")
        st.page_link("pages/worpik.py", label="Worpik")
        st.caption("Si no ves las páginas, verifica que el Main file sea planning/app.py y la carpeta se llame exactamente pages/")
        return True
    

    # (3) Muy antiguo: sin APIs de navegación. Confía en el sidebar automático.
    st.info("Navegación por sidebar. Si no aparece, ejecuta como Main: planning/app.py junto a planning/pages/")
    return False

# Llama esto al inicio de app.py
setup_navigation()




# version sprint 15/9 v2