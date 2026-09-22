from database.db import get_connection

MENSAJE_SIN_REGISTROS = (
    "No se encontró la habitación con los datos ingresados. "
    "Verifica el número de habitación o selecciona una opción del menú."
)
MENSAJE_ERROR_DB = (
    "Hubo un problema al consultar nuestros registros. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def consultar_costo_habitacion(habitacion_id: int) -> str:
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

    costo = habitacion[4]
    return (
        f"💰 Coste operativo habitación {habitacion[1]}:\n"
        f"- Tipo: {habitacion[2]}\n"
        f"- Costo operativo/día: {costo:.2f}€\n"
        f"- Estado: {habitacion[3]}"
    )
