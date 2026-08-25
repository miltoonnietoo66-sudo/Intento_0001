import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# CONFIGURACIÓN INICIAL Y ESTILOS DE PÁGINA
# ==========================================
st.set_page_config(page_title="INER - Bitácora de Laboratorio", layout="wide")

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        background-color: #003366;
        color: white;
        padding: 15px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .section-title {
        background-color: #0077B6;
        color: white;
        padding: 8px 15px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 4px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .btn-hecho button {
        background-color: #28a745 !important;
        color: white !important;
        width: 100%;
        font-weight: bold;
    }
    .btn-eliminar button {
        background-color: #dc3545 !important;
        color: white !important;
        width: 100%;
        font-weight: bold;
    }
    .header-verif {
        font-weight: bold;
        background-color: #0077B6;
        color: white;
        padding: 8px;
        border-radius: 4px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# BASE DE DATOS SQLITE
# ==========================================
def obtener_conexion():
    conn = sqlite3.connect("laboratorio_iner.db")
    return conn

def inicializar_bd():
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Tabla Equipos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id TEXT PRIMARY KEY,
            tipo TEXT,
            numero TEXT,
            marca TEXT,
            modelo TEXT,
            serie TEXT,
            inventario TEXT,
            ubicacion_lab TEXT
        )
    """)
    
    # Tabla Registros de Uso de Equipos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros_uso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id TEXT,
            accion TEXT,
            fecha_hora_cdmx TEXT,
            usuario TEXT,
            verificado INTEGER DEFAULT 0,
            verificado_por TEXT
        )
    """)
    
    # Tabla Configuración Ambiental
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_ambientales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            val_min REAL,
            val_max REAL,
            instrumento TEXT,
            ubicacion_lab TEXT
        )
    """)
    
    # Tabla Mediciones Ambientales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mediciones_ambientales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab TEXT,
            temp_corr REAL,
            hum_corr REAL,
            fecha_hora TEXT,
            usuario TEXT,
            verificado INTEGER DEFAULT 0,
            verificado_por TEXT
        )
    """)
    
    # Tabla Configuración Condiciones de Equipos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_condiciones_equipos (
            id TEXT PRIMARY KEY,
            tipo_equipo TEXT,
            numero TEXT,
            marca TEXT,
            modelo TEXT,
            serie TEXT,
            inventario TEXT,
            ubicacion_lab TEXT
        )
    """)
    
    # Tabla Mediciones Condiciones de Equipos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mediciones_equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab TEXT,
            parametro TEXT,
            corregida REAL,
            fecha_hora TEXT,
            usuario TEXT,
            verificado INTEGER DEFAULT 0,
            verificado_por TEXT
        )
    """)
    
    # Tabla Tabla de Correcciones por Rango
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS correcciones_rangos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entidad_id TEXT,
            rango TEXT,
            correccion REAL
        )
    """)

    conn.commit()
    conn.close()

inicializar_bd()

# ==========================================
# FUNCIONES AUXILIARES DE CARGA Y ESTILOS
# ==========================================
def cargar_equipos():
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT * FROM equipos", conn)
    conn.close()
    return df.to_dict(orient="records")

def aplicar_estilo_seleccion(btn_key):
    st.markdown(f"""
    <style>
        div[data-testid="stButton"] button[key="{btn_key}"] {{
            border: 2px solid #0077B6 !important;
            background-color: #E0F7FA !important;
            font-weight: bold;
        }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# GENERADOR DE PDF (REPORTLAB)
# ==========================================
def generar_pdf_generico(titulo_doc, df_datos, metadata=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    # Encabezado INER
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=16,
        textColor=colors.HexColor('#003366'),
        alignment=1,
        spaceAfter=12
    )
    story.append(Paragraph("<b>INSTITUTO NACIONAL DE ENFERMEDADES RESPIRATORIAS</b>", title_style))
    story.append(Paragraph(f"<b>{titulo_doc.upper()}</b>", ParagraphStyle('Sub', parent=title_style, fontSize=11, textColor=colors.HexColor('#0077B6'))))
    story.append(Spacer(1, 10))

    # Metadatos
    if metadata:
        meta_table_data = []
        keys = list(metadata.keys())
        for i in range(0, len(keys), 2):
            k1 = keys[i]
            v1 = metadata[k1]
            if i + 1 < len(keys):
                k2 = keys[i+1]
                v2 = metadata[k2]
                meta_table_data.append([f"<b>{k1}:</b> {v1}", f"<b>{k2}:</b> {v2}"])
            else:
                meta_table_data.append([f"<b>{k1}:</b> {v1}", ""])
        
        t_meta = Table([[Paragraph(cell, styles['Normal']) for cell in row] for row in meta_table_data], colWidths=[270, 270])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4F6F7')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D5D8DC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#BDC3C7')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 15))

    # Tabla de Datos
    if not df_datos.empty:
        headers = [Paragraph(f"<b>{col}</b>", ParagraphStyle('H', parent=styles['Normal'], textColor=colors.white, alignment=1)) for col in df_datos.columns]
        table_data = [headers]

        for _, row in df_datos.iterrows():
            row_cells = []
            for item in row:
                row_cells.append(Paragraph(str(item), ParagraphStyle('N', parent=styles['Normal'], alignment=1)))
            table_data.append(row_cells)

        col_w = 540 / len(df_datos.columns)
        t_data = Table(table_data, colWidths=[col_w] * len(df_datos.columns))
        t_data.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9EBEA')]),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_data)
        story.append(Spacer(1, 20))

    # Pie de firmas
    firmas_data = [
        [Paragraph("___________________________<br><b>REGISTRÓ</b>", ParagraphStyle('F1', parent=styles['Normal'], alignment=1)),
         Paragraph("___________________________<br><b>VERIFICÓ</b>", ParagraphStyle('F2', parent=styles['Normal'], alignment=1))]
    ]
    t_firmas = Table(firmas_data, colWidths=[270, 270])
    t_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('PADDING', (0,0), (-1,-1), 20),
    ]))
    story.append(t_firmas)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# ESTADOS DE SESIÓN
