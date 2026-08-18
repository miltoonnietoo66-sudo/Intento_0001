import streamlit as st

# Configuración inicial de la página
st.set_page_config(page_title="Sistema INER", layout="wide")

# CSS personalizado: Fondo blanco, texto rojo para botones y bordes/etiquetas en azul
st.markdown(
    """
    <style>
    /* Fondo general blanco */
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }

    /* Reducir espacio superior */
    .block-container {
        padding-top: 1.5rem;
    }

    /* Estilo para los botones (Letras en rojo, bordes azules) */
    div[data-testid="stButton"] > button {
        color: #E63946 !important; /* Rojo */
        font-weight: bold !important;
        background-color: #FFFFFF !important;
        border: 2px solid #0077B6 !important; /* Azul de la imagen */
        border-radius: 4px !important;
        width: 100% !important;
        height: 2.8rem !important;
        font-size: 0.95rem !important;
    }

    div[data-testid="stButton"] > button:hover {
        background-color: #F0F8FF !important;
        border-color: #023E8A !important;
    }

    /* Estilo para etiquetas estáticas de la matriz (Texto y bordes azules) */
    .label-box {
        border: 2px solid #0077B6; /* Azul de la imagen */
        background-color: #FFFFFF;
        color: #0077B6; /* Azul de la imagen */
        font-weight: bold;
        text-align: center;
        padding: 0.5rem;
        border-radius: 4px;
        height: 2.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Inicialización de estado de sesión para controlar qué laboratorio está seleccionado
if "lab_seleccionado" not in st.session_state:
    st.session_state["lab_seleccionado"] = None

if "sub_seccion" not in st.session_state:
    st.session_state["sub_seccion"] = None

# ==========================================
# FILA 1: INER | BUSCAR (Botón) | LIT
# ==========================================
col1_1, col1_2, col1_3 = st.columns([1, 2, 1])

with col1_1:
    st.markdown('<div class="label-box">INER</div>', unsafe_allow_html=True)

with col1_2:
    if st.button("BUSCAR", key="btn_buscar"):
        st.toast("Función de búsqueda activada")

with col1_3:
    st.markdown('<div class="label-box">LIT</div>', unsafe_allow_html=True)

st.write("")  # Espaciador vertical

# ==========================================
# FILA 2: LABORATORIOS | 502 | 503 | 504 | 506 | 507 | 508 | 510 | 🏠
# ==========================================
col2_widths = [2, 1, 1, 1, 1, 1, 1, 1, 1]

cols_f2 = st.columns(col2_widths)

# Columna 'LABORATORIOS' como etiqueta estática azul
with cols_f2[0]:
    st.markdown('<div class="label-box">LABORATORIOS</div>', unsafe_allow_html=True)

# Botones de laboratorios con número "5" en lugar de "S"
labs = ["502", "503", "504", "506", "507", "508", "510", "INICIO"]

for idx, lab in enumerate(labs, start=1):
    with cols_f2[idx]:
        etiqueta = "🏠" if lab == "INICIO" else lab
        if st.button(etiqueta, key=f"btn_{lab}"):
            if lab == "INICIO":
                st.session_state["lab_seleccionado"] = None
                st.session_state["sub_seccion"] = None
            else:
                st.session_state["lab_seleccionado"] = lab

# ==========================================
# FILA 3: USO DE EQUIPOS | CONDICIONES (Se despliega tras pulsar un laboratorio)
# ==========================================
if st.session_state["lab_seleccionado"] is not None:
    st.write("")
    col3_1, col3_2 = st.columns([1, 1])

    with col3_1:
        if st.button(f"USO DE EQUIPOS ({st.session_state['lab_seleccionado']})", key="btn_equipos"):
            st.session_state["sub_seccion"] = "USO DE EQUIPOS"

    with col3_2:
        if st.button(f"CONDICIONES ({st.session_state['lab_seleccionado']})", key="btn_condiciones"):
            st.session_state["sub_seccion"] = "CONDICIONES"

    # ==========================================
    # ÁREA PRINCIPAL DE CONTENIDO
    # ==========================================
    st.markdown("---")
    st.subheader(f"Laboratorio Seleccionado: {st.session_state['lab_seleccionado']}")

    if st.session_state["sub_seccion"]:
        st.info(f"Vista activa: **{st.session_state['sub_seccion']}**")
    else:
        st.caption("Selecciona 'USO DE EQUIPOS' o 'CONDICIONES' para ver la información.")
else:
    st.markdown("---")
    st.caption("👈 Selecciona un laboratorio de la Fila 2 para desplegar las opciones.")
