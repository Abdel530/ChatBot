from database.db import get_connection

MENSAJE_SIN_REGISTROS = (
    "No hay servicios registrados en el sistema actualmente."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al consultar nuestros servicios. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def _row(row):
    return row.asdict() if row else None


def consultar_servicios() -> str:
    try:
        client = get_connection()
        result = client.execute("SELECT * FROM servicios ORDER BY id")
        rows = [_row(r) for r in result.rows]
        client.close()
    except Exception:
        return MENSAJE_ERROR_DB

    if not rows:
        return MENSAJE_SIN_REGISTROS

    lineas = ["🎟️ **Servicios del Hotel Paraíso:**\n"]
    for i, servicio in enumerate(rows, 1):
        nombre = servicio["nombre"]
        descripcion = servicio["descripcion"]
        horario = servicio["horario"]
        ubicacion = servicio["ubicacion"]
        linea = f"{i}. *{nombre}* ({horario})\n   {descripcion}"
        if ubicacion:
            linea += f"\n   📍 {ubicacion}"
        lineas.append(linea)

    return "\n".join(lineas)
