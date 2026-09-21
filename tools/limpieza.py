from database.db import get_connection

HORARIOS_LIMPIEZA = {
    "limpia": "La habitación está limpia y lista para check-in.",
    "sucia": "La habitación necesita limpieza. Se asignará personal en las próximas 2 horas.",
    "en_proceso": "La habitación está en proceso de limpieza. Estará lista en ~30 minutos.",
    "mantenimiento": "La habitación está en mantenimiento. Consulte recepción para alternativas.",
}

MENSAJE_SIN_REGISTROS = (
    "No se encontró la habitación con los datos ingresados. "
    "Verifica el número de habitación o selecciona una opción del menú."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al consultar nuestros registros. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def consultar_limpieza(habitacion_id: int) -> str:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM habitaciones WHERE id = ?", (habitacion_id,))
        habitacion = cursor.fetchone()
        conn.close()
    except Exception as e:
        return MENSAJE_ERROR_DB

    if not habitacion:
        return MENSAJE_SIN_REGISTROS

    estado = habitacion["estado_limpieza"]
    mensaje_base = HORARIOS_LIMPIEZA.get(estado, f"Estado actual: {estado}")

    return (
        f"🏨 Habitación {habitacion['numero']} ({habitacion['tipo']}):\n"
        f"- Estado de limpieza: {estado}\n"
        f"- {mensaje_base}"
    )


def actualizar_estado_limpieza(habitacion_id: int, nuevo_estado: str) -> str:
    validos = {"limpia", "sucia", "en_proceso", "mantenimiento"}
    if nuevo_estado not in validos:
        return f"Estado inválido. Usa uno de: {', '.join(validos)}"

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE habitaciones SET estado_limpieza = ? WHERE id = ?",
            (nuevo_estado, habitacion_id),
        )
        conn.commit()
        conn.close()
        return f"Estado de limpieza de la habitación {habitacion_id} actualizado a '{nuevo_estado}'."
    except Exception as e:
        return MENSAJE_ERROR_DB
