import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from database.db import get_connection
from database.models import SQL_TABLES

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "hotel.db"

HUESPEDES_DATA = [
    (1, "34600123456", "Juan Pérez", "12345678A"),
    (2, "34600999888", "Ana García", "87654321B"),
    (3, "34600777666", "Carlos López", "11223344C"),
    (4, "34600555444", "María Martín", "99887766D"),
    (5, "34600333222", "Pedro Sánchez", "55667788E"),
]

HABITACIONES_DATA = [
    (1, "101", "Sencilla", "limpia", 150.0),
    (2, "102", "Sencilla", "limpia", 150.0),
    (3, "201", "Doble", "limpia", 250.0),
    (4, "202", "Doble", "limpia", 250.0),
    (5, "203", "Doble", "limpia", 250.0),
    (6, "301", "Triple", "limpia", 350.0),
    (7, "302", "Triple", "limpia", 350.0),
    (8, "401", "Cuádruple", "limpia", 450.0),
    (9, "501", "Suite", "limpia", 600.0),
    (10, "502", "Suite", "limpia", 600.0),
]

RESERVAS_DATA = [
    (1, 1, 1, (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
     (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
     "moderada", "confirmada", 700.0, None, None),
    (2, 2, 3, (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
     (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d"),
     "flexible", "confirmada", 600.0, None, None),
    (3, 3, 6, (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
     (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
     "no_reembolsable", "confirmada", 1050.0, None, None),
]

SERVICIOS_DATA = [
    (1, "Recepción 24h", "Atención de check-in y check-out disponible las 24 horas del día.", "24h / 7 días", "Recepción principal"),
    (2, "Desayuno incluido", "Desayuno buffet con opciones calientes y frías, servicio de 6:30 a 10:30.", "6:30 - 10:30", "Restaurante"),
    (3, "WiFi gratuito", "Conexión WiFi de alta velocidad disponible en todas las áreas del hotel.", "24h / 7 días", "Áreas comunes"),
    (4, "Piscina", "Piscina al aire libre con zona de jacuzzi. Capacidad máxima 50 personas.", "08:00 - 22:00", "Área exterior"),
    (5, "Spa", "Servicios de spa con masajes y tratamientos de relajación. Reserve con anticipación.", "09:00 - 21:00", "Planta baja"),
    (6, "Estacionamiento", "Estacionamiento seguro con cargo adicional de $200 MXN por noche.", "24h / 7 días", "Subsuelo"),
    (7, "Restaurante", "Restaurante gourmet con cocina local e internacional. Reserve su mesa.", "07:00 - 23:00", "Planta alta"),
]


def seed():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.executescript(SQL_TABLES)

    cursor.executemany(
        "INSERT OR IGNORE INTO huespedes (id, telefono, nombre, documento) VALUES (?, ?, ?, ?)",
        HUESPEDES_DATA,
    )
    cursor.executemany(
        "INSERT OR IGNORE INTO habitaciones (id, numero, tipo, estado_limpieza, costo_operativo_dia) VALUES (?, ?, ?, ?, ?)",
        HABITACIONES_DATA,
    )
    cursor.executemany(
        "INSERT OR IGNORE INTO reservas (id, huesped_id, habitacion_id, check_in, check_out, politica, estado, importe_total, codigo_acceso, hora_llegada) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        RESERVAS_DATA,
    )
    cursor.executemany(
        "INSERT OR IGNORE INTO servicios (id, nombre, descripcion, horario, ubicacion) VALUES (?, ?, ?, ?, ?)",
        SERVICIOS_DATA,
    )
    conn.commit()
    conn.close()
    print(f"Base de datos inicializada en {DB_PATH}")
    print("Datos de prueba insertados:")
    print("  - 5 huéspedes")
    print("  - 10 habitaciones")
    print("  - 3 reservas")
    print("  - 7 servicios")


if __name__ == "__main__":
    seed()