import customtkinter as ctk
import tkinter as tk
import os

from core.kardex_manager import KardexManager
from core.user_manager import TxtUserManager
from ui.login_screen import LoginScreen
from ui.main_screen import MainScreen
from ui.kardex_selector import KardexSelector  # ¡Aquí llamamos a nuestro nuevo archivo!
from ui.admin_panel import AdminPanel

from core.database import init_db, SecurityLayer
import atexit

# Descifrar la base de datos (At-Rest) antes de inicializar SQLite
SecurityLayer.decrypt_db()

# Asegurar que se cifre al cerrar la app
atexit.register(SecurityLayer.encrypt_db)

init_db()

def check_expirations():
    try:
        from core.database import get_connection
        from datetime import datetime
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
            except Exception: pass
        conn.close()
    except Exception as e:
        print(f"Error en check_expirations: {e}")

check_expirations()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class App:
    def __init__(self, root):
        self.root = root
        
        # Gestor global de errores de Tkinter para evitar cierres abruptos
        def _handle_exception(exc, val, tb):
            err_msg = str(val).lower()
            if isinstance(val, tk.TclError) and ("bad window path name" in err_msg or "invalid command name" in err_msg): pass
            else:
                import traceback
                traceback.print_exception(exc, val, tb)
        self.root.report_callback_exception = _handle_exception

        self.user_manager = TxtUserManager()
        self.kardex_path = None
        self.manager = None
        self.current_user = None
        
        # Iniciamos el flujo de la aplicación
        self.show_login()

    def clear_window(self):
        for w in self.root.winfo_children(): 
            try: w.destroy()
            except: pass

    def show_login(self):
        self.clear_window()
        self.show_login_screen_after_license("PERMANENT")

    # Modificamos esta función para que reciba el 'status'
    def show_login_screen_after_license(self, status):
        self.clear_window()
        # Le enviamos el parámetro trial_status a la ventana de Login
        LoginScreen(self.root, self.on_login, self.on_guest, user_manager=self.user_manager, trial_status=status)

    def on_login(self, username):
        self.current_user = username
        # LA BIFURCACIÓN DE CAMINOS
        if username == "Administrador":
            self.show_admin_panel()
        else:
            self.show_selector()

    def show_admin_panel(self):
        self.clear_window()
        # Le pasamos el 'self.user_manager' al final
        AdminPanel(self.root, self.current_user, self.logout, self.user_manager).pack(fill="both", expand=True)


    def on_guest(self):
        self.current_user = "Invitado"
        self.show_selector()

    def show_selector(self):
        self.clear_window()
        # Aquí se instancia la pantalla limpia que acabamos de modularizar
        KardexSelector(self.root, self.select_kardex, self.current_user, self.logout)

    def select_kardex(self, filepath):
        self.kardex_path = filepath
        self.manager = KardexManager(filepath)
        self.show_main()

    def show_main(self):
        self.clear_window()
        MainScreen(self.root, self.manager, self.current_user, self.logout, self.show_selector)

    def logout(self):
        self.current_user = None
        self.show_login()

if __name__ == "__main__":
    ctk.set_appearance_mode("Light")
    root = ctk.CTk() 
    root.geometry("1050x770") 
    root.title("Almacén Inmaculada - Fase 2.1")
    
    try:
        ruta_icono = os.path.join(BASE_DIR, "ui", "assets", "ciudad_imagen.ico")
        root.iconbitmap(ruta_icono)
    except Exception as e:
        print(f"Aviso: No se pudo cargar el icono de la ventana. {e}")

    def on_closing():
        os._exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    App(root)
    root.mainloop()