import io
import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image

# Módulos para generación de PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ---------------------------------------------------------
# 1. CONFIGURACIÓN INICIAL Y ESTADOS DE SESIÓN
# ---------------------------------------------------------
st.set_page_config(page_title="Sistema INER - Gestión", layout="wide")
TZ_CDMX = ZoneInfo("America/Mexico_City")

if "equipos_db" not in st.session_state:
    st.session_state["equipos_db"] = []

if "condiciones_ambientales_db" not in st.session_state:
    st.session_state["condiciones_ambientales_db"] = []

if "condiciones_equipos_db" not in st.session_state:
    st.session_state["condiciones_equipos_db"] = []

if "registros_guardados" not in st.session_state:
    st.session_state["registros_guardados"] = []

if "logo_iner" not in st.session_state:
    st.session_state["logo_iner"] = None

if "modal_tipo" not in st.session_state:
    st.session_state["modal_tipo"] = None

if "lab_seleccionado" not in st.session_state:
    st.session_state["lab_seleccionado"] = None

if "sub_seccion_lab" not in st.session_state:
    st.session_state["sub_seccion_lab"] = None

# ---------------------------------------------------------
# 2. ESTILOS CSS PERSONALIZADOS
# ---------------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .header-box {
        border: 2px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin-bottom: 20px;
        background-color: #161b22;
    }
    div.stButton > button {
        background-color: #00bcd4;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: bold;
        width: 100%;
        padding: 10px 0px;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #00acc1;
        color: white;
    }
    .btn-plus > button {
        background-color: #2196f3 !important;
        font-size: 24px !important;
        line-height: 1 !important;
    }
    .circle-orange {
        background-color: #161b22;
        border: 2px solid #ff9800;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        color: #ff9800;
        font-weight: bold;
        font-size: 1.2rem;
        margin-top: 10px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. FUNCIONES AUXILIARES Y CÁLCULOS
# ---------------------------------------------------------
def obtener_hora_cdmx():
    return datetime.now(TZ_CDMX).strftime("%d/%m/%Y %H:%M:%S")

def parsear_rango(rango_str):
    if not rango_str or "N/A" in str(rango_str):
        return None, None
    try:
        limpio = str(rango_str).replace('°C', '').replace('%', '').strip()
        partes = limpio.split('-')
        return float(partes[0].strip()), float(partes[1].strip())
    except:
        return None, None

def calcular_correccion(valor_ingresado, lista_correcciones):
    try:
        val_float = float(valor_ingresado)
        for item in lista_correcciones:
            rango_str = item.get("Rango") or item.get("Rango %H") or item.get("Rango TEMP (°C)") or item.get("Rango (°C)")
            corr_str = item.get("Corrección") or item.get("Corrección %H") or item.get("Corrección TEMP (°C)") or item.get("Corrección (°C)")
            
            if rango_str and "N/A" not in str(rango_str):
                min_r, max_r = parsear_rango(rango_str)
                if min_r is not None and max_r is not None:
                    if min_r <= val_float <= max_r:
                        factor = float(corr_str) if corr_str else 0.0
                        return round(val_float + factor, 2)
        return val_float
    except:
        return valor_ingresado

# ---------------------------------------------------------
# 4. GENERADOR DE REPORTES PDF
# ---------------------------------------------------------
def generar_pdf_registro(titulo_tipo, metadata_equipo, lecturas_dict):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#003366"),
        alignment=1
    )

    # Encabezado Institucional
    header_data = []
    if st.session_state["logo_iner"]:
        try:
            img_bytes = io.BytesIO()
            st.session_state["logo_iner"].save(img_bytes, format='PNG')
            img_bytes.seek(0)
            rl_img = RLImage(img_bytes, width=70, height=70)
            header_data = [[rl_img, Paragraph(f"<b>INSTITUTO NACIONAL DE ENFERMEDADES RESPIRATORIAS</b><br/>{titulo_tipo}", title_style)]]
        except:
            header_data = [[Paragraph(f"<b>INSTITUTO NACIONAL DE ENFERMEDADES RESPIRATORIAS</b><br/>{titulo_tipo}", title_style)]]
    else:
        header_data = [[Paragraph(f"<b>INSTITUTO NACIONAL DE ENFERMEDADES RESPIRATORIAS</b><br/>{titulo_tipo}", title_style)]]

    t_header = Table(header_data, colWidths=[80, 460] if len(header_data[0]) > 1 else [540])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 15))

    # Información del Equipo / Ubicación
    meta_rows = [["PARÁMETRO", "DETALLE REGLAMENTARIO"]]
    meta_rows.append(["Fecha y Hora de Registro", obtener_hora_cdmx()])
    
    for k, v in metadata_equipo.items():
        if k != "Correcciones" and isinstance(v, (str, int, float)):
            meta_rows.append([str(k).replace("_", " "), str(v)])

    t_meta = Table(meta_rows, colWidths=[200, 340])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 20))

    # Lecturas y Correcciones
    lec_rows = [["MEDICIÓN / SENSOR", "LECTURA BRUTA", "LECTURA CORREGIDA"]]
    for sensor, datos in lecturas_dict.items():
        lec_rows.append([str(sensor), str(datos['bruta']), str(datos['corregida'])])

    t_lec = Table(lec_rows, colWidths=[200, 170, 170])
    t_lec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#ff9800")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_lec)

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# 5. MODALES DE CONFIGURACIÓN (BOTÓN "+" Y TABLAS)
# ---------------------------------------------------------
@st.dialog("Configuración General")
def abrir_modal_configuracion():
    st.subheader("Opciones de Configuración")
    
    nuevo_logo = st.file_uploader("Cargar / Actualizar Logotipo INER", type=["png", "jpg", "jpeg"])
    if nuevo_logo:
        st.session_state["logo_iner"] = Image.open(nuevo_logo)
        st.success("Logotipo cargado exitosamente.")

    if st.session_state["logo_iner"]:
        st.image(st.session_state["logo_iner"], width=120)

    st.markdown("---")
    opcion = st.radio("Seleccione el elemento a registrar:", [
        "1. Registro de Equipos",
        "2. Condiciones Ambientales (Termohigrómetros)",
        "3. Condiciones de Equipos (Refrigeración/Termómetros)"
    ])

    if st.button("Continuar a Formulario"):
        if "1." in opcion: st.session_state["modal_tipo"] = "EQUIPOS"
        elif "2." in opcion: st.session_state["modal_tipo"] = "AMB"
        elif "3." in opcion: st.session_state["modal_tipo"] = "CE"
        st.rerun()

