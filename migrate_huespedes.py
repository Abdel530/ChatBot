import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "hotel.db"

COLUMNS_TO_ADD = [
    ("nacionalidad", "TEXT"),
    ("email", "TEXT"),
]


def migrate():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='huespedes'")
    table_exists = cursor.fetchone()

    if not table_exists:
        cursor.execute("""
            CREATE TABLE huespedes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telefono TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                documento TEXT,
                nacionalidad TEXT,
                email TEXT
            )
        """)
        print("[OK] Table 'huespedes' created with new columns.")
    else:
        cursor.execute("PRAGMA table_info(huespedes)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        for col_name, col_type in COLUMNS_TO_ADD:
            if col_name not in existing_columns:
                cursor.execute(f"ALTER TABLE huespedes ADD COLUMN {col_name} {col_type}")
                print(f"[OK] Column '{col_name}' added to huespedes.")
            else:
                print(f"[OK] Column '{col_name}' already exists in huespedes.")

    cursor.execute("PRAGMA table_info(huespedes)")
    final_columns = [row[1] for row in cursor.fetchall()]
    print(f"Huespedes columns: {final_columns}")

    conn.commit()
    conn.close()
    print("Migration completed.")


if __name__ == "__main__":
    migrate()
