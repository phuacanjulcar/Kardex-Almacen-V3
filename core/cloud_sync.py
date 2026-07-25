import psycopg2
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
NEON_URL = os.environ.get("NEON_URL", "")

TABLES = {
    'users': ['id', 'username', 'password', 'role'],
    'zones': ['id', 'name'],
    'destinations': ['id', 'name'],
    'categories': ['id', 'name'],
    'products': ['id', 'name', 'unit', 'zone_id', 'category_id', 'prefix', 'min_stock', 'max_stock', 'created_at'],
    'active_lots': ['id', 'product_id', 'lot_code', 'qty', 'unit_cost', 'expiration_date', 'status'],
    'kardex_movements': ['id', 'product_id', 'date', 'lot_code', 'type', 'concept', 'document', 'origin_dest', 'expiration_date', 'qty', 'unit_cost', 'total_cost', 'balance_qty', 'balance_total', 'user', 'lot_status', 'real_timestamp', 'out_of_hours'],
    'mass_receipts': ['id', 'document', 'origin', 'date', 'status', 'items_json'],
    'document_history': ['id', 'user', 'doc_type', 'doc_number', 'date', 'products', 'status', 'origen_global', 'motivo_global'],
    'notifications': ['id', 'user', 'message', 'date', 'status'],
    'recipes': ['id', 'name', 'created_at', 'created_by'],
    'recipe_items': ['id', 'recipe_id', 'product_name', 'quantity']
}

