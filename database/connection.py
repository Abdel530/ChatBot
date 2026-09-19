import os
import libsql_client
from dotenv import load_dotenv

load_dotenv()

def get_db():
    url = os.getenv("TURSO_DATABASE_URL")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")
    
    if not url or not auth_token:
        raise ValueError("❌ Error: Faltan las variables TURSO_DATABASE_URL o TURSO_AUTH_TOKEN en el entorno.")
        
    return libsql_client.create_client_sync(
        url=url,
        auth_token=auth_token
    )