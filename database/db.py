from database.connection import get_db

DB_PATH = None  # Mantenido por compatibilidad antigua

def get_connection():
    """
    Retorna el cliente sincrónico de Turso (LibSQL).
    Reemplaza la conexión local de SQLite.
    """
    return get_db()