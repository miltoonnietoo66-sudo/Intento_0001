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

# 3. CSS RESPONSIVO Y ESTILOS
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
    
    .marco-superior {
        height: 15px;
        width: 100%;
    }

    .banner-azul {
        background-color: #0077B6;
        color: #FFFFFF;
        font-weight: bold;
        text-align: center;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        font-size: clamp(1rem, 2.2vw, 1.4rem);
        letter-spacing: 1px;
        margin-bottom: 12px;
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
        font-size: clamp(0.75rem, 1.6vw, 0.9rem);
    }
    div[data-testid="stButton"] > button {
        color: #0077B6 !important;
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
if "menu_principal" not in st.session_state:
    st.session_state["menu_principal"] = "REGISTRAR"
if "lab_seleccionado" not in st.session_state:
    st.session_state["lab_seleccionado"] = None
if "sub_categoria" not in st.session_state:
    st.session_state["sub_categoria"] = "EQUIPOS"
if "modo_agregar" not in st.session_state:
    st.session_state["modo_agregar"] = False
if "modo_eliminar" not in st.session_state:
    st.session_state["modo_eliminar"] = False
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

# ==========================================
# 5. FUNCIONES AUXILIARES Y GENERACIÓN DE PDF (ACTUALIZADO)
# ==========================================
def generar_pdf_generico(titulo_reporte, df_datos, metadata=None):
    """
    Genera un PDF dinámico donde el encabezado contiene los datos técnicos
    registrados en el botón '➕' y la tabla incluye columnas para Usuario y Verificó.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=30, 
        leftMargin=30, 
        topMargin=30, 
        bottomMargin=30
    )
    styles = getSampleStyleSheet()
    
    style_title = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor("#0077B6"),
        alignment=1,
        spaceAfter=10
    )
    
    style_meta_label = ParagraphStyle(
        name='MetaLabel',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor("#023E8A")
    )
    
    style_meta_val = ParagraphStyle(
        name='MetaVal',
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.black
    )

    style_cell = ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=8,
        alignment=1
    )

    elements = []
    
    # 1. TÍTULO DEL REPORTE
    elements.append(Paragraph(titulo_reporte.upper(), style_title))
    elements.append(Spacer(1, 5))
    
    # 2. ENCABEZADO CON LA INFORMACIÓN DEL BOTÓN (+)
    if metadata:
        meta_table_data = []
        keys = list(metadata.keys())
        # Organizar metadatos en 2 columnas
        for i in range(0, len(keys), 2):
            k1 = keys[i]
            v1 = str(metadata[k1]) if metadata[k1] is not None else ""
            
            if i + 1 < len(keys):
                k2 = keys[i+1]
                v2 = str(metadata[k2]) if metadata[k2] is not None else ""
                row = [
                    Paragraph(f"<b>{k1}:</b>", style_meta_label),
                    Paragraph(v1, style_meta_val),
                    Paragraph(f"<b>{k2}:</b>", style_meta_label),
                    Paragraph(v2, style_meta_val)
                ]
            else:
                row = [
                    Paragraph(f"<b>{k1}:</b>", style_meta_label),
                    Paragraph(v1, style_meta_val),
                    "", ""
                ]
            meta_table_data.append(row)
            
        t_meta = Table(meta_table_data, colWidths=[100, 170, 100, 170])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0F8FF")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0077B6")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D0E1F9")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_meta)
        elements.append(Spacer(1, 15))

    # 3. TABLA DE REGISTROS CON COLUMNAS: FECHA/HORA, LECTURA, USUARIO Y VERIFICÓ
    if not df_datos.empty:
        # Asegurar columnas fijas para Usuario y Verificó
        if "Usuario" not in df_datos.columns:
            df_datos["Usuario"] = ""
        if "Verificó" not in df_datos.columns:
            df_datos["Verificó"] = ""

        headers = df_datos.columns.tolist()
        tabla_data = [[Paragraph(f"<b>{h}</b>", style_cell) for h in headers]]
        
        for _, row in df_datos.iterrows():
            row_cells = []
            for col in headers:
                val = str(row[col]) if row[col] is not None else ""
                row_cells.append(Paragraph(val, style_cell))
            tabla_data.append(row_cells)

        t_datos = Table(tabla_data, colWidths=[150, 150, 120, 120])
        t_datos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0077B6")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ]))
        elements.append(t_datos)
    else:
        elements.append(Paragraph("No hay registros disponibles para este reporte.", styles['Normal']))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# FILA 1: MARCO SUPERIOR
# ==========================================
st.markdown('<div class="marco-superior"></div>', unsafe_allow_html=True)

# ==========================================
# FILA 2: BANNER AZUL INSTITUCIONAL
# ==========================================
st.markdown('<div class="banner-azul">LABORATORIO DE INMUNOBIOLOGÍA DE LA TUBERCULOSIS</div>', unsafe_allow_html=True)

# ==========================================
# FILA 3: MENÚ PRINCIPAL Y RELOJ
# ==========================================
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns([1.5, 1.5, 1.5, 1.5, 3])

with col_m1:
    if st.session_state["menu_principal"] == "REPORTES":
        aplicar_estilo_seleccion("btn_menu_reportes")
    if st.button("REPORTES", key="btn_menu_reportes"):
        st.session_state["menu_principal"] = "REPORTES"
        st.rerun()

with col_m2:
    if st.session_state["menu_principal"] == "REGISTRAR":
        aplicar_estilo_seleccion("btn_menu_registrar")
    if st.button("REGISTRAR", key="btn_menu_registrar"):
        st.session_state["menu_principal"] = "REGISTRAR"
        st.rerun()

with col_m3:
    if st.session_state["menu_principal"] == "VERIFICAR":
        aplicar_estilo_seleccion("btn_menu_verificar")
    if st.button("VERIFICAR", key="btn_menu_verificar"):
        st.session_state["menu_principal"] = "VERIFICAR"
        st.rerun()

with col_m4:
    if st.session_state["menu_principal"] == "USUARIO":
        aplicar_estilo_seleccion("btn_menu_usuario")
    if st.button("USUARIO", key="btn_menu_usuario"):
        st.session_state["menu_principal"] = "USUARIO"
        st.rerun()

with col_m5:
    st.markdown(f'<div class="reloj-box">🕒 CDMX: {obtener_hora_cdmx()}</div>', unsafe_allow_html=True)

st.write("")

# ==========================================
# FILA 4: BARRA DE NAVEGACIÓN DE LABORATORIOS (GLOBAL)
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

        if st.session_state["lab_seleccionado"] == lab and not st.session_state["modo_agregar"] and not st.session_state["modo_eliminar"]:
            aplicar_estilo_seleccion(f"btn_f2_{lab}")

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
            elif lab == "MENOS":
                st.session_state["modo_eliminar"] = True
                st.session_state["modo_agregar"] = False
                st.session_state["lab_seleccionado"] = None
                st.session_state["item_editar_id"] = None
            else:
                st.session_state["lab_seleccionado"] = lab
                st.session_state["modo_agregar"] = False
                st.session_state["modo_eliminar"] = False
                st.session_state["equipo_activo_id"] = None
            st.rerun()

# ==========================================
# FILA 5: TRES BOTONES DE RUBROS (GLOBAL)
# ==========================================
col_cat1, col_cat2, col_cat3 = st.columns([1, 1, 1])

with col_cat1:
    if st.session_state["sub_categoria"] == "EQUIPOS":
        aplicar_estilo_seleccion("btn_cat_equipos")
    if st.button("EQUIPOS", key="btn_cat_equipos"):
        st.session_state["sub_categoria"] = "EQUIPOS"
        st.session_state["item_editar_id"] = None
        st.rerun()

with col_cat2:
    if st.session_state["sub_categoria"] == "CONDICIONES AMBIENTALES":
        aplicar_estilo_seleccion("btn_cat_amb")
    if st.button("CONDICIONES AMBIENTALES", key="btn_cat_amb"):
        st.session_state["sub_categoria"] = "CONDICIONES AMBIENTALES"
        st.session_state["item_editar_id"] = None
        st.rerun()

with col_cat3:
    if st.session_state["sub_categoria"] == "CONDICIONES DE EQUIPOS":
        aplicar_estilo_seleccion("btn_cat_ce")
    if st.button("CONDICIONES DE EQUIPOS", key="btn_cat_ce"):
        st.session_state["sub_categoria"] = "CONDICIONES DE EQUIPOS"
        st.session_state["item_editar_id"] = None
        st.rerun()

st.markdown("---")

# ==========================================
# SECCIÓN: REPORTES (ACTUALIZADO CON METADATOS)
# ==========================================
if st.session_state["menu_principal"] == "REPORTES":
    lab_act = st.session_state["lab_seleccionado"]
    cat_act = st.session_state["sub_categoria"]
    
    if lab_act is None or st.session_state["modo_agregar"] or st.session_state["modo_eliminar"]:
        st.info("👈 Selecciona un laboratorio en la barra superior para descargar reportes en PDF.")
    else:
        st.markdown(f'<div class="section-title">REPORTES DE {cat_act} - LABORATORIO {lab_act}</div>', unsafe_allow_html=True)
        conn = obtener_conexion()
        cols_rep = st.columns(4)
        c_idx = 0

        # --- 1. REPORTES DE EQUIPOS ---
        if cat_act == "EQUIPOS":
            equipos_registrados = pd.read_sql_query("SELECT * FROM equipos WHERE ubicacion_lab = ?", conn, params=(lab_act,)).to_dict(orient="records")
            if not equipos_registrados:
                st.warning(f"No hay equipos de uso registrados en el Lab {lab_act}.")
            else:
                for eq in equipos_registrados:
                    eq_id = eq["id"]
                    nombre_btn = f"📄 PDF: USO {eq['tipo']}-{eq['numero']}"
                    
                    # Ficha técnica capturada en (+)
                    meta_eq = {
                        "Tipo de Equipo": eq['tipo'],
                        "Número": eq['numero'],
                        "Marca": eq['marca'],
                        "Modelo": eq['modelo'],
                        "N° de Serie": eq['serie'],
                        "Inventario": eq['inventario'],
                        "Ubicación": f"Laboratorio {eq['ubicacion_lab']}",
                        "Fecha de Alta": eq['fecha_hora']
                    }
                    
                    with cols_rep[c_idx % 4]:
                        df_uso = pd.read_sql_query(
                            'SELECT fecha_hora_cdmx as "Fecha y Hora", accion as "Acción / Evento" FROM registros_uso WHERE equipo_id = ?', 
                            conn, 
                            params=(eq_id,)
                        )
                        pdf_bytes = generar_pdf_generico(f"BITÁCORA DE USO - EQUIPO {eq['tipo']}-{eq['numero']}", df_uso, metadata=meta_eq)
                        st.download_button(
                            label=nombre_btn,
                            data=pdf_bytes,
                            file_name=f"Reporte_Uso_{eq_id}.pdf",
                            mime="application/pdf",
                            key=f"dl_eq_{eq_id}"
                        )
                    c_idx += 1

        # --- 2. REPORTES DE CONDICIONES AMBIENTALES ---
        elif cat_act == "CONDICIONES AMBIENTALES":
            amb_registrados = pd.read_sql_query("SELECT * FROM config_ambientales WHERE ubicacion_lab = ?", conn, params=(lab_act,)).to_dict(orient="records")
            if not amb_registrados:
                st.warning(f"No hay configuraciones ambientales para el Lab {lab_act}.")
            else:
                # Tomar la última configuración registrada para los metadatos
                cfg = amb_registrados[-1]
                meta_amb = {
                    "Tipo de Medición": cfg['tipo'],
                    "Rango Permitido": f"{cfg['val_min']} a {cfg['val_max']}",
                    "Instrumento": cfg['instrumento'],
                    "Ubicación": f"Laboratorio {cfg['ubicacion_lab']}"
                }
                
                with cols_rep[0]:
                    df_amb = pd.read_sql_query(
                        'SELECT fecha_hora as "Fecha y Hora", temp_corr as "Temp (°C)", hum_corr as "Humedad (%)" FROM mediciones_ambientales WHERE lab = ?', 
                        conn, 
                        params=(lab_act,)
                    )
                    pdf_bytes_amb = generar_pdf_generico(f"REGISTRO DE CONDICIONES AMBIENTALES - LAB {lab_act}", df_amb, metadata=meta_amb)
                    st.download_button(
                        label=f"📄 PDF: CONDICIONES AMBIENTALES",
                        data=pdf_bytes_amb,
                        file_name=f"Reporte_Ambiental_Lab_{lab_act}.pdf",
                        mime="application/pdf",
                        key=f"dl_amb_{lab_act}"
                    )

        # --- 3. REPORTES DE CONDICIONES DE EQUIPOS ---
        elif cat_act == "CONDICIONES DE EQUIPOS":
            ce_registrados = pd.read_sql_query("SELECT * FROM config_condiciones_equipos WHERE ubicacion_lab = ?", conn, params=(lab_act,)).to_dict(orient="records")
            if not ce_registrados:
                st.warning(f"No hay equipos con monitoreo de condiciones configurados en el Lab {lab_act}.")
            else:
                for ce in ce_registrados:
                    ce_id = ce["id"]
                    nombre_ce_btn = f"📄 PDF: TEMP {ce['tipo_equipo']}-{ce['numero']}"
                    
                    # Ficha técnica del equipo de monitoreo capturada en (+)
                    meta_ce = {
                        "Tipo Equipo": ce['tipo_equipo'],
                        "Número": ce['numero'],
                        "Marca": ce['marca'],
                        "Modelo": ce['modelo'],
                        "Serie": ce['serie'],
                        "Inventario": ce['inventario'],
                        "Ubicación": f"Laboratorio {ce['ubicacion_lab']}"
                    }
                    
                    with cols_rep[c_idx % 4]:
                        df_ce = pd.read_sql_query(
                            'SELECT fecha_hora as "Fecha y Hora", corregida as "Lectura Corregida" FROM mediciones_equipos WHERE lab = ? AND parametro LIKE ?', 
                            conn, 
                            params=(lab_act, f"%{ce['tipo_equipo']}-{ce['numero']}%")
                        )
                        pdf_bytes_ce = generar_pdf_generico(f"CONTROL DE TEMPERATURA - {ce['tipo_equipo']}-{ce['numero']}", df_ce, metadata=meta_ce)
                        st.download_button(
                            label=nombre_ce_btn,
                            data=pdf_bytes_ce,
                            file_name=f"Reporte_Condicion_{ce_id}.pdf",
                            mime="application/pdf",
                            key=f"dl_ce_{ce_id}"
                        )
                    c_idx += 1

        conn.close()
# ==========================================
# SECCIÓN: VERIFICAR Y USUARIO
# ==========================================
elif st.session_state["menu_principal"] == "VERIFICAR":
    st.info(f"🔍 Auditoría y Verificación de Bitácoras ({st.session_state['sub_categoria']}): Módulo activo.")

elif st.session_state["menu_principal"] == "USUARIO":
    st.info("👤 Módulo de USUARIO: Gestión de sesiones, firmas digitales e identificadores del personal.")

# ==========================================
# SECCIÓN: REGISTRAR
# ==========================================
elif st.session_state["menu_principal"] == "REGISTRAR":
    
    # MÓDULO ➕ (AGREGAR ALTA)
    if st.session_state["modo_agregar"]:
        if st.session_state["sub_categoria"] == "EQUIPOS":
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

        elif st.session_state["sub_categoria"] == "CONDICIONES AMBIENTALES":
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

        elif st.session_state["sub_categoria"] == "CONDICIONES DE EQUIPOS":
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

    # MÓDULO ➖ (EDITAR O ELIMINAR)
    elif st.session_state["modo_eliminar"]:
        if st.session_state["sub_categoria"] == "EQUIPOS":
            st.markdown('<div class="section-title">SELECCIONA UN EQUIPO PARA EDITAR O ELIMINAR</div>', unsafe_allow_html=True)
            todos_equipos = cargar_equipos()
            if not todos_equipos:
                st.info("No hay equipos de uso registrados.")
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

        else:
            st.info(f"Selecciona un registro de {st.session_state['sub_categoria']} para dar de baja o actualizar.")

    # VISTA REGULAR (SELECCIÓN DE LABORATORIO)
    elif st.session_state["lab_seleccionado"] is not None:
        lab_actual = st.session_state["lab_seleccionado"]

        if st.session_state["sub_categoria"] == "EQUIPOS":
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

        elif st.session_state["sub_categoria"] == "CONDICIONES AMBIENTALES":
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

        elif st.session_state["sub_categoria"] == "CONDICIONES DE EQUIPOS":
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