# --- Diálogos de Entrada Específicos ---
@st.dialog("Alta de Equipos")
def modal_alta_equipos():
    st.write("### Datos Generales del Equipo")
    tipo = st.text_input("Tipo de Equipo")
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    num_serie = st.text_input("Número de Serie")
    id_equipo = st.text_input("ID / Código Interno")
    ubicacion = st.text_input("Ubicación / Laboratorio")

    if st.button("Guardar Equipo"):
        if tipo and id_equipo:
            st.session_state["equipos_db"].append({
                "Tipo": tipo, "Marca": marca, "Modelo": modelo,
                "Serie": num_serie, "ID": id_equipo, "Ubicacion_Lab": ubicacion
            })
            st.session_state["modal_tipo"] = None
            st.success("Equipo registrado correctamente.")
            st.rerun()
        else:
            st.error("Por favor complete al menos el Tipo y el ID.")

@st.dialog("Alta de Condiciones Ambientales")
def modal_alta_ambientales():
    st.write("### Termohigrómetro e Instrumentos Ambientales")
    inst = st.text_input("Instrumento")
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    num_serie = st.text_input("Número de Serie")
    id_inst = st.text_input("ID Instrumento")
    ubicacion = st.text_input("Ubicación / Laboratorio")

    num_rangos = st.number_input("Número de Rangos de Calibración", min_value=1, max_value=10, value=3)
    
    st.write("#### Calibración de Humedad (%H)")
    df_h = st.data_editor(
        pd.DataFrame([{"Rango %H": "0 - 100", "Corrección %H": 0.0} for _ in range(num_rangos)]),
        num_rows="dynamic", key="editor_h"
    )

    st.write("#### Calibración de Temperatura (°C)")
    df_t = st.data_editor(
        pd.DataFrame([{"Rango TEMP (°C)": "0 - 50", "Corrección TEMP (°C)": 0.0} for _ in range(num_rangos)]),
        num_rows="dynamic", key="editor_t"
    )

    if st.button("Guardar Instrumento Ambiental"):
        st.session_state["condiciones_ambientales_db"].append({
            "Instrumento": inst, "Marca": marca, "Modelo": modelo,
            "Serie": num_serie, "ID": id_inst, "Ubicacion_Lab": ubicacion,
            "Correcciones_Humedad": df_h.to_dict('records'),
            "Correcciones_Temp": df_t.to_dict('records')
        })
        st.session_state["modal_tipo"] = None
        st.success("Configuración de ambiente guardada.")
        st.rerun()

