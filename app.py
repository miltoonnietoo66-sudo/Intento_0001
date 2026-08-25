import io
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import streamlit as st

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Sistema INER - Gestión de Laboratorios", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

TZ_CDMX = ZoneInfo("America/Mexico_City")
DB_NAME = "laboratorio_iner.db"

# 2. BASE DE DATOS SQLITE
def obtener_conexion():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_bd():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id TEXT PRIMARY KEY,
            fecha_hora TEXT,
            tipo TEXT,
            numero TEXT,
            marca TEXT,
            modelo TEXT,
            serie TEXT,
            inventario TEXT,
            ubicacion_lab TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros_uso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id TEXT,
            accion TEXT,
            fecha_hora_cdmx TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_ambientales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT,
            tipo TEXT,
            val_min TEXT,
            val_max TEXT,
            instrumento TEXT,
            ubicacion_lab TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_condiciones_equipos (
            id TEXT PRIMARY KEY,
            fecha_hora TEXT,
            tipo_equipo TEXT,
            numero TEXT,
            marca TEXT,
            modelo TEXT,
            serie TEXT,
            inventario TEXT,
            ubicacion_lab TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS correcciones_rangos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entidad_id TEXT,
            rango TEXT,
            correccion REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mediciones_ambientales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT,
            lab TEXT,
            temp_leida REAL,
            temp_corr REAL,
            hum_leida REAL,
            hum_corr REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mediciones_equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT,
            lab TEXT,
            parametro TEXT,
            lectura TEXT,
            corregida TEXT
        )
    """)
    conn.commit()
    conn.close()

inicializar_bd()

# 3. CSS RESPONSIVO Y ESTILOS DE BANNER AZUL
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFFFFF;
        background-image: url('https://www.gob.mx/cms/uploads/action_program/main_image/26915/iner.jpg');
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
        background-size: min(80vw, 420px);
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(255, 255, 255, 0.92);
        z-index: -1;
    }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    
    /* FILA 1: MARCO SUPERIOR */
    .marco-superior {
        height: 15px;
        width: 100%;
    }

    /* FILA 2: BANNER AZUL CON TÍTULO */
    .banner-azul {
        background-color: #0077B6;
        color: #FFFFFF;
        font-weight: bold;
        text-align: center;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        font-size: clamp(1rem, 2.2vw, 1.4rem);
        letter-spacing: 1px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.15);
    }

    .label-box {
        border: 2px solid #0077B6;
        background-color: #FFFFFF;
        color: #0077B6;
        font-weight: bold;
        text-align: center;
        padding: 0.4rem;
        border-radius: 6px;
        min-height: 2.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: clamp(0.85rem, 2vw, 1rem);
    }
    .reloj-box {
        border: 2px solid #0077B6;
        background-color: #F0F8FF;
        color: #0077B6;
        font-weight: bold;
        text-align: center;
        padding: 0.4rem;
        border-radius: 6px;
        min-height: 2.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: clamp(0.8rem, 1.8vw, 0.95rem);
    }
    div[data-testid="stButton"] > button {
        color: #E63946 !important;
        font-weight: bold !important;
        background-color: #FFFFFF !important;
        border: 2px solid #0077B6 !important;
        border-radius: 6px !important;
        width: 100% !important;
        min-height: 2.8rem !important;
        font-size: clamp(0.8rem, 1.8vw, 1rem) !important;
        padding: 0.2rem 0.5rem !important;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #F0F8FF !important;
        border-color: #023E8A !important;
    }
    .btn-hecho div[data-testid="stButton"] > button {
        background-color: #2A9D8F !important;
        color: #FFFFFF !important;
        border: 2px solid #2A9D8F !important;
        font-size: clamp(0.95rem, 2vw, 1.15rem) !important;
    }
    .btn-hecho div[data-testid="stButton"] > button:hover {
        background-color: #218377 !important;
    }
    .btn-eliminar div[data-testid="stButton"] > button {
        background-color: #E63946 !important;
        color: #FFFFFF !important;
        border: 2px solid #E63946 !important;
        font-size: clamp(0.95rem, 2vw, 1.15rem) !important;
    }
    .btn-eliminar div[data-testid="stButton"] > button:hover {
        background-color: #C52A36 !important;
    }
    .section-title {
        color: #0077B6;
        font-weight: bold;
        text-align: center;
        border-bottom: 2px solid #0077B6;
        padding-bottom: 5px;
        margin-bottom: 15px;
        font-size: clamp(1.1rem, 2.5vw, 1.4rem);
    }
    .oval-corregido {
        border: 2px solid #F4A261;
        background-color: #FFF3E0;
        color: #E76F51;
        font-weight: bold;
        text-align: center;
        padding: 0.5rem;
        border-radius: 20px;
        margin-top: 5px;
        margin-bottom: 15px;
        font-size: clamp(0.85rem, 1.8vw, 0.95rem);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 4. INICIALIZACIÓN DE VARIABLES DE ESTADO
if "lab_seleccionado" not in st.session_state:
    st.session_state["lab_seleccionado"] = None
if "modo_agregar" not in st.session_state:
    st.session_state["modo_agregar"] = False
if "modo_eliminar" not in st.session_state:
    st.session_state["modo_eliminar"] = False
if "sub_seccion_mas" not in st.session_state:
    st.session_state["sub_seccion_mas"] = "EQUIPOS"
if "sub_seccion_menos" not in st.session_state:
    st.session_state["sub_seccion_menos"] = "EQUIPOS"
if "sub_seccion_lab" not in st.session_state:
    st.session_state["sub_seccion_lab"] = "USO DE EQUIPOS"
if "equipo_activo_id" not in st.session_state:
    st.session_state["equipo_activo_id"] = None
if "item_editar_id" not in st.session_state:
    st.session_state["item_editar_id"] = None

if "sel_tipo_equipo" not in st.session_state:
    st.session_state["sel_tipo_equipo"] = "GABS"
if "sel_ubicacion_lab" not in st.session_state:
    st.session_state["sel_ubicacion_lab"] = "502"
if "sel_tipo_amb" not in st.session_state:
    st.session_state["sel_tipo_amb"] = "TEMP"
if "sel_tipo_ce" not in st.session_state:
    st.session_state["sel_tipo_ce"] = "CONG"

labs_lista = ["502", "503", "504", "506", "507", "508", "510", "513", "514"]

# 5. FUNCIONES AUXILIARES
def obtener_hora_cdmx():
    return datetime.now(TZ_CDMX).strftime("%d/%m/%Y %H:%M:%S")

def aplicar_estilo_seleccion(llave_css):
    st.markdown(
        f"""
        <style>
        div[data-testid="stButton"] > button[key="{llave_css}"] {{
            background-color: #2A9D8F !important;
            color: #FFFFFF !important;
            border: 2px solid #2A9D8F !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def cargar_equipos(lab=None):
    conn = obtener_conexion()
    if lab:
        df = pd.read_sql_query("SELECT * FROM equipos WHERE ubicacion_lab = ?", conn, params=(lab,))
    else:
        df = pd.read_sql_query("SELECT * FROM equipos", conn)
    conn.close()
    return df.to_dict(orient="records")

def cargar_todas_config_ambientales():
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT * FROM config_ambientales", conn)
    conn.close()
    return df.to_dict(orient="records")

def cargar_todas_config_condiciones_equipos():
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT * FROM config_condiciones_equipos", conn)
    conn.close()
    return df.to_dict(orient="records")

def cargar_correcciones_df(entidad_id):
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT rango as Rango, correccion as Corrección FROM correcciones_rangos WHERE entidad_id = ?", conn, params=(entidad_id,))
    conn.close()
    return df

def calcular_correccion_valor(valor_leido, tabla_correcciones, columna_rango="Rango"):
    if valor_leido is None:
        return None, 0.0

    for reg in tabla_correcciones:
        rango_str = str(reg.get(columna_rango, ""))
        corr_val = reg.get("Corrección", 0)

        try:
            factor_corr = float(corr_val) if corr_val != "" else 0.0
        except ValueError:
            factor_corr = 0.0

        partes = rango_str.split("a") if "a" in rango_str else rango_str.split("-")
        if len(partes) == 2:
            try:
                min_r = float(partes[0].replace("°C", "").replace("%", "").strip())
                max_r = float(partes[1].replace("°C", "").replace("%", "").strip())
                if min_r <= valor_leido <= max_r:
                    return round(valor_leido + factor_corr, 2), factor_corr
            except ValueError:
                continue

    return round(valor_leido, 2), 0.0

def cargar_registros_uso(equipo_id):
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT accion as Acción, fecha_hora_cdmx as FechaHora_CDMX FROM registros_uso WHERE equipo_id = ? ORDER BY id ASC", conn, params=(equipo_id,))
    conn.close()
    return df.to_dict(orient="records")

def cargar_condicion_ambiental_config(lab, tipo):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM config_ambientales WHERE ubicacion_lab = ? AND tipo = ? ORDER BY id DESC LIMIT 1", (lab, tipo))
    row = cursor.fetchone()
    conn.close()
    if row:
        cfg = dict(row)
        entidad_id = f"AMB_{lab}_{tipo}"
        corr_df = cargar_correcciones_df(entidad_id)
        return {
            "Fecha_Hora": cfg["fecha_hora"],
            "Tipo": cfg["tipo"],
            "Min": cfg["val_min"],
            "Max": cfg["val_max"],
            "Instrumento": cfg["instrumento"],
            "Correcciones": corr_df.to_dict(orient="records"),
            "Ubicacion_Lab": cfg["ubicacion_lab"]
        }
    return None

def cargar_condiciones_equipos_db(lab):
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT * FROM config_condiciones_equipos WHERE ubicacion_lab = ?", conn, params=(lab,))
    conn.close()
    res = []
    for _, r in df.iterrows():
        corr_df = cargar_correcciones_df(r["id"])
        res.append({
            "id_ce": r["id"],
            "Fecha_Hora": r["fecha_hora"],
            "Tipo_Equipo": r["tipo_equipo"],
            "Numero": r["numero"],
            "Marca": r["marca"],
            "Modelo": r["modelo"],
            "Serie": r["serie"],
            "Inventario": r["inventario"],
            "Correcciones": corr_df.to_dict(orient="records"),
            "Ubicacion_Lab": r["ubicacion_lab"]
        })
    return res

# ==========================================
# FILA 1: MARCO SUPERIOR (ESPACIO DE MARCO)
# ==========================================
st.markdown('<div class="marco-superior"></div>', unsafe_allow_html=True)

# ==========================================
# FILA 2: BANNER AZUL INSTITUCIONAL
# ==========================================
st.markdown('<div class="banner-azul">LABORATORIO DE INMUNOBIOLOGÍA DE LA TUBERCULOSIS</div>', unsafe_allow_html=True)

# ==========================================
# FILA 3: ENCABEZADO Y BUSCADOR
# ==========================================
col1_1, col1_2, col1_3, col1_4 = st.columns([1.2, 1.2, 3, 1.2])

with col1_1:
    st.markdown('<div class="label-box">INER</div>', unsafe_allow_html=True)

with col1_2:
    if st.button("BUSCAR", key="btn_buscar"):
        st.toast("Función de búsqueda activada")

with col1_3:
    st.markdown(f'<div class="reloj-box">🕒 CDMX: {obtener_hora_cdmx()}</div>', unsafe_allow_html=True)

with col1_4:
    st.markdown('<div class="label-box">LIT</div>', unsafe_allow_html=True)

st.write("")

# ==========================================
# FILA 4: BARRA DE NAVEGACIÓN (LABS + INICIO + MÁS + MENOS)
# ==========================================
labs_menu = labs_lista + ["INICIO", "MAS", "MENOS"]
cols_f2 = st.columns([2] + [1] * (len(labs_menu)))

with cols_f2[0]:
    st.markdown('<div class="label-box">LABS</div>', unsafe_allow_html=True)

for idx, lab in enumerate(labs_menu, start=1):
    with cols_f2[idx]:
        if lab == "INICIO":
            etiqueta = "🏠"
        elif lab == "MAS":
            etiqueta = "➕"
        elif lab == "MENOS":
            etiqueta = "➖"
        else:
            etiqueta = lab

        if st.button(etiqueta, key=f"btn_f2_{lab}"):
            if lab == "INICIO":
                st.session_state["lab_seleccionado"] = None
                st.session_state["modo_agregar"] = False
                st.session_state["modo_eliminar"] = False
                st.session_state["equipo_activo_id"] = None
            elif lab == "MAS":
                st.session_state["modo_agregar"] = True
                st.session_state["modo_eliminar"] = False
                st.session_state["lab_seleccionado"] = None
                st.session_state["sub_seccion_mas"] = "EQUIPOS"
            elif lab == "MENOS":
                st.session_state["modo_eliminar"] = True
                st.session_state["modo_agregar"] = False
                st.session_state["lab_seleccionado"] = None
                st.session_state["sub_seccion_menos"] = "EQUIPOS"
                st.session_state["item_editar_id"] = None
            else:
                st.session_state["lab_seleccionado"] = lab
                st.session_state["modo_agregar"] = False
                st.session_state["modo_eliminar"] = False
                st.session_state["sub_seccion_lab"] = "USO DE EQUIPOS"
                st.session_state["equipo_activo_id"] = None

st.markdown("---")

# ==========================================
# MENÚ MÁS (➕) - CONFIGURACIÓN Y ALTA
# ==========================================
if st.session_state["modo_agregar"]:
    col_m1, col_m2, col_m3 = st.columns([1, 1, 1])

    with col_m1:
        if st.button("EQUIPOS", key="btn_m_equipos"):
            st.session_state["sub_seccion_mas"] = "EQUIPOS"

    with col_m2:
        if st.button("CONDICIONES AMBIENTALES", key="btn_m_ambientales"):
            st.session_state["sub_seccion_mas"] = "CONDICIONES AMBIENTALES"

    with col_m3:
        if st.button("CONDICIONES DE EQUIPOS", key="btn_m_cond_equipos"):
            st.session_state["sub_seccion_mas"] = "CONDICIONES DE EQUIPOS"

    st.write("")

    if st.session_state["sub_seccion_mas"] == "EQUIPOS":
        st.markdown('<div class="section-title">REGISTRO DE EQUIPOS DE USO</div>', unsafe_allow_html=True)
        c_tipo, c_num, c_marca, c_mod, c_serie, c_inv = st.columns([1.5, 1, 1.5, 1.5, 1.5, 1.5])

        with c_tipo:
            st.write("**TIPO**")
            for teq in ["GABS", "CENT", "MICR", "BAAG"]:
                key_btn = f"btn_teq_{teq}"
                if st.session_state["sel_tipo_equipo"] == teq:
                    aplicar_estilo_seleccion(key_btn)
                if st.button(teq, key=key_btn):
                    st.session_state["sel_tipo_equipo"] = teq
                    st.rerun()

        with c_num:
            st.write("**NÚMERO**")
            num_eq = st.text_input("N°", key="req_num")

        with c_marca:
            st.write("**MARCA**")
            marca_eq = st.text_input("Marca", key="req_marca")

        with c_mod:
            st.write("**MODELO**")
            modelo_eq = st.text_input("Modelo", key="req_mod")

        with c_serie:
            st.write("**SERIE**")
            serie_eq = st.text_input("N° Serie", key="req_serie")

        with c_inv:
            st.write("**INVENTARIO**")
            inv_eq = st.text_input("Cód. Inventario", key="req_inv")

        st.write("")
        st.write("**UBICACIÓN (SELECCIONAR LABORATORIO)**")
        cols_ub = st.columns(len(labs_lista))
        for idx_l, l_code in enumerate(labs_lista):
            with cols_ub[idx_l]:
                key_ub = f"btn_ub_lab_{l_code}"
                if st.session_state["sel_ubicacion_lab"] == l_code:
                    aplicar_estilo_seleccion(key_ub)
                if st.button(l_code, key=key_ub):
                    st.session_state["sel_ubicacion_lab"] = l_code
                    st.rerun()

        st.write("")
        st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
        if st.button("HECHO", key="btn_hecho_equipos"):
            id_unico = f"{st.session_state['sel_tipo_equipo']}-{num_eq}_{st.session_state['sel_ubicacion_lab']}"
            conn = obtener_conexion()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO equipos (id, fecha_hora, tipo, numero, marca, modelo, serie, inventario, ubicacion_lab)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_unico, obtener_hora_cdmx(), st.session_state['sel_tipo_equipo'], num_eq, marca_eq, modelo_eq, serie_eq, inv_eq, st.session_state['sel_ubicacion_lab']))
            conn.commit()
            conn.close()
            st.success(f"💾 Guardado: Equipo {st.session_state['sel_tipo_equipo']}-{num_eq} en Lab {st.session_state['sel_ubicacion_lab']}.")
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state["sub_seccion_mas"] == "CONDICIONES AMBIENTALES":
        st.markdown('<div class="section-title">CONFIGURACIÓN DE CONDICIONES AMBIENTALES</div>', unsafe_allow_html=True)
        ca_tipo, ca_rangos, ca_inst, ca_corr = st.columns([1.2, 1.2, 2, 3.5])

        with ca_tipo:
            st.write("**TIPO**")
            for tamb in ["TEMP", "%H"]:
                key_tamb = f"btn_tamb_{tamb}"
                if st.session_state["sel_tipo_amb"] == tamb:
                    aplicar_estilo_seleccion(key_tamb)
                if st.button(tamb, key=key_tamb):
                    st.session_state["sel_tipo_amb"] = tamb
                    st.rerun()

        with ca_rangos:
            st.write("**RANGOS**")
            val_min = st.text_input("MIN", key="ca_min")
            val_max = st.text_input("MAX", key="ca_max")

        with ca_inst:
            st.write("**INSTRUMENTO MEDICIÓN**")
            inst_medicion = st.text_area("Descripción / Código", key="ca_inst")

        with ca_corr:
            st.write("**CORRECCIÓN (TABLA DE VALORES)**")
            rangos = ["10 - 20", "20.1 - 30", "30.1 - 40", "40.1 - 50", "50.1 - 60", "60.1 - 70", "70.1 - 80", "80.1 - 100"] if st.session_state["sel_tipo_amb"] == "%H" else ["10 - 15", "15.1 - 20", "20.1 - 25", "25.1 - 30", "30.1 - 35"]
            df_corr = pd.DataFrame({"Rango": rangos, "Corrección": [0.0] * len(rangos)})
            tabla_corr_amb = st.data_editor(df_corr, hide_index=True, use_container_width=True, key="editor_corr_amb")

        st.write("")
        st.write("**UBICACIÓN (SELECCIONAR LABORATORIO)**")
        cols_ub = st.columns(len(labs_lista))
        for idx_l, l_code in enumerate(labs_lista):
            with cols_ub[idx_l]:
                key_ub = f"btn_ub_amb_{l_code}"
                if st.session_state["sel_ubicacion_lab"] == l_code:
                    aplicar_estilo_seleccion(key_ub)
                if st.button(l_code, key=key_ub):
                    st.session_state["sel_ubicacion_lab"] = l_code
                    st.rerun()

        st.write("")
        st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
        if st.button("HECHO", key="btn_hecho_ambientales"):
            conn = obtener_conexion()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO config_ambientales (fecha_hora, tipo, val_min, val_max, instrumento, ubicacion_lab)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (obtener_hora_cdmx(), st.session_state["sel_tipo_amb"], val_min, val_max, inst_medicion, st.session_state["sel_ubicacion_lab"]))
            
            entidad_id = f"AMB_{st.session_state['sel_ubicacion_lab']}_{st.session_state['sel_tipo_amb']}"
            cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ?", (entidad_id,))
            for _, fila in tabla_corr_amb.iterrows():
                cursor.execute("INSERT INTO correcciones_rangos (entidad_id, rango, correccion) VALUES (?, ?, ?)", (entidad_id, str(fila["Rango"]), float(fila["Corrección"])))
            conn.commit()
            conn.close()
            st.success("💾 Configuración ambiental guardada correctamente.")
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state["sub_seccion_mas"] == "CONDICIONES DE EQUIPOS":
        st.markdown('<div class="section-title">CONFIGURACIÓN DE CONDICIONES DE EQUIPOS</div>', unsafe_allow_html=True)
        ce_tipo, ce_datos, ce_corr = st.columns([1.2, 3.5, 3.5])

        with ce_tipo:
            st.write("**TIPO EQUIPO**")
            for tce in ["CONG", "REFR", "1CO2", "ULTRO"]:
                key_tce = f"btn_tce_{tce}"
                if st.session_state["sel_tipo_ce"] == tce:
                    aplicar_estilo_seleccion(key_tce)
                if st.button(tce, key=key_tce):
                    st.session_state["sel_tipo_ce"] = tce
                    st.rerun()

        with ce_datos:
            st.write("**DATOS TÉCNICOS**")
            d1, d2 = st.columns(2)
            with d1:
                ce_num = st.text_input("NÚMERO", key="ce_num")
                ce_marca = st.text_input("MARCA", key="ce_marca")
                ce_mod = st.text_input("MODELO", key="ce_mod")
            with d2:
                ce_serie = st.text_input("SERIE", key="ce_serie")
                ce_inv = st.text_input("INVENTARIO", key="ce_inv")

        with ce_corr:
            st.write("**CORRECCIÓN (TABLA DE VALORES)**")
            t_act = st.session_state["sel_tipo_ce"]
            r_list = ["-25 a -20", "-19.9 a -15", "-14.9 a -10"] if t_act == "CONG" else (["2 a 5", "5.1 a 8", "8.1 a 10"] if t_act == "REFR" else (["36.0 a 37.5", "4.5 a 5.5"] if t_act == "1CO2" else ["-85 a -80", "-79.9 a -70", "-69.9 a -60"]))
            df_ce_corr = pd.DataFrame({"Rango": r_list, "Corrección": [0.0] * len(r_list)})
            tabla_ce_corr = st.data_editor(df_ce_corr, hide_index=True, use_container_width=True, key="editor_ce_corr")

        st.write("")
        st.write("**UBICACIÓN (SELECCIONAR LABORATORIO)**")
        cols_ub = st.columns(len(labs_lista))
        for idx_l, l_code in enumerate(labs_lista):
            with cols_ub[idx_l]:
                key_ub = f"btn_ub_ce_{l_code}"
                if st.session_state["sel_ubicacion_lab"] == l_code:
                    aplicar_estilo_seleccion(key_ub)
                if st.button(l_code, key=key_ub):
                    st.session_state["sel_ubicacion_lab"] = l_code
                    st.rerun()

        st.write("")
        st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
        if st.button("HECHO", key="btn_hecho_cond_equipos"):
            id_ce = f"{st.session_state['sel_tipo_ce']}-{ce_num}_{st.session_state['sel_ubicacion_lab']}"
            conn = obtener_conexion()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO config_condiciones_equipos (id, fecha_hora, tipo_equipo, numero, marca, modelo, serie, inventario, ubicacion_lab)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_ce, obtener_hora_cdmx(), st.session_state['sel_tipo_ce'], ce_num, ce_marca, ce_mod, ce_serie, ce_inv, st.session_state['sel_ubicacion_lab']))
            
            cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ?", (id_ce,))
            for _, fila in tabla_ce_corr.iterrows():
                cursor.execute("INSERT INTO correcciones_rangos (entidad_id, rango, correccion) VALUES (?, ?, ?)", (id_ce, str(fila["Rango"]), float(fila["Corrección"])))
            conn.commit()
            conn.close()
            st.success("💾 Condición de equipo guardada correctamente.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MENÚ MENOS (➖) - EDICIÓN Y ELIMINACIÓN
# ==========================================
elif st.session_state["modo_eliminar"]:
    col_sub1, col_sub2, col_sub3 = st.columns([1, 1, 1])

    with col_sub1:
        if st.button("EQUIPOS", key="btn_sub_eq_menos"):
            st.session_state["sub_seccion_menos"] = "EQUIPOS"
            st.session_state["item_editar_id"] = None
            st.rerun()

    with col_sub2:
        if st.button("CONDICIONES AMBIENTALES", key="btn_sub_amb_menos"):
            st.session_state["sub_seccion_menos"] = "CONDICIONES AMBIENTALES"
            st.session_state["item_editar_id"] = None
            st.rerun()

    with col_sub3:
        if st.button("CONDICIONES DE EQUIPOS", key="btn_sub_ce_menos"):
            st.session_state["sub_seccion_menos"] = "CONDICIONES DE EQUIPOS"
            st.session_state["item_editar_id"] = None
            st.rerun()

    st.write("")

    if st.session_state["sub_seccion_menos"] == "EQUIPOS":
        st.markdown('<div class="section-title">SELECCIONA UN EQUIPO PARA EDITAR O ELIMINAR</div>', unsafe_allow_html=True)
        todos_equipos = cargar_equipos()

        if not todos_equipos:
            st.info("No hay equipos de uso registrados en la base de datos.")
        else:
            cols_grid = st.columns(4)
            for idx, eq in enumerate(todos_equipos):
                with cols_grid[idx % 4]:
                    lbl_btn = f"{eq['tipo']}-{eq['numero']} (Lab {eq['ubicacion_lab']})"
                    btn_key = f"btn_edit_eq_{eq['id']}"
                    if st.session_state["item_editar_id"] == eq["id"]:
                        aplicar_estilo_seleccion(btn_key)
                    if st.button(lbl_btn, key=btn_key):
                        st.session_state["item_editar_id"] = eq["id"]
                        st.rerun()

        if st.session_state["item_editar_id"]:
            eq_target = next((e for e in todos_equipos if e["id"] == st.session_state["item_editar_id"]), None)
            if eq_target:
                st.markdown("---")
                st.markdown(f'<div class="section-title">EDITANDO EQUIPO: {eq_target["id"]}</div>', unsafe_allow_html=True)

                c_tipo, c_num, c_marca, c_mod, c_serie, c_inv = st.columns([1.5, 1, 1.5, 1.5, 1.5, 1.5])
                with c_tipo:
                    st.write("**TIPO**")
                    tipo_ed = st.selectbox("Tipo", ["GABS", "CENT", "MICR", "BAAG"], index=["GABS", "CENT", "MICR", "BAAG"].index(eq_target["tipo"]) if eq_target["tipo"] in ["GABS", "CENT", "MICR", "BAAG"] else 0, key="ed_eq_tipo")
                with c_num:
                    st.write("**NÚMERO**")
                    num_ed = st.text_input("N°", value=eq_target["numero"], key="ed_eq_num")
                with c_marca:
                    st.write("**MARCA**")
                    marca_ed = st.text_input("Marca", value=eq_target["marca"], key="ed_eq_marca")
                with c_mod:
                    st.write("**MODELO**")
                    mod_ed = st.text_input("Modelo", value=eq_target["modelo"], key="ed_eq_mod")
                with c_serie:
                    st.write("**SERIE**")
                    serie_ed = st.text_input("N° Serie", value=eq_target["serie"], key="ed_eq_serie")
                with c_inv:
                    st.write("**INVENTARIO**")
                    inv_ed = st.text_input("Inventario", value=eq_target["inventario"], key="ed_eq_inv")

                st.write("")
                st.write("**UBICACIÓN (LABORATORIO)**")
                lab_ed = st.selectbox("Laboratorio", labs_lista, index=labs_lista.index(eq_target["ubicacion_lab"]) if eq_target["ubicacion_lab"] in labs_lista else 0, key="ed_eq_lab")

                st.write("")
                col_h, col_e = st.columns(2)
                with col_h:
                    st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
                    if st.button("HECHO (GUARDAR CAMBIOS)", key="btn_save_edit_eq"):
                        nuevo_id = f"{tipo_ed}-{num_ed}_{lab_ed}"
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE equipos 
                            SET id = ?, tipo = ?, numero = ?, marca = ?, modelo = ?, serie = ?, inventario = ?, ubicacion_lab = ?
                            WHERE id = ?
                        """, (nuevo_id, tipo_ed, num_ed, marca_ed, mod_ed, serie_ed, inv_ed, lab_ed, eq_target["id"]))
                        conn.commit()
                        conn.close()
                        st.session_state["item_editar_id"] = None
                        st.success("✅ Cambios guardados correctamente.")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                with col_e:
                    st.markdown('<div class="btn-eliminar">', unsafe_allow_html=True)
                    if st.button("ELIMINAR EQUIPO", key="btn_del_eq"):
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM equipos WHERE id = ?", (eq_target["id"],))
                        cursor.execute("DELETE FROM registros_uso WHERE equipo_id = ?", (eq_target["id"],))
                        conn.commit()
                        conn.close()
                        st.session_state["item_editar_id"] = None
                        st.success("🗑️ Equipo eliminado permanentemente.")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state["sub_seccion_menos"] == "CONDICIONES AMBIENTALES":
        st.markdown('<div class="section-title">SELECCIONA UNA CONFIGURACIÓN AMBIENTAL PARA EDITAR O ELIMINAR</div>', unsafe_allow_html=True)
        todas_amb = cargar_todas_config_ambientales()

        if not todas_amb:
            st.info("No hay configuraciones ambientales registradas.")
        else:
            cols_grid = st.columns(4)
            for idx, amb in enumerate(todas_amb):
                with cols_grid[idx % 4]:
                    lbl_btn = f"{amb['tipo']} (Lab {amb['ubicacion_lab']})"
                    btn_key = f"btn_edit_amb_{amb['id']}"
                    if st.session_state["item_editar_id"] == str(amb["id"]):
                        aplicar_estilo_seleccion(btn_key)
                    if st.button(lbl_btn, key=btn_key):
                        st.session_state["item_editar_id"] = str(amb["id"])
                        st.rerun()

        if st.session_state["item_editar_id"]:
            amb_target = next((a for a in todas_amb if str(a["id"]) == st.session_state["item_editar_id"]), None)
            if amb_target:
                st.markdown("---")
                st.markdown(f'<div class="section-title">EDITANDO CONFIGURACIÓN AMBIENTAL (LAB {amb_target["ubicacion_lab"]})</div>', unsafe_allow_html=True)

                ca_tipo, ca_rangos, ca_inst, ca_corr = st.columns([1.2, 1.2, 2, 3.5])
                with ca_tipo:
                    st.write("**TIPO**")
                    tipo_amb_ed = st.selectbox("Tipo", ["TEMP", "%H"], index=["TEMP", "%H"].index(amb_target["tipo"]) if amb_target["tipo"] in ["TEMP", "%H"] else 0, key="ed_amb_tipo")
                with ca_rangos:
                    st.write("**RANGOS**")
                    min_amb_ed = st.text_input("MIN", value=amb_target["val_min"], key="ed_amb_min")
                    max_amb_ed = st.text_input("MAX", value=amb_target["val_max"], key="ed_amb_max")
                with ca_inst:
                    st.write("**INSTRUMENTO**")
                    inst_amb_ed = st.text_area("Descripción", value=amb_target["instrumento"], key="ed_amb_inst")

                entidad_id = f"AMB_{amb_target['ubicacion_lab']}_{amb_target['tipo']}"
                df_corr_existente = cargar_correcciones_df(entidad_id)

                with ca_corr:
                    st.write("**TABLA DE CORRECCIONES**")
                    tabla_corr_amb_ed = st.data_editor(df_corr_existente, hide_index=True, use_container_width=True, key="ed_editor_corr_amb")

                st.write("")
                col_h, col_e = st.columns(2)
                with col_h:
                    st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
                    if st.button("HECHO (GUARDAR CAMBIOS)", key="btn_save_edit_amb"):
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE config_ambientales 
                            SET tipo = ?, val_min = ?, val_max = ?, instrumento = ?
                            WHERE id = ?
                        """, (tipo_amb_ed, min_amb_ed, max_amb_ed, inst_amb_ed, amb_target["id"]))

                        cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ?", (entidad_id,))
                        for _, fila in tabla_corr_amb_ed.iterrows():
                            cursor.execute("INSERT INTO correcciones_rangos (entidad_id, rango, correccion) VALUES (?, ?, ?)", (entidad_id, str(fila["Rango"]), float(fila["Corrección"])))

                        conn.commit()
                        conn.close()
                        st.session_state["item_editar_id"] = None
                        st.success("✅ Configuración ambiental actualizada.")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                with col_e:
                    st.markdown('<div class="btn-eliminar">', unsafe_allow_html=True)
                    if st.button("ELIMINAR CONFIGURACIÓN", key="btn_del_amb"):
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM config_ambientales WHERE id = ?", (amb_target["id"],))
                        cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ?", (entidad_id,))
                        conn.commit()
                        conn.close()
                        st.session_state["item_editar_id"] = None
                        st.success("🗑️ Configuración ambiental eliminada.")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state["sub_seccion_menos"] == "CONDICIONES DE EQUIPOS":
        st.markdown('<div class="section-title">SELECCIONA UN EQUIPO DE TEMPERATURA PARA EDITAR O ELIMINAR</div>', unsafe_allow_html=True)
        todas_ce = cargar_todas_config_condiciones_equipos()

        if not todas_ce:
            st.info("No hay condiciones de equipos configuradas.")
        else:
            cols_grid = st.columns(4)
            for idx, ce in enumerate(todas_ce):
                with cols_grid[idx % 4]:
                    lbl_btn = f"{ce['tipo_equipo']}-{ce['numero']} (Lab {ce['ubicacion_lab']})"
                    btn_key = f"btn_edit_ce_{ce['id']}"
                    if st.session_state["item_editar_id"] == ce["id"]:
                        aplicar_estilo_seleccion(btn_key)
                    if st.button(lbl_btn, key=btn_key):
                        st.session_state["item_editar_id"] = ce["id"]
                        st.rerun()

        if st.session_state["item_editar_id"]:
            ce_target = next((c for c in todas_ce if c["id"] == st.session_state["item_editar_id"]), None)
            if ce_target:
                st.markdown("---")
                st.markdown(f'<div class="section-title">EDITANDO CONDICIÓN DE EQUIPO: {ce_target["id"]}</div>', unsafe_allow_html=True)

                ce_tipo, ce_datos, ce_corr = st.columns([1.2, 3.5, 3.5])
                with ce_tipo:
                    st.write("**TIPO EQUIPO**")
                    t_ce_ed = st.selectbox("Tipo", ["CONG", "REFR", "1CO2", "ULTRO"], index=["CONG", "REFR", "1CO2", "ULTRO"].index(ce_target["tipo_equipo"]) if ce_target["tipo_equipo"] in ["CONG", "REFR", "1CO2", "ULTRO"] else 0, key="ed_ce_tipo")
                with ce_datos:
                    st.write("**DATOS TÉCNICOS**")
                    d1, d2 = st.columns(2)
                    with d1:
                        num_ce_ed = st.text_input("NÚMERO", value=ce_target["numero"], key="ed_ce_num")
                        marca_ce_ed = st.text_input("MARCA", value=ce_target["marca"], key="ed_ce_marca")
                        mod_ce_ed = st.text_input("MODELO", value=ce_target["modelo"], key="ed_ce_mod")
                    with d2:
                        serie_ce_ed = st.text_input("SERIE", value=ce_target["serie"], key="ed_ce_serie")
                        inv_ce_ed = st.text_input("INVENTARIO", value=ce_target["inventario"], key="ed_ce_inv")

                df_corr_ce_existente = cargar_correcciones_df(ce_target["id"])
                with ce_corr:
                    st.write("**CORRECCIÓN (TABLA DE VALORES)**")
                    tabla_ce_corr_ed = st.data_editor(df_corr_ce_existente, hide_index=True, use_container_width=True, key="ed_editor_ce_corr")

                st.write("")
                col_h, col_e = st.columns(2)
                with col_h:
                    st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
                    if st.button("HECHO (GUARDAR CAMBIOS)", key="btn_save_edit_ce"):
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE config_condiciones_equipos 
                            SET tipo_equipo = ?, numero = ?, marca = ?, modelo = ?, serie = ?, inventario = ?
                            WHERE id = ?
                        """, (t_ce_ed, num_ce_ed, marca_ce_ed, mod_ce_ed, serie_ce_ed, inv_ce_ed, ce_target["id"]))

                        cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ?", (ce_target["id"],))
                        for _, fila in tabla_ce_corr_ed.iterrows():
                            cursor.execute("INSERT INTO correcciones_rangos (entidad_id, rango, correccion) VALUES (?, ?, ?)", (ce_target["id"], str(fila["Rango"]), float(fila["Corrección"])))

                        conn.commit()
                        conn.close()
                        st.session_state["item_editar_id"] = None
                        st.success("✅ Condición de equipo actualizada.")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                with col_e:
                    st.markdown('<div class="btn-eliminar">', unsafe_allow_html=True)
                    if st.button("ELIMINAR REGISTRO", key="btn_del_ce"):
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM config_condiciones_equipos WHERE id = ?", (ce_target["id"],))
                        cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ?", (ce_target["id"],))
                        conn.commit()
                        conn.close()
                        st.session_state["item_editar_id"] = None
                        st.success("🗑️ Condición de equipo eliminada.")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# VISTA DE LABORATORIOS
# ==========================================
elif st.session_state["lab_seleccionado"] is not None:
    lab_actual = st.session_state["lab_seleccionado"]

    col3_1, col3_2, col3_3 = st.columns([1, 1, 1])

    with col3_1:
        if st.session_state["sub_seccion_lab"] == "USO DE EQUIPOS":
            aplicar_estilo_seleccion("btn_lab_uso")
        if st.button(f"EQUIPOS (LAB {lab_actual})", key="btn_lab_uso"):
            st.session_state["sub_seccion_lab"] = "USO DE EQUIPOS"
            st.rerun()

    with col3_2:
        if st.session_state["sub_seccion_lab"] == "CONDICIONES AMBIENTALES":
            aplicar_estilo_seleccion("btn_lab_amb")
        if st.button(f"COND. AMBIENTALES (LAB {lab_actual})", key="btn_lab_amb"):
            st.session_state["sub_seccion_lab"] = "CONDICIONES AMBIENTALES"
            st.rerun()

    with col3_3:
        if st.session_state["sub_seccion_lab"] == "CONDICIONES DE EQUIPOS":
            aplicar_estilo_seleccion("btn_lab_ce")
        if st.button(f"COND. EQUIPOS (LAB {lab_actual})", key="btn_lab_ce"):
            st.session_state["sub_seccion_lab"] = "CONDICIONES DE EQUIPOS"
            st.rerun()

    st.write("")

    if st.session_state["sub_seccion_lab"] == "USO DE EQUIPOS":
        st.markdown(f'<div class="section-title">EQUIPOS DISPONIBLES EN LABORATORIO {lab_actual}</div>', unsafe_allow_html=True)
        equipos_lab = cargar_equipos(lab_actual)

        if not equipos_lab:
            st.warning(f"⚠️ No hay equipos registrados para el Laboratorio {lab_actual}.")
        else:
            cols_eq = st.columns(min(len(equipos_lab), 4))
            for idx, eq in enumerate(equipos_lab):
                col_i = cols_eq[idx % 4]
                nombre_eq = f"{eq['tipo']}-{eq['numero']}"
                key_eq_btn = f"btn_sel_eq_{eq['id']}"

                with col_i:
                    if st.session_state["equipo_activo_id"] == eq["id"]:
                        aplicar_estilo_seleccion(key_eq_btn)
                    if st.button(nombre_eq, key=key_eq_btn):
                        st.session_state["equipo_activo_id"] = eq["id"]
                        st.rerun()

            if st.session_state["equipo_activo_id"]:
                eq_sel = next((item for item in equipos_lab if item["id"] == st.session_state["equipo_activo_id"]), None)

                if eq_sel:
                    st.markdown("---")
                    st.subheader(f"Control de Uso: {eq_sel['tipo']}-{eq_sel['numero']} (Marca: {eq_sel['marca']} | Serie: {eq_sel['serie']})")

                    c_init, c_space, c_fin = st.columns([4, 0.5, 4])
                    with c_init:
                        st.markdown("<h3 style='color:#2A9D8F; text-align:center;'>INICIO</h3>", unsafe_allow_html=True)
                        if st.button("🟢 REGISTRAR INICIO DE USO", key=f"btn_init_{eq_sel['id']}"):
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO registros_uso (equipo_id, accion, fecha_hora_cdmx) VALUES (?, ?, ?)", (eq_sel["id"], "INICIO", obtener_hora_cdmx()))
                            conn.commit()
                            conn.close()
                            st.toast("🟢 Inicio registrado")
                            st.rerun()

                    with c_fin:
                        st.markdown("<h3 style='color:#E63946; text-align:center;'>FINAL</h3>", unsafe_allow_html=True)
                        if st.button("🔴 REGISTRAR FINALIZACIÓN", key=f"btn_fin_{eq_sel['id']}"):
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO registros_uso (equipo_id, accion, fecha_hora_cdmx) VALUES (?, ?, ?)", (eq_sel["id"], "FINAL", obtener_hora_cdmx()))
                            conn.commit()
                            conn.close()
                            st.toast("🔴 Finalización registrada")
                            st.rerun()

                    st.write("")
                    reg_filtrados = cargar_registros_uso(eq_sel["id"])
                    if reg_filtrados:
                        df_usos = pd.DataFrame(reg_filtrados)[["Acción", "FechaHora_CDMX"]]
                        st.dataframe(df_usos, use_container_width=True)

    elif st.session_state["sub_seccion_lab"] == "CONDICIONES AMBIENTALES":
        st.markdown(f'<div class="section-title">CONDICIONES AMBIENTALES - LAB {lab_actual}</div>', unsafe_allow_html=True)

        cfg_temp = cargar_condicion_ambiental_config(lab_actual, "TEMP")
        cfg_hum = cargar_condicion_ambiental_config(lab_actual, "%H")

        col_amb_temp, col_amb_hum = st.columns(2)

        with col_amb_temp:
            st.markdown("<h3 style='text-align:center; color:#0077B6;'>TEMPERATURA</h3>", unsafe_allow_html=True)
            inp_temp = st.number_input("Ingresar Lectura (°C)", key=f"inp_temp_{lab_actual}", value=None, step=0.1)
            t_corregida, factor_t = None, 0.0
            if inp_temp is not None:
                tabla_t = cfg_temp.get("Correcciones", []) if cfg_temp else []
                t_corregida, factor_t = calcular_correccion_valor(inp_temp, tabla_t)

            val_disp_t = f"{t_corregida} °C" if t_corregida is not None else "0.0 °C"
            st.markdown(f'<div class="oval-corregido">Lectura Corregida: {val_disp_t} (Corr: {factor_t:+} °C)</div>', unsafe_allow_html=True)

        with col_amb_hum:
            st.markdown("<h3 style='text-align:center; color:#0077B6;'>% HUMEDAD</h3>", unsafe_allow_html=True)
            inp_hum = st.number_input("Ingresar Lectura (%H)", key=f"inp_hum_{lab_actual}", value=None, step=0.1)
            h_corregida, factor_h = None, 0.0
            if inp_hum is not None:
                tabla_h = cfg_hum.get("Correcciones", []) if cfg_hum else []
                h_corregida, factor_h = calcular_correccion_valor(inp_hum, tabla_h)

            val_disp_h = f"{h_corregida} %" if h_corregida is not None else "0.0 %"
            st.markdown(f'<div class="oval-corregido">Lectura Corregida: {val_disp_h} (Corr: {factor_h:+} %)</div>', unsafe_allow_html=True)

        st.write("")
        st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
        if st.button("HECHO", key=f"btn_hecho_amb_{lab_actual}"):
            conn = obtener_conexion()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mediciones_ambientales (fecha_hora, lab, temp_leida, temp_corr, hum_leida, hum_corr)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (obtener_hora_cdmx(), lab_actual, inp_temp, t_corregida, inp_hum, h_corregida))
            conn.commit()
            conn.close()
            st.success("💾 Mediciones ambientales guardadas.")
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state["sub_seccion_lab"] == "CONDICIONES DE EQUIPOS":
        st.markdown(f'<div class="section-title">CONDICIONES DE EQUIPOS - LAB {lab_actual}</div>', unsafe_allow_html=True)

        equipos_ce_lab = cargar_condiciones_equipos_db(lab_actual)

        if not equipos_ce_lab:
            st.info(f"No hay equipos configurados en el Laboratorio {lab_actual}.")
        else:
            cols_ce_grid = st.columns(min(len(equipos_ce_lab), 4))
            mediciones_resumen = []

            for idx_ce, eq_ce in enumerate(equipos_ce_lab):
                col_curr = cols_ce_grid[idx_ce % 4]
                with col_curr:
                    titulo_eq = f"{eq_ce['Tipo_Equipo']}-{eq_ce['Numero']}"
                    st.markdown(f"<div style='border: 1px solid #0077B6; border-radius: 4px; padding: 4px; text-align: center; font-weight: bold; background-color: #F0F8FF; color: #0077B6; margin-bottom: 5px; font-size: 0.9rem;'>{titulo_eq}</div>", unsafe_allow_html=True)

                    val_leido = st.number_input(f"Lectura Temp", key=f"ce_val_{eq_ce['id_ce']}", value=None, step=0.1)
                    val_corr, f_corr = None, 0.0
                    if val_leido is not None:
                        val_corr, f_corr = calcular_correccion_valor(val_leido, eq_ce.get("Correcciones", []))

                    v_text = f"{val_corr} °C" if val_corr is not None else "0.0 °C"
                    st.markdown(f'<div class="oval-corregido">{v_text}</div>', unsafe_allow_html=True)

                    if val_leido is not None:
                        mediciones_resumen.append({"Parametro": f"{titulo_eq} (Temp)", "Lectura": f"{val_leido} °C", "Corregida": f"{val_corr} °C"})

            st.write("")
            st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
            if st.button("HECHO", key=f"btn_hecho_ce_{lab_actual}"):
                conn = obtener_conexion()
                cursor = conn.cursor()
                for m in mediciones_resumen:
                    cursor.execute("""
                        INSERT INTO mediciones_equipos (fecha_hora, lab, parametro, lectura, corregida)
                        VALUES (?, ?, ?, ?, ?)
                    """, (obtener_hora_cdmx(), lab_actual, m["Parametro"], str(m["Lectura"]), str(m["Corregida"])))
                conn.commit()
                conn.close()
                st.success("💾 Mediciones de equipos guardadas.")
            st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("👈 Selecciona un laboratorio de la barra superior, presiona ➕ para dar de alta o ➖ para editar/eliminar registros.")
