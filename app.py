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

# 5. FUNCIONES AUXILIARES Y GENERACIÓN DE PDF
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

def generar_pdf_generico(titulo_reporte, df_datos):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    style_title = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor("#0077B6"),
        alignment=1,
        spaceAfter=12
    )
    
    elements = []
    elements.append(Paragraph("INSTITUTO NACIONAL DE ENFERMEDADES RESPIRATORIAS (INER)", style_title))
    elements.append(Paragraph("LABORATORIO DE INMUNOBIOLOGÍA DE LA TUBERCULOSIS", style_title))
    elements.append(Paragraph(titulo_reporte, style_title))
    elements.append(Spacer(1, 10))
    
    if not df_datos.empty:
        tabla_data = [df_datos.columns.tolist()] + df_datos.values.tolist()
        t = Table(tabla_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0077B6")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No hay registros disponibles para este reporte.", styles['Normal']))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def cargar_equipos(lab=None):
    conn = obtener_conexion()
    if lab:
        df = pd.read_sql_query("SELECT * FROM equipos WHERE ubicacion_lab = ?", conn, params=(lab,))
    else:
        df = pd.read_sql_query("SELECT * FROM equipos", conn)
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

import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ==========================================
# FUNCIÓN GENERADORA DE REPORTES PDF
# ==========================================
def generar_pdf_generico(titulo_reporte, df_datos, metadata=None):
    """
    Genera un archivo PDF dinámico con la ficha técnica detallada en el encabezado
    y las columnas: Fecha y Hora | Lectura / Temp | Registró (Usuario) | Verificó.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Estilos de texto
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=16,
        alignment=1, # Centrado
        textColor=colors.HexColor('#0077B6'),
        spaceAfter=12
    )
    
    style_meta_val = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontSize=9,
        leading=11
    )

    style_cell = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        alignment=1 # Centrado
    )

    style_header_cell = ParagraphStyle(
        'HeaderCellText',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        alignment=1,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    # 1. TÍTULO DEL REPORTE
    story.append(Paragraph(titulo_reporte.upper(), style_title))
    story.append(Spacer(1, 8))

    # 2. ENCABEZADO CON LA FICHA TÉCNICA (METADATOS DEL BOTÓN +)
    if metadata and isinstance(metadata, dict):
        meta_table_data = []
        keys = list(metadata.keys())
        
        # Agrupamos las propiedades en filas de 2 columnas (Clave: Valor | Clave: Valor)
        for i in range(0, len(keys), 2):
            k1 = keys[i]
            v1 = str(metadata[k1])
            cell_left = Paragraph(f"<b>{k1}:</b> {v1}", style_meta_val)
            
            if i + 1 < len(keys):
                k2 = keys[i+1]
                v2 = str(metadata[k2])
                cell_right = Paragraph(f"<b>{k2}:</b> {v2}", style_meta_val)
            else:
                cell_right = Paragraph("", style_meta_val)
                
            meta_table_data.append([cell_left, cell_right])

        t_meta = Table(meta_table_data, colWidths=[270, 270])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F8FF')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#0077B6')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BEE3F8')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 15))

    # 3. CONSTRUCCIÓN DE LA TABLA DE MEDICIONES
    headers = [
        Paragraph("FECHA Y HORA", style_header_cell),
        Paragraph("LECTURA / TEMP", style_header_cell),
        Paragraph("REGISTRÓ", style_header_cell),
        Paragraph("VERIFICÓ", style_header_cell)
    ]
    
    table_data = [headers]

    # Llenado de filas desde el DataFrame
    if df_datos is not None and not df_datos.empty:
        for _, row in df_datos.iterrows():
            f_hora = str(row.get("Fecha y Hora", row.get("fecha_hora", "")))
            lectura = str(row.get("Lectura Corregida", row.get("corregida", row.get("temp_corr", ""))))
            
            # Columnas preparadas (vacías por el momento)
            usuario = str(row.get("usuario", "")) 
            verifico = str(row.get("verifico", ""))

            table_data.append([
                Paragraph(f_hora, style_cell),
                Paragraph(lectura, style_cell),
                Paragraph(usuario, style_cell),
                Paragraph(verifico, style_cell)
            ])
    else:
        table_data.append([
            Paragraph("Sin datos", style_cell),
            Paragraph("Sin datos", style_cell),
            Paragraph("", style_cell),
            Paragraph("", style_cell)
        ])

    t_mediciones = Table(table_data, colWidths=[150, 130, 130, 130])
    t_mediciones.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0077B6')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))

    story.append(t_mediciones)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# SECCIÓN: REPORTES (PDF)
# ==========================================
if st.session_state["menu_principal"] == "REPORTES":
    st.markdown('<div class="section-title">GENERACIÓN DE REPORTES EN PDF</div>', unsafe_allow_html=True)
    
    cat_act = st.session_state["sub_categoria"]
    lab_act = st.session_state["lab_seleccionado"]
    
    if lab_act is None:
        st.info("👈 Por favor, selecciona un Laboratorio de la barra superior para consultar los reportes.")
    else:
        # --- FILTRO POR RANGO DE FECHAS ---
        st.markdown("**FILTRAR PERÍODO DEL REPORTE**")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_inicio = st.date_input("Fecha Inicio", value=pd.to_datetime("today") - pd.Timedelta(days=30), key="rep_f_inicio")
        with col_f2:
            fecha_fin = st.date_input("Fecha Fin", value=pd.to_datetime("today"), key="rep_f_fin")

        # Formatear fechas para la consulta SQL (YYYY-MM-DD)
        f_inicio_str = f"{fecha_inicio} 00:00:00"
        f_fin_str = f"{fecha_fin} 23:59:59"

        st.markdown("---")
        conn = obtener_conexion()
        cols_rep = st.columns(4)
        c_idx = 0

        # --- A. REPORTES DE EQUIPOS DE USO ---
        if cat_act == "EQUIPOS":
            equipos_registrados = pd.read_sql_query(
                "SELECT * FROM equipos WHERE ubicacion_lab = ?", conn, params=(lab_act,)
            ).to_dict(orient="records")
            
            if not equipos_registrados:
                st.warning(f"No hay equipos registrados en el Lab {lab_act}.")
            else:
                for eq in equipos_registrados:
                    meta_eq = {
                        "Tipo de Equipo": eq['tipo'],
                        "Número": eq['numero'],
                        "Marca": eq['marca'],
                        "Modelo": eq['modelo'],
                        "Serie": eq['serie'],
                        "Inventario": eq['inventario'],
                        "Ubicación": f"Laboratorio {eq['ubicacion_lab']}",
                        "Período": f"{fecha_inicio} al {fecha_fin}"
                    }
                    
                    with cols_rep[c_idx % 4]:
                        df_usos = pd.read_sql_query(
                            '''SELECT fecha_hora_cdmx AS "Fecha y Hora", accion AS "Lectura Corregida" 
                               FROM registros_uso 
                               WHERE equipo_id = ? AND fecha_hora_cdmx BETWEEN ? AND ?''', 
                            conn, 
                            params=(eq['id'], f_inicio_str, f_fin_str)
                        )
                        
                        pdf_bytes = generar_pdf_generico(f"BITÁCORA DE USO: {eq['tipo']}-{eq['numero']}", df_usos, metadata=meta_eq)
                        
                        st.download_button(
                            label=f"📄 PDF: {eq['tipo']}-{eq['numero']}",
                            data=pdf_bytes,
                            file_name=f"Reporte_Uso_{eq['id']}_{fecha_inicio}_{fecha_fin}.pdf",
                            mime="application/pdf",
                            key=f"dl_eq_{eq['id']}"
                        )
                    c_idx += 1

        # --- B. REPORTES DE CONDICIONES AMBIENTALES ---
        elif cat_act == "CONDICIONES AMBIENTALES":
            meta_amb = {
                "Área Monitorizada": f"Laboratorio {lab_act}",
                "Parámetros": "Temperatura y Humedad Relativa",
                "Frecuencia de Registro": "Diaria",
                "Período": f"{fecha_inicio} al {fecha_fin}"
            }
            
            df_amb = pd.read_sql_query(
                '''SELECT fecha_hora AS "Fecha y Hora", ("Temp: " || temp_corr || " °C | Hum: " || hum_corr || " %") AS "Lectura Corregida" 
                   FROM mediciones_ambientales 
                   WHERE lab = ? AND fecha_hora BETWEEN ? AND ?''', 
                conn, 
                params=(lab_act, f_inicio_str, f_fin_str)
            )
            
            with cols_rep[0]:
                pdf_bytes_amb = generar_pdf_generico(f"CONDICIONES AMBIENTALES - LAB {lab_act}", df_amb, metadata=meta_amb)
                st.download_button(
                    label=f"📄 PDF: AMBIENTAL LAB {lab_act}",
                    data=pdf_bytes_amb,
                    file_name=f"Reporte_Ambiental_Lab_{lab_act}_{fecha_inicio}_{fecha_fin}.pdf",
                    mime="application/pdf",
                    key=f"dl_amb_{lab_act}"
                )

        # --- C. REPORTES DE CONDICIONES DE EQUIPOS ---
        elif cat_act == "CONDICIONES DE EQUIPOS":
            ce_registrados = pd.read_sql_query(
                "SELECT * FROM config_condiciones_equipos WHERE ubicacion_lab = ?", conn, params=(lab_act,)
            ).to_dict(orient="records")
            
            if not ce_registrados:
                st.warning(f"No hay equipos de monitoreo configurados en el Lab {lab_act}.")
            else:
                for ce in ce_registrados:
                    meta_ce = {
                        "Tipo de Equipo": ce['tipo_equipo'],
                        "Número": ce['numero'],
                        "Marca": ce['marca'],
                        "Modelo": ce['modelo'],
                        "Serie": ce['serie'],
                        "Inventario": ce['inventario'],
                        "Ubicación": f"Laboratorio {ce['ubicacion_lab']}",
                        "Período": f"{fecha_inicio} al {fecha_fin}"
                    }
                    
                    with cols_rep[c_idx % 4]:
                        df_ce = pd.read_sql_query(
                            '''SELECT fecha_hora AS "Fecha y Hora", corregida AS "Lectura Corregida" 
                               FROM mediciones_equipos 
                               WHERE lab = ? AND parametro LIKE ? AND fecha_hora BETWEEN ? AND ?''', 
                            conn, 
                            params=(lab_act, f"%{ce['tipo_equipo']}-{ce['numero']}%", f_inicio_str, f_fin_str)
                        )
                        
                        pdf_bytes_ce = generar_pdf_generico(f"MONITOREO DE TEMPERATURA: {ce['tipo_equipo']}-{ce['numero']}", df_ce, metadata=meta_ce)
                        
                        st.download_button(
                            label=f"📄 PDF: {ce['tipo_equipo']}-{ce['numero']}",
                            data=pdf_bytes_ce,
                            file_name=f"Reporte_Condicion_{ce['id']}_{fecha_inicio}_{fecha_fin}.pdf",
                            mime="application/pdf",
                            key=f"dl_ce_{ce['id']}"
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
        
        # ----------------------------------------------------
        # 1. EDITAR / ELIMINAR: EQUIPOS
        # ----------------------------------------------------
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
                    st.markdown(f'<div class="section-title">EDITANDO EQUIPO DE USO: {eq_target["id"]}</div>', unsafe_allow_html=True)
                    
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
                    st.write("**UBICACIÓN (SELECCIONAR LABORATORIO)**")
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

        # ----------------------------------------------------
        # 2. EDITAR / ELIMINAR: CONDICIONES AMBIENTALES
        # ----------------------------------------------------
        elif st.session_state["sub_categoria"] == "CONDICIONES AMBIENTALES":
            st.markdown('<div class="section-title">SELECCIONA UNA CONFIGURACIÓN AMBIENTAL PARA EDITAR O ELIMINAR</div>', unsafe_allow_html=True)
            conn = obtener_conexion()
            configs_amb = pd.read_sql_query("SELECT * FROM config_ambientales", conn).to_dict(orient="records")
            conn.close()

            if not configs_amb:
                st.info("No hay configuraciones ambientales registradas.")
            else:
                cols_grid = st.columns(4)
                for idx, ca in enumerate(configs_amb):
                    with cols_grid[idx % 4]:
                        lbl_btn = f"{ca['tipo']} - Lab {ca['ubicacion_lab']}"
                        btn_key = f"btn_sel_amb_{ca['id']}"
                        if st.session_state["item_editar_id"] == ca["id"]:
                            aplicar_estilo_seleccion(btn_key)
                        if st.button(lbl_btn, key=btn_key):
                            st.session_state["item_editar_id"] = ca["id"]
                            st.rerun()

            if st.session_state["item_editar_id"]:
                ca_target = next((c for c in configs_amb if c["id"] == st.session_state["item_editar_id"]), None)
                if ca_target:
                    st.markdown("---")
                    st.markdown(f'<div class="section-title">EDITANDO CONFIGURACIÓN AMBIENTAL ({ca_target["tipo"]} - LAB {ca_target["ubicacion_lab"]})</div>', unsafe_allow_html=True)
                    
                    # Recuperar rangos actuales de la BD
                    entidad_id = f"AMB_{ca_target['ubicacion_lab']}_{ca_target['tipo']}"
                    conn = obtener_conexion()
                    df_rangos_bd = pd.read_sql_query("SELECT rango AS Rango, correccion AS Corrección FROM correcciones_rangos WHERE entidad_id = ?", conn, params=(entidad_id,))
                    conn.close()

                    if df_rangos_bd.empty:
                        rangos_default = ["10 - 20", "20.1 - 30", "30.1 - 40", "40.1 - 50", "50.1 - 60", "60.1 - 70", "70.1 - 80", "80.1 - 100"] if ca_target["tipo"] == "%H" else ["10 - 15", "15.1 - 20", "20.1 - 25", "25.1 - 30", "30.1 - 35"]
                        df_rangos_bd = pd.DataFrame({"Rango": rangos_default, "Corrección": [0.0] * len(rangos_default)})

                    ca_tipo, ca_rangos, ca_inst, ca_corr = st.columns([1.2, 1.2, 2, 3.5])
                    with ca_tipo:
                        st.write("**TIPO**")
                        tipo_amb_ed = st.selectbox("Tipo", ["TEMP", "%H"], index=0 if ca_target["tipo"] == "TEMP" else 1, key="ed_ca_tipo")
                    with ca_rangos:
                        st.write("**RANGOS**")
                        min_ed = st.text_input("MIN", value=str(ca_target["val_min"]), key="ed_ca_min")
                        max_ed = st.text_input("MAX", value=str(ca_target["val_max"]), key="ed_ca_max")
                    with ca_inst:
                        st.write("**INSTRUMENTO MEDICIÓN**")
                        inst_ed = st.text_area("Descripción / Código", value=str(ca_target["instrumento"]), key="ed_ca_inst")
                    with ca_corr:
                        st.write("**CORRECCIÓN (TABLA DE VALORES)**")
                        tabla_corr_amb_ed = st.data_editor(df_rangos_bd, hide_index=True, use_container_width=True, key="ed_editor_corr_amb")

                    st.write("")
                    st.write("**UBICACIÓN (LABORATORIO)**")
                    lab_amb_ed = st.selectbox("Laboratorio", labs_lista, index=labs_lista.index(ca_target["ubicacion_lab"]) if ca_target["ubicacion_lab"] in labs_lista else 0, key="ed_ca_lab")

                    st.write("")
                    col_h, col_e = st.columns(2)
                    with col_h:
                        st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
                        if st.button("HECHO (GUARDAR CAMBIOS)", key="btn_save_edit_amb"):
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE config_ambientales
                                SET tipo = ?, val_min = ?, val_max = ?, instrumento = ?, ubicacion_lab = ?
                                WHERE id = ?
                            """, (tipo_amb_ed, min_ed, max_ed, inst_ed, lab_amb_ed, ca_target["id"]))

                            new_entidad_id = f"AMB_{lab_amb_ed}_{tipo_amb_ed}"
                            cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ? OR entidad_id = ?", (entidad_id, new_entidad_id))
                            for _, fila in tabla_corr_amb_ed.iterrows():
                                cursor.execute("INSERT INTO correcciones_rangos (entidad_id, rango, correccion) VALUES (?, ?, ?)", (new_entidad_id, str(fila["Rango"]), float(fila["Corrección"])))
                            conn.commit()
                            conn.close()
                            st.session_state["item_editar_id"] = None
                            st.success("✅ Cambios en configuración ambiental guardados.")
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                    with col_e:
                        st.markdown('<div class="btn-eliminar">', unsafe_allow_html=True)
                        if st.button("ELIMINAR CONFIGURACIÓN", key="btn_del_amb"):
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM config_ambientales WHERE id = ?", (ca_target["id"],))
                            cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ?", (entidad_id,))
                            conn.commit()
                            conn.close()
                            st.session_state["item_editar_id"] = None
                            st.success("🗑️ Configuración ambiental eliminada.")
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

        # ----------------------------------------------------
        # 3. EDITAR / ELIMINAR: CONDICIONES DE EQUIPOS
        # ----------------------------------------------------
        elif st.session_state["sub_categoria"] == "CONDICIONES DE EQUIPOS":
            st.markdown('<div class="section-title">SELECCIONA UN EQUIPO DE MONITOREO PARA EDITAR O ELIMINAR</div>', unsafe_allow_html=True)
            conn = obtener_conexion()
            configs_ce = pd.read_sql_query("SELECT * FROM config_condiciones_equipos", conn).to_dict(orient="records")
            conn.close()

            if not configs_ce:
                st.info("No hay equipos de monitoreo configurados.")
            else:
                cols_grid = st.columns(4)
                for idx, ce in enumerate(configs_ce):
                    with cols_grid[idx % 4]:
                        lbl_btn = f"{ce['tipo_equipo']}-{ce['numero']} (Lab {ce['ubicacion_lab']})"
                        btn_key = f"btn_sel_ce_{ce['id']}"
                        if st.session_state["item_editar_id"] == ce["id"]:
                            aplicar_estilo_seleccion(btn_key)
                        if st.button(lbl_btn, key=btn_key):
                            st.session_state["item_editar_id"] = ce["id"]
                            st.rerun()

            if st.session_state["item_editar_id"]:
                ce_target = next((c for c in configs_ce if c["id"] == st.session_state["item_editar_id"]), None)
                if ce_target:
                    st.markdown("---")
                    st.markdown(f'<div class="section-title">EDITANDO EQUIPO DE MONITOREO: {ce_target["id"]}</div>', unsafe_allow_html=True)
                    
                    conn = obtener_conexion()
                    df_ce_rangos_bd = pd.read_sql_query("SELECT rango AS Rango, correccion AS Corrección FROM correcciones_rangos WHERE entidad_id = ?", conn, params=(ce_target["id"],))
                    conn.close()

                    if df_ce_rangos_bd.empty:
                        t_act = ce_target["tipo_equipo"]
                        r_list = ["-25 a -20", "-19.9 a -15", "-14.9 a -10"] if t_act == "CONG" else (["2 a 5", "5.1 a 8", "8.1 a 10"] if t_act == "REFR" else (["36.0 a 37.5", "4.5 a 5.5"] if t_act == "1CO2" else ["-85 a -80", "-79.9 a -70", "-69.9 a -60"]))
                        df_ce_rangos_bd = pd.DataFrame({"Rango": r_list, "Corrección": [0.0] * len(r_list)})

                    ce_tipo, ce_datos, ce_corr = st.columns([1.2, 3.5, 3.5])
                    with ce_tipo:
                        st.write("**TIPO EQUIPO**")
                        opts_tce = ["CONG", "REFR", "1CO2", "ULTRO"]
                        tce_ed = st.selectbox("Tipo", opts_tce, index=opts_tce.index(ce_target["tipo_equipo"]) if ce_target["tipo_equipo"] in opts_tce else 0, key="ed_ce_tipo")
                    with ce_datos:
                        st.write("**DATOS TÉCNICOS**")
                        d1, d2 = st.columns(2)
                        with d1:
                            ce_num_ed = st.text_input("NÚMERO", value=str(ce_target["numero"]), key="ed_ce_num")
                            ce_marca_ed = st.text_input("MARCA", value=str(ce_target["marca"]), key="ed_ce_marca")
                            ce_mod_ed = st.text_input("MODELO", value=str(ce_target["modelo"]), key="ed_ce_mod")
                        with d2:
                            ce_serie_ed = st.text_input("SERIE", value=str(ce_target["serie"]), key="ed_ce_serie")
                            ce_inv_ed = st.text_input("INVENTARIO", value=str(ce_target["inventario"]), key="ed_ce_inv")
                    with ce_corr:
                        st.write("**CORRECCIÓN (TABLA DE VALORES)**")
                        tabla_ce_corr_ed = st.data_editor(df_ce_rangos_bd, hide_index=True, use_container_width=True, key="ed_editor_ce_corr")

                    st.write("")
                    st.write("**UBICACIÓN (LABORATORIO)**")
                    ce_lab_ed = st.selectbox("Laboratorio", labs_lista, index=labs_lista.index(ce_target["ubicacion_lab"]) if ce_target["ubicacion_lab"] in labs_lista else 0, key="ed_ce_lab")

                    st.write("")
                    col_h, col_e = st.columns(2)
                    with col_h:
                        st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
                        if st.button("HECHO (GUARDAR CAMBIOS)", key="btn_save_edit_ce"):
                            nuevo_ce_id = f"{tce_ed}-{ce_num_ed}_{ce_lab_ed}"
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE config_condiciones_equipos
                                SET id = ?, tipo_equipo = ?, numero = ?, marca = ?, modelo = ?, serie = ?, inventario = ?, ubicacion_lab = ?
                                WHERE id = ?
                            """, (nuevo_ce_id, tce_ed, ce_num_ed, ce_marca_ed, ce_mod_ed, ce_serie_ed, ce_inv_ed, ce_lab_ed, ce_target["id"]))

                            cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ? OR entidad_id = ?", (ce_target["id"], nuevo_ce_id))
                            for _, fila in tabla_ce_corr_ed.iterrows():
                                cursor.execute("INSERT INTO correcciones_rangos (entidad_id, rango, correccion) VALUES (?, ?, ?)", (nuevo_ce_id, str(fila["Rango"]), float(fila["Corrección"])))
                            conn.commit()
                            conn.close()
                            st.session_state["item_editar_id"] = None
                            st.success("✅ Cambios guardados correctamente.")
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                    with col_e:
                        st.markdown('<div class="btn-eliminar">', unsafe_allow_html=True)
                        if st.button("ELIMINAR CONFIGURACIÓN", key="btn_del_ce"):
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM config_condiciones_equipos WHERE id = ?", (ce_target["id"],))
                            cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ?", (ce_target["id"],))
                            conn.commit()
                            conn.close()
                            st.session_state["item_editar_id"] = None
                            st.success("🗑️ Equipo de monitoreo eliminado.")
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
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
