import customtkinter as ctk
import os
import json
import uuid
from datetime import datetime
from tkinter import simpledialog, messagebox
from core.database import get_connection

class AuditView(ctk.CTkFrame):
    def __init__(self, parent, controller, base_dir):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.base_dir = base_dir
        self.modo = ctk.get_appearance_mode()
        self.pack(fill="both", expand=True)

        top_panel = ctk.CTkFrame(self, fg_color="transparent")
        top_panel.pack(fill="x", pady=(0, 15))
        
        titulo_frame = ctk.CTkFrame(top_panel, fg_color="transparent")
        titulo_frame.pack(side="left")
        ctk.CTkLabel(titulo_frame, text="Auditoria de Operarios", font=("Segoe UI", 26, "bold"), text_color="#3B82F6").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(titulo_frame, text="Rastrea todos los movimientos y envia citaciones a operarios.", font=("Segoe UI", 14), text_color="#64748B").pack(anchor="w")

        from ui.theme import Theme
        ctk.CTkButton(top_panel, text="✍️ Redactar Memorandum General", font=("Segoe UI", 13, "bold"), fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER, height=45, command=self._abrir_redactor_general).pack(side="right", padx=10)
        ctk.CTkButton(top_panel, text="📊 Exportar Kardex a Excel", font=("Segoe UI", 13, "bold"), fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, height=45, command=self._exportar_kardex).pack(side="right", padx=10)

        # Controles de Zoom
        zoom_frame = ctk.CTkFrame(top_panel, fg_color="transparent")
        zoom_frame.pack(side="right", padx=10)
        
        self.font_size = 11
        ctk.CTkButton(zoom_frame, text="- Tamaño", width=60, height=30, fg_color="#64748B", hover_color="#475569", command=self.zoom_out).pack(side="left", padx=2)
        ctk.CTkButton(zoom_frame, text="+ Tamaño", width=60, height=30, fg_color="#64748B", hover_color="#475569", command=self.zoom_in).pack(side="left", padx=2)

        container = ctk.CTkFrame(self, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0" if self.modo=="Light" else "#334155")
        container.pack(fill="both", expand=True)

        # Botones de Acciones para Selección
        acciones_frame = ctk.CTkFrame(container, fg_color="transparent")
        acciones_frame.pack(fill="x", padx=10, pady=(15, 0))
        
        ctk.CTkLabel(acciones_frame, text="Acciones sobre el registro seleccionado:", font=("Segoe UI", 12, "italic"), text_color="#64748B").pack(side="left")
        self.btn_edit = ctk.CTkButton(acciones_frame, text="⚠️ Corregir Cantidad", width=140, height=30, font=("Segoe UI", 12, "bold"), fg_color=Theme.DANGER, hover_color=Theme.DANGER_HOVER, state="disabled", command=self._corregir_seleccion)
        self.btn_edit.pack(side="right", padx=5)
        self.btn_notif = ctk.CTkButton(acciones_frame, text="✉️ Enviar Mensaje", width=140, height=30, font=("Segoe UI", 12, "bold"), fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER, text_color="#FFFFFF", state="disabled", command=self._notificar_seleccion)
        self.btn_notif.pack(side="right", padx=5)

        # Treeview de Auditoría
        from tkinter import ttk
        self.style = ttk.Style()
        self.style.configure("Audit.Treeview", rowheight=35, font=("Segoe UI", self.font_size), background="#FFFFFF" if self.modo=="Light" else "#1E293B", foreground="#121212" if self.modo=="Light" else "#FFFFFF", fieldbackground="#FFFFFF" if self.modo=="Light" else "#1E293B", borderwidth=0)
        self.style.configure("Audit.Treeview.Heading", font=("Segoe UI", 12, "bold"), background="#F1F5F9" if self.modo=="Light" else "#0F172A", foreground="#1E293B" if self.modo=="Light" else "#FFFFFF")
        
        self.tree = ttk.Treeview(container, style="Audit.Treeview", show="headings", height=15)
        
        cols = ("ID", "Fecha y Hora", "Operario", "Operación", "Detalle", "Ext. H", "Documento", "Destino", "Producto", "Marca", "Lote", "Cant.", "Costo U.", "Vence")
        self.tree.configure(columns=cols)
        
        self.tree.heading("Detalle", text="Detalle / Motivo", anchor="w")
        self.tree.heading("Ext. H", text="Ext. H", anchor="center")
        self.tree.heading("Documento", text="Documento", anchor="w")
        self.tree.heading("Destino", text="Destino / Uso", anchor="w")
        self.tree.heading("Producto", text="Producto", anchor="w")
        self.tree.heading("Marca", text="Marca", anchor="w")
        self.tree.heading("Lote", text="Paquete/Lote", anchor="center")
        self.tree.heading("Cant.", text="Cant.", anchor="e")
        self.tree.heading("Costo U.", text="Costo U.", anchor="e")
        
        for col in cols:
            if col not in ["Detalle", "Ext. H", "Documento", "Destino", "Producto", "Marca", "Lote", "Cant.", "Costo U."]:
                self.tree.heading(col, text=col)
            
            if col == "ID":
                self.tree.column(col, width=0, stretch=False)
            elif col == "Destino":
                self.tree.column(col, width=120, minwidth=120, anchor="w", stretch=True)
            elif col == "Producto":
                self.tree.column(col, width=140, minwidth=140, anchor="w", stretch=True)
            elif col == "Marca":
                self.tree.column(col, width=110, minwidth=110, anchor="w", stretch=True)
            elif col == "Lote":
                self.tree.column(col, width=100, minwidth=100, anchor="center", stretch=True)
            elif col == "Cant.":
                self.tree.column(col, width=90, minwidth=90, anchor="e", stretch=True)
            elif col == "Costo U.":
                self.tree.column(col, width=80, minwidth=80, anchor="e", stretch=True)
            elif col == "Ext. H":
                self.tree.column(col, width=60, minwidth=60, anchor="center", stretch=True)
            else:
                self.tree.column(col, width=100, minwidth=100, anchor="center", stretch=True)

        scroll_y = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        scroll_y.pack(side="right", fill="y", pady=(5, 10), padx=(0, 10))
        scroll_x.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        self.tree.pack(fill="both", expand=True, padx=(10, 0), pady=(5, 0))

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        # Diccionario para guardar referencias de los objetos movimiento originales
        self.movimientos_data = {}

        self._cargar_auditoria()

    def zoom_in(self):
        if self.font_size < 18:
            self.font_size += 1
            self.style.configure("Audit.Treeview", font=("Segoe UI", self.font_size), rowheight=25 + (self.font_size - 9)*2)

    def zoom_out(self):
        if self.font_size > 8:
            self.font_size -= 1
            self.style.configure("Audit.Treeview", font=("Segoe UI", self.font_size), rowheight=25 + (self.font_size - 9)*2)

    def _exportar_kardex(self):
        ruta_salida = os.path.join(os.path.expanduser("~"), "Desktop", "Kardex_General_Movimientos.xlsx")
        try:
            import pandas as pd
            conn = get_connection()
            query = '''
                SELECT 
                    m.date as Fecha, 
                    p.name as Producto, 
                    c.name as Categoria,
                    CASE WHEN m.type IN ('E', 'SI') THEN 'Entrada' ELSE 'Salida' END as Operacion,
                    m.concept as Detalle, 
                    m.document as Documento, 
                    m.origin_dest as Origen_Destino, 
                    m.lot_code as Lote, 
                    m.qty as Cantidad, 
                    m.unit_cost as Costo_Unitario, 
                    m.total_cost as Costo_Total, 
                    m.balance_qty as Saldo_Cantidad, 
                    m.balance_total as Saldo_Total, 
                    m.user as Usuario
                FROM kardex_movements m
                LEFT JOIN products p ON m.product_id = p.id
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY m.id ASC
            '''
            df = pd.read_sql_query(query, conn)
            conn.close()
            df.to_excel(ruta_salida, index=False)
            messagebox.showinfo("Éxito", f"Kardex exportado exitosamente al Escritorio:\n{ruta_salida}")
        except Exception as e:
            messagebox.showerror("Error", f"Error exportando a Excel:\n{str(e)}")

    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel[0])
            m_id = item["values"][0]
            mov = self.movimientos_data.get(str(m_id))
            if mov:
                self.btn_edit.configure(state="normal")
                if mov['usuario'].lower() not in ["sistema", "invitado", "desconocido"]:
                    self.btn_notif.configure(state="normal")
                else:
                    self.btn_notif.configure(state="disabled")
        else:
            self.btn_edit.configure(state="disabled")
            self.btn_notif.configure(state="disabled")

    def _corregir_seleccion(self):
        sel = self.tree.selection()
        if sel:
            m_id = self.tree.item(sel[0])["values"][0]
            mov = self.movimientos_data.get(str(m_id))
            if mov:
                self._corregir_movimiento(mov)

    def _notificar_seleccion(self):
        sel = self.tree.selection()
        if sel:
            m_id = self.tree.item(sel[0])["values"][0]
            mov = self.movimientos_data.get(str(m_id))
            if mov:
                self._enviar_nota_rapida(mov)

    def _cargar_auditoria(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        movimientos = []
        self.movimientos_data.clear()
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.id as m_id, m.date, CASE WHEN m.user = 'Desconocido' THEN m.origin_dest ELSE m.user END as usuario, m.concept, m.type, p.name as producto, p.id as product_id,
                       m.qty, m.unit_cost, m.expiration_date, m.lot_code, m.out_of_hours, m.document, m.origin_dest
                FROM kardex_movements m
                JOIN products p ON m.product_id = p.id
                ORDER BY m.date DESC LIMIT 100
            ''')
            
            rows = cursor.fetchall()
            for row in rows:
                mov = {
                    "id": row['m_id'],
                    "product_id": row['product_id'],
                    "fecha": row['date'] or "Sin Fecha",
                    "usuario": row['usuario'] or "Sistema",
                    "concepto": row['concept'] or "",
                    "tipo": row['type'] or "",
                    "producto": row['producto'],
                    "cantidad": row['qty'] or 0,
                    "costo": row['unit_cost'] if row['unit_cost'] is not None else "-",
                    "vence": row['expiration_date'] or "-",
                    "lote_id": row['lot_code'] or "",
                    "out_of_hours": row['out_of_hours'] or 0,
                    "documento": row['document'] or "-",
                    "origin_dest": row['origin_dest'] or "-"
                }
                
                # Obtener Marca para salidas
                if mov['tipo'] == 'S':
                    mov['marca'] = "-"
                    cursor.execute("SELECT concept, origin_dest FROM kardex_movements WHERE lot_code = ? AND type IN ('E', 'SI') LIMIT 1", (mov['lote_id'],))
                    erow = cursor.fetchone()
                    if erow:
                        econcept = erow['concept'] or ""
                        if " (Marca: " in econcept:
                            mov['marca'] = econcept.split(" (Marca: ")[1].split(")")[0]
                        else:
                            mov['marca'] = erow['origin_dest'] or "-"
                
                movimientos.append(mov)
            
            conn.close()
        except Exception as e:
            print("Error cargando auditoría SQLite:", e)
                            
        def safe_date(date_str):
            try: return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except: return datetime.min
            
        movimientos.sort(key=lambda x: safe_date(x["fecha"]), reverse=True)

        for m in movimientos:
            self.movimientos_data[str(m["id"])] = m
            
            t = m["tipo"]
            concepto_raw = m['concepto']
            marca_str = "-"
            
            if " (Marca: " in concepto_raw and concepto_raw.endswith(")"):
                parts = concepto_raw.split(" (Marca: ")
                if len(parts) == 2:
                    concepto_raw = parts[0]
                    marca_str = parts[1][:-1]
            elif " (" in concepto_raw and concepto_raw.endswith(")"):
                parts = concepto_raw.split(" (")
                if len(parts) == 2:
                    concepto_raw = parts[1][:-1]
            
            if "Merma" in concepto_raw:
                tipo_mov = "Merma"
            elif t in ["E", "SI"]:
                tipo_mov = "Entrada"
            elif t == "S":
                tipo_mov = "Salida"
            else:
                tipo_mov = "-"
                
            destino_str = m['origin_dest']
            if t in ["E", "SI"]:
                if marca_str == "-":
                    marca_str = destino_str
                destino_str = "-"
            else:
                if marca_str == "-":
                    marca_str = m.get('marca', '-')
                
            ext_h_str = "⚠️" if m["out_of_hours"] == 1 else ""
            
            try: costo_str = f"S/ {float(m['costo']):.2f}"
            except ValueError: costo_str = str(m['costo'])

            qty = m['cantidad']
            if tipo_mov in ["Entrada", "Stock Inicial"]:
                qty_str = f"▲ {qty:,.2f}" if qty else "-"
                tipo_mov_lbl = "Ingreso" if tipo_mov == "Entrada" else "Stock Ini."
            elif tipo_mov in ["Salida", "Merma"]:
                qty_str = f"▼ {qty:,.2f}" if qty else "-"
                tipo_mov_lbl = tipo_mov.capitalize()
            else:
                qty_str = f"{qty:,.2f}" if qty else "-"
                tipo_mov_lbl = tipo_mov

            self.tree.insert("", "end", values=(
                m['id'],
                m['fecha'][:16] if len(m['fecha'])>16 else m['fecha'],
                m['usuario'],
                tipo_mov_lbl,
                concepto_raw,
                ext_h_str,
                m['documento'] or "-",
                destino_str,
                m['producto'],
                marca_str,
                m['lote_id'] or "-",
                qty_str,
                costo_str,
                m.get("vence", "-")
            ))

    def _corregir_movimiento(self, mov):
        win_edit = ctk.CTkToplevel(self)
        win_edit.title("Corregir Auditoría")
        win_edit.geometry("380x450")
        win_edit.grab_set()

        ctk.CTkLabel(win_edit, text=f"Editando: {mov['producto']}", font=("Segoe UI", 15, "bold")).pack(pady=15)

        ctk.CTkLabel(win_edit, text="Concepto / Motivo:").pack(anchor="w", padx=20)
        entry_concepto = ctk.CTkEntry(win_edit)
        entry_concepto.insert(0, mov['concepto'])
        entry_concepto.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(win_edit, text="Cantidad Real:").pack(anchor="w", padx=20)
        entry_cant = ctk.CTkEntry(win_edit)
        entry_cant.insert(0, str(mov['cant']))
        entry_cant.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(win_edit, text="Costo Unitario (S/):").pack(anchor="w", padx=20)
        entry_costo = ctk.CTkEntry(win_edit)
        entry_costo.insert(0, str(mov['costo']))
        entry_costo.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(win_edit, text="Vencimiento (AAAA-MM-DD):").pack(anchor="w", padx=20)
        entry_vence = ctk.CTkEntry(win_edit)
        entry_vence.insert(0, str(mov['vence']))
        entry_vence.pack(fill="x", padx=20, pady=(0, 15))

        is_salida = "Salida" in mov['concepto'] or "Despacho" in mov['concepto']
        if is_salida:
            entry_costo.configure(state="disabled")
            entry_vence.configure(state="disabled")

        def guardar():
            try: n_cant = float(entry_cant.get().strip())
            except: return messagebox.showerror("Error", "Cantidad inválida.")

            n_costo = mov['costo']
            n_vence = mov['vence']
            n_concepto = entry_concepto.get().strip()

            if not is_salida:
                try: n_costo = float(entry_costo.get().strip())
                except: return messagebox.showerror("Error", "Costo inválido.")
                n_vence = entry_vence.get().strip()

            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Update kardex_movements
                if not is_salida:
                    cursor.execute('''
                        UPDATE kardex_movements 
                        SET qty = ?, unit_cost = ?, expiration_date = ?, concept = ? 
                        WHERE id = ?
                    ''', (n_cant, n_costo, n_vence, n_concepto, mov['id']))
                else:
                    cursor.execute("UPDATE kardex_movements SET qty = ?, concept = ? WHERE id = ?", (n_cant, n_concepto, mov['id']))
                
                # Update lot if it exists
                if mov.get('lote_id'):
                    if not is_salida:
                        cursor.execute("UPDATE active_lots SET qty = ?, expiration_date = ? WHERE lot_code = ? AND product_id = ?", 
                                       (n_cant, n_vence, mov['lote_id'], mov['product_id']))
                    else:
                        cursor.execute("UPDATE active_lots SET qty = ? WHERE lot_code = ? AND product_id = ?", 
                                       (n_cant, mov['lote_id'], mov['product_id']))
                
                conn.commit()
                conn.close()
                self.controller.mostrar_toast("Corrección guardada en BD")
                win_edit.destroy()
                self._cargar_auditoria()
            except Exception as e:
                messagebox.showerror("Error DB", str(e))

        ctk.CTkButton(win_edit, text="Sobreescribir Registro", fg_color="#F59E0B", text_color="#0F172A", hover_color="#D97706", command=guardar).pack(fill="x", padx=20, pady=10)

    def _enviar_nota_rapida(self, mov):
        usuario = mov['usuario']
        motivo = simpledialog.askstring("Nota Rápida", f"Citación sobre {mov['producto']} ({mov['fecha']}):")
        if not motivo: return
        self._guardar_notificacion(usuario, f"REVISIÓN DE REGISTRO ('{mov['producto']}' el {mov['fecha']}):\n{motivo}")

    def _abrir_redactor_general(self):
        operarios_reales = []
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE role != 'admin' AND username != 'Invitado'")
            operarios_reales = [row['username'] for row in cursor.fetchall()]
            conn.close()
        except:
            pass

        if not operarios_reales:
            return messagebox.showwarning("Aviso", "No hay operarios registrados en el sistema de usuarios para notificar.")

        win_memo = ctk.CTkToplevel(self)
        win_memo.title("Redacción de Memorandum")
        win_memo.geometry("450x400")
        win_memo.grab_set()

        ctk.CTkLabel(win_memo, text="Memorándum Interno", font=("Segoe UI", 18, "bold"), text_color="#F59E0B").pack(pady=(20, 10))
        
        form_frame = ctk.CTkFrame(win_memo, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20)

        ctk.CTkLabel(form_frame, text="1. Seleccionar Operario:", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        combo_usr = ctk.CTkOptionMenu(form_frame, values=operarios_reales, height=35)
        combo_usr.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="2. Escribir Citación o Llamado de Atención:", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        txt_memo = ctk.CTkTextbox(form_frame, height=120, border_width=1, border_color="#E2E8F0" if self.modo=="Light" else "#334155")
        txt_memo.pack(fill="x", pady=(0, 20))

        def enviar():
            usr = combo_usr.get()
            mensaje = txt_memo.get("1.0", "end-1c").strip()
            
            if not mensaje:
                return messagebox.showerror("Error", "El memorándum no puede estar vacío.")
                
            self._guardar_notificacion(usr, f"MEMORÁNDUM GENERAL:\n\n{mensaje}")
            win_memo.destroy()
            self.controller.mostrar_toast(f"Memorándum despachado a {usr}")

        ctk.CTkButton(form_frame, text="Enviar a Bandeja del Operario", font=("Segoe UI", 13, "bold"), fg_color="#F59E0B", text_color="#0F172A", hover_color="#D97706", height=45, command=enviar).pack(fill="x")

    def _guardar_notificacion(self, usuario, mensaje_completo):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notifications (user, message, date, status) VALUES (?, ?, ?, 'unread')", 
                           (usuario, mensaje_completo, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            self.controller.mostrar_toast(f"Notificación enviada a {usuario}", color_fondo="#F59E0B")
        except Exception as e:
            print("Error enviando notificacion SQLite:", e)