import io
from datetime import datetime
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import streamlit as st

# Configuración inicial de la página
st.set_page_config(page_title="Sistema INER", layout="wide")

# CSS personalizado para corregir la Fila 1 y los estados de color dinámicos
st.markdown(
    """
    <style>
    /* Fondo general blanco */
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }

    .block-container {
        padding-top: 1rem;
    }

    /* Estilo Fila 1 y Etiquetas del Menú (Bordes azulaos visibles) */
    .label-box {
        border: 2px solid #0077B6;
        background-color: #FFFFFF;
        color: #0077B6;
        font-weight: bold;
        text-align: center;
        padding: 0.4rem;
        border-radius: 4px;
        height: 2.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
    }

    /* Reloj y Fecha (Fila 1) */
    .reloj-box {
        border: 2px solid #0077B6;
        background-color: #F0F8FF;
        color: #0077B6;
        font-weight: bold;
        text-align: center;
        padding: 0.4rem;
        border-radius: 4px;
        height: 2.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
    }

    /* Botones de Menú Fila 2 */
    div[data-testid="stButton"] > button {
        color: #E63946 !important;
        font-weight: bold !important;
        background-color: #FFFFFF !important;
        border: 2px solid #0077B6 !important;
        border-radius: 4px !important;
        width: 100% !important;
        height: 2.8rem !important;
    }

    div[data-testid="stButton"] > button:hover {
        background-color: #F0F8FF !important;
    }

    /* Títulos de Secciones INICIO y FINAL */
    .section-header-inicio {
        color: #2A9D8F;
        font-weight: bold;
        font-size: 1.4rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .section-header-final {
        color: #E63946;
        font-weight: bold;
        font-size: 1.4rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Inicialización de Estados de Sesión (Base de datos local)
if "lab_seleccionado" not in st.session_state:
    st.session_state["lab_seleccionado"] = None

if "sub_seccion" not in st.session_state:
    st.session_state["sub_seccion"] = None

if "historial_registros" not in st.session_state:
    st.session_state["historial_registros"] = []

# Estado individual para cada equipo (Azul base / Verde cuando se inicia / Rojo cuando finaliza)
equipos_list = ["GABS-3", "CENT-10", "MICR-1"]
for eq in equipos_list:
    if f"estado_{eq}" not in st.session_state:
        st.session_state[f"estado_{eq}"] = "INACTIVO"

# ==========================================
# FILA 1: INER | BUSCAR | RELOJ Y FECHA | LIT
# ==========================================
col1_1, col1_2, col1_3, col1_4 = st.columns([1.5, 1.5, 3.5, 1.5])

with col1_1:
    st.markdown('<div class="label-box">INER</div>', unsafe_allow_html=True)

with col1_2:
    if st.button("BUSCAR", key="btn_buscar"):
        st.toast("Función de búsqueda activada")

with col1_3:
    ahora = datetime.now()
    fecha_reloj = ahora.strftime("%d/%m/%Y — %H:%M:%S")
    st.markdown(
        f'<div class="reloj-box">🕒 {fecha_reloj}</div>', unsafe_allow_html=True
    )

with col1_4:
    st.markdown('<div class="label-box">LIT</div>', unsafe_allow_html=True)

st.write("")

# ==========================================
# FILA 2: LABORATORIOS | 502 | 503 | 504 | 506 | 507 | 508 | 510 | 🏠
# ==========================================
cols_f2 = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1])

with cols_f2[0]:
    st.markdown('<div class="label-box">LABORATORIOS</div>', unsafe_allow_html=True)

labs = ["502", "503", "504", "506", "507", "508", "510", "INICIO"]

for idx, lab in enumerate(labs, start=1):
    with cols_f2[idx]:
        etiqueta = "🏠" if lab == "INICIO" else lab
        if st.button(etiqueta, key=f"btn_lab_{lab}"):
            if lab == "INICIO":
                st.session_state["lab_seleccionado"] = None
                st.session_state["sub_seccion"] = None
            else:
                st.session_state["lab_seleccionado"] = lab

# ==========================================
# FILA 3: USO DE EQUIPOS | CONDICIONES
# ==========================================
if st.session_state["lab_seleccionado"] is not None:
    st.write("")
    col3_1, col3_2 = st.columns([1, 1])

    lab_actual = st.session_state["lab_seleccionado"]

    with col3_1:
        if st.button(
            f"USO DE EQUIPOS ({lab_actual})", key="btn_uso_equipos"
        ):
            st.session_state["sub_seccion"] = "USO DE EQUIPOS"

    with col3_2:
        if st.button(f"CONDICIONES ({lab_actual})", key="btn_condiciones"):
            st.session_state["sub_seccion"] = "CONDICIONES"

    st.markdown("---")

    # ==========================================
    # VISTA DE EQUIPOS PARA EL LAB 503
    # ==========================================
    if lab_actual == "503":
        st.subheader("Control de Equipos — Laboratorio 503")

        col_inicio, col_linea, col_final = st.columns([4, 0.2, 4])

        # COLUMNA INICIO
        with col_inicio:
            st.markdown(
                '<div class="section-header-inicio">INICIO</div>',
                unsafe_allow_html=True,
            )

            for eq in equipos_list:
                estado_actual = st.session_state[f"estado_{eq}"]

                # Estilo dinámico: Pasa a verde al pulsar INICIO
                if estado_actual == "EN_USO":
                    btn_type = "primary"
                    lbl_btn = f"🟢 {eq} (EN CURSO)"
                else:
                    btn_type = "secondary"
                    lbl_btn = f"🔵 {eq}"

                if st.button(
                    lbl_btn, key=f"btn_inc_{eq}", type=btn_type
                ):
                    timestamp_inicio = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    st.session_state[f"estado_{eq}"] = "EN_USO"
                    st.session_state[f"inicio_{eq}"] = timestamp_inicio

                    st.session_state["historial_registros"].append(
                        {
                            "Laboratorio": "503",
                            "Equipo": eq,
                            "Acción": "INICIO",
                            "FechaHora": timestamp_inicio,
                        }
                    )
                    st.toast(f"Inicio registrado para {eq} a las {timestamp_inicio}")
                    st.rerun()

        # LÍNEA DIVISORA
        with col_linea:
            st.markdown(
                "<div style='border-left: 2px solid #0077B6; height: 300px; margin: 0 auto;'></div>",
                unsafe_allow_html=True,
            )

        # COLUMNA FINAL
        with col_final:
            st.markdown(
                '<div class="section-header-final">FINAL</div>',
                unsafe_allow_html=True,
            )

            for eq in equipos_list:
                estado_actual = st.session_state[f"estado_{eq}"]

                # Estilo dinámico: Pasa a rojo al pulsar FINAL
                if estado_actual == "FINALIZADO":
                    lbl_btn_fin = f"🔴 {eq} (CONCLUIDO)"
                else:
                    lbl_btn_fin = f"🔵 {eq}"

                if st.button(
                    lbl_btn_fin, key=f"btn_fin_{eq}"
                ):
                    timestamp_fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state[f"estado_{eq}"] = "FINALIZADO"

                    st.session_state["historial_registros"].append(
                        {
                            "Laboratorio": "503",
                            "Equipo": eq,
                            "Acción": "FINAL",
                            "FechaHora": timestamp_fin,
                        }
                    )
                    st.toast(f"Finalización registrada para {eq} a las {timestamp_fin}")
                    st.rerun()

        # ==========================================
        # BASE DE DATOS Y GENERACIÓN DE PDF
        # ==========================================
        st.markdown("---")
        st.subheader("📋 Registro de Marcas de Tiempo")

        if st.session_state["historial_registros"]:
            df = pd.DataFrame(st.session_state["historial_registros"])
            st.dataframe(df, use_container_width=True)

            # Función para construir el reporte PDF dinámico
            def generar_pdf(dataframe):
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                elements = []

                styles = getSampleStyleSheet()
                title = Paragraph(
                    "<b>Reporte de Uso de Equipos - Laboratorio 503</b>",
                    styles["Title"],
                )
                elements.append(title)

                data = [list(dataframe.columns)] + dataframe.values.tolist()
                table = Table(data)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0077B6")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F0F8FF")),
                            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#0077B6")),
                        ]
                    )
                )
                elements.append(table)
                doc.build(elements)
                buffer.seek(0)
                return buffer

            pdf_data = generar_pdf(df)

            st.download_button(
                label="📄 Descargar Bitácora en PDF",
                data=pdf_data,
                file_name=f"Bitacora_Equipos_503_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
            )
        else:
            st.info("Aún no se han registrado pulsos de inicio o final.")

    else:
        st.subheader(f"Laboratorio {lab_actual}")
        st.caption("Selecciona una opción en la Fila 3 para desplegar información.")
