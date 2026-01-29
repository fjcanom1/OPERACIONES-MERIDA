import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="OP PJ MERIDA", layout="wide")

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.title("ACCESO")
    pw = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        if pw == st.secrets["password_general"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Error")
    return False

DB = "data.json"

def load():
    if os.path.exists(DB):
        with open(DB, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save(d):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=4, ensure_ascii=False)

if check_password():
    if "db" not in st.session_state:
        st.session_state.db = load()
    
    st.sidebar.title("MENU")
    if st.sidebar.button("Salir"):
        st.session_state.authenticated = False
        st.rerun()
    
    f_new = st.sidebar.text_input("Carpeta Nueva")
    if st.sidebar.button("Crear"):
        if f_new and f_new not in st.session_state.db:
            st.session_state.db[f_new] = {}
            save(st.session_state.db)
            st.rerun()
            
    f_list = list(st.session_state.db.keys())
    sel = st.sidebar.selectbox("Carpeta", ["---"] + f_list)
    bus = st.sidebar.text_input("Buscar")

    if sel != "---":
        t1, t2, t3 = st.tabs(["VER", "AÑADIR", "EXCEL"])
        
        with t2:
            with st.form("f1", clear_on_submit=True):
                n = st.text_input("Nombre")
                d = st.text_input("DNI")
                t = st.text_area("Tels")
                dr = st.text_area("Dirs")
                v = st.text_area("Vehs")
                o = st.text_area("Obs")
                if st.form_submit_button("Guardar"):
                    if n and d:
                        uid = f"{n}_{d}".replace(" ", "_")
                        st.session_state.db[sel][uid] = {
                            "nombre": n, "dni": d, "telefonos": t,
                            "direcciones": dr, "vehiculos": v,
                            "observaciones": o, "fecha": datetime.now().strftime("%d/%m/%Y")
                        }
                        save(st.session_state.db)
                        st.success("OK")
        
        with t1:
            cont = st.session_state.db[sel]
            ks = [k for k,v in cont.items() if bus.lower() in v["nombre"].lower()] if bus else list(cont.keys())
            if ks:
                s_obj = st.selectbox("Objetivo", ks)
                curr = cont[s_obj]
                with st.expander("Datos", expanded=True):
                    st.write(f"DNI: {curr['dni']}")
                    st.write(f"Tels: {curr['telefonos']}")
                    st.write(f"Obs: {curr['observaciones']}")
                    if st.button("Borrar"):
                        del st.session_state.db[sel][s_obj]
                        save(st.session_state.db)
                        st.rerun()
        
        with t3:
            if st.button("Excel"):
                rows = []
                for c, items in st.session_state.db.items():
                    for k, val in items.items():
                        val["Carpeta"] = c
                        rows.append(val)
                if rows:
                    df = pd.DataFrame(rows)
                    buf = BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as ex:
                        df.to_excel(ex, index=False)
                    st.download_button("Descargar", buf.getvalue(), "datos.xlsx")
