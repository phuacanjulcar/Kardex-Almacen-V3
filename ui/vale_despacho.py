import customtkinter as ctk
from tkinter import ttk, messagebox
import os
import json
from datetime import datetime
from core.kardex_manager import KardexManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class ValeDespachoWindow(ctk.CTkToplevel):
    def __init__(self, master, current_user):
        super().__init__(master)
        self.title("Vale de Despacho (Salida Masiva)")
        self.geometry("900x650")
        self.current_user = current_user
        self.lista_temporal = [] 
        self.grab_set()
        
        self.modo = ctk.get_appearance_mode()
        self.configure(fg_color=("#F5F7FA", "#121212"))
        
        self._setup_ui()

    def _get_productos(self):
        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM products WHERE is_active = 1 ORDER BY name ASC")
            names = [row['name'] for row in cursor.fetchall()]
            conn.close()
            return names if names else ["-- No hay productos --"]
        except:
            return ["-- No hay productos --"]

    def _cargar_lotes(self, choice):
        if choice == "-- No hay productos --": return
        
        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            # Buscamos el ID del producto
            cursor.execute("SELECT id FROM products WHERE name = ?", (choice,))
            row = cursor.fetchone()
            if not row:
                self.combo_lote.configure(values=["Sin stock"])
                self.combo_lote.set("Sin stock")
                conn.close()
                return
                
            p_id = row['id']
            cursor.execute("SELECT lot_code, qty, expiration_date FROM active_lots WHERE product_id = ? AND qty > 0", (p_id,))
            lotes = [dict(r) for r in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print("Error cargando lotes SQLite:", e)
            lotes = []
            
        if not lotes:
            self.combo_lote.configure(values=["Sin stock"])
            self.combo_lote.set("Sin stock")
            return
            
        valores = []
        for l in lotes:
            vence = l.get('expiration_date', '-')
            if not vence or vence == "": vence = "-"
            valores.append(f"{l.get('lot_code')} (Cant: {l.get('qty')} | Vence: {vence})")
            
        self.combo_lote.configure(values=valores)
        self.combo_lote.set(valores[0])
        self.bind("<Configure>", lambda e: self._on_resize())
        
    def _get_destinations(self):
        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM destinations ORDER BY name ASC")
            rows = cursor.fetchall()
            conn.close()
            if rows:
                return [r['name'] for r in rows]
            else:
                return ["Despacho General"]
        except Exception as e:
            print("Error cargando destinos:", e)
            return ["Despacho General"]

    def _on_resize(self):
        pass

    def _setup_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#1E1E2F"), corner_radius=10, border_width=1, border_color="#E2E8F0")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="1. Datos del Vale de Despacho", font=("Segoe UI", 15, "bold"), text_color="#1565C0").pack(anchor="w", padx=20, pady=(15, 5))
        
        row_header_1 = ctk.CTkFrame(header_frame, fg_color="transparent")
        row_header_1.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(row_header_1, text="N Documento:", font=("Segoe UI", 12)).pack(side="left")
        
        self.entry_doc = ctk.CTkEntry(row_header_1, width=150, fg_color="#E2E8F0" if self.modo=="Light" else "#334155", text_color="#1E293B" if self.modo=="Light" else "white", state="disabled")
        self.entry_doc.pack(side="left", padx=(5, 25))
        
        try:
            from core.database import get_next_sequence
            next_doc = get_next_sequence("Despacho", "VAL")
            self.entry_doc.configure(state="normal")
            self.entry_doc.insert(0, next_doc)
            self.entry_doc.configure(state="disabled")
        except: pass
        
        ctk.CTkLabel(row_header_1, text="Destino / Area Solicitante:", font=("Segoe UI", 12)).pack(side="left")
        destinos = self._get_destinations()
        self.combo_destino = ctk.CTkComboBox(row_header_1, values=destinos, width=200)
        if destinos:
            self.combo_destino.set(destinos[0])
        self.combo_destino.pack(side="left", padx=5)

        detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        detail_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(detail_frame, text="2. Seleccionar Productos a Retirar", font=("Segoe UI", 15, "bold"), text_color="#1565C0").pack(anchor="w", pady=(5, 10))
        
        row_prod = ctk.CTkFrame(detail_frame, fg_color="transparent")
        row_prod.pack(fill="x")
        
        ctk.CTkLabel(row_prod, text="Producto:").pack(side="left")
        productos_lista = self._get_productos()
        self.combo_prod = ctk.CTkOptionMenu(row_prod, values=productos_lista, width=180, command=self._cargar_lotes)
        self.combo_prod.pack(side="left", padx=5)
        
        ctk.CTkLabel(row_prod, text="Lote (FEFO):").pack(side="left", padx=(10, 0))
        self.combo_lote = ctk.CTkOptionMenu(row_prod, values=["Seleccione un producto"], width=220)
        self.combo_lote.pack(side="left", padx=5)
        
        ctk.CTkLabel(row_prod, text="Cant:").pack(side="left", padx=(10, 0))
        self.entry_cant = ctk.CTkEntry(row_prod, width=80)
        self.entry_cant.pack(side="left", padx=5)
        
        ctk.CTkButton(row_prod, text="Agregar a Lista", font=("Segoe UI", 12, "bold"), fg_color="#F57C00", hover_color="#E65100", width=120, command=self._agregar_lista).pack(side="right", padx=(10, 0))

        if productos_lista and productos_lista[0] != "-- No hay productos --":
            self._cargar_lotes(productos_lista[0])

        table_container = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#1E1E2F"), corner_radius=10, border_width=1, border_color="#E2E8F0")
        table_container.pack(fill="both", expand=True, padx=20, pady=15)
        
        cols = ("Producto", "Zona", "Lote a Descontar", "Cantidad a Retirar")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=8)
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
            
        self.tree.column("Producto", width=250, anchor="w")
        self.tree.column("Zona", width=120, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkButton(self, text="📄 Finalizar y Previsualizar Vale", font=("Segoe UI", 14, "bold"), height=45, fg_color="#D32F2F", hover_color="#B71C1C", command=self._mostrar_previsualizacion).pack(fill="x", padx=20, pady=(0, 20))

    def _agregar_lista(self):
        doc = self.entry_doc.get().strip()
        if not doc:
            return messagebox.showerror("Error", "Ingrese el N de Documento / Vale.")

        prod = self.combo_prod.get()
        lote_str = self.combo_lote.get()
        cant_str = self.entry_cant.get().strip()
        
        if "Sin stock" in lote_str or not cant_str:
            return messagebox.showerror("Error", "Verifique el stock y la cantidad ingresada.")
            
        try:
            cant_float = float(cant_str)
            if cant_float <= 0: raise ValueError
        except ValueError:
            return messagebox.showerror("Error", "Cantidad invalida.")

        lote_id = lote_str.split(" ")[0]

        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT z.name as zona 
                FROM products p
                LEFT JOIN zones z ON p.zone_id = z.id
                WHERE p.name = ?
            ''', (prod,))
            row = cursor.fetchone()
            conn.close()
            zona_str = row['zona'] if row and row['zona'] else "Sin Asignar"
        except:
            zona_str = "Desconocida"

        item = {
            "producto": prod, 
            "zona": zona_str,
            "lote": lote_id, 
            "cantidad": cant_float
        }
        self.lista_temporal.append(item)
        
        self.tree.insert("", "end", values=(prod, zona_str, lote_id, cant_float))
        self.entry_cant.delete(0, 'end')

    def _mostrar_previsualizacion(self):
        if not self.lista_temporal:
            return messagebox.showwarning("Aviso", "No hay productos en la lista.")

        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        doc = self.entry_doc.get().strip()
        destino = self.combo_destino.get().strip()
        
        prev_win = ctk.CTkToplevel(self)
        prev_win.title("📄 Previsualización de Vale de Despacho")
        prev_win.geometry("850x700")
        prev_win.transient(self)
        prev_win.grab_set()
        prev_win.configure(fg_color=("#F5F7FA", "#121212"))

        paper = ctk.CTkFrame(prev_win, fg_color="white", corner_radius=0, border_width=1, border_color="#D1D5DB")
        paper.pack(fill="both", expand=True, padx=40, pady=(20, 10))

        header_paper = ctk.CTkFrame(paper, fg_color="transparent")
        header_paper.pack(fill="x", padx=30, pady=30)
        
        left_header = ctk.CTkFrame(header_paper, fg_color="transparent")
        left_header.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(left_header, text="ALMACÉN INMACULADA", font=("Segoe UI", 22, "bold"), text_color="black").pack(anchor="w")
        ctk.CTkLabel(left_header, text="Vale de Despacho Interno", font=("Segoe UI", 12), text_color="#546E7A").pack(anchor="w")
        ctk.CTkLabel(left_header, text=f"Operador Responsable: {self.current_user}", font=("Segoe UI", 12), text_color="black").pack(anchor="w", pady=(10, 0))

        right_header = ctk.CTkFrame(header_paper, fg_color="white", border_width=2, border_color="black", corner_radius=8)
        right_header.pack(side="right", ipadx=20, ipady=10)
        ctk.CTkLabel(right_header, text="SISTEMA DE DESPACHO", font=("Segoe UI", 13, "bold"), text_color="black").pack(pady=(5, 0))
        ctk.CTkLabel(right_header, text="DOCUMENTO DE REFERENCIA", font=("Segoe UI", 11), text_color="black").pack()
        ctk.CTkLabel(right_header, text=f"N° {doc}", font=("Segoe UI", 18, "bold"), text_color="#D32F2F").pack(pady=(5, 0))

        info_frame = ctk.CTkFrame(paper, fg_color="transparent")
        info_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(info_frame, text=f"Fecha de Despacho: {fecha_actual}", font=("Segoe UI", 12, "bold"), text_color="black").grid(row=0, column=0, sticky="w", pady=2)
        ctk.CTkLabel(info_frame, text=f"Destino / Área: {destino}", font=("Segoe UI", 12, "bold"), text_color="black").grid(row=1, column=0, sticky="w", pady=2)

        ctk.CTkLabel(paper, text="Datos de los bienes despachados", font=("Segoe UI", 12, "bold"), text_color="black", anchor="w").pack(fill="x", padx=30, pady=(15, 5))
        
        table_frame = ctk.CTkFrame(paper, fg_color="white", border_width=1, border_color="black", corner_radius=0)
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        
        style = ttk.Style()
        style.configure("Paper.Treeview", background="white", foreground="black", fieldbackground="white", rowheight=25, borderwidth=0)
        style.configure("Paper.Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#F3F4F6", foreground="black")
        
        cols = ("DESCRIPCIÓN", "ZONA", "LOTE", "CANTIDAD")
        tree_prev = ttk.Treeview(table_frame, columns=cols, show="headings", style="Paper.Treeview", height=8)
        for col in cols: tree_prev.heading(col, text=col)
        tree_prev.column("DESCRIPCIÓN", width=300, anchor="w")
        tree_prev.column("ZONA", width=120, anchor="center")
        tree_prev.column("LOTE", width=120, anchor="center")
        tree_prev.column("CANTIDAD", width=100, anchor="center")
        
        for item in self.lista_temporal:
            tree_prev.insert("", "end", values=(item['producto'], item.get('zona', '-'), item['lote'], item['cantidad']))
            
        tree_prev.pack(fill="both", expand=True, padx=1, pady=1)

        ctk.CTkLabel(paper, text=f"Total Ítems: {len(self.lista_temporal)}", font=("Segoe UI", 13, "bold"), text_color="black").pack(anchor="e", padx=30, pady=10)

        btn_frame = ctk.CTkFrame(prev_win, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        ctk.CTkButton(btn_frame, text="⬅️ Modificar Vale", font=("Segoe UI", 13, "bold"), fg_color="transparent", border_width=1, border_color="#D32F2F", text_color="#D32F2F", command=prev_win.destroy).pack(side="left", expand=True, padx=10, fill="x")
        ctk.CTkButton(btn_frame, text="✅ Validar y Descontar", font=("Segoe UI", 13, "bold"), fg_color="#2E7D32", hover_color="#1B5E20", command=lambda: self._procesar_vale(prev_win)).pack(side="right", expand=True, padx=10, fill="x")

    def _procesar_vale(self, prev_win=None):
        if not self.lista_temporal:
            return messagebox.showwarning("Aviso", "La lista de despacho esta vacia.")
            
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        destino = self.combo_destino.get().strip()
        doc = self.entry_doc.get().strip()
        
        # 1. ESTRUCTURA DE SEGURIDAD (Para la Bandeja del Admin)
        log_seguridad = {
            "id_operacion": f"VALE-{doc}",
            "estado": "Pendiente de Validación", 
            "fecha_registro": fecha_actual,
            "ejecutado_por": self.current_user,
            "origen_global": destino, # Se usa como destino para la salida
            "motivo_global": "Despacho Masivo de Almacén",
            "total_items": len(self.lista_temporal),
            "detalles": []
        }
        
        for item in self.lista_temporal:
            manager = KardexManager(item['producto'])
            
            # Descontamos el stock de inmediato para no bloquear el trabajo físico
            ok, msg = manager.register_exit(fecha_actual, item['cantidad'], f"{destino} | Vale: {doc}", self.current_user, item['lote'])
            if not ok:
                messagebox.showerror("Error de Stock", f"Fallo al retirar {item['producto']} (Lote: {item['lote']}): {msg}")
                return 
            
            # Agregamos el detalle al reporte del Jefe
            log_seguridad["detalles"].append({
                "producto": item['producto'],
                "cantidad": float(item['cantidad']),
                "costo_unitario": "N/A (Salida)",
                "vencimiento": "-",
                "lote_asignado": item['lote']
            })
            
        # 2. INYECTAR EL REPORTE EN EL HISTORIAL (Para que el Admin lo valide)
        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO document_history (user, doc_type, doc_number, date, products, status, origen_global, motivo_global)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.current_user,
                "Despacho",
                doc,
                fecha_actual,
                json.dumps(log_seguridad["detalles"]),
                "Pendiente de Validación",
                destino,
                "Despacho Interno / Vale"
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print("Error guardando vale de despacho en SQLite:", e)
        
        messagebox.showinfo("Auditoria", "Vale de despacho procesado. Stock descontado y enviado a Gerencia para su validacion final.")
        if prev_win:
            prev_win.destroy()
        self.destroy()