import sqlite3
from pathlib import Path

from database.db import get_connection

DB_PATH = Path(__file__).parent.parent / "hotel.db"


def consultar_costo_habitacion(habitacion_id: int) -> str:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM habitaciones WHERE id = ?", (habitacion_id,))
    habitacion = cursor.fetchone()
    conn.close()

    if not habitacion:
        return f"No se encontró la habitación con ID {habitacion_id}."

    costo = habitacion["costo_operativo_dia"]
    return (
        f"💰 Coste operativo habitación {habitacion['numero']}:\n"
        f"- Tipo: {habitacion['tipo']}\n"
        f"- Costo operativo/día: {costo:.2f}€\n"
        f"- Estado: {habitacion['estado_limpieza']}"
    )