@st.dialog("Alta de Condiciones de Equipos")
def modal_alta_condiciones_equipos():
    st.write("### Equipos de Frío / Sensores Internos")
    tipo_eq = st.text_input("Tipo de Equipo (ej. Ultra-congelador)")
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    num_serie = st.text_input("Número de Serie")
    id_eq = st.text_input("ID Equipo")
    ubicacion = st.text_input("Ubicación / Laboratorio")

    sensores = st.text_area("Lista de Sensores/Termómetros (separados por coma)", "Sensor Superior, Sensor Inferior")
    num_rangos = st.number_input("Número de Rangos de Calibración", min_value=1, max_value=10, value=2)

    df_ce = st.data_editor(
        pd.DataFrame([{"Rango (°C)": "-80 - -40", "Corrección (°C)": 0.0} for _ in range(num_rangos)]),
        num_rows="dynamic", key="editor_ce"
    )

    if st.button("Guardar Configuración de Equipo"):
        st.session_state["condiciones_equipos_db"].append({
            "Tipo_Equipo": tipo_eq, "Marca": marca, "Modelo": modelo,
            "Serie": num_serie, "ID": id_eq, "Ubicacion_Lab": ubicacion,
            "Sensores": [s.strip() for s in sensores.split(",") if s.strip()],
            "Correcciones": df_ce.to_dict('records')
        })
        st.session_state["modal_tipo"] = None
        st.success("Configuración guardada.")
        st.rerun()

# Evaluadores de estado del modal
if st.session_state["modal_tipo"] == "EQUIPOS": modal_alta_equipos()
elif st.session_state["modal_tipo"] == "AMB": modal_alta_ambientales()
elif st.session_state["modal_tipo"] == "CE": modal_alta_condiciones_equipos()

# ---------------------------------------------------------
# 6. ENCABEZADO Y FILA 1 DE BOTONES (LABORATORIOS Y "+")
# ---------------------------------------------------------
st.markdown("<div class='header-box'><h2>SISTEMA DE REGISTRO Y CONTROL DE LABORATORIOS</h2></div>", unsafe_allow_html=True)

col_l1, col_l2, col_l3, col_plus = st.columns([1, 1, 1, 0.3])

with col_l1:
    if st.button("LABORATORIO 1"):
        st.session_state["lab_seleccionado"] = "1"
        st.session_state["sub_seccion_lab"] = None

with col_l2:
    if st.button("LABORATORIO 2"):
        st.session_state["lab_seleccionado"] = "2"
        st.session_state["sub_seccion_lab"] = None

with col_l3:
    if st.button("LABORATORIO 3"):
        st.session_state["lab_seleccionado"] = "3"
        st.session_state["sub_seccion_lab"] = None

with col_plus:
    st.markdown("<div class='btn-plus'>", unsafe_allow_html=True)
    if st.button("+", key="btn_mas_global"):
        abrir_modal_configuracion()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 7. FILA 3 Y VISTAS DE REGISTRO EN PANTALLA
