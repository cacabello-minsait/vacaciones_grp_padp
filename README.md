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


✅ Descripción funcional detallada
Esta sección describe el comportamiento esperado de cada funcionalidad de la app de gestión de vacaciones y días de libre disposición desarrollada en Streamlit.

🧍 1. Gestión de miembros
Alta de miembros:

Se pueden añadir miembros con los siguientes campos:

Nombre

Rol (Funcional, Implantación, Integración)

Vacaciones disponibles (número entero)

Horas de libre disposición disponibles (número entero)

Edición:

Permite modificar directamente las celdas de la tabla de miembros.

Eliminación:

Cada fila tiene un botón para eliminar un miembro.

📝 2. Solicitudes
Creación:

Cada miembro puede solicitar un día para:

Vacaciones (V)

Libre disposición (L)

La solicitud se realiza seleccionando:

Nombre del miembro

Fecha única

Tipo de solicitud

Validaciones automáticas:

Se impide solicitar si:

El miembro no tiene suficientes días/horas disponibles.

El formato de la fecha es inválido.

Control de tipo:

Si es vacación (V): descuenta 1 día.

Si es libre disposición (L): descuenta 1 hora.

📅 3. Calendario visual (streamlit-calendar)
Se muestra el calendario completo con:

Solicitudes marcadas por color:

Verde: Aprobadas

Azul: Pendientes

Gris: Rechazadas

Rojo: Solapamientos

Amarillo: Fines de semana y festivos (FS, FR, FN)

Solicitudes desde calendario:

Se puede seleccionar un día para solicitar V o L directamente desde la vista del calendario.

Festivos:

Se pueden añadir fines de semana y festivos nacionales/regionales.

🔴 4. Solapamientos
Detección automática de solapamientos:

Se marcan en rojo cuando más de un miembro con el mismo rol tiene una solicitud el mismo día.

📋 5. Listado de solicitudes
Muestra todas las solicitudes en tabla editable.

Cada fila permite:

Aprobar (✔️)

Rechazar (❌)

Eliminar (🗑️)

Al aprobar:

Se descuenta el día/hora correspondiente del miembro.

Al eliminar:

No se descuenta ningún valor.

📤 6. Exportación a Excel
El botón "Exportar a Excel" genera un archivo .xlsx con tres hojas:

Miembros: listado completo y actualizado de miembros.

Solicitudes: todas las solicitudes realizadas y su estado.

Calendario visual: vista diaria por tipo y color.

👨‍🏫 Manual de usuario sencillo
Este manual está dirigido a usuarios que utilizarán la aplicación, incluyendo jefes de proyecto, implantadores, funcionales e integradores.

🔓 Iniciar la app
Abre un terminal y ejecuta:

bash
Copiar
Editar
streamlit run app.py
Se abrirá en tu navegador una app web.

🧍 Pestaña "Miembros"
Añade un miembro:

Escribe el nombre.

Selecciona el rol.

Define vacaciones y horas de libre disposición.

Pulsa "Añadir".

Edita los datos haciendo clic directamente en la tabla.

Elimina con el icono 🗑️.

📅 Pestaña "Calendario"
Revisa el calendario completo.

Colores:

🟩 Aprobado

🟦 Pendiente

🟥 Solapado

⚫ Rechazado

🟨 Festivo / fin de semana

Para solicitar:

Selecciona nombre, fecha y tipo (V o L) en la parte inferior.

Pulsa "Solicitar".

Para añadir festivos:

Usa los botones para añadir FS, FR o FN.

🔁 Pestaña "Solapamientos" / "Listado de solicitudes"
Verás una tabla con todas las solicitudes.

Puedes:

Aprobar (✔️)

Rechazar (❌)

Eliminar (🗑️)

📤 Exportar a Excel
Haz clic en "Exportar a Excel" en cualquier pestaña.

Se descargará un archivo con los datos actualizados.

✅ Reglas importantes
Solo puedes solicitar si tienes días/horas disponibles.

No puedes repetir una solicitud para la misma fecha y tipo.

El sistema detecta automáticamente si hay solapamientos por rol.

