import streamlit as st
import json
import os
import urllib.parse
import pandas as pd
from datetime import datetime
from io import BytesIO

# ==========================================
# 1. CONFIGURACIÓN Y SEGURIDAD
# ==========================================
PASSWORD_ACTUAL = "MERIDA2024" 
EMAIL_ADMIN = "fjcanom@gmail.com"

def enviar_correo_cambio():
    asunto = "SOLICITUD CAMBIO CONTRASEÑA - OP PJ MERIDA"
    cuerpo = f"Solicito el cambio de contraseña.\nFecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    mailto_link = f"mailto:{EMAIL_ADMIN}?subject={urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}"
    return mailto_link

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.markdown("<h1 style='text-align: center;'>🔐 OP PJ MERIDA</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            ingreso = st.text_input("Contraseña de Seguridad", type="password")
            if st.button("🔓 Entrar", use_container_width=True):
                if ingreso == PASSWORD_ACTUAL:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Incorrecta")
            st.markdown("---")
            link = enviar_correo_cambio()
            st.markdown(f'<a href="{link}"><button style="width:100%; cursor:pointer; border-radius:5px;">📧 Solicitar Cambio</button></a>', unsafe_allow_html=True)
        return False
    return True

# ==========================================
# 2. GESTIÓN DE DATOS
# ==========================================
DB_FILE = "database_pj_merida.json"

def cargar_datos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_datos(datos):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# ==========================================
# 3. INTERFAZ
# ==========================================
if check_password():
    st.set_page_config(page_title="OP PJ MERIDA", layout="wide")
    if 'db' not in st.session_state:
        st.session_state.db = cargar_datos()

    # SIDEBAR
    st.sidebar.title("📁 CARPETAS")
    nueva_c = st.sidebar.text_input("Nueva Carpeta:")
    if st.sidebar.button("➕ Crear"):
        if nueva_c and nueva_c not in st.session_state.db:
            st.session_state.db[nueva_c] = {}
            guardar_datos(st.session_state.db)
            st.rerun()

    carpetas = list(st.session_state.db.keys())
    c_sel = st.sidebar.selectbox("📂 Seleccionar Carpeta", ["---"] + carpetas)
    busqueda = st.sidebar.text_input("🔍 Buscar (DNI/Nombre)")

    if c_sel != "---":
        tab_ver, tab_reg, tab_exp = st.tabs(["🧐 CONSULTAR / EDITAR", "📝 REGISTRAR", "📊 EXPORTAR OFFICE"])

        # REGISTRO
        with tab_reg:
            with st.form("reg_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                nombre = col1.text_input("Nombre*")
                dni = col1.text_input("DNI*")
                tels = col1.text_area("Teléfonos")
                dirs = col2.text_area("Direcciones")
                vehs = col2.text_area("Vehículos")
                obs = st.text_area("Observaciones")
                if st.form_submit_button("💾 GUARDAR"):
                    id_obj = f"{nombre}_{dni}".replace(" ", "_")
                    st.session_state.db[c_sel][id_obj] = {
                        "nombre": nombre, "dni": dni, "telefonos": tels, 
                        "direcciones": dirs, "vehiculos": vehs, "observaciones": obs,
                        "fecha": datetime.now().strftime("%d/%m/%Y")
                    }
                    guardar_datos(st.session_state.db)
                    st.success("Guardado")

        # CONSULTA Y EDICIÓN
        with tab_ver:
            objs = st.session_state.db[c_sel]
            filtrados = [k for k,v in objs.items() if busqueda.lower() in v['nombre'].lower() or busqueda in v['dni']] if busqueda else list(objs.keys())
            
            if filtrados:
                sel = st.selectbox("Objetivo:", filtrados)
                item = objs[sel]
                
                with st.expander("✏️ EDITAR DATOS DE " + item['nombre']):
                    e_nom = st.text_input("Nombre", item['nombre'])
                    e_dni = st.text_input("DNI", item['dni'])
                    e_tels = st.text_area("Teléfonos", item['telefonos'])
                    e_vehs = st.text_area("Vehículos", item['vehiculos'])
                    e_obs = st.text_area("Observaciones", item['observaciones'])
                    
                    c_ed1, c_ed2 = st.columns(2)
                    if c_ed1.button("🆙 ACTUALIZAR"):
                        objs[sel] = {**item, "nombre": e_nom, "dni": e_dni, "telefonos": e_tels, "vehiculos": e_vehs, "observaciones": e_obs}
                        guardar_datos(st.session_state.db)
                        st.rerun()
                    if c_ed2.button("🗑️ ELIMINAR PERFIL"):
                        del st.session_state.db[c_sel][sel]
                        guardar_datos(st.session_state.db)
                        st.rerun()

        # EXPORTACIÓN A EXCEL
        with tab_exp:
            st.subheader("Generar Reporte Excel")
            if st.button("📊 Preparar Archivo Office"):
                lista_excel = []
                for carp, contenidos in st.session_state.db.items():
                    for k, v in contenidos.items():
                        v['Carpeta'] = carp
                        lista_excel.append(v)
                
                if lista_excel:
                    df = pd.DataFrame(lista_excel)
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Datos_PJ')
                    st.download_button(
                        label="📥 Descargar EXCEL (.xlsx)",
                        data=output.getvalue(),
                        file_name=f"reporte_merida_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No hay datos para exportar.")

### Archivo requirements.txt:
# streamlit
# pandas
# openpyxl