# ==========================================
if "menu_principal" not in st.session_state:
    st.session_state["menu_principal"] = "REGISTRAR"
if "sub_categoria" not in st.session_state:
    st.session_state["sub_categoria"] = "EQUIPOS"
if "modo_agregar" not in st.session_state:
    st.session_state["modo_agregar"] = False
if "modo_eliminar" not in st.session_state:
    st.session_state["modo_eliminar"] = False
if "item_editar_id" not in st.session_state:
    st.session_state["item_editar_id"] = None
if "lab_seleccionado" not in st.session_state:
    st.session_state["lab_seleccionado"] = "502"
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = "TECNICO_LAB"

labs_lista = ["502", "503", "504", "506", "507", "508", "510", "513", "514"]

# ==========================================
# ENCABEZADO Y MENÚ PRINCIPAL
# ==========================================
st.markdown('<div class="main-header">LABORATORIO DE INMUNOBIOLOGÍA DE LA TUBERCULOSIS</div>', unsafe_allow_html=True)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    if st.button("REPORTES", use_container_width=True):
        st.session_state["menu_principal"] = "REPORTES"
        st.session_state["modo_agregar"] = False
        st.session_state["modo_eliminar"] = False
        st.rerun()
with col_m2:
    if st.button("REGISTRAR", use_container_width=True):
        st.session_state["menu_principal"] = "REGISTRAR"
        st.rerun()
with col_m3:
    if st.button("VERIFICAR", use_container_width=True):
        st.session_state["menu_principal"] = "VERIFICAR"
        st.session_state["modo_agregar"] = False
        st.session_state["modo_eliminar"] = False
        st.rerun()
with col_m4:
    if st.button("USUARIO", use_container_width=True):
        st.session_state["menu_principal"] = "USUARIO"
        st.rerun()

st.markdown("---")

