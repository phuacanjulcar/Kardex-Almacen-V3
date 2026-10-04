import os
import tkinter as tk
import customtkinter as ctk
import atexit
import traceback

from core.database import init_db, SecurityLayer
from core.managers.kardex_manager import KardexManager
from core.managers.user_manager import TxtUserManager
from core.services.expiration_service import run_expiration_check_async

from ui.screens.login_screen import LoginScreen
from ui.screens.main_screen import MainScreen
from ui.screens.kardex_selector import KardexSelector
from ui.screens.admin_panel import AdminPanel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AppRouter:
    """
    Gestor principal de la aplicación.
    Encargado del enrutamiento de vistas y mantenimiento del estado global (sesión).
    """
    def __init__(self, root):
        self.root = root
        self._setup_global_exception_handler()

        # Estado global (Session)
        self.user_manager = TxtUserManager()
        self.kardex_path = None
        self.manager = None
        self.current_user = None
        
        # Iniciamos el flujo de la aplicación
        self.show_login()

    def _setup_global_exception_handler(self):
        def _handle_exception(exc, val, tb):
            err_msg = str(val).lower()
            if isinstance(val, tk.TclError) and ("bad window path name" in err_msg or "invalid command name" in err_msg): 
                pass
            else:
                traceback.print_exception(exc, val, tb)
        self.root.report_callback_exception = _handle_exception

    def clear_window(self):
        """Limpia los widgets actuales para cargar una nueva vista de forma limpia."""
        for w in self.root.winfo_children(): 
            try: 
                w.destroy()
            except Exception: 
                pass

    # --- RUTAS DE LA APLICACIÓN ---

    def show_login(self):
        self.clear_window()
        self.show_login_screen_after_license("PERMANENT")

    def show_login_screen_after_license(self, status):
        self.clear_window()
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
        AdminPanel(self.root, self.current_user, self.logout, self.user_manager).pack(fill="both", expand=True)

    def on_guest(self):
        self.current_user = "Invitado"
        self.show_selector()

    def show_selector(self):
        self.clear_window()
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


def main():
    # 1. Configuración de Seguridad y Base de Datos
    SecurityLayer.decrypt_db()
    atexit.register(SecurityLayer.encrypt_db)
    init_db()

    # 2. Tareas en segundo plano (Evita bloqueos en el hilo principal)
    run_expiration_check_async()

    # 3. Configuración de la Ventana Principal de la UI
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
    
    # 4. Iniciar el Enrutador y Bucle de la App
    app = AppRouter(root)  # Mantenemos viva la referencia del router y variables
    root.mainloop()

if __name__ == "__main__":
    main()