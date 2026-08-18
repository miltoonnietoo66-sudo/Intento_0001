from datetime import datetime
import pandas as pd
import pytz
import streamlit as st

# Configuración inicial de la página
st.set_page_config(page_title="Sistema INER", layout="wide")

# CSS Personalizado: Marca de agua del INER, márgenes y estilos de botones
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
        background-size: 450px;
        position: relative;
    }

    /* Superposición translúcida blanca para asegurar contraste de texto */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.88);
        z-index: -1;
    }

    /* Padding superior para evitar recorte de la Fila 1 */
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 2rem !important;
    }

    /* Estilo para etiquetas estáticas del menú */
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

    /* Estilo del contenedor del Reloj CDMX */
    .reloj-box {
        border: 2px solid #0077B6;
        background-color: #F0F8FF;
        color: #0077B6;
        font-weight: bold;
        text-align: center;
        border-radius: 4px;
        height: 2.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
    }

    /* Estilo de los botones del menú */
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

    /* ENCABEZADOS INICIO / FINAL */
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

# Función para obtener hora oficial CDMX
tz_cdmx = pytz.timezone("America/Mexico_City")


def obtener_hora_cdmx():
    return datetime.now(tz_cdmx).strftime("%Y-%m-%d %H:%M:%S")


# ==========================================
# FILA 1: INER | BUSCAR | RELOJ EN VIVO (CDMX) | LIT
# ==========================================
col1_1, col1_2, col1_3, col1_4 = st.columns([1.5, 1.5, 3.5, 1.5])

with col1_1:
    st.markdown('<div class="label-box">INER</div>', unsafe_allow_html=True)

with col1_2:
    if st.button("BUSCAR", key="btn_buscar"):
        st.toast("Función de búsqueda activada")

with col1_3:
    # Reloj en vivo dinámico con JavaScript en zona horaria Ciudad de México
    reloj_html = """
    <div class="reloj-box" id="reloj-cdmx">🕒 Cargando hora CDMX...</div>
    <script>
    function actualizarReloj() {
        const opciones = {
            timeZone: 'America/Mexico_City',
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        };
        const ahoraCDMX = new Intl.DateTimeFormat('es-MX', opciones).format(new Date());
        document.getElementById('reloj-cdmx').innerHTML = '🕒 CDMX: ' + ahoraCDMX;
    }
    setInterval(actualizarReloj, 1000);
    actualizarReloj();
    </script>
    """
    st.components.v1.html(reloj_html, height=50)

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
    # DESPLIEGUE SOLO TRAS PRESIONAR "USO DE EQUIPOS"
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
                        timestamp_inicio = obtener_hora_cdmx()
                        st.session_state[f"estado_{eq}"] = "EN_USO"

                        st.session_state["historial_registros"].append(
                            {
                                "Laboratorio": "503",
                                "Equipo": eq,
                                "Acción": "INICIO",
                                "FechaHora_CDMX": timestamp_inicio,
                            }
                        )
                        st.toast(
                            f"Inicio registrado para {eq} a las {timestamp_inicio} (CDMX)"
                        )
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
                        timestamp_fin = obtener_hora_cdmx()
                        st.session_state[f"estado_{eq}"] = "FINALIZADO"

                        st.session_state["historial_registros"].append(
                            {
                                "Laboratorio": "503",
                                "Equipo": eq,
                                "Acción": "FINAL",
                                "FechaHora_CDMX": timestamp_fin,
                            }
                        )
                        st.toast(
                            f"Finalización registrada para {eq} a las {timestamp_fin} (CDMX)"
                        )
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
                    file_name=f"Bitacora_Equipos_503_{datetime.now(tz_cdmx).strftime('%Y%m%d_%H%M')}.csv",
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
