import streamlit as st

def setup_navigation():
    if hasattr(st, "Page") and hasattr(st, "navigation"):
        alan   = st.Page("pages/alan.py",   title="Alan")
        martin = st.Page("pages/martin.py", title="Martin")
        martinBt = st.Page("pages/martin_bt.py", title="martin BT")
        worpik = st.Page("pages/worpik.py", title="Worpik")
        estimaciones = st.Page("pages/estimationTimes.py", title="Estimaciones")
        reviewTimes = st.Page("pages/reviewTimes.py", title="Revisiones de tarjetas")
        projectosBt = st.Page("pages/proyectosBt.py", title="Estados de proyectos")
        movimientoTarjetas = st.Page("pages/movimientoTarjetas.py", title="Movimiento de tarjetas")
        metrics = st.Page("pages/metrics.py", title="metrics")
        nav = st.navigation([alan, martinBt, martin, worpik, estimaciones, reviewTimes, projectosBt, movimientoTarjetas, metrics])
        nav.run()
        return True

    if hasattr(st, "page_link"):
        st.page_link("pages/alan.py",   label="Alan")
        st.page_link("pages/martin.py", label="Martin")
        st.page_link("pages/martin_bt.py", label="martin BT")
        st.page_link("pages/worpik.py", label="Worpik")
        st.page_link("pages/estimationTimes.py", label="Estimaciones")
        st.page_link("pages/reviewTimes.py", label="Revisiones de tarjetas")
        st.page_link("pages/proyectosBt.py", label="Estados de proyectos")
        st.page_link("pages/movimientoTarjetas.py", label="movimientoTarjetas")
        st.page_link("pages/metrics.py", label="metrics")
        st.caption("Si no ves las páginas, verifica que el Main file sea planning/app.py y la carpeta se llame exactamente pages/")
        return True
    
    st.info("Navegación por sidebar. Si no aparece, ejecuta como Main: planning/app.py junto a planning/pages/")
    return False
#

setup_navigation()




# nuevas paginas de changelog del proyecto it