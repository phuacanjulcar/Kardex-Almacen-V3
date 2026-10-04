import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from core.database import get_connection

class AdminMessageInboxView(ctk.CTkFrame):
    def __init__(self, parent, controller, base_dir):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.base_dir = base_dir
        self.modo = ctk.get_appearance_mode()
        self.pack(fill="both", expand=True)
        self._construir_inbox()

    def _construir_inbox(self):
        ctk.CTkLabel(self, text="Bandeja de Mensajes y Alertas", font=("Segoe UI", 26, "bold"), text_color="#0F172A" if self.modo=="Light" else "white").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Gestiona solicitudes de extorno, mensajes de usuarios y alertas del sistema.", font=("Segoe UI", 14), text_color="#64748B").pack(anchor="w", pady=(0, 20))

        split_frame = ctk.CTkFrame(self, fg_color="transparent")
        split_frame.pack(fill="both", expand=True)
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_columnconfigure(1, weight=2)

        lista_frame = ctk.CTkFrame(split_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        lista_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.filtro_var = ctk.StringVar(value="Bandeja de Entrada")
        self.filtro_btn = ctk.CTkSegmentedButton(
            lista_frame, 
            values=["Bandeja de Entrada", "Extornos Pendientes", "Alertas Sistema"], 
            variable=self.filtro_var, 
            command=self._cargar_mensajes
        )
        from ui.components.theme import Theme
        Theme.apply_segmented_button_style(self.filtro_btn)
        self.filtro_btn.pack(fill="x", padx=15, pady=15)

        self.scroll_mensajes = ctk.CTkScrollableFrame(lista_frame, fg_color="transparent")
        self.scroll_mensajes.pack(fill="both", expand=True, padx=5, pady=5)

        self.detalle_frame = ctk.CTkFrame(split_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        self.detalle_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self._cargar_mensajes()

    def _cargar_mensajes(self, *args):
        for widget in self.scroll_mensajes.winfo_children(): widget.destroy()
        for widget in self.detalle_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.detalle_frame, text="Seleccione un mensaje para leer", font=("Segoe UI", 14, "italic"), text_color="#64748B").place(relx=0.5, rely=0.5, anchor="center")

        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            filtro_val = self.filtro_var.get()
            if filtro_val == "Bandeja de Entrada":
                cursor.execute("SELECT * FROM messages WHERE receiver = 'Administrador' AND sender != 'SISTEMA' AND reason NOT LIKE '%Extorno%' ORDER BY id DESC")
            elif filtro_val == "Extornos Pendientes":
                cursor.execute("SELECT * FROM messages WHERE receiver = 'Administrador' AND reason LIKE '%Extorno%' ORDER BY status ASC, id DESC")
            else:
                cursor.execute("SELECT * FROM messages WHERE receiver = 'Administrador' AND sender = 'SISTEMA' ORDER BY id DESC")
            
            mensajes = [dict(row) for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"Error cargando inbox admin: {e}")
            return

        if not mensajes:
            ctk.CTkLabel(self.scroll_mensajes, text="Bandeja limpia.", text_color="#10B981").pack(pady=40)
            return

        for msg in mensajes:
            item = ctk.CTkFrame(self.scroll_mensajes, fg_color="#F8FAFC" if self.modo == "Light" else "#0F172A", corner_radius=8, border_width=1, border_color="#E2E8F0")
            item.pack(fill="x", pady=5, padx=5)
            
            status = msg.get('status', '')
            color_txt = "#1565C0" if status == 'unread' else "#64748B"
            
            ctk.CTkLabel(item, text=f"{msg.get('sender', '')} - {msg.get('reason', '')}", font=("Segoe UI", 13, "bold"), text_color=color_txt).pack(anchor="w", padx=10, pady=(10, 0))
            if msg.get('doc_reference'):
                ctk.CTkLabel(item, text=f"Doc: {msg.get('doc_reference')}", font=("Segoe UI", 11)).pack(anchor="w", padx=10)
            ctk.CTkLabel(item, text=f"Fecha: {msg.get('created_at', '')}", font=("Segoe UI", 10), text_color="#64748B").pack(anchor="w", padx=10, pady=(0, 10))
            
            for widget in [item] + item.winfo_children():
                widget.bind("<Button-1>", lambda event, m=msg: self._ver_detalle(m))
                widget.configure(cursor="hand2")

    def _ver_detalle(self, msg):
        for widget in self.detalle_frame.winfo_children(): widget.destroy()
        
        # Marcar como leído si está unread
        if msg['status'] == 'unread':
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE messages SET status = 'read' WHERE id = ?", (msg['id'],))
                conn.commit()
                conn.close()
                msg['status'] = 'read'
                self._cargar_mensajes()
            except: pass

        header = ctk.CTkFrame(self.detalle_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(header, text=msg.get('reason'), font=("Segoe UI", 20, "bold"), text_color="#0F172A" if self.modo=="Light" else "white").pack(anchor="w")
        ctk.CTkLabel(header, text=f"De: {msg.get('sender')}  |  Fecha: {msg.get('created_at')}", font=("Segoe UI", 13)).pack(anchor="w", pady=(5, 0))
        
        if msg.get('doc_reference'):
            ctk.CTkLabel(header, text=f"Referencia: {msg.get('doc_reference')}", font=("Segoe UI", 13, "bold"), text_color="#F59E0B").pack(anchor="w", pady=(5, 0))

        status_lbl = ctk.CTkLabel(header, text=f"Estado: {msg.get('status').upper()}", font=("Segoe UI", 12, "bold"))
        status_lbl.pack(anchor="w", pady=(5, 0))

        body_frame = ctk.CTkFrame(self.detalle_frame, fg_color="#F1F5F9" if self.modo=="Light" else "#0F172A", corner_radius=5)
        body_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        ctk.CTkLabel(body_frame, text=msg.get('body'), font=("Segoe UI", 14), justify="left", wraplength=450).pack(anchor="nw", padx=15, pady=15)

        # Botones de acción
        btn_box = ctk.CTkFrame(self.detalle_frame, fg_color="transparent")
        btn_box.pack(fill="x", side="bottom", padx=20, pady=20)

        if msg['status'] in ['read', 'unread']:
            if "Extorno" in msg.get('reason'):
                ctk.CTkButton(btn_box, text="Rechazar Extorno", font=("Segoe UI", 12, "bold"), fg_color="transparent", border_width=1, border_color="#EF4444", text_color="#EF4444", hover_color="#FEE2E2", command=lambda: self._responder(msg, 'rejected')).pack(side="left", padx=5)
                ctk.CTkButton(btn_box, text="Aprobar Extorno (Generar Contracuenta)", font=("Segoe UI", 12, "bold"), fg_color="#10B981", hover_color="#059669", command=lambda: self._aprobar_extorno(msg)).pack(side="right", padx=5)
            else:
                ctk.CTkButton(btn_box, text="Responder", font=("Segoe UI", 12, "bold"), fg_color="#1565C0", hover_color="#0F4787", command=lambda: self._responder(msg, 'read')).pack(side="right", padx=5)
        else:
            ctk.CTkLabel(btn_box, text="Este mensaje ha sido CERRADO Y AUDITADO, es inmutable.", font=("Segoe UI", 12, "italic"), text_color="#8B5CF6").pack()

    def _responder(self, msg, new_status):
        import tkinter.simpledialog as sd
        respuesta = sd.askstring("Responder", "Escribe tu respuesta al usuario:")
        if not respuesta: return
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Enviar mensaje al usuario
            cursor.execute("""
                INSERT INTO messages (sender, receiver, doc_reference, reason, body, created_at, status, reply_to_id)
                VALUES (?, ?, ?, ?, ?, ?, 'unread', ?)
            """, ('Administrador', msg['sender'], msg['doc_reference'], f"Re: {msg['reason']}", respuesta, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg['id']))
            
            if new_status == 'rejected':
                cursor.execute("UPDATE messages SET status = 'CERRADO_Y_AUDITADO' WHERE id = ?", (msg['id'],))
            
            conn.commit()
            conn.close()
            self.controller.mostrar_toast("Respuesta enviada.")
            self._cargar_mensajes()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _aprobar_extorno(self, msg):
        if not messagebox.askyesno("Confirmar Extorno", "Se generará una contracuenta automática en el Kardex y el hilo será inmutable.\n¿Proceder?"):
            return
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            doc_ref = msg['doc_reference']
            if doc_ref:
                # Buscar movimientos originales
                cursor.execute("SELECT * FROM kardex_movements WHERE document = ? OR origin_dest = ?", (doc_ref, doc_ref))
                movs = cursor.fetchall()
                
                for m in movs:
                    nuevo_tipo = 'S' if m['type'] in ['E', 'SI'] else 'E'
                    nuevo_concepto = f"EXTORNO AUTO ({doc_ref})"
                    
                    cursor.execute('''
                        INSERT INTO kardex_movements (product_id, date, lot_code, type, concept, document, origin_dest, expiration_date, qty, unit_cost, user)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (m['product_id'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), m['lot_code'], nuevo_tipo, nuevo_concepto, f"EXT-{doc_ref}", "SISTEMA", m['expiration_date'], m['qty'], m['unit_cost'], 'Admin'))
            
            # Marcar inmutable
            cursor.execute("UPDATE messages SET status = 'CERRADO_Y_AUDITADO' WHERE id = ?", (msg['id'],))
            
            # Avisar al usuario
            cursor.execute("""
                INSERT INTO messages (sender, receiver, doc_reference, reason, body, created_at, status, reply_to_id)
                VALUES (?, ?, ?, ?, ?, ?, 'unread', ?)
            """, ('Administrador', msg['sender'], msg['doc_reference'], "Extorno Aprobado", "El Administrador ha aprobado el extorno y se ha generado la contracuenta.", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg['id']))
            
            conn.commit()
            conn.close()
            self.controller.mostrar_toast("Extorno aprobado e inmutable.")
            self._cargar_mensajes()
        except Exception as e:
            messagebox.showerror("Error", str(e))
