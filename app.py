import streamlit as st
import pandas as pd
import psycopg2
import bcrypt
import re
import io
import os
from datetime import datetime, date
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Control de Facturación",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ARCA_RE = re.compile(r'^[A-Z]-\d{5}-\d{8}$')

OBRAS_SOCIALES = [
  {
    "codigo": 1064,
    "nombre": "O.S.D.I.P.P.",
    "cuit": "30-54741601-1"
  },
  {
    "codigo": 10001,
    "nombre": "OSAPM DE LA R.A.",
    "cuit": "30-62313465-9"
  },
  {
    "codigo": 10019,
    "nombre": "CORTE SUPREMA DE JUSTICIA O. S. DEL PODER JUDICIAL",
    "cuit": "30-63619685-8"
  },
  {
    "codigo": 10020,
    "nombre": "SUPERINTENDENCIA DE BIENESTAR POLICIA FEDERAL ARG.",
    "cuit": "30-54666267-1"
  },
  {
    "codigo": 10021,
    "nombre": "S.E.R.O.S.",
    "cuit": "30-99922290-7"
  },
  {
    "codigo": 10039,
    "nombre": "O.S.P.I.A.",
    "cuit": "30-64399773-4"
  },
  {
    "codigo": 10040,
    "nombre": "GRIAL Salud SA",
    "cuit": "30-71434838-4"
  },
  {
    "codigo": 10043,
    "nombre": "O.S.DEL PERSONAL DE TELEVISION",
    "cuit": "30-51674838-5"
  },
  {
    "codigo": 10050,
    "nombre": "JERARQUICOS SALUD",
    "cuit": "33-71018560-9"
  },
  {
    "codigo": 10053,
    "nombre": "MEDICUS S.A.",
    "cuit": "30-54677131-4"
  },
  {
    "codigo": 11060,
    "nombre": "SWISS MEDICAL S.A.",
    "cuit": "30-65485516-8"
  },
  {
    "codigo": 10067,
    "nombre": "A.C.A. SALUD",
    "cuit": "30-60495864-0"
  },
  {
    "codigo": 10076,
    "nombre": "MEDIFE ASOCIACION CIVIL",
    "cuit": "30-68273765-0"
  },
  {
    "codigo": 10077,
    "nombre": "MEDIFE ASOCIACION CIVIL (I.V.A.)",
    "cuit": "30-68273765-0"
  },
  {
    "codigo": 10079,
    "nombre": "O.S.SEG.",
    "cuit": "30-50005352-2"
  },
  {
    "codigo": 10082,
    "nombre": "O.S.P.E.(Obra Social de Petroleros)",
    "cuit": "30-66187671-5"
  },
  {
    "codigo": 10099,
    "nombre": "GALENO Argentina S.A. AZUL/BLANCO/ORO/PLATA",
    "cuit": "30-52242816-3"
  },
  {
    "codigo": 10103,
    "nombre": "SCIS S.A. OSTRAC - AATRAC",
    "cuit": "30-70842808-2"
  },
  {
    "codigo": 10105,
    "nombre": "OBRA SOCIAL DE COND.CAMIONEROS",
    "cuit": "30-66150769-8"
  },
  {
    "codigo": 10108,
    "nombre": "CLINICA DEL VALLE SALUD S.R.L.",
    "cuit": "33-71021054-9"
  },
  {
    "codigo": 10109,
    "nombre": "O.S.P.I.L. (O.S.del Personal de la Ind. Lechera)",
    "cuit": "30-58419478-9"
  },
  {
    "codigo": 10110,
    "nombre": "O.S.D.O.P. (O.S.DOCENTES PARTICULARES)",
    "cuit": "30-58541245-3"
  },
  {
    "codigo": 10112,
    "nombre": "O.S.T.P.C.P.H.y A.R.A. (PASTELEROS)",
    "cuit": "30-67906538-2"
  },
  {
    "codigo": 10113,
    "nombre": "A.D.O.S.",
    "cuit": "30-56199613-6"
  },
  {
    "codigo": 10114,
    "nombre": "OBRA SOCIAL DE LUZ Y FUERZA DE LA PATAGONIA",
    "cuit": "30-71035033-3"
  },
  {
    "codigo": 10115,
    "nombre": "UNO SALUD S.A.",
    "cuit": "30-71160242-5"
  },
  {
    "codigo": 10117,
    "nombre": "ASOCIACION MUTUAL SANCOR",
    "cuit": "30-59035479-8"
  },
  {
    "codigo": 10118,
    "nombre": "ASOCIACION MUTUAL SANCOR - VOLUNTARIO",
    "cuit": "30-59035479-8"
  },
  {
    "codigo": 10119,
    "nombre": "ASOCIACION MUTUAL DE PROTECCION FAMILIAR",
    "cuit": "30-67856284-6"
  },
  {
    "codigo": 10123,
    "nombre": "GERDANNA S.A.",
    "cuit": "30-69760639-0"
  },
  {
    "codigo": 10124,
    "nombre": "O.S.V.V.R.A.",
    "cuit": "30-69349438-5"
  },
  {
    "codigo": 10125,
    "nombre": "ITER MEDICINA S.A.",
    "cuit": "30-70473487-1"
  },
  {
    "codigo": 10126,
    "nombre": "EN EL HOGAR",
    "cuit": "30-71314800-4"
  },
  {
    "codigo": 10127,
    "nombre": "PREVENCION SALUD S.A.",
    "cuit": "30-71304500-0"
  },
  {
    "codigo": 10130,
    "nombre": "CAMINOS PROTEGIDOS ART S.A.",
    "cuit": "33-71105830-9"
  },
  {
    "codigo": 10022,
    "nombre": "SEROS VALORES PAMI",
    "cuit": "nan"
  },
  {
    "codigo": 10081,
    "nombre": "I.N.S.S.J.P.-VETER.DE GUERRA",
    "cuit": "30-52276392-2"
  },
  {
    "codigo": 10131,
    "nombre": "PROME S.A.",
    "cuit": "30-69627684-2"
  },
  {
    "codigo": 10133,
    "nombre": "LIDERAR S.A. ART",
    "cuit": "30-71122767-5"
  },
  {
    "codigo": 10134,
    "nombre": "PREVENCION ART",
    "cuit": "30-68436191-7"
  },
  {
    "codigo": 10135,
    "nombre": "SANCOR COOP.SEGUROS",
    "cuit": "30-50004946-0"
  },
  {
    "codigo": 10137,
    "nombre": "LA SEGUNDA ART",
    "cuit": "30-68913348-3"
  },
  {
    "codigo": 10140,
    "nombre": "INTERACCION ART",
    "cuit": "nan"
  },
  {
    "codigo": 10141,
    "nombre": "FEDERACION PATRONAL SEGUROS S.A.",
    "cuit": "33-70736658-9"
  },
  {
    "codigo": 10142,
    "nombre": "EXPERTA ART S.A.",
    "cuit": "30-68715616-8"
  },
  {
    "codigo": 10143,
    "nombre": "GALENO ART. S.A.",
    "cuit": "30-68522850-1"
  },
  {
    "codigo": 10145,
    "nombre": "BERKLEY ART",
    "cuit": "nan"
  },
  {
    "codigo": 10151,
    "nombre": "I.N.S.S.J.P.",
    "cuit": "30-52276392-2"
  },
  {
    "codigo": 10152,
    "nombre": "O.S. SERVICIOS SOCIALES BANCARIOS (OSSSB)",
    "cuit": "30-69156146-8"
  },
  {
    "codigo": 10153,
    "nombre": "O.S.P.E.R.Y H.R.A",
    "cuit": "30-59545956-3"
  },
  {
    "codigo": 10154,
    "nombre": "OMINT ASEGURADORA DE RIESGO DEL TRABAJO S,A,",
    "cuit": "30-71234180-3"
  },
  {
    "codigo": 10155,
    "nombre": "CONFERENCIA EPISCOPAL ARGENTINA",
    "cuit": "30-51731290-4"
  },
  {
    "codigo": 10157,
    "nombre": "O.S.COND. CAMIONEROS (SANTA CRUZ)",
    "cuit": "30-66150769-8"
  },
  {
    "codigo": 10163,
    "nombre": "O.S.P.y G. CHUBUT",
    "cuit": "30-71549799-5"
  },
  {
    "codigo": 10164,
    "nombre": "I.O.S.F.A.",
    "cuit": "30-71429214-1"
  },
  {
    "codigo": 10165,
    "nombre": "O.S.P.E.D.Y.C.",
    "cuit": "30-68833954-1"
  },
  {
    "codigo": 10167,
    "nombre": "HEMISFERIO SALUD S.A.",
    "cuit": "30-71425148-8"
  },
  {
    "codigo": 11001,
    "nombre": "VISITAR SRL",
    "cuit": "33-65712962-9"
  },
  {
    "codigo": 11038,
    "nombre": "D.A.S.U.(U.N.P.S.J.B.)",
    "cuit": "30-64187154-7"
  },
  {
    "codigo": 11039,
    "nombre": "D.A.S.U.(I.V.A.)",
    "cuit": "30-64187154-7"
  },
  {
    "codigo": 11050,
    "nombre": "VALORES PAMI",
    "cuit": "nan"
  },
  {
    "codigo": 11052,
    "nombre": "I.N.S.S.J.P. (SANTA CRUZ)",
    "cuit": "30-52276392-2"
  },
  {
    "codigo": 11062,
    "nombre": "SWISS MEDICAL S.A. (I.V.A.)",
    "cuit": "30-65485516-8"
  },
  {
    "codigo": 12037,
    "nombre": "A.M.F.F.A.",
    "cuit": "30-57101480-3"
  },
  {
    "codigo": 13055,
    "nombre": "A.P.S.O.T.",
    "cuit": "30-56430406-5"
  },
  {
    "codigo": 13056,
    "nombre": "F.S.S.T.",
    "cuit": "30-63763030-6"
  },
  {
    "codigo": 23031,
    "nombre": "O.S.D.E.",
    "cuit": "30-54674125-3"
  },
  {
    "codigo": 23032,
    "nombre": "O.S.D.E. (I.V.A.) 2-210 / 2-310",
    "cuit": "30-54674125-3"
  },
  {
    "codigo": 10104,
    "nombre": "SCIS OSFENTOS",
    "cuit": "30-70842808-2"
  },
  {
    "codigo": 10106,
    "nombre": "SCIS S.A. OSPESCA",
    "cuit": "30-70842808-2"
  },
  {
    "codigo": 23033,
    "nombre": "O.S.D.E. (IVA) 2-410",
    "cuit": "30-54674125-3"
  },
  {
    "codigo": 23034,
    "nombre": "O.S.D.E. (IVA) 2-450",
    "cuit": "30-54674125-3"
  },
  {
    "codigo": 23035,
    "nombre": "O.S.D.E.(IVA) 2-510",
    "cuit": "30-54674125-3"
  },
  {
    "codigo": 11002,
    "nombre": "VISITAR - OSDEPYM",
    "cuit": "33-65712962-9"
  },
  {
    "codigo": 10159,
    "nombre": "O.S.J.e R.A.",
    "cuit": "30-69635177-1"
  },
  {
    "codigo": 1,
    "nombre": "HONORARIOS SISTEMA ANTERIOR",
    "cuit": "30-55881458-2"
  },
  {
    "codigo": 1060,
    "nombre": "ARANCEL ETICO DE REFERENCIA",
    "cuit": "22-22222222-2"
  },
  {
    "codigo": 999,
    "nombre": "modelo de prueba - no valido",
    "cuit": "20-16743702-9"
  },
  {
    "codigo": 9999,
    "nombre": "modelo de prueba - no valido",
    "cuit": "20-16743702-9"
  },
  {
    "codigo": 10168,
    "nombre": "SAN FRANCISCO A.R.T.",
    "cuit": "30-71721658-6"
  },
  {
    "codigo": 13057,
    "nombre": "UTEPLIM SALUD",
    "cuit": "30-71592266-1"
  },
  {
    "codigo": 13058,
    "nombre": "OSFATUN",
    "cuit": "30-68333676-5"
  },
  {
    "codigo": 10111,
    "nombre": "GRUPO ROISA",
    "cuit": "30-66193106-6"
  },
  {
    "codigo": 10169,
    "nombre": "NATIVUS",
    "cuit": "30-71018653-3"
  },
  {
    "codigo": 13060,
    "nombre": "O.S.F.A.T.L.Y.F.",
    "cuit": "30-66322124-4"
  },
  {
    "codigo": 1065,
    "nombre": "O.S.T.R.A.C.",
    "cuit": "30-66318527-2"
  },
  {
    "codigo": 1066,
    "nombre": "OBRA SOCIAL DEL PERSONAL DE FARMACIA",
    "cuit": "33-64810438-9"
  },
  {
    "codigo": 10170,
    "nombre": "GLOBAL EMPRESARIA S.A.",
    "cuit": "30-71513403-5"
  }
]
OBRAS_NOMBRES = [f"{o['codigo']} - {o['nombre']}" for o in OBRAS_SOCIALES]

