import customtkinter as ctk
from tkinter import messagebox
from core.database import get_connection
from core.kardex_manager import KardexManager
import json
from datetime import datetime
from tkinter import ttk

class UserRecipeView(ctk.CTkToplevel):
    def __init__(self, master, current_user):
        super().__init__(master)
        self.title("Preparar Receta")
        self.geometry("900x700")
        self.current_user = current_user
        self.grab_set()
        
        self.modo = ctk.get_appearance_mode()
        self.configure(fg_color="#F5F7FA" if self.modo == "Light" else "#121212")
        
        # Estado
        self.selected_recipe = None
        self.recipe_items = []
        self.dispatch_items = []
        
        self._setup_ui()
        self._load_recipes()

    def _setup_ui(self):
        header = ctk.CTkFrame(self, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="Preparación de Fórmulas y Recetas", font=("Segoe UI", 20, "bold"), text_color="#1565C0").pack(anchor="w", padx=20, pady=(15, 5))
        
        row_header = ctk.CTkFrame(header, fg_color="transparent")
        row_header.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(row_header, text="Seleccionar Receta:", font=("Segoe UI", 13, "bold")).pack(side="left")
        self.combo_recipe = ctk.CTkComboBox(row_header, values=[], width=300, command=self._on_recipe_select)
        self.combo_recipe.pack(side="left", padx=15)
        
        ctk.CTkLabel(row_header, text="Destino:", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(20,0))
        destinos = self._get_destinations()
        self.combo_destino = ctk.CTkComboBox(row_header, values=destinos, width=200)
        if destinos:
            self.combo_destino.set(destinos[0])
        self.combo_destino.pack(side="left", padx=10)

        # Panel Principal
        main_frame = ctk.CTkFrame(self, fg_color="#FFFFFF" if self.modo=="Light" else "#1E293B", corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(main_frame, text="Plan de Despacho de Ingredientes", font=("Segoe UI", 16, "bold")).pack(pady=10)
        
        # Treeview para mostrar el plan auto-calculado
        style = ttk.Style()
        style.configure("RecipePlan.Treeview", rowheight=30, borderwidth=0, font=("Segoe UI", 11))
        style.configure("RecipePlan.Treeview.Heading", font=("Segoe UI", 11, "bold"))
        
        cols = ("Ingrediente", "Zona", "Cant. Necesaria", "Lote a Extraer", "Cant. a Extraer", "Vencimiento")
        self.tree = ttk.Treeview(main_frame, columns=cols, show="headings", style="RecipePlan.Treeview")
        
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Ingrediente", width=200, anchor="w")
        self.tree.column("Zona", width=120, anchor="center")
        self.tree.column("Cant. Necesaria", width=120, anchor="center")
        self.tree.column("Lote a Extraer", width=150, anchor="center")
        self.tree.column("Cant. a Extraer", width=120, anchor="center")
        self.tree.column("Vencimiento", width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Mensaje de error/faltantes si no hay stock
        self.lbl_error = ctk.CTkLabel(main_frame, text="", font=("Segoe UI", 13, "bold"), text_color="#EF4444")
        self.lbl_error.pack(pady=5)
        
        # Footer
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(footer, text="🚀 Previsualizar y Preparar Receta", font=("Segoe UI", 15, "bold"), fg_color="#10B981", hover_color="#059669", height=45, command=self._mostrar_previsualizacion).pack(fill="x")

    def _load_recipes(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM recipes ORDER BY name ASC")
            nombres = [row['name'] for row in cursor.fetchall()]
            conn.close()
            if not nombres: nombres = ["-- Sin Recetas --"]
            self.combo_recipe.configure(values=nombres)
            self.combo_recipe.set(nombres[0])
            if nombres[0] != "-- Sin Recetas --":
                self._on_recipe_select(nombres[0])
        except Exception as e:
            print("Error cargando recetas:", e)

    def _get_destinations(self):
        try:
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

    def _on_recipe_select(self, val):
        if val == "-- Sin Recetas --": return
        self.selected_recipe = val
        self.recipe_items = []
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM recipes WHERE name = ?", (val,))
            r_id = cursor.fetchone()['id']
            cursor.execute("SELECT product_name, quantity FROM recipe_items WHERE recipe_id = ?", (r_id,))
            self.recipe_items = [dict(row) for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print("Error", e)
            
        self._autofill_plan()

    def _autofill_plan(self):
        self.dispatch_items = []
        self.lbl_error.configure(text="")
        errores_faltantes = []
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            for ing in self.recipe_items:
                prod = ing['product_name']
                req_qty = float(ing['quantity'])
                
                # Buscar id producto
                cursor.execute('''
                    SELECT p.id, z.name as zona
                    FROM products p
                    LEFT JOIN zones z ON p.zone_id = z.id
                    WHERE p.name = ?
                ''', (prod,))
                p_row = cursor.fetchone()
                if not p_row:
                    errores_faltantes.append(f"Producto '{prod}' no encontrado en BD.")
                    continue
                p_id = p_row['id']
                zona_str = p_row['zona'] if p_row['zona'] else "Sin Asignar"
                
                # Lotes activos ordenados por vencimiento (FEFO)
                cursor.execute("SELECT lot_code, qty, expiration_date FROM active_lots WHERE product_id = ? AND qty > 0 ORDER BY expiration_date ASC", (p_id,))
                lotes = [dict(r) for r in cursor.fetchall()]
                
                assigned = 0
                for lote in lotes:
                    if assigned >= req_qty: break
                    available = float(lote['qty'])
                    if available <= 0: continue
                    
                    take = min(available, req_qty - assigned)
                    self.dispatch_items.append({
                        "product": prod,
                        "zona": zona_str,
                        "lot": lote['lot_code'],
                        "qty": take,
                        "req_qty": req_qty,
                        "vence": lote['expiration_date']
                    })
                    assigned += take
                    
                if assigned < req_qty:
                    errores_faltantes.append(f"Falta stock de {prod} (Requerido: {req_qty}, Disp: {assigned})")
                    
            conn.close()
        except Exception as e:
            print("Error auto-filling:", e)
            
        if errores_faltantes:
            self.lbl_error.configure(text="\n".join(errores_faltantes))
            
        self._render_plan()

    def _render_plan(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        for d in self.dispatch_items:
            self.tree.insert("", "end", values=(
                d['product'],
                d.get('zona', '-'),
                d.get('req_qty', '-'),
                d['lot'],
                d['qty'],
                d['vence']
            ))

    def _mostrar_previsualizacion(self):
        destino = self.combo_destino.get().strip()
        if not destino:
            return messagebox.showerror("Error", "Debes seleccionar un destino.")
            
        if not hasattr(self, 'dispatch_items') or not self.dispatch_items:
            return messagebox.showerror("Error", "No hay lotes asignados para despachar.")
            
        if self.lbl_error.cget("text") != "":
            if not messagebox.askyesno("Stock Insuficiente", "Algunos ingredientes no tienen stock completo.\n¿Desea despachar la receta de todas formas?"):
                return
                
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            from core.database import get_next_sequence
            doc = get_next_sequence("Receta", "REC")
        except: doc = "REC-000001"
            
        prev_win = ctk.CTkToplevel(self)
        prev_win.title("📝 Previsualización de Receta")
        prev_win.geometry("750x650")
        prev_win.transient(self)
        prev_win.grab_set()
        prev_win.configure(fg_color=("#F5F7FA", "#121212"))

        paper = ctk.CTkFrame(prev_win, fg_color="white", corner_radius=0, border_width=1, border_color="#D1D5DB")
        paper.pack(fill="both", expand=True, padx=40, pady=(20, 10))

        header_paper = ctk.CTkFrame(paper, fg_color="transparent")
        header_paper.pack(fill="x", padx=30, pady=20)
        
        ctk.CTkLabel(header_paper, text="FICHA TÉCNICA DE RECETA", font=("Segoe UI", 20, "bold"), text_color="black").pack(pady=(0,5))
        ctk.CTkLabel(header_paper, text=f"Receta: {self.selected_recipe}   |   Destino: {destino}", font=("Segoe UI", 14), text_color="#334155").pack()
        ctk.CTkLabel(header_paper, text=f"Doc: {doc}   |   Operador: {self.current_user}", font=("Segoe UI", 12), text_color="#64748B").pack(pady=(5,0))

        table_frame = ctk.CTkFrame(paper, fg_color="white", border_width=1, border_color="black", corner_radius=0)
        table_frame.pack(fill="both", expand=True, padx=30, pady=(10, 10))
        
        style = ttk.Style()
        style.configure("Paper.Treeview", background="white", foreground="black", fieldbackground="white", rowheight=25, borderwidth=0)
        style.configure("Paper.Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#F3F4F6", foreground="black")
        
        cols = ("INGREDIENTE", "ZONA", "LOTE", "CANTIDAD")
        tree_prev = ttk.Treeview(table_frame, columns=cols, show="headings", style="Paper.Treeview", height=8)
        for col in cols: tree_prev.heading(col, text=col)
        tree_prev.column("INGREDIENTE", width=300, anchor="w")
        tree_prev.column("ZONA", width=120, anchor="center")
        tree_prev.column("LOTE", width=120, anchor="center")
        tree_prev.column("CANTIDAD", width=120, anchor="center")
        
        for item in self.dispatch_items:
            tree_prev.insert("", "end", values=(item['product'], item.get('zona', '-'), item['lot'], item['qty']))
            
        tree_prev.pack(fill="both", expand=True, padx=1, pady=1)

        btn_frame = ctk.CTkFrame(prev_win, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        ctk.CTkButton(btn_frame, text="⬅️ Modificar", font=("Segoe UI", 13, "bold"), fg_color="transparent", border_width=1, border_color="#D32F2F", text_color="#D32F2F", command=prev_win.destroy).pack(side="left", expand=True, padx=10, fill="x")
        ctk.CTkButton(btn_frame, text="✅ Confirmar y Preparar", font=("Segoe UI", 13, "bold"), fg_color="#10B981", hover_color="#059669", command=lambda: self._procesar_despacho(self.dispatch_items, destino, doc, fecha_actual, prev_win)).pack(side="right", expand=True, padx=10, fill="x")

    def _procesar_despacho(self, dispatch_items, destino, doc, fecha_actual, prev_win):
        log_seguridad = {
            "id_operacion": doc,
            "origen_global": destino,
            "motivo_global": f"Preparación de Receta: {self.selected_recipe}",
            "fecha_registro": fecha_actual,
            "ejecutado_por": self.current_user,
            "estado": "Pendiente de Validación",
            "detalles": []
        }
        
        for item in dispatch_items:
            manager = KardexManager(item['product'])
            
            ok, msg = manager.register_exit(fecha_actual, item['qty'], f"{destino} | Receta: {self.selected_recipe}", self.current_user, item['lot'])
            if not ok:
                messagebox.showerror("Error de Stock", f"Fallo al retirar {item['product']} (Lote: {item['lot']}): {msg}")
                return 
            
            log_seguridad["detalles"].append({
                "producto": item['product'],
                "cantidad": float(item['qty']),
                "costo_unitario": "N/A (Receta)",
                "vencimiento": item['vence'],
                "lote_asignado": item['lot']
            })
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO document_history (user, doc_type, doc_number, date, products, status, origen_global, motivo_global)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.current_user,
                "Receta",
                doc,
                fecha_actual,
                json.dumps(log_seguridad["detalles"]),
                "Pendiente de Validación",
                destino,
                f"Preparación de Receta: {self.selected_recipe}"
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando receta: {e}")
            return
            
        messagebox.showinfo("Operación Exitosa", f"Receta procesada.\nVale '{doc}' enviado a Gerencia para validación.")
        prev_win.destroy()
        self.destroy()
