import io
import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Configuración base
st.set_page_config(page_title="Sistema INER - Gestión", layout="wide")
TZ_CDMX = ZoneInfo("America/Mexico_City")

# [MANTENER EL MISMO CSS DE LA VERSIÓN ANTERIOR...]
# (He omitido el CSS aquí para brevedad, pero asegúrate de conservar el que ya tienes en tu app.py)

# Funciones de utilidad
def obtener_hora_cdmx():
    return datetime.now(TZ_CDMX).strftime("%d/%m/%Y %H:%M:%S")

def parsear_rango(rango_str):
    """Convierte un string como '10 - 15' a (10.0, 15.0)"""
    if "N/A" in rango_str: return None, None
    try:
        partes = rango_str.replace('°C', '').replace('%', '').split('-')
        return float(partes[0].strip()), float(partes[1].strip())
    except: return None, None

def calcular_correccion(valor, lista_correcciones):
    """Busca el valor de corrección según el rango registrado"""
    try:
        val_float = float(valor)
        for item in lista_correcciones:
            rango_str = item.get("Rango") or item.get("Rango %H") or item.get("Rango TEMP (°C)")
            corr_str = item.get("Corrección")
            if rango_str and "N/A" not in rango_str:
                min_r, max_r = parsear_rango(rango_str)
                if min_r and max_r and min_r <= val_float <= max_r:
                    return val_float + float(corr_str) if corr_str else val_float
        return val_float
    except: return valor

# [AQUÍ VA TU LÓGICA DE PDF GENERATOR...]
def generar_pdf_registro(tipo, metadata, valor_medido, valor_corregido):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Encabezado (Metadata)
    elements.append(Paragraph(f"REGISTRO DE {tipo}", styles['Title']))
    elements.append(Spacer(1, 12))
    
    info_data = [
        ["Campo", "Detalle"],
        ["Fecha", obtener_hora_cdmx()],
        ["Equipo/Inst.", metadata.get('Tipo') or metadata.get('Tipo_Equipo')],
        ["Marca/Modelo", f"{metadata.get('Marca', '')} / {metadata.get('Modelo', '')}"],
        ["Ubicación", metadata.get('Ubicacion_Lab', '')]
    ]
    elements.append(Table(info_data))
    elements.append(Spacer(1, 20))
    
    # Resultados
    elements.append(Paragraph(f"Valor Medido: {valor_medido}", styles['Normal']))
    elements.append(Paragraph(f"<b>LECTURA CORREGIDA: {valor_corregido}</b>", styles['Heading2']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- NAVEGACIÓN LAB ---
if st.session_state.get("lab_seleccionado"):
    lab = st.session_state["lab_seleccionado"]
    
    # Fila 3: botones de acción
    col3_1, col3_2, col3_3 = st.columns(3)
    
    with col3_1:
        if st.button("EQUIPOS"): st.session_state["sub_seccion_lab"] = "USO"
    with col3_2:
        if st.button("COND. AMBIENTALES"): st.session_state["sub_seccion_lab"] = "AMB"
    with col3_3:
        if st.button("COND. EQUIPOS"): st.session_state["sub_seccion_lab"] = "CE"

    # Lógica de Fila 4 y Registro (Ejemplo para Condiciones Ambientales)
    if st.session_state.get("sub_seccion_lab") == "AMB":
        st.subheader(f"Registro Ambiental - Lab {lab}")
        
        # Obtener configuración previa guardada en "+"
        config_amb = [a for a in st.session_state.get("condiciones_ambientales_db", []) if a["Ubicacion_Lab"] == lab]
        
        if config_amb:
            # Selector de equipo/instrumento
            idx = st.selectbox("Seleccionar Instrumento", range(len(config_amb)), format_func=lambda i: config_amb[i]['Instrumento'])
            instrumento = config_amb[idx]
            
            # Entrada de datos (Fila 4)
            valor_usuario = st.text_input("Ingrese Lectura actual")
            
            # Cálculo de corrección (El círculo naranja)
            if valor_usuario:
                corr_val = calcular_correccion(valor_usuario, instrumento['Correcciones'])
                st.info(f"### Lectura Corregida: {corr_val}")
                
                if st.button("HECHO"):
                    # Guardar registro
                    pdf = generar_pdf_registro("CONDICIONES AMBIENTALES", instrumento, valor_usuario, corr_val)
                    st.success("Registro guardado.")
                    st.download_button("Descargar PDF Registro", pdf, file_name="registro.pdf")
        else:
            st.warning("Primero configure las condiciones ambientales en el menú '+'")
