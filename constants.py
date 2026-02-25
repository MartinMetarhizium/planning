import requests
PROJECT_MAP = {
    "Alan Mori - Carestino": {
        "Worpik": {"deadline": "2025-08-14", "progress": 0},
        "Clientes": {"deadline": "2025-10-30", "progress": 0},
        "Descripciones automáticas / plantillas Interior templates": {"deadline": "2026-01-01", "progress": 0},
        "Training": {"deadline": "2026-02-01", "progress": 10},
        "API Whatsapp": {"deadline": "2026-01-01", "progress": 0},
        "Auditoría de stock": {"deadline": "2025-11-30", "progress": 0},
    },
    "Franco Lorenzo": {
        "Rediseño Portal Gestión": {"deadline": "2025-07-30", "progress": 0},
        "Rediseño Admin Nicox": {"deadline": "2025-12-01", "progress": 0},
        "Indicadores de sistema": {"deadline": "2025-08-10", "progress": 0},
        "Lupa Buscador Sitio WEB": {"deadline": "2025-10-31", "progress": 0},
        "Rediseño web - Carestino": {"deadline": "2025-10-01", "progress": 90},
        "Filtros en listado de productos – Desarrollo y ajustes": {"deadline": "2026-01-31", "progress": 0},

    },
    "Gastón Ojeda": {
        "Customer Experience (Bot, Gestiones, Reclamos, automatización de ventas)": {"deadline": "2026-01-01", "progress": 30},
    },
    "Miguel Armentano": {
        "Facturación USA": {"deadline": "2025-08-01", "progress": 100},
        "Expenses - SAP": {"deadline": "2025-10-30", "progress": 0},
    },
    "Luis Uran": {
        "Actualizar API Reseller": {"deadline": "2025-12-01", "progress": 90},
        "Mejoras en Seguimiento y Tiempos de Entrega para Clientes": {"deadline": "2025-12-01", "progress": 0},
        "Integraciones logísticas – Mercado Envíos / Amazon / falabella / liverpool (estados de ventas y etiquetas) Dominicana / Andesmar / Bigsmart": {"deadline": "2025-12-01", "progress": 20},
        "Remplazo Easymailing": {"deadline": "2025-11-01", "progress": 80},
        "Logística v2": {"deadline": "2025-09-01", "progress": 0},
        "API de conversiones google": {"deadline": "2025-10-01", "progress": 0},
        "Delivery Admin – Implementación y ajustes finales": {"deadline": "2025-10-31", "progress": 100},

    },
    "Nicolas Pardo": {
        "Cupones": {"deadline": "2025-07-01", "progress": 0},
        "Integracion dentro del modulo marketplace (stock y precio)": {"deadline": "2025-10-01", "progress": 30},
        "Integracion pasarelas de cobros: Pagoplux / paypal / Dominicana": {"deadline": "2026-02-01", "progress": 0},
        "Migracion a red privada": {"deadline": "2025-07-01", "progress": 0},
    },
    "Diego Gogorza": {
        "Auditoría equipos tecnológico": {"deadline": "2025-10-31", "progress": 0},

    },
     "Martín Horn": {
        "Agente | Pricing": {"deadline": "2025-10-31", "progress": 0},
        "Agente | Gestión de Posventa Nicox": {"deadline": "2025-10-31", "progress": 0},
        "Agente | Gestión de Reviews Wise / Bot auditor": {"deadline": "2025-10-31", "progress": 0},
        "Agente | Scoring Clientes": {"deadline": "2025-10-31", "progress": 0},
        "Agente | Pedidos Tienda": {"deadline": "2025-10-31", "progress": 0},
        
    },
    "Alan Fernandez": {
        "Operación de Seguimiento": {"deadline": "2025-10-31", "progress": 0},
        "Operación de Finanzas": {"deadline": "2025-10-31", "progress": 0},
    },
    "Joaquin Fernandez - Carestino": {},
    "ivanalberghini": {},
    "Martín Horn": {},
    "Facundo Capua": {},
    "Default": {}
}



