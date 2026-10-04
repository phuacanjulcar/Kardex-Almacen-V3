import threading
from datetime import datetime

def _check_expirations_task():
    """ Tarea asíncrona para revisar vencimientos e insertar notificaciones """
    try:
        from core.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.name, a.lot_code, a.expiration_date, a.qty
            FROM active_lots a
            JOIN products p ON a.product_id = p.id
            WHERE a.expiration_date != '' AND a.expiration_date IS NOT NULL AND a.qty > 0
        """)
        lots = cursor.fetchall()
        
        hoy = datetime.now()
        for row in lots:
            try:
                fv = datetime.strptime(row['expiration_date'], "%Y-%m-%d")
                dias = (fv - hoy).days
                if 0 <= dias <= 15:
                    reason = f"Alerta de Vencimiento: {row['name']}"
                    doc_ref = row['lot_code']
                    body = f"ALERTA CRÍTICA: El lote {row['lot_code']} del producto {row['name']} vencerá en {dias} días (Fecha: {row['expiration_date']}). Quedan {row['qty']} unidades."
                    
                    cursor.execute("SELECT id FROM messages WHERE sender = 'SISTEMA' AND reason = ? AND doc_reference = ?", (reason, doc_ref))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO messages (sender, receiver, doc_reference, reason, body, created_at, status)
                            VALUES ('SISTEMA', 'Administrador', ?, ?, ?, ?, 'unread')
                        """, (doc_ref, reason, body, hoy.strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
            except Exception: 
                pass
        conn.close()
    except Exception as e:
        print(f"Error en check_expirations_task: {e}")

def run_expiration_check_async():
    """Ejecuta la revisión de vencimientos en un hilo secundario (daemon) para no bloquear la UI."""
    thread = threading.Thread(target=_check_expirations_task, daemon=True)
    thread.start()
