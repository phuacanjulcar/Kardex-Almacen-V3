import customtkinter as ctk
import os
import json
from core.database import get_connection

class HistoryView(ctk.CTkFrame):
    def __init__(self, parent, controller, base_dir):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.base_dir = base_dir
        self.modo = ctk.get_appearance_mode()
        self.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self, text="Documentos Observados", font=("Segoe UI", 26, "bold"), text_color="#EF4444").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Seguimiento de documentos rechazados o anulados del sistema.", font=("Segoe UI", 14), text_color="#64748B").pack(anchor="w", pady=(0, 20))
        
        split_frame = ctk.CTkFrame(self, fg_color="transparent")
        split_frame.pack(fill="both", expand=True)
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_columnconfigure(1, weight=2)

        lista_frame = ctk.CTkFrame(split_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        lista_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.filtro_var = ctk.StringVar(value="Guias de Remision")
        self.filtro_btn = ctk.CTkSegmentedButton(
            lista_frame, 
            values=["Guias de Remision", "Vales de Despacho"], 
            variable=self.filtro_var, 
            command=self._cargar_lista
        )
        from ui.components.theme import Theme
        Theme.apply_segmented_button_style(self.filtro_btn)
        self.filtro_btn.pack(fill="x", padx=15, pady=15)

        self.scroll_pendientes = ctk.CTkScrollableFrame(lista_frame, fg_color="transparent")
        self.scroll_pendientes.pack(fill="both", expand=True, padx=5, pady=5)

        self.detalle_frame = ctk.CTkFrame(split_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        self.detalle_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self._cargar_lista()

    def _cargar_lista(self, *args):
        for widget in self.scroll_pendientes.winfo_children(): widget.destroy()
        for widget in self.detalle_frame.winfo_children(): widget.destroy()
        
        ctk.CTkLabel(self.detalle_frame, text="Seleccione un registro historico para ver el detalle", font=("Segoe UI", 14, "italic"), text_color="#64748B").place(relx=0.5, rely=0.5, anchor="center")

        try:
            conn = get_connection()
            cursor = conn.cursor()
            tipo = "Recepción" if self.filtro_var.get() == "Guias de Remision" else "Despacho"
            
            cursor.execute('''
                SELECT * FROM document_history 
                WHERE status IN ('Observada por Admin', 'Anulada por Admin') AND doc_type = ?
                ORDER BY date DESC
            ''', (tipo,))
            
            pendientes = [dict(row) for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"Error cargando historial SQLite: {e}")
            return
            
        for doc in pendientes:
            item = ctk.CTkFrame(self.scroll_pendientes, fg_color="#FEF2F2", corner_radius=8, border_width=1, border_color="#EF4444")
            item.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(item, text=f"Doc: {doc.get('doc_number', 'S/N')}", font=("Segoe UI", 13, "bold"), text_color="#B91C1C").pack(anchor="w", padx=10, pady=(10, 0))
            ctk.CTkLabel(item, text=f"Estado: {doc.get('status')}", font=("Segoe UI", 11, "bold"), text_color="#7F1D1D").pack(anchor="w", padx=10, pady=(0, 5))
            ctk.CTkLabel(item, text=f"Fecha: {doc.get('date', '')}", font=("Segoe UI", 10), text_color="#64748B").pack(anchor="w", padx=10, pady=(0, 10))
            for widget in [item] + item.winfo_children():
                widget.bind("<Button-1>", lambda event, d=doc: self._ver_detalle(d))
                widget.configure(cursor="hand2")

    def _ver_detalle(self, doc):
        for widget in self.detalle_frame.winfo_children(): widget.destroy()
        header = ctk.CTkFrame(self.detalle_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        try:
            productos_doc = json.loads(doc.get('products', '[]'))
        except:
            productos_doc = []
            
        ctk.CTkLabel(header, text=f"Documento N {doc.get('doc_number')}", font=("Segoe UI", 20, "bold"), text_color="#0F172A" if self.modo=="Light" else "white").pack(anchor="w")
        ctk.CTkLabel(header, text=f"Operario: {doc.get('user', 'Desconocido')} | Estado: {doc.get('status')}", font=("Segoe UI", 13)).pack(anchor="w", pady=(5, 0))

        cols_frame = ctk.CTkFrame(self.detalle_frame, fg_color="#F1F5F9" if self.modo=="Light" else "#0F172A", corner_radius=5)
        cols_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(cols_frame, text="Producto", font=("Segoe UI", 11, "bold"), width=120, anchor="w").grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(cols_frame, text="Cant.", font=("Segoe UI", 11, "bold"), width=50, anchor="center").grid(row=0, column=1, padx=2)
        ctk.CTkLabel(cols_frame, text="Costo U.", font=("Segoe UI", 11, "bold"), width=70, anchor="center").grid(row=0, column=2, padx=2)
        ctk.CTkLabel(cols_frame, text="Subtotal", font=("Segoe UI", 11, "bold"), width=70, anchor="center").grid(row=0, column=3, padx=2)

        scroll_det = ctk.CTkScrollableFrame(self.detalle_frame, fg_color="transparent", height=200)
        scroll_det.pack(fill="both", expand=True, padx=10, pady=5)

        total_doc = 0.0
        for item in productos_doc:
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
            ctk.CTkLabel(row, text=costo_str, width=70, anchor="center", font=("Segoe UI", 11)).grid(row=0, column=2, padx=2)
            ctk.CTkLabel(row, text=total_str, width=70, anchor="center", font=("Segoe UI", 11)).grid(row=0, column=3, padx=2)

        if total_doc > 0:
            ctk.CTkLabel(scroll_det, text=f"Total Documento: S/ {total_doc:,.2f}", font=("Segoe UI", 15, "bold"), text_color="#1565C0").pack(anchor="e", pady=15, padx=20)
            
        if doc.get('status') != "Anulada por Admin":
            ctk.CTkButton(self.detalle_frame, text="Permitir Reenvio (Devolver a Pendiente)", font=("Segoe UI", 12, "bold"), fg_color="#3B82F6", hover_color="#2563EB", command=lambda: self._devolver_a_pendiente(doc)).pack(side="bottom", pady=20, padx=20)
            
    def _devolver_a_pendiente(self, doc):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE document_history SET status = 'Pendiente de Validación' WHERE id = ?", (doc['id'],))
            cursor.execute("INSERT INTO notifications (user, message, date, status) VALUES (?, ?, ?, 'unread')", 
                           (doc.get("user"), f"DOCUMENTO {doc.get('doc_number')} ha sido liberado para reenviar.", "hoy"))
            conn.commit()
            conn.close()
            self.controller.mostrar_toast("Documento devuelto a Pendientes")
            self._cargar_lista()
        except Exception as e:
            print("Error devolviendo documento", e)
