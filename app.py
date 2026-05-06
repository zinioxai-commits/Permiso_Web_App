import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import os

# ── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PERMISOLOGÍA",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = os.path.join(os.path.dirname(__file__), "PERMISOLOGIA.db")

ESTADO_OPTIONS = ["EN PROCESO", "OBSERVADO", "EMITIDO", "CANCELADO"]

# ── DB helpers ───────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_df(query, params=()):
    with get_conn() as conn:
        return pd.read_sql_query(query, conn, params=params)

def execute(query, params=()):
    with get_conn() as conn:
        conn.execute(query, params)
        conn.commit()

def get_dorsales():
    df = fetch_df("SELECT DORSAL FROM PROYECTOS ORDER BY DORSAL")
    return df["DORSAL"].tolist() if not df.empty else []

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #1a2332; }
    [data-testid="stSidebar"] * { color: #e8edf3 !important; }
    [data-testid="stSidebar"] .stRadio label { font-size: 0.95rem; }
    .section-header {
        background: linear-gradient(90deg, #1a2332, #2d4a6b);
        color: white !important;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .stDataFrame { border-radius: 8px; overflow: hidden; }
    div[data-testid="stForm"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
    }
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ───────────────────────────────────────────────────────
SECCIONES = {
    "🏗️ Proyectos": "proyectos",
    "🌿 Permisos Ambientales": "ambientales",
    "🏺 Permisos Arqueológicos": "arqueologicos",
    "⚡ Permisos Eléctricos": "electricos",
    "🏛️ Permisos Municipales": "municipales",
    "🛣️ Permisos PROVIAS": "provias",
    "📜 Historial": "historial",
}

with st.sidebar:
    st.markdown("## 📋 PERMISOLOGÍA")
    st.markdown("---")
    seccion = st.radio("Sección", list(SECCIONES.keys()), label_visibility="collapsed")
    st.markdown("---")
    st.caption("Sistema de Gestión de Permisos")

page = SECCIONES[seccion]

# ════════════════════════════════════════════════════════════════════════════
# PROYECTOS
# ════════════════════════════════════════════════════════════════════════════
if page == "proyectos":
    st.markdown('<div class="section-header">🏗️ Proyectos</div>', unsafe_allow_html=True)

    df = fetch_df("SELECT * FROM PROYECTOS ORDER BY DORSAL")
    st.subheader("Registro de proyectos")
    if df.empty:
        st.info("No hay proyectos registrados aún.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("➕ Nuevo Proyecto")
    with st.form("form_proyecto", clear_on_submit=True):
        c1, c2 = st.columns(2)
        dorsal = c1.text_input("DORSAL *", placeholder="Ej: D-001")
        ccpp   = c2.text_input("CCPP / VIAL / SITIO CLARO")
        c3, c4 = st.columns(2)
        resp   = c3.text_input("Responsable")
        metrado = c4.number_input("Metrado (m)", min_value=0.0, step=0.1)
        c5, c6, c7 = st.columns(3)
        postes_p = c5.number_input("Postes Proyectados", min_value=0, step=1)
        postes_e = c6.number_input("Postes Existentes",  min_value=0, step=1)
        canaliz  = c7.number_input("Canalizado (m)",     min_value=0.0, step=0.1)
        submitted = st.form_submit_button("💾 Guardar Proyecto", use_container_width=True)
        if submitted:
            if not dorsal:
                st.error("El campo DORSAL es obligatorio.")
            else:
                try:
                    execute(
                        """INSERT INTO PROYECTOS
                           (DORSAL,CCPP_VIAL_SITIOCLARO,RESPONSABLE,
                            POSTES_PROYECTADOS,POSTES_EXISTENTES,METRADO,CANALIZADO)
                           VALUES (?,?,?,?,?,?,?)""",
                        (dorsal, ccpp, resp, postes_p, postes_e, metrado, canaliz)
                    )
                    st.success(f"✅ Proyecto **{dorsal}** guardado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ════════════════════════════════════════════════════════════════════════════
# PERMISOS AMBIENTALES
# ════════════════════════════════════════════════════════════════════════════
elif page == "ambientales":
    st.markdown('<div class="section-header">🌿 Permisos Ambientales</div>', unsafe_allow_html=True)

    df = fetch_df("SELECT * FROM PERMISOS_AMBIENTALES ORDER BY ID DESC")
    st.subheader("Tabla de Permisos Ambientales")
    if df.empty:
        st.info("Sin registros aún.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("➕ Nuevo Permiso Ambiental")
    dorsales = get_dorsales()
    if not dorsales:
        st.warning("⚠️ Primero debes registrar al menos un **Proyecto**.")
    else:
        with st.form("form_ambiental", clear_on_submit=True):
            c1, c2 = st.columns(2)
            dorsal       = c1.selectbox("DORSAL (Proyecto) *", dorsales)
            tipo_permiso = c2.text_input("Tipo de Permiso")
            c3, c4 = st.columns(2)
            contrata   = c3.text_input("Contrata / Gestor")
            costo      = c4.number_input("Costo Contrata (S/)", min_value=0.0, step=0.01)
            c5, c6 = st.columns(2)
            f_aprox_ing = c5.date_input("Fecha Aprox. Ingreso", value=None)
            f_ingreso   = c6.date_input("Fecha Ingreso Real",   value=None)
            c7, c8 = st.columns(2)
            n_exp       = c7.text_input("N° Expediente")
            f_aprox_em  = c8.date_input("Fecha Aprox. Emisión", value=None)
            c9, c10 = st.columns(2)
            f_emision   = c9.date_input("Fecha Emisión Real",   value=None)
            rd          = c10.text_input("RD")
            c11, c12 = st.columns(2)
            estado      = c11.selectbox("Estado", ESTADO_OPTIONS)
            f_carta     = c12.date_input("Fecha Ingreso Carta Inicio", value=None)
            inf_ambiental = st.text_input("Informe Ambiental")
            submitted = st.form_submit_button("💾 Guardar", use_container_width=True)
            if submitted:
                execute(
                    """INSERT INTO PERMISOS_AMBIENTALES
                       (DORSAL,TIPO_PERMISO,CONTRATA_PERMISO,COSTO_CONTRATA,
                        FECHA_APROXIMADA_INGRESO,FECHA_INGRESO,N_EXPEDIENTE,
                        FECHA_APROXIMADA_EMISION,FECHA_EMISION,RD,ESTADO_PERMISO,
                        FECHA_INGRESO_CARTA_INICIO,INFORME_AMBIENTAL)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (dorsal, tipo_permiso, contrata, costo,
                     str(f_aprox_ing) if f_aprox_ing else None,
                     str(f_ingreso)   if f_ingreso   else None,
                     n_exp,
                     str(f_aprox_em)  if f_aprox_em  else None,
                     str(f_emision)   if f_emision   else None,
                     rd, estado,
                     str(f_carta)     if f_carta     else None,
                     inf_ambiental)
                )
                st.success("✅ Permiso ambiental guardado.")
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# PERMISOS ARQUEOLÓGICOS
# ════════════════════════════════════════════════════════════════════════════
elif page == "arqueologicos":
    st.markdown('<div class="section-header">🏺 Permisos Arqueológicos</div>', unsafe_allow_html=True)

    df = fetch_df("SELECT * FROM PERMISOS_ARQUEOLOGICOS ORDER BY ID DESC")
    st.subheader("Tabla de Permisos Arqueológicos")
    if df.empty:
        st.info("Sin registros aún.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("➕ Nuevo Permiso Arqueológico")
    dorsales = get_dorsales()
    if not dorsales:
        st.warning("⚠️ Primero debes registrar al menos un **Proyecto**.")
    else:
        with st.form("form_arqueologico", clear_on_submit=True):
            c1, c2 = st.columns(2)
            dorsal       = c1.selectbox("DORSAL (Proyecto) *", dorsales)
            tipo_permiso = c2.text_input("Tipo de Permiso")
            c3, c4 = st.columns(2)
            contrata = c3.text_input("Contrata / Gestor")
            costo    = c4.number_input("Costo Contrata (S/)", min_value=0.0, step=0.01)
            c5, c6 = st.columns(2)
            f_aprox_ing = c5.date_input("Fecha Aprox. Ingreso",   value=None)
            f_ingreso   = c6.date_input("Fecha Ingreso Real",     value=None)
            c7, c8 = st.columns(2)
            cargo_ing   = c7.text_input("Cargo Ingreso")
            f_aprox_r   = c8.date_input("Fecha Aprox. Respuesta", value=None)
            c9, c10 = st.columns(2)
            f_rd        = c9.date_input("Fecha RD",   value=None)
            cargo_rd    = c10.text_input("Cargo RD")
            estado = st.selectbox("Estado", ESTADO_OPTIONS)
            submitted = st.form_submit_button("💾 Guardar", use_container_width=True)
            if submitted:
                execute(
                    """INSERT INTO PERMISOS_ARQUEOLOGICOS
                       (DORSAL,TIPO_PERMISO,CONTRATA_PERMISO,COSTO_CONTRATA,
                        FECHA_APROXIMADA_INGRESO,FECHA_INGRESO,CARGO_INGRESO,
                        FECHA_APROXIMADA_RESPUESTA,FECHA_RD,CARGO_RD,ESTADO_PERMISO)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (dorsal, tipo_permiso, contrata, costo,
                     str(f_aprox_ing) if f_aprox_ing else None,
                     str(f_ingreso)   if f_ingreso   else None,
                     cargo_ing,
                     str(f_aprox_r)   if f_aprox_r   else None,
                     str(f_rd)        if f_rd        else None,
                     cargo_rd, estado)
                )
                st.success("✅ Permiso arqueológico guardado.")
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# PERMISOS ELÉCTRICOS
# ════════════════════════════════════════════════════════════════════════════
elif page == "electricos":
    st.markdown('<div class="section-header">⚡ Permisos Eléctricos</div>', unsafe_allow_html=True)

    df = fetch_df("SELECT * FROM PERMISOS_ELECTRICOS ORDER BY ID DESC")
    st.subheader("Tabla de Permisos Eléctricos")
    if df.empty:
        st.info("Sin registros aún.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("➕ Nuevo Permiso Eléctrico")
    dorsales = get_dorsales()
    if not dorsales:
        st.warning("⚠️ Primero debes registrar al menos un **Proyecto**.")
    else:
        with st.form("form_electrico", clear_on_submit=True):
            c1, c2 = st.columns(2)
            dorsal   = c1.selectbox("DORSAL (Proyecto) *", dorsales)
            entidad  = c2.text_input("Entidad Eléctrica")
            c3, c4 = st.columns(2)
            armado   = c3.text_input("Armado Expediente")
            esfuerzo = c4.text_input("Esfuerzo Estructural")
            c5, c6 = st.columns(2)
            contrata_esf = c5.text_input("Contrata Esfuerzo Estructural")
            costo_esf    = c6.number_input("Costo Esfuerzo Estructural (S/)", min_value=0.0, step=0.01)
            c7, c8 = st.columns(2)
            f_ingreso = c7.date_input("Fecha Ingreso Expediente", value=None)
            cargo_exp = c8.text_input("Cargo Expediente")
            c9, c10 = st.columns(2)
            f_aprox_em  = c9.date_input("Fecha Aprox. Emisión",    value=None)
            f_insp_ini  = c10.date_input("Fecha Inicio Inspección", value=None)
            c11, c12 = st.columns(2)
            f_insp_fin  = c11.date_input("Fecha Fin Inspección",      value=None)
            resp_entidad = c12.text_input("Responsable Entidad Inspección")
            c13, c14 = st.columns(2)
            encargado = c13.text_input("Encargado REDSETEL Inspección")
            estado    = c14.selectbox("Estado", ESTADO_OPTIONS)
            submitted = st.form_submit_button("💾 Guardar", use_container_width=True)
            if submitted:
                execute(
                    """INSERT INTO PERMISOS_ELECTRICOS
                       (DORSAL,ENTIDAD_ELECTRICA,ARMADO_EXP,ESFUERZO_ESTRUCTURAL,
                        CONTRATA_ESFUERZO_ESTRUCTURAL,COSTO_ESFUERZO_ESTRUCTURAL,
                        FECHA_INGRESO_EXP,CARGO_EXP,FECHA_APROXIMADO_EMISION,
                        FECHA_INSPECCION_INICIO,FECHA_INSPECCION_FIN,
                        RESPONSABLE_ENTIDAD_INSPECCION,ENCARGADO_REDSETEL_INSPECCION,
                        ESTADO_PERMISO)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (dorsal, entidad, armado, esfuerzo, contrata_esf, costo_esf,
                     str(f_ingreso)   if f_ingreso   else None,
                     cargo_exp,
                     str(f_aprox_em)  if f_aprox_em  else None,
                     str(f_insp_ini)  if f_insp_ini  else None,
                     str(f_insp_fin)  if f_insp_fin  else None,
                     resp_entidad, encargado, estado)
                )
                st.success("✅ Permiso eléctrico guardado.")
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# PERMISOS MUNICIPALES
# ════════════════════════════════════════════════════════════════════════════
elif page == "municipales":
    st.markdown('<div class="section-header">🏛️ Permisos Municipales</div>', unsafe_allow_html=True)

    df = fetch_df("SELECT * FROM PERMISOS_MUNICIPALES ORDER BY ID DESC")
    st.subheader("Tabla de Permisos Municipales")
    if df.empty:
        st.info("Sin registros aún.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("➕ Nuevo Permiso Municipal")
    dorsales = get_dorsales()
    if not dorsales:
        st.warning("⚠️ Primero debes registrar al menos un **Proyecto**.")
    else:
        with st.form("form_municipal", clear_on_submit=True):
            c1, c2 = st.columns(2)
            dorsal    = c1.selectbox("DORSAL (Proyecto) *", dorsales)
            armado    = c2.text_input("Armado Expediente")
            c3, c4 = st.columns(2)
            costo_arm = c3.number_input("Costo Armado Exp. (S/)", min_value=0.0, step=0.01)
            f_ingreso = c4.date_input("Fecha Ingreso Exp.", value=None)
            c5, c6 = st.columns(2)
            cargo_exp = c5.text_input("Cargo Expediente")
            pago_cargo = c6.number_input("Pago Cargo Exp. (S/)", min_value=0.0, step=0.01)
            c7, c8 = st.columns(2)
            f_aprox_em = c7.date_input("Fecha Aprox. Emisión", value=None)
            f_emision  = c8.date_input("Fecha Emisión Real",   value=None)
            c9, c10 = st.columns(2)
            contacto_nombre = c9.text_input("Contacto - Nombre")
            contacto_numero = c10.text_input("Contacto - Número")
            estado = st.selectbox("Estado", ESTADO_OPTIONS)
            submitted = st.form_submit_button("💾 Guardar", use_container_width=True)
            if submitted:
                execute(
                    """INSERT INTO PERMISOS_MUNICIPALES
                       (DORSAL,ARMADO_EXP,COSTO_ARMADO_EXP,FECHA_INGRESO_EXP,
                        CARGO_EXP,PAGO_CARGO_EXP,FECHA_APROXIMADA_EMISION,
                        FECHA_EMISION,CONTACTO_NOMBRE,CONTACTO_NUMERO,ESTADO_PERMISO)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (dorsal, armado, costo_arm,
                     str(f_ingreso)   if f_ingreso   else None,
                     cargo_exp, pago_cargo,
                     str(f_aprox_em)  if f_aprox_em  else None,
                     str(f_emision)   if f_emision   else None,
                     contacto_nombre, contacto_numero, estado)
                )
                st.success("✅ Permiso municipal guardado.")
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# PERMISOS PROVIAS
# ════════════════════════════════════════════════════════════════════════════
elif page == "provias":
    st.markdown('<div class="section-header">🛣️ Permisos PROVIAS</div>', unsafe_allow_html=True)

    df = fetch_df("SELECT * FROM PERMISOS_PROVIAS ORDER BY ID DESC")
    st.subheader("Tabla de Permisos PROVIAS")
    if df.empty:
        st.info("Sin registros aún.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("➕ Nuevo Permiso PROVIAS")
    dorsales = get_dorsales()
    if not dorsales:
        st.warning("⚠️ Primero debes registrar al menos un **Proyecto**.")
    else:
        with st.form("form_provias", clear_on_submit=True):
            c1, c2 = st.columns(2)
            dorsal   = c1.selectbox("DORSAL (Proyecto) *", dorsales)
            tipo_p   = c2.text_input("Tipo de Permiso")
            c3, c4 = st.columns(2)
            contrata = c3.text_input("Contrata / Gestor")
            costo    = c4.number_input("Costo Contrata (S/)", min_value=0.0, step=0.01)
            c5, c6 = st.columns(2)
            f_aprox_ing = c5.date_input("Fecha Aprox. Ingreso", value=None)
            f_ingreso   = c6.date_input("Fecha Ingreso Real",   value=None)
            c7, c8 = st.columns(2)
            cargo_ing   = c7.text_input("Cargo Ingreso")
            f_aprox_rd  = c8.date_input("Fecha Aprox. RD",      value=None)
            c9, c10 = st.columns(2)
            f_rd      = c9.date_input("Fecha RD",   value=None)
            cargo_rd  = c10.text_input("Cargo RD")
            estado = st.selectbox("Estado", ESTADO_OPTIONS)
            submitted = st.form_submit_button("💾 Guardar", use_container_width=True)
            if submitted:
                execute(
                    """INSERT INTO PERMISOS_PROVIAS
                       (DORSAL,TIPO_PERMISOS,CONTRATA_PERMISOS,COSTO_CONTRATA,
                        FECHA_APROXIMADA_INGRESO,FECHA_INGRESO,CARGO_INGRESO,
                        FECHA_APROXIMADA_RD,FECHA_RD,CARGO_RD,ESTADO_PERMISO)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (dorsal, tipo_p, contrata, costo,
                     str(f_aprox_ing) if f_aprox_ing else None,
                     str(f_ingreso)   if f_ingreso   else None,
                     cargo_ing,
                     str(f_aprox_rd)  if f_aprox_rd  else None,
                     str(f_rd)        if f_rd        else None,
                     cargo_rd, estado)
                )
                st.success("✅ Permiso PROVIAS guardado.")
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# HISTORIAL
# ════════════════════════════════════════════════════════════════════════════
elif page == "historial":
    st.markdown('<div class="section-header">📜 Historial de Permisos</div>', unsafe_allow_html=True)

    df = fetch_df("SELECT * FROM HISTORIAL_PERMISOS ORDER BY FECHA_REGISTRO DESC")
    st.subheader("Registro de Historial")
    if df.empty:
        st.info("Sin registros aún.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("➕ Nuevo Registro de Historial")
    dorsales = get_dorsales()
    if not dorsales:
        st.warning("⚠️ Primero debes registrar al menos un **Proyecto**.")
    else:
        with st.form("form_historial", clear_on_submit=True):
            c1, c2 = st.columns(2)
            proyecto = c1.selectbox("Proyecto (DORSAL) *", dorsales)
            ccpp     = c2.text_input("CCPP / Vial / Sitio Claro")
            fecha_reg = st.date_input("Fecha Registro", value=date.today())
            comentario = st.text_area("Comentario", height=100)
            submitted = st.form_submit_button("💾 Guardar", use_container_width=True)
            if submitted:
                execute(
                    """INSERT INTO HISTORIAL_PERMISOS
                       (PROYECTO,CCPP_VIAL_SITIOCLARO,FECHA_REGISTRO,COMENTARIO)
                       VALUES (?,?,?,?)""",
                    (proyecto, ccpp, str(fecha_reg), comentario)
                )
                st.success("✅ Historial guardado.")
                st.rerun()
