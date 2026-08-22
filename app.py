from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Sistema INER - Gestión de Laboratorios", layout="wide"
)

# Zona horaria oficial de Ciudad de México
TZ_CDMX = ZoneInfo("America/Mexico_City")

# CSS Personalizado
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
        background-size: 420px;
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

    /* Margen superior */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Estilo de Cajas Azules Fila 1 */
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

    /* Estilo general para botones */
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

    /* Botón HECHO en color destacado */
    .btn-hecho div[data-testid="stButton"] > button {
        background-color: #2A9D8F !important;
        color: #FFFFFF !important;
        border: 2px solid #2A9D8F !important;
        font-size: 1.1rem !important;
    }

    /* Encabezados de secciones */
    .section-title {
        color: #0077B6;
        font-weight: bold;
        text-align: center;
        border-bottom: 2px solid #0077B6;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Inicialización de Estados de Sesión
if "lab_seleccionado" not in st.session_state:
    st.session_state["lab_seleccionado"] = None

if "modo_agregar" not in st.session_state:
    st.session_state["modo_agregar"] = False

if "sub_seccion_mas" not in st.session_state:
    st.session_state["sub_seccion_mas"] = "EQUIPOS"

if "sub_seccion_lab" not in st.session_state:
    st.session_state["sub_seccion_lab"] = None

if "historial_registros" not in st.session_state:
    st.session_state["historial_registros"] = []

if "inventario_equipos" not in st.session_state:
    st.session_state["inventario_equipos"] = []

if "condiciones_ambientales_db" not in st.session_state:
    st.session_state["condiciones_ambientales_db"] = []

if "condiciones_equipos_db" not in st.session_state:
    st.session_state["condiciones_equipos_db"] = []

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
    st.markdown(
        f'<div class="reloj-box">🕒 CDMX: {obtener_hora_cdmx()}</div>',
        unsafe_allow_html=True,
    )

with col1_4:
    st.markdown('<div class="label-box">LIT</div>', unsafe_allow_html=True)

st.write("")

# ==========================================
# FILA 2: LABORATORIOS | 502 | 503 | ... | 🏠 | ➕
# ==========================================
labs_menu = [
    "502",
    "503",
    "504",
    "506",
    "507",
    "508",
    "510",
    "513",
    "514",
    "INICIO",
    "MAS",
]
cols_f2 = st.columns([2] + [1] * (len(labs_menu) - 1) + [1])

with cols_f2[0]:
    st.markdown('<div class="label-box">LABORATORIOS</div>', unsafe_allow_html=True)

for idx, lab in enumerate(labs_menu, start=1):
    with cols_f2[idx]:
        if lab == "INICIO":
            etiqueta = "🏠"
        elif lab == "MAS":
            etiqueta = "➕"
        else:
            etiqueta = lab

        if st.button(etiqueta, key=f"btn_f2_{lab}"):
            if lab == "INICIO":
                st.session_state["lab_seleccionado"] = None
                st.session_state["modo_agregar"] = False
                st.session_state["sub_seccion_lab"] = None
            elif lab == "MAS":
                st.session_state["modo_agregar"] = True
                st.session_state["lab_seleccionado"] = None
                st.session_state["sub_seccion_mas"] = "EQUIPOS"
            else:
                st.session_state["lab_seleccionado"] = lab
                st.session_state["modo_agregar"] = False
                st.session_state["sub_seccion_lab"] = None

st.markdown("---")

# ==========================================
# FILA 3 (OPCIÓN A): MENÚ DEL BOTÓN "+"
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

    # ------------------------------------------
    # FORMULARIO 1: EQUIPOS (IMAGEN 3)
    # ------------------------------------------
    if st.session_state["sub_seccion_mas"] == "EQUIPOS":
        st.markdown(
            '<div class="section-title">REGISTRO DE EQUIPOS</div>',
            unsafe_allow_html=True,
        )

        c_tipo, c_num, c_marca, c_mod, c_serie, c_inv = st.columns(
            [1.5, 1, 1.5, 1.5, 1.5, 1.5]
        )

        with c_tipo:
            st.write("**TIPO**")
            tipo_eq = st.radio(
                "Selecciona Tipo",
                ["GABS", "CENT", "MICR", "BAAG"],
                key="req_tipo",
            )

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
        st.write("**UBICACIÓN**")
        u1, u2, u3, u4, u5, u6, u7 = st.columns(7)
        ubicaciones = []
        with u1:
            ubicaciones.append(st.text_input("Lab/Piso", key="eq_u1"))
        with u2:
            ubicaciones.append(st.text_input("Área", key="eq_u2"))
        with u3:
            ubicaciones.append(st.text_input("Mesa", key="eq_u3"))
        with u4:
            ubicaciones.append(st.text_input("Estante", key="eq_u4"))
        with u5:
            ubicaciones.append(st.text_input("Pos 1", key="eq_u5"))
        with u6:
            ubicaciones.append(st.text_input("Pos 2", key="eq_u6"))
        with u7:
            ubicaciones.append(st.text_input("Notas", key="eq_u7"))

        st.write("")
        st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
        if st.button("HECHO", key="btn_hecho_equipos"):
            nuevo_registro = {
                "Fecha_Hora": obtener_hora_cdmx(),
                "Tipo": tipo_eq,
                "Numero": num_eq,
                "Marca": marca_eq,
                "Modelo": modelo_eq,
                "Serie": serie_eq,
                "Inventario": inv_eq,
                "Ubicación": " | ".join([u for u in ubicaciones if u]),
            }
            st.session_state["inventario_equipos"].append(nuevo_registro)
            st.success("✅ Equipo registrado exitosamente en el sistema.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------
    # FORMULARIO 2: CONDICIONES AMBIENTALES (IMAGEN 2)
    # ------------------------------------------
    elif st.session_state["sub_seccion_mas"] == "CONDICIONES AMBIENTALES":
        st.markdown(
            '<div class="section-title">CONDICIONES AMBIENTALES</div>',
            unsafe_allow_html=True,
        )

        ca_tipo, ca_rangos, ca_inst, ca_corr = st.columns([1.5, 1.2, 2, 2.5])

        with ca_tipo:
            st.write("**TIPO**")
            tipo_amb = st.radio(
                "Variable", ["TEMP", "%H"], key="radio_tipo_amb"
            )

        with ca_rangos:
            st.write("**MÍNIMO**")
            val_min = st.text_input("MIN", key="ca_min")
            st.write("**MÁXIMO**")
            val_max = st.text_input("MAX", key="ca_max")

        with ca_inst:
            st.write("**INSTRUMENTO MEDICIÓN**")
            inst_medicion = st.text_area("Descripción / Código", key="ca_inst")

        with ca_corr:
            st.write("**CORRECCIÓN**")
            if tipo_amb == "%H":
                st.caption("Rangos de Humedad Relative (%H):")
                r_h = st.selectbox(
                    "Seleccione Rango",
                    [
                        "10 - 20",
                        "20.1 - 30",
                        "30.1 - 40",
                        "40.1 - 50",
                        "50.1 - 60",
                        "60.1 - 70",
                        "70.1 - 80",
                        "80.1 - 100",
                        "N/A",
                    ],
                    key="select_corr_h",
                )
                val_corr_h = st.text_input("Valor Corrección", key="val_corr_h")
            else:
                st.caption("Rangos de Temperatura (TEMP °C):")
                r_temp = st.selectbox(
                    "Seleccione Rango",
                    [
                        "10 - 15",
                        "15.1 - 20",
                        "20.1 - 25",
                        "25.1 - 30",
                        "30.1 - 35",
                        "N/A",
                    ],
                    key="select_corr_temp",
                )
                val_corr_t = st.text_input(
                    "Valor Corrección", key="val_corr_t"
                )

        st.write("")
        st.write("**UBICACIÓN**")
        u1, u2, u3, u4, u5, u6, u7 = st.columns(7)
        ubic_amb = []
        with u1:
            ubic_amb.append(st.text_input("Lab", key="ca_u1"))
        with u2:
            ubic_amb.append(st.text_input("Zona", key="ca_u2"))
        with u3:
            ubic_amb.append(st.text_input("Punto", key="ca_u3"))
        with u4:
            ubic_amb.append(st.text_input("Sensor", key="ca_u4"))
        with u5:
            ubic_amb.append(st.text_input("Piso", key="ca_u5"))
        with u6:
            ubic_amb.append(st.text_input("Ref 1", key="ca_u6"))
        with u7:
            ubic_amb.append(st.text_input("Ref 2", key="ca_u7"))

        st.write("")
        st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
        if st.button("HECHO", key="btn_hecho_ambientales"):
            reg_amb = {
                "Fecha_Hora": obtener_hora_cdmx(),
                "Tipo": tipo_amb,
                "Min": val_min,
                "Max": val_max,
                "Instrumento": inst_medicion,
                "Correccion_Rango": r_h if tipo_amb == "%H" else r_temp,
                "Ubicación": " | ".join([u for u in ubic_amb if u]),
            }
            st.session_state["condiciones_ambientales_db"].append(reg_amb)
            st.success("✅ Condición ambiental guardada exitosamente.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------
    # FORMULARIO 3: CONDICIONES DE EQUIPOS (IMAGEN 1)
    # ------------------------------------------
    elif st.session_state["sub_seccion_mas"] == "CONDICIONES DE EQUIPOS":
        st.markdown(
            '<div class="section-title">CONDICIONES DE EQUIPOS</div>',
            unsafe_allow_html=True,
        )

        ce_tipo, ce_datos, ce_corr = st.columns([1.5, 3.5, 3])

        with ce_tipo:
            st.write("**TIPO EQUIPO**")
            tipo_ce = st.radio(
                "Seleccionar",
                ["CONG", "REFR", "1CO2", "ULTRO"],
                key="radio_ce_tipo",
            )

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
            st.write("**CORRECCIÓN SEGÚN TIPO**")
            if tipo_ce == "CONG":
                rango_ce = st.selectbox(
                    "Rango Congelador (°C)",
                    ["-25 a -20", "-19.9 a -15", "-14.9 a -10", "N/A"],
                    key="ce_rango_cong",
                )
            elif tipo_ce == "REFR":
                rango_ce = st.selectbox(
                    "Rango Refrigerador (°C)",
                    ["2 a 5", "5.1 a 8", "8.1 a 10", "N/A"],
                    key="ce_rango_refr",
                )
            elif tipo_ce == "1CO2":
                rango_ce = st.selectbox(
                    "Rango Incubadora CO2",
                    ["36.0 a 37.5 °C", "4.5% a 5.5% CO2", "N/A"],
                    key="ce_rango_co2",
                )
            else:  # ULTRO
                rango_ce = st.selectbox(
                    "Rango Ultracongelador (°C)",
                    ["-85 a -80", "-79.9 a -70", "-69.9 a -60", "N/A"],
                    key="ce_rango_ultro",
                )

            val_ce_corr = st.text_input(
                "Valor Ajuste / Corrección", key="ce_val_corr"
            )

        st.write("")
        st.write("**UBICACIÓN**")
        u1, u2, u3, u4, u5, u6, u7 = st.columns(7)
        ubic_ce = []
        with u1:
            ubic_ce.append(st.text_input("Lab", key="ce_u1"))
        with u2:
            ubic_ce.append(st.text_input("Sala", key="ce_u2"))
        with u3:
            ubic_ce.append(st.text_input("Posición", key="ce_u3"))
        with u4:
            ubic_ce.append(st.text_input("Piso", key="ce_u4"))
        with u5:
            ubic_ce.append(st.text_input("Sector", key="ce_u5"))
        with u6:
            ubic_ce.append(st.text_input("Ref 1", key="ce_u6"))
        with u7:
            ubic_ce.append(st.text_input("Ref 2", key="ce_u7"))

        st.write("")
        st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
        if st.button("HECHO", key="btn_hecho_cond_equipos"):
            reg_ce = {
                "Fecha_Hora": obtener_hora_cdmx(),
                "Tipo_Equipo": tipo_ce,
                "Numero": ce_num,
                "Marca": ce_marca,
                "Modelo": ce_mod,
                "Serie": ce_serie,
                "Inventario": ce_inv,
                "Rango_Correccion": rango_ce,
                "Valor_Correccion": val_ce_corr,
                "Ubicación": " | ".join([u for u in ubic_ce if u]),
            }
            st.session_state["condiciones_equipos_db"].append(reg_ce)
            st.success("✅ Condición de equipo guardada correctamente.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# FILA 3 (OPCIÓN B): NAVEGACIÓN NORMAL POR LABORATORIO
# ==========================================
elif st.session_state["lab_seleccionado"] is not None:
    lab_actual = st.session_state["lab_seleccionado"]

    col3_1, col3_2, col3_3 = st.columns([1, 1, 1])

    with col3_1:
        if st.button(
            f"USO DE EQUIPOS ({lab_actual})", key="btn_uso_equipos"
        ):
            st.session_state["sub_seccion_lab"] = "USO DE EQUIPOS"

    with col3_2:
        if st.button(
            f"CONDICIONES AMBIENTALES ({lab_actual})", key="btn_cond_amb_lab"
        ):
            st.session_state["sub_seccion_lab"] = "CONDICIONES AMBIENTALES"

    with col3_3:
        if st.button(
            f"CONDICIONES DE EQUIPOS ({lab_actual})", key="btn_cond_eq_lab"
        ):
            st.session_state["sub_seccion_lab"] = "CONDICIONES DE EQUIPOS"

    st.write("")

    if st.session_state["sub_seccion_lab"] == "USO DE EQUIPOS":
        if lab_actual == "503":
            st.subheader("Control de Equipos en Tiempo Real — Lab 503")

            col_inicio, col_linea, col_final = st.columns([4, 0.2, 4])

            with col_inicio:
                st.markdown(
                    "<h3 style='color:#2A9D8F; text-align:center;'>INICIO</h3>",
                    unsafe_allow_html=True,
                )
                for eq in equipos_list:
                    estado_actual = st.session_state[f"estado_{eq}"]
                    lbl = (
                        f"🟢 {eq} (EN CURSO)"
                        if estado_actual == "EN_USO"
                        else f"🔵 {eq}"
                    )

                    if st.button(lbl, key=f"btn_inc_{eq}"):
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
                        st.toast(f"Inicio de {eq} a las {ts}")
                        st.rerun()

            with col_linea:
                st.markdown(
                    "<div style='border-left: 2px solid #0077B6; height: 280px; margin: auto;'></div>",
                    unsafe_allow_html=True,
                )

            with col_final:
                st.markdown(
                    "<h3 style='color:#E63946; text-align:center;'>FINAL</h3>",
                    unsafe_allow_html=True,
                )
                for eq in equipos_list:
                    estado_actual = st.session_state[f"estado_{eq}"]
                    lbl_fin = (
                        f"🔴 {eq} (CONCLUIDO)"
                        if estado_actual == "FINALIZADO"
                        else f"🔵 {eq}"
                    )

                    if st.button(lbl_fin, key=f"btn_fin_{eq}"):
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
                        st.toast(f"Finalización de {eq} a las {ts}")
                        st.rerun()

            st.markdown("---")
            st.subheader("📋 Historial de Pulsos (Hora CDMX)")
            if st.session_state["historial_registros"]:
                df_hist = pd.DataFrame(st.session_state["historial_registros"])
                st.dataframe(df_hist, use_container_width=True)
            else:
                st.info("Sin registros de inicio/final aún.")

        else:
            st.subheader(f"Laboratorio {lab_actual}")
            st.caption("No hay equipos activos configurados aún.")

    elif st.session_state["sub_seccion_lab"] == "CONDICIONES AMBIENTALES":
        st.subheader(f"Monitoreo Ambiental — Laboratorio {lab_actual}")
        if st.session_state["condiciones_ambientales_db"]:
            st.dataframe(
                pd.DataFrame(st.session_state["condiciones_ambientales_db"]),
                use_container_width=True,
            )
        else:
            st.info("Aún no hay registros cargados desde el menú ➕.")

    elif st.session_state["sub_seccion_lab"] == "CONDICIONES DE EQUIPOS":
        st.subheader(f"Estado de Equipos — Laboratorio {lab_actual}")
        if st.session_state["condiciones_equipos_db"]:
            st.dataframe(
                pd.DataFrame(st.session_state["condiciones_equipos_db"]),
                use_container_width=True,
            )
        else:
            st.info("Aún no hay registros cargados desde el menú ➕.")
