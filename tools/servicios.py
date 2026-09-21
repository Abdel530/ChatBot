from database.db import get_connection

MENSAJE_SIN_REGISTROS = (
    "No hay servicios registrados en el sistema actualmente."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al consultar nuestros servicios. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def consultar_servicios() -> str:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servicios ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        return MENSAJE_ERROR_DB

    if not rows:
        return MENSAJE_SIN_REGISTROS

    lineas = ["🎟️ **Servicios del Hotel Paraíso:**\n"]
    for i, servicio in enumerate(rows, 1):
        nombre = servicio[1]
        descripcion = servicio[2]
        horario = servicio[3]
        ubicacion = servicio[4]
        linea = f"{i}. *{nombre}* ({horario})\n   {descripcion}"
        if ubicacion:
            linea += f"\n   📍 {ubicacion}"
        lineas.append(linea)

    return "\n".join(lineas)
