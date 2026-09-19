import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "hotel.db"

SERVICIOS_DATA = [
    (1, "Recepción 24h", "Atención de check-in y check-out disponible las 24 horas del día.", "24h / 7 días", "Recepción principal"),
    (2, "Desayuno incluido", "Desayuno buffet con opciones calientes y frías, servicio de 6:30 a 10:30.", "6:30 - 10:30", "Restaurante"),
    (3, "WiFi gratuito", "Conexión WiFi de alta velocidad disponible en todas las áreas del hotel.", "24h / 7 días", "Áreas comunes"),
    (4, "Piscina", "Piscina al aire libre con zona de jacuzzi. Capacidad máxima 50 personas.", "08:00 - 22:00", "Área exterior"),
    (5, "Spa", "Servicios de spa con masajes y tratamientos de relajación. Reserve con anticipación.", "09:00 - 21:00", "Planta baja"),
    (6, "Estacionamiento", "Estacionamiento seguro con cargo adicional de $200 MXN por noche.", "24h / 7 días", "Subsuelo"),
    (7, "Restaurante", "Restaurante gourmet con cocina local e internacional. Reserve su mesa.", "07:00 - 23:00", "Planta alta"),
]


def migrate():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='servicios'")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute("""
            CREATE TABLE servicios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                horario TEXT NOT NULL,
                ubicacion TEXT DEFAULT ''
            )
        """)
        cursor.executemany(
            "INSERT INTO servicios (id, nombre, descripcion, horario, ubicacion) VALUES (?, ?, ?, ?, ?)",
            SERVICIOS_DATA,
        )
        conn.commit()
        print("[OK] Tabla 'servicios' creada y poblada con exito.")
    else:
        cursor.execute("SELECT COUNT(*) FROM servicios")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.executemany(
                "INSERT INTO servicios (id, nombre, descripcion, horario, ubicacion) VALUES (?, ?, ?, ?, ?)",
                SERVICIOS_DATA,
            )
            conn.commit()
            print("[OK] Tabla 'servicios' ya existia pero estaba vacia. Registros insertados.")
        else:
            print("[OK] Tabla 'servicios' ya existe con datos. Sin cambios necesarios.")

    cursor.execute("SELECT COUNT(*) FROM servicios")
    print("Total de servicios en BD: %d" % cursor.fetchone()[0])
    conn.close()


if __name__ == "__main__":
    migrate()
