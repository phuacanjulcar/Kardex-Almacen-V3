import customtkinter as ctk
import os

# Importamos nuestros módulos recién creados
from ui.admin_views.dashboard_view import DashboardView
from ui.admin_views.inbox_view import InboxView
from ui.admin_views.catalog_view import CatalogView
from ui.admin_views.users_view import UsersView
from ui.admin_views.history_view import HistoryView
from ui.admin_views.files_view import FilesView
from ui.admin_views.audit_view import AuditView
from ui.admin_views.recipe_view import RecipeView
from ui.admin_views.gestor_view import GestorView
from ui.admin_views.message_inbox_view import AdminMessageInboxView
from ui.modals.cloud_sync_modal import CloudSyncModal
from ui.components.theme import Theme

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class AdminPanel(ctk.CTkFrame):
    def __init__(self, master, current_user, on_logout, user_manager):
        super().__init__(master, fg_color="transparent")
        self.current_user = current_user
        self.on_logout_callback = on_logout
        self.user_manager = user_manager
        
        self.modo = ctk.get_appearance_mode()
        self.configure(fg_color=Theme.BG_GENERAL)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self._crear_sidebar()
        
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        self.mostrar_inicio()

    def _crear_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(13, weight=1) # Aumentado para empujar el botón de logout correctamente
        
        ctk.CTkLabel(self.sidebar, text="Centro de Control", font=("Segoe UI", 18, "bold"), text_color=Theme.PRIMARY).grid(row=0, column=0, padx=20, pady=(30, 10), sticky="w")
        
        # --- CENTRO DE NOTIFICACIONES (Campanita) ---
        from datetime import datetime
        docs_count = msgs_count = alerts_count = moves_count = 0
        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM document_history WHERE status = 'Pendiente de Validación'")
            docs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM messages WHERE receiver = 'Administrador' AND status = 'unread'")
            msgs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE user = 'Administrador' AND status = 'unread'")
            alerts_count = cursor.fetchone()[0]
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM kardex_movements WHERE date LIKE ?", (f"{today_str}%",))
            moves_count = cursor.fetchone()[0]
            
            conn.close()
        except Exception as e:
            print("Error cargando notificaciones:", e)
            
        total_alertas = docs_count + msgs_count + alerts_count
        texto_campana = f"🔔 Notificaciones ({total_alertas})"
        color_campana = Theme.DANGER if total_alertas > 0 else Theme.SUCCESS
        hover_campana = Theme.DANGER_HOVER if total_alertas > 0 else Theme.SUCCESS_HOVER
        
        self.current_metrics = {"docs": docs_count, "msgs": msgs_count, "alerts": alerts_count, "moves": moves_count}
        
        ctk.CTkButton(self.sidebar, text=texto_campana, font=("Segoe UI", 12, "bold"), fg_color="transparent", border_width=1, border_color=color_campana, text_color=color_campana, hover_color=hover_campana, command=self.mostrar_notification_center).grid(row=1, column=0, padx=15, pady=(0, 20), sticky="ew")

        # --- BOTONES ---
        txt_c = Theme.TEXT_MUTED
        hov_c = Theme.TRANSPARENT_HOVER

        ctk.CTkButton(self.sidebar, text="Inicio", font=("Segoe UI", 14), fg_color="transparent", text_color=txt_c, hover_color=hov_c, anchor="w", command=self.mostrar_inicio).grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        
        # NUEVO BOTÓN: BANDEJA DE MENSAJES (Fase 1)
        ctk.CTkButton(self.sidebar, text="Bandeja de Mensajes", font=("Segoe UI", 14), fg_color="#8B5CF6", text_color="white", hover_color="#7C3AED", anchor="w", command=self.mostrar_mensajes).grid(row=3, column=0, padx=15, pady=5, sticky="ew")
        
        ctk.CTkButton(self.sidebar, text="Documentos Pendientes", font=("Segoe UI", 14), fg_color="transparent", text_color=txt_c, hover_color=hov_c, anchor="w", command=self.mostrar_recepciones).grid(row=4, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Documentos Observados", font=("Segoe UI", 14), fg_color="transparent", text_color=txt_c, hover_color=hov_c, anchor="w", command=self.mostrar_historial).grid(row=5, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Auditoria de Movimientos", font=("Segoe UI", 14), fg_color="transparent", text_color=txt_c, hover_color=hov_c, anchor="w", command=self.mostrar_auditoria).grid(row=6, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Organizacion de Catalogo", font=("Segoe UI", 14), fg_color="transparent", text_color=txt_c, hover_color=hov_c, anchor="w", command=self.mostrar_catalogo).grid(row=7, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Gestor de Zonas/Cat.", font=("Segoe UI", 14), fg_color="transparent", text_color=txt_c, hover_color=hov_c, anchor="w", command=self.mostrar_gestor).grid(row=8, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Gestion de Personal", font=("Segoe UI", 14), fg_color="transparent", text_color=txt_c, hover_color=hov_c, anchor="w", command=self.mostrar_usuarios).grid(row=9, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Gestion de Recetas", font=("Segoe UI", 14), fg_color="transparent", text_color=txt_c, hover_color=hov_c, anchor="w", command=self.mostrar_recetas).grid(row=10, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Archivos Generales", font=("Segoe UI", 14), fg_color="transparent", text_color=txt_c, hover_color=hov_c, anchor="w", command=self.mostrar_archivos).grid(row=11, column=0, padx=15, pady=5, sticky="ew")
        
        # NUEVO BOTÓN: Respaldo Manual a la Nube
        ctk.CTkButton(self.sidebar, text="☁️ Respaldo en la Nube", font=("Segoe UI", 14, "bold"), fg_color="transparent", border_width=1, border_color=Theme.SUCCESS[0], text_color=Theme.SUCCESS[0], hover_color=Theme.TRANSPARENT_HOVER, command=self.sincronizacion_manual).grid(row=12, column=0, padx=15, pady=5, sticky="ew")
        
        # NUEVO BOTÓN: Autorizar Horario
        ctk.CTkButton(self.sidebar, text="🕒 Autorizar Horario Extra", font=("Segoe UI", 14, "bold"), fg_color="transparent", border_width=1, border_color=Theme.WARNING[0], text_color=Theme.WARNING[0], hover_color=Theme.TRANSPARENT_HOVER, command=self.autorizar_horario).grid(row=13, column=0, padx=15, pady=(5, 15), sticky="ew")
        
        self.switch_var = ctk.IntVar(value=1 if self.modo == "Dark" else 0)
        self.switch_theme = ctk.CTkSwitch(self.sidebar, text="Modo Oscuro", font=("Segoe UI", 12, "bold"), variable=self.switch_var, text_color=txt_c, progress_color=Theme.PRIMARY[0], command=self._toggle_theme)
        self.switch_theme.grid(row=14, column=0, padx=20, pady=10, sticky="sw")

        ctk.CTkButton(self.sidebar, text="Cerrar Sesion", font=("Segoe UI", 13, "bold"), fg_color=Theme.DANGER, text_color="white", hover_color=Theme.DANGER_HOVER, command=self.cerrar_sesion).grid(row=15, column=0, padx=20, pady=30, sticky="ew")

    # [RESTO DE TUS FUNCIONES _toggle_theme, _limpiar_pantalla, mostrar_inicio... se mantienen intactas]

    # Añade esta función al final del archivo junto a tus otros enrutadores
    def mostrar_gestor(self):
        self._limpiar_pantalla()
        GestorView(self.main_frame, self, BASE_DIR)

        
    # Función que cambia el tema y recarga el panel
    def _toggle_theme(self):
        nuevo_modo = "Dark" if self.switch_var.get() == 1 else "Light"
        ctk.set_appearance_mode(nuevo_modo)
        self.modo = nuevo_modo

    def _limpiar_pantalla(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
    def _reload_ui(self):
        # Recargar la interfaz completa (utilizado cuando se marcan notificaciones como leídas)
        for widget in self.winfo_children():
            widget.destroy()
        
        self.configure(fg_color=Theme.BG_GENERAL)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._crear_sidebar()
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.mostrar_inicio()

    # Enrutadores que cargan las vistas modulares
    def mostrar_inicio(self):
        self._limpiar_pantalla()
        DashboardView(self.main_frame, self, BASE_DIR)
        
    def mostrar_notification_center(self):
        from ui.modals.notification_center_modal import NotificationCenterModal
        callbacks = {
            "docs": self.mostrar_recepciones,
            "msgs": self.mostrar_mensajes,
            "moves": self.mostrar_auditoria,
            "refresh": self._reload_ui
        }
        NotificationCenterModal(self.winfo_toplevel(), self.current_user, getattr(self, 'current_metrics', {}), callbacks)

    def mostrar_recepciones(self):
        self._limpiar_pantalla()
        InboxView(self.main_frame, self, BASE_DIR)

    def mostrar_mensajes(self):
        self._limpiar_pantalla()
        AdminMessageInboxView(self.main_frame, self, BASE_DIR)

    def mostrar_catalogo(self):
        self._limpiar_pantalla()
        CatalogView(self.main_frame, self, BASE_DIR)
        
    def mostrar_usuarios(self):
        self._limpiar_pantalla()
        UsersView(self.main_frame, self, self.user_manager)

    def mostrar_recetas(self):
        self._limpiar_pantalla()
        RecipeView(self.main_frame, self, BASE_DIR)

    def mostrar_toast(self, mensaje, color_fondo="#10B981"):
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True) 
        toast.attributes("-topmost", True)
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 150
        y = self.winfo_rooty() + 50
        toast.geometry(f"300x45+{x}+{y}")
        frame = ctk.CTkFrame(toast, fg_color=color_fondo, corner_radius=8)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text=mensaje, text_color="white", font=("Segoe UI", 13, "bold")).pack(pady=10)
        
        def fade_out(alpha=1.0):
            alpha -= 0.05
            if alpha > 0:
                toast.attributes("-alpha", alpha)
                toast.after(30, lambda: fade_out(alpha))
            else:
                toast.destroy()
        toast.after(1500, fade_out)

    def cerrar_sesion(self):
        # Interceptar el cierre de sesión y forzar la sincronización en la nube
        def do_logout():
            self.destroy()
            self.on_logout_callback()
            
        CloudSyncModal(self.winfo_toplevel(), do_logout)
        
    def sincronizacion_manual(self):
        # Muestra la ventana modal de CloudSync pero sin cerrar la sesión
        CloudSyncModal(self.winfo_toplevel(), lambda: self.mostrar_toast("Respaldo completado, puedes seguir trabajando."))
        
    def autorizar_horario(self):
        import json
        from datetime import datetime, timedelta
        from tkinter import messagebox
        
        if messagebox.askyesno("Autorización", "¿Deseas autorizar a los operarios a iniciar sesión y registrar movimientos fuera del horario laboral (por las próximas 2 horas)?\n\nNota: Los movimientos seguirán marcándose como 'Retroactivos/Fuera de Horario' para auditoría."):
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                override_file = os.path.join(base_dir, "data", "override_horario.json")
                valid_until = datetime.now() + timedelta(hours=2)
                
                os.makedirs(os.path.dirname(override_file), exist_ok=True)
                with open(override_file, "w") as f:
                    json.dump({"valid_until": valid_until.strftime("%Y-%m-%d %H:%M:%S")}, f)
                    
                self.mostrar_toast(f"Horario extendido habilitado hasta las {valid_until.strftime('%H:%M')}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la autorización: {e}")
    def mostrar_historial(self):
        self._limpiar_pantalla()
        HistoryView(self.main_frame, self, BASE_DIR)

    def mostrar_archivos(self):
        self._limpiar_pantalla()
        FilesView(self.main_frame, self, BASE_DIR)
        
    def mostrar_auditoria(self): self._limpiar_pantalla(); AuditView(self.main_frame, self, BASE_DIR)

