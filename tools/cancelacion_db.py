from database.db import get_connection

MENSAJE_SIN_RESERVA = (
    "No se encontró ninguna reserva con ese número o identificador. "
    "Verifica tus datos o selecciona una opción del menú."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al cancelar la reserva. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def _row(row):
    return row.asdict() if row else None


def cancelar_reserva_db(identificador: str) -> str:
    try:
        client = get_connection()
        digitos = ''.join(c for c in identificador if c.isdigit())

        if len(digitos) >= 7:
            result = client.execute(
                "SELECT r.id, r.estado FROM reservas r JOIN huespedes h ON r.huesped_id = h.id WHERE h.telefono = ?",
                (digitos,),
            )
            row = _row(result.rows[0]) if result.rows else None
            if not row:
                result = client.execute(
                    "SELECT r.id, r.estado FROM reservas r JOIN huespedes h ON r.huesped_id = h.id WHERE h.telefono = ? AND r.estado != 'cancelada'",
                    (digitos,),
                )
                row = _row(result.rows[0]) if result.rows else None
        else:
            result = client.execute("SELECT id, estado FROM reservas WHERE id = ?", (int(digitos),))
            row = _row(result.rows[0]) if result.rows else None

        if not row:
            client.close()
            return MENSAJE_SIN_RESERVA

        reserva_id = row["id"]
        estado = row["estado"]

        if estado == "cancelada":
            client.close()
            return f"La reserva {reserva_id} ya está cancelada."

        client.execute("UPDATE reservas SET estado = 'cancelada' WHERE id = ?", (reserva_id,))
        client.close()

        return (
            f"✅ Reserva {reserva_id} cancelada correctamente.\n"
            f"- Estado actualizado a: CANCELADA\n"
            f"- Si necesitas reprogramar, contacta a recepción."
        )
    except Exception:
        return MENSAJE_ERROR_DB
