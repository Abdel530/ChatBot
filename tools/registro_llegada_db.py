from datetime import datetime

from database.db import get_connection

MENSAJE_SIN_RESERVA = (
    "No se encontró ninguna reserva con ese número o identificador. "
    "Verifica tus datos o selecciona una opción del menú."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al registrar tu llegada. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def _row(row):
    return row.asdict() if row else None


def registrar_llegada_db(identificador: str) -> str:
    try:
        client = get_connection()
        digitos = ''.join(c for c in identificador if c.isdigit())

        if len(digitos) >= 7:
            result = client.execute(
                "SELECT r.id FROM reservas r JOIN huespedes h ON r.huesped_id = h.id WHERE h.telefono = ? AND r.estado != 'cancelada'",
                (digitos,),
            )
            row = _row(result.rows[0]) if result.rows else None
            if not row:
                result = client.execute(
                    "SELECT r.id FROM reservas r JOIN huespedes h ON r.huesped_id = h.id WHERE h.telefono = ? AND r.estado != 'cancelada'",
                    (digitos,),
                )
                row = _row(result.rows[0]) if result.rows else None
        else:
            result = client.execute("SELECT id FROM reservas WHERE id = ? AND estado != 'cancelada'", (int(digitos),))
            row = _row(result.rows[0]) if result.rows else None

        if not row:
            client.close()
            return MENSAJE_SIN_RESERVA

        reserva_id = row["id"]
        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        client.execute("INSERT INTO llegadas (reserva_id, hora_llegada) VALUES (?, ?)", (reserva_id, hora_actual))
        client.execute("UPDATE reservas SET hora_llegada = ? WHERE id = ?", (hora_actual, reserva_id))

        result = client.execute("SELECT h.nombre FROM reservas r JOIN huespedes h ON r.huesped_id = h.id WHERE r.id = ?", (reserva_id,))
        nombre_row = _row(result.rows[0]) if result.rows else None
        client.close()

        nombre = nombre_row["nombre"] if nombre_row else "Huésped"

        return (
            f"✅ Check-in registrado con éxito.\n"
            f"- Reserva ID: {reserva_id}\n"
            f"- Huésped: {nombre}\n"
            f"- Hora de llegada: {hora_actual}\n"
            f"- Tu registro ha sido guardado en nuestros sistemas."
        )
    except Exception:
        return MENSAJE_ERROR_DB
