import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="OP PJ MERIDA", layout="wide", page_icon="🛡️")

def check_password():
    if "rol" not in st.session_state:
        st.session_state.rol = None
    if st.session_state.rol is not None:
        return True

    st.title("🛡️ CONTROL DE ACCESO - OP PJ MERIDA")
    pw = st.text_input("Clave de Seguridad", type="password")
    if st.button("Entrar"):
        if pw == st.secrets.get("pass_admin"):
            st.session_state.rol = "admin"
            st.rerun()
        elif pw == st.secrets.get("pass_consulta"):
            st.session_state.rol = "consulta"
            st.rerun()
        else:
            st.error("Clave incorrecta")
    return False

# 2. GESTIÓN DE BASE DE DATOS
DB_FILE = "database_pj_merida.json"

def cargar_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"operaciones": {}, "config_privacidad": {}}

def guardar_db(datos):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# 3. LÓGICA PRINCIPAL
if check_password():
    if "db" not in st.session_state:
        st.session_state.db = cargar_db()
    
    db = st.session_state.db
    rol = st.session_state.rol

    # BARRA LATERAL
    st.sidebar.title(f"👮 PERFIL: {rol.upper()}")
    menu = st.sidebar.radio("MENÚ PRINCIPAL", ["GESTIÓN OPERATIVA", "🔍 CENTRAL DE BÚSQUEDA"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.rol = None
        st.rerun()

    if menu == "🔍 CENTRAL DE BÚSQUEDA":
        st.title("🔍 Central de Búsqueda Transversal")
        query = st.text_input("Nombre, Alias, DNI o Matrícula:", placeholder="Ej: 1234BBB")
        
        if query:
            encontrado = []
            resumen_texto = f"INFORME DE BÚSQUEDA - OP PJ MERIDA\nFECHA: {datetime.now()}\nCRITERIO: {query}\n" + "="*30 + "\n"
            
            for op_n, op_d in db["operaciones"].items():
                if rol != "admin" and not db["config_privacidad"].get(op_n, False): continue
                
                # Buscar en Objetivos
                for obj_id, info in op_d["objetivos"].items():
                    if query.lower() in obj_id.lower() or query.lower() in info.get("dni","").lower():
                        st.info(f"👤 OBJETIVO: {obj_id} (En {op_n})")
                        resumen_texto += f"\n[OBJETIVO] {obj_id} en {op_n}\nRol: {info['rol']}\n"
                        encontrado.append(obj_id)

                # Buscar en Medios
                for m in op_d.get("medios", []):
                    if query.lower() in m["ID"].lower():
                        st.warning(f"🚗/📞 MEDIO: {m['ID']} ({m['Tipo']}) en {op_n}")
                        resumen_texto += f"\n[MEDIO] {m['ID']} ({m['Tipo']}) - Relación: {m['Objetivo']}\n"
                        encontrado.append(m["ID"])

            if encontrado:
                st.download_button("📥 EXPORTAR FICHA DE BÚSQUEDA", resumen_texto, file_name=f"Ficha_{query}.txt")
            else:
                st.error("Sin coincidencias.")

    elif menu == "GESTIÓN OPERATIVA":
        if rol == "admin":
            st.sidebar.subheader("⚡ Nueva Operación")
            n_op = st.sidebar.text_input("Nombre:")
            if st.sidebar.button("Crear"):
                if n_op:
                    nombre_full = f"OP. {n_op.upper()}"
                    db["operaciones"][nombre_full] = {"objetivos":{}, "medios":[], "actuaciones":[], "juzgado":[], "informes_operativos":[], "documentos":[]}
                    db["config_privacidad"][nombre_full] = False
                    guardar_db(db); st.rerun()

        ops_vis = [o for o in db["operaciones"].keys() if rol == "admin" or db["config_privacidad"].get(o, False)]
        op_sel = st.sidebar.selectbox("📂 Seleccionar OPERACIÓN", ["---"] + ops_vis)

        if op_sel != "---":
            st.title(f"🛡️ {op_sel}")
            if rol == "admin":
                vis = st.toggle("Visible para usuarios CONSULTA", value=db["config_privacidad"].get(op_sel, False))
                if vis != db["config_privacidad"].get(op_sel, False):
                    db["config_privacidad"][op_sel] = vis
                    guardar_db(db); st.toast("Privacidad actualizada")

            t_obj, t_med, t_inf, t_juz, t_act, t_doc = st.tabs(["👤 OBJETIVOS", "📞 MEDIOS", "📋 INF. OPERATIVO", "⚖️ JUZGADO", "📝 ACTUACIONES", "📂 ARCHIVOS"])

            # MÓDULO OBJETIVOS
            with t_obj:
                with st.expander("➕ Añadir Objetivo"):
                    with st.form("f_obj"):
                        nom = st.text_input("Nombre y Apellidos"); al = st.text_input("Alias")
                        dni = st.text_input("DNI/NIE"); rl = st.selectbox("Rol", ["Líder", "Logística", "Seguridad", "Trapicheo", "Otros"])
                        vin = st.text_input("Vínculos detectados")
                        if st.form_submit_button("Guardar"):
                            db["operaciones"][op_sel]["objetivos"][f"{nom} ({al})"] = {"dni":dni, "alias":al, "rol":rl, "tipo_vinculo":vin}
                            guardar_db(db); st.rerun()
                for o, d in db["operaciones"][op_sel]["objetivos"].items():
                    st.write(f"**{o}** - {d['rol']} (DNI: {d['dni']})")

            # MÓDULO MEDIOS
            with t_med:
                with st.form("f_med"):
                    tip = st.radio("Tipo", ["Vehículo", "Teléfono"], horizontal=True)
                    ident = st.text_input("Matrícula / Número")
                    pose = st.selectbox("Relacionar con", ["Desconocido"] + list(db["operaciones"][op_sel]["objetivos"].keys()))
                    uso = st.radio("Relación", ["Propietario", "Usuario Habitual"])
                    if st.form_submit_button("Registrar"):
                        db["operaciones"][op_sel]["medios"].append({"Tipo":tip, "ID":ident, "Objetivo":pose, "Rol":uso})
                        guardar_db(db); st.rerun()
                st.table(db["operaciones"][op_sel]["medios"])

            # MÓDULO INFORME OPERATIVO (Escritura Libre)
            with t_inf:
                with st.form("f_inf"):
                    c1, c2 = st.columns(2)
                    f_op = c1.date_input("Fecha"); h_op = c2.text_input("Horario (Inicio-Fin)")
                    txt = st.text_area("Relato de hechos (Formato libre)")
                    if st.form_submit_button("Guardar Informe"):
                        db["operaciones"][op_sel]["informes_operativos"].append({"fecha":str(f_op), "horario":h_op, "contenido":txt, "autor":rol})
                        guardar_db(db); st.rerun()
                for i in reversed(db["operaciones"][op_sel]["informes_operativos"]):
                    st.info(f"**{i['fecha']} ({i['horario']})**\n\n{i['contenido']}\n*Autor: {i['autor']}*")

            # MÓDULO JUZGADO
            with t_juz:
                with st.form("f_juz"):
                    j = st.text_input("Juzgado"); m = st.text_area("Mandamientos"); e = st.text_area("Entrevistas/Ampliatorias")
                    if st.form_submit_button("Guardar"):
                        db["operaciones"][op_sel]["juzgado"].append({"juzgado":j, "mandamientos":m, "entrevistas":e})
                        guardar_db(db); st.rerun()
                st.write(db["operaciones"][op_sel]["juzgado"])

            # MÓDULO DOCUMENTOS (Archivos)
            with t_doc:
                st.subheader("Subida de Documentación Técnica")
                up = st.file_uploader("Seleccione PDF, Word, Excel...", type=["pdf","docx","xlsx","jpg"])
                desc = st.text_input("Descripción del archivo")
                if st.button("Subir"):
                    if up and desc:
                        db["operaciones"][op_sel]["documentos"].append({"archivo":up.name, "desc":desc, "fecha":datetime.now().strftime("%d/%m/%Y")})
                        guardar_db(db); st.success("Registrado")
                st.write(db["operaciones"][op_sel]["documentos"])
