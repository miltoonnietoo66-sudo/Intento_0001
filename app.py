from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Sistema INER - Gestión de Laboratorios", layout="wide"
)

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

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Estilo Cajas Azules Fila 1 */
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

    /* Estilo general para botones estándar */
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

    /* Botón HECHO */
    .btn-hecho div[data-testid="stButton"] > button {
        background-color: #2A9D8F !important;
        color: #FFFFFF !important;
        border: 2px solid #2A9D8F !important;
        font-size: 1.1rem !important;
    }

    /* Títulos de sección */
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

# Selección de botones interactivos
if "sel_tipo_equipo" not in st.session_state:
    st.session_state["sel_tipo_equipo"] = "GABS"

if "sel_ubicacion_lab" not in st.session_state:
    st.session_state["sel_ubicacion_lab"] = "502"

if "sel_tipo_amb" not in st.session_state:
    st.session_state["sel_tipo_amb"] = "TEMP"

if "sel_tipo_ce" not in st.session_state:
    st.session_state["sel_tipo_ce"] = "CONG"

# Bases de datos internas
if "inventario_equipos" not in st.session_state:
    st.session_state["inventario_equipos"] = []

if "condiciones_ambientales_db" not in st.session_state:
    st.session_state["condiciones_ambientales_db"] = []

if "condiciones_equipos_db" not in st.session_state:
    st.session_state["condiciones_equipos_db"] = []

labs_lista = ["502", "503", "504", "506", "507", "508", "510", "513", "514"]


def obtener_hora_cdmx():
    return datetime.now(TZ_CDMX).strftime("%d/%m/%Y %H:%M:%S")


# Generador de CSS para botones resaltados en verde
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
labs_menu = labs_lista + ["INICIO", "MAS"]
cols_f2 = st.columns([2] + [1] * (len(labs_menu)))

with cols_f2[0]:
    st.markdown('<div class="label-box">LABORATORIOS</div>', unsafe_allow_html=True)

for idx, lab in enumerate(labs_menu, start=1):
    with cols_f2[idx]:
        etiqueta = "🏠" if lab == "INICIO" else ("➕" if lab == "MAS" else lab)

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
# FILA 3: MENÚ DEL BOTÓN "+"
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
            tipos_eq = ["GABS", "CENT", "MICR", "BAAG"]
            for teq in tipos_eq:
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
            nuevo_registro = {
                "Fecha_Hora": obtener_hora_cdmx(),
                "Tipo": st.session_state["sel_tipo_equipo"],
                "Numero": num_eq,
                "Marca": marca_eq,
                "Modelo": modelo_eq,
                "Serie": serie_eq,
                "Inventario": inv_eq,
                "Ubicación": f"LAB {st.session_state['sel_ubicacion_lab']}",
            }
            st.session_state["inventario_equipos"].append(nuevo_registro)
            st.success("✅ Equipo guardado exitosamente.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------
    # FORMULARIO 2: CONDICIONES AMBIENTALES (IMAGEN 2)
    # ------------------------------------------
    elif st.session_state["sub_seccion_mas"] == "CONDICIONES AMBIENTALES":
        st.markdown(
            '<div class="section-title">CONDICIONES AMBIENTALES</div>',
            unsafe_allow_html=True,
        )

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
            if st.session_state["sel_tipo_amb"] == "%H":
                rangos_h = [
                    "10 - 20",
                    "20.1 - 30",
                    "30.1 - 40",
                    "40.1 - 50",
                    "50.1 - 60",
                    "60.1 - 70",
                    "70.1 - 80",
                    "80.1 - 100",
                    "N/A",
                ]
                df_corr = pd.DataFrame(
                    {"Rango %H": rangos_h, "Corrección": [""] * len(rangos_h)}
                )
            else:
                rangos_t = [
                    "10 - 15",
                    "15.1 - 20",
                    "20.1 - 25",
                    "25.1 - 30",
                    "30.1 - 35",
                    "N/A",
                ]
                df_corr = pd.DataFrame(
                    {
                        "Rango TEMP (°C)": rangos_t,
                        "Corrección": [""] * len(rangos_t),
                    }
                )

            tabla_corr_amb = st.data_editor(
                df_corr,
                hide_index=True,
                use_container_width=True,
                key="editor_corr_amb",
            )

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
            reg_amb = {
                "Fecha_Hora": obtener_hora_cdmx(),
                "Tipo": st.session_state["sel_tipo_amb"],
                "Min": val_min,
                "Max": val_max,
                "Instrumento": inst_medicion,
                "Correcciones": tabla_corr_amb.to_dict(orient="records"),
                "Ubicación": f"LAB {st.session_state['sel_ubicacion_lab']}",
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
            tipo_actual = st.session_state["sel_tipo_ce"]
            if tipo_actual == "CONG":
                r_list = ["-25 a -20", "-19.9 a -15", "-14.9 a -10", "N/A"]
            elif tipo_actual == "REFR":
                r_list = ["2 a 5", "5.1 a 8", "8.1 a 10", "N/A"]
            elif tipo_actual == "1CO2":
                r_list = ["36.0 a 37.5 °C", "4.5% a 5.5% CO2", "N/A"]
            else:  # ULTRO
                r_list = ["-85 a -80", "-79.9 a -70", "-69.9 a -60", "N/A"]

            df_ce_corr = pd.DataFrame(
                {"Rango": r_list, "Corrección": [""] * len(r_list)}
            )
            tabla_ce_corr = st.data_editor(
                df_ce_corr,
                hide_index=True,
                use_container_width=True,
                key="editor_ce_corr",
            )

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
            reg_ce = {
                "Fecha_Hora": obtener_hora_cdmx(),
                "Tipo_Equipo": st.session_state["sel_tipo_ce"],
                "Numero": ce_num,
                "Marca": ce_marca,
                "Modelo": ce_mod,
                "Serie": ce_serie,
                "Inventario": ce_inv,
                "Correcciones": tabla_ce_corr.to_dict(orient="records"),
                "Ubicación": f"LAB {st.session_state['sel_ubicacion_lab']}",
            }
            st.session_state["condiciones_equipos_db"].append(reg_ce)
            st.success("✅ Condición de equipo guardada correctamente.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# FILA 3 (NAVEGACIÓN NORMAL)
# ==========================================
elif st.session_state["lab_seleccionado"] is not None:
    lab_actual = st.session_state["lab_seleccionado"]
    st.subheader(f"Vista General — Laboratorio {lab_actual}")
    st.caption("Selecciona una opción del menú interactivo para continuar.")
