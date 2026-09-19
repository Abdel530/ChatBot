from database.connection import get_db

def get_connection():
    """
    Retorna el cliente sincrónico de Turso (LibSQL).
    Reemplaza la conexión local de SQLite.
    """
    return get_db()