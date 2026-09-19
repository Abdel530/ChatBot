import sqlite3
from pathlib import Path

from database.db import get_connection

DB_PATH = Path(__file__).parent.parent / "hotel.db"

MENSAJE_SIN_REGISTROS = (
    "No hay servicios registrados en el sistema actualmente."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al consultar nuestros servicios. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def consultar_servicios() -> str:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servicios ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
    except sqlite3.Error:
        return MENSAJE_ERROR_DB
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
