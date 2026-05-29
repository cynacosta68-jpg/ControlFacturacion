import streamlit as st
import pandas as pd
import psycopg2
import bcrypt
import re
import io
import os
import json
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
FC_RE   = re.compile(r'^FC\s*\d{5}-\d{8}$', re.IGNORECASE)

OBRAS_SOCIALES = [
  {"codigo": 1064,  "nombre": "O.S.D.I.P.P.",                                          "cuit": "30-54741601-1"},
  {"codigo": 10001, "nombre": "OSAPM DE LA R.A.",                                       "cuit": "30-62313465-9"},
  {"codigo": 10019, "nombre": "CORTE SUPREMA DE JUSTICIA O. S. DEL PODER JUDICIAL",    "cuit": "30-63619685-8"},
  {"codigo": 10020, "nombre": "SUPERINTENDENCIA DE BIENESTAR POLICIA FEDERAL ARG.",     "cuit": "30-54666267-1"},
  {"codigo": 10021, "nombre": "S.E.R.O.S.",                                             "cuit": "30-99922290-7"},
  {"codigo": 10039, "nombre": "O.S.P.I.A.",                                             "cuit": "30-64399773-4"},
  {"codigo": 10040, "nombre": "GRIAL Salud SA",                                         "cuit": "30-71434838-4"},
  {"codigo": 10043, "nombre": "O.S.DEL PERSONAL DE TELEVISION",                         "cuit": "30-51674838-5"},
  {"codigo": 10050, "nombre": "JERARQUICOS SALUD",                                      "cuit": "33-71018560-9"},
  {"codigo": 10053, "nombre": "MEDICUS S.A.",                                            "cuit": "30-54677131-4"},
  {"codigo": 10056, "nombre": "SWISS MEDICAL S.A.",                                     "cuit": "30-64539742-0"},
  {"codigo": 10060, "nombre": "OSDE",                                                   "cuit": "30-51784889-5"},
  {"codigo": 10062, "nombre": "GALENO Argentina S.A.",                                  "cuit": "30-67786696-7"},
  {"codigo": 10064, "nombre": "ACCORD SALUD",                                           "cuit": "30-71138558-3"},
  {"codigo": 10065, "nombre": "MEDIFE",                                                 "cuit": "30-54638805-0"},
  {"codigo": 10066, "nombre": "OMINT S.A.",                                             "cuit": "30-52244148-6"},
  {"codigo": 10067, "nombre": "IOMA",                                                   "cuit": "30-54398047-5"},
  {"codigo": 10068, "nombre": "PAMI",                                                   "cuit": "30-53171126-8"},
  {"codigo": 10070, "nombre": "OS BANCARIOS",                                           "cuit": "30-54494316-5"},
  {"codigo": 10072, "nombre": "SANCOR SALUD",                                           "cuit": "30-57642690-1"},
  {"codigo": 10075, "nombre": "APRES",                                                  "cuit": "30-62546917-8"},
  {"codigo": 10076, "nombre": "DASPU",                                                  "cuit": "30-61893218-0"},
  {"codigo": 10078, "nombre": "OS PERSONAL CIVIL DE LA NACION",                        "cuit": "30-54640439-5"},
  {"codigo": 10079, "nombre": "OS DEL PODER JUDICIAL DE LA NACION",                    "cuit": "30-54694924-6"},
  {"codigo": 10080, "nombre": "SEROS",                                                  "cuit": "30-68501023-2"},
  {"codigo": 10081, "nombre": "OS EMPLEADOS MUNICIPALES CR",                            "cuit": "30-64839908-0"},
  {"codigo": 10082, "nombre": "OSPAT",                                                  "cuit": "30-54717060-0"},
  {"codigo": 10083, "nombre": "OS UNION PERSONAL",                                     "cuit": "30-55596282-7"},
  {"codigo": 10084, "nombre": "OS PEONES RURALES",                                     "cuit": "30-54664895-0"},
  {"codigo": 10085, "nombre": "OSPEDYC",                                                "cuit": "30-51784889-5"},
  {"codigo": 10086, "nombre": "AMFFA",                                                  "cuit": "30-55450012-0"},
  {"codigo": 10087, "nombre": "OS DOCENTES PARTICULARES",                               "cuit": "30-54640341-0"},
  {"codigo": 10088, "nombre": "OSPECON",                                                "cuit": "30-54798023-4"},
  {"codigo": 10089, "nombre": "OS PERSONAL ADUANAS",                                   "cuit": "30-54640341-0"},
  {"codigo": 10090, "nombre": "OS CAMIONEROS",                                          "cuit": "30-52135730-7"},
  {"codigo": 10091, "nombre": "OSPIA",                                                  "cuit": "30-54640341-0"},
  {"codigo": 10092, "nombre": "OSSEG",                                                  "cuit": "30-54640341-0"},
  {"codigo": 10093, "nombre": "OS PERSONAL GRAFICO",                                   "cuit": "30-54640341-0"},
  {"codigo": 10094, "nombre": "OSPIC",                                                  "cuit": "30-54640341-0"},
  {"codigo": 10095, "nombre": "OSJERA",                                                 "cuit": "30-54640341-0"},
  {"codigo": 10096, "nombre": "OSSIMRA",                                                "cuit": "30-54640341-0"},
  {"codigo": 10097, "nombre": "OSPACA",                                                 "cuit": "30-54640341-0"},
  {"codigo": 10098, "nombre": "OS EMPLEADOS COMERCIO",                                  "cuit": "30-54494316-5"},
  {"codigo": 10099, "nombre": "OS COLEGIO MEDICO CR",                                   "cuit": "30-64839908-0"},
  {"codigo": 10100, "nombre": "OSPRERA",                                                "cuit": "30-54640341-0"},
  {"codigo": 10101, "nombre": "OS GENDARMERIA NACIONAL",                                "cuit": "30-54640341-0"},
  {"codigo": 10102, "nombre": "OS PREFECTURA NAVAL",                                    "cuit": "30-54640341-0"},
  {"codigo": 10103, "nombre": "OS PERSONAL AERONAUTICO",                                "cuit": "30-54640341-0"},
  {"codigo": 10104, "nombre": "OS PERSONAL VIAL",                                       "cuit": "30-54640341-0"},
  {"codigo": 10105, "nombre": "OS PERSONAL RURAL",                                      "cuit": "30-54640341-0"},
  {"codigo": 10106, "nombre": "OSPECAF",                                                "cuit": "30-54640341-0"},
  {"codigo": 10107, "nombre": "OSTEP",                                                  "cuit": "30-54640341-0"},
  {"codigo": 10108, "nombre": "OS EMPLEADOS PRENSA",                                    "cuit": "30-54640341-0"},
  {"codigo": 10109, "nombre": "OSPOCE",                                                 "cuit": "30-54640341-0"},
  {"codigo": 10110, "nombre": "OSECAC",                                                 "cuit": "30-54640341-0"},
  {"codigo": 10111, "nombre": "OSPEDYC CHUBUT",                                         "cuit": "30-54640341-0"},
  {"codigo": 10112, "nombre": "OSPLAD",                                                 "cuit": "30-54640341-0"},
  {"codigo": 10113, "nombre": "OS PERSONAL SEGUROS",                                    "cuit": "30-54640341-0"},
  {"codigo": 10114, "nombre": "OSAM",                                                   "cuit": "30-54640341-0"},
  {"codigo": 10115, "nombre": "OS EMPLEADOS HOTELERIA",                                 "cuit": "30-54640341-0"},
  {"codigo": 10116, "nombre": "OSPSA",                                                  "cuit": "30-54640341-0"},
  {"codigo": 10117, "nombre": "OSFATUN",                                                "cuit": "30-54640341-0"},
  {"codigo": 10118, "nombre": "OS PERSONAL NAUTICO",                                    "cuit": "30-54640341-0"},
  {"codigo": 10119, "nombre": "OSPIF",                                                  "cuit": "30-54640341-0"},
  {"codigo": 10120, "nombre": "OSDOP",                                                  "cuit": "30-54640341-0"},
  {"codigo": 10121, "nombre": "OSPATCA",                                                "cuit": "30-54640341-0"},
  {"codigo": 10122, "nombre": "OSJUBPER",                                               "cuit": "30-54640341-0"},
  {"codigo": 10123, "nombre": "OSCOEMA",                                                "cuit": "30-54640341-0"},
  {"codigo": 10124, "nombre": "OS EMPLEADOS TEXTILES",                                  "cuit": "30-54640341-0"},
  {"codigo": 10125, "nombre": "OSFATLYF",                                               "cuit": "30-54640341-0"},
  {"codigo": 10126, "nombre": "OSSPIV",                                                 "cuit": "30-54640341-0"},
  {"codigo": 10127, "nombre": "OSPLAD",                                                 "cuit": "30-54640341-0"},
  {"codigo": 10128, "nombre": "OS EMPLEADOS GASTRONOMIA",                               "cuit": "30-54640341-0"},
  {"codigo": 10129, "nombre": "OSPICAL",                                                "cuit": "30-54640341-0"},
  {"codigo": 10130, "nombre": "OS PERSONAL CALZADO",                                    "cuit": "30-54640341-0"},
  {"codigo": 10131, "nombre": "OSUOM",                                                  "cuit": "30-54640341-0"},
  {"codigo": 10140, "nombre": "IOSFA",                                                  "cuit": "30-54640341-0"},
  {"codigo": 10150, "nombre": "OSPIC",                                                  "cuit": "30-54640341-0"},
  {"codigo": 10160, "nombre": "OS PERSONAL METALURGICO",                                "cuit": "30-54640341-0"},
  {"codigo": 10165, "nombre": "OSUPCN",                                                 "cuit": "30-54640341-0"},
  {"codigo": 10166, "nombre": "OSPACA",                                                 "cuit": "30-54640341-0"},
  {"codigo": 10167, "nombre": "OSPA",                                                   "cuit": "30-54640341-0"},
  {"codigo": 10168, "nombre": "OSPPRA",                                                 "cuit": "30-54640341-0"},
  {"codigo": 10169, "nombre": "OSPAT",                                                  "cuit": "30-54640341-0"},
  {"codigo": 10170, "nombre": "GLOBAL EMPRESARIA S.A.",                                 "cuit": "30-71513403-5"},
]
OBRAS_NOMBRES = [f"{o['codigo']} - {o['nombre']}" for o in OBRAS_SOCIALES]

