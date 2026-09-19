import sqlite3
from datetime import datetime
from pathlib import Path

from database.db import get_connection

DB_PATH = Path(__file__).parent.parent / "hotel.db"

MENSAJE_SIN_REGISTROS = (
    "No se encontró ninguna reserva con ese número o teléfono. "
    "Verifica tus datos o selecciona una opción del menú."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al consultar nuestros registros. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def consultar_reserva(identificador: str) -> str:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        digitos = ''.join(c for c in identificador if c.isdigit())

        if len(digitos) >= 7:
            cursor.execute(
                """SELECT r.id, r.check_in, r.check_out, r.politica, r.importe_total, r.estado,
                          h.nombre, h.telefono, hab.numero as habitacion_numero, hab.tipo as habitacion_tipo
                   FROM reservas r
                   JOIN huespedes h ON r.huesped_id = h.id
                   JOIN habitaciones hab ON r.habitacion_id = hab.id
                   WHERE h.telefono = ? OR r.id = ?
                   ORDER BY r.check_in DESC""",
                (digitos, int(digitos)),
            )
        else:
            conn.close()
            return MENSAJE_SIN_REGISTROS

        rows = cursor.fetchall()
        conn.close()
    except sqlite3.Error:
        return MENSAJE_ERROR_DB
    except Exception:
        return MENSAJE_ERROR_DB

    if not rows:
        return MENSAJE_SIN_REGISTROS

    lineas = []
    for row in rows:
        check_in = __parse_date(row["check_in"])
        dias_restantes = (check_in - datetime.now()).days
        lineas.append(
            f"✅ Reserva #{row['id']}:\n"
            f"- Huésped: {row['nombre']} ({row['telefono']})\n"
            f"- Habitación: {row['habitacion_numero']} ({row['habitacion_tipo']})\n"
            f"- Check-in: {row['check_in']} ({dias_restantes} días restantes)\n"
            f"- Check-out: {row['check_out']}\n"
            f"- Política: {row['politica']}\n"
            f"- Importe total: {row['importe_total']:.2f}€\n"
            f"- Estado: {row['estado']}"
        )

    return "\n\n".join(lineas)


def __parse_date(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return datetime.now()