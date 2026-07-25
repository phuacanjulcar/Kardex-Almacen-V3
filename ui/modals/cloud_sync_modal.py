import customtkinter as ctk
from tkinter import messagebox
import threading
from core.cloud_sync import NeonSyncEngine

class CloudSyncModal(ctk.CTkToplevel):
    def __init__(self, master, on_success_callback):
        super().__init__(master)
        self.title("Cierre de Turno - Respaldo en la Nube")
        self.geometry("450x350")
        self.on_success_callback = on_success_callback
        
        self.transient(master)
        self.grab_set()  # Block interaction with the main window
        self.protocol("WM_DELETE_WINDOW", self._on_close_attempt) # Prevent normal closing
        
        self.configure(fg_color="#F5F7FA")
        self.engine = NeonSyncEngine()
        
        self._setup_ui()

    def _setup_ui(self):
        ctk.CTkLabel(self, text="⚠️ Cierre de Turno Requerido", font=("Segoe UI", 18, "bold"), text_color="#D32F2F").pack(pady=(30, 10))
        
        msg = "Es obligatorio respaldar la base de datos en\nla nube de Neon antes de finalizar tu turno."
        ctk.CTkLabel(self, text=msg, font=("Segoe UI", 14), text_color="#334155").pack(pady=(0, 20))
        
        self.btn_sync = ctk.CTkButton(self, text="☁️ Iniciar Sincronización y Salir", font=("Segoe UI", 15, "bold"), fg_color="#10B981", hover_color="#059669", height=45, command=self._start_sync)
        self.btn_sync.pack(pady=(10, 5))
        
        self.btn_cancel = ctk.CTkButton(self, text="Cancelar (Volver al Panel)", font=("Segoe UI", 13, "bold"), fg_color="transparent", text_color="#D32F2F", hover_color="#FEE2E2", height=35, command=self._on_close_attempt)
        self.btn_cancel.pack(pady=5)
        
        self.lbl_status = ctk.CTkLabel(self, text="", font=("Segoe UI", 12), text_color="#1565C0")
        self.lbl_status.pack(pady=5)
        
        self.progress = ctk.CTkProgressBar(self, width=300)
        self.progress.pack(pady=10)
        self.progress.set(0)
        
    def _on_close_attempt(self):
        # Permitir al usuario cancelar el cierre de sesión y volver al panel de admin
        self.grab_release()
        self.destroy()

    def _start_sync(self):
        self.btn_sync.configure(state="disabled", text="Verificando Conexión...")
        self.btn_cancel.configure(state="disabled")
        
        # Check connection in thread
        threading.Thread(target=self._run_sync_thread, daemon=True).start()
        
    def _update_progress(self, percentage, msg):
        # Callback for progress bar
        self.lbl_status.configure(text=msg)
        self.progress.set(percentage / 100.0)
        self.update_idletasks()

    def _run_sync_thread(self):
        ok, msg = self.engine.test_connection()
        if not ok:
            self._handle_result(False, f"Fallo al conectar con Neon:\n{msg}")
            return
            
        ok, msg = self.engine.sync_data(progress_callback=self._update_progress)
        self._handle_result(ok, msg)

    def _handle_result(self, success, msg):
        if success:
            messagebox.showinfo("Éxito", "Sincronización a la nube completada.\nLa sesión se cerrará ahora.")
            self.grab_release()
            self.destroy()
            self.on_success_callback()
        else:
            messagebox.showerror("Error", msg)
            self.btn_sync.configure(state="normal", text="☁️ Reintentar Sincronización")
            self.btn_cancel.configure(state="normal")
            self.lbl_status.configure(text="Sincronización fallida.")
