import customtkinter as ctk
import os
import json
import uuid
from datetime import datetime
from tkinter import simpledialog, messagebox
from core.kardex_manager import KardexManager
from core.database import get_connection

class InboxView(ctk.CTkFrame):
    def __init__(self, parent, controller, base_dir):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.base_dir = base_dir
        self.modo = ctk.get_appearance_mode()
        self.pack(fill="both", expand=True)
        self._construir_inbox()

    def _construir_inbox(self):
        ctk.CTkLabel(self, text="Documentos Pendientes", font=("Segoe UI", 26, "bold"), text_color="#0F172A" if self.modo=="Light" else "white").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Audita y aprueba los documentos recien ingresados por los operarios.", font=("Segoe UI", 14), text_color="#64748B").pack(anchor="w", pady=(0, 20))

        split_frame = ctk.CTkFrame(self, fg_color="transparent")
        split_frame.pack(fill="both", expand=True)
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_columnconfigure(1, weight=2)

        lista_frame = ctk.CTkFrame(split_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        lista_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.filtro_var = ctk.StringVar(value="Guias de Remision")
        self.filtro_btn = ctk.CTkSegmentedButton(
            lista_frame, 
            values=["Guias de Remision", "Vales de Despacho", "Recetas"], 
            variable=self.filtro_var, 
            command=self._cargar_lista_pendientes
        )
        from ui.theme import Theme
        Theme.apply_segmented_button_style(self.filtro_btn)
        self.filtro_btn.pack(fill="x", padx=15, pady=15)

        self.scroll_pendientes = ctk.CTkScrollableFrame(lista_frame, fg_color="transparent")
        self.scroll_pendientes.pack(fill="both", expand=True, padx=5, pady=5)

        self.detalle_frame = ctk.CTkFrame(split_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        self.detalle_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self._cargar_lista_pendientes()

    def _cargar_lista_pendientes(self, *args):
        for widget in self.scroll_pendientes.winfo_children(): widget.destroy()
        for widget in self.detalle_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.detalle_frame, text="Seleccione un documento para revisar", font=("Segoe UI", 14, "italic"), text_color="#64748B").place(relx=0.5, rely=0.5, anchor="center")

        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            filtro_val = self.filtro_var.get()
            if filtro_val == "Guias de Remision":
                tipo = "Recepción"
            elif filtro_val == "Vales de Despacho":
                tipo = "Despacho"
            else:
                tipo = "Receta"
            
            cursor.execute('''
                SELECT * FROM document_history 
                WHERE status = 'Pendiente de Validación' AND doc_type = ?
            ''', (tipo,))
            
            pendientes = [dict(row) for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"Error cargando inbox SQLite: {e}")
            return

        if not pendientes:
            ctk.CTkLabel(self.scroll_pendientes, text="Bandeja limpia.", text_color="#10B981").pack(pady=40)
            return

        for doc in pendientes:
            item = ctk.CTkFrame(self.scroll_pendientes, fg_color="#F8FAFC" if self.modo == "Light" else "#0F172A", corner_radius=8, border_width=1, border_color="#E2E8F0")
            item.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(item, text=f"Doc: {doc.get('doc_number', 'S/N')}", font=("Segoe UI", 13, "bold"), text_color="#1565C0").pack(anchor="w", padx=10, pady=(10, 0))
            ctk.CTkLabel(item, text=f"Operario: {doc.get('user', 'Desconocido')}", font=("Segoe UI", 11)).pack(anchor="w", padx=10)
            ctk.CTkLabel(item, text=f"Fecha: {doc.get('date', '')}", font=("Segoe UI", 10), text_color="#64748B").pack(anchor="w", padx=10, pady=(0, 10))
            for widget in [item] + item.winfo_children():
                widget.bind("<Button-1>", lambda event, d=doc: self._ver_detalle_guia(d))
                widget.configure(cursor="hand2")

    def _ver_detalle_guia(self, doc):
        for widget in self.detalle_frame.winfo_children(): widget.destroy()
        header = ctk.CTkFrame(self.detalle_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        # Deserializar productos
        try:
            productos_doc = json.loads(doc.get('products', '[]'))
        except:
            productos_doc = []
            
        doc['detalles'] = productos_doc

        doc_type = doc.get("doc_type", "")
        is_recepcion = doc_type == "Recepción"

        ctk.CTkLabel(header, text=f"Documento N {doc.get('doc_number')}", font=("Segoe UI", 20, "bold"), text_color="#0F172A" if self.modo=="Light" else "white").pack(anchor="w")
        ctk.CTkLabel(header, text=f"{'Proveedor / Origen' if is_recepcion else 'Destino'}: {doc.get('origen_global', 'No especificado')}  |  Operario: {doc.get('user', 'Desconocido')}", font=("Segoe UI", 13)).pack(anchor="w", pady=(5, 0))
        ctk.CTkLabel(header, text=f"Observaciones del Operario: {doc.get('motivo_global', 'Ninguna observación')}", font=("Segoe UI", 12, "italic"), text_color="#64748B").pack(anchor="w", pady=(2, 5))

        cols_frame = ctk.CTkFrame(self.detalle_frame, fg_color="#F1F5F9" if self.modo=="Light" else "#0F172A", corner_radius=5)
        cols_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(cols_frame, text="Producto", font=("Segoe UI", 11, "bold"), width=120, anchor="w").grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(cols_frame, text="Cant.", font=("Segoe UI", 11, "bold"), width=50, anchor="center").grid(row=0, column=1, padx=2)
        
        if is_recepcion:
            ctk.CTkLabel(cols_frame, text="Costo U.", font=("Segoe UI", 11, "bold"), width=70, anchor="center").grid(row=0, column=2, padx=2)
            ctk.CTkLabel(cols_frame, text="Subtotal", font=("Segoe UI", 11, "bold"), width=70, anchor="center").grid(row=0, column=3, padx=2)
            ctk.CTkLabel(cols_frame, text="Vence", font=("Segoe UI", 11, "bold"), width=75, anchor="center").grid(row=0, column=4, padx=2)
            ctk.CTkLabel(cols_frame, text="Lote Interno", font=("Segoe UI", 11, "bold"), width=80, anchor="center").grid(row=0, column=5, padx=5)
        else:
            ctk.CTkLabel(cols_frame, text="Vence", font=("Segoe UI", 11, "bold"), width=75, anchor="center").grid(row=0, column=2, padx=2)
            ctk.CTkLabel(cols_frame, text="Lote Interno", font=("Segoe UI", 11, "bold"), width=80, anchor="center").grid(row=0, column=3, padx=5)

        scroll_det = ctk.CTkScrollableFrame(self.detalle_frame, fg_color="transparent", height=200)
        scroll_det.pack(fill="both", expand=True, padx=10, pady=5)

        total_doc = 0.0
        for item in doc.get("detalles", []):
            costo_u = item.get("costo_unitario", 0)
            cant = float(item.get("cantidad", 0))
            try:
                subtotal = float(costo_u) * cant
                costo_str = f"S/ {float(costo_u):.2f}"
                total_str = f"S/ {subtotal:.2f}"
                total_doc += subtotal
            except ValueError:
                costo_str = str(costo_u)
                total_str = "-"

            row = ctk.CTkFrame(scroll_det, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=item.get("producto", ""), width=120, anchor="w", font=("Segoe UI", 11)).grid(row=0, column=0, padx=5)
            ctk.CTkLabel(row, text=str(cant), width=50, anchor="center", font=("Segoe UI", 11)).grid(row=0, column=1, padx=2)
            
            if is_recepcion:
                ctk.CTkLabel(row, text=costo_str, width=70, anchor="center", font=("Segoe UI", 11)).grid(row=0, column=2, padx=2)
                ctk.CTkLabel(row, text=total_str, width=70, anchor="center", font=("Segoe UI", 11)).grid(row=0, column=3, padx=2)
                ctk.CTkLabel(row, text=item.get("vencimiento", "-"), width=75, anchor="center", font=("Segoe UI", 11)).grid(row=0, column=4, padx=2)
                ctk.CTkLabel(row, text=item.get("lote_asignado", ""), width=80, anchor="center", font=("Segoe UI", 11)).grid(row=0, column=5, padx=5)
                ctk.CTkButton(row, text="Corregir", font=("Segoe UI", 10, "bold"), width=60, fg_color="#F59E0B", text_color="#0F172A", hover_color="#D97706", command=lambda i=item, d=doc: self._corregir_silenciosamente(d, i)).grid(row=0, column=6, padx=5)
            else:
                ctk.CTkLabel(row, text=item.get("vencimiento", "-"), width=75, anchor="center", font=("Segoe UI", 11)).grid(row=0, column=2, padx=2)
                ctk.CTkLabel(row, text=item.get("lote_asignado", ""), width=80, anchor="center", font=("Segoe UI", 11)).grid(row=0, column=3, padx=5)
                ctk.CTkButton(row, text="Corregir", font=("Segoe UI", 10, "bold"), width=60, fg_color="#F59E0B", text_color="#0F172A", hover_color="#D97706", command=lambda i=item, d=doc: self._corregir_silenciosamente(d, i)).grid(row=0, column=4, padx=5)

        if is_recepcion and total_doc > 0:
            ctk.CTkLabel(scroll_det, text=f"Total Documento: S/ {total_doc:,.2f}", font=("Segoe UI", 15, "bold"), text_color="#1565C0").pack(anchor="e", pady=15, padx=20)

        btn_box = ctk.CTkFrame(self.detalle_frame, fg_color="transparent")
        btn_box.pack(fill="x", side="bottom", padx=20, pady=20)
        
        is_receta = doc.get('doc_type') == "Receta"
        is_vale = doc.get('doc_type') == "Despacho"
        
        if not is_receta and not is_vale:
            # Guía de Recepción tiene todos los botones
            ctk.CTkButton(btn_box, text="Anular (Extorno)", font=("Segoe UI", 12, "bold"), fg_color="transparent", border_width=1, border_color="#EF4444", text_color="#EF4444", hover_color="#FEE2E2", command=lambda: self._anular_guia(doc)).pack(side="left", padx=5)
            
        if not is_receta:
            # Vales y Guías tienen Observar
            ctk.CTkButton(btn_box, text="Observar (Notificar)", font=("Segoe UI", 12, "bold"), fg_color="#F59E0B", text_color="#0F172A", hover_color="#D97706", command=lambda: self._observar_guia(doc)).pack(side="left", padx=5)
            
        # Todos tienen Validar
        ctk.CTkButton(btn_box, text="Validar Conforme", font=("Segoe UI", 12, "bold"), fg_color="#10B981", hover_color="#059669", command=lambda: self._validar_guia(doc)).pack(side="right", padx=5)

    def _corregir_silenciosamente(self, doc, item):
        is_vale = doc.get('doc_type') == "Despacho"
        win_edit = ctk.CTkToplevel(self)
        win_edit.title("Correccion Maestra de Auditoria")
        win_edit.geometry("350x350")
        win_edit.grab_set()

        ctk.CTkLabel(win_edit, text=f"Editando: {item['producto']}", font=("Segoe UI", 15, "bold")).pack(pady=15)
        
        ctk.CTkLabel(win_edit, text="Cantidad Real:").pack(anchor="w", padx=20)
        entry_cant = ctk.CTkEntry(win_edit)
        entry_cant.insert(0, str(item['cantidad']))
        entry_cant.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(win_edit, text="Costo Unitario (S/):").pack(anchor="w", padx=20)
        entry_costo = ctk.CTkEntry(win_edit)
        entry_costo.insert(0, str(item.get('costo_unitario', '0')))
        entry_costo.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(win_edit, text="Vencimiento (AAAA-MM-DD):").pack(anchor="w", padx=20)
        entry_vence = ctk.CTkEntry(win_edit)
        entry_vence.insert(0, str(item.get('vencimiento', '-')))
        entry_vence.pack(fill="x", padx=20, pady=(0, 15))

        if is_vale:
            entry_costo.configure(state="disabled")
            entry_vence.configure(state="disabled")

        def guardar():
            try: n_cant = float(entry_cant.get().strip())
            except: return messagebox.showerror("Error", "Cantidad invalida.")
            
            n_costo = item.get('costo_unitario')
            n_vence = item.get('vencimiento')
            if not is_vale:
                try: n_costo = float(entry_costo.get().strip())
                except: return messagebox.showerror("Error", "Costo invalido.")
                n_vence = entry_vence.get().strip()

            item['cantidad'] = n_cant
            if not is_vale:
                item['costo_unitario'] = n_costo
                item['vencimiento'] = n_vence

            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE document_history SET products = ? WHERE id = ?", (json.dumps(doc['detalles']), doc['id']))
                conn.commit()
                conn.close()
                self.controller.mostrar_toast("Documento corregido en BD silenciosamente")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la corrección: {e}")
                return

            win_edit.destroy()
            self._ver_detalle_guia(doc)

        ctk.CTkButton(win_edit, text="Aplicar Corrección", font=("Segoe UI", 12, "bold"), fg_color="#F59E0B", text_color="#0F172A", hover_color="#D97706", command=guardar).pack(pady=10)

    def _validar_guia(self, doc):
        if not messagebox.askyesno("Confirmación", "El stock ingresará al kardex de cada producto.\n¿Está seguro?"): return
        
        is_vale = doc.get('doc_type') == "Despacho"

        for item in doc.get("detalles", []):
            km = KardexManager(item["producto"])
            # El KardexManager se encarga de guardar a la BD automáticamente cuando se usa procesar_*
            if is_vale:
                lote_id = item.get("lote_asignado", "S/C")
                km.register_exit(
                    fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    qty=item["cantidad"],
                    destino=doc.get("doc_number"),
                    user=doc.get("user"),
                    lote_id=lote_id,
                    concept="Despacho de Vale Validado"
                )
            else:
                lote_id = item.get("lote_asignado")
                if not lote_id: lote_id = str(uuid.uuid4())[:8].upper()
                venc = item.get("vencimiento")
                if not venc: venc = datetime.now().strftime("%Y-%m-%d")
                
                km.register_entry(
                    fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    qty=item["cantidad"],
                    unit_cost=item.get("costo_unitario", 0),
                    prov=doc.get("doc_number"),
                    venc=venc,
                    user=doc.get("user"),
                    lote_id=lote_id,
                    masivo=True,
                    guia=doc.get("doc_number"),
                    concept="Ingreso Masivo Validado"
                )

        self._cambiar_estado(doc, "Ingresado al Kardex" if not is_vale else "Despacho Efectuado")

    def _observar_guia(self, doc):
        motivo = simpledialog.askstring("Observar", "Ingrese el motivo del rechazo:")
        if not motivo: return
        self._notificar_operario(doc.get("user"), f"DOCUMENTO {doc.get('doc_number')} OBSERVADO:\nMotivo: {motivo}\nPor favor corregir y enviar de nuevo.")
        self._cambiar_estado(doc, "Observada por Admin")

    def _anular_guia(self, doc):
        if messagebox.askyesno("Anulación Definitiva", "Esta guía pasará al archivo muerto sin afectar stock.\n¿Anular?"):
            self._cambiar_estado(doc, "Anulada por Admin")
            self._notificar_operario(doc.get("user"), f"DOCUMENTO {doc.get('doc_number')} ANULADO definitivamente.")

    def _cambiar_estado(self, doc, nuevo_estado):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE document_history SET status = ? WHERE id = ?", (nuevo_estado, doc['id']))
            conn.commit()
            conn.close()
            self.controller.mostrar_toast(f"El documento fue: {nuevo_estado}")
            self._cargar_lista_pendientes()
        except Exception as e:
            messagebox.showerror("Error DB", str(e))

    def _notificar_operario(self, operario, mensaje):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notifications (user, message, date, status) VALUES (?, ?, ?, 'unread')", 
                           (operario, mensaje, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
        except Exception as e:
            print("Error enviando notificacion SQLite:", e)
