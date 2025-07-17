# 🔄 Mismo encabezado
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from streamlit_calendar import calendar

# --------------------- Inicialización de datos ---------------------
if "miembros" not in st.session_state:
    st.session_state.miembros = pd.DataFrame(columns=[
        "Nombre", "Rol", "Vacaciones disponibles", "Horas disponibles"])

if "solicitudes" not in st.session_state:
    st.session_state.solicitudes = pd.DataFrame(columns=[
        "Nombre", "Fecha", "Tipo", "Estado", "Horas"])

# --------------------- Funciones auxiliares ---------------------
def obtener_eventos():
    eventos = []
    solicitudes = st.session_state.solicitudes.copy()

    for _, row in solicitudes.iterrows():
        estado = row["Estado"]
        tipo = row["Tipo"]
        nombre = row["Nombre"]

        color = {
            "Aprobado": "green",
            "Rechazado": "gray",
            "Pendiente": "blue",
            "Solapado": "red"
        }.get(estado, "blue")

        if tipo in ["FN", "FR"]:
            title = f"🏖 {tipo}"
            color = "yellow"
            text_color = "black"
        else:
            tipo_texto = {"V": "Vacaciones", "L": "Libre"}[tipo]
            title = f"🧍 {nombre} ({tipo_texto} - {estado})"
            text_color = "white" if color != "yellow" else "black"

        eventos.append({
            "title": title,
            "start": row["Fecha"].strftime("%Y-%m-%d"),
            "end": row["Fecha"].strftime("%Y-%m-%d"),
            "color": color,
            "textColor": text_color
        })

    # Añadir fines de semana para este año y el siguiente
    hoy = date.today()
    for año in [hoy.year, hoy.year + 1]:
        inicio = date(año, 1, 1)
        fin = date(año, 12, 31)
        dia = inicio
        while dia <= fin:
            if dia.weekday() in [5, 6]:  # sábado o domingo
                eventos.append({
                    "title": "🟡 FdS",
                    "start": dia.strftime("%Y-%m-%d"),
                    "end": dia.strftime("%Y-%m-%d"),
                    "color": "yellow",
                    "textColor": "black"
                })
            dia += timedelta(days=1)

    return eventos

def detectar_solapamiento(fecha, rol, umbral=1):
    solicitudes = st.session_state.solicitudes
    coincidencias = solicitudes[(solicitudes["Fecha"] == fecha) & (solicitudes["Estado"].isin(["Aprobado", "Pendiente"]))]
    if coincidencias.empty:
        return False
    coincidencias_mismo_rol = coincidencias.merge(st.session_state.miembros, on="Nombre")
    return (coincidencias_mismo_rol[coincidencias_mismo_rol["Rol"] == rol].shape[0] > umbral)

# --------------------- Navegación ---------------------
pagina = st.sidebar.radio("🧭 Navegación", ["👥 Miembros", "📅 Calendario", "✅ Listado de solicitudes", "📤 Exportar"])

