import random

from database.db import get_connection

MENSAJE_SIN_REGISTROS = (
    "No se encontró la habitación con los datos ingresados. "
    "Verifica el número de habitación o selecciona una opción del menú."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al consultar nuestros registros. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def _row(row):
    return row.asdict() if row else None


def generar_codigo_acceso(habitacion_id: int) -> str:
    try:
        client = get_connection()
        result = client.execute("SELECT * FROM habitaciones WHERE id = ?", (habitacion_id,))
        habitacion = _row(result.rows[0]) if result.rows else None

        if not habitacion:
            client.close()
            return MENSAJE_SIN_REGISTROS

        if habitacion["estado_limpieza"] not in ("limpia", "en_proceso"):
            client.close()
            return (
                f"La habitación {habitacion['numero']} no está lista para check-in "
                f"(estado: {habitacion['estado_limpieza']})."
            )

        codigo = str(random.randint(100000, 999999))
        client.execute(
            "UPDATE reservas SET codigo_acceso = ? WHERE habitacion_id = ? AND estado != 'cancelada'",
            (codigo, habitacion_id),
        )
        client.close()

        return (
            f"✅ Código de acceso generado para la habitación {habitacion['numero']}:\n"
            f"- Código: **{codigo}**\n"
            f"- Guarde este código, será necesario para el check-in."
        )
    except Exception:
        return MENSAJE_ERROR_DB


def get_codigo_acceso(habitacion_id: int) -> str | None:
    try:
        client = get_connection()
        result = client.execute(
            "SELECT codigo_acceso FROM reservas WHERE habitacion_id = ? AND estado != 'cancelada'",
            (habitacion_id,),
        )
        row = _row(result.rows[0]) if result.rows else None
        client.close()
        if row and row.get("codigo_acceso"):
            return row["codigo_acceso"]
        return None
    except Exception:
        return None