class NeonSyncEngine:
    def __init__(self):
        self.neon_url = NEON_URL
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sqlite_path = os.path.join(base_dir, "data", "kardex.db")
        
    def test_connection(self):
        try:
            conn = psycopg2.connect(self.neon_url, connect_timeout=5)
            conn.close()
            return True, "Conexión exitosa"
        except Exception as e:
            return False, str(e)
            
    def sync_data(self, progress_callback=None):
        try:
            pg_conn = psycopg2.connect(self.neon_url)
            pg_cursor = pg_conn.cursor()
            
            sl_conn = sqlite3.connect(self.sqlite_path)
            sl_conn.row_factory = sqlite3.Row
            sl_cursor = sl_conn.cursor()
            
            if progress_callback: progress_callback(10, "Preparando Neon DB (Esquema Completo)...")
            
            # Create schema in Postgres
            # We map SQLite types roughly. Since it's a backup, TEXT for everything except REAL and INT is fine.
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT);")
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_zones (id INTEGER PRIMARY KEY, name TEXT);")
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_destinations (id INTEGER PRIMARY KEY, name TEXT);")
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_categories (id INTEGER PRIMARY KEY, name TEXT);")
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_products (id INTEGER PRIMARY KEY, name TEXT, unit TEXT, zone_id INTEGER, category_id INTEGER, prefix TEXT, min_stock REAL, max_stock REAL, created_at TEXT);")
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_active_lots (id INTEGER PRIMARY KEY, product_id INTEGER, lot_code TEXT, qty REAL, unit_cost REAL, expiration_date TEXT, status TEXT);")
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_kardex_movements (id INTEGER PRIMARY KEY, product_id INTEGER, date TEXT, lot_code TEXT, type TEXT, concept TEXT, document TEXT, origin_dest TEXT, expiration_date TEXT, qty REAL, unit_cost REAL, total_cost REAL, balance_qty REAL, balance_total REAL, user_name TEXT, lot_status TEXT, real_timestamp TEXT, out_of_hours INTEGER);")
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_mass_receipts (id INTEGER PRIMARY KEY, document TEXT, origin TEXT, date TEXT, status TEXT, items_json TEXT);")
            
            # Guardamos (commit) las creaciones de tabla anteriores antes de intentar alterar
            pg_conn.commit()
            
            # --- NUEVO: ALTER TABLE para añadir columnas a DB en la nube si ya existía antes ---
            for alter_cmd in [
                "ALTER TABLE sync_active_lots ADD COLUMN status TEXT;",
                "ALTER TABLE sync_kardex_movements ADD COLUMN lot_status TEXT;",
                "ALTER TABLE sync_kardex_movements ADD COLUMN real_timestamp TEXT;",
                "ALTER TABLE sync_kardex_movements ADD COLUMN out_of_hours INTEGER;"
            ]:
                try:
                    pg_cursor.execute(alter_cmd)
                    pg_conn.commit()
                except Exception:
                    pg_conn.rollback() # Limpia el estado de transacción abortada
            # -----------------------------------------------------------------------------------
            
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_document_history (id INTEGER PRIMARY KEY, user_name TEXT, doc_type TEXT, doc_number TEXT, date TEXT, products TEXT, status TEXT, origen_global TEXT, motivo_global TEXT);")
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_notifications (id INTEGER PRIMARY KEY, user_name TEXT, message TEXT, date TEXT, status TEXT);")
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_recipes (id INTEGER PRIMARY KEY, name TEXT, created_at TEXT, created_by TEXT);")
            pg_cursor.execute("CREATE TABLE IF NOT EXISTS sync_recipe_items (id INTEGER PRIMARY KEY, recipe_id INTEGER, product_name TEXT, quantity REAL);")
            pg_conn.commit()

            total_tables = len(TABLES)
            for idx, (table_name, columns) in enumerate(TABLES.items()):
                if progress_callback: progress_callback(15 + int((idx/total_tables)*70), f"Subiendo {table_name}...")
                
                # 'user' is a reserved keyword in Postgres, we map it to 'user_name' in our sync tables
                pg_cols = [c if c != 'user' else 'user_name' for c in columns]
                
                sl_cursor.execute(f"SELECT {','.join(columns)} FROM {table_name}")
                rows = sl_cursor.fetchall()
                
                if not rows: continue
                
                placeholders = ','.join(['%s'] * len(columns))
                update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in pg_cols if col != 'id'])
                
                # Handle cases with no columns to update (e.g., only ID)
                if not update_set:
                    query = f"INSERT INTO sync_{table_name} (id) VALUES (%s) ON CONFLICT (id) DO NOTHING"
                else:
                    query = f"INSERT INTO sync_{table_name} ({','.join(pg_cols)}) VALUES ({placeholders}) ON CONFLICT (id) DO UPDATE SET {update_set}"
                
                for row in rows:
                    pg_cursor.execute(query, tuple(row))
                    
            pg_conn.commit()
            pg_conn.close()
            sl_conn.close()
            
            if progress_callback: progress_callback(100, "Respaldo Total Exitoso.")
            return True, "Sincronización exitosa."
            
        except Exception as e:
            return False, f"Error durante la sincronización: {str(e)}"

    def restore_data(self, progress_callback=None):
        try:
            if progress_callback: progress_callback(10, "Conectando con Neon DB...")
            pg_conn = psycopg2.connect(self.neon_url)
            pg_cursor = pg_conn.cursor()
            
            sl_conn = sqlite3.connect(self.sqlite_path)
            sl_cursor = sl_conn.cursor()
            
            total_tables = len(TABLES)
            for idx, (table_name, columns) in enumerate(TABLES.items()):
                if progress_callback: progress_callback(15 + int((idx/total_tables)*80), f"Restaurando {table_name}...")
                
                pg_cols = [c if c != 'user' else 'user_name' for c in columns]
                try:
                    pg_cursor.execute(f"SELECT {','.join(pg_cols)} FROM sync_{table_name}")
                    rows = pg_cursor.fetchall()
                except Exception:
                    pg_conn.rollback() # Table might not exist in Neon yet
                    continue
                
                if not rows: continue
                
                placeholders = ','.join(['?'] * len(columns))
                
                for row in rows:
                    sl_cursor.execute(f"INSERT OR REPLACE INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})", row)
                    
            sl_conn.commit()
            sl_conn.close()
            pg_conn.close()
            
            if progress_callback: progress_callback(100, "Restauración completada.")
            return True, "Restauración exitosa."
            
        except Exception as e:
            return False, f"Error al restaurar: {str(e)}"
