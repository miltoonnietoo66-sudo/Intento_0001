from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

# Configuración inicial de la página
st.set_page_config(page_title="Sistema INER", layout="wide")

# Zona horaria oficial de Ciudad de México
TZ_CDMX = ZoneInfo("America/Mexico_City")

# CSS Personalizado: Escudo INER de fondo y márgenes adaptados
st.markdown(
    """
    <style>
    /* Fondo con marca de agua (Escudo INER) */
    .stApp {
        background-color: #FFFFFF;
        background-image: url('https://www.gob.mx/cms/uploads/action_program/main_image/26915/iner.jpg');
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
        background-size: 400px;
    }

    /* Capa de contraste */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.90);
        z-index: -1;
    }

    /* Margen superior para evitar solapamientos */
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 2rem !important;
    }

    /* Cajas azules de la Fila 1 y Etiquetas */
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

    /* Botones principales de la Fila 2 y 3 */
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

    /* Títulos de secciones INICIO y FINAL */
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

# Inicialización de Estados de Sesión
if "lab_seleccionado" not in st.session_state:
    st.session_state["lab_seleccionado"] = None

if "sub_seccion" not in st.session_state:
    st.session_state["sub_seccion"] = None

if "historial_registros" not in st.session_state:
    st.session_state["historial_registros"] = []

equipos_list = ["GABS-3", "CENT-10", "MICR-1"]
for eq in equipos_list:
    if f"estado_{eq}" not in st.session_state:
        st.session_state[f"estado_{eq}"] = "INACTIVO"


def obtener_hora_cdmx():
    return datetime.now(TZ_CDMX).strftime("%d/%m/%Y %H:%M:%S")


# ==========================================
# FILA 1: INER | BUSCAR | RELOJ (CDMX) | LIT
# ==========================================
col1_1, col1_2, col1_3, col1_4 = st.columns([1.5, 1.5, 3.5, 1.5])

with col1_1:
    st.markdown('<div class="label-box">INER</div>', unsafe_allow_html=True)

with col1_2:
    if st.button("BUSCAR", key="btn_buscar"):
        st.toast("Función de búsqueda activada")

with col1_3:
    hora_actual = obtener_hora_cdmx()
    st.markdown(
        f'<div class="reloj-box">🕒 CDMX: {hora_actual}</div>',
        unsafe_allow_html=True,
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
                st.session_state["sub_seccion"] = None

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
    # DESPLIEGUE EXCLUSIVO AL PULSAR "USO DE EQUIPOS"
    # ==========================================
    if st.session_state["sub_seccion"] == "USO DE EQUIPOS":
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

                    if estado_actual == "EN_USO":
                        lbl_btn = f"🟢 {eq} (EN CURSO)"
                    else:
                        lbl_btn = f"🔵 {eq}"

                    if st.button(lbl_btn, key=f"btn_inc_{eq}"):
                        ts = obtener_hora_cdmx()
                        st.session_state[f"estado_{eq}"] = "EN_USO"

                        st.session_state["historial_registros"].append(
                            {
                                "Laboratorio": "503",
                                "Equipo": eq,
                                "Acción": "INICIO",
                                "FechaHora_CDMX": ts,
                            }
                        )
                        st.toast(f"Inicio registrado para {eq} a las {ts}")
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

                    if estado_actual == "FINALIZADO":
                        lbl_btn_fin = f"🔴 {eq} (CONCLUIDO)"
                    else:
                        lbl_btn_fin = f"🔵 {eq}"

                    if st.button(lbl_btn_fin, key=f"btn_fin_{eq}"):
                        ts = obtener_hora_cdmx()
                        st.session_state[f"estado_{eq}"] = "FINALIZADO"

                        st.session_state["historial_registros"].append(
                            {
                                "Laboratorio": "503",
                                "Equipo": eq,
                                "Acción": "FINAL",
                                "FechaHora_CDMX": ts,
                            }
                        )
                        st.toast(f"Finalización registrada para {eq} a las {ts}")
                        st.rerun()

            # BASE DE DATOS Y EXPORTACIÓN
            st.markdown("---")
            st.subheader("📋 Registro de Marcas de Tiempo (Hora CDMX)")

            if st.session_state["historial_registros"]:
                df = pd.DataFrame(st.session_state["historial_registros"])
                st.dataframe(df, use_container_width=True)

                csv_data = df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="📊 Descargar Bitácora (CSV / Excel)",
                    data=csv_data,
                    file_name=f"Bitacora_Equipos_503_{datetime.now(TZ_CDMX).strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("Aún no se han registrado pulsos de inicio o final.")

        else:
            st.subheader(f"Laboratorio {lab_actual}")
            st.caption("Aún no hay equipos configurados para este laboratorio.")

    elif st.session_state["sub_seccion"] == "CONDICIONES":
        st.subheader(f"Condiciones Ambientales — Laboratorio {lab_actual}")
        st.info("Módulo de monitoreo de condiciones (Temperatura, Humedad, etc.)")

    else:
        st.caption(
            "👈 Haz clic en 'USO DE EQUIPOS' o 'CONDICIONES' para ver la información."
        )
