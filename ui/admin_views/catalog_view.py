import customtkinter as ctk
import os
from tkinter import messagebox
from core.database import get_connection

class CatalogView(ctk.CTkFrame):
    def __init__(self, parent, controller, base_dir):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.modo = ctk.get_appearance_mode()
        self.pack(fill="both", expand=True)
        
        txt_main = "#0F172A" if self.modo=="Light" else "#FFFFFF"
        ctk.CTkLabel(self, text="Organización del Catálogo", font=("Segoe UI", 26, "bold"), text_color=txt_main).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Clasifica y asigna propiedades a los productos desde un solo panel.", font=("Segoe UI", 14), text_color="#64748B").pack(anchor="w", pady=(0, 20))

        split_frame = ctk.CTkFrame(self, fg_color="transparent")
        split_frame.pack(fill="both", expand=True)
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_columnconfigure(1, weight=1)

        lista_frame = ctk.CTkFrame(split_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        lista_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        header_lista = ctk.CTkFrame(lista_frame, fg_color="transparent")
        header_lista.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(header_lista, text="Inventario Maestro", font=("Segoe UI", 14, "bold")).pack(side="left")
        from ui.components.theme import Theme
        ctk.CTkButton(header_lista, text="➕ Nuevo", width=80, height=30, font=("Segoe UI", 12, "bold"), fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, corner_radius=8, command=self._abrir_crear_producto).pack(side="right")
        self.scroll_productos = ctk.CTkScrollableFrame(lista_frame, fg_color="transparent")
        self.scroll_productos.pack(fill="both", expand=True, padx=5, pady=5)

        self.editor_frame = ctk.CTkFrame(split_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        self.editor_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        ctk.CTkLabel(self.editor_frame, text="Seleccione un producto para organizar", font=("Segoe UI", 14, "italic"), text_color="#64748B").place(relx=0.5, rely=0.5, anchor="center")

        self._cargar_lista_productos()

    def _cargar_lista_productos(self):
        for widget in self.scroll_productos.winfo_children(): widget.destroy()

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.id, p.name as Producto, p.unit, p.prefix, p.min_stock, p.max_stock, 
                       c.name as Categoria, z.name as Ubicacion
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN zones z ON p.zone_id = z.id
                WHERE p.is_active = 1
                ORDER BY p.name ASC
            ''')
            productos = cursor.fetchall()
            conn.close()
            
            for prod in productos:
                meta = dict(prod)
                
                es_huerfano = meta.get("Categoria") == "Sin Categoría" or meta.get("Ubicacion") in ["Sin Asignar", "Pendiente de Gerencia"]
                
                from ui.components.theme import Theme
                bg_huerfano = "#FEF2F2" if self.modo == "Light" else "#451a1a"
                border_huerfano = Theme.DANGER[0] if self.modo == "Light" else Theme.DANGER[1]
                text_huerfano = "#B91C1C" if self.modo == "Light" else "#FCA5A5"

                bg_color = bg_huerfano if es_huerfano else ("#F8FAFC" if self.modo == "Light" else "#0F172A")
                border_color = border_huerfano if es_huerfano else ("#E2E8F0" if self.modo == "Light" else "#334155")
                item = ctk.CTkFrame(self.scroll_productos, fg_color=bg_color, corner_radius=8, border_width=1, border_color=border_color)
                item.pack(fill="x", pady=5, padx=5)
                
                title_color = text_huerfano if es_huerfano else ("#0F172A" if self.modo=="Light" else "white")
                ctk.CTkLabel(item, text=meta.get("Producto", "Desconocido"), font=("Segoe UI", 13, "bold"), text_color=title_color).pack(anchor="w", padx=10, pady=(10, 0))
                ctk.CTkLabel(item, text=f"Zona: {meta.get('Ubicacion', 'N/A')} | Cat: {meta.get('Categoria', 'N/A')}", font=("Segoe UI", 11), text_color="#64748B").pack(anchor="w", padx=10, pady=(0, 10))
                
                for widget in [item] + item.winfo_children():
                    widget.bind("<Button-1>", lambda event, m=meta: self._abrir_editor_producto(m))
                    widget.configure(cursor="hand2")
        except Exception as e:
            print(f"Error cargando catálogo: {e}")

    def _abrir_editor_producto(self, meta):
        for widget in self.editor_frame.winfo_children(): widget.destroy()

        ctk.CTkLabel(self.editor_frame, text="Edición Maestra de Producto", font=("Segoe UI", 18, "bold"), text_color="#1565C0").pack(anchor="w", padx=20, pady=(15, 5))
        
        form = ctk.CTkFrame(self.editor_frame, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)
        form.grid_columnconfigure((0, 1), weight=1)

        # Fila 1: Nombre y Prefijo
        ctk.CTkLabel(form, text="Nombre Técnico:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        nombre_entry = ctk.CTkEntry(form, height=35)
        nombre_entry.insert(0, meta.get("Producto", ""))
        nombre_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(0, 10))

        ctk.CTkLabel(form, text="Prefijo Corto:", font=("Segoe UI", 12, "bold")).grid(row=0, column=1, sticky="w", padx=(5, 0))
        pref_entry = ctk.CTkEntry(form, height=35)
        pref_entry.insert(0, meta.get("prefix", "PAQ"))
        pref_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(0, 10))

        # Fila 2: Unidad de Medida
        ctk.CTkLabel(form, text="Unidad (Compra/Venta):", font=("Segoe UI", 12, "bold")).grid(row=2, column=0, sticky="w")
        uni_combo = ctk.CTkOptionMenu(form, values=["Kilogramos (Kg)", "Gramos (g)", "Litros (L)", "Unidades (Und)"], height=35)
        uni_combo.set(meta.get("unit", "Unidades (Und)"))
        uni_combo.grid(row=3, column=0, sticky="ew", padx=(0, 5), pady=(0, 10))

        # Cargar Zonas y Categorias de SQLite
        zonas_disp = ["Sin Asignar"]
        cats_disp = ["Sin Categoría"]
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM zones ORDER BY name")
            zonas_disp = [row['name'] for row in cursor.fetchall()] or zonas_disp
            cursor.execute("SELECT name FROM categories ORDER BY name")
            cats_disp = [row['name'] for row in cursor.fetchall()] or cats_disp
            conn.close()
        except: pass

        ctk.CTkLabel(form, text="Asignar Zona Física:", font=("Segoe UI", 12, "bold")).grid(row=4, column=0, sticky="w")
        zona_combo = ctk.CTkOptionMenu(form, values=zonas_disp, height=35)
        zona_combo.set(meta.get("Ubicacion") if meta.get("Ubicacion") in zonas_disp else zonas_disp[0])
        zona_combo.grid(row=5, column=0, sticky="ew", padx=(0, 5), pady=(0, 10))

        ctk.CTkLabel(form, text="Asignar Categoría:", font=("Segoe UI", 12, "bold")).grid(row=4, column=1, sticky="w", padx=(5, 0))
        cat_combo = ctk.CTkOptionMenu(form, values=cats_disp, height=35)
        cat_combo.set(meta.get("Categoria") if meta.get("Categoria") in cats_disp else cats_disp[0])
        cat_combo.grid(row=5, column=1, sticky="ew", padx=(5, 0), pady=(0, 10))

        # Fila 3: Stock Min y Max
        ctk.CTkLabel(form, text="Stock Mínimo (Alerta):", font=("Segoe UI", 12, "bold")).grid(row=6, column=0, sticky="w")
        stock_min_entry = ctk.CTkEntry(form, height=35)
        stock_min_entry.insert(0, str(meta.get("min_stock", 0)))
        stock_min_entry.grid(row=7, column=0, sticky="ew", padx=(0, 5), pady=(0, 10))

        ctk.CTkLabel(form, text="Stock Máximo (Exceso):", font=("Segoe UI", 12, "bold")).grid(row=6, column=1, sticky="w", padx=(5, 0))
        stock_max_entry = ctk.CTkEntry(form, height=35)
        stock_max_entry.insert(0, str(meta.get("max_stock", 100)))
        stock_max_entry.grid(row=7, column=1, sticky="ew", padx=(5, 0), pady=(0, 10))

        def guardar_cambios():
            nombre = nombre_entry.get().strip()
            if nombre.upper().startswith("VAL-") or nombre.upper().startswith("REC-"):
                return messagebox.showwarning("Aviso de Sistema", "Los prefijos 'VAL-' y 'REC-' están reservados exclusivamente para los Códigos de Vales de Despacho y Recetas respectivamente.\n\nPor favor, elija un nombre distinto.")
                
            pref = pref_entry.get().strip()[:3].upper()
            if pref in ("VAL", "REC"):
                return messagebox.showwarning("Aviso de Sistema", "Los prefijos 'VAL' y 'REC' están reservados exclusivamente para Vales de Despacho y Recetas.\n\nPor favor, elija otro prefijo.")

            try: 
                s_min = float(stock_min_entry.get().strip())
                s_max = float(stock_max_entry.get().strip())
            except ValueError:
                return messagebox.showerror("Error", "Los valores de stock deben ser numéricos.")

            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM zones WHERE name = ?", (zona_combo.get(),))
                z_row = cursor.fetchone()
                z_id = z_row['id'] if z_row else None
                
                cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_combo.get(),))
                c_row = cursor.fetchone()
                c_id = c_row['id'] if c_row else None
                
                # Check if it's a new product or edit
                if meta.get("id") is None:
                    # New product
                    cursor.execute('''
                        INSERT INTO products (name, prefix, unit, zone_id, category_id, min_stock, max_stock)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        nombre,
                        pref,
                        uni_combo.get(),
                        z_id,
                        c_id,
                        s_min,
                        s_max
                    ))
                else:
                    cursor.execute('''
                        UPDATE products 
                        SET name = ?, prefix = ?, unit = ?, zone_id = ?, category_id = ?, 
                            min_stock = ?, max_stock = ?
                        WHERE id = ?
                    ''', (
                        nombre,
                        pref,
                        uni_combo.get(),
                        z_id,
                        c_id,
                        s_min,
                        s_max,
                        meta['id']
                    ))
                conn.commit()
                conn.close()
                
                if hasattr(self.controller, 'mostrar_toast'):
                    self.controller.mostrar_toast(f"Catálogo actualizado")
                else:
                    messagebox.showinfo("Éxito", "Catálogo actualizado")
                    
                self._cargar_lista_productos() 
                for widget in self.editor_frame.winfo_children(): widget.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Fallo al actualizar en DB: {e}")

        botones_frame = ctk.CTkFrame(self.editor_frame, fg_color="transparent")
        botones_frame.pack(pady=(0, 20), padx=20, fill="x", side="bottom")
        
        ctk.CTkButton(botones_frame, text="Guardar Cambios", font=("Segoe UI", 14, "bold"), fg_color="#10B981", hover_color="#059669", height=40, command=guardar_cambios).pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        if meta.get("id") is not None:
            ctk.CTkButton(botones_frame, text="Eliminar Producto", font=("Segoe UI", 14, "bold"), fg_color="#EF4444", hover_color="#DC2626", height=40, command=lambda: self._eliminar_producto(meta['id'], meta.get('Producto', ''))).pack(side="left", fill="x", expand=True, padx=(0, 5))

    def _eliminar_producto(self, p_id, p_name):
        if not messagebox.askyesno("Confirmar", f"¿Seguro que deseas desactivar el producto '{p_name}'?\nYa no aparecerá en las listas, pero su historial se mantendrá intacto."): return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET is_active = 0 WHERE id = ?", (p_id,))
            conn.commit()
            conn.close()
            
            if hasattr(self.controller, 'mostrar_toast'):
                self.controller.mostrar_toast("Producto eliminado")
            else:
                messagebox.showinfo("Éxito", "Producto eliminado")
                
            self._cargar_lista_productos()
            for widget in self.editor_frame.winfo_children(): widget.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al eliminar: {e}")

    def _abrir_crear_producto(self):
        meta_vacia = {
            "Producto": "",
            "prefix": "PAQ",
            "unit": "Unidades (Und)",
            "min_stock": 10,
            "max_stock": 100,
            "Categoria": "Sin Categoría",
            "Ubicacion": "Sin Asignar"
        }
        self._abrir_editor_producto(meta_vacia)
