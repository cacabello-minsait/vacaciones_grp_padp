# utils.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from streamlit_calendar import calendar
import json

# -------------------- ARCHIVOS --------------------
RUTA_MIEMBROS = "data/miembros.csv"
RUTA_SOLICITUDES = "data/solicitudes.csv"
RUTA_FESTIVOS = "data/festivos.csv"

# -------------------- CARGA Y GUARDADO --------------------
def cargar_datos_miembros():
    try:
        df = pd.read_csv(RUTA_MIEMBROS)
        return df
    except:
        return pd.DataFrame(columns=[
            "Nombre", "Tipo de miembro",
            "Vacaciones disponibles", "Vacaciones solicitadas", "Vacaciones pendientes",
            "Horas disponibles", "Horas solicitadas", "Horas pendientes"
        ])

def guardar_datos_miembros(df):
    df.to_csv(RUTA_MIEMBROS, index=False)

def cargar_solicitudes():
    try:
        return pd.read_csv(RUTA_SOLICITUDES, parse_dates=["Fecha"])
    except:
        return pd.DataFrame(columns=["Nombre", "Tipo", "Fecha", "Etiqueta", "Estado"])

def guardar_solicitudes(df):
    df.to_csv(RUTA_SOLICITUDES, index=False)

def cargar_festivos():
    try:
        return pd.read_csv(RUTA_FESTIVOS, parse_dates=["Fecha"])
    except:
        return pd.DataFrame(columns=["Fecha", "Tipo"])

def guardar_festivos(df):
    df.to_csv(RUTA_FESTIVOS, index=False)

# -------------------- TAB 1: MIEMBROS --------------------
def mostrar_tab_miembros():
    st.header("👥 Gestión de miembros")
    df = cargar_datos_miembros()

    with st.form("form_miembro"):
        nombre = st.text_input("Nombre")
        tipo = st.selectbox("Tipo de miembro", ["Consultoría", "Integración", "Jefatura de Proyecto", "Implantación"])
        vacaciones = st.number_input("Días de vacaciones disponibles", min_value=0)
        horas = st.number_input("Horas de libre disposición disponibles", min_value=0)
        submit = st.form_submit_button("Guardar o actualizar")

        if submit and nombre:
            if nombre in df["Nombre"].values:
                df.loc[df["Nombre"] == nombre, ["Tipo de miembro", "Vacaciones disponibles", "Horas disponibles"]] = [tipo, vacaciones, horas]
            else:
                nueva = {
                    "Nombre": nombre,
                    "Tipo de miembro": tipo,
                    "Vacaciones disponibles": vacaciones,
                    "Vacaciones solicitadas": 0,
                    "Vacaciones pendientes": vacaciones,
                    "Horas disponibles": horas,
                    "Horas solicitadas": 0,
                    "Horas pendientes": horas
                }
                df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
            guardar_datos_miembros(df)
            st.success("Datos actualizados.")

    st.dataframe(df)

# -------------------- TAB 2: CALENDARIO --------------------
def mostrar_tab_calendario(usuario, rol):
    st.header("📅 Calendario de solicitudes")

    df_miembros = cargar_datos_miembros()
    df_solicitudes = cargar_solicitudes()
    df_festivos = cargar_festivos()

    eventos = []

    for _, row in df_solicitudes.iterrows():
        color = "#3788d8"  # Azul por defecto
        if row["Estado"] == "Aprobada":
            color = "green"
        elif row["Estado"] == "Rechazada":
            color = "gray"
        elif hay_solapamiento(row, df_solicitudes, df_miembros):
            color = "red"

        eventos.append({
            "title": f"{row['Etiqueta']} - {row['Nombre']}",
            "start": row["Fecha"].strftime("%Y-%m-%d"),
            "end": row["Fecha"].strftime("%Y-%m-%d"),
            "color": color
        })

    for _, row in df_festivos.iterrows():
        eventos.append({
            "title": row["Tipo"],
            "start": row["Fecha"].strftime("%Y-%m-%d"),
            "end": row["Fecha"].strftime("%Y-%m-%d"),
            "color": "yellow"
        })

    config = {"editable": False, "selectable": True}
    calendario = calendar(events=eventos, options=config)

    if calendario.get("date"):
        fecha = pd.to_datetime(calendario["date"][:10])
        with st.expander(f"📅 Solicitar para {fecha.date()}"):
            tipo_solicitud = st.radio("Tipo de solicitud", ["Vacaciones", "Libre disposición", "Festivo"])
            if tipo_solicitud == "Festivo":
                tipo = st.selectbox("Tipo de festivo", ["FS", "FN", "FR"])
                df_festivos = pd.concat([df_festivos, pd.DataFrame([{"Fecha": fecha, "Tipo": tipo}])], ignore_index=True)
                guardar_festivos(df_festivos)
                st.success("Festivo añadido")
            else:
                nueva = {
                    "Nombre": usuario,
                    "Tipo": tipo_solicitud,
                    "Fecha": fecha,
                    "Etiqueta": "V" if tipo_solicitud == "Vacaciones" else "L",
                    "Estado": "Pendiente"
                }
                df_solicitudes = pd.concat([df_solicitudes, pd.DataFrame([nueva])], ignore_index=True)
                guardar_solicitudes(df_solicitudes)
                st.success("Solicitud registrada")

    if rol == "Jefe de proyecto":
        st.subheader("✅ Aprobar o rechazar solicitudes pendientes")
        pendientes = df_solicitudes[df_solicitudes["Estado"] == "Pendiente"]
        for i, row in pendientes.iterrows():
            with st.expander(f"{row['Nombre']} solicita {row['Tipo']} el {row['Fecha'].date()}"):
                col1, col2 = st.columns(2)
                if col1.button("✅ Aprobar", key=f"ap_{i}"):
                    df_solicitudes.at[i, "Estado"] = "Aprobada"
                    actualizar_miembro(row)
                    guardar_solicitudes(df_solicitudes)
                    st.success("Solicitud aprobada")
                if col2.button("❌ Rechazar", key=f"re_{i}"):
                    df_solicitudes.at[i, "Estado"] = "Rechazada"
                    guardar_solicitudes(df_solicitudes)
                    st.warning("Solicitud rechazada")

