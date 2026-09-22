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

def registrar_huesped(
    nombre: str,
    apellidos: str,
    cedula: str,
    telefono: str,
    email: str = None,
    nacionalidad: str = None,
) -> int | None:
  """Guarda un nuevo huésped en Turso DB con las columnas reales de la tabla huespedes."""
  conn = get_connection()
  try:
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO huespedes (nombre, apellidos, cedula, telefono, email, nacionalidad)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
        (nombre, apellidos, cedula, telefono, email, nacionalidad),
    )
    conn.commit()

    # Obtener el ID del huésped recién creado
    cursor.execute("SELECT id FROM huespedes WHERE cedula = ?", (cedula,))
    row = cursor.fetchone()
    huesped_id = row[0] if row else None
    conn.close()
    return hueped_id
  except Exception as e:
    conn.close()
    print(f'❌ ERROR AL INSERTAR HUESPED: {e}')
    raise


def registrar_llegada_db(identificador: str) -> str:
  """Registra el Check-in (llegada) de una reserva existente en Turso DB."""
  try:
    conn = get_connection()
    cursor = conn.cursor()
    digitos = "".join(c for c in identificador if c.isdigit())

    row = None
    if len(digitos) >= 7:
      cursor.execute(
          "SELECT r.id FROM reservas r JOIN huespedes h ON r.huesped_id = h.id"
          " WHERE h.telefono = ? AND r.estado != 'cancelada'",
          (digitos,),
      )
      row = cursor.fetchone()
    elif digitos:
      cursor.execute(
          "SELECT id FROM reservas WHERE id = ? AND estado != 'cancelada'",
          (int(digitos),),
      )
      row = cursor.fetchone()

    if not row:
      return MENSAJE_SIN_RESERVA

    reserva_id = row[0] if isinstance(row, tuple) else row["id"]
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO llegadas (reserva_id, hora_llegada) VALUES (?, ?)",
        (reserva_id, hora_actual),
    )
    cursor.execute(
        "UPDATE reservas SET hora_llegada = ? WHERE id = ?",
        (hora_actual, reserva_id),
    )
    conn.commit()

    cursor.execute(
        "SELECT h.nombre, h.apellidos FROM reservas r JOIN huespedes h ON"
        " r.huesped_id = h.id WHERE r.id = ?",
        (reserva_id,),
    )
    nombre_row = cursor.fetchone()
    conn.close()

    if nombre_row:
      nombre = (
          f"{nombre_row[0]} {nombre_row[1]}"
          if isinstance(nombre_row, tuple)
          else f"{nombre_row['nombre']} {nombre_row['apellidos']}"
      )
    else:
      nombre = "Huésped"

    return (
        f"✅ Check-in registrado con éxito.\n"
        f"- Reserva ID: {reserva_id}\n"
        f"- Huésped: {nombre}\n"
        f"- Hora de llegada: {hora_actual}\n"
        f"- Tu registro ha sido guardado en nuestros sistemas."
    )
  except Exception as e:
    conn.close()
    print(f"Error en registrar_llegada_db: {e}")
    return MENSAJE_ERROR_DB
