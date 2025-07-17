import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from io import BytesIO
import plotly.express as px

st.set_page_config(page_title="Gestión de Vacaciones", layout="wide")

# -------------------- Configuración inicial --------------------
RUTA_MIEMBROS = "data_miembros.csv"
RUTA_SOLICITUDES = "data_solicitudes.csv"

ROLES = ["Funcional", "Integración", "Implantación"]
TIPOS_SOLICITUD = ["Vacaciones", "Libre disposición"]
ESTADOS = ["Pendiente", "Aprobada", "Rechazada"]

# -------------------- Carga y guardado de datos --------------------
def cargar_datos():
    if os.path.exists(RUTA_MIEMBROS):
        miembros = pd.read_csv(RUTA_MIEMBROS)
    else:
        miembros = pd.DataFrame(columns=["Nombre", "Rol", "Vacaciones disponibles", "Horas disponibles"])
        
    if os.path.exists(RUTA_SOLICITUDES):
        solicitudes = pd.read_csv(RUTA_SOLICITUDES, parse_dates=["Fecha"])
    else:
        solicitudes = pd.DataFrame(columns=["Nombre", "Rol", "Fecha", "Tipo", "Estado", "Comentario"])
        
    return miembros, solicitudes

def guardar_datos(miembros, solicitudes):
    miembros.to_csv(RUTA_MIEMBROS, index=False)
    solicitudes.to_csv(RUTA_SOLICITUDES, index=False)

# -------------------- Lógica de solapamientos --------------------
def detectar_solapamientos(solicitudes):
    solapados = set()
    solicitudes_aprob_pend = solicitudes[solicitudes["Estado"].isin(["Aprobada", "Pendiente"])]
    for (fecha, rol), grupo in solicitudes_aprob_pend.groupby(["Fecha", "Rol"]):
        if len(grupo) > 1:
            solapados.update(grupo.index)
    return solapados

# -------------------- Vista: Miembros --------------------
def mostrar_tab_miembros(miembros):
    st.subheader("Gestión de miembros del equipo")

    with st.expander("➕ Añadir nuevo miembro"):
        with st.form("form_miembro"):
            nombre = st.text_input("Nombre")
            rol = st.selectbox("Rol", ROLES)
            vacaciones = st.number_input("Vacaciones disponibles", min_value=0, step=1)
            horas = st.number_input("Horas disponibles", min_value=0, step=1)
            submitted = st.form_submit_button("Guardar")
            if submitted and nombre:
                nuevo = pd.DataFrame([[nombre, rol, vacaciones, horas]], columns=miembros.columns)
                miembros = pd.concat([miembros, nuevo], ignore_index=True)
                guardar_datos(miembros, solicitudes)
                st.success("Miembro añadido correctamente")

    st.dataframe(miembros)

    eliminar = st.multiselect("Selecciona miembros a eliminar", miembros["Nombre"])
    if eliminar:
        miembros = miembros[~miembros["Nombre"].isin(eliminar)]
        guardar_datos(miembros, solicitudes)
        st.success("Miembros eliminados")

    return miembros

