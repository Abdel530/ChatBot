import re
from datetime import datetime

from database.db import get_connection

TIPO_CATEGORIAS = {
    "Sencilla": "Sencilla",
    "Doble": "Doble",
    "Triple": "Triple",
    "Cuádruple": "Cuádruple",
    "Suite": "Suite",
}

PRECIO_MAP = {
    "Sencilla": 150.0,
    "Doble": 250.0,
    "Triple": 350.0,
    "Cuádruple": 450.0,
    "Suite": 600.0,
}

HORA_PATTERN = re.compile(r"^(\d|[01]\d|2[0-3]):([0-5][0-9])\s*([AP]M|[ap]m)$")

MENSAJE_ERROR_DB = (
    "Hubo un problema al consultar la disponibilidad. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def parsear_fechas(fecha_str: str) -> tuple:
    texto_limpio = fecha_str.replace("--", " ").replace("  ", " ")
    partes = texto_limpio.strip().split()
    if len(partes) != 2:
        raise ValueError(
            f"Formato de fechas inválido: '{fecha_str}'. Usa el formato YYYY-MM-DD -- YYYY-MM-DD."
        )
    check_in = partes[0]
    check_out = partes[1]
    return check_in, check_out


def validar_hora_12h(hora_str: str) -> str:
    match = HORA_PATTERN.match(hora_str.strip())
    if not match:
        raise ValueError(
            f"Formato de hora inválido: '{hora_str}'. Usa formato 12h: 8:30 PM, 02:30 PM o 10:00 AM."
        )
    return hora_str.strip()


def consultar_disponibilidad(fecha_entrada: str, fecha_salida: str = None) -> str:
  try:
    if fecha_salida is None:
      # Limpiamos guiones dobles y espacios extras
      texto_limpio = fecha_entrada.replace("--", " ").replace("  ", " ").strip()
      if " " in texto_limpio:
        check_in, check_out = texto_limpio.split(maxsplit=1)
      else:
        check_in, check_out = parsear_fechas(fecha_entrada)
    else:
      check_in = fecha_entrada
      check_out = fecha_salida or ""

    __validar_fechas(check_in, check_out)
  except ValueError as e:
    return str(e)
  except Exception as e:
    print(f"Error en validación de fechas: {e}")
    return MENSAJE_ERROR_DB

  try:
    conn = get_connection()
    cursor = conn.cursor()

    # Query 1: Obtener habitaciones
    cursor.execute(
        "SELECT id, tipo, numero FROM habitaciones WHERE estado_limpieza IN"
        " ('limpia', 'en_proceso') ORDER BY tipo"
    )
    habitaciones_raw = cursor.fetchall()

    # Query 2: Obtener reservas activas
    cursor.execute(
        "SELECT habitacion_id FROM reservas WHERE estado = 'confirmada' AND"
        " check_out > ? AND check_in < ?",
        (check_in, check_out),
    )
    reservas_raw = cursor.fetchall()
    conn.close()

    # Mapeo usando índices numéricos de tupla
    # habitaciones_raw -> row[0]=id, row[1]=tipo, row[2]=numero
    reservas_activas = [row[0] for row in reservas_raw]
    habitaciones_libres = [h for h in habitaciones_raw if h[0] not in reservas_activas]

    conteo = {}
    for h in habitaciones_libres:
      tipo = h[1]  # Índice 1 corresponde a 'tipo'
      categoria = TIPO_CATEGORIAS.get(tipo, tipo)
      conteo[categoria] = conteo.get(categoria, 0) + 1

  except Exception as e:
    print(f"Error en consulta DB de disponibilidad: {e}")
    return MENSAJE_ERROR_DB

  tipos_ordenados = ["Sencilla", "Doble", "Triple", "Cuádruple", "Suite"]
  lineas = ["🏨 **Disponibilidad de habitaciones:**\n"]
  hay_disponibilidad = False

  for tipo in tipos_ordenados:
    if tipo in conteo:
      lineas.append(f"• {conteo[tipo]} Habitaciones {tipo.lower()}")
      hay_disponibilidad = True
    else:
      lineas.append(f"• 0 Habitaciones {tipo.lower()} (Agotado)")

  if not hay_disponibilidad or all(v == 0 for v in conteo.values()):
    return (
        "Lo sentimos, no hay habitaciones disponibles para esas fechas. Por"
        " favor intenta con otro rango de fechas."
    )

  return "\n".join(lineas)

def upsert_huesped(huesped_id: int, nombre: str = None, apellidos: str = None,
                    cedula: str = None, nacionalidad: str = None,
                    email: str = None, telefono: str = None) -> int:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM huespedes WHERE id = ?", (huesped_id,))
        existing = cursor.fetchone()
        if existing:
            set_clauses = []
            params = []
            if nombre is not None:
                set_clauses.append("nombre = ?")
                params.append(nombre)
            if apellidos is not None:
                set_clauses.append("apellidos = ?")
                params.append(apellidos)
            if cedula is not None:
                set_clauses.append("cedula = ?")
                params.append(cedula)
            if nacionalidad is not None:
                set_clauses.append("nacionalidad = ?")
                params.append(nacionalidad)
            if email is not None:
                set_clauses.append("email = ?")
                params.append(email)
            if telefono is not None:
                set_clauses.append("telefono = ?")
                params.append(telefono)
            if set_clauses:
                params.append(huesped_id)
                cursor.execute(
                    f"UPDATE huespedes SET {', '.join(set_clauses)} WHERE id = ?",
                    params,
                )
        else:
            cursor.execute(
                "INSERT INTO huespedes (id, nombre, apellidos, cedula, nacionalidad, email, telefono) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (huesped_id, nombre or f"Huésped_{huesped_id}", apellidos or "", cedula or "", nacionalidad or "", email or "", telefono or ""),
            )
        conn.commit()
        conn.close()
        return huesped_id
    except Exception as e:
        print(f'Error al insertar en huespedes: {e}')
        raise


def obtener_habitacion_disponible(tipo_habitacion: str, check_in: str, check_out: str) -> int | None:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id FROM habitaciones 
            WHERE LOWER(tipo) LIKE LOWER(?) 
              AND id NOT IN (
                  SELECT habitacion_id FROM reservas 
                  WHERE LOWER(estado) = 'confirmada' 
                    AND check_out > ? 
                    AND check_in < ?
              ) 
            LIMIT 1
        """
        cursor.execute(query, (f"%{tipo_habitacion.strip()}%", check_in, check_out))
        row = cursor.fetchone()
        conn.close()

        if row:
            return row["id"]
        return None
    except Exception as e:
        print(f"❌ Error en obtener_habitacion_disponible: {e}", flush=True)
        return None


def registrar_reserva(huesped_id: int, tipo_habitacion: str, check_in: str, check_out: str,
                       politica: str, importe_total: float,
                       nombre: str = None, apellidos: str = None, cedula: str = None,
                       nacionalidad: str = None, email: str = None, telefono: str = None) -> str:
    try:
        habitacion_id = obtener_habitacion_disponible(tipo_habitacion, check_in, check_out)
        if not habitacion_id:
            return "Lo sentimos, no hay habitaciones disponibles para ese tipo en esas fechas."

        conn = get_connection()
        cursor = conn.cursor()

        if nombre or apellidos or cedula or nacionalidad or email or telefono:
            cursor.execute("SELECT id FROM huespedes WHERE id = ?", (huesped_id,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE huespedes SET nombre=?, apellidos=?, cedula=?, nacionalidad=?, email=?, telefono=? WHERE id=?",
                    (nombre, apellidos, cedula, nacionalidad, email, telefono, huesped_id),
                )
            else:
                cursor.execute(
                    "INSERT INTO huespedes (id, nombre, apellidos, cedula, nacionalidad, email, telefono) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (huesped_id, nombre or f"Huésped_{huesped_id}", apellidos or "", cedula or "", nacionalidad or "", email or "", telefono or ""),
                )

        cursor.execute(
            "INSERT INTO reservas (huesped_id, habitacion_id, check_in, check_out, estado, importe_total) VALUES (?, ?, ?, ?, ?, ?)",
            (huesped_id, habitacion_id, check_in, check_out, 'CONFIRMADA', float(importe_total) if importe_total else 0.0)
        )

        reserva_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return (
            f"✅ ¡Reserva confirmada!\n"
            f"- ID de reserva: #{reserva_id}\n"
            f"- Habitación: {habitacion_id} ({tipo_habitacion})\n"
            f"- Check-in: {check_in}\n"
            f"- Check-out: {check_out}\n"
            f"- Estado: CONFIRMADA\n"
            f"- Recibirás un código de acceso en tu check-in."
        )
    except Exception as e:
        print(f'Error al insertar en huespedes: {e}')
        raise


def __validar_fechas(fecha_entrada: str, fecha_salida: str) -> None:
    if fecha_salida <= fecha_entrada:
        raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada.")
    from datetime import datetime as dt
    if dt.fromisoformat(fecha_entrada) < dt.now():
        raise ValueError("La fecha de entrada debe ser una fecha futura.")


def listar_tipos_habitaciones() -> str:
    return "📅 **Tipos de habitación disponibles:**\n• Sencilla\n• Doble\n• Triple\n• Cuádruple\n• Suite\n\nEnvíame tus fechas en formato YYYY-MM-DD -- YYYY-MM-DD.\nEjemplo: 2026-09-25 -- 2026-10-25"
