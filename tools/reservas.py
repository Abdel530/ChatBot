from datetime import datetime, timedelta

from database.db import get_connection

POLITICAS = {
    "flexible": {"dias_min": 1, "porcentaje": 0},
    "moderada": {"dias_min": 3, "porcentaje": 50},
    "no_reembolsable": {"dias_min": 999, "porcentaje": 100},
}

MENSAJE_ERROR_DB = (
    "Hubo un problema al consultar nuestros registros. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def _get_db():
    return get_connection()


def buscar_reserva(telefono: str) -> str:
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT r.id, r.check_in, r.check_out, r.politica, r.importe_total, r.estado,
                      h.nombre, hab.numero as habitacion_numero
               FROM reservas r
               JOIN huespedes h ON r.huesped_id = h.id
               JOIN habitaciones hab ON r.habitacion_id = hab.id
               WHERE h.telefono = ? AND r.estado != 'cancelada'
               ORDER BY r.check_in DESC LIMIT 1""",
            (telefono,),
        )
        row = cursor.fetchone()
        conn.close()
    except Exception as e:
        return MENSAJE_ERROR_DB

    if not row:
        return f"No se encontró una reserva activa para el teléfono {telefono}."

    dias_restantes = (datetime.fromisoformat(row["check_in"]) - datetime.now()).days
    return (
        f"Reserva encontrada para {row['nombre']}:\n"
        f"- Habitación: {row['habitacion_numero']}\n"
        f"- Check-in: {row['check_in']} ({dias_restantes} días restantes)\n"
        f"- Check-out: {row['check_out']}\n"
        f"- Política: {row['politica']}\n"
        f"- Importe total: {row['importe_total']:.2f}€\n"
        f"- Estado: {row['estado']}"
    )


def calcular_penalizacion(reserva_id: int) -> str:
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,))
        row = cursor.fetchone()
        conn.close()
    except Exception as e:
        return MENSAJE_ERROR_DB

    if not row:
        return f"No se encontró la reserva con ID {reserva_id}."

    check_in = datetime.fromisoformat(row["check_in"])
    dias_restantes = (check_in - datetime.now()).days
    politica = row["politica"]
    politica_info = POLITICAS.get(politica, {"dias_min": 999, "porcentaje": 100})

    if dias_restantes >= politica_info["dias_min"]:
        return (
            f"Cancelación gratuita para la reserva {reserva_id}.\n"
            f"Días restantes hasta check-in: {dias_restantes} (umbral: {politica_info['dias_min']} días).\n"
            f"Política aplicable: {politica}"
        )

    importe = row["importe_total"] * politica_info["porcentaje"] / 100
    return (
        f"⚠️ Penalización por cancelación - Reserva {reserva_id}:\n"
        f"- Política: {politica}\n"
        f"- Porcentaje: {politica_info['porcentaje']}%\n"
        f"- Importe de la penalización: {importe:.2f}€\n"
        f"- Días restantes hasta check-in: {dias_restantes}\n"
        f"- Importe total de la reserva: {row['importe_total']:.2f}€"
    )


def confirmar_cancelacion(reserva_id: int) -> str:
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT estado FROM reservas WHERE id = ?", (reserva_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"No se encontró la reserva con ID {reserva_id}."

        if row["estado"] == "cancelada":
            conn.close()
            return f"La reserva {reserva_id} ya está cancelada."

        cursor.execute("UPDATE reservas SET estado = 'cancelada' WHERE id = ?", (reserva_id,))
        conn.commit()
        conn.close()
        return f"✅ Reserva {reserva_id} cancelada correctamente."
    except Exception as e:
        return MENSAJE_ERROR_DB


def registrar_llegada(reserva_id: int, hora_llegada: str) -> str:
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT r.*, h.nombre FROM reservas r JOIN huespedes h ON r.huesped_id = h.id WHERE r.id = ?",
            (reserva_id,),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"No se encontró la reserva con ID {reserva_id}."

        cursor.execute(
            "INSERT INTO llegadas (reserva_id, hora_llegada) VALUES (?, ?)",
            (reserva_id, hora_llegada),
        )
        cursor.execute("UPDATE reservas SET hora_llegada = ? WHERE id = ?", (hora_llegada, reserva_id))
        conn.commit()
        conn.close()
        return (
            f"✅ Hora de llegada registrada para la reserva {reserva_id}.\n"
            f"- Hora estimada: {hora_llegada}\n"
            f"- Huésped: {row['nombre']}\n"
            f"- Habitación: {row['habitacion_id']}"
        )
    except Exception as e:
        return MENSAJE_ERROR_DB


def escalar_recepcion(telefono: str, mensaje: str) -> str:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO escalaciones (telefono, mensaje) VALUES (?, ?)",
            (telefono, mensaje),
        )
        conn.commit()
        conn.close()
        return (
            "Un agente de recepción le contactará en breve.\n"
            "Su mensaje ha sido registrado y será atendido lo antes posible."
        )
    except Exception as e:
        return "No fue posible registrar tu solicitud. Inténtalo de nuevo o contacta a recepción directamente."


def get_reserva_by_id(reserva_id: int) -> dict | None:
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        return None
