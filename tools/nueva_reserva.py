import sqlite3
import re
from datetime import datetime
from pathlib import Path

from database.db import get_connection

DB_PATH = Path(__file__).parent.parent / "hotel.db"

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


def ddmmyyyy_to_yyyymmdd(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Formato de fecha inválido: '{date_str}'. Usa YYYY-MM-DD (ejemplo: 2026-09-25).")


def validar_hora_12h(hora_str: str) -> str:
    match = HORA_PATTERN.match(hora_str.strip())
    if not match:
        raise ValueError(
            f"Formato de hora inválido: '{hora_str}'. Usa formato 12h: 8:30 PM, 02:30 PM o 10:00 AM."
        )
    return hora_str.strip()


def consultar_disponibilidad(fecha_entrada: str, fecha_salida: str) -> str:
    try:
        check_in = fecha_entrada
        check_out = fecha_salida
        __validar_fechas(check_in, check_out)
    except ValueError as e:
        return str(e)
    except Exception:
        return MENSAJE_ERROR_DB

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, tipo, numero FROM habitaciones WHERE estado_limpieza IN ('limpia', 'en_proceso') ORDER BY tipo"
        )
        habitaciones = cursor.fetchall()
        cursor.execute(
            "SELECT habitacion_id FROM reservas WHERE estado = 'confirmada' AND check_out > ? AND check_in < ?",
            (check_in, check_out),
        )
        reservas_activas = [row["habitacion_id"] for row in cursor.fetchall()]
        conn.close()
    except sqlite3.Error:
        return MENSAJE_ERROR_DB
    except Exception:
        return MENSAJE_ERROR_DB

    habitaciones_libres = [h for h in habitaciones if h["id"] not in reservas_activas]
    conteo = {}
    for h in habitaciones_libres:
        tipo = h["tipo"]
        categoria = TIPO_CATEGORIAS.get(tipo, tipo)
        conteo[categoria] = conteo.get(categoria, 0) + 1

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
        return "Lo sentimos, no hay habitaciones disponibles para esas fechas. Por favor intenta con otro rango de fechas."
    return "\n".join(lineas)


def upsert_huesped(huesped_id: int, nombre: str = None, apellidos: str = None,
                    cedula: str = None, nacionalidad: str = None,
                    email: str = None, telefono: str = None) -> int:
    try:
        conn = sqlite3.connect(str(DB_PATH))
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
    except sqlite3.Error:
        return None
    except Exception:
        return None


def obtener_habitacion_disponible(tipo_habitacion: str, check_in: str, check_out: str) -> int | None:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Consulta simplificada: busca por tipo y descarta habitaciones ocupadas en esas fechas
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
                      politica: str, importe_total: float, hora_llegada: str = None,
                      nombre: str = None, apellidos: str = None, cedula: str = None,
                      nacionalidad: str = None, email: str = None, telefono: str = None) -> str:
    try:
        habitacion_id = obtener_habitacion_disponible(tipo_habitacion, check_in, check_out)
        if not habitacion_id:
            return "Lo sentimos, no hay habitaciones disponibles para ese tipo en esas fechas."

        conn = sqlite3.connect(str(DB_PATH))
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

       # INSERT CORREGIDO SIN 'hora_llegada' EN RESERVAS
        cursor.execute(
            """
            INSERT INTO reservas (
                huesped_id, habitacion_id, check_in, check_out, politica, estado, importe_total
            ) VALUES (?, ?, ?, ?, ?, 'CONFIRMADA', ?)
            """,
            (huesped_id, habitacion_id, check_in, check_out, politica or "Estándar", float(importe_total) if importe_total else 0.0)
        )
        
        # 1. Capturar el ID de la reserva inmediatamente
        reserva_id = cursor.lastrowid

        # 2. Guardar la hora en la tabla 'llegadas'
        if hora_llegada:
            cursor.execute(
                "INSERT INTO llegadas (reserva_id, hora_llegada) VALUES (?, ?)",
                (reserva_id, hora_llegada)
            )

        # 3. Hacer un solo commit final
        conn.commit()

        conn.close()

        return (
            f"✅ ¡Reserva confirmada!\n"
            f"- ID de reserva: #{reserva_id}\n"
            f"- Habitación: {habitacion_id} ({tipo_habitacion})\n"
            f"- Check-in: {check_in}\n"
            f"- Check-out: {check_out}\n"
            f"- Estado: CONFIRMADA\n"
            f"- Hora de llegada: {hora_llegada or 'No especificada'}\n"
            f"- Recibirás un código de acceso en tu check-in."
        )
    except sqlite3.Error:
        return MENSAJE_ERROR_DB
    except Exception:
        return MENSAJE_ERROR_DB


def registrar_reserva(huesped_id: int, tipo_habitacion: str, check_in: str, check_out: str,
                         politica: str, importe_total: float, hora_llegada: str = None,
                         nombre: str = None, apellidos: str = None, cedula: str = None,
                         nacionalidad: str = None, email: str = None, telefono: str = None) -> str:
    try:
        habitacion_id = obtener_habitacion_disponible(tipo_habitacion, check_in, check_out)
        if not habitacion_id:
            return "Lo sentimos, no hay habitaciones disponibles para ese tipo en esas fechas."

        conn = sqlite3.connect(str(DB_PATH))
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
            "INSERT INTO reservas (huesped_id, habitacion_id, check_in, check_out, politica, estado, importe_total, hora_llegada) VALUES (?, ?, ?, ?, ?, 'CONFIRMADA', ?, ?)",
            (huesped_id, habitacion_id, check_in, check_out, importe_total, hora_llegada or ""),
        )
        conn.commit()
        reserva_id = cursor.lastrowid

        if hora_llegada:
            cursor.execute(
                "INSERT INTO llegadas (reserva_id, hora_llegada) VALUES (?, ?)",
                (reserva_id, hora_llegada),
            )
            cursor.execute(
                "UPDATE reservas SET hora_llegada = ? WHERE id = ?",
                (hora_llegada, reserva_id),
            )
            conn.commit()

        conn.close()

        return (
            f"✅ ¡Reserva confirmada!\n"
            f"- ID de reserva: #{reserva_id}\n"
            f"- Habitación: {habitacion_id} ({tipo_habitacion})\n"
            f"- Check-in: {check_in}\n"
            f"- Check-out: {check_out}\n"
            f"- Estado: CONFIRMADA\n"
            f"- Hora de llegada: {hora_llegada or 'No especificada'}\n"
            f"- Recibirás un código de acceso en tu check-in."
        )
    except sqlite3.Error:
        return MENSAJE_ERROR_DB
    except Exception:
        return MENSAJE_ERROR_DB


def __validar_fechas(fecha_entrada: str, fecha_salida: str) -> None:
    if fecha_salida <= fecha_entrada:
        raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada.")
    from datetime import datetime as dt
    if dt.fromisoformat(fecha_entrada) < dt.now():
        raise ValueError("La fecha de entrada debe ser una fecha futura.")


def listar_tipos_habitaciones() -> str:
    return "📅 **Tipos de habitación disponibles:**\n• Sencilla\n• Doble\n• Triple\n• Cuádruple\n• Suite\n\nEnvíame tus fechas de entrada y salida en formato DD-MM-YYYY.\nEjemplo: 25-09-2026 -- 28-09-2026"