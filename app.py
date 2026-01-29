import streamlit as st
import json
import os
import urllib.parse
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="OP PJ MERIDA", page_icon="🛡️", layout="wide")

# --- CONTROL DE ACCESO (USANDO SECRETS) ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("<h1 style='text-align: center;'>🔐 Acceso OP PJ MERIDA</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Nota: La clave se configura en el panel de Streamlit Cloud (Secrets)
        password_input = st.text_input("Introduzca la clave de seguridad", type="password")
        if st.button("🔓 Entrar al Sistema", use_container_width=True):
            if password_input == st.secrets["password_general"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
        
        st.markdown("---")
        email_admin = "fjcanom@gmail.com"
        asunto = "SOLICITUD CAMBIO CONTRASEÑA - OP PJ MERIDA"
        cuerpo = f"Solicito cambio de clave. Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        link_mail = f"mailto:{email_admin}?subject={urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}"
        st.markdown(f'<a href="{link_mail}"><button style="width:100%; cursor:pointer; padding:10px; border-radius:5px; border:1px solid #ccc;">📧 Contactar Administrador</button></a>', unsafe_allow_html=True)
    return False

# --- LÓGICA DE BASE DE DATOS ---
DB_FILE = "database_pj_merida.json"

def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def guardar_datos(datos):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# --- INICIO DE LA APLICACIÓN ---
if check_password():
    if 'db' not in st.session_state:
        st.session_state.db = cargar_datos()

    # Barra lateral
    st.sidebar.title("👮‍♂️ Gestión OP")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()

    st.sidebar.markdown("---")
    nueva_carpeta = st.sidebar.text_input("Añadir Nueva Carpeta:")
    if st.sidebar.button("➕ Crear"):
        if nueva_carpeta and nueva_carpeta not in st.session_state.db:
            st.session_state.db[nueva_carpeta] = {}
            guardar_datos(st.session_state.db)
            st.rerun()

    carpetas = list(st.session_state.db.keys())
    carpeta_sel = st.sidebar.selectbox("📂 Carpeta Actual", ["---"] + carpetas)
    busqueda = st.sidebar.text_input("🔍 Buscar (Nombre/DNI)")

    st.title("🛡️ Sistema de Inteligencia MERIDA")

    if carpeta_sel != "---":
        tab1, tab2, tab3 = st.tabs(["🧐 CONSULTA / EDICIÓN", "📝 REGISTRO NUEVO", "📊 EXPORTAR"])

        with tab2:
            st.subheader(f"Nuevo Objetivo en: {carpeta_sel}")
            with st.form("form_reg", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nom = c1.text_input("Nombre y Apellidos*")
                dni_input = c1.text_input("DNI / Identificación*")
                tels_input = c1.text_area("Teléfonos (Uno por línea)")
                dirs_input = c2.text_area("Direcciones (Una por línea)")
                vehs_input = c2.text_area("Vehículos (Marca, Matrícula)")
                obs_input = st.text_area("Observaciones (Sin límite)")
                if st.form_submit_button("💾 GUARDAR REGISTRO"):
                    if nom and dni_input:
                        id_obj = f"{nom}_{dni_input}".replace(" ", "_")
                        st.session_state.db[carpeta_sel][id_obj] = {
                            "nombre": nom, "dni": dni_input, "telefonos": tels_input,
                            "direcciones": dirs_input, "vehiculos": vehs_input,
                            "observaciones": obs_input, "fecha": datetime.now().strftime("%d/%m/%Y")
                        }
                        guardar_datos(st.session_state.db)
                        st.success(f"✅ Guardado: {nom}")
                    else:
                        st.error("⚠️ Nombre y DNI son obligatorios")

        with tab1:
            objs = st.session_state.db[carpeta_sel]
            filtrados = [k for k,v in objs.items() if busqueda.lower() in v['nombre'].lower() or busqueda in v['dni']] if busqueda else list(objs.keys())
            
            if filtrados:
                sel_obj = st.selectbox("Seleccione un perfil:", filtrados)
                item = objs[sel_obj]
                
                with st.expander(f"✏️ Editar/Ver Detalle: {item['nombre']}", expanded=True):
                    enom = st.text_input("Nombre", item['nombre'])
                    edni = st.text_input("DNI", item['dni'])
                    etels = st.text_area("Teléfonos", item['telefonos'])
                    edirs = st.text_area("Direcciones", item['direcciones'])
                    evehs = st.text_area("Vehículos", item['vehiculos'])
                    eobs = st.text_area("Observaciones", item['observaciones'])
                    
                    col_b1, col_b2 = st.columns(2)
                    if col_b1.button("🆙 ACTUALIZAR DATOS"):
                        objs[sel_obj] = {"nombre": enom, "dni": edni, "telefonos": etels, "direcciones": edirs, "vehiculos": evehs, "observaciones": eobs, "fecha": item['fecha']}
                        guardar_datos(st.session_state.db)
                        st.success("Actualizado")
                        st.rerun()
                    if col_b2.button("🗑️ ELIMINAR PERFIL"):
                        del st.session_state.db[carpeta_sel][sel_obj]
                        guardar_datos(st.session_state.db)
                        st.rerun()
            else:
                st.info("No hay datos en esta carpeta.")

        with tab3:
            st.subheader("Exportar a Office")
            if st.button("📊 Generar Excel de toda la base de datos"):
                all_data = []
                for carp, c_objs in st.session_state.db.items():
                    for o_id, o_val in c_objs.items():
                        o_val['Carpeta'] = carp
                        all_data.append(o_val)
                
                if all_data:
                    df = pd.DataFrame(all_data)
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Objetivos')
                    st.download_button(label="📥 Descargar Excel (.xlsx)", data=output.getvalue(), file_name=f"PJ_MERIDA_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    st.warning("No hay datos para exportar")
    else:
        st.info("👈 Seleccione una carpeta para comenzar.")