# -------------------- TAB 3: SOLAPAMIENTOS --------------------
def mostrar_tab_solapamientos():
    st.header("⚠️ Solapamientos detectados")
    df_miembros = cargar_datos_miembros()
    df = cargar_solicitudes()
    df_aprobadas = df[df["Estado"] == "Pendiente"]

    conflictos = []
    for i, row in df_aprobadas.iterrows():
        if hay_solapamiento(row, df, df_miembros):
            mismo_dia = df[(df["Fecha"] == row["Fecha"]) & (df["Nombre"] != row["Nombre"])]
            coinciden = mismo_dia[mismo_dia["Tipo"] == row["Tipo"]]["Nombre"].tolist()
            conflictos.append({
                "Nombre": row["Nombre"],
                "Tipo": row["Tipo"],
                "Fecha": row["Fecha"].date(),
                "Coincide con": ", ".join(coinciden)
            })

    if conflictos:
        st.dataframe(pd.DataFrame(conflictos))
    else:
        st.success("✅ No hay solapamientos detectados")

# -------------------- LÓGICA AUXILIAR --------------------
def hay_solapamiento(row, df, df_miembros):
    mismo_dia = df[(df["Fecha"] == row["Fecha"]) & (df["Nombre"] != row["Nombre"])]
    tipo_miembro = df_miembros[df_miembros["Nombre"] == row["Nombre"]]["Tipo de miembro"].values
    if not tipo_miembro:
        return False
    tipo_miembro = tipo_miembro[0]
    coincidencias = mismo_dia[mismo_dia["Estado"] == "Aprobada"]
    coincidencias = coincidencias[coincidencias["Nombre"].isin(
        df_miembros[df_miembros["Tipo de miembro"] == tipo_miembro]["Nombre"]
    )]
    return not coincidencias.empty

def actualizar_miembro(row):
    df = cargar_datos_miembros()
    idx = df[df["Nombre"] == row["Nombre"]].index[0]
    if row["Tipo"] == "Vacaciones":
        df.at[idx, "Vacaciones solicitadas"] += 1
    else:
        df.at[idx, "Horas solicitadas"] += 8
    df["Vacaciones pendientes"] = df["Vacaciones disponibles"] - df["Vacaciones solicitadas"]
    df["Horas pendientes"] = df["Horas disponibles"] - df["Horas solicitadas"]
    guardar_datos_miembros(df)

# -------------------- EXPORTACIÓN --------------------
def exportar_datos_excel():
    df_miembros = cargar_datos_miembros()
    df_solicitudes = cargar_solicitudes()
    df_festivos = cargar_festivos()

    calendario = df_solicitudes.copy()
    calendario["Visual"] = calendario["Etiqueta"] + " (" + calendario["Estado"] + ")"

    with BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            calendario.to_excel(writer, sheet_name="Calendario detallado", index=False)
            df_miembros.to_excel(writer, sheet_name="Resumen por miembro", index=False)
            df_festivos.to_excel(writer, sheet_name="Festivos", index=False)
        buffer.seek(0)
        st.download_button("Descargar Excel", buffer, file_name="solicitudes_export.xlsx")