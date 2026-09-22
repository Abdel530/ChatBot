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


def generar_codigo_acceso(habitacion_id: int) -> str:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM habitaciones WHERE id = ?", (habitacion_id,))
        habitacion = cursor.fetchone()

        if not habitacion:
            conn.close()
            return MENSAJE_SIN_REGISTROS

        if habitacion[3] not in ("limpia", "en_proceso"):
            conn.close()
            return (
                f"La habitación {habitacion[1]} no está lista para check-in "
                f"(estado: {habitacion[3]})."
            )

        codigo = str(random.randint(100000, 999999))
        cursor.execute(
            "UPDATE reservas SET codigo_acceso = ? WHERE habitacion_id = ? AND estado != 'cancelada'",
            (codigo, habitacion_id),
        )
        conn.commit()
        conn.close()

        return (
            f"✅ Código de acceso generado para la habitación {habitacion[1]}:\n"
            f"- Código: **{codigo}**\n"
            f"- Guarde este código, será necesario para el check-in."
        )
    except Exception as e:
        return MENSAJE_ERROR_DB


def get_codigo_acceso(habitacion_id: int) -> str | None:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT codigo_acceso FROM reservas WHERE habitacion_id = ? AND estado != 'cancelada'",
            (habitacion_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return row[0]
        return None
    except Exception as e:
        return None
