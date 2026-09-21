from datetime import datetime

from database.db import get_connection

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
        conn = get_connection()
        cursor = conn.cursor()
        digitos = ''.join(c for c in identificador if c.isdigit())

        if len(digitos) >= 7:
            try:
                id_param = int(digitos)
            except ValueError:
                id_param = -1
            cursor.execute(
                """SELECT r.id, r.check_in, r.check_out, r.politica, r.importe_total, r.estado,
                          r.hora_llegada,
                          h.nombre, h.apellidos, h.cedula, h.telefono,
                          hab.numero as habitacion_numero, hab.tipo as habitacion_tipo
                   FROM reservas r
                   JOIN huespedes h ON r.huesped_id = h.id
                   JOIN habitaciones hab ON r.habitacion_id = hab.id
                   WHERE h.telefono = ? OR h.cedula = ? OR r.id = ?
                   ORDER BY r.check_in DESC""",
                (digitos, digitos, id_param),
            )
        else:
            conn.close()
            return MENSAJE_SIN_REGISTROS

        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        return MENSAJE_ERROR_DB

    if not rows:
        return "No se encontraron registros. Verifica tu número de cédula o teléfono e intenta de nuevo."

    lineas = []
    for row in rows:
        check_in = __parse_date(row["check_in"])
        dias_restantes = (check_in - datetime.now()).days
        nombre_completo = f"{row['nombre']} {row['apellidos']}".strip()
        hora_llegada = row["hora_llegada"] or "No especificada"
        lineas.append(
            f"✅ Reserva #{row['id']}:\n"
            f"- Nombre completo: {nombre_completo}\n"
            f"- Teléfono: {row['telefono']}\n"
            f"- Tipo de habitación: {row['habitacion_tipo']}\n"
            f"- Fechas de estancia: {row['check_in']} al {row['check_out']} ({dias_restantes} días restantes)\n"
            f"- Hora estimada de llegada: {hora_llegada}\n"
            f"- Estado: {row['estado']}"
        )

    return "\n\n".join(lineas)


def __parse_date(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str)
    except Exception as e:
        return datetime.now()