# ---------------------------------------------------------
if st.session_state["lab_seleccionado"]:
    lab = st.session_state["lab_seleccionado"]
    st.markdown(f"--- \n### 📍 Laboratorio Seleccionado: **Laboratorio {lab}**")

    # Fila 3: Botones principales según tu diagrama
    col3_1, col3_2, col3_3 = st.columns(3)
    
    with col3_1:
        if st.button("EQUIPOS (USO)", key="f3_eq"):
            st.session_state["sub_seccion_lab"] = "USO"
            
    with col3_2:
        if st.button("CONDICIONES AMBIENTALES", key="f3_amb"):
            st.session_state["sub_seccion_lab"] = "AMB"
            
    with col3_3:
        if st.button("CONDICIONES DE EQUIPOS", key="f3_ce"):
            st.session_state["sub_seccion_lab"] = "CE"

    st.markdown("<br/>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # VISTA: REGISTRO DE USO DE EQUIPOS
    # -----------------------------------------------------
    if st.session_state["sub_seccion_lab"] == "USO":
        st.subheader("📌 Registro de Uso e Inspección de Equipos")
        
        eqs_lab = [e for e in st.session_state["equipos_db"] if str(e.get("Ubicacion_Lab")) == str(lab)]
        
        if not eqs_lab:
            st.info("No hay equipos configurados para este laboratorio. Presiona '+' para agregar uno.")
        else:
            for idx, eq in enumerate(eqs_lab):
                with st.expander(f"🔹 {eq['Tipo']} - ID: {eq['ID']} ({eq['Marca']} {eq['Modelo']})", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        usuario = st.text_input("Usuario / Técnico", key=f"u_eq_{idx}")
                    with c2:
                        obs = st.text_input("Observaciones de Operación", key=f"o_eq_{idx}")
                    with c3:
                        estado = st.selectbox("Estado", ["Correcto", "Con Falla", "Mantenimiento"], key=f"e_eq_{idx}")

                    if st.button("HECHO", key=f"btn_h_eq_{idx}"):
                        lecturas = {"Estado de Uso": {"bruta": estado, "corregida": estado}}
                        pdf_buf = generar_pdf_registro("REGISTRO DE USO DE EQUIPO", eq, lecturas)
                        
                        st.success("✅ Registro guardado.")
                        st.download_button(
                            label="📄 Descargar PDF de Registro",
                            data=pdf_buf,
                            file_name=f"Registro_Equipo_{eq['ID']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf",
                            key=f"dl_eq_{idx}"
                        )

    # -----------------------------------------------------
    # VISTA: CONDICIONES AMBIENTALES (IMAGEN 2 DEL BOCETO)
    # -----------------------------------------------------
    elif st.session_state["sub_seccion_lab"] == "AMB":
        st.subheader("🌡️ Registro de Condiciones Ambientales")
        
        amb_lab = [a for a in st.session_state["condiciones_ambientales_db"] if str(a.get("Ubicacion_Lab")) == str(lab)]
        
        if not amb_lab:
            st.info("No hay instrumentos ambientales configurados para este laboratorio. Presiona '+' para agregar.")
        else:
            for idx, inst in enumerate(amb_lab):
                st.markdown(f"#### Instrumento: **{inst['Instrumento']}** (ID: {inst['ID']})")
                
                col_t, col_h = st.columns(2)
                
                # Fila 4: Cajas de Entrada (Temperatura)
                with col_t:
                    st.markdown("**TEMPERATURA (°C)**")
                    val_t = st.text_input("Lectura Termohigrómetro (°C)", key=f"in_t_{idx}")
                    corr_t = calcular_correccion(val_t, inst.get("Correcciones_Temp", [])) if val_t else "--"
                    
                    # Círculo Naranja: Lectura Corregida
                    st.markdown(f"""
                        <div class='circle-orange'>
                            Lectura Corregida<br/>
                            <span style='font-size: 1.8rem;'>{corr_t} °C</span>
                        </div>
                    """, unsafe_allow_html=True)

                # Fila 4: Cajas de Entrada (Humedad)
                with col_h:
                    st.markdown("**HUMEDAD RELATIVA (%H)**")
                    val_h = st.text_input("Lectura Termohigrómetro (%H)", key=f"in_h_{idx}")
                    corr_h = calcular_correccion(val_h, inst.get("Correcciones_Humedad", [])) if val_h else "--"
                    
                    # Círculo Naranja: Lectura Corregida
                    st.markdown(f"""
                        <div class='circle-orange'>
                            Lectura Corregida<br/>
                            <span style='font-size: 1.8rem;'>{corr_h} %</span>
                        </div>
                    """, unsafe_allow_html=True)

                if st.button("HECHO", key=f"btn_h_amb_{idx}"):
                    if val_t and val_h:
                        lecturas = {
                            "Temperatura": {"bruta": f"{val_t} °C", "corregida": f"{corr_t} °C"},
                            "Humedad Relativa": {"bruta": f"{val_h} %", "corregida": f"{corr_h} %"}
                        }
                        pdf_buf = generar_pdf_registro("CONDICIONES AMBIENTALES", inst, lecturas)
                        
                        st.success("✅ Registro Ambiental guardado.")
                        st.download_button(
                            label="📄 Descargar PDF de Registro",
                            data=pdf_buf,
                            file_name=f"Registro_Ambiental_{inst['ID']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf",
                            key=f"dl_amb_{idx}"
                        )
                    else:
                        st.error("Por favor ingrese ambas lecturas antes de continuar.")

    # -----------------------------------------------------
    # VISTA: CONDICIONES DE EQUIPOS (IMAGEN 1 DEL BOCETO)
    # -----------------------------------------------------
    elif st.session_state["sub_seccion_lab"] == "CE":
        st.subheader("🧊 Registro de Condiciones de Equipos (Frío/Sensores)")
        
        ce_lab = [c for c in st.session_state["condiciones_equipos_db"] if str(c.get("Ubicacion_Lab")) == str(lab)]
        
        if not ce_lab:
            st.info("No hay equipos de congelación o sensores configurados para este laboratorio. Presiona '+' para agregar.")
        else:
            for idx, eq_c in enumerate(ce_lab):
                st.markdown(f"#### Equipo: **{eq_c['Tipo_Equipo']}** (ID: {eq_c['ID']})")
                
                sensores = eq_c.get("Sensores", ["Sensor Principal"])
                cols = st.columns(len(sensores))
                lecturas_cap = {}
                
                # Despliegue dinámico según Fila 4 y Registros
                for s_idx, sensor in enumerate(sensores):
                    with cols[s_idx]:
                        st.markdown(f"**{sensor}**")
                        val_s = st.text_input(f"Lectura {sensor}", key=f"in_ce_{idx}_{s_idx}")
                        corr_s = calcular_correccion(val_s, eq_c.get("Correcciones", [])) if val_s else "--"
                        
                        lecturas_cap[sensor] = {"bruta": f"{val_s} °C", "corregida": f"{corr_s} °C"}
                        
                        # Círculo Naranja: Corrección
                        st.markdown(f"""
                            <div class='circle-orange'>
                                Corrección<br/>
                                <span style='font-size: 1.6rem;'>{corr_s} °C</span>
                            </div>
                        """, unsafe_allow_html=True)

                if st.button("HECHO", key=f"btn_h_ce_{idx}"):
                    pdf_buf = generar_pdf_registro("CONDICIONES DE EQUIPO", eq_c, lecturas_cap)
                    st.success("✅ Registro de Equipo guardado.")
                    st.download_button(
                        label="📄 Descargar PDF de Registro",
                        data=pdf_buf,
                        file_name=f"Registro_Cond_Equipo_{eq_c['ID']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        key=f"dl_ce_{idx}"
                    )

# ---------------------------------------------------------
# 8. HISTORIAL GLOBAL DE REGISTROS AL FINAL DE LA PÁGINA
# ---------------------------------------------------------
st.markdown("---")
with st.expander("📊 Ver resumen global de datos almacenados en memoria"):
    st.write("**Equipos:**", st.session_state["equipos_db"])
    st.write("**Condiciones Ambientales:**", st.session_state["condiciones_ambientales_db"])
    st.write("**Condiciones de Equipos:**", st.session_state["condiciones_equipos_db"])
