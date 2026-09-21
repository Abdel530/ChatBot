import libsql
from config import settings


def get_connection():
  """Retorna una conexión nativa a Turso DB usando la librería libsql."""
  conn = libsql.connect(
      database=settings.turso_database_url,
      auth_token=settings.turso_auth_token,
  )
  return conn