# --------------------- Miembros ---------------------
if pagina == "👥 Miembros":
    st.header("👥 Gestión de miembros")

    with st.form("form_miembros"):
        nombre = st.text_input("Nombre")
        rol = st.selectbox("Rol", ["Funcional", "Integración", "Implantación", "Jefe de Proyecto"])
        vacaciones_disp = st.number_input("Vacaciones disponibles", min_value=0, value=0)
        horas_disp = st.number_input("Horas disponibles", min_value=0, value=0)
        if st.form_submit_button("Añadir miembro"):
            if nombre in st.session_state.miembros["Nombre"].values:
                st.warning("El nombre ya existe. Usa editar si quieres modificarlo.")
            else:
                nuevo_miembro = pd.DataFrame([[nombre, rol, vacaciones_disp, horas_disp]], columns=st.session_state.miembros.columns)
                st.session_state.miembros = pd.concat([st.session_state.miembros, nuevo_miembro], ignore_index=True)
                st.success("Miembro añadido correctamente")

    st.subheader("📋 Lista de miembros")
    for idx, row in st.session_state.miembros.iterrows():
        with st.expander(f"{row['Nombre']}"):
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**Rol:** {row['Rol']}")
            col1.write(f"**Vacaciones disponibles:** {row['Vacaciones disponibles']}")
            col1.write(f"**Horas disponibles:** {row['Horas disponibles']}")
            if col2.button("✏️ Editar", key=f"edit_{idx}"):
                st.session_state.edit_idx = idx
                st.rerun()
            if col3.button("🗑 Eliminar", key=f"delete_{idx}"):
                st.session_state.miembros.drop(index=idx, inplace=True)
                st.session_state.miembros.reset_index(drop=True, inplace=True)
                st.success("Miembro eliminado")
                st.rerun()

    if "edit_idx" in st.session_state:
        idx = st.session_state.edit_idx
        miembro = st.session_state.miembros.loc[idx]
        st.subheader("✏️ Editar miembro")
        with st.form("form_editar"):
            nuevo_nombre = st.text_input("Nombre", value=miembro["Nombre"])
            nuevo_rol = st.selectbox("Rol", ["Funcional", "Integración", "Implantación", "Jefe de Proyecto"], index=["Funcional", "Integración", "Implantación", "Jefe de Proyecto"].index(miembro["Rol"]))
            nuevas_vacaciones = st.number_input("Vacaciones disponibles", min_value=0, value=int(miembro["Vacaciones disponibles"]))
            nuevas_horas = st.number_input("Horas disponibles", min_value=0, value=int(miembro["Horas disponibles"]))
            if st.form_submit_button("Guardar cambios"):
                st.session_state.miembros.at[idx, "Nombre"] = nuevo_nombre
                st.session_state.miembros.at[idx, "Rol"] = nuevo_rol
                st.session_state.miembros.at[idx, "Vacaciones disponibles"] = nuevas_vacaciones
                st.session_state.miembros.at[idx, "Horas disponibles"] = nuevas_horas
                del st.session_state.edit_idx
                st.success("Miembro actualizado")
                st.rerun()

# --------------------- Calendario ---------------------
if pagina == "📅 Calendario":
    st.header("📅 Calendario de solicitudes")
    eventos = obtener_eventos()
    calendar_options = {
        "initialView": "dayGridMonth",
        "locale": "es",
        "selectable": False,
    }
    calendar(events=eventos, options=calendar_options, custom_css="")

    st.subheader("📝 Solicitudes de días")
    with st.form("form_solicitudes"):
        if len(st.session_state.miembros) == 0:
            st.warning("Añade miembros primero.")
        else:
            nombre_s = st.selectbox("Nombre", st.session_state.miembros["Nombre"].unique())
            fecha_s = st.date_input("Fecha")
            tipo_s = st.selectbox("Tipo de solicitud", ["Vacaciones", "Libre Disposición"])
            horas_s = 0
            if tipo_s == "Libre Disposición":
                horas_s = st.number_input("Horas a solicitar", min_value=1, max_value=8, value=1)
            if st.form_submit_button("Enviar solicitud"):
                miembro = st.session_state.miembros[st.session_state.miembros["Nombre"] == nombre_s].iloc[0]
                if tipo_s == "Vacaciones" and miembro["Vacaciones disponibles"] < 1:
                    st.error("No hay suficientes días de vacaciones disponibles.")
                elif tipo_s == "Libre Disposición" and miembro["Horas disponibles"] < horas_s:
                    st.error("No hay suficientes horas disponibles.")
                else:
                    nueva = pd.DataFrame([{ "Nombre": nombre_s, "Fecha": fecha_s, "Tipo": tipo_s[0], "Estado": "Pendiente", "Horas": horas_s }])
                    st.session_state.solicitudes = pd.concat([st.session_state.solicitudes, nueva], ignore_index=True)
                    st.success("Solicitud enviada")

    st.subheader("➕ Añadir festivos")
    with st.form("form_festivos"):
        fecha_festivo = st.date_input("Fecha del festivo", value=date.today())
        tipo_festivo = st.selectbox("Tipo de festivo", ["FN", "FR"])
        if st.form_submit_button("Añadir festivo"):
            festivo = {
                "Nombre": "Festivo",
                "Fecha": fecha_festivo,
                "Tipo": tipo_festivo,
                "Estado": "Aprobado",
                "Horas": 0
            }
            st.session_state.solicitudes = pd.concat([st.session_state.solicitudes, pd.DataFrame([festivo])], ignore_index=True)
            st.success(f"Festivo {tipo_festivo} añadido")