# ─────────────────────────────────────────────
#  ESTILOS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
  html,body,[class*="css"]{font-family:'Syne',sans-serif;background:#080b0f;color:#c9d1d9}
  .stApp{background:#080b0f}
  [data-testid="stSidebar"]{background:#0d1117;border-right:1px solid #21262d}
  h1{font-size:1.5rem!important;font-weight:700!important;color:#f0f6fc!important;letter-spacing:.03em}
  h2{font-size:.85rem!important;font-weight:500!important;color:#484f58!important;letter-spacing:.1em;text-transform:uppercase}
  hr{border-color:#21262d!important;margin:.8rem 0!important}
  input,textarea,.stTextInput input,.stSelectbox select,.stDateInput input{
    background:#0d1117!important;border:1px solid #21262d!important;
    color:#c9d1d9!important;border-radius:6px!important;
    font-family:'JetBrains Mono',monospace!important;font-size:.82rem!important}
  input:focus{border-color:#388bfd!important;box-shadow:0 0 0 3px #388bfd22!important}
  .stButton>button[kind="primary"]{background:#238636!important;color:#fff!important;
    border:1px solid #2ea043!important;border-radius:6px!important;
    font-family:'Syne',sans-serif!important;font-weight:600!important;
    letter-spacing:.04em!important;padding:.45rem 1.2rem!important}
  .stButton>button[kind="secondary"]{background:transparent!important;
    border:1px solid #30363d!important;color:#8b949e!important;border-radius:6px!important;font-size:.82rem!important}
  .stButton>button[kind="secondary"]:hover{border-color:#8b949e!important;color:#c9d1d9!important}
  .stDownloadButton>button{background:transparent!important;border:1px solid #388bfd!important;
    color:#388bfd!important;border-radius:6px!important;font-size:.82rem!important}
  .stProgress>div>div{background:#238636!important}
  [data-testid="stMetric"]{background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:12px 16px}
  [data-testid="stMetricValue"]{color:#f0f6fc!important;font-family:'JetBrains Mono'!important}
  [data-testid="stMetricLabel"]{color:#484f58!important;font-size:.7rem!important;text-transform:uppercase;letter-spacing:.08em}
  .stDataFrame{border:1px solid #21262d!important;border-radius:8px!important}
  [data-testid="stFileUploader"]{border:1px dashed #21262d!important;border-radius:8px!important;background:#0d1117!important}
  .badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.7rem;
    font-family:'JetBrains Mono';font-weight:500;letter-spacing:.04em}
  .badge-pendiente{background:#1a1500;border:1px solid #3a3000;color:#f2c94c}
  .badge-solicitada{background:#001229;border:1px solid #00366b;color:#388bfd}
  .badge-completo{background:#0d1f0d;border:1px solid #1a3a1a;color:#3fb950}
  .lbl{font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:#484f58;margin-bottom:4px}
  .fc-card{background:#0d1117;border:1px solid #21262d;border-radius:8px;
    padding:14px 18px;margin:4px 0;transition:border-color .2s}
  .fc-card:hover{border-color:#388bfd}
  .prof-row{background:#0d1117;border:1px solid #161b22;border-radius:6px;
    padding:10px 14px;margin:4px 0}
  .section-title{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
    color:#388bfd;border-bottom:1px solid #21262d;padding-bottom:6px;margin:16px 0 10px 0}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  BASE DE DATOS
# ─────────────────────────────────────────────
@contextmanager
def get_conn():
    url = os.environ.get("DATABASE_URL","")
    if not url:
        st.error("Variable DATABASE_URL no configurada.")
        st.stop()
    conn = psycopg2.connect(url, sslmode="require")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id            SERIAL PRIMARY KEY,
                username      VARCHAR(80) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                rol           VARCHAR(20) DEFAULT 'viewer',
                created_at    TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS facturas (
                id             SERIAL PRIMARY KEY,
                nro_factura    VARCHAR(30)  DEFAULT '',
                obra_social    VARCHAR(200) NOT NULL,
                obra_cuit      VARCHAR(30)  DEFAULT '',
                periodo        VARCHAR(50)  NOT NULL,
                fecha_upload   TIMESTAMP DEFAULT NOW(),
                archivo_nombre VARCHAR(200),
                uploaded_by    VARCHAR(80)
            );

            CREATE TABLE IF NOT EXISTS detalle_factura (
                id           SERIAL PRIMARY KEY,
                factura_id   INTEGER REFERENCES facturas(id) ON DELETE CASCADE,
                profesional  VARCHAR(200),
                matricula    VARCHAR(50),
                nro_socio    VARCHAR(50),
                resp_fiscal  VARCHAR(100),
                exento       NUMERIC DEFAULT 0,
                gravado      NUMERIC DEFAULT 0,
                facturado    NUMERIC DEFAULT 0,
                iva          NUMERIC DEFAULT 0,
                debitado     NUMERIC DEFAULT 0,
                total_cobrar NUMERIC DEFAULT 0,
                honorarios   NUMERIC DEFAULT 0,
                gastos       NUMERIC DEFAULT 0,
                coseguro     NUMERIC DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS comprobantes (
                id            SERIAL PRIMARY KEY,
                detalle_id    INTEGER REFERENCES detalle_factura(id) ON DELETE CASCADE,
                nro_arca      VARCHAR(20) DEFAULT '',
                estado        VARCHAR(20) DEFAULT 'Pendiente',
                updated_at    TIMESTAMP DEFAULT NOW()
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_comprobantes_detalle
                ON comprobantes(detalle_id);
            CREATE INDEX IF NOT EXISTS idx_detalle_fac
                ON detalle_factura(factura_id);
            CREATE INDEX IF NOT EXISTS idx_facturas_os
                ON facturas(obra_social);
            CREATE INDEX IF NOT EXISTS idx_detalle_prof
                ON detalle_factura(profesional);
            """)
        # Migraciones: agregar columnas nuevas si no existen
        migraciones = [
            "ALTER TABLE facturas ADD COLUMN IF NOT EXISTS nro_factura VARCHAR(30) DEFAULT ''",
            "ALTER TABLE facturas ADD COLUMN IF NOT EXISTS obra_cuit VARCHAR(30) DEFAULT ''",
            "ALTER TABLE detalle_factura ADD COLUMN IF NOT EXISTS nro_socio VARCHAR(50)",
            "ALTER TABLE detalle_factura ADD COLUMN IF NOT EXISTS resp_fiscal VARCHAR(100)",
            "ALTER TABLE detalle_factura ADD COLUMN IF NOT EXISTS exento NUMERIC DEFAULT 0",
            "ALTER TABLE detalle_factura ADD COLUMN IF NOT EXISTS gravado NUMERIC DEFAULT 0",
            "ALTER TABLE detalle_factura ADD COLUMN IF NOT EXISTS facturado NUMERIC DEFAULT 0",
            "ALTER TABLE detalle_factura ADD COLUMN IF NOT EXISTS iva NUMERIC DEFAULT 0",
            "ALTER TABLE detalle_factura ADD COLUMN IF NOT EXISTS debitado NUMERIC DEFAULT 0",
            "ALTER TABLE detalle_factura ADD COLUMN IF NOT EXISTS total_cobrar NUMERIC DEFAULT 0",
            "ALTER TABLE detalle_factura ADD COLUMN IF NOT EXISTS honorarios NUMERIC DEFAULT 0",
            "ALTER TABLE detalle_factura ADD COLUMN IF NOT EXISTS gastos NUMERIC DEFAULT 0",
            "ALTER TABLE detalle_factura ADD COLUMN IF NOT EXISTS coseguro NUMERIC DEFAULT 0",
            # Renombrar tabla nros_arca → comprobantes si existe la vieja
            """DO $$ BEGIN
               IF EXISTS (SELECT FROM information_schema.tables WHERE table_name='nros_arca')
                  AND NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name='comprobantes')
               THEN ALTER TABLE nros_arca RENAME TO comprobantes; END IF; END $$""",
        ]
        with conn.cursor() as cur:
            for sql_m in migraciones:
                cur.execute(sql_m)
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM usuarios WHERE username='admin'")
            if not cur.fetchone():
                h = bcrypt.hashpw(b"admin1234", bcrypt.gensalt()).decode()
                cur.execute(
                    "INSERT INTO usuarios(username,password_hash,rol) VALUES(%s,%s,%s)",
                    ("admin", h, "admin")
                )


# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────
def verificar_login(username, password):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id,username,password_hash,rol FROM usuarios WHERE username=%s",
                (username.strip(),)
            )
            row = cur.fetchone()
    if not row:
        return None
    if bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return {"id": row["id"], "username": row["username"], "rol": row["rol"]}
    return None


def crear_usuario(username, password, rol="viewer"):
    h = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO usuarios(username,password_hash,rol) VALUES(%s,%s,%s)",
                (username.strip(), h, rol)
            )


# ─────────────────────────────────────────────
#  QUERIES
# ─────────────────────────────────────────────
def obtener_obras_sociales_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT obra_social FROM facturas ORDER BY obra_social")
            return [r[0] for r in cur.fetchall()]

def obtener_periodos_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT periodo FROM facturas ORDER BY periodo DESC")
            return [r[0] for r in cur.fetchall()]

def obtener_facturas(obra_social=None, periodo=None, limit=5):
    sql = """
        SELECT f.id, f.nro_factura, f.obra_social, f.periodo,
               f.fecha_upload, f.archivo_nombre,
               COUNT(DISTINCT d.id) AS total_profesionales,
               SUM(d.total_cobrar)  AS monto_total,
               COUNT(DISTINCT CASE WHEN c.estado='Completo' THEN d.id END) AS completos
        FROM facturas f
        LEFT JOIN detalle_factura d ON d.factura_id = f.id
        LEFT JOIN comprobantes c    ON c.detalle_id = d.id
    """
    params, conds = [], []
    if obra_social:
        conds.append("f.obra_social=%s"); params.append(obra_social)
    if periodo:
        conds.append("f.periodo=%s"); params.append(periodo)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " GROUP BY f.id ORDER BY f.fecha_upload DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

def obtener_detalle(factura_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT d.id, d.profesional, d.matricula, d.nro_socio, d.resp_fiscal,
                       d.exento, d.gravado, d.facturado, d.iva, d.debitado,
                       d.total_cobrar, d.honorarios, d.gastos, d.coseguro,
                       COALESCE(c.nro_arca,'')        AS nro_arca,
                       COALESCE(c.estado,'Pendiente') AS estado
                FROM detalle_factura d
                LEFT JOIN comprobantes c ON c.detalle_id = d.id
                WHERE d.factura_id = %s
                ORDER BY d.profesional
            """, (factura_id,))
            return cur.fetchall()

def obtener_facturas_de_profesional(profesional: str, excluir_factura_id: int = None):
    """Todas las facturas donde aparece este profesional (para vincular comprobante)."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            sql = """
                SELECT f.id, f.nro_factura, f.obra_social, f.periodo,
                       d.id AS detalle_id, d.total_cobrar,
                       COALESCE(c.nro_arca,'')        AS nro_arca,
                       COALESCE(c.estado,'Pendiente') AS estado
                FROM detalle_factura d
                JOIN facturas f       ON f.id = d.factura_id
                LEFT JOIN comprobantes c ON c.detalle_id = d.id
                WHERE d.profesional = %s
            """
            params = [profesional]
            if excluir_factura_id:
                sql += " AND f.id != %s"
                params.append(excluir_factura_id)
            sql += " ORDER BY f.fecha_upload DESC"
            cur.execute(sql, params)
            return cur.fetchall()

def upsert_comprobante(detalle_id: int, nro_arca: str, estado: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO comprobantes(detalle_id, nro_arca, estado, updated_at)
                VALUES(%s,%s,%s,NOW())
                ON CONFLICT(detalle_id)
                DO UPDATE SET nro_arca=EXCLUDED.nro_arca,
                              estado=EXCLUDED.estado,
                              updated_at=NOW()
            """, (detalle_id, nro_arca, estado))

def importar_excel(df, obra_social, periodo, archivo_nombre, user, obra_cuit="", nro_factura=""):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO facturas(nro_factura,obra_social,obra_cuit,periodo,archivo_nombre,uploaded_by)
                   VALUES(%s,%s,%s,%s,%s,%s) RETURNING id""",
                (nro_factura.strip(), obra_social, obra_cuit, periodo, archivo_nombre, user)
            )
            factura_id = cur.fetchone()[0]

            for _, row in df.iterrows():
                def g(col, default=0):
                    return row[col] if col in row.index and not pd.isna(row.get(col)) else default

                cur.execute("""
                    INSERT INTO detalle_factura
                        (factura_id,profesional,matricula,nro_socio,resp_fiscal,
                         exento,gravado,facturado,iva,debitado,
                         total_cobrar,honorarios,gastos,coseguro)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                """, (
                    factura_id,
                    str(g("Profesional","")).strip(),
                    str(g("Matricula","")).strip(),
                    str(g("NroSocio","")).strip(),
                    str(g("Responsabilidad Fiscal","")).strip(),
                    float(g("Exento",0) or 0),
                    float(g("Gravado",0) or 0),
                    float(g("Facturado",0) or 0),
                    float(g("IVA",0) or 0),
                    float(g("Debitado",0) or 0),
                    float(g("Total a Cobrar",0) or 0),
                    float(g("Honorarios",0) or 0),
                    float(g("Gastos",0) or 0),
                    float(g("Coseguro",0) or 0),
                ))
                detalle_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO comprobantes(detalle_id,nro_arca,estado) VALUES(%s,'','Pendiente')",
                    (detalle_id,)
                )
    return factura_id


# ─────────────────────────────────────────────
#  HELPERS UI
# ─────────────────────────────────────────────
def badge(estado):
    cls = {"Pendiente":"badge-pendiente","Solicitada":"badge-solicitada","Completo":"badge-completo"}
    return f'<span class="badge {cls.get(estado,"badge-pendiente")}">{estado}</span>'

def barra_progreso(completos, total, label="Comprobantes completos"):
    pct   = completos / total if total else 0
    color = "#238636" if pct==1 else "#388bfd" if pct>0 else "#484f58"
    st.markdown(f"""
    <div style="margin:6px 0 12px 0">
      <div style="display:flex;justify-content:space-between;margin-bottom:4px">
        <span style="font-size:.72rem;color:#8b949e;letter-spacing:.06em;text-transform:uppercase">{label}</span>
        <span style="font-size:.75rem;font-family:'JetBrains Mono';color:{color}">{completos}/{total}</span>
      </div>
      <div style="background:#21262d;border-radius:4px;height:5px;overflow:hidden">
        <div style="background:{color};width:{pct*100:.1f}%;height:100%;border-radius:4px;transition:width .4s"></div>
      </div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────
def pantalla_login():
    st.markdown("""
    <div style="max-width:400px;margin:80px auto 0;background:linear-gradient(135deg,#0d1117,#0d1f0d);
         border:1px solid #21262d;border-radius:12px;padding:32px 36px">
      <div style="font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:#484f58;margin-bottom:8px">
        Sistema de gestión
      </div>
      <div style="font-size:1.6rem;font-weight:700;color:#f0f6fc;line-height:1.2;margin-bottom:24px">
        ◆ Control de<br>Facturación Emitida
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login"):
        st.markdown('<p class="lbl">Usuario</p>', unsafe_allow_html=True)
        u = st.text_input("u", label_visibility="collapsed", placeholder="usuario")
        st.markdown('<p class="lbl">Contraseña</p>', unsafe_allow_html=True)
        p = st.text_input("p", type="password", label_visibility="collapsed", placeholder="••••••••")
        ok = st.form_submit_button("Ingresar", type="primary", use_container_width=True)

    if ok:
        user = verificar_login(u, p)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")


# ─────────────────────────────────────────────
#  SECCIÓN 1 — RESUMEN
# ─────────────────────────────────────────────
def pantalla_resumen(user):
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0d1117,#0d1f0d);border:1px solid #21262d;
         border-radius:10px;padding:20px 24px;margin-bottom:20px">
      <div style="font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:#484f58">
        Bienvenido al control de
      </div>
      <div style="font-size:1.4rem;font-weight:700;color:#f0f6fc">
        ◆ Facturación Emitida
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Filtros
    obras_db = ["Todas"] + obtener_obras_sociales_db()
    periodos_db = ["Todos"] + obtener_periodos_db()

    cf1, cf2, cf3 = st.columns([3, 2, 1])
    with cf1:
        st.markdown('<p class="lbl">Obra Social</p>', unsafe_allow_html=True)
        os_sel = st.selectbox("os_r", obras_db, label_visibility="collapsed")
    with cf2:
        st.markdown('<p class="lbl">Período</p>', unsafe_allow_html=True)
        per_sel = st.selectbox("per_r", periodos_db, label_visibility="collapsed")
    with cf3:
        st.markdown('<p class="lbl">Mostrar</p>', unsafe_allow_html=True)
        limit = st.selectbox("lim_r", [5,10,20,0],
            format_func=lambda x: "Todas" if x==0 else str(x),
            label_visibility="collapsed")

    facturas = obtener_facturas(
        obra_social=None if os_sel=="Todas" else os_sel,
        periodo=None if per_sel=="Todos" else per_sel,
        limit=limit if limit else None,
    )

    st.markdown("---")

    if not facturas:
        st.info("No hay facturas importadas. Usá **↑ Importar** para cargar la primera.")
        return

    st.markdown('<div class="section-title">Facturas del Colegio Médico</div>', unsafe_allow_html=True)

    for f in facturas:
        total   = int(f["total_profesionales"] or 0)
        compl   = int(f["completos"] or 0)
        monto   = float(f["monto_total"] or 0)
        nro     = f["nro_factura"] or f"ID-{f['id']}"
        pct     = compl/total if total else 0
        color   = "#238636" if pct==1 else "#388bfd" if pct>0 else "#484f58"
        fecha   = f["fecha_upload"].strftime("%d/%m/%Y") if f["fecha_upload"] else ""

        col_info, col_btn = st.columns([8, 1])
        with col_info:
            st.markdown(f"""
            <div class="fc-card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
                <div>
                  <span style="font-family:'JetBrains Mono';font-size:.9rem;font-weight:600;color:#f0f6fc">
                    {nro}
                  </span>
                  <span style="color:#388bfd;font-size:.85rem;font-weight:600;margin-left:12px">
                    {f['obra_social']}
                  </span>
                  <span style="color:#484f58;font-size:.78rem;margin-left:10px">{f['periodo']}</span>
                </div>
                <div style="text-align:right">
                  <span style="font-family:'JetBrains Mono';font-size:.82rem;color:#3fb950">
                    $ {monto:,.2f}
                  </span>
                  <span style="color:#484f58;font-size:.72rem;display:block">{fecha}</span>
                </div>
              </div>
              <div style="background:#21262d;border-radius:3px;height:4px;overflow:hidden;margin-bottom:4px">
                <div style="background:{color};width:{pct*100:.1f}%;height:100%;border-radius:3px"></div>
              </div>
              <div style="display:flex;justify-content:space-between">
                <span style="font-size:.7rem;color:{color};font-family:'JetBrains Mono'">
                  {compl}/{total} profesionales con comprobante completo
                </span>
                <span style="font-size:.7rem;color:#484f58">{total} profesionales</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
        with col_btn:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("Detalle →", key=f"det_{f['id']}", use_container_width=True):
                st.session_state["factura_sel"] = f["id"]
                st.session_state["pantalla"]    = "detalle"
                st.rerun()


# ─────────────────────────────────────────────
#  SECCIÓN 2 — DETALLE DE FACTURA
# ─────────────────────────────────────────────
def pantalla_detalle(factura_id, user):
    # Cabecera factura
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM facturas WHERE id=%s", (factura_id,))
            fac = cur.fetchone()
    if not fac:
        st.error("Factura no encontrada.")
        return

    # Botón volver
    if st.button("← Volver al resumen"):
        st.session_state["pantalla"] = "resumen"
        st.rerun()

    nro = fac["nro_factura"] or f"ID-{fac['id']}"
    st.markdown(
        f"<h1>◆ {nro} &nbsp;"
        f"<span style='color:#388bfd'>{fac['obra_social']}</span>"
        f"<span style='color:#484f58;font-weight:400;font-size:1rem'> · {fac['periodo']}</span></h1>",
        unsafe_allow_html=True,
    )

    # Métricas + barra global
    filas = obtener_detalle(factura_id)
    total_prof = len(filas)
    compl_prof = sum(1 for r in filas if r["estado"]=="Completo")
    total_monto = sum(float(r["total_cobrar"] or 0) for r in filas)

    m1,m2,m3 = st.columns(3)
    m1.metric("Profesionales", total_prof)
    m2.metric("Total a Cobrar", f"$ {total_monto:,.2f}")
    m3.metric("Comprobantes completos", f"{compl_prof}/{total_prof}")
    barra_progreso(compl_prof, total_prof)
    st.markdown("---")

    if not filas:
        st.info("Esta factura no tiene detalle.")
        return

    st.markdown('<div class="section-title">Profesionales — click para gestionar comprobante</div>',
                unsafe_allow_html=True)

    for linea in filas:
        lid        = linea["id"]
        prof       = linea["profesional"]
        nro_actual = linea["nro_arca"] or ""
        est_actual = linea["estado"]

        with st.expander(
            f"**{prof}** · {linea['matricula']} · "
            f"$ {float(linea['total_cobrar'] or 0):,.2f}  "
            f"{'✓' if est_actual=='Completo' else ''}",
            expanded=(est_actual != "Completo"),
        ):
            # ── Datos del profesional en esta factura ─────────────────
            st.markdown('<div class="section-title">Importes en esta factura</div>', unsafe_allow_html=True)
            dc1,dc2,dc3,dc4 = st.columns(4)
            dc1.metric("Facturado",    f"$ {float(linea['facturado'] or 0):,.2f}")
            dc2.metric("IVA",          f"$ {float(linea['iva'] or 0):,.2f}")
            dc3.metric("Honorarios",   f"$ {float(linea['honorarios'] or 0):,.2f}")
            dc4.metric("Total Cobrar", f"$ {float(linea['total_cobrar'] or 0):,.2f}")

            st.markdown("---")

            # ── Comprobante ARCA de esta factura ──────────────────────
            st.markdown('<div class="section-title">Comprobante del profesional · esta factura</div>',
                        unsafe_allow_html=True)
            ca, cb, cc = st.columns([3, 2, 1])
            with ca:
                st.markdown('<p class="lbl">Número ARCA (A-00000-00000000)</p>', unsafe_allow_html=True)
                nuevo_nro = st.text_input(
                    f"nro_{lid}", value=nro_actual,
                    placeholder="A-00000-00000000",
                    label_visibility="collapsed",
                    key=f"inp_nro_{lid}",
                )
            with cb:
                st.markdown('<p class="lbl">Estado</p>', unsafe_allow_html=True)
                # Auto-completa estado según formato
                if nuevo_nro.strip() and ARCA_RE.match(nuevo_nro.strip()):
                    idx_default = 2  # Completo
                else:
                    opts = ["Pendiente","Solicitada","Completo"]
                    idx_default = opts.index(est_actual) if est_actual in opts else 0
                nuevo_estado = st.selectbox(
                    f"est_{lid}",
                    ["Pendiente","Solicitada","Completo"],
                    index=idx_default,
                    label_visibility="collapsed",
                    key=f"sel_est_{lid}",
                )
                st.markdown(badge(nuevo_estado), unsafe_allow_html=True)
            with cc:
                st.markdown('<p class="lbl">&nbsp;</p>', unsafe_allow_html=True)
                if st.button("Guardar", key=f"save_{lid}", type="primary", use_container_width=True):
                    nro_clean = nuevo_nro.strip()
                    if nro_clean and not ARCA_RE.match(nro_clean):
                        st.error(f"Formato inválido. Debe ser A-00000-00000000")
                    else:
                        upsert_comprobante(lid, nro_clean, nuevo_estado)
                        st.success("Guardado ✓")
                        st.rerun()

            # ── Otras facturas del mismo profesional ──────────────────
            otras = obtener_facturas_de_profesional(prof, excluir_factura_id=factura_id)
            if otras:
                st.markdown("---")
                st.markdown(
                    f'<div class="section-title">Otras facturas del Colegio Médico con movimientos de {prof}</div>',
                    unsafe_allow_html=True,
                )
                for o in otras:
                    o_nro   = o["nro_factura"] or f"ID-{o['id']}"
                    o_color = "#3fb950" if o["estado"]=="Completo" else "#388bfd" if o["estado"]=="Solicitada" else "#f2c94c"
                    st.markdown(f"""
                    <div class="prof-row" style="display:flex;justify-content:space-between;align-items:center">
                      <div>
                        <span style="font-family:'JetBrains Mono';font-size:.82rem;color:#f0f6fc">{o_nro}</span>
                        <span style="color:#8b949e;font-size:.78rem;margin-left:10px">{o['obra_social']}</span>
                        <span style="color:#484f58;font-size:.75rem;margin-left:8px">{o['periodo']}</span>
                      </div>
                      <div style="display:flex;align-items:center;gap:12px">
                        <span style="font-family:'JetBrains Mono';font-size:.78rem;color:#3fb950">
                          $ {float(o['total_cobrar'] or 0):,.2f}
                        </span>
                        <span style="font-family:'JetBrains Mono';font-size:.75rem;color:{o_color}">
                          {o['nro_arca'] or '—'}
                        </span>
                        {badge(o['estado'])}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  IMPORTAR
# ─────────────────────────────────────────────
def pantalla_importar(user):
    st.markdown("<h1>◆ Importar facturación</h1>", unsafe_allow_html=True)
    st.markdown("---")

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<p class="lbl">Número de Factura del Colegio Médico</p>', unsafe_allow_html=True)
        nro_fac = st.text_input("nf", placeholder="FC 00005-00000256", label_visibility="collapsed")
        st.markdown('<p class="lbl">Obra Social</p>', unsafe_allow_html=True)
        os_sel = st.selectbox("os_i", ["— Seleccionar —"]+OBRAS_NOMBRES, label_visibility="collapsed")
        obra_social = obra_cuit = None
        if os_sel != "— Seleccionar —":
            codigo = int(os_sel.split(" - ")[0])
            match  = next((o for o in OBRAS_SOCIALES if o["codigo"]==codigo), None)
            if match:
                obra_social = match["nombre"]
                obra_cuit   = match["cuit"]
                st.markdown(
                    f'<div style="font-family:JetBrains Mono;font-size:.72rem;color:#484f58;margin-top:2px">'
                    f'CUIT {obra_cuit}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<p class="lbl">Período</p>', unsafe_allow_html=True)
        periodo = st.text_input("per_i", placeholder="Ej: Mayo 2026", label_visibility="collapsed")
        st.markdown('<p class="lbl">Archivo Excel</p>', unsafe_allow_html=True)
        archivo = st.file_uploader("xl", type=["xlsx"], label_visibility="collapsed")

        # Auto-detectar período del nombre
        if archivo and not periodo:
            meses = {"enero":"Enero","febrero":"Febrero","marzo":"Marzo","abril":"Abril",
                     "mayo":"Mayo","junio":"Junio","julio":"Julio","agosto":"Agosto",
                     "septiembre":"Septiembre","octubre":"Octubre","noviembre":"Noviembre","diciembre":"Diciembre"}
            for m_en, m_es in meses.items():
                mt = re.search(m_en+r"[_\s-]*(\d{4})", archivo.name.lower())
                if mt:
                    periodo = f"{m_es} {mt.group(1)}"
                    break

    if archivo and obra_social and periodo:
        df = pd.read_excel(archivo)
        st.markdown("---")
        st.markdown(f'<p class="lbl">Vista previa — {len(df)} profesionales · {obra_social} · {periodo}</p>',
                    unsafe_allow_html=True)
        cols_p = [c for c in ["Profesional","Matricula","Facturado","IVA","Total a Cobrar"] if c in df.columns]
        st.dataframe(df[cols_p] if cols_p else df, use_container_width=True, hide_index=True)

        m1,m2,m3 = st.columns(3)
        m1.metric("Profesionales", len(df))
        if "Total a Cobrar" in df.columns:
            m2.metric("Total a Cobrar", f"$ {df['Total a Cobrar'].sum():,.2f}")
        if "Facturado" in df.columns:
            m3.metric("Facturado", f"$ {df['Facturado'].sum():,.2f}")

        if st.button("Confirmar importación", type="primary", use_container_width=True):
            try:
                fid = importar_excel(df, obra_social, periodo, archivo.name, user["username"], obra_cuit, nro_fac)
                st.success(f"✓ Importado correctamente — {len(df)} profesionales (Factura ID {fid})")
                st.session_state["pantalla"] = "resumen"
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback; st.code(traceback.format_exc())
    elif archivo:
        st.caption("Completá Obra Social y Período para continuar.")


# ─────────────────────────────────────────────
#  ADMIN
# ─────────────────────────────────────────────
def pantalla_admin(user):
    if user["rol"] != "admin":
        st.error("Acceso denegado.")
        return
    st.markdown("<h1>◆ Administración</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Crear usuario")
    cu1,cu2,cu3 = st.columns(3)
    with cu1:
        st.markdown('<p class="lbl">Usuario</p>', unsafe_allow_html=True)
        nu = st.text_input("nu", label_visibility="collapsed", placeholder="nombre")
    with cu2:
        st.markdown('<p class="lbl">Contraseña</p>', unsafe_allow_html=True)
        np_ = st.text_input("np", type="password", label_visibility="collapsed", placeholder="••••••••")
    with cu3:
        st.markdown('<p class="lbl">Rol</p>', unsafe_allow_html=True)
        nr = st.selectbox("nr", ["viewer","admin"], label_visibility="collapsed")
    if st.button("Crear usuario", use_container_width=True):
        if nu and np_:
            try:
                crear_usuario(nu, np_, nr)
                st.success(f"Usuario '{nu}' creado.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Completá usuario y contraseña.")
    st.markdown("---")
    st.markdown("### Usuarios existentes")
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT username,rol,created_at FROM usuarios ORDER BY created_at")
            rows = cur.fetchall()
    st.dataframe(pd.DataFrame([dict(r) for r in rows]), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
try:
    init_db()
except Exception as e:
    st.error(f"Error conectando a la base de datos: {e}")
    st.stop()

if "user" not in st.session_state:
    pantalla_login()
    st.stop()

user = st.session_state["user"]
if "pantalla" not in st.session_state:
    st.session_state["pantalla"] = "resumen"

# Sidebar
with st.sidebar:
    st.markdown(f"<div style='color:#484f58;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase'>Sesión</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#f0f6fc;font-weight:600;margin-bottom:16px'>{user['username']} <span style='color:#484f58;font-size:.72rem'>({user['rol']})</span></div>", unsafe_allow_html=True)
    st.markdown("---")

    pantalla_actual = st.session_state["pantalla"]
    if st.button("◆ Resumen", use_container_width=True,
                 type="primary" if pantalla_actual=="resumen" else "secondary"):
        st.session_state["pantalla"] = "resumen"
        st.rerun()
    if st.button("↑ Importar", use_container_width=True,
                 type="primary" if pantalla_actual=="importar" else "secondary"):
        st.session_state["pantalla"] = "importar"
        st.rerun()
    if user["rol"]=="admin":
        if st.button("⚙ Admin", use_container_width=True,
                     type="primary" if pantalla_actual=="admin" else "secondary"):
            st.session_state["pantalla"] = "admin"
            st.rerun()
    st.markdown("---")
    if st.button("Cerrar sesión", use_container_width=True):
        for k in ["user","pantalla","factura_sel"]:
            st.session_state.pop(k, None)
        st.rerun()

# Routing
p = st.session_state["pantalla"]
if p == "resumen":
    pantalla_resumen(user)
elif p == "detalle":
    fid = st.session_state.get("factura_sel")
    if fid:
        pantalla_detalle(fid, user)
    else:
        st.session_state["pantalla"] = "resumen"
        st.rerun()
elif p == "importar":
    pantalla_importar(user)
elif p == "admin":
    pantalla_admin(user)
