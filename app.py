import streamlit as st
import json
import os
import urllib.parse
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURACION ---
st.set_page_config(page_title="OP PJ MERIDA", layout="wide")

# --- FUNCION DE CONTRASEÑA ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True

    st.title("Acceso OP PJ MERIDA")
    # Buscara 'password_general' en la pestaña Secrets de Streamlit Cloud
    password_input = st.text_input("Introduzca la clave", type="password")
    if st.button("Entrar"):
        if password_input == st.secrets["password_general"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Clave incorrecta")
    return False

# --- BASE DE DATOS ---
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

# --- INICIO APP ---
if check_password():
    if 'db' not in st.session_state:
        st.session_state.db = cargar_datos()

    st.sidebar.title("MENU")
    if st.sidebar.button("Cerrar Sesion"):
        st.session_state.authenticated = False
        st.rerun()

    st.sidebar.markdown("---")
    nueva_c = st.sidebar.text_input("Nueva Carpeta:")
    if st.sidebar.button("Crear"):
        if nueva_c and nueva_c not in st.session_state.db:
            st.session_state.db[nueva_c] = {}
            guardar_datos(st.session_state.db)
            st.rerun()

    carpetas = list(st.session_state.db.keys())
    c_sel = st.sidebar.selectbox("Carpeta Actual", ["---"] + carpetas)
    busqueda = st.sidebar.text_input("Buscar (DNI/Nombre)")

    st.title("Sistema OP PJ MERIDA")

    if c_sel != "---":
        tab1, tab2, tab3 = st.tabs(["Consultar", "Registrar", "Exportar"])

        with tab2:
            with st.form("form_reg", clear_on_submit=True):
                col1, col2 = st.columns(2)
                nom = col1.text_input("Nombre y Apellidos")
                dni_in = col1.text_input("DNI")
                tels_in = col1.text_area("Telefonos")
                dirs_in = col2.text_area("Direcciones")
                vehs_in = col2.text_area("Vehiculos")
                obs_in = st.text_area("Observaciones")
                if st.form_submit_button("Guardar"):
                    if nom and dni_in:
                        id_obj = f"{nom}_{dni_in}".replace(" ", "_")
                        st.session_state.db[c_sel][id_obj] = {
                            "nombre": nom, "dni": dni_in, "telefonos": tels_in,
                            "direcciones": dirs_in, "vehiculos": vehs_in,
                            "observaciones": obs_in, "fecha": datetime.now().strftime("%d/%m/%Y")
                        }
                        guardar_datos(st.session_state.db)
                        st.success("Guardado")
                    else:
                        st.error("Faltan campos")

        with tab1:
            objs = st.session_state.db[c_sel]
            filtrados = [k for k,v in objs.items() if busqueda.lower() in v['nombre'].lower() or busqueda in v['dni']] if busqueda else list(objs.keys())
            if filtrados:
                sel = st.selectbox("Perfil:", filtrados)
                it = objs[sel]
                with st.expander(f"Ver/Editar: {it['nombre']}", expanded=True):
                    enom = st.text_input("Nombre", it['nombre'])
                    edni = st.text_input("DNI", it['dni'])
                    etels = st.text_area("Telefonos", it['telefonos'])
                    edirs = st.text_area("Direcciones", it['direcciones'])
                    evehs = st.text_area("Vehiculos", it['vehiculos'])
                    eobs = st.text_area("Observaciones", it['observaciones'])
                    if st.button("Actualizar"):
                        objs[sel] = {"nombre": enom, "dni": edni, "telefonos": etels, "direcciones": edirs, "vehiculos": evehs, "observaciones": eobs, "fecha": it['fecha']}
                        guardar_datos(st.session_state.db)
                        st.rerun()
                    if st.button("Eliminar"):
                        del st.session_state.db[c_sel][sel]
                        guardar_datos(st.session_state.db)
                        st.rerun()

        with tab3:
            if st.button("Generar Excel"):
                all_data = []
                for cp, items in st.session_state.db.items():
                    for o_id, val in items.items():
                        val['Carpeta'] = cp
                        all_data.append(val)
                if all_data:
                    df = pd.DataFrame(all_data)
                    out = BytesIO()
                    with pd.ExcelWriter(out, engine='openpyxl') as wr:
                        df.to_excel(wr, index=False)
                    st.download_button("Descargar Excel", out.getvalue(), "PJ_MERIDA.xlsx")
    else:
        st.info("Seleccione carpeta.")
