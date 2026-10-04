import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime

from core.database import get_connection

class MessageInboxWindow(ctk.CTkToplevel):
    def __init__(self, master, current_user, doc_reference=""):
        super().__init__(master)
        self.current_user = current_user
        self.doc_reference = doc_reference
        
        self.title("Bandeja de Mensajes y Solicitudes")
        self.geometry("800x600")
        self.grab_set()
        
        self.modo = ctk.get_appearance_mode()
        self.configure(fg_color="#F5F7FA" if self.modo == "Light" else "#0F172A")
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.filtro_var = ctk.StringVar(value="Redactar Solicitud")
        self.filtro_btn = ctk.CTkSegmentedButton(
            self, 
            values=["Redactar Solicitud", "Enviados", "Recibidos (Alertas)"], 
            variable=self.filtro_var, 
            command=self._switch_tab
        )
        from ui.components.theme import Theme
        Theme.apply_segmented_button_style(self.filtro_btn)
        self.filtro_btn.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.tab_compose = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.tab_sent = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.tab_inbox = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        for frame in (self.tab_compose, self.tab_sent, self.tab_inbox):
            frame.grid(row=0, column=0, sticky="nsew")
        
        self._setup_compose_tab()
        self._setup_sent_tab()
        self._setup_inbox_tab()
        
        if self.doc_reference:
            self.filtro_var.set("Redactar Solicitud")
        else:
            self.filtro_var.set("Recibidos (Alertas)")
        
        self._switch_tab(self.filtro_var.get())

    def _switch_tab(self, tab_name):
        self.tab_compose.grid_remove()
        self.tab_sent.grid_remove()
        self.tab_inbox.grid_remove()
        
        if tab_name == "Redactar Solicitud":
            self.tab_compose.grid()
        elif tab_name == "Enviados":
            self.tab_sent.grid()
        elif tab_name == "Recibidos (Alertas)":
            self.tab_inbox.grid()

    def _setup_compose_tab(self):
        container = ctk.CTkFrame(self.tab_compose, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=20)
        
        ctk.CTkLabel(container, text="Para: Administrador (Soporte y Autorizaciones)", font=("Segoe UI", 12, "bold"), text_color="#1565C0").pack(anchor="w", pady=(0, 10))
        
        ctk.CTkLabel(container, text="Documento de Referencia (Obligatorio para extornos):").pack(anchor="w")
        self.entry_doc = ctk.CTkEntry(container, width=300)
        self.entry_doc.insert(0, self.doc_reference)
        self.entry_doc.pack(anchor="w", pady=(0, 15))
        if self.doc_reference:
            self.entry_doc.configure(state="disabled")
            
        ctk.CTkLabel(container, text="Motivo:").pack(anchor="w")
        self.combo_motivo = ctk.CTkOptionMenu(container, values=[
            "Error de Digitación (Solicitud de Extorno)",
            "Aviso de Urgencia / Emergencia",
            "Insumo en mal estado / Merma",
            "Reporte General"
        ], width=300)
        self.combo_motivo.pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(container, text="Mensaje Detallado:").pack(anchor="w")
        self.text_body = ctk.CTkTextbox(container, height=150, fg_color="#F1F5F9" if self.modo == "Light" else "#0F172A", border_width=1, border_color="#E2E8F0")
        self.text_body.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(container, text="📤 Enviar Mensaje", font=("Segoe UI", 14, "bold"), fg_color="#1565C0", hover_color="#0F4787", command=self._enviar_mensaje).pack(anchor="e")

    def _enviar_mensaje(self):
        doc_ref = self.entry_doc.get().strip()
        motivo = self.combo_motivo.get()
        body = self.text_body.get("1.0", "end").strip()
        
        if not body:
            return messagebox.showerror("Error", "El cuerpo del mensaje no puede estar vacío.")
            
        if "Extorno" in motivo and not doc_ref:
            return messagebox.showerror("Error", "Para un extorno, es obligatorio indicar el Documento de Referencia.")
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (sender, receiver, doc_reference, reason, body, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, 'unread')
            """, (self.current_user, 'Administrador', doc_ref, motivo, body, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito", "Mensaje enviado al Administrador.")
            self.text_body.delete("1.0", "end")
            self._load_sent()
            self.tabview.set("Enviados")
        except Exception as e:
            messagebox.showerror("Error DB", f"No se pudo enviar el mensaje: {e}")

    def _setup_sent_tab(self):
        self.scroll_sent = ctk.CTkScrollableFrame(self.tab_sent, fg_color="transparent")
        self.scroll_sent.pack(fill="both", expand=True)
        self._load_sent()
        
    def _load_sent(self):
        for widget in self.scroll_sent.winfo_children():
            widget.destroy()
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages WHERE sender = ? ORDER BY id DESC", (self.current_user,))
            msgs = [dict(r) for r in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print("Error cargando enviados:", e)
            return
            
        if not msgs:
            ctk.CTkLabel(self.scroll_sent, text="No has enviado mensajes.").pack(pady=20)
            return
            
        for m in msgs:
            self._crear_tarjeta_mensaje(self.scroll_sent, m, is_inbox=False)

    def _setup_inbox_tab(self):
        self.scroll_inbox = ctk.CTkScrollableFrame(self.tab_inbox, fg_color="transparent")
        self.scroll_inbox.pack(fill="both", expand=True)
        self._load_inbox()
        
    def _load_inbox(self):
        for widget in self.scroll_inbox.winfo_children():
            widget.destroy()
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages WHERE receiver = ? ORDER BY id DESC", (self.current_user,))
            msgs = [dict(r) for r in cursor.fetchall()]
            
            # --- NUEVO: Marcar como leído y notificar al remitente (Administrador) ---
            updated = False
            for m in msgs:
                if m['status'] == 'unread':
                    cursor.execute("UPDATE messages SET status = 'read' WHERE id = ?", (m['id'],))
                    if m['sender'] == 'Administrador':
                        doc = m['doc_reference'] if m['doc_reference'] else "una consulta general"
                        alert_msg = f"El usuario {self.current_user} ha leído tu respuesta sobre {doc}."
                        cursor.execute("INSERT INTO notifications (user, message, date, status) VALUES (?, ?, ?, 'unread')",
                                       ('Administrador', alert_msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    updated = True
                    m['status'] = 'read' # Actualizar localmente para la UI
                    
            if updated:
                conn.commit()
            # -------------------------------------------------------------------------
            
            conn.close()
        except Exception as e:
            print("Error cargando inbox:", e)
            return
            
        if not msgs:
            ctk.CTkLabel(self.scroll_inbox, text="Bandeja vacía.").pack(pady=20)
            return
            
        for m in msgs:
            self._crear_tarjeta_mensaje(self.scroll_inbox, m, is_inbox=True)

    def _crear_tarjeta_mensaje(self, parent, m, is_inbox):
        card = ctk.CTkFrame(parent, fg_color="#F8FAFC" if self.modo=="Light" else "#1E293B", corner_radius=8, border_width=1, border_color="#E2E8F0" if self.modo=="Light" else "#334155")
        card.pack(fill="x", padx=10, pady=5)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        remitente = m['sender'] if is_inbox else f"Para: {m['receiver']}"
        
        status_color = "#10B981" if m['status'] == 'approved' else ("#EF4444" if m['status'] == 'rejected' else "#64748B")
        if m['status'] == 'CERRADO_Y_AUDITADO': status_color = "#8B5CF6"
        
        ctk.CTkLabel(header, text=f"{m['reason']} ({m['created_at']})", font=("Segoe UI", 12, "bold"), text_color="#1565C0").pack(side="left")
        ctk.CTkLabel(header, text=f"[{m['status'].upper()}]", font=("Segoe UI", 10, "bold"), text_color=status_color).pack(side="right")
        
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=10, pady=(0, 10))
        
        if m['doc_reference']:
            ctk.CTkLabel(body, text=f"Documento: {m['doc_reference']}", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        
        ctk.CTkLabel(body, text=m['body'], justify="left", wraplength=600).pack(anchor="w", pady=(5, 0))
