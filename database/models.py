SQL_TABLES = """
CREATE TABLE IF NOT EXISTS huespedes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telefono TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    apellidos TEXT,
    cedula TEXT,
    nacionalidad TEXT,
    email TEXT
);

CREATE TABLE IF NOT EXISTS habitaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL,
    tipo TEXT,
    estado_limpieza TEXT DEFAULT 'limpia',
    costo_operativo_dia REAL DEFAULT 25.0
);

CREATE TABLE IF NOT EXISTS reservas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    huesped_id INTEGER NOT NULL,
    habitacion_id INTEGER NOT NULL,
    check_in TEXT NOT NULL,
    check_out TEXT NOT NULL,
    politica TEXT NOT NULL,
    estado TEXT DEFAULT 'confirmada',
    importe_total REAL NOT NULL,
    codigo_acceso TEXT,
    hora_llegada TEXT,
    FOREIGN KEY (huesped_id) REFERENCES huespedes(id),
    FOREIGN KEY (habitacion_id) REFERENCES habitaciones(id)
);

CREATE TABLE IF NOT EXISTS llegadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reserva_id INTEGER NOT NULL,
    hora_llegada TEXT,
    FOREIGN KEY (reserva_id) REFERENCES reservas(id)
);

CREATE TABLE IF NOT EXISTS escalaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telefono TEXT NOT NULL,
    mensaje TEXT,
    creada_en TEXT DEFAULT (datetime('now','localtime')),
    atendida INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS servicios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    horario TEXT NOT NULL,
    ubicacion TEXT DEFAULT ''
);
"""