# --------------------- Listado de solicitudes ---------------------
if pagina == "✅ Listado de solicitudes":
    st.header("✅ Listado de solicitudes")
    pendientes = st.session_state.solicitudes[st.session_state.solicitudes["Estado"] == "Pendiente"]
    for idx, row in pendientes.iterrows():
        with st.expander(f"{row['Nombre']} - {row['Fecha']} ({row['Tipo']})"):
            cols = st.columns([1, 1, 1])
            miembro = st.session_state.miembros[st.session_state.miembros["Nombre"] == row["Nombre"]].iloc[0]
            rol = miembro["Rol"]
            if cols[0].button("Aprobar", key=f"ap_{idx}"):
                if row["Tipo"] == "V":
                    if miembro["Vacaciones disponibles"] >= 1:
                        st.session_state.miembros.loc[st.session_state.miembros["Nombre"] == row["Nombre"], "Vacaciones disponibles"] -= 1
                        nuevo_estado = "Aprobado"
                        if detectar_solapamiento(row["Fecha"], rol):
                            nuevo_estado = "Solapado"
                        st.session_state.solicitudes.at[idx, "Estado"] = nuevo_estado
                        st.success("Solicitud aprobada")
                    else:
                        st.error("No hay suficientes días de vacaciones disponibles.")
                elif row["Tipo"] == "L":
                    horas = row["Horas"]
                    if miembro["Horas disponibles"] >= horas:
                        st.session_state.miembros.loc[st.session_state.miembros["Nombre"] == row["Nombre"], "Horas disponibles"] -= horas
                        nuevo_estado = "Aprobado"
                        if detectar_solapamiento(row["Fecha"], rol):
                            nuevo_estado = "Solapado"
                        st.session_state.solicitudes.at[idx, "Estado"] = nuevo_estado
                        st.success("Solicitud aprobada")
                    else:
                        st.error("No hay suficientes horas disponibles.")
            if cols[1].button("Rechazar", key=f"rej_{idx}"):
                st.session_state.solicitudes.at[idx, "Estado"] = "Rechazado"
                st.error("Solicitud rechazada")
            if cols[2].button("🗑 Eliminar", key=f"del_{idx}"):
                st.session_state.solicitudes.drop(index=idx, inplace=True)
                st.session_state.solicitudes.reset_index(drop=True, inplace=True)
                st.warning("Solicitud eliminada")
                st.rerun()

# --------------------- Exportar ---------------------
if pagina == "📤 Exportar":
    st.header("📤 Exportar datos")
    excel_data = {
        "Miembros": st.session_state.miembros,
        "Solicitudes": st.session_state.solicitudes[["Nombre", "Fecha", "Tipo", "Estado"]]
    }

    with pd.ExcelWriter("export_vacaciones.xlsx", engine="xlsxwriter") as writer:
        for hoja, df in excel_data.items():
            df.to_excel(writer, sheet_name=hoja, index=False)

    with open("export_vacaciones.xlsx", "rb") as f:
        st.download_button("Descargar Excel", data=f.read(), file_name="vacaciones.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
