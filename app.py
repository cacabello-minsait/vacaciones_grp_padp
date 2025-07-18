import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date, timedelta, datetime
from streamlit_calendar import calendar

DB = "vacaciones.db"
st.set_page_config(page_title="Gestión de Vacaciones", layout="wide")

# ---------- INICIALIZACIÓN ----------
def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS miembros (
        nombre TEXT PRIMARY KEY,
        rol TEXT,
        vacaciones_disp INTEGER,
        horas_disp INTEGER
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS solicitudes (
        id TEXT PRIMARY KEY,
        nombre TEXT,
        rol TEXT,
        tipo TEXT,
        fecha TEXT,
        estado TEXT,
        comentario TEXT,
        horas INTEGER
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS festivos (
        fecha TEXT PRIMARY KEY,
        nombre TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

# ---------- FUNCIONES DE DATOS ----------
def cargar_miembros():
    return pd.read_sql("SELECT * FROM miembros", sqlite3.connect(DB))

def cargar_solicitudes():
    return pd.read_sql("SELECT * FROM solicitudes", sqlite3.connect(DB))

def cargar_festivos():
    return pd.read_sql("SELECT * FROM festivos", sqlite3.connect(DB))

def agregar_miembro(nombre, rol, vacaciones, horas):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT OR REPLACE INTO miembros VALUES (?, ?, ?, ?)", (nombre, rol, vacaciones, horas))
    conn.commit()
    conn.close()

def eliminar_miembro(nombre):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM miembros WHERE nombre = ?", (nombre,))
    conn.commit()
    conn.close()

def agregar_solicitud(nombre, rol, tipo, fecha, horas=0):
    conn = sqlite3.connect(DB)
    id_solicitud = str(uuid.uuid4())
    conn.execute("INSERT INTO solicitudes VALUES (?, ?, ?, ?, ?, 'pendiente', '', ?)",
                 (id_solicitud, nombre, rol, tipo, fecha, horas))
    conn.commit()
    conn.close()

def actualizar_estado(id_solicitud, nuevo_estado, comentario=""):
    conn = sqlite3.connect(DB)
    try:
        if nuevo_estado == "aprobado":
            solicitud = pd.read_sql("SELECT * FROM solicitudes WHERE id = ?", conn, params=(id_solicitud,))
            tipo = solicitud["tipo"].values[0]
            nombre = solicitud["nombre"].values[0]
            horas = solicitud["horas"].values[0] or 0

            conn.execute("UPDATE solicitudes SET estado = ?, comentario = ? WHERE id = ?",
                         (nuevo_estado, comentario, id_solicitud))

            if tipo == "Vacaciones":
                conn.execute("UPDATE miembros SET vacaciones_disp = MAX(vacaciones_disp - 1, 0) WHERE nombre = ?", (nombre,))
            elif tipo == "Libre Disposición" and horas > 0:
                conn.execute("UPDATE miembros SET horas_disp = MAX(horas_disp - ?, 0) WHERE nombre = ?", (horas, nombre))
        else:
            conn.execute("UPDATE solicitudes SET estado = ?, comentario = ? WHERE id = ?",
                         (nuevo_estado, comentario, id_solicitud))

        conn.commit()
    finally:
        conn.close()

def eliminar_solicitud(id_solicitud):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM solicitudes WHERE id = ?", (id_solicitud,))
    conn.commit()
    conn.close()

def hay_disponibilidad(nombre, tipo, horas=1):
    df = cargar_miembros()
    fila = df[df["nombre"] == nombre]
    if fila.empty:
        return False
    if tipo == "Vacaciones":
        return fila["vacaciones_disp"].values[0] > 0
    elif tipo == "Libre Disposición":
        return fila["horas_disp"].values[0] >= horas
    return False

def agregar_festivo(fecha, nombre):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT OR REPLACE INTO festivos VALUES (?, ?)", (fecha, nombre))
    conn.commit()
    conn.close()

# ---------- INTERFAZ ----------
st.markdown("<h1 style='text-align: center; color: #3c6e71;'>🗓️ Gestión de Vacaciones del Equipo</h1>", unsafe_allow_html=True)

menu = st.sidebar.radio("Menú", ["👥 Miembros", "📅 Calendario", "📋 Listado de Solicitudes"])

# ---------- MIEMBROS ----------
if menu == "👥 Miembros":
    st.subheader("👥 Gestión de Miembros del Equipo")
    with st.expander("➕ Añadir nuevo miembro"):
        with st.form("form_miembro"):
            nombre = st.text_input("Nombre")
            rol = st.selectbox("Rol", ["Funcional", "Integración", "Implantación"])
            vacaciones = st.number_input("Vacaciones disponibles", 0, 100, 22)
            horas = st.number_input("Horas libres disponibles", 0, 100, 16)
            if st.form_submit_button("Guardar miembro"):
                if nombre:
                    agregar_miembro(nombre, rol, vacaciones, horas)
                    st.success("Miembro guardado correctamente.")
                    st.rerun()
                else:
                    st.warning("El nombre no puede estar vacío.")

    st.divider()
    st.markdown("### 📋 Lista de miembros")
    miembros = cargar_miembros()
    if not miembros.empty:
        for idx, row in miembros.iterrows():
            with st.expander(f"👤 {row['nombre']} - {row['rol']}"):
                st.write(f"**Vacaciones disponibles**: {row['vacaciones_disp']}")
                st.write(f"**Horas libres disponibles**: {row['horas_disp']}")
                if st.button("❌ Eliminar", key=f"del_{row['nombre']}"):
                    eliminar_miembro(row['nombre'])
                    st.rerun()
    else:
        st.info("No hay miembros registrados.")

# ---------- CALENDARIO ----------
elif menu == "📅 Calendario":
    st.subheader("📆 Calendario de Solicitudes")
    solicitudes = cargar_solicitudes()
    eventos = []

    for _, row in solicitudes.iterrows():
        color = {
            "aprobado": "#3fb950",
            "pendiente": "#1f77b4",
            "rechazado": "#999999"
        }.get(row["estado"], "#f6c71e")
        eventos.append({
            "title": f"{row['nombre']} - {row['tipo']}",
            "start": row["fecha"],
            "end": row["fecha"],
            "color": color
        })

    # Fines de semana
    hoy = date.today()
    fecha_fin = hoy.replace(year=hoy.year + 2)
    delta = timedelta(days=1)
    f = hoy
    while f <= fecha_fin:
        if f.weekday() >= 5:
            eventos.append({
                "title": "Fin de semana",
                "start": f.isoformat(),
                "end": f.isoformat(),
                "color": "#facc15"
            })
        f += delta

    # Añadir festivos guardados
    festivos = cargar_festivos()
    for _, row in festivos.iterrows():
        eventos.append({
            "title": row["nombre"],
            "start": row["fecha"],
            "end": row["fecha"],
            "color": "#facc15"
        })

    # Formulario de festivo
    st.markdown("### 🏖️ Añadir Festivo Manual")
    with st.form("form_festivo"):
        festivo_fecha = st.date_input("Fecha festiva", min_value=date(2020,1,1), key="festivo_fecha")
        festivo_nombre = st.text_input("Nombre del festivo", "Festivo", key="festivo_nombre")
        if st.form_submit_button("Añadir festivo"):
            agregar_festivo(festivo_fecha.isoformat(), festivo_nombre)
            st.success("Festivo añadido correctamente.")
            st.rerun()

    # Formulario de solicitud
    st.markdown("### 📝 Solicitar día libre")
    miembros = cargar_miembros()
    if miembros.empty:
        st.warning("Debes registrar al menos un miembro.")
    else:
        nombre = st.selectbox("Miembro", miembros["nombre"], key="sol_nombre")
        tipo = st.selectbox("Tipo de solicitud", ["Vacaciones", "Libre Disposición"], key="sol_tipo")
        mostrar_horas = tipo == "Libre Disposición"

        if mostrar_horas:
            horas = st.number_input("Horas solicitadas", min_value=1, max_value=9, value=1, key="sol_horas")
        else:
            horas = 0

        fecha = st.date_input("Fecha solicitada", min_value=date.today(), key="sol_fecha")

        with st.form("form_solicitud"):
            if st.form_submit_button("Solicitar"):
                if hay_disponibilidad(nombre, tipo, horas):
                    rol = miembros.set_index("nombre").loc[nombre]["rol"]
                    agregar_solicitud(nombre, rol, tipo, fecha.isoformat(), horas)
                    st.success("Solicitud registrada.")
                    st.rerun()
                else:
                    st.warning("No tienes disponibilidad suficiente.")

    calendar_options = {"initialView": "dayGridMonth", "locale": "es"}
    calendar(events=eventos, options=calendar_options)

# ---------- LISTADO DE SOLICITUDES ----------
elif menu == "📋 Listado de Solicitudes":
    st.subheader("📋 Gestión de Solicitudes")
    solicitudes = cargar_solicitudes()

    if solicitudes.empty:
        st.info("No hay solicitudes registradas.")
    else:
        for _, row in solicitudes.iterrows():
            with st.expander(f"📅 {row['fecha']} - {row['nombre']} ({row['tipo']})"):
                st.write(f"**Estado**: {row['estado'].capitalize()}")
                st.write(f"**Rol**: {row['rol']}")
                if row["tipo"] == "Libre Disposición":
                    st.write(f"**Horas solicitadas**: {row['horas']}h")
                st.write(f"**Comentario**: {row['comentario'] or '—'}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Aprobar", key=f"ap_{row['id']}"):
                        actualizar_estado(row["id"], "aprobado")
                        st.rerun()
                with col2:
                    if st.button("❌ Rechazar", key=f"rej_{row['id']}"):
                        actualizar_estado(row["id"], "rechazado")
                        st.rerun()
                with col3:
                    if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                        eliminar_solicitud(row["id"])
                        st.rerun()

# ---------- EXPORTACIÓN ----------
st.sidebar.markdown("### 📁 Exportar datos")
if st.sidebar.button("📥 Exportar a Excel"):
    miembros = cargar_miembros()
    solicitudes = cargar_solicitudes()

    calendario_df = solicitudes.copy()
    calendario_df["Evento"] = calendario_df["nombre"] + " - " + calendario_df["tipo"]
    calendario_df["Color"] = calendario_df["estado"].map({
        "aprobado": "Verde",
        "pendiente": "Azul",
        "rechazado": "Gris"
    }).fillna("Otro")
    calendario_df = calendario_df[["fecha", "Evento", "Color"]]
    calendario_df.columns = ["Fecha", "Evento", "Color"]

    with pd.ExcelWriter("vacaciones_export.xlsx") as writer:
        miembros.to_excel(writer, sheet_name="Miembros", index=False)
        solicitudes.to_excel(writer, sheet_name="Solicitudes", index=False)
        calendario_df.to_excel(writer, sheet_name="Calendario", index=False)

    with open("vacaciones_export.xlsx", "rb") as f:
        st.sidebar.download_button("📤 Descargar Excel", f, file_name="vacaciones_export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
