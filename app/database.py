import sqlite3
import os

_ENV_DB = os.environ.get("DATABASE_PATH")
_PRIMARY_DB = r"C:\Users\CONECTIA BA\OneDrive\Escritorio\SaludNatura_archivos\salud_natura.db"
_FALLBACK_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "salud_natura.db")

if _ENV_DB:
    DB_PATH = _ENV_DB
elif os.path.exists(_PRIMARY_DB):
    DB_PATH = _PRIMARY_DB
else:
    DB_PATH = _FALLBACK_DB


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # Asegurar que el directorio padre de la base de datos exista
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS base_conocimiento_salud (
            id_remedio INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_remedio TEXT NOT NULL,
            planta_base TEXT,
            propiedades TEXT,
            contraindicaciones TEXT,
            dosificacion TEXT,
            link_articulo_web TEXT,
            imagen_url TEXT
        )
    """)

    for col_sql in [
        "ALTER TABLE base_conocimiento_salud ADD COLUMN imagen_url TEXT",
        "ALTER TABLE base_conocimiento_salud ADD COLUMN imagen_fuente TEXT",
        "ALTER TABLE base_conocimiento_salud ADD COLUMN imagen_miniatura BLOB",
        "ALTER TABLE base_conocimiento_salud ADD COLUMN imagen_miniatura_url TEXT",
    ]:
        try:
            conn.execute(col_sql)
            conn.commit()
        except:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_y_clientes (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_completo TEXT NOT NULL,
            celular TEXT,
            email TEXT,
            direccion_completa TEXT,
            ciudad_prov_pais TEXT,
            latitud REAL,
            longitud REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS botiquin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dolencia TEXT NOT NULL,
            emoji TEXT,
            categoria TEXT,
            planta TEXT,
            nombre_cientifico TEXT,
            preparacion TEXT,
            nota TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            fecha TEXT DEFAULT (datetime('now','localtime')),
            id_usuario INTEGER,
            respondida INTEGER DEFAULT 0,
            respuesta TEXT
        )
    """)

    # Agregar columna id_remedio a botiquin si no existe
    try:
        conn.execute("ALTER TABLE botiquin ADD COLUMN id_remedio INTEGER REFERENCES base_conocimiento_salud(id_remedio)")
        conn.commit()
    except:
        pass

    # Vincular botiquin con base_conocimiento_salud por nombre de planta
    conn.execute("""
        UPDATE botiquin SET id_remedio = (
            SELECT id_remedio FROM base_conocimiento_salud
            WHERE nombre_remedio = botiquin.planta
        ) WHERE id_remedio IS NULL
    """)
    conn.commit()

    conn.commit()
    conn.close()
