import random
import sqlite3
from pathlib import Path

from database.db import get_connection

DB_PATH = Path(__file__).parent.parent / "hotel.db"


def generar_codigo_acceso(habitacion_id: int) -> str:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM habitaciones WHERE id = ?", (habitacion_id,))
    habitacion = cursor.fetchone()

    if not habitacion:
        conn.close()
        return f"No se encontró la habitación con ID {habitacion_id}."

    if habitacion["estado_limpieza"] not in ("limpia", "en_proceso"):
        conn.close()
        return (
            f"La habitación {habitacion['numero']} no está lista para check-in "
            f"(estado: {habitacion['estado_limpieza']})."
        )

    codigo = str(random.randint(100000, 999999))
    cursor.execute(
        "UPDATE reservas SET codigo_acceso = ? WHERE habitacion_id = ? AND estado != 'cancelada'",
        (codigo, habitacion_id),
    )
    conn.commit()
    conn.close()

    return (
        f"✅ Código de acceso generado para la habitación {habitacion['numero']}:\n"
        f"- Código: **{codigo}**\n"
        f"- Guarde este código, será necesario para el check-in."
    )


def get_codigo_acceso(habitacion_id: int) -> str | None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT codigo_acceso FROM reservas WHERE habitacion_id = ? AND estado != 'cancelada'",
        (habitacion_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row and row["codigo_acceso"]:
        return row["codigo_acceso"]
    return None