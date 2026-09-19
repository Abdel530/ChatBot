import sqlite3
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

MENSAJE_ERROR_DB = (
    "Hubo un problema al consultar la disponibilidad. "
    "Intenta de nuevo o selecciona 'Hablar con recepción' del menú."
)


def consultar_disponibilidad(fecha_entrada: str, fecha_salida: str) -> str:
    try:
        __validar_fechas(fecha_entrada, fecha_salida)
    except ValueError as e:
        return str(e)

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
            (fecha_entrada, fecha_salida),
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
        return "Lo sentimos, no tenemos disponibilidad para las fechas seleccionadas."
    return "\n".join(lineas)


def upsert_huesped(huesped_id: int, nombre: str = None, documento: str = None,
                   nacionalidad: str = None, email: str = None, telefono: str = None) -> int:
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
            if documento is not None:
                set_clauses.append("documento = ?")
                params.append(documento)
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
                "INSERT INTO huespedes (id, nombre, documento, nacionalidad, email, telefono) VALUES (?, ?, ?, ?, ?, ?)",
                (huesped_id, nombre or f"Huésped_{huesped_id}", documento or "", nacionalidad or "", email or "", telefono or ""),
            )
        conn.commit()
        conn.close()
        return huesped_id
    except sqlite3.Error:
        return None
    except Exception:
        return None


def guardar_itinerario_vuelo(reserva_id: int, vuelo: str, aerolinea: str, hora_llegada: str) -> bool:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO llegadas (reserva_id, hora_llegada) VALUES (?, ?)",
            (reserva_id, f"Vuelo {vuelo} - {aerolinea} - Llegada: {hora_llegada}"),
        )
        cursor.execute(
            "UPDATE reservas SET hora_llegada = ? WHERE id = ?",
            (f"Vuelo {vuelo} - {aerolinea}", reserva_id),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False
    except Exception:
        return False


def registrar_reserva(huesped_id: int, habitacion_id: int, check_in: str, check_out: str,
                      politica: str, importe_total: float) -> str:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM habitaciones WHERE id = ? AND estado_limpieza IN ('limpia', 'en_proceso')",
            (habitacion_id,),
        )
        habitacion = cursor.fetchone()
        if not habitacion:
            conn.close()
            return "La habitación seleccionada no está disponible."

        cursor.execute(
            "SELECT id FROM reservas WHERE habitacion_id = ? AND estado = 'confirmada' AND check_out > ? AND check_in < ?",
            (habitacion_id, check_in, check_out),
        )
        if cursor.fetchone():
            conn.close()
            return "Lo sentimos, esta habitación ya tiene una reserva activa para esas fechas."

        cursor.execute(
            "INSERT INTO reservas (huesped_id, habitacion_id, check_in, check_out, politica, estado, importe_total) VALUES (?, ?, ?, ?, ?, 'confirmada', ?)",
            (huesped_id, habitacion_id, check_in, check_out, politica, importe_total),
        )
        conn.commit()
        reserva_id = cursor.lastrowid
        conn.close()

        return (
            f"✅ ¡Reserva confirmada!\n"
            f"- ID de reserva: #{reserva_id}\n"
            f"- Habitación: {habitacion_id}\n"
            f"- Check-in: {check_in}\n"
            f"- Check-out: {check_out}\n"
            f"- Estado: confirmada\n"
            f"- Recibirás un código de acceso en tu check-in."
        )
    except sqlite3.Error:
        return MENSAJE_ERROR_DB
    except Exception:
        return MENSAJE_ERROR_DB


def registrar_reserva_con_transfer(huesped_id: int, check_in: str, check_out: str,
                                    politica: str, importe_total: float,
                                    vuelo: str, aerolinea: str, hora_llegada: str) -> str:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reservas (huesped_id, habitacion_id, check_in, check_out, politica, estado, importe_total) VALUES (?, 0, ?, ?, ?, 'confirmada', ?)",
            (huesped_id, check_in, check_out, politica, importe_total),
        )
        conn.commit()
        reserva_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO llegadas (reserva_id, hora_llegada) VALUES (?, ?)",
            (reserva_id, f"Vuelo {vuelo} - {aerolinea} - Llegada: {hora_llegada}"),
        )
        cursor.execute(
            "UPDATE reservas SET hora_llegada = ? WHERE id = ?",
            (f"Vuelo {vuelo} - {aerolinea}", reserva_id),
        )
        conn.commit()
        conn.close()

        return (
            f"✅ ¡Reserva confirmada con transfer!\n"
            f"- ID de reserva: #{reserva_id}\n"
            f"- Vuelo: {vuelo}\n"
            f"- Aerolínea: {aerolinea}\n"
            f"- Hora de llegada: {hora_llegada}\n"
            f"- ¡Te esperamos en el aeropuerto!"
        )
    except sqlite3.Error:
        return MENSAJE_ERROR_DB
    except Exception:
        return MENSAJE_ERROR_DB


def __validar_fechas(fecha_entrada: str, fecha_salida: str) -> None:
    try:
        entrada = datetime.fromisoformat(fecha_entrada)
        salida = datetime.fromisoformat(fecha_salida)
        if salida <= entrada:
            raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada.")
        if entrada < datetime.now():
            raise ValueError("La fecha de entrada debe ser una fecha futura.")
    except ValueError:
        raise


def listar_tipos_habitaciones() -> str:
    return "📅 **Tipos de habitación disponibles:**\n• Sencilla\n• Doble\n• Triple\n• Cuádruple\n• Suite\n\nEnvíame tus fechas de entrada y salida en formato YYYY-MM-DD."