PROJECT_MAP_BT = {
    "Federico Macias": {
        "Facturación USA": {
            "vencimiento": "2025-06-01",
            "completado": "2025-06-01",
            "estado": "finalizado"
        },
        "Expenses": {
            "vencimiento": "2025-08-01",
            "completado": "2025-07-28",
            "estado": "finalizado"
        },
        "SAP": {
            "vencimiento": "2025-10-30",
            "completado": None,
            "estado": "pendiente"
        },
        "Clientes": {
            "vencimiento": "2025-10-01",
            "completado": None,
            "estado": "pendiente"
        },
        "API Whatsapp": {
            "vencimiento": "2025-12-01",
            "completado": None,
            "estado": "pendiente"
        },
        "Filtros worpik": {
            "vencimiento": "2025-11-15",
            "completado": None,
            "estado": "pendiente"
        },
        "Training": {
            "vencimiento": "2026-02-01",
            "completado": None,
            "estado": "pendiente"
        },
        "Seguridad / Accesos": {
            "vencimiento": "2026-02-01",
            "completado": None,
            "estado": "pendiente"
        },
        "Integracion pasarelas de cobros: Pagoplux / paypal / Dominicana": {
            "vencimiento": "2026-01-01",
            "completado": None,
            "estado": "pendiente"
        },
    },
    "Juan Ignacio Morelis": {
        "Actualizar Api Reseller": {
            "vencimiento": "2025-11-01",
            "completado": "2025-09-10",
            "estado": "finalizado"
        },
        "Integracion dentro del modulo marketplace (stock y precio)": {
            "vencimiento": "2025-10-01",
            "completado": None,
            "estado": "pendiente"
        },
        "Logistica v2": {
            "vencimiento": "2025-08-01",
            "completado": "2025-07-27",
            "estado": "finalizado"
        },
        "Mejoras en Seguimiento y Tiempos de Entrega para Clientes": {
            "vencimiento": "2025-10-01",
            "completado": "2025-05-27",
            "estado": "finalizado"
        },
        "Integraciones logísticas – Mercado Envíos / Amazon / falabella / liverpool (estados de ventas y etiquetas) Dominicana / Andesmar / Bigsmart": {
            "vencimiento": "2026-01-01",
            "completado": None,
            "estado": "pendiente"
        },
        "Delivery Admin – Implementación y ajustes finales": {
            "vencimiento": "2025-09-01",
            "completado": None,
            "estado": "pendiente"
        },
    },
    "Martín Horn": {
        "Agente | Gestión de Posventa Nicox": {
            "vencimiento": "2025-10-01",
            "completado": None,
            "estado": "pendiente"
        },
        "Agente | Scoring Clientes": {
            "vencimiento": "2025-08-01",
            "completado": None,
            "estado": "pendiente"
        },
        "Agente | Pedidos Tienda": {
            "vencimiento": "2025-10-01",
            "completado": None,
            "estado": "pendiente"
        },
        "Agente | Pricing": {
            "vencimiento": "2025-10-01",
            "completado": None,
            "estado": "pendiente"
        },
    },
    "Joaquin Fernandez": {
        "Rediseño Portal Gestion": {
            "vencimiento": "2025-07-01",
            "completado": None,
            "estado": "pendiente"
        },
        "Rediseño web - Carestino": {
            "vencimiento": "2025-08-01",
            "completado": "2025-07-15",
            "estado": "finalizado"
        },
        "Rediseño Admin Nicox": {
            "vencimiento": "2025-12-01",
            "completado": None,
            "estado": "pendiente"
        },
        "Descripciones automaticas / plantillas interior templates ": {
            "vencimiento": "2025-12-01",
            "completado": None,
            "estado": "pendiente"
        },
        
        "API de conversiones google": {
            "vencimiento": "2025-08-01",
            "completado": None,
            "estado": "pendiente"
        },
    },
    "Thiago Cabrera": {},
    
}



from datetime import datetime, timedelta
import datetime as dt
DEFAULT_START_DATE = datetime(2026, 3, 2)  #año mes día
DEFAULT_END_DATE = DEFAULT_START_DATE + timedelta(days=11)
import pytz
# 🕓 Rango de fechas a consultar
DEFAULT_START_DATE_with_timezone = dt.datetime(2025, 3, 2, 0, 0, 0, tzinfo=pytz.UTC)
DEFAULT_END_DATE_with_timezone = DEFAULT_START_DATE_with_timezone + dt.timedelta(days=11)
VALID_STATUSES = {"BACKLOG", "REDEFINED", "RECHAZADO", "IN IMPROVEMENT"}
VALID_STATUSES_BT = {"Por Hacer"}


MIN_PROJECT_RATIO = {
    "Alan Mori - Carestino": 1,
    "Franco Lorenzo": 0.5,
    "Gastón Ojeda": 0.0,
    "Miguel Armentano": 0.5,
    "Luis Uran": 0.5,
    "Default": 0.1,
    "Facundo Capua":0.1,
    "Nicolas Pardo": 0.1,
    "ivanalberghini": 0.1,
    "Martín Horn": 0.1,
    "Joaquin Fernandez - Carestino": 0.5,
}

MIN_BT_PROJECT_RATIO = {
    "federicomacias": 0.7,
    "Martín Horn": 0.5,
    "Joaquin Fernandez - Carestino": 0.3,
    "Juan Ignacio Morelis - Carestino": 0.5,
    "Thiago Cabrera": 0.5,
    "Default": 0.5,

}

DAILY_BT_HOURS = {
    "federicomacias": 6,
    "Martín Horn": 6,
    "Joaquin Fernandez - Carestino": 6,
    "Juan Ignacio Morelis - Carestino": 6,
    "Thiago Cabrera": 3,
    "Default": 6,
}