# ─────────────────────────────────────────────
#  ESTILOS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background: #080b0f;
    color: #c9d1d9;
  }
  .stApp { background: #080b0f; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #21262d;
  }

  /* Tipografía */
  h1 { font-size:1.6rem!important; font-weight:700!important; letter-spacing:.04em; color:#f0f6fc!important; }
  h2 { font-size:1.1rem!important; font-weight:600!important; color:#8b949e!important; letter-spacing:.08em; text-transform:uppercase; }
  h3 { font-size:.8rem!important;  font-weight:500!important; color:#484f58!important; letter-spacing:.1em;  text-transform:uppercase; }

  /* Inputs */
  input, textarea, select,
  .stTextInput input, .stSelectbox select, .stDateInput input {
    background: #0d1117!important;
    border: 1px solid #21262d!important;
    color: #c9d1d9!important;
    border-radius: 6px!important;
    font-family: 'JetBrains Mono', monospace!important;
    font-size: .82rem!important;
  }
  input:focus { border-color: #388bfd!important; box-shadow: 0 0 0 3px #388bfd22!important; }

  /* Botón primario */
  .stButton > button[kind="primary"] {
    background: #238636!important;
    color: #fff!important;
    border: 1px solid #2ea043!important;
    border-radius: 6px!important;
    font-family: 'Syne', sans-serif!important;
    font-weight: 600!important;
    letter-spacing: .04em!important;
    padding: .5rem 1.4rem!important;
    transition: all .2s!important;
  }
  .stButton > button[kind="primary"]:hover { background:#2ea043!important; }

  /* Botón secundario */
  .stButton > button[kind="secondary"] {
    background: transparent!important;
    border: 1px solid #30363d!important;
    color: #8b949e!important;
    border-radius: 6px!important;
    font-size:.82rem!important;
  }
  .stButton > button[kind="secondary"]:hover { border-color:#8b949e!important; color:#c9d1d9!important; }

  /* Download */
  .stDownloadButton > button {
    background: transparent!important;
    border: 1px solid #388bfd!important;
    color: #388bfd!important;
    border-radius: 6px!important;
    font-size:.82rem!important;
  }

  /* Separador */
  hr { border-color: #21262d!important; margin: 1.2rem 0!important; }

  /* Métricas */
  [data-testid="stMetric"] {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px 16px;
  }
  [data-testid="stMetricValue"] { color: #f0f6fc!important; font-family: 'JetBrains Mono'!important; }
  [data-testid="stMetricLabel"] { color: #484f58!important; font-size:.72rem!important; text-transform:uppercase; letter-spacing:.08em; }

  /* Dataframe */
  .stDataFrame { border: 1px solid #21262d!important; border-radius: 8px!important; }

  /* Progress */
  .stProgress > div > div { background: #238636!important; }

  /* Cards de facturas */
  .factura-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 6px 0;
    cursor: pointer;
    transition: border-color .2s, background .2s;
  }
  .factura-card:hover { border-color: #388bfd; background: #0d1117ee; }
  .factura-card.selected { border-color: #238636; background: #0d1f0d; }

  /* Badge de estado */
  .badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: .72rem;
    font-family: 'JetBrains Mono';
    font-weight: 500;
    letter-spacing: .04em;
  }
  .badge-pendiente  { background:#1a1500; border:1px solid #3a3000; color:#f2c94c; }
  .badge-solicitada { background:#001229; border:1px solid #00366b; color:#388bfd; }
  .badge-completo   { background:#0d1f0d; border:1px solid #1a3a1a; color:#3fb950; }

  /* Bienvenida */
  .welcome-header {
    background: linear-gradient(135deg, #0d1117 0%, #0d1f0d 100%);
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 24px;
  }
  .welcome-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #f0f6fc;
    letter-spacing: .02em;
    margin: 0 0 6px 0;
  }
  .welcome-sub {
    font-size: .85rem;
    color: #484f58;
    letter-spacing: .06em;
    text-transform: uppercase;
    margin: 0;
  }

  /* Label pequeño */
  .lbl {
    font-size: .7rem;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: #484f58;
    margin-bottom: 4px;
  }

  /* Alertas personalizadas */
  .stSuccess { background:#0d1f0d!important; border:1px solid #1a3a1a!important; color:#3fb950!important; border-radius:6px!important; }
  .stError   { background:#1f0d0d!important; border:1px solid #3a1a1a!important; color:#f85149!important; border-radius:6px!important; }
  .stInfo    { background:#001229!important; border:1px solid #00366b!important; color:#388bfd!important; border-radius:6px!important; }

  /* File uploader */
  [data-testid="stFileUploader"] {
    border: 1px dashed #21262d!important;
    border-radius: 8px!important;
    background: #0d1117!important;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  BASE DE DATOS
# ─────────────────────────────────────────────

@contextmanager
def get_conn():
    """Conexión segura con cierre garantizado."""
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    if not DATABASE_URL:
        st.error("Variable DATABASE_URL no configurada en Railway.")
        st.stop()
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Crea las tablas si no existen."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id          SERIAL PRIMARY KEY,
                username    VARCHAR(80)  UNIQUE NOT NULL,
                password_hash TEXT       NOT NULL,
                rol         VARCHAR(20)  NOT NULL DEFAULT 'viewer',
                created_at  TIMESTAMP    DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS facturas (
                id            SERIAL PRIMARY KEY,
                obra_social   VARCHAR(200) NOT NULL,
                obra_cuit     VARCHAR(30)  DEFAULT \'\',
                periodo       VARCHAR(50)  NOT NULL,
                fecha_upload  TIMESTAMP    DEFAULT NOW(),
                archivo_nombre VARCHAR(200),
                uploaded_by   VARCHAR(80)
            );

            CREATE TABLE IF NOT EXISTS detalle_factura (
                id              SERIAL PRIMARY KEY,
                factura_id      INTEGER REFERENCES facturas(id) ON DELETE CASCADE,
                profesional     VARCHAR(200),
                matricula       VARCHAR(50),
                nro_socio       VARCHAR(50),
                resp_fiscal     VARCHAR(100),
                exento          NUMERIC DEFAULT 0,
                gravado         NUMERIC DEFAULT 0,
                facturado       NUMERIC DEFAULT 0,
                iva             NUMERIC DEFAULT 0,
                debitado        NUMERIC DEFAULT 0,
                total_cobrar    NUMERIC DEFAULT 0,
                honorarios      NUMERIC DEFAULT 0,
                gastos          NUMERIC DEFAULT 0,
                coseguro        NUMERIC DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS nros_arca (
                id              SERIAL PRIMARY KEY,
                detalle_id      INTEGER REFERENCES detalle_factura(id) ON DELETE CASCADE UNIQUE,
                nro_arca        VARCHAR(20)  DEFAULT '',
                estado          VARCHAR(20)  DEFAULT 'Pendiente',
                updated_at      TIMESTAMP    DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_facturas_os      ON facturas(obra_social);
            CREATE INDEX IF NOT EXISTS idx_facturas_periodo ON facturas(periodo);
            CREATE INDEX IF NOT EXISTS idx_detalle_fac      ON detalle_factura(factura_id);
            """)

        # Crear admin por defecto si no existe
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM usuarios WHERE username = 'admin'")
            if not cur.fetchone():
                pw_hash = bcrypt.hashpw(b"admin1234", bcrypt.gensalt()).decode()
                cur.execute(
                    "INSERT INTO usuarios (username, password_hash, rol) VALUES (%s, %s, %s)",
                    ("admin", pw_hash, "admin")
                )


# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────

def verificar_login(username: str, password: str):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, username, password_hash, rol FROM usuarios WHERE username = %s",
                (username.strip(),)
            )
            row = cur.fetchone()
    if not row:
        return None
    if bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return {"id": row["id"], "username": row["username"], "rol": row["rol"]}
    return None


def crear_usuario(username: str, password: str, rol: str = "viewer"):
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO usuarios (username, password_hash, rol) VALUES (%s, %s, %s)",
                (username.strip(), pw_hash, rol)
            )


def pantalla_login():
    st.markdown("""
    <div class="welcome-header" style="max-width:420px;margin:80px auto 0;">
      <p class="welcome-sub">Sistema de gestión</p>
      <p class="welcome-title">◆ Control de<br>Facturación</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        st.markdown('<p class="lbl">Usuario</p>', unsafe_allow_html=True)
        username = st.text_input("u", label_visibility="collapsed", placeholder="usuario")
        st.markdown('<p class="lbl">Contraseña</p>', unsafe_allow_html=True)
        password = st.text_input("p", type="password", label_visibility="collapsed", placeholder="••••••••")
        submitted = st.form_submit_button("Ingresar", type="primary", use_container_width=True)

    if submitted:
        user = verificar_login(username, password)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")


# ─────────────────────────────────────────────
#  DATOS — FACTURAS
# ─────────────────────────────────────────────

def obtener_obras_sociales():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT obra_social FROM facturas ORDER BY obra_social")
            return [r[0] for r in cur.fetchall()]


def obtener_periodos():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT periodo FROM facturas ORDER BY periodo DESC")
            return [r[0] for r in cur.fetchall()]


def obtener_facturas(obra_social=None, periodo=None, limit=5):
    sql = """
        SELECT f.id, f.obra_social, f.periodo, f.fecha_upload, f.archivo_nombre,
               COUNT(d.id) AS total_lineas,
               COUNT(DISTINCT d.profesional) AS total_profesionales,
               SUM(d.total) AS monto_total
        FROM facturas f
        LEFT JOIN detalle_factura d ON d.factura_id = f.id
    """
    params = []
    conditions = []
    if obra_social:
        conditions.append("f.obra_social = %s")
        params.append(obra_social)
    if periodo:
        conditions.append("f.periodo = %s")
        params.append(periodo)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " GROUP BY f.id ORDER BY f.fecha_upload DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def obtener_detalle(factura_id: int):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT d.id, d.profesional, d.matricula, d.especialidad,
                       d.codigo_practica, d.descripcion, d.cantidad,
                       d.valor_unit, d.total,
                       COALESCE(n.nro_arca, '')  AS nro_arca,
                       COALESCE(n.estado, 'Pendiente') AS estado
                FROM detalle_factura d
                LEFT JOIN nros_arca n ON n.detalle_id = d.id
                WHERE d.factura_id = %s
                ORDER BY d.profesional, d.id
            """, (factura_id,))
            return cur.fetchall()


def progreso_factura(factura_id: int):
    """Devuelve (profesionales_completos, total_profesionales)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(DISTINCT d.profesional) AS total,
                       COUNT(DISTINCT CASE WHEN n.estado = 'Completo' THEN d.profesional END) AS completos
                FROM detalle_factura d
                LEFT JOIN nros_arca n ON n.detalle_id = d.id
                WHERE d.factura_id = %s
            """, (factura_id,))
            row = cur.fetchone()
            return (row[1] or 0, row[0] or 0)


def actualizar_arca(detalle_id: int, nro_arca: str, estado: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO nros_arca (detalle_id, nro_arca, estado, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (detalle_id)
                DO UPDATE SET nro_arca = EXCLUDED.nro_arca,
                              estado   = EXCLUDED.estado,
                              updated_at = NOW()
            """, (detalle_id, nro_arca, estado))


def importar_excel(df: pd.DataFrame, obra_social: str, periodo: str, archivo_nombre: str, user: str, obra_cuit: str = "") -> int:
    """Inserta una nueva factura con su detalle. Mapea las columnas del modelo real."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO facturas (obra_social, periodo, archivo_nombre, uploaded_by, obra_cuit)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (obra_social, periodo, archivo_nombre, user, obra_cuit)
            )
            factura_id = cur.fetchone()[0]

            # Mapeo fijo para el modelo ImportesPorMedicos
            # Columnas: Profesional, NroSocio, Matricula, Responsabilidad Fiscal,
            #           Exento, Gravado, Facturado, IVA, Debitado, Total a Cobrar,
            #           Honorarios, Gastos, Coseguro
            for _, row in df.iterrows():
                def g(col, default=None):
                    if col in row.index and not pd.isna(row[col]):
                        return row[col]
                    return default

                profesional  = str(g("Profesional", "")).strip()
                matricula    = str(g("Matricula", "")).strip()
                nro_socio    = str(g("NroSocio", "")).strip()
                resp_fiscal  = str(g("Responsabilidad Fiscal", "")).strip()
                exento       = float(g("Exento", 0) or 0)
                gravado      = float(g("Gravado", 0) or 0)
                facturado    = float(g("Facturado", 0) or 0)
                iva          = float(g("IVA", 0) or 0)
                debitado     = float(g("Debitado", 0) or 0)
                total_cobrar = float(g("Total a Cobrar", 0) or 0)
                honorarios   = float(g("Honorarios", 0) or 0)
                gastos       = float(g("Gastos", 0) or 0)
                coseguro     = float(g("Coseguro", 0) or 0)

                cur.execute("""
                    INSERT INTO detalle_factura
                        (factura_id, profesional, matricula, nro_socio, resp_fiscal,
                         exento, gravado, facturado, iva, debitado,
                         total_cobrar, honorarios, gastos, coseguro)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                """, (
                    factura_id, profesional, matricula, nro_socio, resp_fiscal,
                    exento, gravado, facturado, iva, debitado,
                    total_cobrar, honorarios, gastos, coseguro,
                ))
                detalle_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO nros_arca (detalle_id, nro_arca, estado) VALUES (%s,\'\',\'Pendiente\')",
                    (detalle_id,)
                )
    return factura_id


def actualizar_arca(detalle_id: int, nro_arca: str, estado: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO nros_arca (detalle_id, nro_arca, estado, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (detalle_id)
                DO UPDATE SET nro_arca = EXCLUDED.nro_arca,
                              estado   = EXCLUDED.estado,
                              updated_at = NOW()
            """, (detalle_id, nro_arca, estado))


def importar_excel(df: pd.DataFrame, obra_social: str, periodo: str, archivo_nombre: str, user: str) -> int:
    """Inserta una nueva factura con su detalle. Devuelve el id de la factura."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO facturas (obra_social, periodo, archivo_nombre, uploaded_by)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (obra_social, periodo, archivo_nombre, user)
            )
            factura_id = cur.fetchone()[0]

            # Detectar columnas del Excel de forma flexible
            col_map = {}
            mapeos = {
                "profesional": ["profesional", "nombre", "medico", "doctor"],
                "matricula":   ["matricula", "matricula", "mat", "cta", "cuenta"],
                "especialidad":["especialidad", "especialidad"],
                "codigo_practica": ["practi. presta", "codigo", "practica", "cod"],
                "descripcion": ["descripcion practica", "descripcion", "descripcion_practica", "desc"],
                "cantidad":    ["cant. tratamientos", "cantidad", "cant"],
                "valor_unit":  ["valor_unit", "valor unit", "precio", "importe"],
                "total":       ["total"],
            }
            df_cols_norm = {c.lower().strip(): c for c in df.columns}
            for campo, candidatos in mapeos.items():
                for cand in candidatos:
                    if cand in df_cols_norm:
                        col_map[campo] = df_cols_norm[cand]
                        break

            for _, row in df.iterrows():
                def g(campo):
                    c = col_map.get(campo)
                    if not c or pd.isna(row.get(c)): return None
                    return row[c]

                cur.execute("""
                    INSERT INTO detalle_factura
                        (factura_id, profesional, matricula, especialidad,
                         codigo_practica, descripcion, cantidad, valor_unit, total)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                """, (
                    factura_id,
                    str(g("profesional") or ""),
                    str(g("matricula") or ""),
                    str(g("especialidad") or ""),
                    str(g("codigo_practica") or ""),
                    str(g("descripcion") or ""),
                    float(g("cantidad") or 1),
                    float(g("valor_unit") or 0),
                    float(g("total") or 0),
                ))
                detalle_id = cur.fetchone()[0]
                # Crear registro ARCA vacío
                cur.execute(
                    "INSERT INTO nros_arca (detalle_id, nro_arca, estado) VALUES (%s,'','Pendiente')",
                    (detalle_id,)
                )

    return factura_id


# ─────────────────────────────────────────────
#  COMPONENTES UI
# ─────────────────────────────────────────────

def badge_html(estado: str) -> str:
    cls = {"Pendiente": "badge-pendiente", "Solicitada": "badge-solicitada", "Completo": "badge-completo"}
    return f'<span class="badge {cls.get(estado,"badge-pendiente")}">{estado}</span>'


def render_barra_progreso(completos: int, total: int):
    pct = completos / total if total else 0
    color = "#238636" if pct == 1 else "#388bfd" if pct > 0 else "#484f58"
    st.markdown(
        f"""<div style="margin:8px 0">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px">
            <span style="font-size:.75rem;color:#8b949e;letter-spacing:.06em;text-transform:uppercase">
              Facturas ARCA completas
            </span>
            <span style="font-size:.75rem;font-family:'JetBrains Mono';color:{color}">
              {completos}/{total}
            </span>
          </div>
          <div style="background:#21262d;border-radius:4px;height:6px;overflow:hidden">
            <div style="background:{color};width:{pct*100:.1f}%;height:100%;border-radius:4px;
                        transition:width .4s ease"></div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
#  PANTALLAS
# ─────────────────────────────────────────────

def pantalla_home(user: dict):
    # ── Bienvenida ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="welcome-header">
      <p class="welcome-sub">Bienvenido, {user['username']}</p>
      <p class="welcome-title">Bienvenido al control de<br>facturación emitida</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Filtros ───────────────────────────────────────────────────────────
    obras = ["Todas"] + obtener_obras_sociales()
    periodos = ["Todos"] + obtener_periodos()

    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        st.markdown('<p class="lbl">Obra Social</p>', unsafe_allow_html=True)
        os_sel = st.selectbox("os", obras, label_visibility="collapsed")
    with col_f2:
        st.markdown('<p class="lbl">Período</p>', unsafe_allow_html=True)
        per_sel = st.selectbox("per", periodos, label_visibility="collapsed")
    with col_f3:
        st.markdown('<p class="lbl">Mostrar</p>', unsafe_allow_html=True)
        limit = st.selectbox("lim", [5, 10, 20, 50, 0], format_func=lambda x: "Todas" if x == 0 else str(x), label_visibility="collapsed")

    facturas = obtener_facturas(
        obra_social=None if os_sel == "Todas" else os_sel,
        periodo=None if per_sel == "Todos" else per_sel,
        limit=limit if limit else None,
    )

    st.markdown("---")

    if not facturas:
        st.info("No hay facturas que coincidan con los filtros.")
        return

    # ── Lista de facturas ─────────────────────────────────────────────────
    st.markdown('<p class="lbl">Facturas emitidas</p>', unsafe_allow_html=True)

    for f in facturas:
        completos, total_prof = progreso_factura(f["id"])
        pct = completos / total_prof if total_prof else 0
        color_prog = "#238636" if pct == 1 else "#388bfd" if pct > 0 else "#484f58"

        col_card, col_btn = st.columns([6, 1])
        with col_card:
            st.markdown(f"""
            <div class="factura-card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div>
                  <span style="font-weight:600;color:#f0f6fc;font-size:.95rem">{f['obra_social']}</span>
                  <span style="color:#484f58;font-size:.8rem;margin-left:10px">{f['periodo']}</span>
                </div>
                <span style="font-family:'JetBrains Mono';font-size:.8rem;color:#8b949e">
                  {f['fecha_upload'].strftime('%d/%m/%Y') if f['fecha_upload'] else ''}
                </span>
              </div>
              <div style="margin-top:8px;display:flex;gap:20px;align-items:center">
                <span style="font-size:.78rem;color:#8b949e">{f['total_lineas']} líneas</span>
                <span style="font-size:.78rem;color:#8b949e">{f['total_profesionales']} profesionales</span>
                <span style="font-family:'JetBrains Mono';font-size:.82rem;color:#3fb950">
                  $ {float(f['monto_total'] or 0):,.2f}
                </span>
              </div>
              <div style="margin-top:8px;background:#21262d;border-radius:3px;height:4px;overflow:hidden">
                <div style="background:{color_prog};width:{pct*100:.1f}%;height:100%;border-radius:3px"></div>
              </div>
              <div style="font-size:.7rem;color:{color_prog};margin-top:3px;font-family:'JetBrains Mono'">
                {completos}/{total_prof} profesionales con ARCA completo
              </div>
            </div>
            """, unsafe_allow_html=True)
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Ver detalle", key=f"btn_{f['id']}", use_container_width=True):
                st.session_state["factura_sel"] = f["id"]
                st.session_state["pantalla"] = "detalle"
                st.rerun()


def pantalla_detalle(factura_id: int, user: dict):
    # ── Cabecera ──────────────────────────────────────────────────────────
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM facturas WHERE id = %s", (factura_id,))
            fac = cur.fetchone()

    if not fac:
        st.error("Factura no encontrada.")
        return

    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← Volver", key="btn_volver"):
            st.session_state["pantalla"] = "home"
            st.rerun()
    with col_title:
        st.markdown(
            f"<h1>◆ {fac['obra_social']} <span style='color:#484f58;font-weight:400'>"
            f"· {fac['periodo']}</span></h1>",
            unsafe_allow_html=True,
        )

    # ── Barra de progreso ─────────────────────────────────────────────────
    completos, total_prof = progreso_factura(factura_id)
    render_barra_progreso(completos, total_prof)
    st.markdown("---")

    # ── Detalle ───────────────────────────────────────────────────────────
    filas = obtener_detalle(factura_id)
    if not filas:
        st.info("Esta factura no tiene líneas de detalle.")
        return

    st.markdown('<p class="lbl">Detalle de líneas · click en estado para editar</p>', unsafe_allow_html=True)

    # Agrupar por profesional
    profesionales = {}
    for f in filas:
        p = f["profesional"]
        if p not in profesionales:
            profesionales[p] = []
        profesionales[p].append(f)

    cambios = []

    for prof, lineas in profesionales.items():
        # Header de profesional
        total_prof_monto = sum(float(l["total"] or 0) for l in lineas)
        estados = [l["estado"] for l in lineas]
        estado_prof = "Completo" if all(e == "Completo" for e in estados) \
                      else "Solicitada" if any(e == "Solicitada" for e in estados) \
                      else "Pendiente"

        with st.expander(
            f"**{prof}** — {len(lineas)} prácticas · $ {total_prof_monto:,.2f}  "
            + ("✓" if estado_prof == "Completo" else ""),
            expanded=(estado_prof != "Completo"),
        ):
            for linea in lineas:
                lid = linea["id"]
                cols = st.columns([2, 2, 1, 1, 2, 2])

                with cols[0]:
                    st.markdown(f'<div class="lbl">{linea["codigo_practica"]}</div>'
                                f'<div style="font-size:.85rem;color:#c9d1d9">{linea["descripcion"][:40]}</div>',
                                unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(f'<div class="lbl">Matrícula</div>'
                                f'<div style="font-family:JetBrains Mono;font-size:.82rem;color:#8b949e">'
                                f'{linea["matricula"]}</div>',
                                unsafe_allow_html=True)
                with cols[2]:
                    st.markdown(f'<div class="lbl">Cant</div>'
                                f'<div style="font-family:JetBrains Mono;font-size:.82rem">{linea["cantidad"]}</div>',
                                unsafe_allow_html=True)
                with cols[3]:
                    st.markdown(f'<div class="lbl">Total</div>'
                                f'<div style="font-family:JetBrains Mono;font-size:.82rem;color:#3fb950">'
                                f'$ {float(linea["total"] or 0):,.2f}</div>',
                                unsafe_allow_html=True)
                with cols[4]:
                    nro_actual = linea["nro_arca"] or ""
                    nuevo_nro = st.text_input(
                        f"ARCA_{lid}",
                        value=nro_actual,
                        placeholder="A-00000-00000000",
                        label_visibility="collapsed",
                        key=f"nro_{lid}",
                    )
                with cols[5]:
                    # Auto-completar estado si el formato ARCA es válido
                    if nuevo_nro and ARCA_RE.match(nuevo_nro.strip()):
                        estado_auto = "Completo"
                    else:
                        estado_auto = None

                    opciones_estado = ["Pendiente", "Solicitada", "Completo"]
                    idx_default = opciones_estado.index(linea["estado"]) if linea["estado"] in opciones_estado else 0
                    if estado_auto:
                        idx_default = opciones_estado.index(estado_auto)

                    nuevo_estado = st.selectbox(
                        f"est_{lid}",
                        opciones_estado,
                        index=idx_default,
                        label_visibility="collapsed",
                        key=f"est_{lid}",
                    )
                    st.markdown(badge_html(nuevo_estado), unsafe_allow_html=True)

                cambios.append((lid, nuevo_nro.strip(), nuevo_estado))
                st.markdown('<hr style="margin:6px 0;border-color:#161b22">', unsafe_allow_html=True)

    st.markdown("---")

    col_save, col_export = st.columns([2, 1])
    with col_save:
        if st.button("Guardar cambios", type="primary", use_container_width=True):
            errores = []
            for lid, nro, estado in cambios:
                if nro and not ARCA_RE.match(nro):
                    errores.append(f"Formato inválido: {nro} (debe ser A-00000-00000000)")
                else:
                    actualizar_arca(lid, nro, estado)
            if errores:
                for e in errores:
                    st.error(e)
            else:
                st.success("Cambios guardados correctamente.")
                st.rerun()

    with col_export:
        # Exportar Excel con estado actual
        rows = obtener_detalle(factura_id)
        df_exp = pd.DataFrame([dict(r) for r in rows])
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df_exp.to_excel(writer, index=False, sheet_name="Detalle")
        buf.seek(0)
        st.download_button(
            "Exportar Excel",
            data=buf.getvalue(),
            file_name=f"factura_{factura_id}_{fac['obra_social'].replace(' ','_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def pantalla_importar(user: dict):
    st.markdown("<h1>◆ Importar facturación</h1>", unsafe_allow_html=True)
    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<p class="lbl">Obra Social</p>', unsafe_allow_html=True)
        os_sel = st.selectbox(
            "os_imp",
            options=["— Seleccionar —"] + OBRAS_NOMBRES,
            label_visibility="collapsed",
        )
        obra_social = None
        obra_cuit   = None
        if os_sel != "— Seleccionar —":
            codigo = int(os_sel.split(" - ")[0])
            match  = next((o for o in OBRAS_SOCIALES if o["codigo"] == codigo), None)
            if match:
                obra_social = match["nombre"]
                obra_cuit   = match["cuit"]
                st.markdown(
                    f'<div style="font-family:JetBrains Mono;font-size:.75rem;color:#484f58;margin-top:4px">'
                    f'CUIT {obra_cuit}</div>',
                    unsafe_allow_html=True,
                )

    with col_b:
        st.markdown('<p class="lbl">Período</p>', unsafe_allow_html=True)
        periodo = st.text_input("perr", placeholder="Ej: Mayo 2026", label_visibility="collapsed")

    st.markdown('<p class="lbl">Archivo Excel</p>', unsafe_allow_html=True)
    archivo = st.file_uploader("Subir Excel", type=["xlsx"], label_visibility="collapsed")

    # Auto-detectar período del nombre del archivo
    if archivo and not periodo:
        nombre = archivo.name
        meses = {
            "enero":"Enero","febrero":"Febrero","marzo":"Marzo","abril":"Abril",
            "mayo":"Mayo","junio":"Junio","julio":"Julio","agosto":"Agosto",
            "septiembre":"Septiembre","octubre":"Octubre","noviembre":"Noviembre","diciembre":"Diciembre"
        }
        for mes_en, mes_es in meses.items():
            m = re.search(mes_en + r"[_\s-]*(\d{4})", nombre.lower())
            if m:
                periodo = f"{mes_es} {m.group(1)}"
                break
        if not periodo:
            m = re.search(r"(\d{4})[_\s-]*(\d{2})", nombre)
            if m:
                periodo = f"{m.group(2)}/{m.group(1)}"

    if archivo and obra_social and periodo:
        df = pd.read_excel(archivo)

        # Mostrar vista previa con columnas del modelo real
        st.markdown(f'<p class="lbl">Vista previa — {len(df)} profesionales · Obra Social: {obra_social} · {periodo}</p>', unsafe_allow_html=True)

        # Columnas a mostrar en preview
        cols_preview = [c for c in [
            "Profesional","Matricula","Responsabilidad Fiscal",
            "Exento","Gravado","Facturado","IVA","Total a Cobrar"
        ] if c in df.columns]
        st.dataframe(df[cols_preview] if cols_preview else df, use_container_width=True, hide_index=True)

        # Métricas rápidas
        m1, m2, m3 = st.columns(3)
        m1.metric("Profesionales", len(df))
        if "Total a Cobrar" in df.columns:
            m2.metric("Total a cobrar", f"$ {df['Total a Cobrar'].sum():,.2f}")
        if "Facturado" in df.columns:
            m3.metric("Facturado", f"$ {df['Facturado'].sum():,.2f}")

        st.markdown("---")

        if st.button("Confirmar importación", type="primary", use_container_width=True):
            try:
                fid = importar_excel(df, obra_social, periodo, archivo.name, user["username"], obra_cuit)
                st.success(f"✓ Importación exitosa — {len(df)} profesionales cargados (ID {fid})")
                st.session_state["pantalla"] = "home"
                st.rerun()
            except Exception as e:
                st.error(f"Error al importar: {e}")
                import traceback
                st.code(traceback.format_exc())

    elif archivo and not obra_social:
        st.warning("Seleccioná la Obra Social para continuar.")
    elif archivo and not periodo:
        st.warning("Ingresá el período para continuar.")


def pantalla_admin(user: dict):
    if user["rol"] != "admin":
        st.error("Acceso denegado.")
        return

    st.markdown("<h1>◆ Administración</h1>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### Crear usuario")
    col_u, col_p, col_r = st.columns(3)
    with col_u:
        st.markdown('<p class="lbl">Usuario</p>', unsafe_allow_html=True)
        new_user = st.text_input("nu", label_visibility="collapsed", placeholder="nombre")
    with col_p:
        st.markdown('<p class="lbl">Contraseña</p>', unsafe_allow_html=True)
        new_pass = st.text_input("np", type="password", label_visibility="collapsed", placeholder="••••••••")
    with col_r:
        st.markdown('<p class="lbl">Rol</p>', unsafe_allow_html=True)
        new_rol = st.selectbox("nr", ["viewer", "admin"], label_visibility="collapsed")

    if st.button("Crear usuario", use_container_width=True):
        if new_user and new_pass:
            try:
                crear_usuario(new_user, new_pass, new_rol)
                st.success(f"Usuario '{new_user}' creado.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Completá usuario y contraseña.")

    st.markdown("---")

    # Lista usuarios
    st.markdown("### Usuarios existentes")
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, username, rol, created_at FROM usuarios ORDER BY created_at")
            usuarios = cur.fetchall()

    df_u = pd.DataFrame([dict(u) for u in usuarios])
    st.dataframe(df_u[["username","rol","created_at"]], use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

# Inicializar DB
try:
    init_db()
except Exception as e:
    st.error(f"Error conectando a la base de datos: {e}")
    st.stop()

# Auth
if "user" not in st.session_state:
    pantalla_login()
    st.stop()

user = st.session_state["user"]

# Inicializar estado de navegación
if "pantalla" not in st.session_state:
    st.session_state["pantalla"] = "home"

# ── Sidebar navegación ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<div style='color:#484f58;font-size:.75rem;letter-spacing:.08em;text-transform:uppercase'>Sesión activa</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#f0f6fc;font-weight:600;margin-bottom:16px'>{user['username']} <span style='color:#484f58;font-size:.75rem'>({user['rol']})</span></div>", unsafe_allow_html=True)
    st.markdown("---")

    if st.button("◆ Inicio", use_container_width=True,
                 type="primary" if st.session_state["pantalla"] == "home" else "secondary"):
        st.session_state["pantalla"] = "home"
        st.rerun()

    if st.button("↑ Importar", use_container_width=True,
                 type="primary" if st.session_state["pantalla"] == "importar" else "secondary"):
        st.session_state["pantalla"] = "importar"
        st.rerun()

    if user["rol"] == "admin":
        if st.button("⚙ Admin", use_container_width=True,
                     type="primary" if st.session_state["pantalla"] == "admin" else "secondary"):
            st.session_state["pantalla"] = "admin"
            st.rerun()

    st.markdown("---")
    if st.button("Cerrar sesión", use_container_width=True):
        del st.session_state["user"]
        del st.session_state["pantalla"]
        st.rerun()

# ── Routing ───────────────────────────────────────────────────────────────
pantalla = st.session_state["pantalla"]

if pantalla == "home":
    pantalla_home(user)
elif pantalla == "detalle":
    fid = st.session_state.get("factura_sel")
    if fid:
        pantalla_detalle(fid, user)
    else:
        st.session_state["pantalla"] = "home"
        st.rerun()
elif pantalla == "importar":
    pantalla_importar(user)
elif pantalla == "admin":
    pantalla_admin(user)
