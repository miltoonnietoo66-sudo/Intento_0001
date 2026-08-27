import sqlite3
import pytz
from datetime import datetime
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. CONFIGURACIÓN INICIAL DE STREAMLIT Y ESTILOS CSS
# ==============================================================================
st.set_page_config(
    page_title="Gestión de Laboratorio - INER",
    page_layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .section-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #0077B6;
        margin-bottom: 10px;
    }
    .oval-corregido {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 6px 12px;
        border-radius: 15px;
        text-align: center;
        font-weight: bold;
        margin-top: 5px;
    }
    .btn-hecho button {
        background-color: #2A9D8F !important;
        color: white !important;
        width: 100%;
    }
    .btn-eliminar button {
        background-color: #E63946 !important;
        color: white !important;
        width: 100%;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. BASE DE DATOS Y FUNCIONES AUXILIARES
# ==============================================================================
DB_NAME = "laboratorio.db"


def obtener_conexion():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_bd():
    conn = obtener_conexion()
    cursor = conn.cursor()

    # Tabla de equipos generales para control de uso
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

    # Tabla de configuración de condiciones ambientales (Temp / Humedad)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config_condiciones_ambientales (
        id TEXT PRIMARY KEY,
        tipo TEXT,
        ubicacion_lab TEXT
    )
    """)

    # Tabla de configuración de condiciones de equipos (Congeladores, Refrigeradores, etc.)
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

    # Tabla de rangos de corrección
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS correcciones_rangos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entidad_id TEXT,
        rango TEXT,
        correccion REAL
    )
    """)

    # Registros de uso (Inicio / Final)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registros_uso (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipo_id TEXT,
        accion TEXT,
        fecha_hora_cdmx TEXT
    )
    """)

    # Mediciones Ambientales
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

    # Mediciones de Equipos
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


def obtener_hora_cdmx():
    tz = pytz.timezone("America/Mexico_City")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


def calcular_correccion_valor(valor, tabla_correcciones):
    if valor is None:
        return None, 0.0
    for reg in tabla_correcciones:
        rango_str = reg.get("rango", reg.get("Rango", ""))
        corr = float(reg.get("correccion", reg.get("Corrección", 0.0)))
        try:
            if "a" in rango_str:
                partes = rango_str.split("a")
                v_min, v_max = float(partes[0].strip()), float(
                    partes[1].strip()
                )
                if v_min <= valor <= v_max:
                    return round(valor + corr, 2), corr
        except ValueError:
            continue
    return round(valor, 2), 0.0


# Carga de datos
def cargar_equipos(lab):
    conn = obtener_conexion()
    equipos = pd.read_sql_query(
        "SELECT * FROM equipos WHERE ubicacion_lab = ?", conn, params=(lab,)
    ).to_dict(orient="records")
    conn.close()
    return equipos


def cargar_registros_uso(equipo_id):
    conn = obtener_conexion()
    registros = pd.read_sql_query(
        "SELECT accion AS Acción, fecha_hora_cdmx AS FechaHora_CDMX FROM registros_uso WHERE equipo_id = ? ORDER BY id DESC",
        conn,
        params=(equipo_id,),
    ).to_dict(orient="records")
    conn.close()
    return registros


def cargar_condicion_ambiental_config(lab, tipo):
    conn = obtener_conexion()
    cfg = pd.read_sql_query(
        "SELECT * FROM config_condiciones_ambientales WHERE ubicacion_lab = ? AND tipo = ?",
        conn,
        params=(lab, tipo),
    ).to_dict(orient="records")
    if cfg:
        cfg_item = cfg[0]
        corrs = pd.read_sql_query(
            "SELECT rango, correccion FROM correcciones_rangos WHERE entidad_id = ?",
            conn,
            params=(cfg_item["id"],),
        ).to_dict(orient="records")
        cfg_item["Correcciones"] = corrs
        conn.close()
        return cfg_item
    conn.close()
    return None


def cargar_condiciones_equipos_db(lab):
    conn = obtener_conexion()
    configs = pd.read_sql_query(
        "SELECT * FROM config_condiciones_equipos WHERE ubicacion_lab = ?",
        conn,
        params=(lab,),
    ).to_dict(orient="records")
    resultado = []
    for c in configs:
        corrs = pd.read_sql_query(
            "SELECT rango, correccion FROM correcciones_rangos WHERE entidad_id = ?",
            conn,
            params=(c["id"],),
        ).to_dict(orient="records")
        resultado.append({
            "id_ce": c["id"],
            "Tipo_Equipo": c["tipo_equipo"],
            "Numero": c["numero"],
            "Correcciones": corrs,
        })
    conn.close()
    return resultado


def aplicar_estilo_seleccion(key):
    st.markdown(
        f"""
        <style>
        div[data-testid="stButton"] > button[key="{key}"] {{
            background-color: #0077B6 !important;
            color: white !important;
            border-color: #0077B6 !important;
        }}
        </style>
    """,
        unsafe_allow_html=True,
    )


# Inicializar base de datos al arrancar
inicializar_bd()

# ==============================================================================
# 3. CONTROL DE ESTADO DE SESIÓN (SESSION STATE)
# ==============================================================================
if "modo_operacion" not in st.session_state:
    st.session_state["modo_operacion"] = "REGULAR"
if "sub_categoria" not in st.session_state:
    st.session_state["sub_categoria"] = "EQUIPOS"
if "lab_seleccionado" not in st.session_state:
    st.session_state["lab_seleccionado"] = "1"
if "item_editar_id" not in st.session_state:
    st.session_state["item_editar_id"] = None
if "equipo_activo_id" not in st.session_state:
    st.session_state["equipo_activo_id"] = None

labs_lista = ["1", "2", "3", "4", "5", "6", "BC"]

# ==============================================================================
# 4. BARRA SUPERIOR Y NAVEGACIÓN
# ==============================================================================
st.title("🧪 Control de Equipos y Condiciones Ambientales - INER")

col_labs, col_sub, col_modos = st.columns([4, 4, 2])

with col_labs:
    st.write("**LABORATORIOS**")
    cols_b_labs = st.columns(len(labs_lista))
    for i, l in enumerate(labs_lista):
        btn_k = f"btn_lab_{l}"
        if st.session_state["lab_seleccionado"] == l:
            aplicar_estilo_seleccion(btn_k)
        if cols_b_labs[i].button(l, key=btn_k):
            st.session_state["lab_seleccionado"] = l
            st.session_state["equipo_activo_id"] = None
            st.rerun()

with col_sub:
    st.write("**CATEGORÍA**")
    sub_opts = ["EQUIPOS", "CONDICIONES AMBIENTALES", "CONDICIONES DE EQUIPOS"]
    cols_sub = st.columns(3)
    for i, s_opt in enumerate(sub_opts):
        btn_k_sub = f"btn_sub_{i}"
        if st.session_state["sub_categoria"] == s_opt:
            aplicar_estilo_seleccion(btn_k_sub)
        if cols_sub[i].button(s_opt, key=btn_k_sub):
            st.session_state["sub_categoria"] = s_opt
            st.session_state["item_editar_id"] = None
            st.rerun()

with col_modos:
    st.write("**MODO**")
    c_m1, c_m2, c_m3 = st.columns(3)
    if c_m1.button("📋", help="Modo Regular / Uso"):
        st.session_state["modo_operacion"] = "REGULAR"
        st.rerun()
    if c_m2.button("➕", help="Modo Alta / Agregar"):
        st.session_state["modo_operacion"] = "ALTA"
        st.rerun()
    if c_m3.button("➖", help="Modo Edición / Eliminar"):
        st.session_state["modo_operacion"] = "EDITAR"
        st.rerun()

st.divider()

# ==============================================================================
# 5. MODO ALTA (AGREGAR NUEVOS REGISTROS)
# ==============================================================================
if st.session_state["modo_operacion"] == "ALTA":
    st.header("➕ Altas y Configuraciones")

    if st.session_state["sub_categoria"] == "EQUIPOS":
        st.markdown(
            '<div class="section-title">DAR DE ALTA NUEVO EQUIPO DE'
            " LABORATORIO</div>",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            eq_tipo = st.text_input("TIPO (ej. CENTRIFUGA, TERMOCICLADOR)")
            eq_num = st.text_input("NÚMERO / ID")
            eq_lab = st.selectbox("LABORATORIO", labs_lista)
        with c2:
            eq_marca = st.text_input("MARCA")
            eq_mod = st.text_input("MODELO")
        with c3:
            eq_serie = st.text_input("SERIE")
            eq_inv = st.text_input("INVENTARIO")

        if st.button("GUARDAR EQUIPO", key="btn_add_eq"):
            if eq_tipo and eq_num:
                eq_id = f"{eq_tipo}-{eq_num}_{eq_lab}"
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO equipos VALUES (?, ?, ?, ?, ?, ?,"
                    " ?, ?)",
                    (
                        eq_id,
                        eq_tipo,
                        eq_num,
                        eq_marca,
                        eq_mod,
                        eq_serie,
                        eq_inv,
                        eq_lab,
                    ),
                )
                conn.commit()
                conn.close()
                st.success("✅ Equipo registrado exitosamente.")
            else:
                st.error("⚠️ El tipo y el número son requeridos.")

    elif st.session_state["sub_categoria"] == "CONDICIONES AMBIENTALES":
        st.markdown(
            '<div class="section-title">CONFIGURAR CONDICIÓN AMBIENTAL (TEMP /'
            " %H)</div>",
            unsafe_allow_html=True,
        )
        ca_tipo = st.selectbox("TIPO DE MEDICIÓN", ["TEMP", "%H"])
        ca_lab = st.selectbox("LABORATORIO", labs_lista)

        r_default = (
            ["15 a 20", "20.1 a 25", "25.1 a 30"]
            if ca_tipo == "TEMP"
            else ["30 a 50", "50.1 a 70"]
        )
        df_ca_rangos = pd.DataFrame(
            {"Rango": r_default, "Corrección": [0.0] * len(r_default)}
        )

        st.write("**TABLA DE CORRECCIONES DE RANGOS**")
        tabla_ca_corr = st.data_editor(
            df_ca_rangos, hide_index=True, use_container_width=True
        )

        if st.button("GUARDAR CONFIGURACIÓN AMBIENTAL", key="btn_add_ca"):
            ca_id = f"AMB_{ca_tipo}_{ca_lab}"
            conn = obtener_conexion()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO config_condiciones_ambientales VALUES"
                " (?, ?, ?)",
                (ca_id, ca_tipo, ca_lab),
            )
            cursor.execute(
                "DELETE FROM correcciones_rangos WHERE entidad_id = ?",
                (ca_id,),
            )
            for _, fila in tabla_ca_corr.iterrows():
                cursor.execute(
                    "INSERT INTO correcciones_rangos (entidad_id, rango,"
                    " correccion) VALUES (?, ?, ?)",
                    (ca_id, str(fila["Rango"]), float(fila["Corrección"])),
                )
            conn.commit()
            conn.close()
            st.success("✅ Configuración ambiental guardada.")

    elif st.session_state["sub_categoria"] == "CONDICIONES DE EQUIPOS":
        st.markdown(
            '<div class="section-title">CONFIGURAR MONITOREO DE EQUIPO'
            " (CONG/REFR/ULTRO/1CO2)</div>",
            unsafe_allow_html=True,
        )
        ce_tipo = st.selectbox("TIPO DE EQUIPO", ["CONG", "REFR", "1CO2", "ULTRO"])
        ce_num = st.text_input("NÚMERO")
        ce_lab = st.selectbox("LABORATORIO", labs_lista)

        c1, c2, c3 = st.columns(3)
        with c1:
            ce_marca = st.text_input("MARCA", key="add_ce_m")
        with c2:
            ce_mod = st.text_input("MODELO", key="add_ce_mod")
        with c3:
            ce_serie = st.text_input("SERIE", key="add_ce_s")

        ce_inv = st.text_input("INVENTARIO", key="add_ce_inv")

        r_list = (
            ["-25 a -20", "-19.9 a -15", "-14.9 a -10"]
            if ce_tipo == "CONG"
            else (
                ["2 a 5", "5.1 a 8", "8.1 a 10"]
                if ce_tipo == "REFR"
                else (
                    ["36.0 a 37.5", "4.5 a 5.5"]
                    if ce_tipo == "1CO2"
                    else ["-85 a -80", "-79.9 a -70", "-69.9 a -60"]
                )
            )
        )
        df_ce_rangos = pd.DataFrame(
            {"Rango": r_list, "Corrección": [0.0] * len(r_list)}
        )

        st.write("**TABLA DE CORRECCIONES DE RANGOS**")
        tabla_ce_corr = st.data_editor(
            df_ce_rangos, hide_index=True, use_container_width=True
        )

        if st.button("GUARDAR EQUIPO DE MONITOREO", key="btn_add_ce"):
            if ce_num:
                ce_id = f"{ce_tipo}-{ce_num}_{ce_lab}"
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO config_condiciones_equipos VALUES"
                    " (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        ce_id,
                        ce_tipo,
                        ce_num,
                        ce_marca,
                        ce_mod,
                        ce_serie,
                        ce_inv,
                        ce_lab,
                    ),
                )
                cursor.execute(
                    "DELETE FROM correcciones_rangos WHERE entidad_id = ?",
                    (ce_id,),
                )
                for _, fila in tabla_ce_corr.iterrows():
                    cursor.execute(
                        "INSERT INTO correcciones_rangos (entidad_id, rango,"
                        " correccion) VALUES (?, ?, ?)",
                        (ce_id, str(fila["Rango"]), float(fila["Corrección"])),
                    )
                conn.commit()
                conn.close()
                st.success("✅ Equipo de monitoreo guardado.")

# ==============================================================================
# 6. MODO EDITAR / ELIMINAR
# ==============================================================================
elif st.session_state["modo_operacion"] == "EDITAR":
    st.header("➖ Modificación y Bajas")

    if st.session_state["sub_categoria"] == "CONDICIONES DE EQUIPOS":
        st.markdown(
            '<div class="section-title">SELECCIONA UN EQUIPO DE MONITOREO PARA'
            " EDITAR O ELIMINAR</div>",
            unsafe_allow_html=True,
        )
        conn = obtener_conexion()
        configs_ce = pd.read_sql_query(
            "SELECT * FROM config_condiciones_equipos", conn
        ).to_dict(orient="records")
        conn.close()

        if not configs_ce:
            st.info("No hay equipos de monitoreo configurados.")
        else:
            cols_grid = st.columns(4)
            for idx, ce in enumerate(configs_ce):
                with cols_grid[idx % 4]:
                    lbl_btn = f"{ce['tipo_equipo']}-{ce['numero']} (Lab"
                    f" {ce['ubicacion_lab']})"
                    btn_key = f"btn_sel_ce_{ce['id']}"
                    if st.session_state["item_editar_id"] == ce["id"]:
                        aplicar_estilo_seleccion(btn_key)
                    if st.button(lbl_btn, key=btn_key):
                        st.session_state["item_editar_id"] = ce["id"]
                        st.rerun()

        if st.session_state["item_editar_id"]:
            ce_target = next(
                (
                    c
                    for c in configs_ce
                    if c["id"] == st.session_state["item_editar_id"]
                ),
                None,
            )
            if ce_target:
                st.markdown("---")
                st.markdown(
                    '<div class="section-title">EDITANDO EQUIPO DE MONITOREO:'
                    f' {ce_target["id"]}</div>',
                    unsafe_allow_html=True,
                )

                conn = obtener_conexion()
                df_ce_rangos_bd = pd.read_sql_query(
                    "SELECT rango AS Rango, correccion AS Corrección FROM"
                    " correcciones_rangos WHERE entidad_id = ?",
                    conn,
                    params=(ce_target["id"],),
                )
                conn.close()

                if df_ce_rangos_bd.empty:
                    t_act = ce_target["tipo_equipo"]
                    r_list = (
                        ["-25 a -20", "-19.9 a -15", "-14.9 a -10"]
                        if t_act == "CONG"
                        else (
                            ["2 a 5", "5.1 a 8", "8.1 a 10"]
                            if t_act == "REFR"
                            else (
                                ["36.0 a 37.5", "4.5 a 5.5"]
                                if t_act == "1CO2"
                                else ["-85 a -80", "-79.9 a -70", "-69.9 a -60"]
                            )
                        )
                    )
                    df_ce_rangos_bd = pd.DataFrame(
                        {"Rango": r_list, "Corrección": [0.0] * len(r_list)}
                    )

                ce_tipo, ce_datos, ce_corr = st.columns([1.2, 3.5, 3.5])
                with ce_tipo:
                    st.write("**TIPO EQUIPO**")
                    opts_tce = ["CONG", "REFR", "1CO2", "ULTRO"]
                    tce_ed = st.selectbox(
                        "Tipo",
                        opts_tce,
                        index=(
                            opts_tce.index(ce_target["tipo_equipo"])
                            if ce_target["tipo_equipo"] in opts_tce
                            else 0
                        ),
                        key="ed_ce_tipo",
                    )
                with ce_datos:
                    st.write("**DATOS TÉCNICOS**")
                    d1, d2 = st.columns(2)
                    with d1:
                        ce_num_ed = st.text_input(
                            "NÚMERO",
                            value=str(ce_target["numero"]),
                            key="ed_ce_num",
                        )
                        ce_marca_ed = st.text_input(
                            "MARCA",
                            value=str(ce_target["marca"]),
                            key="ed_ce_marca",
                        )
                        ce_mod_ed = st.text_input(
                            "MODELO",
                            value=str(ce_target["modelo"]),
                            key="ed_ce_mod",
                        )
                    with d2:
                        ce_serie_ed = st.text_input(
                            "SERIE",
                            value=str(ce_target["serie"]),
                            key="ed_ce_serie",
                        )
                        ce_inv_ed = st.text_input(
                            "INVENTARIO",
                            value=str(ce_target["inventario"]),
                            key="ed_ce_inv",
                        )
                with ce_corr:
                    st.write("**CORRECCIÓN (TABLA DE VALORES)**")
                    tabla_ce_corr_ed = st.data_editor(
                        df_ce_rangos_bd,
                        hide_index=True,
                        use_container_width=True,
                        key="ed_editor_ce_corr",
                    )

                st.write("")
                st.write("**UBICACIÓN (LABORATORIO)**")
                ce_lab_ed = st.selectbox(
                    "Laboratorio",
                    labs_lista,
                    index=(
                        labs_lista.index(ce_target["ubicacion_lab"])
                        if ce_target["ubicacion_lab"] in labs_lista
                        else 0
                    ),
                    key="ed_ce_lab",
                )

                st.write("")
                col_h, col_e = st.columns(2)
                with col_h:
                    st.markdown(
                        '<div class="btn-hecho">', unsafe_allow_html=True
                    )
                    if st.button(
                        "HECHO (GUARDAR CAMBIOS)", key="btn_save_edit_ce"
                    ):
                        nuevo_ce_id = f"{tce_ed}-{ce_num_ed}_{ce_lab_ed}"
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            UPDATE config_condiciones_equipos
                            SET id = ?, tipo_equipo = ?, numero = ?, marca = ?, modelo = ?, serie = ?, inventario = ?, ubicacion_lab = ?
                            WHERE id = ?
                        """,
                            (
                                nuevo_ce_id,
                                tce_ed,
                                ce_num_ed,
                                ce_marca_ed,
                                ce_mod_ed,
                                ce_serie_ed,
                                ce_inv_ed,
                                ce_lab_ed,
                                ce_target["id"],
                            ),
                        )

                        cursor.execute(
                            "DELETE FROM correcciones_rangos WHERE entidad_id ="
                            " ? OR entidad_id = ?",
                            (ce_target["id"], nuevo_ce_id),
                        )
                        for _, fila in tabla_ce_corr_ed.iterrows():
                            cursor.execute(
                                "INSERT INTO correcciones_rangos (entidad_id,"
                                " rango, correccion) VALUES (?, ?, ?)",
                                (
                                    nuevo_ce_id,
                                    str(fila["Rango"]),
                                    float(fila["Corrección"]),
                                ),
                            )
                        conn.commit()
                        conn.close()
                        st.session_state["item_editar_id"] = None
                        st.success("✅ Cambios guardados correctamente.")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                with col_e:
                    st.markdown(
                        '<div class="btn-eliminar">', unsafe_allow_html=True
                    )
                    if st.button("ELIMINAR CONFIGURACIÓN", key="btn_del_ce"):
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute(
                            "DELETE FROM config_condiciones_equipos WHERE id ="
                            " ?",
                            (ce_target["id"],),
                        )
                        cursor.execute(
                            "DELETE FROM correcciones_rangos WHERE entidad_id ="
                            " ?",
                            (ce_target["id"],),
                        )
                        conn.commit()
                        conn.close()
                        st.session_state["item_editar_id"] = None
                        st.success("🗑️ Equipo de monitoreo eliminado.")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# 7. MODO REGULAR (USO Y REGISTRO OPERATIVO DIARIO)