DAILY_HOURS = {
    "Default": 6,
    "Facundo Capua": 8,
    "Nicolas Pardo": 8,
    "Franco Lorenzo": 5,
    "Luis Uran": 6,
    "Alan Mori - Carestino":5.5,
    "Juan Ignacio Morelis - Carestino":8,
    "Gastón Ojeda": 5,
    "Miguel Armentano": 5,
    "ivanalberghini": 6,
    "Martín Horn": 6,
    "Joaquin Fernandez - Carestino": 6,
}


MAIL_BT_MAP = {
    "federicomacias": "federicomacias@biamex.com",
    "Martín Horn": "martinhorn@biamex.com",
    "Joaquin Fernandez - Carestino": "joaquinfernandez@biamex.com",
    "Juan Ignacio Morelis - Carestino": "juanmorelis@biamex.com",
    "Thiago Cabrera": "thiagocabrera@biamex.com",
    
}

MAIL_MAP = {
    "Luis Uran": "luisuran@biamex.com",
    "Diego Martin Gogorza": "diegogogorza@biamex.com",
    "Nicolas Pardo": "nicolaspardo@biamex.com",
    "Martín Horn": "martinhorn@biamex.com",
    "Facundo Capua": "facundocapua@biamex.com",
    "Franco Lorenzo": "francolorenzo@biamex.com",
    "Alan Mori - Carestino": "alanmori@biamex.com",
    "Gastón Ojeda": "gastonojeda@biamex.com",
    "Miguel Armentano": "miguelarmentano@biamex.com",
    "Juan Ignacio Morelis - Carestino": "juanmorelis@biamex.com",
    "ivanalberghini": "ivanalberghini@biamex.com",
    "Joaquin Fernandez - Carestino": "joaquinfernandez@biamex.com",
}

MODULE_DEVS = {
    "Clientes": [],
    "Ventas": ["Gastón Ojeda", "Nicolas Pardo"],
    "Reintegros": ["Gastón Ojeda"],
    "Contactos": [],
    "Logística": ["Luis Uran"],
    "Productos": ["Alan Mori - Carestino", "Gastón Ojeda"],
    "Forzar": ["Luis Uran"],
    "Contable": ["Miguel Armentano", "Luis Uran"],
    "Depositos": [],
    "Ajustes": ["Alan Mori - Carestino", "Miguel Armentano", "Luis Uran", "Gastón Ojeda", "Nicolas Pardo"],
    "Comercio internacional": ["Miguel Armentano"],
    "Home page": ["Franco Lorenzo", "Nicolas Pardo"],
    "Facturación": ["Miguel Armentano"],
    "Pim": ["Alan Mori - Carestino"],
    "Encuestas": [],
    "Control de calidad": ["Luis Uran"],
    "Diccionarios": [],
    "Wms": ["Gastón Ojeda"],
    "Payments": ["Miguel Armentano", "Luis Uran"],
    "Rendición de gastos": ["Miguel Armentano"],
    "Centros de costos": ["Miguel Armentano"],
    "IERO": ["Alan Mori - Carestino"],
    "Auditoría": [],
    "Worpik": ["Alan Mori - Carestino"],
    "Delivery App": ["Gastón Ojeda", "Franco Lorenzo"],
    "Integraciones logisticas": ["Luis Uran"],
    "Integraciones de Facturadores": ["Miguel Armentano"],
    "Integración de procesadoras": ["Miguel Armentano"],
    "API Stock": ["Gastón Ojeda"],
    "Nicox API": ["Alan Mori - Carestino", "Gastón Ojeda"],
    "Control de Caja": ["Miguel Armentano"],
    "Delivery Admin": ["Gastón Ojeda", "Franco Lorenzo"],
    "Next js": ["Franco Lorenzo"],
    "Monorepo": ["Franco Lorenzo"],
    "FusionAuth": ["Alan Mori - Carestino"],
    "Nomina": [],
    "Ecommerce": ["Franco Lorenzo"],
    "Payroll": [],
    "Internal-API": [],
    "Reseller": ["Nicolas Pardo"]
}

JIRA_DOMAIN = "team-1583163151751.atlassian.net"
EMAIL = "martinhorn@biamex.com"
MAX_RESULTS = 100
JQL = """
project = IT
AND issuetype NOT IN (Epic, Subtarea)
ORDER BY priority DESC, due ASC
"""

FIELDS = "key,summary,assignee,status,timetracking,duedate,parent,issuelinks,project,customfield_10016,customfield_10212,customfield_10214,customfield_10442,customfield_10608,reporter"
BASE_URL = f"https://{JIRA_DOMAIN}/rest/api/3/search"



def post_to_slack(channel: str, text: str, token: str):
    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
        json={"channel": channel, "text": text},
        timeout=30,
    )
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack error: {data}")
    