# -------------------- Vista: Calendario y solicitudes --------------------
def mostrar_tab_calendario(miembros, solicitudes):
    st.subheader("Calendario de solicitudes y festivos")

    # Calendario visual básico (puedes usar streamlit_calendar si lo tienes instalado)
    calendario = solicitudes.copy()
    calendario["Color"] = calendario["Estado"].map({
        "Aprobada": "green",
        "Rechazada": "gray",
        "Pendiente": "blue"
    })

    solapamientos = detectar_solapamientos(solicitudes)
    calendario.loc[calendario.index.isin(solapamientos), "Color"] = "red"

    fig = px.timeline(
        calendario, x_start="Fecha", x_end="Fecha",
        y="Nombre", color="Color", title="Calendario de eventos",
        hover_data=["Tipo", "Estado", "Rol"]
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("➕ Solicitar nuevo día")
    with st.form("form_solicitud"):
        nombre = st.selectbox("Miembro", miembros["Nombre"])
        fecha = st.date_input("Fecha de la solicitud")
        tipo = st.selectbox("Tipo", TIPOS_SOLICITUD)
        comentario = st.text_input("Comentario (opcional)")
        enviar = st.form_submit_button("Solicitar")

        if enviar:
            miembro = miembros[miembros["Nombre"] == nombre].iloc[0]
            rol = miembro["Rol"]

            # Control de disponibilidad
            if tipo == "Vacaciones" and miembro["Vacaciones disponibles"] <= 0:
                st.error("No quedan vacaciones disponibles.")
            elif tipo == "Libre disposición" and miembro["Horas disponibles"] < 4:
                st.error("No quedan horas suficientes (mínimo 4h por solicitud).")
            else:
                nueva = pd.DataFrame([[nombre, rol, fecha, tipo, "Pendiente", comentario]],
                                     columns=solicitudes.columns)
                solicitudes = pd.concat([solicitudes, nueva], ignore_index=True)
                guardar_datos(miembros, solicitudes)
                st.success("Solicitud enviada")

    return solicitudes

# -------------------- Vista: Listado de solicitudes --------------------
def mostrar_tab_solicitudes(miembros, solicitudes):
    st.subheader("Listado de solicitudes")

    for idx, fila in solicitudes.iterrows():
        with st.expander(f"{fila['Fecha'].date()} - {fila['Nombre']} ({fila['Estado']})"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Tipo:** {fila['Tipo']}")
                st.write(f"**Rol:** {fila['Rol']}")
                st.write(f"**Comentario:** {fila['Comentario']}")

            with col2:
                if fila["Estado"] == "Pendiente":
                    if st.button("✅ Aprobar", key=f"aprobar_{idx}"):
                        solicitudes.at[idx, "Estado"] = "Aprobada"
                        miembro_idx = miembros[miembros["Nombre"] == fila["Nombre"]].index[0]
                        if fila["Tipo"] == "Vacaciones":
                            miembros.at[miembro_idx, "Vacaciones disponibles"] -= 1
                        else:
                            miembros.at[miembro_idx, "Horas disponibles"] -= 4
                        guardar_datos(miembros, solicitudes)
                        st.success("Solicitud aprobada")

                    if st.button("❌ Rechazar", key=f"rechazar_{idx}"):
                        solicitudes.at[idx, "Estado"] = "Rechazada"
                        guardar_datos(miembros, solicitudes)
                        st.warning("Solicitud rechazada")

            with col3:
                if st.button("🗑️ Eliminar", key=f"eliminar_{idx}"):
                    solicitudes = solicitudes.drop(idx).reset_index(drop=True)
                    guardar_datos(miembros, solicitudes)
                    st.info("Solicitud eliminada")

    return solicitudes

# -------------------- Exportar a Excel --------------------
def exportar_excel(miembros, solicitudes):
    st.subheader("📤 Exportar datos")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        miembros.to_excel(writer, sheet_name="Miembros", index=False)
        solicitudes.to_excel(writer, sheet_name="Solicitudes", index=False)
        resumen = solicitudes.groupby(["Nombre", "Tipo", "Estado"]).size().unstack(fill_value=0)
        resumen.to_excel(writer, sheet_name="Resumen", index=True)
    st.download_button("📥 Descargar Excel", data=output.getvalue(), file_name="vacaciones.xlsx")

# -------------------- Interfaz principal --------------------
st.title("🗓️ Gestión de Vacaciones y Días Libres")
menu = st.sidebar.radio("Navegación", ["Miembros", "Calendario", "Listado de solicitudes", "Exportar"])

miembros, solicitudes = cargar_datos()

if menu == "Miembros":
    miembros = mostrar_tab_miembros(miembros)
elif menu == "Calendario":
    solicitudes = mostrar_tab_calendario(miembros, solicitudes)
elif menu == "Listado de solicitudes":
    solicitudes = mostrar_tab_solicitudes(miembros, solicitudes)
elif menu == "Exportar":
    exportar_excel(miembros, solicitudes)
