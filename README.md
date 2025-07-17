# 🗓️ App de Gestión de Vacaciones y Días de Libre Disposición

Esta es una aplicación web desarrollada en [Streamlit](https://streamlit.io) que permite gestionar las vacaciones y días libres de los miembros de un equipo, incluyendo detección de solapamientos y control por tipo de miembro (rol).

---

## 🚀 Características

- 🧍 **Gestión de miembros**: añade, edita o elimina miembros del equipo con sus días disponibles.
- 📅 **Solicitudes**: los miembros pueden solicitar vacaciones (V) o libre disposición (L), con validación automática.
- ✅ **Control de disponibilidad**: la app impide solicitudes si no hay días/horas suficientes.
- 🔄 **Descuento automático** al aprobar solicitudes.
- ❗ **Detección de solapamientos** entre solicitudes del mismo rol.
- 🌈 **Calendario visual codificado por colores**, con soporte para:
  - Solicitudes aprobadas (verde)
  - Pendientes (azul)
  - Rechazadas (gris)
  - Solapamientos (rojo)
  - Fines de semana y festivos (amarillo)
- 📤 **Exportación a Excel** con tres hojas:
  - `Miembros`
  - `Solicitudes`
  - `Calendario visual`

---

## 🧱 Estructura

- `app.py`: contiene toda la lógica y la interfaz Streamlit. No requiere archivo `utils.py`.
- No se requiere base de datos. La información se guarda en `st.session_state`.

---

## 🖥️ Requisitos

- Python 3.9 o superior
- Paquetes necesarios:

```bash
pip install streamlit pandas streamlit-calendar openpyxl