# ==============================================================================
elif st.session_state["lab_seleccionado"] is not None:
    lab_actual = st.session_state["lab_seleccionado"]

    if st.session_state["sub_categoria"] == "EQUIPOS":
        st.markdown(
            f'<div class="section-title">EQUIPOS DISPONIBLES EN LABORATORIO'
            f" {lab_actual}</div>",
            unsafe_allow_html=True,
        )
        equipos_lab = cargar_equipos(lab_actual)

        if not equipos_lab:
            st.warning(
                "⚠️ No hay equipos registrados para el Laboratorio"
                f" {lab_actual}."
            )
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
            eq_sel = next(
                (
                    item
                    for item in equipos_lab
                    if item["id"] == st.session_state["equipo_activo_id"]
                ),
                None,
            )

            if eq_sel:
                st.markdown("---")
                st.subheader(
                    f"Control de Uso: {eq_sel['tipo']}-{eq_sel['numero']}"
                    f" (Marca: {eq_sel['marca']} | Serie: {eq_sel['serie']})"
                )

                c_init, c_space, c_fin = st.columns([4, 0.5, 4])
                with c_init:
                    st.markdown(
                        "<h3 style='color:#2A9D8F; text-align:center;'>INICIO</h3>",
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "🟢 REGISTRAR INICIO DE USO",
                        key=f"btn_init_{eq_sel['id']}",
                    ):
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO registros_uso (equipo_id, accion,"
                            " fecha_hora_cdmx) VALUES (?, ?, ?)",
                            (eq_sel["id"], "INICIO", obtener_hora_cdmx()),
                        )
                        conn.commit()
                        conn.close()
                        st.toast("🟢 Inicio registrado")
                        st.rerun()

                with c_fin:
                    st.markdown(
                        "<h3 style='color:#E63946; text-align:center;'>FINAL</h3>",
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "🔴 REGISTRAR FINALIZACIÓN", key=f"btn_fin_{eq_sel['id']}"
                    ):
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO registros_uso (equipo_id, accion,"
                            " fecha_hora_cdmx) VALUES (?, ?, ?)",
                            (eq_sel["id"], "FINAL", obtener_hora_cdmx()),
                        )
                        conn.commit()
                        conn.close()
                        st.toast("🔴 Finalización registrada")
                        st.rerun()

                st.write("")
                reg_filtrados = cargar_registros_uso(eq_sel["id"])
                if reg_filtrados:
                    df_usos = pd.DataFrame(reg_filtrados)[
                        ["Acción", "FechaHora_CDMX"]
                    ]
                    st.dataframe(df_usos, use_container_width=True)

    elif st.session_state["sub_categoria"] == "CONDICIONES AMBIENTALES":
        st.markdown(
            '<div class="section-title">CONDICIONES AMBIENTALES - LAB'
            f" {lab_actual}</div>",
            unsafe_allow_html=True,
        )
        cfg_temp = cargar_condicion_ambiental_config(lab_actual, "TEMP")
        cfg_hum = cargar_condicion_ambiental_config(lab_actual, "%H")

        col_amb_temp, col_amb_hum = st.columns(2)
        with col_amb_temp:
            st.markdown(
                "<h3 style='text-align:center;"
                " color:#0077B6;'>TEMPERATURA</h3>",
                unsafe_allow_html=True,
            )
            inp_temp = st.number_input(
                "Ingresar Lectura (°C)",
                key=f"inp_temp_{lab_actual}",
                value=None,
                step=0.1,
            )
            t_corregida, factor_t = None, 0.0
            if inp_temp is not None:
                tabla_t = cfg_temp.get("Correcciones", []) if cfg_temp else []
                t_corregida, factor_t = calcular_correccion_valor(
                    inp_temp, tabla_t
                )

            val_disp_t = (
                f"{t_corregida} °C" if t_corregida is not None else "0.0 °C"
            )
            st.markdown(
                f'<div class="oval-corregido">Lectura Corregida: {val_disp_t}'
                f" (Corr: {factor_t:+} °C)</div>",
                unsafe_allow_html=True,
            )

        with col_amb_hum:
            st.markdown(
                "<h3 style='text-align:center; color:#0077B6;'>% HUMEDAD</h3>",
                unsafe_allow_html=True,
            )
            inp_hum = st.number_input(
                "Ingresar Lectura (%H)",
                key=f"inp_hum_{lab_actual}",
                value=None,
                step=0.1,
            )
            h_corregida, factor_h = None, 0.0
            if inp_hum is not None:
                tabla_h = cfg_hum.get("Correcciones", []) if cfg_hum else []
                h_corregida, factor_h = calcular_correccion_valor(
                    inp_hum, tabla_h
                )

            val_disp_h = (
                f"{h_corregida} %" if h_corregida is not None else "0.0 %"
            )
            st.markdown(
                f'<div class="oval-corregido">Lectura Corregida: {val_disp_h}'
                f" (Corr: {factor_h:+} %)</div>",
                unsafe_allow_html=True,
            )

        st.write("")
        st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
        if st.button("HECHO", key=f"btn_hecho_amb_{lab_actual}"):
            conn = obtener_conexion()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO mediciones_ambientales (fecha_hora, lab, temp_leida, temp_corr, hum_leida, hum_corr)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    obtener_hora_cdmx(),
                    lab_actual,
                    inp_temp,
                    t_corregida,
                    inp_hum,
                    h_corregida,
                ),
            )
            conn.commit()
            conn.close()
            st.success("💾 Mediciones ambientales guardadas.")
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state["sub_categoria"] == "CONDICIONES DE EQUIPOS":
        st.markdown(
            '<div class="section-title">CONDICIONES DE EQUIPOS - LAB'
            f" {lab_actual}</div>",
            unsafe_allow_html=True,
        )
        equipos_ce_lab = cargar_condiciones_equipos_db(lab_actual)

        if not equipos_ce_lab:
            st.info(
                f"No hay equipos configurados en el Laboratorio {lab_actual}."
            )
        else:
            cols_ce_grid = st.columns(min(len(equipos_ce_lab), 4))
            mediciones_resumen = []

            for idx_ce, eq_ce in enumerate(equipos_ce_lab):
                col_curr = cols_ce_grid[idx_ce % 4]
                with col_curr:
                    titulo_eq = f"{eq_ce['Tipo_Equipo']}-{eq_ce['Numero']}"
                    st.markdown(
                        "<div style='border: 1px solid #0077B6; border-radius:"
                        " 4px; padding: 4px; text-align: center; font-weight:"
                        " bold; background-color: #F0F8FF; color: #0077B6;"
                        " margin-bottom: 5px; font-size:"
                        f" 0.9rem;'>{titulo_eq}</div>",
                        unsafe_allow_html=True,
                    )

                    val_leido = st.number_input(
                        f"Lectura Temp",
                        key=f"ce_val_{eq_ce['id_ce']}",
                        value=None,
                        step=0.1,
                    )
                    val_corr, f_corr = None, 0.0
                    if val_leido is not None:
                        val_corr, f_corr = calcular_correccion_valor(
                            val_leido, eq_ce.get("Correcciones", [])
                        )

                    v_text = (
                        f"{val_corr} °C" if val_corr is not None else "0.0 °C"
                    )
                    st.markdown(
                        f'<div class="oval-corregido">{v_text}</div>',
                        unsafe_allow_html=True,
                    )

                    if val_leido is not None:
                        mediciones_resumen.append({
                            "Parametro": f"{titulo_eq} (Temp)",
                            "Lectura": f"{val_leido} °C",
                            "Corregida": f"{val_corr} °C",
                        })

            st.write("")
            st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
            if st.button("HECHO", key=f"btn_hecho_ce_{lab_actual}"):
                conn = obtener_conexion()
                cursor = conn.cursor()
                for m in mediciones_resumen:
                    cursor.execute(
                        """
                        INSERT INTO mediciones_equipos (fecha_hora, lab, parametro, lectura, corregida)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            obtener_hora_cdmx(),
                            lab_actual,
                            m["Parametro"],
                            str(m["Lectura"]),
                            str(m["Corregida"]),
                        ),
                    )
                conn.commit()
                conn.close()
                st.success("💾 Mediciones de equipos guardadas.")
            st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info(
        "👈 Selecciona un laboratorio de la barra superior, presiona ➕ para"
        " dar de alta o ➖ para editar/eliminar registros."
    )
