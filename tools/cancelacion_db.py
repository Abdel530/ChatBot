from database.db import get_connection

MENSAJE_SIN_RESERVA = (
    "No se encontró ninguna reserva con ese número o identificador. "
    "Verifica tus datos o selecciona una opción del menú."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al cancelar la reserva. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def cancelar_reserva_db(identificador: str) -> str:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        digitos = ''.join(c for c in identificador if c.isdigit())

        if len(digitos) >= 7:
            cursor.execute(
                "SELECT r.id, r.estado FROM reservas r JOIN huespedes h ON r.huesped_id = h.id WHERE h.telefono = ?",
                (digitos,),
            )
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    "SELECT r.id, r.estado FROM reservas r JOIN huespedes h ON r.huesped_id = h.id WHERE h.telefono = ? AND r.estado != 'cancelada'",
                    (digitos,),
                )
                row = cursor.fetchone()
        else:
            cursor.execute("SELECT id, estado FROM reservas WHERE id = ?", (int(digitos),))
            row = cursor.fetchone()

        if not row:
            conn.close()
            return MENSAJE_SIN_RESERVA

        reserva_id = row[0]
        estado = row[1]

        if estado == "cancelada":
            conn.close()
            return f"La reserva {reserva_id} ya está cancelada."

        cursor.execute("UPDATE reservas SET estado = 'cancelada' WHERE id = ?", (reserva_id,))
        conn.commit()
        conn.close()

        return (
            f"✅ Reserva {reserva_id} cancelada correctamente.\n"
            f"- Estado actualizado a: CANCELADA\n"
            f"- Si necesitas reprogramar, contacta a recepción."
        )
    except Exception as e:
        return MENSAJE_ERROR_DB