# ==========================================
# SUBCATEGORÍAS (OCULTAS EN VERIFICAR Y REPORTES)
# ==========================================
if st.session_state["menu_principal"] not in ["VERIFICAR", "REPORTES"]:
    col_sub1, col_sub2, col_sub3 = st.columns(3)
    with col_sub1:
        if st.button("EQUIPOS", use_container_width=True):
            st.session_state["sub_categoria"] = "EQUIPOS"
            st.rerun()
    with col_sub2:
        if st.button("CONDICIONES AMBIENTALES", use_container_width=True):
            st.session_state["sub_categoria"] = "CONDICIONES AMBIENTALES"
            st.rerun()
    with col_sub3:
        if st.button("CONDICIONES DE EQUIPOS", use_container_width=True):
            st.session_state["sub_categoria"] = "CONDICIONES DE EQUIPOS"
            st.rerun()

    st.markdown("---")

# ==========================================
# BARRA DE SELECCIÓN DE LABORATORIOS (LABS)
# ==========================================
st.write("**LABS:**")
cols_labs = st.columns(len(labs_lista))
for idx, lab_num in enumerate(labs_lista):
    with cols_labs[idx]:
        btn_k = f"btn_lab_{lab_num}"
        if st.session_state["lab_seleccionado"] == lab_num:
            aplicar_estilo_seleccion(btn_k)
        if st.button(lab_num, key=btn_k, use_container_width=True):
            st.session_state["lab_seleccionado"] = lab_num
            st.rerun()

st.markdown("---")

# ==========================================
# SECCIÓN: REGISTRAR (CAPTURA Y MÁS / MENOS)
# ==========================================
if st.session_state["menu_principal"] == "REGISTRAR":
    c_plus, c_minus = st.columns([1, 1])
    with c_plus:
        if st.button("➕ AGREGAR CONFIGURACIÓN", use_container_width=True):
            st.session_state["modo_agregar"] = True
            st.session_state["modo_eliminar"] = False
            st.session_state["item_editar_id"] = None
            st.rerun()
    with c_minus:
        if st.button("➖ EDITAR / ELIMINAR CONFIGURACIÓN", use_container_width=True):
            st.session_state["modo_eliminar"] = True
            st.session_state["modo_agregar"] = False
            st.session_state["item_editar_id"] = None
            st.rerun()

    st.markdown("---")

    # MÓDULO ➕ (AGREGAR NUEVO)
    if st.session_state["modo_agregar"]:
        if st.session_state["sub_categoria"] == "EQUIPOS":
            st.markdown('<div class="section-title">REGISTRAR NUEVO EQUIPO DE USO</div>', unsafe_allow_html=True)
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1: tipo_eq = st.selectbox("Tipo", ["GABS", "CENT", "MICR", "BAAG"])
            with c2: num_eq = st.text_input("Número", "01")
            with c3: marca_eq = st.text_input("Marca")
            with c4: mod_eq = st.text_input("Modelo")
            with c5: serie_eq = st.text_input("Serie")
            with c6: inv_eq = st.text_input("Inventario")
            
            st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
            if st.button("HECHO (GUARDAR EQUIPO)"):
                eq_id = f"{tipo_eq}-{num_eq}_{st.session_state['lab_seleccionado']}"
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO equipos VALUES (?,?,?,?,?,?,?,?)",
                               (eq_id, tipo_eq, num_eq, marca_eq, mod_eq, serie_eq, inv_eq, st.session_state['lab_seleccionado']))
                conn.commit()
                conn.close()
                st.session_state["modo_agregar"] = False
                st.success("✅ Equipo registrado correctamente.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # MÓDULO DE USO DIARIO DE EQUIPOS / LECTURAS
    elif not st.session_state["modo_eliminar"]:
        lab_act = st.session_state["lab_seleccionado"]
        st.markdown(f'<div class="section-title">REGISTROS DIARIOS EN LABORATORIO {lab_act}</div>', unsafe_allow_html=True)
        
        conn = obtener_conexion()
        equipos_lab = pd.read_sql_query("SELECT * FROM equipos WHERE ubicacion_lab = ?", conn, params=(lab_act,)).to_dict(orient="records")
        conn.close()

        if st.session_state["sub_categoria"] == "EQUIPOS":
            if not equipos_lab:
                st.info("No hay equipos registrados en este laboratorio. Presiona ➕ para agregar uno.")
            else:
                for eq in equipos_lab:
                    c1, c2, c3 = st.columns([3, 2, 2])
                    with c1:
                        st.write(f"**{eq['tipo']}-{eq['numero']}** | Marca: {eq['marca']} | Serie: {eq['serie']}")
                    with c2:
                        accion = st.selectbox("Acción", ["INICIO DE USO", "FIN DE USO", "MANTENIMIENTO"], key=f"acc_{eq['id']}")
                    with c3:
                        if st.button("REGISTRAR USO", key=f"btn_reg_{eq['id']}"):
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO registros_uso (equipo_id, accion, fecha_hora_cdmx, usuario, verificado) VALUES (?, ?, ?, ?, 0)",
                                           (eq['id'], accion, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state["usuario_actual"]))
                            conn.commit()
                            conn.close()
                            st.success("Registrado para verificación.")

