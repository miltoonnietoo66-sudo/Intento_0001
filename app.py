data=pdf_bytes_amb,
                        file_name=f"Reporte_Ambiental_Lab_{lab_act}.pdf",
                        mime="application/pdf",
                        key=f"dl_amb_{lab_act}"
                    )

        # --- 3. REPORTES DE CONDICIONES DE EQUIPOS ---
        elif cat_act == "CONDICIONES DE EQUIPOS":
            cond_registradas = pd.read_sql_query(
                "SELECT * FROM config_condiciones_equipos WHERE ubicacion_lab = ?", 
                conn, 
                params=(lab_act,)
            ).to_dict(orient="records")
            
            if not cond_registradas:
                st.warning(f"No hay equipos de monitoreo configurados en el Lab {lab_act}.")
            else:
                for cond in cond_registradas:
                    cond_id = cond["id"]
                    nombre_btn = f"📄 PDF: {cond['tipo']}-{cond['numero']}"
                    
                    meta_cond = {
                        "Equipo Monitoreado": f"{cond['tipo']} - {cond['numero']}",
                        "Rango Permitido": f"{cond['val_min']} a {cond['val_max']} {cond['unidad']}",
                        "Instrumento / Sensor": cond['instrumento'],
                        "Ubicación": f"Laboratorio {cond['ubicacion_lab']}",
                        "Fecha de Configuración": cond['fecha_hora']
                    }
                    
                    with cols_rep[c_idx % 4]:
                        df_med_ce = pd.read_sql_query(
                            'SELECT fecha_hora as "Fecha y Hora", lectura_corr as "Lectura Corregida" FROM mediciones_cond_equipos WHERE config_id = ?', 
                            conn, 
                            params=(cond_id,)
                        )
                        pdf_bytes_ce = generar_pdf_generico(
                            f"MONITOREO DE CONDICIONES - {cond['tipo']}-{cond['numero']}", 
                            df_med_ce, 
                            metadata=meta_cond
                        )
                        st.download_button(
                            label=nombre_btn,
                            data=pdf_bytes_ce,
                            file_name=f"Reporte_Condicion_{cond_id}.pdf",
                            mime="application/pdf",
                            key=f"dl_ce_{cond_id}"
                        )
                    c_idx += 1
        conn.close()

