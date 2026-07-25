import sqlite3
import os
from cryptography.fernet import Fernet

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "kardex.db")
ENC_PATH = os.path.join(BASE_DIR, "data", "kardex.db.enc")

# Static key for at-rest encryption to deter offline tampering
SECRET_KEY = b'eG05F2uW-k_P0wY_F3M7Gz1_4qJ8bY9wM4P5K9D_uLQ='
_fernet = Fernet(SECRET_KEY)

class SecurityLayer:
    @staticmethod
    def decrypt_db():
        if os.path.exists(ENC_PATH):
            try:
                with open(ENC_PATH, 'rb') as f:
                    enc_data = f.read()
                data = _fernet.decrypt(enc_data)
                with open(DB_PATH, 'wb') as f:
                    f.write(data)
                os.remove(ENC_PATH)
            except Exception as e:
                print("Error decrypting DB:", e)

    @staticmethod
    def encrypt_db():
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, 'rb') as f:
                    data = f.read()
                enc_data = _fernet.encrypt(data)
                with open(ENC_PATH, 'wb') as f:
                    f.write(enc_data)
                os.remove(DB_PATH)
            except Exception as e:
                print("Error encrypting DB:", e)

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'usuario',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            last_login TEXT
        )
    ''')
    
    # Sembrar Administrador si no existe
    import bcrypt
    cursor.execute("SELECT 1 FROM users WHERE username = 'Administrador'")
    if not cursor.fetchone():
        salt = bcrypt.gensalt()
        default_hash = bcrypt.hashpw("Admin_Kardex2026!".encode('utf-8'), salt).decode('utf-8')
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                      ('Administrador', default_hash, 'admin'))

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN locked_until TEXT")
    except sqlite3.OperationalError:
        pass

    # Zonas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Destinos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    # Categorias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    # Productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            unit TEXT DEFAULT 'Unds',
            zone_id INTEGER,
            category_id INTEGER,
            prefix TEXT DEFAULT 'PAQ',
            min_stock REAL DEFAULT 10,
            max_stock REAL DEFAULT 100,
            created_at TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY(zone_id) REFERENCES zones(id) ON DELETE SET NULL,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    ''')

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN is_active INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    # Lotes Activos (Inventory Lots) con Constraints
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_lots_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            lot_code TEXT NOT NULL UNIQUE,
            qty REAL NOT NULL CHECK(qty >= 0),
            unit_cost REAL NOT NULL CHECK(unit_cost >= 0),
            expiration_date TEXT,
            status TEXT DEFAULT 'Disponible',
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    ''')
    
    # Migrar si la tabla vieja existe y no tiene la estructura nueva
    cursor.execute("PRAGMA table_info(active_lots)")
    columns = [col['name'] for col in cursor.fetchall()]
    if columns:
        try:
            # Copiar datos a la tabla nueva si no existen
            cursor.execute('''
                INSERT OR IGNORE INTO active_lots_new (id, product_id, lot_code, qty, unit_cost, expiration_date, status)
                SELECT id, product_id, lot_code, qty, unit_cost, expiration_date, status FROM active_lots
            ''')
            cursor.execute("DROP TABLE active_lots")
            cursor.execute("ALTER TABLE active_lots_new RENAME TO active_lots")
        except sqlite3.OperationalError:
            pass
    else:
        cursor.execute("ALTER TABLE active_lots_new RENAME TO active_lots")

    try:
        cursor.execute("ALTER TABLE active_lots ADD COLUMN status TEXT DEFAULT 'Disponible'")
    except sqlite3.OperationalError:
        pass

    # Historial de Movimientos (Kardex Rows)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kardex_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            lot_code TEXT,
            type TEXT, -- Ingreso, Salida, Vencido
            concept TEXT,
            document TEXT,
            origin_dest TEXT,
            expiration_date TEXT,
            qty REAL,
            unit_cost REAL,
            total_cost REAL,
            balance_qty REAL,
            balance_total REAL,
            user TEXT DEFAULT 'Desconocido',
            lot_status TEXT DEFAULT 'Disponible',
            real_timestamp TEXT,
            out_of_hours INTEGER DEFAULT 0,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    ''')

    try:
        cursor.execute("ALTER TABLE kardex_movements ADD COLUMN user TEXT DEFAULT 'Desconocido'")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE kardex_movements ADD COLUMN lot_status TEXT DEFAULT 'Disponible'")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE kardex_movements ADD COLUMN real_timestamp TEXT")
        cursor.execute("ALTER TABLE kardex_movements ADD COLUMN out_of_hours INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Alertas y Notificaciones Globales (Removido, consolidado abajo)

    # Recepciones Masivas Pendientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mass_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document TEXT,
            origin TEXT,
            date TEXT,
            status TEXT,
            items_json TEXT
        )
    ''')

    # Historial de Recepciones y Despachos (Antes historial_recepciones.json)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            doc_type TEXT,
            doc_number TEXT,
            date TEXT,
            products TEXT,
            status TEXT,
            origen_global TEXT DEFAULT '',
            motivo_global TEXT DEFAULT ''
        )
    ''')

    # Notificaciones (Antes notificaciones.json)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            message TEXT,
            date TEXT,
            status TEXT DEFAULT 'unread'
        )
    ''')

    # Mensajería y Auditoría de Extornos (Fase 1 - Gmail)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            doc_reference TEXT,
            reason TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'unread',
            reply_to_id INTEGER,
            FOREIGN KEY(reply_to_id) REFERENCES messages(id) ON DELETE SET NULL
        )
    ''')

    # Recetas (Fórmulas predefinidas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            created_at TEXT,
            created_by TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            product_name TEXT,
            quantity REAL,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        )
    ''')

    # Auditoría de Catálogos (DB-002)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catalog_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT,
            record_id INTEGER,
            action TEXT,
            old_value TEXT,
            new_value TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Triggers para auditar productos
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS trg_products_insert
        AFTER INSERT ON products
        BEGIN
            INSERT INTO catalog_logs (table_name, record_id, action, new_value)
            VALUES ('products', NEW.id, 'INSERT', NEW.name || ' (' || NEW.prefix || ')');
        END;
    ''')
    
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS trg_products_update
        AFTER UPDATE ON products
        BEGIN
            INSERT INTO catalog_logs (table_name, record_id, action, old_value, new_value)
            VALUES ('products', NEW.id, 'UPDATE', OLD.name || ' (Active:' || OLD.is_active || ')', NEW.name || ' (Active:' || NEW.is_active || ')');
        END;
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database schema created successfully.")

def get_next_sequence(doc_type, prefix):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT doc_number FROM document_history WHERE doc_type = ? AND doc_number LIKE ? ORDER BY id DESC LIMIT 1", (doc_type, f"{prefix}-%"))
        row = cursor.fetchone()
        conn.close()
        
        if row and row['doc_number']:
            parts = row['doc_number'].split('-')
            if len(parts) > 1 and parts[1].isdigit():
                return f"{prefix}-{(int(parts[1]) + 1):06d}"
        return f"{prefix}-000001"
    except Exception as e:
        print(f"Error generando secuencia: {e}")
        return f"{prefix}-000001"
