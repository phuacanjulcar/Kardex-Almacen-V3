import customtkinter as ctk
import os
import json
import csv
import threading
from tkinter import messagebox
from ui.modals.cloud_sync_modal import CloudSyncModal
from core.services.cloud_sync import NeonSyncEngine

class FilesView(ctk.CTkFrame):
    def __init__(self, parent, controller, base_dir):
        super().__init__(parent, fg_color="transparent")
        self.base_dir = base_dir
        self.kardex_dir = os.path.join(base_dir, "data", "kardex_files")
        self.modo = ctk.get_appearance_mode()
        self.pack(fill="both", expand=True)
        
        txt_main = "#0F172A" if self.modo=="Light" else "#FFFFFF"
        ctk.CTkLabel(self, text="Archivos Generales (Guías y Vales)", font=("Segoe UI", 26, "bold"), text_color=txt_main).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Compilación histórica de todos los documentos emitidos (Entradas y Salidas).", font=("Segoe UI", 14), text_color="#64748B").pack(anchor="w", pady=(0, 20))

        # Controles
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(ctrl_frame, text="Exportar Maestro CSV", font=("Segoe UI", 12, "bold"), fg_color="#107C41", hover_color="#0B5A2B", command=self._exportar_csv).pack(side="right", padx=5)
        ctk.CTkButton(ctrl_frame, text="Exportar Documentos Excel", font=("Segoe UI", 12, "bold"), fg_color="#107C41", hover_color="#0B5A2B", command=self._exportar_historial_excel).pack(side="right", padx=5)
        ctk.CTkButton(ctrl_frame, text="📄 Imprimir PDF Seleccionado", font=("Segoe UI", 12, "bold"), fg_color="#D32F2F", hover_color="#B71C1C", command=self._imprimir_pdf).pack(side="left", padx=5)
        
        # Boton Nube
        self.btn_restaurar = ctk.CTkButton(ctrl_frame, text="☁️ Restaurar Backup Nube", font=("Segoe UI", 12, "bold"), fg_color="#F59E0B", hover_color="#D97706", text_color="white", command=self._confirmar_restauracion)
        self.btn_restaurar.pack(side="left", padx=15)
        
        # Tabla
        table_frame = ctk.CTkFrame(self, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0" if self.modo=="Light" else "#334155")
        table_frame.pack(fill="both", expand=True)

        from tkinter import ttk
        style = ttk.Style()
        style.configure("Hist.Treeview", rowheight=35, font=("Segoe UI", 11), background="#FFFFFF" if self.modo=="Light" else "#1E293B", foreground="#121212" if self.modo=="Light" else "#FFFFFF", fieldbackground="#FFFFFF" if self.modo=="Light" else "#1E293B", borderwidth=0)
        style.configure("Hist.Treeview.Heading", font=("Segoe UI", 12, "bold"), background="#F1F5F9" if self.modo=="Light" else "#0F172A", foreground="#1E293B" if self.modo=="Light" else "#FFFFFF")

        cols = ("ID", "Fecha", "Tipo", "N° Doc", "Usuario", "Origen/Destino", "Motivo", "Estado")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", style="Hist.Treeview")
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Fecha", width=120, anchor="center")
        self.tree.column("Tipo", width=100, anchor="center")
        self.tree.column("N° Doc", width=120, anchor="center")
        self.tree.column("Usuario", width=100, anchor="center")
        self.tree.column("Origen/Destino", width=150, anchor="w")
        self.tree.column("Motivo", width=200, anchor="w")
        self.tree.column("Estado", width=100, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.cargar_datos()
        
    def cargar_datos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, date, doc_type, doc_number, user, origen_global, motivo_global, status 
                FROM document_history 
                WHERE status != 'Pendiente de Validación'
                ORDER BY id DESC
            ''')
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=(
                    row['id'],
                    row['date'][:16],
                    row['doc_type'],
                    row['doc_number'],
                    row['user'],
                    row['origen_global'] or "-",
                    row['motivo_global'] or "-",
                    row['status']
                ))
            conn.close()
        except Exception as e:
            print("Error cargando historial de documentos:", e)

    def _exportar_historial_excel(self):
        ruta_salida = os.path.join(os.path.expanduser("~"), "Desktop", "Historial_Documentos.xlsx")
        try:
            import pandas as pd
            from core.database import get_connection
            conn = get_connection()
            df = pd.read_sql_query('''
                SELECT id, date as Fecha, doc_type as Tipo, doc_number as Documento, user as Usuario, origen_global as Origen_Destino, motivo_global as Motivo, status as Estado 
                FROM document_history 
                WHERE status != 'Pendiente de Validación'
                ORDER BY id DESC
            ''', conn)
            conn.close()
            df.to_excel(ruta_salida, index=False)
            messagebox.showinfo("Exportar", f"Historial de Documentos exportado en el Escritorio:\n{ruta_salida}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {e}")

    def _confirmar_restauracion(self):
        if messagebox.askyesno("Confirmar Restauración", "⚠️ ADVERTENCIA: Esta acción descargará toda la base de datos desde Neon (Nube) y sobreescribirá los datos locales actuales. ¿Estás seguro que deseas continuar?"):
            self._iniciar_restauracion()

    def _iniciar_restauracion(self):
        self.btn_restaurar.configure(state="disabled", text="Descargando...")
        
        def restore_thread():
            engine = NeonSyncEngine()
            def cb(pct, msg): pass # Silencioso por ahora, o podríamos usar toast
            ok, msg = engine.restore_data(progress_callback=cb)
            
            self.after(0, lambda: self._finalizar_restauracion(ok, msg))
            
        threading.Thread(target=restore_thread, daemon=True).start()

    def _finalizar_restauracion(self, ok, msg):
        self.btn_restaurar.configure(state="normal", text="☁️ Restaurar Backup Nube")
        if ok:
            messagebox.showinfo("Éxito", "La base de datos fue restaurada exitosamente desde la nube.")
            self.cargar_datos()
        else:
            messagebox.showerror("Error", f"Error durante la restauración:\n{msg}")

    def _exportar_csv(self):
        ruta_salida = os.path.join(os.path.expanduser("~"), "Desktop", "Reporte_Inventario_Maestro.csv")
        try:
            with open(ruta_salida, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';') 
                writer.writerow(["Producto", "Categoria", "Ubicacion", "Unidad", "Stock Actual", "Costo Total (S/)"])
                
                try:
                    from core.database import get_connection
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT p.name as Producto, c.name as Categoria, z.name as Ubicacion, p.unit as Unidad,
                               COALESCE(SUM(l.qty), 0) as stock, COALESCE(SUM(l.qty * l.unit_cost), 0) as costo_total
                        FROM products p
                        LEFT JOIN categories c ON p.category_id = c.id
                        LEFT JOIN zones z ON p.zone_id = z.id
                        LEFT JOIN active_lots l ON p.id = l.product_id
                        GROUP BY p.id
                    ''')
                    for row in cursor.fetchall():
                        writer.writerow([
                            row['Producto'] or "N/A",
                            row['Categoria'] or "N/A",
                            row['Ubicacion'] or "N/A",
                            row['Unidad'] or "N/A",
                            row['stock'] or 0,
                            row['costo_total'] or 0
                        ])
                    conn.close()
                except Exception as ex:
                    print("Error exportando a CSV:", ex)
            messagebox.showinfo("Exito", f"Reporte maestro generado exitosamente en el Escritorio:\n{ruta_salida}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el archivo: {e}")

    def _imprimir_pdf(self):
        selected = self.tree.selection()
        if not selected:
            return messagebox.showwarning("Aviso", "Por favor, seleccione un documento de la tabla.")
            
        item_values = self.tree.item(selected[0])['values']
        doc_id = item_values[0]
        doc_type = item_values[2]
        
        try:
            from core.database import get_connection
            from core.services.pdf_generator import PDFGenerator
            from tkinter.filedialog import asksaveasfilename
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM document_history WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return messagebox.showerror("Error", "Documento no encontrado.")
                
            doc_data = dict(row)
            
            # Pedir al usuario donde guardar
            ruta_defecto = f"Documento_{doc_data.get('doc_number')}.pdf"
            ruta_guardado = asksaveasfilename(
                defaultextension=".pdf", 
                filetypes=[("PDF files", "*.pdf")],
                initialfile=ruta_defecto,
                title="Guardar PDF como..."
            )
            
            if not ruta_guardado:
                return # El usuario canceló
                
            pdf_gen = PDFGenerator(os.path.dirname(ruta_guardado))
            
            if doc_type == "Recepción":
                pdf_gen.generar_guia_remision(doc_data, ruta_guardado)
            elif doc_type == "Despacho" or doc_type == "Receta":
                pdf_gen.generar_vale_despacho(doc_data, ruta_guardado)
            else:
                return messagebox.showinfo("Info", "Tipo de documento no soportado para impresión aquí.")
                
            messagebox.showinfo("Éxito", f"PDF generado correctamente en:\n{ruta_guardado}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF: {e}")


