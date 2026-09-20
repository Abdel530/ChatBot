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


def consultar_costo_habitacion(habitacion_id: int) -> str:
    try:
        client = get_connection()
        result = client.execute("SELECT * FROM habitaciones WHERE id = ?", (habitacion_id,))
        habitacion = _row(result.rows[0]) if result.rows else None
        client.close()
    except Exception:
        return MENSAJE_ERROR_DB

    if not habitacion:
        return MENSAJE_SIN_REGISTROS

    costo = habitacion["costo_operativo_dia"]
    return (
        f"💰 Coste operativo habitación {habitacion['numero']}:\n"
        f"- Tipo: {habitacion['tipo']}\n"
        f"- Costo operativo/día: {costo:.2f}€\n"
        f"- Estado: {habitacion['estado_limpieza']}"
    )
