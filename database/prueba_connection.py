from connection import get_db

try:
    client = get_db()
    result = client.execute("SELECT * FROM habitaciones LIMIT 5;")
    print("✅ ¡Conexión a Turso exitosa! Habitaciones encontradas:")
    for row in result.rows:
        print(row)
    client.close()
except Exception as e:
    print(f"❌ Error al conectar con Turso: {e}")