# ==========================================
# SECCIÓN: REGISTRAR (CAPTURA DE DATOS)
# ==========================================
elif st.session_state["menu_principal"] == "REGISTRAR":
    lab_act = st.session_state["lab_seleccionado"]
    cat_act = st.session_state["sub_categoria"]
    
    # --- MODO AGREGAR (+) ---
    if st.session_state["modo_agregar"]:
        if lab_act is None:
            st.error("Por favor selecciona un laboratorio arriba antes de guardar el nuevo elemento.")
        else:
            st.markdown(f'<div class="section-title">NUEVO REGISTRO EN {cat_act} (LAB {lab_act})</div>', unsafe_allow_html=True)
            
            if cat_act == "EQUIPOS":
                with st.form("form_alta_equipo"):
                    c1, c2 = st.columns(2)
                    with c1:
                        tipo_eq = st.text_input("Tipo de Equipo (ej. Centrífuga, Incubadora)")
                        num_eq = st.text_input("Número / Identificador")
                        marca_eq = st.text_input("Marca")
                    with c2:
                        mod_eq = st.text_input("Modelo")
                        ser_eq = st.text_input("N° de Serie")
                        inv_eq = st.text_input("N° de Inventario INER")
                    
                    btn_guardar_eq = st.form_submit_button("Guardar Equipo")
                    if btn_guardar_eq:
                        if tipo_eq and num_eq:
                            conn = obtener_conexion()
                            c = conn.cursor()
                            c.execute('''
                                INSERT INTO equipos (tipo, numero, marca, modelo, serie, inventario, ubicacion_lab, fecha_hora)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (tipo_eq, num_eq, marca_eq, mod_eq, ser_eq, inv_eq, lab_act, obtener_hora_cdmx()))
                            conn.commit()
                            conn.close()
                            st.success(f"Equipo {tipo_eq}-{num_eq} guardado exitosamente.")
                            st.session_state["modo_agregar"] = False
                            st.rerun()
                        else:
                            st.error("Los campos 'Tipo' y 'Número' son obligatorios.")

            elif cat_act == "CONDICIONES AMBIENTALES":
                with st.form("form_alta_amb"):
                    c1, c2 = st.columns(2)
                    with c1:
                        tipo_amb = st.selectbox("Tipo de Medición", ["Temperatura y Humedad Ambiental"])
                        inst_amb = st.text_input("Instrumento / Termohigrómetro")
                    with c2:
                        min_amb = st.number_input("Valor Mínimo (°C)", value=18.0)
                        max_amb = st.number_input("Valor Máximo (°C)", value=25.0)
                    
                    btn_guardar_amb = st.form_submit_button("Guardar Configuración Ambiental")
                    if btn_guardar_amb:
                        conn = obtener_conexion()
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO config_ambientales (tipo, val_min, val_max, instrumento, ubicacion_lab, fecha_hora)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (tipo_amb, min_amb, max_amb, inst_amb, lab_act, obtener_hora_cdmx()))
                        conn.commit()
                        conn.close()
                        st.success("Configuración ambiental guardada correctamente.")
                        st.session_state["modo_agregar"] = False
                        st.rerun()

            elif cat_act == "CONDICIONES DE EQUIPOS":
                with st.form("form_alta_ce"):
                    c1, c2 = st.columns(2)
                    with c1:
                        tipo_ce = st.text_input("Tipo de Equipo Monitoreado (ej. Ultracongelador)")
                        num_ce = st.text_input("Número / ID")
                        inst_ce = st.text_input("Sensor / Termómetro Asignado")
                    with c2:
                        min_ce = st.number_input("Límite Mínimo Permisible", value=-80.0)
                        max_ce = st.number_input("Límite Máximo Permisible", value=-70.0)
                        uni_ce = st.text_input("Unidad de Medida", value="°C")
                    
                    btn_guardar_ce = st.form_submit_button("Guardar Parámetro de Equipo")
                    if btn_guardar_ce:
                        if tipo_ce and num_ce:
                            conn = obtener_conexion()
                            c = conn.cursor()
                            c.execute('''
                                INSERT INTO config_condiciones_equipos (tipo, numero, val_min, val_max, unidad, instrumento, ubicacion_lab, fecha_hora)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (tipo_ce, num_ce, min_ce, max_ce, uni_ce, inst_ce, lab_act, obtener_hora_cdmx()))
                            conn.commit()
                            conn.close()
                            st.success(f"Monitoreo para {tipo_ce}-{num_ce} guardado.")
                            st.session_state["modo_agregar"] = False
                            st.rerun()
                        else:
                            st.error("Los campos 'Tipo' y 'Número' son obligatorios.")

    # --- MODO ELIMINAR (➖) ---
    elif st.session_state["modo_eliminar"]:
        if lab_act is None:
            st.error("Selecciona un laboratorio arriba para gestionar la eliminación de registros.")
        else:
            st.markdown(f'<div class="section-title">GESTIÓN Y ELIMINACIÓN EN {cat_act} (LAB {lab_act})</div>', unsafe_allow_html=True)
            conn = obtener_conexion()
            
            if cat_act == "EQUIPOS":
                df_eq_del = pd.read_sql_query("SELECT id, tipo, numero, marca, modelo, serie FROM equipos WHERE ubicacion_lab = ?", conn, params=(lab_act,))
                if df_eq_del.empty:
                    st.info("No hay equipos configurados en este laboratorio.")
                else:
                    for _, row in df_eq_del.iterrows():
                        c1, c2 = st.columns([4, 1])
                        with c1:
                            st.write(f"**{row['tipo']} - {row['numero']}** | Marca: {row['marca']} | Serie: {row['serie']}")
                        with c2:
                            if st.button("❌ Eliminar", key=f"del_eq_{row['id']}"):
                                c = conn.cursor()
                                c.execute("DELETE FROM equipos WHERE id = ?", (row['id'],))
                                c.execute("DELETE FROM registros_uso WHERE equipo_id = ?", (row['id'],))
                                conn.commit()
                                st.success("Equipo eliminado.")
                                st.rerun()

            elif cat_act == "CONDICIONES AMBIENTALES":
                df_amb_del = pd.read_sql_query("SELECT id, tipo, val_min, val_max, instrumento FROM config_ambientales WHERE ubicacion_lab = ?", conn, params=(lab_act,))
                if df_amb_del.empty:
                    st.info("No hay parámetros ambientales configurados en este laboratorio.")
                else:
                    for _, row in df_amb_del.iterrows():
                        c1, c2 = st.columns([4, 1])
                        with c1:
                            st.write(f"**{row['tipo']}** | Rango: {row['val_min']} a {row['val_max']} °C | Sensor: {row['instrumento']}")
                        with c2:
                            if st.button("❌ Eliminar", key=f"del_amb_{row['id']}"):
                                c = conn.cursor()
                                c.execute("DELETE FROM config_ambientales WHERE id = ?", (row['id'],))
                                conn.commit()
                                st.success("Configuración eliminada.")
                                st.rerun()

            elif cat_act == "CONDICIONES DE EQUIPOS":
                df_ce_del = pd.read_sql_query("SELECT id, tipo, numero, val_min, val_max, unidad FROM config_condiciones_equipos WHERE ubicacion_lab = ?", conn, params=(lab_act,))
                if df_ce_del.empty:
                    st.info("No hay monitoreos de condiciones de equipos configurados en este laboratorio.")
                else:
                    for _, row in df_ce_del.iterrows():
                        c1, c2 = st.columns([4, 1])
                        with c1:
                            st.write(f"**{row['tipo']} - {row['numero']}** | Rango: {row['val_min']} a {row['val_max']} {row['unidad']}")
                        with c2:
                            if st.button("❌ Eliminar", key=f"del_ce_{row['id']}"):
                                c = conn.cursor()
                                c.execute("DELETE FROM config_condiciones_equipos WHERE id = ?", (row['id'],))
                                c.execute("DELETE FROM mediciones_cond_equipos WHERE config_id = ?", (row['id'],))
                                conn.commit()
                                st.success("Monitoreo eliminado.")
                                st.rerun()
            conn.close()

    # --- NAVEGACIÓN NORMAL POR LABORATORIOS ---
    else:
        if lab_act is None:
            st.info("👈 Selecciona un laboratorio de la lista superior o usa (+) para agregar uno nuevo.")
        else:
            conn = obtener_conexion()
            
            if cat_act == "EQUIPOS":
                st.markdown(f'<div class="section-title">REGISTRO DE USO DE EQUIPOS - LAB {lab_act}</div>', unsafe_allow_html=True)
                df_eq = pd.read_sql_query("SELECT * FROM equipos WHERE ubicacion_lab = ?", conn, params=(lab_act,))
                
                if df_eq.empty:
                    st.warning("No hay equipos registrados en este laboratorio. Presiona (+) para agregar uno.")
                else:
                    cols_eq_btns = st.columns(4)
                    for idx, row in df_eq.iterrows():
                        with cols_eq_btns[idx % 4]:
                            if st.button(f"⚙️ {row['tipo']}-{row['numero']}", key=f"btn_eq_act_{row['id']}"):
                                st.session_state["equipo_activo_id"] = row['id']
                    
                    if st.session_state["equipo_activo_id"]:
                        eq_sel = df_eq[df_eq['id'] == st.session_state["equipo_activo_id"]].iloc[0]
                        st.markdown(f"### Bitácora de Registro: **{eq_sel['tipo']} - {eq_sel['numero']}**")
                        
                        with st.form("form_uso_equipo"):
                            accion_uso = st.text_input("Acción / Actividad realizada", placeholder="ej. Purificación de RNA - 12,000 RPM x 15 min")
                            btn_reg_uso = st.form_submit_button("Registrar Uso")
                            
                            if btn_reg_uso and accion_uso:
                                c = conn.cursor()
                                c.execute('''
                                    INSERT INTO registros_uso (equipo_id, accion, fecha_hora_cdmx)
                                    VALUES (?, ?, ?)
                                ''', (eq_sel['id'], accion_uso, obtener_hora_cdmx()))
                                conn.commit()
                                st.success("Uso registrado correctamente.")
                                st.rerun()
                        
                        st.markdown("#### Historial Reciente")
                        df_hist = pd.read_sql_query("SELECT fecha_hora_cdmx as 'Fecha y Hora', accion as 'Acción' FROM registros_uso WHERE equipo_id = ? ORDER BY id DESC LIMIT 10", conn, params=(eq_sel['id'],))
                        st.dataframe(df_hist, use_container_width=True)

            elif cat_act == "CONDICIONES AMBIENTALES":
                st.markdown(f'<div class="section-title">MEDICIÓN AMBIENTAL - LAB {lab_act}</div>', unsafe_allow_html=True)
                with st.form("form_med_amb"):
                    c1, c2 = st.columns(2)
                    with c1:
                        temp_val = st.number_input("Temperatura Leída (°C)", value=21.5, step=0.1)
                    with c2:
                        hum_val = st.number_input("Humedad Leída (%)", value=45.0, step=0.5)
                    
                    btn_save_amb = st.form_submit_button("Guardar Lectura Ambiental")
                    if btn_save_amb:
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO mediciones_ambientales (lab, temp_corr, hum_corr, fecha_hora)
                            VALUES (?, ?, ?, ?)
                        ''', (lab_act, temp_val, hum_val, obtener_hora_cdmx()))
                        conn.commit()
                        st.success("Condiciones ambientales registradas.")
                        st.rerun()
                
                st.markdown("#### Historial Reciente")
                df_hist_amb = pd.read_sql_query("SELECT fecha_hora as 'Fecha y Hora', temp_corr as 'Temp (°C)', hum_corr as 'Humedad (%)' FROM mediciones_ambientales WHERE lab = ? ORDER BY id DESC LIMIT 10", conn, params=(lab_act,))
                st.dataframe(df_hist_amb, use_container_width=True)

            elif cat_act == "CONDICIONES DE EQUIPOS":
                st.markdown(f'<div class="section-title">MONITOREO DE CONDICIONES DE EQUIPOS - LAB {lab_act}</div>', unsafe_allow_html=True)
                df_ce = pd.read_sql_query("SELECT * FROM config_condiciones_equipos WHERE ubicacion_lab = ?", conn, params=(lab_act,))
                
                if df_ce.empty:
                    st.warning("No hay equipos configurados para monitoreo de condiciones en este laboratorio.")
                else:
                    for _, row in df_ce.iterrows():
                        with st.expander(f"❄️ / 🎛️ {row['tipo']} - {row['numero']} (Rango: {row['val_min']} a {row['val_max']} {row['unidad']})"):
                            with st.form(f"form_ce_{row['id']}"):
                                lect = st.number_input(f"Lectura Actual ({row['unidad']})", key=f"inp_ce_{row['id']}")
                                btn_save_ce = st.form_submit_button("Guardar Lectura")
                                
                                if btn_save_ce:
                                    c = conn.cursor()
                                    c.execute('''
                                        INSERT INTO mediciones_cond_equipos (config_id, lectura_corr, fecha_hora)
                                        VALUES (?, ?, ?)
                                    ''', (row['id'], lect, obtener_hora_cdmx()))
                                    conn.commit()
                                    st.success("Lectura guardada correctamente.")
                                    st.rerun()
                            
                            df_hist_ce = pd.read_sql_query("SELECT fecha_hora as 'Fecha y Hora', lectura_corr as 'Lectura' FROM mediciones_cond_equipos WHERE config_id = ? ORDER BY id DESC LIMIT 5", conn, params=(row['id'],))
                            st.dataframe(df_hist_ce, use_container_width=True)
            conn.close()

# ==========================================
# SECCIÓN: VERIFICAR Y USUARIO
# ==========================================
elif st.session_state["menu_principal"] in ["VERIFICAR", "USUARIO"]:
    st.markdown(f'<div class="section-title">MÓDULO DE {st.session_state["menu_principal"]}</div>', unsafe_allow_html=True)
    st.info(f"El módulo de **{st.session_state['menu_principal']}** se encuentra activo y disponible para firmas de validación y control de perfiles.")
data=pdf_bytes_amb,
                        file_name=f"Reporte_Ambiental_Lab_{lab_act}.pdf",
                        mime="application/pdf",
                        key=f"dl_amb_{lab_act}"
                    )

        # --- 3. REPORTES DE CONDICIONES DE EQUIPOS ---
        elif cat_act == "CONDICIONES DE EQUIPOS":
            ce_registrados = pd.read_sql_query("SELECT * FROM config_condiciones_equipos WHERE ubicacion_lab = ?", conn, params=(lab_act,)).to_dict(orient="records")
            if not ce_registrados:
                st.warning(f"No hay equipos con monitoreo de condiciones configurados en el Lab {lab_act}.")
            else:
                for ce in ce_registrados:
                    ce_id = ce["id"]
                    nombre_ce_btn = f"📄 PDF: TEMP {ce['tipo_equipo']}-{ce['numero']}"
                    
                    # Ficha técnica del equipo de monitoreo capturada en (+)
                    meta_ce = {
                        "Tipo Equipo": ce['tipo_equipo'],
                        "Número": ce['numero'],
                        "Marca": ce['marca'],
                        "Modelo": ce['modelo'],
                        "Serie": ce['serie'],
                        "Inventario": ce['inventario'],
                        "Ubicación": f"Laboratorio {ce['ubicacion_lab']}"
                    }
                    
                    with cols_rep[c_idx % 4]:
                        df_ce = pd.read_sql_query(
                            'SELECT fecha_hora as "Fecha y Hora", corregida as "Lectura Corregida" FROM mediciones_equipos WHERE lab = ? AND parametro LIKE ?', 
                            conn, 
                            params=(lab_act, f"%{ce['tipo_equipo']}-{ce['numero']}%")
                        )
                        pdf_bytes_ce = generar_pdf_generico(f"CONTROL DE TEMPERATURA - {ce['tipo_equipo']}-{ce['numero']}", df_ce, metadata=meta_ce)
                        st.download_button(
                            label=nombre_ce_btn,
                            data=pdf_bytes_ce,
                            file_name=f"Reporte_Condicion_{ce_id}.pdf",
                            mime="application/pdf",
                            key=f"dl_ce_{ce_id}"
                        )
                    c_idx += 1

        conn.close()

# ==========================================
# SECCIÓN: VERIFICAR Y USUARIO
# ==========================================
elif st.session_state["menu_principal"] == "VERIFICAR":
    st.info(f"🔍 Auditoría y Verificación de Bitácoras ({st.session_state['sub_categoria']}): Módulo activo.")

elif st.session_state["menu_principal"] == "USUARIO":
    st.info("👤 Módulo de USUARIO: Gestión de sesiones, firmas digitales e identificadores del personal.")

# ==========================================
# SECCIÓN: REGISTRAR
# ==========================================
elif st.session_state["menu_principal"] == "REGISTRAR":
    
    # MÓDULO ➕ (AGREGAR ALTA)
    if st.session_state["modo_agregar"]:
        if st.session_state["sub_categoria"] == "EQUIPOS":
            st.markdown('<div class="section-title">REGISTRO DE EQUIPOS DE USO</div>', unsafe_allow_html=True)
            c_tipo, c_num, c_marca, c_mod, c_serie, c_inv = st.columns([1.5, 1, 1.5, 1.5, 1.5, 1.5])
            with c_tipo:
                st.write("**TIPO**")
                for teq in ["GABS", "CENT", "MICR", "BAAG"]:
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
                id_unico = f"{st.session_state['sel_tipo_equipo']}-{num_eq}_{st.session_state['sel_ubicacion_lab']}"
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO equipos (id, fecha_hora, tipo, numero, marca, modelo, serie, inventario, ubicacion_lab)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id_unico, obtener_hora_cdmx(), st.session_state['sel_tipo_equipo'], num_eq, marca_eq, modelo_eq, serie_eq, inv_eq, st.session_state['sel_ubicacion_lab']))
                conn.commit()
                conn.close()
                st.success(f"💾 Guardado: Equipo {st.session_state['sel_tipo_equipo']}-{num_eq} en Lab {st.session_state['sel_ubicacion_lab']}.")
            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state["sub_categoria"] == "CONDICIONES AMBIENTALES":
            st.markdown('<div class="section-title">CONFIGURACIÓN DE CONDICIONES AMBIENTALES</div>', unsafe_allow_html=True)
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
                rangos = ["10 - 20", "20.1 - 30", "30.1 - 40", "40.1 - 50", "50.1 - 60", "60.1 - 70", "70.1 - 80", "80.1 - 100"] if st.session_state["sel_tipo_amb"] == "%H" else ["10 - 15", "15.1 - 20", "20.1 - 25", "25.1 - 30", "30.1 - 35"]
                df_corr = pd.DataFrame({"Rango": rangos, "Corrección": [0.0] * len(rangos)})
                tabla_corr_amb = st.data_editor(df_corr, hide_index=True, use_container_width=True, key="editor_corr_amb")

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
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO config_ambientales (fecha_hora, tipo, val_min, val_max, instrumento, ubicacion_lab)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (obtener_hora_cdmx(), st.session_state["sel_tipo_amb"], val_min, val_max, inst_medicion, st.session_state["sel_ubicacion_lab"]))
                
                entidad_id = f"AMB_{st.session_state['sel_ubicacion_lab']}_{st.session_state['sel_tipo_amb']}"
                cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ?", (entidad_id,))
                for _, fila in tabla_corr_amb.iterrows():
                    cursor.execute("INSERT INTO correcciones_rangos (entidad_id, rango, correccion) VALUES (?, ?, ?)", (entidad_id, str(fila["Rango"]), float(fila["Corrección"])))
                conn.commit()
                conn.close()
                st.success("💾 Configuración ambiental guardada correctamente.")
            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state["sub_categoria"] == "CONDICIONES DE EQUIPOS":
            st.markdown('<div class="section-title">CONFIGURACIÓN DE CONDICIONES DE EQUIPOS</div>', unsafe_allow_html=True)
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
                t_act = st.session_state["sel_tipo_ce"]
                r_list = ["-25 a -20", "-19.9 a -15", "-14.9 a -10"] if t_act == "CONG" else (["2 a 5", "5.1 a 8", "8.1 a 10"] if t_act == "REFR" else (["36.0 a 37.5", "4.5 a 5.5"] if t_act == "1CO2" else ["-85 a -80", "-79.9 a -70", "-69.9 a -60"]))
                df_ce_corr = pd.DataFrame({"Rango": r_list, "Corrección": [0.0] * len(r_list)})
                tabla_ce_corr = st.data_editor(df_ce_corr, hide_index=True, use_container_width=True, key="editor_ce_corr")

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
                id_ce = f"{st.session_state['sel_tipo_ce']}-{ce_num}_{st.session_state['sel_ubicacion_lab']}"
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO config_condiciones_equipos (id, fecha_hora, tipo_equipo, numero, marca, modelo, serie, inventario, ubicacion_lab)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id_ce, obtener_hora_cdmx(), st.session_state['sel_tipo_ce'], ce_num, ce_marca, ce_mod, ce_serie, ce_inv, st.session_state['sel_ubicacion_lab']))
                
                cursor.execute("DELETE FROM correcciones_rangos WHERE entidad_id = ?", (id_ce,))
                for _, fila in tabla_ce_corr.iterrows():
                    cursor.execute("INSERT INTO correcciones_rangos (entidad_id, rango, correccion) VALUES (?, ?, ?)", (id_ce, str(fila["Rango"]), float(fila["Corrección"])))
                conn.commit()
                conn.close()
                st.success("💾 Condición de equipo guardada correctamente.")
            st.markdown("</div>", unsafe_allow_html=True)

    # MÓDULO ➖ (EDITAR O ELIMINAR)
    elif st.session_state["modo_eliminar"]:
        if st.session_state["sub_categoria"] == "EQUIPOS":
            st.markdown('<div class="section-title">SELECCIONA UN EQUIPO PARA EDITAR O ELIMINAR</div>', unsafe_allow_html=True)
            todos_equipos = cargar_equipos()
            if not todos_equipos:
                st.info("No hay equipos de uso registrados.")
            else:
                cols_grid = st.columns(4)
                for idx, eq in enumerate(todos_equipos):
                    with cols_grid[idx % 4]:
                        lbl_btn = f"{eq['tipo']}-{eq['numero']} (Lab {eq['ubicacion_lab']})"
                        btn_key = f"btn_edit_eq_{eq['id']}"
                        if st.session_state["item_editar_id"] == eq["id"]:
                            aplicar_estilo_seleccion(btn_key)
                        if st.button(lbl_btn, key=btn_key):
                            st.session_state["item_editar_id"] = eq["id"]
                            st.rerun()

            if st.session_state["item_editar_id"]:
                eq_target = next((e for e in todos_equipos if e["id"] == st.session_state["item_editar_id"]), None)
                if eq_target:
                    st.markdown("---")
                    st.markdown(f'<div class="section-title">EDITANDO EQUIPO: {eq_target["id"]}</div>', unsafe_allow_html=True)
                    c_tipo, c_num, c_marca, c_mod, c_serie, c_inv = st.columns([1.5, 1, 1.5, 1.5, 1.5, 1.5])
                    with c_tipo:
                        st.write("**TIPO**")
                        tipo_ed = st.selectbox("Tipo", ["GABS", "CENT", "MICR", "BAAG"], index=["GABS", "CENT", "MICR", "BAAG"].index(eq_target["tipo"]) if eq_target["tipo"] in ["GABS", "CENT", "MICR", "BAAG"] else 0, key="ed_eq_tipo")
                    with c_num:
                        st.write("**NÚMERO**")
                        num_ed = st.text_input("N°", value=eq_target["numero"], key="ed_eq_num")
                    with c_marca:
                        st.write("**MARCA**")
                        marca_ed = st.text_input("Marca", value=eq_target["marca"], key="ed_eq_marca")
                    with c_mod:
                        st.write("**MODELO**")
                        mod_ed = st.text_input("Modelo", value=eq_target["modelo"], key="ed_eq_mod")
                    with c_serie:
                        st.write("**SERIE**")
                        serie_ed = st.text_input("N° Serie", value=eq_target["serie"], key="ed_eq_serie")
                    with c_inv:
                        st.write("**INVENTARIO**")
                        inv_ed = st.text_input("Inventario", value=eq_target["inventario"], key="ed_eq_inv")

                    st.write("")
                    st.write("**UBICACIÓN (LABORATORIO)**")
                    lab_ed = st.selectbox("Laboratorio", labs_lista, index=labs_lista.index(eq_target["ubicacion_lab"]) if eq_target["ubicacion_lab"] in labs_lista else 0, key="ed_eq_lab")

                    st.write("")
                    col_h, col_e = st.columns(2)
                    with col_h:
                        st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
                        if st.button("HECHO (GUARDAR CAMBIOS)", key="btn_save_edit_eq"):
                            nuevo_id = f"{tipo_ed}-{num_ed}_{lab_ed}"
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE equipos 
                                SET id = ?, tipo = ?, numero = ?, marca = ?, modelo = ?, serie = ?, inventario = ?, ubicacion_lab = ?
                                WHERE id = ?
                            """, (nuevo_id, tipo_ed, num_ed, marca_ed, mod_ed, serie_ed, inv_ed, lab_ed, eq_target["id"]))
                            conn.commit()
                            conn.close()
                            st.session_state["item_editar_id"] = None
                            st.success("✅ Cambios guardados correctamente.")
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                    with col_e:
                        st.markdown('<div class="btn-eliminar">', unsafe_allow_html=True)
                        if st.button("ELIMINAR EQUIPO", key="btn_del_eq"):
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM equipos WHERE id = ?", (eq_target["id"],))
                            cursor.execute("DELETE FROM registros_uso WHERE equipo_id = ?", (eq_target["id"],))
                            conn.commit()
                            conn.close()
                            st.session_state["item_editar_id"] = None
                            st.success("🗑️ Equipo eliminado permanentemente.")
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

        else:
            st.info(f"Selecciona un registro de {st.session_state['sub_categoria']} para dar de baja o actualizar.")

    # VISTA REGULAR (SELECCIÓN DE LABORATORIO)
    elif st.session_state["lab_seleccionado"] is not None:
        lab_actual = st.session_state["lab_seleccionado"]

        if st.session_state["sub_categoria"] == "EQUIPOS":
            st.markdown(f'<div class="section-title">EQUIPOS DISPONIBLES EN LABORATORIO {lab_actual}</div>', unsafe_allow_html=True)
            equipos_lab = cargar_equipos(lab_actual)

            if not equipos_lab:
                st.warning(f"⚠️ No hay equipos registrados para el Laboratorio {lab_actual}.")
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
                    eq_sel = next((item for item in equipos_lab if item["id"] == st.session_state["equipo_activo_id"]), None)

                    if eq_sel:
                        st.markdown("---")
                        st.subheader(f"Control de Uso: {eq_sel['tipo']}-{eq_sel['numero']} (Marca: {eq_sel['marca']} | Serie: {eq_sel['serie']})")

                        c_init, c_space, c_fin = st.columns([4, 0.5, 4])
                        with c_init:
                            st.markdown("<h3 style='color:#2A9D8F; text-align:center;'>INICIO</h3>", unsafe_allow_html=True)
                            if st.button("🟢 REGISTRAR INICIO DE USO", key=f"btn_init_{eq_sel['id']}"):
                                conn = obtener_conexion()
                                cursor = conn.cursor()
                                cursor.execute("INSERT INTO registros_uso (equipo_id, accion, fecha_hora_cdmx) VALUES (?, ?, ?)", (eq_sel["id"], "INICIO", obtener_hora_cdmx()))
                                conn.commit()
                                conn.close()
                                st.toast("🟢 Inicio registrado")
                                st.rerun()

                        with c_fin:
                            st.markdown("<h3 style='color:#E63946; text-align:center;'>FINAL</h3>", unsafe_allow_html=True)
                            if st.button("🔴 REGISTRAR FINALIZACIÓN", key=f"btn_fin_{eq_sel['id']}"):
                                conn = obtener_conexion()
                                cursor = conn.cursor()
                                cursor.execute("INSERT INTO registros_uso (equipo_id, accion, fecha_hora_cdmx) VALUES (?, ?, ?)", (eq_sel["id"], "FINAL", obtener_hora_cdmx()))
                                conn.commit()
                                conn.close()
                                st.toast("🔴 Finalización registrada")
                                st.rerun()

                        st.write("")
                        reg_filtrados = cargar_registros_uso(eq_sel["id"])
                        if reg_filtrados:
                            df_usos = pd.DataFrame(reg_filtrados)[["Acción", "FechaHora_CDMX"]]
                            st.dataframe(df_usos, use_container_width=True)

        elif st.session_state["sub_categoria"] == "CONDICIONES AMBIENTALES":
            st.markdown(f'<div class="section-title">CONDICIONES AMBIENTALES - LAB {lab_actual}</div>', unsafe_allow_html=True)
            cfg_temp = cargar_condicion_ambiental_config(lab_actual, "TEMP")
            cfg_hum = cargar_condicion_ambiental_config(lab_actual, "%H")

            col_amb_temp, col_amb_hum = st.columns(2)
            with col_amb_temp:
                st.markdown("<h3 style='text-align:center; color:#0077B6;'>TEMPERATURA</h3>", unsafe_allow_html=True)
                inp_temp = st.number_input("Ingresar Lectura (°C)", key=f"inp_temp_{lab_actual}", value=None, step=0.1)
                t_corregida, factor_t = None, 0.0
                if inp_temp is not None:
                    tabla_t = cfg_temp.get("Correcciones", []) if cfg_temp else []
                    t_corregida, factor_t = calcular_correccion_valor(inp_temp, tabla_t)

                val_disp_t = f"{t_corregida} °C" if t_corregida is not None else "0.0 °C"
                st.markdown(f'<div class="oval-corregido">Lectura Corregida: {val_disp_t} (Corr: {factor_t:+} °C)</div>', unsafe_allow_html=True)

            with col_amb_hum:
                st.markdown("<h3 style='text-align:center; color:#0077B6;'>% HUMEDAD</h3>", unsafe_allow_html=True)
                inp_hum = st.number_input("Ingresar Lectura (%H)", key=f"inp_hum_{lab_actual}", value=None, step=0.1)
                h_corregida, factor_h = None, 0.0
                if inp_hum is not None:
                    tabla_h = cfg_hum.get("Correcciones", []) if cfg_hum else []
                    h_corregida, factor_h = calcular_correccion_valor(inp_hum, tabla_h)

                val_disp_h = f"{h_corregida} %" if h_corregida is not None else "0.0 %"
                st.markdown(f'<div class="oval-corregido">Lectura Corregida: {val_disp_h} (Corr: {factor_h:+} %)</div>', unsafe_allow_html=True)

            st.write("")
            st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
            if st.button("HECHO", key=f"btn_hecho_amb_{lab_actual}"):
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO mediciones_ambientales (fecha_hora, lab, temp_leida, temp_corr, hum_leida, hum_corr)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (obtener_hora_cdmx(), lab_actual, inp_temp, t_corregida, inp_hum, h_corregida))
                conn.commit()
                conn.close()
                st.success("💾 Mediciones ambientales guardadas.")
            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state["sub_categoria"] == "CONDICIONES DE EQUIPOS":
            st.markdown(f'<div class="section-title">CONDICIONES DE EQUIPOS - LAB {lab_actual}</div>', unsafe_allow_html=True)
            equipos_ce_lab = cargar_condiciones_equipos_db(lab_actual)

            if not equipos_ce_lab:
                st.info(f"No hay equipos configurados en el Laboratorio {lab_actual}.")
            else:
                cols_ce_grid = st.columns(min(len(equipos_ce_lab), 4))
                mediciones_resumen = []

                for idx_ce, eq_ce in enumerate(equipos_ce_lab):
                    col_curr = cols_ce_grid[idx_ce % 4]
                    with col_curr:
                        titulo_eq = f"{eq_ce['Tipo_Equipo']}-{eq_ce['Numero']}"
                        st.markdown(f"<div style='border: 1px solid #0077B6; border-radius: 4px; padding: 4px; text-align: center; font-weight: bold; background-color: #F0F8FF; color: #0077B6; margin-bottom: 5px; font-size: 0.9rem;'>{titulo_eq}</div>", unsafe_allow_html=True)

                        val_leido = st.number_input(f"Lectura Temp", key=f"ce_val_{eq_ce['id_ce']}", value=None, step=0.1)
                        val_corr, f_corr = None, 0.0
                        if val_leido is not None:
                            val_corr, f_corr = calcular_correccion_valor(val_leido, eq_ce.get("Correcciones", []))

                        v_text = f"{val_corr} °C" if val_corr is not None else "0.0 °C"
                        st.markdown(f'<div class="oval-corregido">{v_text}</div>', unsafe_allow_html=True)

                        if val_leido is not None:
                            mediciones_resumen.append({"Parametro": f"{titulo_eq} (Temp)", "Lectura": f"{val_leido} °C", "Corregida": f"{val_corr} °C"})

                st.write("")
                st.markdown('<div class="btn-hecho">', unsafe_allow_html=True)
                if st.button("HECHO", key=f"btn_hecho_ce_{lab_actual}"):
                    conn = obtener_conexion()
                    cursor = conn.cursor()
                    for m in mediciones_resumen:
                        cursor.execute("""
                            INSERT INTO mediciones_equipos (fecha_hora, lab, parametro, lectura, corregida)
                            VALUES (?, ?, ?, ?, ?)
                        """, (obtener_hora_cdmx(), lab_actual, m["Parametro"], str(m["Lectura"]), str(m["Corregida"])))
                    conn.commit()
                    conn.close()
                    st.success("💾 Mediciones de equipos guardadas.")
                st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("👈 Selecciona un laboratorio de la barra superior, presiona ➕ para dar de alta o ➖ para editar/eliminar registros.")
