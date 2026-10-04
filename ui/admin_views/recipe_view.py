import customtkinter as ctk
from tkinter import messagebox
from core.database import get_connection
from datetime import datetime

class RecipeView(ctk.CTkFrame):
    def __init__(self, parent, controller, base_dir):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.base_dir = base_dir
        self.modo = ctk.get_appearance_mode()
        self.pack(fill="both", expand=True)
        
        self.ingredients_list = []
        
        ctk.CTkLabel(self, text="Recetas y Fórmulas", font=("Segoe UI", 26, "bold"), text_color="#10B981").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Crea recetas predefinidas para facilitar el despacho a los operarios.", font=("Segoe UI", 14), text_color="#64748B").pack(anchor="w", pady=(0, 20))
        
        split_frame = ctk.CTkFrame(self, fg_color="transparent")
        split_frame.pack(fill="both", expand=True)
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_columnconfigure(1, weight=2)

        lista_frame = ctk.CTkFrame(split_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        lista_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        header_lista = ctk.CTkFrame(lista_frame, fg_color="transparent")
        header_lista.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(header_lista, text="Recetas Guardadas", font=("Segoe UI", 16, "bold")).pack(side="left")
        ctk.CTkButton(header_lista, text="+ Nueva Receta", width=100, font=("Segoe UI", 12, "bold"), fg_color="#10B981", hover_color="#059669", command=self._show_create_form).pack(side="right")
        
        self.scroll_recetas = ctk.CTkScrollableFrame(lista_frame, fg_color="transparent")
        self.scroll_recetas.pack(fill="both", expand=True, padx=5, pady=5)

        self.detalle_frame = ctk.CTkFrame(split_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        self.detalle_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self._cargar_lista()

    def _cargar_lista(self):
        for widget in self.scroll_recetas.winfo_children(): widget.destroy()
        for widget in self.detalle_frame.winfo_children(): widget.destroy()
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recipes ORDER BY name ASC")
            recetas = cursor.fetchall()
            conn.close()
        except Exception as e:
            print("Error cargando recetas:", e)
            recetas = []
            
        if not recetas:
            ctk.CTkLabel(self.scroll_recetas, text="No hay recetas guardadas.", font=("Segoe UI", 13, "italic"), text_color="#94A3B8").pack(pady=20)
            return

        for r in recetas:
            r_dict = dict(r)
            item = ctk.CTkFrame(self.scroll_recetas, fg_color="#F8FAFC" if self.modo == "Light" else "#0F172A", corner_radius=5, border_width=1, border_color="#E2E8F0", cursor="hand2")
            item.pack(fill="x", pady=3)
            
            lbl1 = ctk.CTkLabel(item, text=r_dict['name'], font=("Segoe UI", 14, "bold"), text_color="#1E293B" if self.modo=="Light" else "white", cursor="hand2")
            lbl1.pack(anchor="w", padx=10, pady=(10, 0))
            lbl2 = ctk.CTkLabel(item, text=f"Por: {r_dict['created_by']} | {r_dict['created_at']}", font=("Segoe UI", 10), text_color="#64748B", cursor="hand2")
            lbl2.pack(anchor="w", padx=10, pady=(0, 10))
            
            # Usar un wrapper para el bind con parámetro por defecto
            def make_cmd(x=r_dict):
                return lambda e: self._ver_detalle(x)
            
            cmd = make_cmd()
            item.bind("<Button-1>", cmd)
            lbl1.bind("<Button-1>", cmd)
            lbl2.bind("<Button-1>", cmd)
            # CTk en Windows puede necesitar bind en el canvas interno del frame
            if hasattr(item, "_canvas"): item._canvas.bind("<Button-1>", cmd)

    def _ver_detalle(self, receta):
        for widget in self.detalle_frame.winfo_children(): widget.destroy()
        
        header = ctk.CTkFrame(self.detalle_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(header, text=f"Receta: {receta['name']}", font=("Segoe UI", 20, "bold"), text_color="#10B981").pack(anchor="w")
        ctk.CTkLabel(header, text=f"Autor: {receta['created_by']} | Fecha: {receta['created_at']}", font=("Segoe UI", 13), text_color="#64748B").pack(anchor="w", pady=(5, 0))
        
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(anchor="e")
        ctk.CTkButton(btn_frame, text="Eliminar Receta", font=("Segoe UI", 12, "bold"), fg_color="#EF4444", hover_color="#DC2626", command=lambda: self._eliminar_receta(receta['id'])).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Editar Receta", font=("Segoe UI", 12, "bold"), fg_color="#F59E0B", text_color="#0F172A", hover_color="#D97706", command=lambda: self._editar_receta(receta)).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="📄 Imprimir Receta", font=("Segoe UI", 12, "bold"), fg_color="#3B82F6", hover_color="#2563EB", command=lambda: self._imprimir_receta(receta)).pack(side="right", padx=5)
        
        cols_frame = ctk.CTkFrame(self.detalle_frame, fg_color="#F1F5F9" if self.modo=="Light" else "#0F172A", corner_radius=5)
        cols_frame.pack(fill="x", padx=20, pady=5)
        cols_frame.grid_columnconfigure(0, weight=3)
        cols_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(cols_frame, text="Producto", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(cols_frame, text="Cantidad Req.", font=("Segoe UI", 12, "bold")).grid(row=0, column=1, sticky="e", padx=10, pady=5)

        scroll_ingredientes = ctk.CTkScrollableFrame(self.detalle_frame, fg_color="transparent")
        scroll_ingredientes.pack(fill="both", expand=True, padx=15, pady=5)

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT product_name, quantity FROM recipe_items WHERE recipe_id = ?", (receta['id'],))
            ingredientes = cursor.fetchall()
            conn.close()
            
            for i, ing in enumerate(ingredientes):
                row_color = "transparent" if i % 2 == 0 else ("#F8FAFC" if self.modo=="Light" else "#1E293B")
                row_f = ctk.CTkFrame(scroll_ingredientes, fg_color=row_color, corner_radius=0)
                row_f.pack(fill="x")
                row_f.grid_columnconfigure(0, weight=3)
                row_f.grid_columnconfigure(1, weight=1)
                
                ctk.CTkLabel(row_f, text=ing['product_name'], font=("Segoe UI", 13), text_color="#1E293B" if self.modo=="Light" else "white").grid(row=0, column=0, sticky="w", padx=10, pady=8)
                ctk.CTkLabel(row_f, text=str(ing['quantity']), font=("Segoe UI", 13), text_color="#1E293B" if self.modo=="Light" else "white").grid(row=0, column=1, sticky="e", padx=10, pady=8)
        except Exception as e:
            print("Error cargando ingredientes:", e)

    def _eliminar_receta(self, r_id):
        if not messagebox.askyesno("Confirmar", "¿Seguro que deseas eliminar esta receta?"): return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recipes WHERE id = ?", (r_id,))
            conn.commit()
            conn.close()
            self._cargar_lista()
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al eliminar: {e}")

    def _imprimir_receta(self, receta):
        try:
            from core.database import get_connection
            from core.services.pdf_generator import PDFGenerator
            from tkinter.filedialog import asksaveasfilename
            import os
            
            # Obtener items
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT product_name, quantity FROM recipe_items WHERE recipe_id = ?", (receta['id'],))
            items = cursor.fetchall()
            conn.close()
            
            receta_full = dict(receta)
            receta_full['items'] = [dict(i) for i in items]
            
            ruta_defecto = f"Receta_{receta['name']}.pdf"
            ruta_guardado = asksaveasfilename(
                defaultextension=".pdf", 
                filetypes=[("PDF files", "*.pdf")],
                initialfile=ruta_defecto,
                title="Guardar PDF como..."
            )
            
            if not ruta_guardado: return
            
            pdf_gen = PDFGenerator(os.path.dirname(ruta_guardado))
            pdf_gen.generar_receta(receta_full, ruta_guardado)
            
            messagebox.showinfo("Éxito", f"Receta guardada en:\n{ruta_guardado}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al imprimir receta: {e}")

    def _show_create_form(self):
        for widget in self.detalle_frame.winfo_children(): widget.destroy()
        self.ingredients_list = []
        self.editing_recipe_id = None
        
        ctk.CTkLabel(self.detalle_frame, text="Crear Nueva Receta", font=("Segoe UI", 20, "bold"), text_color="#10B981").pack(anchor="w", padx=20, pady=20)
        
        form = ctk.CTkFrame(self.detalle_frame, fg_color="transparent")
        form.pack(fill="x", padx=20)
        
        ctk.CTkLabel(form, text="Nombre de la Receta (ej. Cena Navideña):", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.entry_name = ctk.CTkEntry(form, placeholder_text="Nombre...", text_color="white" if self.modo=="Dark" else "black")
        self.entry_name.pack(fill="x", pady=(0, 15))
        
        # Selección de productos
        add_frame = ctk.CTkFrame(form, fg_color="#F8FAFC" if self.modo=="Light" else "#0F172A", border_width=1, border_color="#E2E8F0")
        add_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(add_frame, text="Agregar Ingrediente", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=10, pady=10)
        
        row_inputs = ctk.CTkFrame(add_frame, fg_color="transparent")
        row_inputs.pack(fill="x", padx=10, pady=(0, 10))
        
        productos = self._get_productos()
        self.combo_prod = ctk.CTkComboBox(row_inputs, values=productos, width=250, text_color="white" if self.modo=="Dark" else "black")
        self.combo_prod.set(productos[0] if productos else "")
        self.combo_prod.pack(side="left", padx=5)
        
        self.entry_qty = ctk.CTkEntry(row_inputs, width=80, placeholder_text="Cant.", text_color="white" if self.modo=="Dark" else "black")
        self.entry_qty.pack(side="left", padx=5)
        
        from ui.components.theme import Theme
        ctk.CTkButton(row_inputs, text="➕ Añadir", width=80, font=("Segoe UI", 12, "bold"), fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, corner_radius=8, command=self._add_ingredient).pack(side="left", padx=5)
        # Lista de ingredientes actual
        self.list_frame = ctk.CTkScrollableFrame(self.detalle_frame, fg_color="transparent", height=150)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.btn_save = ctk.CTkButton(self.detalle_frame, text="💾 Guardar Receta", font=("Segoe UI", 14, "bold"), fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, height=40, corner_radius=8, command=self._save_recipe)
        self.btn_save.pack(side="bottom", fill="x", padx=20, pady=20)
        self._render_ingredients()

    def _editar_receta(self, receta):
        self._show_create_form()
        self.editing_recipe_id = receta['id']
        
        # Cambiar titulo
        for w in self.detalle_frame.winfo_children():
            if isinstance(w, ctk.CTkLabel) and w.cget("text") == "Crear Nueva Receta":
                w.configure(text=f"Editar Receta: {receta['name']}")
                break
                
        self.entry_name.insert(0, receta['name'])
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT product_name, quantity FROM recipe_items WHERE recipe_id = ?", (receta['id'],))
            for ing in cursor.fetchall():
                self.ingredients_list.append({"product": ing['product_name'], "quantity": ing['quantity']})
            conn.close()
            self._render_ingredients()
        except: pass

    def _get_productos(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM products WHERE is_active = 1 ORDER BY name ASC")
            names = [row['name'] for row in cursor.fetchall()]
            conn.close()
            return names if names else ["-- No hay productos --"]
        except: return []

    def _add_ingredient(self):
        prod = self.combo_prod.get()
        if not prod or prod == "-- No hay productos --": return
        qty = self.entry_qty.get()
        try:
            qty = float(qty)
            if qty <= 0: raise ValueError
        except:
            messagebox.showerror("Error", "Cantidad inválida")
            return
            
        for i in self.ingredients_list:
            if i['product'] == prod:
                i['quantity'] += qty
                self._render_ingredients()
                self.entry_qty.delete(0, 'end')
                return
                
        self.ingredients_list.append({"product": prod, "quantity": qty})
        self.entry_qty.delete(0, 'end')
        self._render_ingredients()

    def _render_ingredients(self):
        for w in self.list_frame.winfo_children(): w.destroy()
        for idx, ing in enumerate(self.ingredients_list):
            item = ctk.CTkFrame(self.list_frame, fg_color="#FFFFFF" if self.modo=="Light" else "#1E293B", corner_radius=5)
            item.pack(fill="x", pady=2)
            ctk.CTkLabel(item, text=f"{ing['product']} - Cant: {ing['quantity']}", font=("Segoe UI", 13)).pack(side="left", padx=10, pady=5)
            ctk.CTkButton(item, text="X", width=30, fg_color="#EF4444", hover_color="#DC2626", command=lambda i=idx: self._remove_ingredient(i)).pack(side="right", padx=5, pady=5)

    def _remove_ingredient(self, idx):
        self.ingredients_list.pop(idx)
        self._render_ingredients()

    def _save_recipe(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showerror("Error", "Debes poner un nombre a la receta")
            return
        if not self.ingredients_list:
            messagebox.showerror("Error", "Debes añadir al menos un ingrediente")
            return
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if getattr(self, 'editing_recipe_id', None):
                cursor.execute("UPDATE recipes SET name = ? WHERE id = ?", (name, self.editing_recipe_id))
                r_id = self.editing_recipe_id
                cursor.execute("DELETE FROM recipe_items WHERE recipe_id = ?", (r_id,))
            else:
                cursor.execute("INSERT INTO recipes (name, created_at, created_by) VALUES (?, ?, ?)", (name, datetime.now().strftime("%Y-%m-%d %H:%M"), "Administrador"))
                r_id = cursor.lastrowid
            
            for ing in self.ingredients_list:
                cursor.execute("INSERT INTO recipe_items (recipe_id, product_name, quantity) VALUES (?, ?, ?)", (r_id, ing['product'], ing['quantity']))
                
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Receta guardada exitosamente.")
            self._cargar_lista()
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                messagebox.showerror("Error", "Ya existe una receta con ese nombre.")
            else:
                messagebox.showerror("Error", f"Fallo al guardar: {e}")
