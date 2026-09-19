import sqlite3
from datetime import datetime
from pathlib import Path

from database.db import get_connection

DB_PATH = Path(__file__).parent.parent / "hotel.db"

MENSAJE_SIN_RESERVA = (
    "No se encontró ninguna reserva con ese número o identificador. "
    "Verifica tus datos o selecciona una opción del menú."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al registrar tu llegada. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def registrar_llegada_db(identificador: str) -> str:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        digitos = ''.join(c for c in identificador if c.isdigit())

        if len(digitos) >= 7:
            cursor.execute(
                "SELECT r.id FROM reservas r JOIN huespedes h ON r.huesped_id = h.id WHERE h.telefono = ? AND r.estado != 'cancelada'",
                (digitos,),
            )
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    "SELECT r.id FROM reservas r JOIN huespedes h ON r.huesped_id = h.id WHERE h.telefono = ? AND r.estado != 'cancelada'",
                    (digitos,),
                )
                row = cursor.fetchone()
        else:
            cursor.execute("SELECT id FROM reservas WHERE id = ? AND estado != 'cancelada'", (int(digitos),))
            row = cursor.fetchone()

        if not row:
            conn.close()
            return MENSAJE_SIN_RESERVA

        reserva_id = row["id"]
        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO llegadas (reserva_id, hora_llegada) VALUES (?, ?)",
            (reserva_id, hora_actual),
        )
        cursor.execute(
            "UPDATE reservas SET hora_llegada = ? WHERE id = ?",
            (hora_actual, reserva_id),
        )
        conn.commit()

        cursor.execute("SELECT h.nombre FROM reservas r JOIN huespedes h ON r.huesped_id = h.id WHERE r.id = ?", (reserva_id,))
        nombre_row = cursor.fetchone()
        conn.close()

        nombre = nombre_row["nombre"] if nombre_row else "Huésped"

        return (
            f"✅ Check-in registrado con éxito.\n"
            f"- Reserva ID: {reserva_id}\n"
            f"- Huésped: {nombre}\n"
            f"- Hora de llegada: {hora_actual}\n"
            f"- Tu registro ha sido guardado en nuestros sistemas."
        )
    except sqlite3.Error:
        return MENSAJE_ERROR_DB
    except Exception:
        return MENSAJE_ERROR_DB