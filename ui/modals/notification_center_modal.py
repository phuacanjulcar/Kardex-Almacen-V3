import customtkinter as ctk
from tkinter import messagebox
from core.database import get_connection

class NotificationCenterModal(ctk.CTkToplevel):
    def __init__(self, master, current_user, metrics, callbacks):
        super().__init__(master)
        self.current_user = current_user
        self.metrics = metrics
        self.callbacks = callbacks
        
        self.title("🔔 Centro de Notificaciones")
        self.geometry("450x550")
        self.transient(master)
        self.grab_set()
        
        self.modo = ctk.get_appearance_mode()
        self.configure(fg_color="#F8FAFC" if self.modo == "Light" else "#0F172A")
        
        ctk.CTkLabel(self, text="Centro de Notificaciones", font=("Segoe UI", 18, "bold"), text_color="#1565C0").pack(pady=(20, 10))
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        has_items = False
        
        if self.metrics.get("docs", 0) > 0:
            self._crear_tarjeta(
                "📑 Documentos Pendientes", 
                f"Tienes {self.metrics['docs']} documento(s) pendiente(s) de validación.", 
                "Revisar Documentos", 
                "#EF4444", 
                self._handle_docs
            )
            has_items = True
            
        if self.metrics.get("msgs", 0) > 0:
            self._crear_tarjeta(
                "✉️ Mensajes y Réplicas", 
                f"Tienes {self.metrics['msgs']} mensaje(s) nuevo(s) sin leer.", 
                "Abrir Bandeja", 
                "#8B5CF6", 
                self._handle_msgs
            )
            has_items = True
            
        if self.metrics.get("alerts", 0) > 0:
            self._crear_tarjeta(
                "🔔 Alertas del Sistema", 
                f"Tienes {self.metrics['alerts']} notificación(es) del sistema (Lecturas, avisos).", 
                "Ver Alertas", 
                "#F57C00", 
                self._handle_alerts
            )
            has_items = True
            
        if self.metrics.get("moves", 0) > 0:
            self._crear_tarjeta(
                "📦 Movimientos de Hoy", 
                f"Se han registrado {self.metrics['moves']} movimiento(s) de inventario el día de hoy.", 
                "Ver Auditoría", 
                "#2E7D32", 
                self._handle_moves
            )
            has_items = True
            
        if not has_items:
            ctk.CTkLabel(self.scroll, text="Todo está al día. No hay notificaciones nuevas.", font=("Segoe UI", 14), text_color="#64748B").pack(pady=40)
            
        ctk.CTkButton(self, text="Cerrar", font=("Segoe UI", 14), fg_color="#E2E8F0" if self.modo=="Light" else "#334155", text_color="#1E293B" if self.modo=="Light" else "#FFFFFF", hover_color="#CBD5E1" if self.modo=="Light" else "#475569", command=self.destroy).pack(pady=20)

    def _crear_tarjeta(self, titulo, subtitulo, txt_boton, color_tema, comando):
        card = ctk.CTkFrame(self.scroll, fg_color="#FFFFFF" if self.modo=="Light" else "#1E293B", corner_radius=12, border_width=1, border_color="#E2E8F0" if self.modo=="Light" else "#334155")
        card.pack(fill="x", pady=10)
        
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(top, text=titulo, font=("Segoe UI", 14, "bold"), text_color=color_tema).pack(side="left")
        
        ctk.CTkLabel(card, text=subtitulo, font=("Segoe UI", 12), text_color="#475569" if self.modo=="Light" else "#94A3B8", justify="left", wraplength=350).pack(anchor="w", padx=15, pady=(0, 15))
        
        ctk.CTkButton(card, text=txt_boton, font=("Segoe UI", 12, "bold"), fg_color="transparent", border_width=1, border_color=color_tema, text_color=color_tema, command=comando).pack(anchor="e", padx=15, pady=(0, 15))

    def _handle_docs(self):
        self.destroy()
        self.callbacks.get("docs")()
        
    def _handle_msgs(self):
        self.destroy()
        self.callbacks.get("msgs")()
        
    def _handle_moves(self):
        self.destroy()
        self.callbacks.get("moves")()
        
    def _handle_alerts(self):
        # Leer las alertas directamente, mostrarlas y marcarlas como leídas.
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, message, date FROM notifications WHERE user = 'Administrador' AND status = 'unread' ORDER BY id DESC")
            rows = cursor.fetchall()
            
            if not rows:
                messagebox.showinfo("Alertas", "No hay alertas nuevas.")
            else:
                alertas_txt = ""
                ids_to_update = []
                for r in rows:
                    alertas_txt += f"• {r['message']} ({r['date']})\n\n"
                    ids_to_update.append(str(r['id']))
                
                # Mostrar el popup
                messagebox.showinfo("Alertas del Sistema", alertas_txt)
                
                # Marcar como leídas
                if ids_to_update:
                    placeholders = ",".join(["?"] * len(ids_to_update))
                    cursor.execute(f"UPDATE notifications SET status = 'read' WHERE id IN ({placeholders})", ids_to_update)
                    conn.commit()
            conn.close()
            
            # Recargar panel
            self.destroy()
            self.callbacks.get("refresh")()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las alertas: {e}")