# ==========================================
# SECCIÓN: VERIFICAR (AUDITORÍA SEGÚN DIAGRAMA)
# ==========================================
if st.session_state["menu_principal"] == "VERIFICAR":
    st.markdown('<div class="section-title">AUDITORÍA Y VERIFICACIÓN DE BITÁCORAS PENDIENTES</div>', unsafe_allow_html=True)
    
    lab_act = st.session_state.get("lab_seleccionado")
    
    if lab_act is None:
        st.info("👈 Por favor, selecciona un Laboratorio de la barra superior para consultar los registros pendientes de verificación.")
    else:
        usuario_verificador = st.session_state.get("usuario_actual", "SUPERVISOR")
        conn = obtener_conexion()
        
        # CABECERA DE TABLA SEGÚN EL DIAGRAMA DE USUARIO
        c_t1, c_t2, c_t3, c_t4, c_t5 = st.columns([2, 2.5, 1.5, 1.5, 1.5])
        with c_t1: st.markdown('<div class="header-verif">ELEMENTO</div>', unsafe_allow_html=True)
        with c_t2: st.markdown('<div class="header-verif">LECTURA / TIEMPO</div>', unsafe_allow_html=True)
        with c_t3: st.markdown('<div class="header-verif">HORA</div>', unsafe_allow_html=True)
        with c_t4: st.markdown('<div class="header-verif">USUARIO</div>', unsafe_allow_html=True)
        with c_t5: st.markdown('<div class="header-verif">ACCIÓN</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        registros_encontrados = False

        # 1. FILAS DE EQUIPOS (EQUIPOS | HORA INICIO/FIN | HORA | USUARIO | VERIFICAR)
        try:
            sql_eq = "SELECT r.id, r.equipo_id, r.accion, r.fecha_hora_cdmx, r.usuario, e.tipo, e.numero FROM registros_uso r JOIN equipos e ON r.equipo_id = e.id WHERE e.ubicacion_lab = ? AND (r.verificado IS NULL OR r.verificado = 0)"
            usos_pendientes = pd.read_sql_query(sql_eq, conn, params=(lab_act,)).to_dict(orient="records")
        except Exception:
            usos_pendientes = []

        for u in usos_pendientes:
            registros_encontrados = True
            c1, c2, c3, c4, c5 = st.columns([2, 2.5, 1.5, 1.5, 1.5])
            with c1:
                st.write(f"**EQUIPOS:** {u['tipo']}-{u['numero']}")
            with c2:
                st.write(f"**H.INICIO/FIN:** {u['accion']}")
            with c3:
                hora_str = str(u['fecha_hora_cdmx']).split(" ")[-1] if " " in str(u['fecha_hora_cdmx']) else str(u['fecha_hora_cdmx'])
                st.write(f"**HORA:** {hora_str[:5]}")
            with c4:
                st.write(f"**USUARIO:** {u.get('usuario', 'N/A')}")
            with c5:
                if st.button("VERIFICAR", key=f"v_eq_{u['id']}"):
                    cur = conn.cursor()
                    cur.execute("UPDATE registros_uso SET verificado = 1, verificado_por = ? WHERE id = ?", (usuario_verificador, u['id']))
                    conn.commit()
                    st.success("Verificado correctamente")
                    st.rerun()
            st.markdown("---")

        # 2. FILAS DE CONDICIONES AMBIENTALES (TEMP / %H | LECTURA | HORA | USUARIO | VERIFICAR)
        try:
            sql_amb = "SELECT id, temp_corr, hum_corr, fecha_hora, usuario FROM mediciones_ambientales WHERE lab = ? AND (verificado IS NULL OR verificado = 0)"
            amb_pendientes = pd.read_sql_query(sql_amb, conn, params=(lab_act,)).to_dict(orient="records")
        except Exception:
            amb_pendientes = []

        for a in amb_pendientes:
            registros_encontrados = True
            c1, c2, c3, c4, c5 = st.columns([2, 2.5, 1.5, 1.5, 1.5])
            with c1:
                st.write("**TEMP / %H**")
            with c2:
                st.write(f"**LECTURA:** {a['temp_corr']} °C | {a['hum_corr']} %")
            with c3:
                hora_str = str(a['fecha_hora']).split(" ")[-1] if " " in str(a['fecha_hora']) else str(a['fecha_hora'])
                st.write(f"**HORA:** {hora_str[:5]}")
            with c4:
                st.write(f"**USUARIO:** {a.get('usuario', 'N/A')}")
            with c5:
                if st.button("VERIFICAR", key=f"v_amb_{a['id']}"):
                    cur = conn.cursor()
                    cur.execute("UPDATE mediciones_ambientales SET verificado = 1, verificado_por = ? WHERE id = ?", (usuario_verificador, a['id']))
                    conn.commit()
                    st.success("Verificado correctamente")
                    st.rerun()
            st.markdown("---")

        # 3. FILAS DE CONDICIONES DE EQUIPOS (CONDICIONES EQUIPOS | LECTURA | HORA | USUARIO | VERIFICAR)
        try:
            sql_ce = "SELECT id, parametro, corregida, fecha_hora, usuario FROM mediciones_equipos WHERE lab = ? AND (verificado IS NULL OR verificado = 0)"
            ce_pendientes = pd.read_sql_query(sql_ce, conn, params=(lab_act,)).to_dict(orient="records")
        except Exception:
            ce_pendientes = []

        for ce in ce_pendientes:
            registros_encontrados = True
            c1, c2, c3, c4, c5 = st.columns([2, 2.5, 1.5, 1.5, 1.5])
            with c1:
                st.write(f"**COND. EQUIPO:** {ce['parametro']}")
            with c2:
                st.write(f"**LECTURA:** {ce['corregida']}")
            with c3:
                hora_str = str(ce['fecha_hora']).split(" ")[-1] if " " in str(ce['fecha_hora']) else str(ce['fecha_hora'])
                st.write(f"**HORA:** {hora_str[:5]}")
            with c4:
                st.write(f"**USUARIO:** {ce.get('usuario', 'N/A')}")
            with c5:
                if st.button("VERIFICAR", key=f"v_ce_{ce['id']}"):
                    cur = conn.cursor()
                    cur.execute("UPDATE mediciones_equipos SET verificado = 1, verificado_por = ? WHERE id = ?", (usuario_verificador, ce['id']))
                    conn.commit()
                    st.success("Verificado correctamente")
                    st.rerun()
            st.markdown("---")

        if not registros_encontrados:
            st.info(f"🎉 No hay mediciones ni registros pendientes por verificar en el Lab {lab_act}.")

        conn.close()

# ==========================================
# SECCIÓN: REPORTES (PDF VERIFICADOS POR FECHA)
# ==========================================
if st.session_state["menu_principal"] == "REPORTES":
    st.markdown('<div class="section-title">GENERACIÓN DE REPORTES EN PDF (REGISTROS VERIFICADOS)</div>', unsafe_allow_html=True)
    
    cat_act = st.session_state.get("sub_categoria", "EQUIPOS")
    lab_act = st.session_state.get("lab_seleccionado")
    
    if lab_act is None:
        st.info("👈 Por favor, selecciona un Laboratorio de la barra superior para consultar los reportes.")
    else:
        # FILTRO POR RANGO DE FECHAS
        st.markdown("**FILTRAR PERÍODO DEL REPORTE**")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_inicio = st.date_input("Fecha Inicio", value=pd.to_datetime("today") - pd.Timedelta(days=30), key="rep_f_inicio")
        with col_f2:
            fecha_fin = st.date_input("Fecha Fin", value=pd.to_datetime("today"), key="rep_f_fin")

        f_inicio_str = f"{fecha_inicio} 00:00:00"
        f_fin_str = f"{fecha_fin} 23:59:59"

        st.markdown("---")
        conn = obtener_conexion()
        cols_rep = st.columns(4)
        c_idx = 0

        # REPORTES DE EQUIPOS DE USO
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
                        sql_usos = 'SELECT fecha_hora_cdmx AS "Fecha y Hora", accion AS "Lectura/Uso", usuario AS "Registró", verificado_por AS "Verificó" FROM registros_uso WHERE equipo_id = ? AND verificado = 1 AND fecha_hora_cdmx BETWEEN ? AND ?'
                        df_usos = pd.read_sql_query(sql_usos, conn, params=(eq['id'], f_inicio_str, f_fin_str))
                        
                        pdf_bytes = generar_pdf_generico(f"BITÁCORA DE USO: {eq['tipo']}-{eq['numero']}", df_usos, metadata=meta_eq)
                        
                        st.download_button(
                            label=f"📄 PDF: {eq['tipo']}-{eq['numero']}",
                            data=pdf_bytes,
                            file_name=f"Reporte_Uso_{eq['id']}_{fecha_inicio}_{fecha_fin}.pdf",
                            mime="application/pdf",
                            key=f"dl_eq_{eq['id']}"
                        )
                    c_idx += 1

        # REPORTES DE CONDICIONES AMBIENTALES
        elif cat_act == "CONDICIONES AMBIENTALES":
            meta_amb = {
                "Área Monitorizada": f"Laboratorio {lab_act}",
                "Parámetros": "Temperatura y Humedad Relativa",
                "Frecuencia de Registro": "Diaria",
                "Período": f"{fecha_inicio} al {fecha_fin}"
            }
            
            sql_amb_rep = 'SELECT fecha_hora AS "Fecha y Hora", ("Temp: " || temp_corr || " °C | Hum: " || hum_corr || " %") AS "Lectura Corregida", usuario AS "Registró", verificado_por AS "Verificó" FROM mediciones_ambientales WHERE lab = ? AND verificado = 1 AND fecha_hora BETWEEN ? AND ?'
            df_amb = pd.read_sql_query(sql_amb_rep, conn, params=(lab_act, f_inicio_str, f_fin_str))
            
            with cols_rep[0]:
                pdf_bytes_amb = generar_pdf_generico(f"CONDICIONES AMBIENTALES - LAB {lab_act}", df_amb, metadata=meta_amb)
                st.download_button(
                    label=f"📄 PDF: AMBIENTAL LAB {lab_act}",
                    data=pdf_bytes_amb,
                    file_name=f"Reporte_Ambiental_Lab_{lab_act}_{fecha_inicio}_{fecha_fin}.pdf",
                    mime="application/pdf",
                    key=f"dl_amb_{lab_act}"
                )

        # REPORTES DE CONDICIONES DE EQUIPOS
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
                        sql_ce_rep = 'SELECT fecha_hora AS "Fecha y Hora", corregida AS "Lectura Corregida", usuario AS "Registró", verificado_por AS "Verificó" FROM mediciones_equipos WHERE lab = ? AND parametro LIKE ? AND verificado = 1 AND fecha_hora BETWEEN ? AND ?'
                        df_ce = pd.read_sql_query(sql_ce_rep, conn, params=(lab_act, f"%{ce['tipo_equipo']}-{ce['numero']}%", f_inicio_str, f_fin_str))
                        
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
# SECCIÓN: USUARIO
# ==========================================
if st.session_state["menu_principal"] == "USUARIO":
    st.markdown('<div class="section-title">GESTIÓN Y FIRMA DE USUARIO</div>', unsafe_allow_html=True)
    st.session_state["usuario_actual"] = st.text_input("Nombre de Usuario / Clave de Personal", value=st.session_state["usuario_actual"])
    st.success(f"Usuario activo para firmas: {st.session_state['usuario_actual']}")
