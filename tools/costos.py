import sqlite3
from pathlib import Path

from database.db import get_connection

DB_PATH = Path(__file__).parent.parent / "hotel.db"

MENSAJE_SIN_REGISTROS = (
    "No se encontró la habitación con los datos ingresados. "
    "Verifica el número de habitación o selecciona una opción del menú."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al consultar nuestros registros. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def consultar_costo_habitacion(habitacion_id: int) -> str:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM habitaciones WHERE id = ?", (habitacion_id,))
        habitacion = cursor.fetchone()
        conn.close()
    except sqlite3.Error:
        return MENSAJE_ERROR_DB
    except Exception:
        return MENSAJE_ERROR_DB

    if not habitacion:
        return MENSAJE_SIN_REGISTROS

    costo = habitacion["costo_operativo_dia"]
    return (
        f"💰 Coste operativo habitación {habitacion['numero']}:\n"
        f"- Tipo: {habitacion['tipo']}\n"
        f"- Costo operativo/día: {costo:.2f}€\n"
        f"- Estado: {habitacion['estado_limpieza']}"
    )