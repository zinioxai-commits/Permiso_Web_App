import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os

# ── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PERMISOLOGÍA",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = os.path.join(os.path.dirname(__file__), "PERMISOLOGIA.db")
ESTADO_OPTIONS = ["EN PROCESO", "OBSERVADO", "EMITIDO", "CANCELADO"]

# ── DB helpers ────────────────────────────────────────────────────────────────
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

def get_proyectos():
    df = fetch_df("SELECT DORSAL, CCPP_VIAL_SITIOCLARO FROM PROYECTOS ORDER BY DORSAL")
    if df.empty:
        return [], {}
    mapping = dict(zip(df["DORSAL"], df["CCPP_VIAL_SITIOCLARO"].fillna("")))
    return df["DORSAL"].tolist(), mapping

def safe_date(val):
    if val and str(val) not in ("None", ""):
        try:
            return date.fromisoformat(str(val)[:10])
        except Exception:
            pass
    return None

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #1a2332; }
    [data-testid="stSidebar"] * { color: #e8edf3 !important; }
    .section-header {
        background: linear-gradient(90deg, #1a2332, #2d4a6b);
        color: white !important;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 1.1rem;
        font-weight: 600;
    }
    div[data-testid="stForm"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
    }
    .edit-header {
        background: #fff7ed;
        border-left: 4px solid #f97316;
        padding: 0.5rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
SECCIONES = {
    "🏗️ Proyectos":              "proyectos",
    "🌿 Permisos Ambientales":   "ambientales",
    "🏺 Permisos Arqueológicos": "arqueologicos",
    "⚡ Permisos Eléctricos":    "electricos",
    "🏛️ Permisos Municipales":   "municipales",
    "🛣️ Permisos PROVIAS":       "provias",
    "📜 Historial":              "historial",
}

with st.sidebar:
    st.markdown("## 📋 PERMISOLOGÍA")
    st.markdown("---")
    seccion = st.radio("Sección", list(SECCIONES.keys()), label_visibility="collapsed")
    st.markdown("---")
    st.caption("Sistema de Gestión de Permisos")

page = SECCIONES[seccion]

# ── Shared filter bar ─────────────────────────────────────────────────────────
def filter_bar(df, key_prefix):
    if df.empty:
        return df
    c1, c2 = st.columns(2)
    dorsal_col = "DORSAL" if "DORSAL" in df.columns else None
    ccpp_col   = "CCPP_VIAL_SITIOCLARO" if "CCPP_VIAL_SITIOCLARO" in df.columns else None

    sel_d = sel_cc = "Todos"
    if dorsal_col:
        d_opts = ["Todos"] + sorted(df[dorsal_col].dropna().unique().tolist())
        sel_d  = c1.selectbox("Filtrar por DORSAL", d_opts, key=f"{key_prefix}_fd")
    if ccpp_col:
        cc_opts = ["Todos"] + sorted(df[ccpp_col].dropna().replace("", float("nan")).dropna().unique().tolist())
        sel_cc  = c2.selectbox("Filtrar por CCPP / Vial / Sitio Claro", cc_opts, key=f"{key_prefix}_fcc")

    if sel_d  != "Todos" and dorsal_col: df = df[df[dorsal_col] == sel_d]
    if sel_cc != "Todos" and ccpp_col:   df = df[df[ccpp_col]   == sel_cc]
    return df

# ── Row selector for edit ─────────────────────────────────────────────────────
def row_selector(df, id_col, key):
    opts = {}
    for _, row in df.iterrows():
        dorsal = row.get("DORSAL", "?")
        ccpp   = row.get("CCPP_VIAL_SITIOCLARO", "") or ""
        label  = f"ID {row[id_col]}  —  {dorsal}  |  {ccpp}"
        opts[label] = row[id_col]
    choice = st.selectbox("Selecciona registro para editar / eliminar",
                          ["— Selecciona —"] + list(opts.keys()), key=key)
    return None if choice == "— Selecciona —" else opts[choice]


# ════════════════════════════════════════════════════════════════════════════
# PROYECTOS
# ════════════════════════════════════════════════════════════════════════════
if page == "proyectos":
    st.markdown('<div class="section-header">🏗️ Proyectos</div>', unsafe_allow_html=True)

    df_all  = fetch_df("SELECT * FROM PROYECTOS ORDER BY DORSAL")
    df_view = filter_bar(df_all.copy(), "proy") if not df_all.empty else df_all

    st.subheader("Registro de Proyectos")
    if not df_view.empty:
        st.dataframe(df_view, use_container_width=True, hide_index=True)
    else:
        st.info("Sin proyectos registrados.")

    st.markdown("---")
    tab_new, tab_edit = st.tabs(["➕ Nuevo Proyecto", "✏️ Editar / Eliminar"])

    with tab_new:
        with st.form("form_proyecto", clear_on_submit=True):
            c1, c2 = st.columns(2)
            dorsal  = c1.text_input("DORSAL *", placeholder="Ej: D-001")
            ccpp    = c2.text_input("CCPP / Vial / Sitio Claro")
            c3, c4  = st.columns(2)
            resp    = c3.text_input("Responsable")
            metrado = c4.number_input("Metrado (m)", min_value=0.0, step=0.1)
            c5, c6, c7 = st.columns(3)
            postes_p = c5.number_input("Postes Proyectados", min_value=0, step=1)
            postes_e = c6.number_input("Postes Existentes",  min_value=0, step=1)
            canaliz  = c7.number_input("Canalizado (m)",     min_value=0.0, step=0.1)
            if st.form_submit_button("💾 Guardar Proyecto", use_container_width=True):
                if not dorsal:
                    st.error("El campo DORSAL es obligatorio.")
                else:
                    try:
                        execute(
                            "INSERT INTO PROYECTOS (DORSAL,CCPP_VIAL_SITIOCLARO,RESPONSABLE,POSTES_PROYECTADOS,POSTES_EXISTENTES,METRADO,CANALIZADO) VALUES (?,?,?,?,?,?,?)",
                            (dorsal, ccpp, resp, postes_p, postes_e, metrado, canaliz)
                        )
                        st.success(f"✅ Proyecto **{dorsal}** guardado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab_edit:
        if df_all.empty:
            st.info("Sin proyectos para editar.")
        else:
            opts = {f"{r['DORSAL']}  —  {r['CCPP_VIAL_SITIOCLARO'] or ''}": r["DORSAL"] for _, r in df_all.iterrows()}
            choice = st.selectbox("Selecciona proyecto", ["— Selecciona —"] + list(opts.keys()), key="proy_edit_sel")
            if choice != "— Selecciona —":
                sel_d = opts[choice]
                row = df_all[df_all["DORSAL"] == sel_d].iloc[0]
                st.markdown('<div class="edit-header">✏️ Editando proyecto</div>', unsafe_allow_html=True)
                with st.form("form_edit_proyecto"):
                    c1, c2 = st.columns(2)
                    new_ccpp    = c1.text_input("CCPP / Vial / Sitio Claro", value=row["CCPP_VIAL_SITIOCLARO"] or "")
                    new_resp    = c2.text_input("Responsable",               value=row["RESPONSABLE"] or "")
                    c3, c4      = st.columns(2)
                    new_metrado = c3.number_input("Metrado (m)",    value=float(row["METRADO"] or 0),   step=0.1)
                    new_canal   = c4.number_input("Canalizado (m)", value=float(row["CANALIZADO"] or 0), step=0.1)
                    c5, c6      = st.columns(2)
                    new_pp = c5.number_input("Postes Proyectados", value=int(row["POSTES_PROYECTADOS"] or 0), step=1)
                    new_pe = c6.number_input("Postes Existentes",  value=int(row["POSTES_EXISTENTES"] or 0),  step=1)
                    cs, cd = st.columns(2)
                    if cs.form_submit_button("💾 Guardar cambios", use_container_width=True):
                        execute(
                            "UPDATE PROYECTOS SET CCPP_VIAL_SITIOCLARO=?,RESPONSABLE=?,POSTES_PROYECTADOS=?,POSTES_EXISTENTES=?,METRADO=?,CANALIZADO=? WHERE DORSAL=?",
                            (new_ccpp, new_resp, new_pp, new_pe, new_metrado, new_canal, sel_d)
                        )
                        st.success("✅ Proyecto actualizado.")
                        st.rerun()
                    if cd.form_submit_button("🗑️ Eliminar proyecto", use_container_width=True):
                        execute("DELETE FROM PROYECTOS WHERE DORSAL=?", (sel_d,))
                        st.success(f"Proyecto {sel_d} eliminado.")
                        st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# GENERIC PERMIT PAGE
# ════════════════════════════════════════════════════════════════════════════
def permit_page(title, table, fields_fn, insert_fn, update_fn):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

    dorsales, dorsal_to_ccpp = get_proyectos()
    df_all  = fetch_df(f"SELECT * FROM {table} ORDER BY ID DESC")
    df_view = filter_bar(df_all.copy(), table.lower()) if not df_all.empty else df_all

    st.subheader("Registros")
    if not df_view.empty:
        st.dataframe(df_view, use_container_width=True, hide_index=True)
    else:
        st.info("Sin registros para el filtro seleccionado.")

    st.markdown("---")
    if not dorsales:
        st.warning("⚠️ Primero registra un **Proyecto** en la sección correspondiente.")
        return

    tab_new, tab_edit = st.tabs(["➕ Nuevo registro", "✏️ Editar / Eliminar"])

    with tab_new:
        with st.form(f"form_new_{table}", clear_on_submit=True):
            c1, c2   = st.columns(2)
            dorsal   = c1.selectbox("DORSAL *", dorsales, key=f"new_d_{table}")
            ccpp_auto = dorsal_to_ccpp.get(dorsal, "")
            c2.text_input("CCPP / Vial / Sitio Claro (auto)", value=ccpp_auto, disabled=True)
            fields = fields_fn(f"new_{table}", {})
            if st.form_submit_button("💾 Guardar", use_container_width=True):
                insert_fn(fields, dorsal, ccpp_auto)
                st.success("✅ Registro guardado.")
                st.rerun()

    with tab_edit:
        if df_all.empty:
            st.info("Sin registros para editar.")
            return
        sel_id = row_selector(df_all, "ID", key=f"edit_sel_{table}")
        if sel_id is not None:
            row = df_all[df_all["ID"] == sel_id].iloc[0].to_dict()
            row_dorsal = row.get("DORSAL", dorsales[0])
            row_ccpp   = row.get("CCPP_VIAL_SITIOCLARO", "") or ""
            st.markdown('<div class="edit-header">✏️ Editando registro</div>', unsafe_allow_html=True)
            with st.form(f"form_edit_{table}_{sel_id}"):
                c1, c2     = st.columns(2)
                d_idx      = dorsales.index(row_dorsal) if row_dorsal in dorsales else 0
                new_dorsal = c1.selectbox("DORSAL", dorsales, index=d_idx, key=f"edit_d_{table}")
                new_ccpp   = c2.text_input("CCPP / Vial / Sitio Claro", value=row_ccpp, key=f"edit_cc_{table}")
                fields = fields_fn(f"edit_{table}_{sel_id}", row)
                cs, cd = st.columns(2)
                if cs.form_submit_button("💾 Guardar cambios", use_container_width=True):
                    fields["DORSAL"]               = new_dorsal
                    fields["CCPP_VIAL_SITIOCLARO"] = new_ccpp
                    update_fn(fields, sel_id)
                    st.success("✅ Registro actualizado.")
                    st.rerun()
                if cd.form_submit_button("🗑️ Eliminar", use_container_width=True):
                    execute(f"DELETE FROM {table} WHERE ID=?", (sel_id,))
                    st.success("Registro eliminado.")
                    st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# FIELD DEFINITIONS PER TABLE
# ════════════════════════════════════════════════════════════════════════════

# ── AMBIENTALES ──────────────────────────────────────────────────────────────
def amb_fields(pfx, d):
    r = {}
    c1,c2 = st.columns(2)
    r["TIPO_PERMISO"]               = c1.text_input("Tipo de Permiso",    value=d.get("TIPO_PERMISO","") or "",       key=f"{pfx}_tp")
    r["CONTRATA_PERMISO"]           = c2.text_input("Contrata / Gestor",  value=d.get("CONTRATA_PERMISO","") or "",   key=f"{pfx}_cp")
    c3,c4 = st.columns(2)
    r["COSTO_CONTRATA"]             = c3.number_input("Costo Contrata (S/)", value=float(d.get("COSTO_CONTRATA") or 0), step=0.01, key=f"{pfx}_cc")
    r["N_EXPEDIENTE"]               = c4.text_input("N° Expediente",      value=d.get("N_EXPEDIENTE","") or "",       key=f"{pfx}_ne")
    c5,c6 = st.columns(2)
    r["FECHA_APROXIMADA_INGRESO"]   = str(c5.date_input("Fecha Aprox. Ingreso",  value=safe_date(d.get("FECHA_APROXIMADA_INGRESO")), key=f"{pfx}_fai") or "")
    r["FECHA_INGRESO"]              = str(c6.date_input("Fecha Ingreso Real",    value=safe_date(d.get("FECHA_INGRESO")),            key=f"{pfx}_fi")  or "")
    c7,c8 = st.columns(2)
    r["FECHA_APROXIMADA_EMISION"]   = str(c7.date_input("Fecha Aprox. Emisión",  value=safe_date(d.get("FECHA_APROXIMADA_EMISION")), key=f"{pfx}_fae") or "")
    r["FECHA_EMISION"]              = str(c8.date_input("Fecha Emisión Real",    value=safe_date(d.get("FECHA_EMISION")),            key=f"{pfx}_fe")  or "")
    c9,c10 = st.columns(2)
    r["RD"]                         = c9.text_input("RD",                 value=d.get("RD","") or "",                 key=f"{pfx}_rd")
    idx = ESTADO_OPTIONS.index(d["ESTADO_PERMISO"]) if d.get("ESTADO_PERMISO") in ESTADO_OPTIONS else 0
    r["ESTADO_PERMISO"]             = c10.selectbox("Estado", ESTADO_OPTIONS, index=idx, key=f"{pfx}_ep")
    c11,c12 = st.columns(2)
    r["FECHA_INGRESO_CARTA_INICIO"] = str(c11.date_input("Fecha Carta Inicio", value=safe_date(d.get("FECHA_INGRESO_CARTA_INICIO")), key=f"{pfx}_fic") or "")
    r["INFORME_AMBIENTAL"]          = c12.text_input("Informe Ambiental", value=d.get("INFORME_AMBIENTAL","") or "",  key=f"{pfx}_ia")
    return r

def amb_insert(f, dorsal, ccpp):
    execute("""INSERT INTO PERMISOS_AMBIENTALES
        (DORSAL,CCPP_VIAL_SITIOCLARO,TIPO_PERMISO,CONTRATA_PERMISO,COSTO_CONTRATA,
         FECHA_APROXIMADA_INGRESO,FECHA_INGRESO,N_EXPEDIENTE,FECHA_APROXIMADA_EMISION,
         FECHA_EMISION,RD,ESTADO_PERMISO,FECHA_INGRESO_CARTA_INICIO,INFORME_AMBIENTAL)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (dorsal,ccpp,f["TIPO_PERMISO"],f["CONTRATA_PERMISO"],f["COSTO_CONTRATA"],
         f["FECHA_APROXIMADA_INGRESO"],f["FECHA_INGRESO"],f["N_EXPEDIENTE"],
         f["FECHA_APROXIMADA_EMISION"],f["FECHA_EMISION"],f["RD"],f["ESTADO_PERMISO"],
         f["FECHA_INGRESO_CARTA_INICIO"],f["INFORME_AMBIENTAL"]))

def amb_update(f, rid):
    execute("""UPDATE PERMISOS_AMBIENTALES SET
        DORSAL=?,CCPP_VIAL_SITIOCLARO=?,TIPO_PERMISO=?,CONTRATA_PERMISO=?,COSTO_CONTRATA=?,
        FECHA_APROXIMADA_INGRESO=?,FECHA_INGRESO=?,N_EXPEDIENTE=?,FECHA_APROXIMADA_EMISION=?,
        FECHA_EMISION=?,RD=?,ESTADO_PERMISO=?,FECHA_INGRESO_CARTA_INICIO=?,INFORME_AMBIENTAL=?
        WHERE ID=?""",
        (f["DORSAL"],f["CCPP_VIAL_SITIOCLARO"],f["TIPO_PERMISO"],f["CONTRATA_PERMISO"],f["COSTO_CONTRATA"],
         f["FECHA_APROXIMADA_INGRESO"],f["FECHA_INGRESO"],f["N_EXPEDIENTE"],
         f["FECHA_APROXIMADA_EMISION"],f["FECHA_EMISION"],f["RD"],f["ESTADO_PERMISO"],
         f["FECHA_INGRESO_CARTA_INICIO"],f["INFORME_AMBIENTAL"],rid))

# ── ARQUEOLÓGICOS ─────────────────────────────────────────────────────────────
def arq_fields(pfx, d):
    r = {}
    c1,c2 = st.columns(2)
    r["TIPO_PERMISO"]              = c1.text_input("Tipo de Permiso",    value=d.get("TIPO_PERMISO","") or "",    key=f"{pfx}_tp")
    r["CONTRATA_PERMISO"]          = c2.text_input("Contrata / Gestor",  value=d.get("CONTRATA_PERMISO","") or "",key=f"{pfx}_cp")
    c3,c4 = st.columns(2)
    r["COSTO_CONTRATA"]            = c3.number_input("Costo Contrata (S/)", value=float(d.get("COSTO_CONTRATA") or 0), step=0.01, key=f"{pfx}_cc")
    r["CARGO_INGRESO"]             = c4.text_input("Cargo Ingreso",      value=d.get("CARGO_INGRESO","") or "",   key=f"{pfx}_ci")
    c5,c6 = st.columns(2)
    r["FECHA_APROXIMADA_INGRESO"]  = str(c5.date_input("Fecha Aprox. Ingreso",    value=safe_date(d.get("FECHA_APROXIMADA_INGRESO")),  key=f"{pfx}_fai") or "")
    r["FECHA_INGRESO"]             = str(c6.date_input("Fecha Ingreso Real",      value=safe_date(d.get("FECHA_INGRESO")),             key=f"{pfx}_fi")  or "")
    c7,c8 = st.columns(2)
    r["FECHA_APROXIMADA_RESPUESTA"]= str(c7.date_input("Fecha Aprox. Respuesta",  value=safe_date(d.get("FECHA_APROXIMADA_RESPUESTA")),key=f"{pfx}_far") or "")
    r["FECHA_RD"]                  = str(c8.date_input("Fecha RD",                value=safe_date(d.get("FECHA_RD")),                  key=f"{pfx}_frd") or "")
    c9,c10 = st.columns(2)
    r["CARGO_RD"]                  = c9.text_input("Cargo RD", value=d.get("CARGO_RD","") or "", key=f"{pfx}_crd")
    idx = ESTADO_OPTIONS.index(d["ESTADO_PERMISO"]) if d.get("ESTADO_PERMISO") in ESTADO_OPTIONS else 0
    r["ESTADO_PERMISO"]            = c10.selectbox("Estado", ESTADO_OPTIONS, index=idx, key=f"{pfx}_ep")
    return r

def arq_insert(f, dorsal, ccpp):
    execute("""INSERT INTO PERMISOS_ARQUEOLOGICOS
        (DORSAL,CCPP_VIAL_SITIOCLARO,TIPO_PERMISO,CONTRATA_PERMISO,COSTO_CONTRATA,
         FECHA_APROXIMADA_INGRESO,FECHA_INGRESO,CARGO_INGRESO,
         FECHA_APROXIMADA_RESPUESTA,FECHA_RD,CARGO_RD,ESTADO_PERMISO)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (dorsal,ccpp,f["TIPO_PERMISO"],f["CONTRATA_PERMISO"],f["COSTO_CONTRATA"],
         f["FECHA_APROXIMADA_INGRESO"],f["FECHA_INGRESO"],f["CARGO_INGRESO"],
         f["FECHA_APROXIMADA_RESPUESTA"],f["FECHA_RD"],f["CARGO_RD"],f["ESTADO_PERMISO"]))

def arq_update(f, rid):
    execute("""UPDATE PERMISOS_ARQUEOLOGICOS SET
        DORSAL=?,CCPP_VIAL_SITIOCLARO=?,TIPO_PERMISO=?,CONTRATA_PERMISO=?,COSTO_CONTRATA=?,
        FECHA_APROXIMADA_INGRESO=?,FECHA_INGRESO=?,CARGO_INGRESO=?,
        FECHA_APROXIMADA_RESPUESTA=?,FECHA_RD=?,CARGO_RD=?,ESTADO_PERMISO=? WHERE ID=?""",
        (f["DORSAL"],f["CCPP_VIAL_SITIOCLARO"],f["TIPO_PERMISO"],f["CONTRATA_PERMISO"],f["COSTO_CONTRATA"],
         f["FECHA_APROXIMADA_INGRESO"],f["FECHA_INGRESO"],f["CARGO_INGRESO"],
         f["FECHA_APROXIMADA_RESPUESTA"],f["FECHA_RD"],f["CARGO_RD"],f["ESTADO_PERMISO"],rid))

# ── ELÉCTRICOS ────────────────────────────────────────────────────────────────
def elec_fields(pfx, d):
    r = {}
    c1,c2 = st.columns(2)
    r["ENTIDAD_ELECTRICA"]              = c1.text_input("Entidad Eléctrica",        value=d.get("ENTIDAD_ELECTRICA","") or "",             key=f"{pfx}_ee")
    r["ARMADO_EXP"]                     = c2.text_input("Armado Expediente",        value=d.get("ARMADO_EXP","") or "",                    key=f"{pfx}_ae")
    c3,c4 = st.columns(2)
    r["ESFUERZO_ESTRUCTURAL"]           = c3.text_input("Esfuerzo Estructural",     value=d.get("ESFUERZO_ESTRUCTURAL","") or "",           key=f"{pfx}_esf")
    r["CONTRATA_ESFUERZO_ESTRUCTURAL"]  = c4.text_input("Contrata Esfuerzo Est.",  value=d.get("CONTRATA_ESFUERZO_ESTRUCTURAL","") or "",  key=f"{pfx}_cee")
    c5,c6 = st.columns(2)
    r["COSTO_ESFUERZO_ESTRUCTURAL"]     = c5.number_input("Costo Esfuerzo Est. (S/)", value=float(d.get("COSTO_ESFUERZO_ESTRUCTURAL") or 0), step=0.01, key=f"{pfx}_cost")
    r["CARGO_EXP"]                      = c6.text_input("Cargo Expediente",         value=d.get("CARGO_EXP","") or "",                     key=f"{pfx}_cexp")
    c7,c8 = st.columns(2)
    r["FECHA_INGRESO_EXP"]              = str(c7.date_input("Fecha Ingreso Exp.",        value=safe_date(d.get("FECHA_INGRESO_EXP")),        key=f"{pfx}_fie")  or "")
    r["FECHA_APROXIMADO_EMISION"]       = str(c8.date_input("Fecha Aprox. Emisión",      value=safe_date(d.get("FECHA_APROXIMADO_EMISION")), key=f"{pfx}_fae")  or "")
    c9,c10 = st.columns(2)
    r["FECHA_INSPECCION_INICIO"]        = str(c9.date_input("Fecha Inicio Inspección",   value=safe_date(d.get("FECHA_INSPECCION_INICIO")),  key=f"{pfx}_fii")  or "")
    r["FECHA_INSPECCION_FIN"]           = str(c10.date_input("Fecha Fin Inspección",     value=safe_date(d.get("FECHA_INSPECCION_FIN")),     key=f"{pfx}_fif")  or "")
    c11,c12 = st.columns(2)
    r["RESPONSABLE_ENTIDAD_INSPECCION"] = c11.text_input("Resp. Entidad Insp.", value=d.get("RESPONSABLE_ENTIDAD_INSPECCION","") or "",  key=f"{pfx}_rei")
    r["ENCARGADO_REDSETEL_INSPECCION"]  = c12.text_input("Encargado REDSETEL", value=d.get("ENCARGADO_REDSETEL_INSPECCION","") or "",   key=f"{pfx}_eri")
    idx = ESTADO_OPTIONS.index(d["ESTADO_PERMISO"]) if d.get("ESTADO_PERMISO") in ESTADO_OPTIONS else 0
    r["ESTADO_PERMISO"]                 = st.selectbox("Estado", ESTADO_OPTIONS, index=idx, key=f"{pfx}_ep")
    return r

def elec_insert(f, dorsal, ccpp):
    execute("""INSERT INTO PERMISOS_ELECTRICOS
        (DORSAL,CCPP_VIAL_SITIOCLARO,ENTIDAD_ELECTRICA,ARMADO_EXP,ESFUERZO_ESTRUCTURAL,
         CONTRATA_ESFUERZO_ESTRUCTURAL,COSTO_ESFUERZO_ESTRUCTURAL,FECHA_INGRESO_EXP,CARGO_EXP,
         FECHA_APROXIMADO_EMISION,FECHA_INSPECCION_INICIO,FECHA_INSPECCION_FIN,
         RESPONSABLE_ENTIDAD_INSPECCION,ENCARGADO_REDSETEL_INSPECCION,ESTADO_PERMISO)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (dorsal,ccpp,f["ENTIDAD_ELECTRICA"],f["ARMADO_EXP"],f["ESFUERZO_ESTRUCTURAL"],
         f["CONTRATA_ESFUERZO_ESTRUCTURAL"],f["COSTO_ESFUERZO_ESTRUCTURAL"],f["FECHA_INGRESO_EXP"],f["CARGO_EXP"],
         f["FECHA_APROXIMADO_EMISION"],f["FECHA_INSPECCION_INICIO"],f["FECHA_INSPECCION_FIN"],
         f["RESPONSABLE_ENTIDAD_INSPECCION"],f["ENCARGADO_REDSETEL_INSPECCION"],f["ESTADO_PERMISO"]))

def elec_update(f, rid):
    execute("""UPDATE PERMISOS_ELECTRICOS SET
        DORSAL=?,CCPP_VIAL_SITIOCLARO=?,ENTIDAD_ELECTRICA=?,ARMADO_EXP=?,ESFUERZO_ESTRUCTURAL=?,
        CONTRATA_ESFUERZO_ESTRUCTURAL=?,COSTO_ESFUERZO_ESTRUCTURAL=?,FECHA_INGRESO_EXP=?,CARGO_EXP=?,
        FECHA_APROXIMADO_EMISION=?,FECHA_INSPECCION_INICIO=?,FECHA_INSPECCION_FIN=?,
        RESPONSABLE_ENTIDAD_INSPECCION=?,ENCARGADO_REDSETEL_INSPECCION=?,ESTADO_PERMISO=? WHERE ID=?""",
        (f["DORSAL"],f["CCPP_VIAL_SITIOCLARO"],f["ENTIDAD_ELECTRICA"],f["ARMADO_EXP"],f["ESFUERZO_ESTRUCTURAL"],
         f["CONTRATA_ESFUERZO_ESTRUCTURAL"],f["COSTO_ESFUERZO_ESTRUCTURAL"],f["FECHA_INGRESO_EXP"],f["CARGO_EXP"],
         f["FECHA_APROXIMADO_EMISION"],f["FECHA_INSPECCION_INICIO"],f["FECHA_INSPECCION_FIN"],
         f["RESPONSABLE_ENTIDAD_INSPECCION"],f["ENCARGADO_REDSETEL_INSPECCION"],f["ESTADO_PERMISO"],rid))

# ── MUNICIPALES ───────────────────────────────────────────────────────────────
def mun_fields(pfx, d):
    r = {}
    c1,c2 = st.columns(2)
    r["ARMADO_EXP"]               = c1.text_input("Armado Expediente",      value=d.get("ARMADO_EXP","") or "",  key=f"{pfx}_ae")
    r["COSTO_ARMADO_EXP"]         = c2.number_input("Costo Armado Exp. (S/)", value=float(d.get("COSTO_ARMADO_EXP") or 0), step=0.01, key=f"{pfx}_ca")
    c3,c4 = st.columns(2)
    r["FECHA_INGRESO_EXP"]        = str(c3.date_input("Fecha Ingreso Exp.",     value=safe_date(d.get("FECHA_INGRESO_EXP")),      key=f"{pfx}_fie") or "")
    r["CARGO_EXP"]                = c4.text_input("Cargo Expediente",       value=d.get("CARGO_EXP","") or "",   key=f"{pfx}_ce")
    c5,c6 = st.columns(2)
    r["PAGO_CARGO_EXP"]           = c5.number_input("Pago Cargo Exp. (S/)", value=float(d.get("PAGO_CARGO_EXP") or 0), step=0.01, key=f"{pfx}_pc")
    r["FECHA_APROXIMADA_EMISION"] = str(c6.date_input("Fecha Aprox. Emisión",  value=safe_date(d.get("FECHA_APROXIMADA_EMISION")),key=f"{pfx}_fae") or "")
    c7,c8 = st.columns(2)
    r["FECHA_EMISION"]            = str(c7.date_input("Fecha Emisión Real",    value=safe_date(d.get("FECHA_EMISION")),          key=f"{pfx}_fe")  or "")
    r["CONTACTO_NOMBRE"]          = c8.text_input("Contacto - Nombre",     value=d.get("CONTACTO_NOMBRE","") or "", key=f"{pfx}_cn")
    c9,c10 = st.columns(2)
    r["CONTACTO_NUMERO"]          = c9.text_input("Contacto - Número",     value=d.get("CONTACTO_NUMERO","") or "", key=f"{pfx}_cnum")
    idx = ESTADO_OPTIONS.index(d["ESTADO_PERMISO"]) if d.get("ESTADO_PERMISO") in ESTADO_OPTIONS else 0
    r["ESTADO_PERMISO"]           = c10.selectbox("Estado", ESTADO_OPTIONS, index=idx, key=f"{pfx}_ep")
    return r

def mun_insert(f, dorsal, ccpp):
    execute("""INSERT INTO PERMISOS_MUNICIPALES
        (DORSAL,CCPP_VIAL_SITIOCLARO,ARMADO_EXP,COSTO_ARMADO_EXP,FECHA_INGRESO_EXP,
         CARGO_EXP,PAGO_CARGO_EXP,FECHA_APROXIMADA_EMISION,FECHA_EMISION,
         CONTACTO_NOMBRE,CONTACTO_NUMERO,ESTADO_PERMISO)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (dorsal,ccpp,f["ARMADO_EXP"],f["COSTO_ARMADO_EXP"],f["FECHA_INGRESO_EXP"],
         f["CARGO_EXP"],f["PAGO_CARGO_EXP"],f["FECHA_APROXIMADA_EMISION"],f["FECHA_EMISION"],
         f["CONTACTO_NOMBRE"],f["CONTACTO_NUMERO"],f["ESTADO_PERMISO"]))

def mun_update(f, rid):
    execute("""UPDATE PERMISOS_MUNICIPALES SET
        DORSAL=?,CCPP_VIAL_SITIOCLARO=?,ARMADO_EXP=?,COSTO_ARMADO_EXP=?,FECHA_INGRESO_EXP=?,
        CARGO_EXP=?,PAGO_CARGO_EXP=?,FECHA_APROXIMADA_EMISION=?,FECHA_EMISION=?,
        CONTACTO_NOMBRE=?,CONTACTO_NUMERO=?,ESTADO_PERMISO=? WHERE ID=?""",
        (f["DORSAL"],f["CCPP_VIAL_SITIOCLARO"],f["ARMADO_EXP"],f["COSTO_ARMADO_EXP"],f["FECHA_INGRESO_EXP"],
         f["CARGO_EXP"],f["PAGO_CARGO_EXP"],f["FECHA_APROXIMADA_EMISION"],f["FECHA_EMISION"],
         f["CONTACTO_NOMBRE"],f["CONTACTO_NUMERO"],f["ESTADO_PERMISO"],rid))

# ── PROVIAS ───────────────────────────────────────────────────────────────────
def prov_fields(pfx, d):
    r = {}
    c1,c2 = st.columns(2)
    r["TIPO_PERMISOS"]            = c1.text_input("Tipo de Permiso",    value=d.get("TIPO_PERMISOS","") or "",    key=f"{pfx}_tp")
    r["CONTRATA_PERMISOS"]        = c2.text_input("Contrata / Gestor",  value=d.get("CONTRATA_PERMISOS","") or "",key=f"{pfx}_cp")
    c3,c4 = st.columns(2)
    r["COSTO_CONTRATA"]           = c3.number_input("Costo Contrata (S/)", value=float(d.get("COSTO_CONTRATA") or 0), step=0.01, key=f"{pfx}_cc")
    r["CARGO_INGRESO"]            = c4.text_input("Cargo Ingreso",      value=d.get("CARGO_INGRESO","") or "",    key=f"{pfx}_ci")
    c5,c6 = st.columns(2)
    r["FECHA_APROXIMADA_INGRESO"] = str(c5.date_input("Fecha Aprox. Ingreso", value=safe_date(d.get("FECHA_APROXIMADA_INGRESO")), key=f"{pfx}_fai") or "")
    r["FECHA_INGRESO"]            = str(c6.date_input("Fecha Ingreso Real",   value=safe_date(d.get("FECHA_INGRESO")),            key=f"{pfx}_fi")  or "")
    c7,c8 = st.columns(2)
    r["FECHA_APROXIMADA_RD"]      = str(c7.date_input("Fecha Aprox. RD",      value=safe_date(d.get("FECHA_APROXIMADA_RD")),      key=f"{pfx}_far") or "")
    r["FECHA_RD"]                 = str(c8.date_input("Fecha RD",             value=safe_date(d.get("FECHA_RD")),                 key=f"{pfx}_frd") or "")
    c9,c10 = st.columns(2)
    r["CARGO_RD"]                 = c9.text_input("Cargo RD", value=d.get("CARGO_RD","") or "", key=f"{pfx}_crd")
    idx = ESTADO_OPTIONS.index(d["ESTADO_PERMISO"]) if d.get("ESTADO_PERMISO") in ESTADO_OPTIONS else 0
    r["ESTADO_PERMISO"]           = c10.selectbox("Estado", ESTADO_OPTIONS, index=idx, key=f"{pfx}_ep")
    return r

def prov_insert(f, dorsal, ccpp):
    execute("""INSERT INTO PERMISOS_PROVIAS
        (DORSAL,CCPP_VIAL_SITIOCLARO,TIPO_PERMISOS,CONTRATA_PERMISOS,COSTO_CONTRATA,
         FECHA_APROXIMADA_INGRESO,FECHA_INGRESO,CARGO_INGRESO,
         FECHA_APROXIMADA_RD,FECHA_RD,CARGO_RD,ESTADO_PERMISO)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (dorsal,ccpp,f["TIPO_PERMISOS"],f["CONTRATA_PERMISOS"],f["COSTO_CONTRATA"],
         f["FECHA_APROXIMADA_INGRESO"],f["FECHA_INGRESO"],f["CARGO_INGRESO"],
         f["FECHA_APROXIMADA_RD"],f["FECHA_RD"],f["CARGO_RD"],f["ESTADO_PERMISO"]))

def prov_update(f, rid):
    execute("""UPDATE PERMISOS_PROVIAS SET
        DORSAL=?,CCPP_VIAL_SITIOCLARO=?,TIPO_PERMISOS=?,CONTRATA_PERMISOS=?,COSTO_CONTRATA=?,
        FECHA_APROXIMADA_INGRESO=?,FECHA_INGRESO=?,CARGO_INGRESO=?,
        FECHA_APROXIMADA_RD=?,FECHA_RD=?,CARGO_RD=?,ESTADO_PERMISO=? WHERE ID=?""",
        (f["DORSAL"],f["CCPP_VIAL_SITIOCLARO"],f["TIPO_PERMISOS"],f["CONTRATA_PERMISOS"],f["COSTO_CONTRATA"],
         f["FECHA_APROXIMADA_INGRESO"],f["FECHA_INGRESO"],f["CARGO_INGRESO"],
         f["FECHA_APROXIMADA_RD"],f["FECHA_RD"],f["CARGO_RD"],f["ESTADO_PERMISO"],rid))


# ════════════════════════════════════════════════════════════════════════════
# ROUTE PERMIT PAGES
# ════════════════════════════════════════════════════════════════════════════
if page == "ambientales":
    permit_page("🌿 Permisos Ambientales",   "PERMISOS_AMBIENTALES",  amb_fields,  amb_insert,  amb_update)

elif page == "arqueologicos":
    permit_page("🏺 Permisos Arqueológicos", "PERMISOS_ARQUEOLOGICOS",arq_fields,  arq_insert,  arq_update)

elif page == "electricos":
    permit_page("⚡ Permisos Eléctricos",    "PERMISOS_ELECTRICOS",   elec_fields, elec_insert, elec_update)

elif page == "municipales":
    permit_page("🏛️ Permisos Municipales",   "PERMISOS_MUNICIPALES",  mun_fields,  mun_insert,  mun_update)

elif page == "provias":
    permit_page("🛣️ Permisos PROVIAS",       "PERMISOS_PROVIAS",      prov_fields, prov_insert, prov_update)


# ════════════════════════════════════════════════════════════════════════════
# HISTORIAL
# ════════════════════════════════════════════════════════════════════════════
elif page == "historial":
    st.markdown('<div class="section-header">📜 Historial de Permisos</div>', unsafe_allow_html=True)

    dorsales, dorsal_to_ccpp = get_proyectos()
    df_all  = fetch_df("SELECT rowid as ID, * FROM HISTORIAL_PERMISOS ORDER BY FECHA_REGISTRO DESC")
    df_view = filter_bar(df_all.rename(columns={"PROYECTO": "DORSAL"}).copy(), "hist") if not df_all.empty else df_all

    st.subheader("Registros de Historial")
    display_cols = [c for c in df_view.columns if c != "ID"]
    if not df_view.empty:
        st.dataframe(df_view[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("Sin registros aún.")

    st.markdown("---")
    if not dorsales:
        st.warning("⚠️ Primero registra un Proyecto.")
    else:
        tab_new, tab_edit = st.tabs(["➕ Nuevo registro", "✏️ Editar / Eliminar"])

        with tab_new:
            with st.form("form_historial", clear_on_submit=True):
                c1, c2     = st.columns(2)
                proyecto   = c1.selectbox("Proyecto (DORSAL) *", dorsales)
                ccpp_auto  = dorsal_to_ccpp.get(proyecto, "")
                c2.text_input("CCPP (auto)", value=ccpp_auto, disabled=True)
                fecha_reg  = st.date_input("Fecha Registro", value=date.today())
                comentario = st.text_area("Comentario", height=100)
                if st.form_submit_button("💾 Guardar", use_container_width=True):
                    execute("INSERT INTO HISTORIAL_PERMISOS (PROYECTO,CCPP_VIAL_SITIOCLARO,FECHA_REGISTRO,COMENTARIO) VALUES (?,?,?,?)",
                            (proyecto, ccpp_auto, str(fecha_reg), comentario))
                    st.success("✅ Historial guardado.")
                    st.rerun()

        with tab_edit:
            if df_all.empty:
                st.info("Sin registros para editar.")
            else:
                opts = {f"ID {r['ID']}  —  {r['PROYECTO']}  |  {r['FECHA_REGISTRO']}": r["ID"] for _, r in df_all.iterrows()}
                choice = st.selectbox("Selecciona registro", ["— Selecciona —"] + list(opts.keys()), key="hist_edit_sel")
                if choice != "— Selecciona —":
                    sel_id = opts[choice]
                    row    = df_all[df_all["ID"] == sel_id].iloc[0]
                    st.markdown('<div class="edit-header">✏️ Editando registro</div>', unsafe_allow_html=True)
                    with st.form(f"form_edit_hist_{sel_id}"):
                        c1, c2    = st.columns(2)
                        d_idx     = dorsales.index(row["PROYECTO"]) if row["PROYECTO"] in dorsales else 0
                        new_proy  = c1.selectbox("Proyecto", dorsales, index=d_idx)
                        new_ccpp  = c2.text_input("CCPP", value=row["CCPP_VIAL_SITIOCLARO"] or "")
                        new_fecha = st.date_input("Fecha Registro", value=safe_date(row["FECHA_REGISTRO"]) or date.today())
                        new_com   = st.text_area("Comentario", value=row["COMENTARIO"] or "")
                        cs, cd    = st.columns(2)
                        if cs.form_submit_button("💾 Guardar cambios", use_container_width=True):
                            execute("UPDATE HISTORIAL_PERMISOS SET PROYECTO=?,CCPP_VIAL_SITIOCLARO=?,FECHA_REGISTRO=?,COMENTARIO=? WHERE rowid=?",
                                    (new_proy, new_ccpp, str(new_fecha), new_com, sel_id))
                            st.success("✅ Actualizado.")
                            st.rerun()
                        if cd.form_submit_button("🗑️ Eliminar", use_container_width=True):
                            execute("DELETE FROM HISTORIAL_PERMISOS WHERE rowid=?", (sel_id,))
                            st.success("Eliminado.")
                            st.rerun()
