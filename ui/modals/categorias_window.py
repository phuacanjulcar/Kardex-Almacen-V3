import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import os
from PIL import Image
from core.database import get_connection
from ui.toast import show_toast

class CategoriasWindow(ctk.CTkToplevel):
    def __init__(self, master, current_user):
        super().__init__(master)
        self.current_user = current_user
        self.is_guest = (current_user == "Invitado")
        
        self.title("Directorio de Categorías")
        self.geometry("900x550")
        
        modo = ctk.get_appearance_mode()
        self.bg_color = "#1E1E2F" if modo == "Dark" else "#FFFFFF"
        self.panel_bg = "#2A2D43" if modo == "Dark" else "#F9FBFD"
        self.txt_color = "#FFFFFF" if modo == "Dark" else "#121212"
        self.accent_color = "#5C6BC0"
        self.configure(fg_color=self.bg_color)
        self.categorias_db = self.cargar_datos_db()
        
        self.transient(master)
        self.grab_set()

        self.left_panel = ctk.CTkFrame(self, width=260, fg_color=self.panel_bg, corner_radius=0)
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)
        
        self.lista_cats = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent")
        self.lista_cats.pack(fill="both", expand=True)

        if self.current_user == "Administrador":
            ctk.CTkButton(self.left_panel, text="+ Crear Nueva Categoría", fg_color=self.accent_color, hover_color="#3F51B5", height=45, font=("Segoe UI", 14, "bold"), command=self.crear_categoria).pack(fill="x", padx=15, pady=15)
        
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.construir_panel_izquierdo()

    def cargar_datos_db(self):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        cats = cursor.fetchall()
        
        db = {}
        for c in cats:
            name = c['name']
            db[name] = []
            
            cursor.execute('''
                SELECT p.name as prod, p.unit as unidad, COALESCE(SUM(l.qty), 0) as stock
                FROM products p
                LEFT JOIN active_lots l ON p.id = l.product_id
                WHERE p.category_id = ?
                GROUP BY p.id
            ''', (c['id'],))
            
            prods = cursor.fetchall()
            for p in prods:
                db[name].append({
                    "prod": p['prod'],
                    "stock": p['stock'],
                    "unidad": p['unidad']
                })
                
        conn.close()
        return db

    def construir_panel_izquierdo(self):
        for w in self.lista_cats.winfo_children(): w.destroy()
        ctk.CTkLabel(self.lista_cats, text="CATEGORÍAS DE INVENTARIO", font=("Segoe UI", 13, "bold"), text_color=self.accent_color).pack(pady=20)
        
        cats_ordenadas = list(self.categorias_db.keys())
        if "Sin Categoría" in cats_ordenadas:
            cats_ordenadas.remove("Sin Categoría")
            cats_ordenadas.insert(0, "Sin Categoría")

        ic_cat = ctk.CTkImage(Image.open(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "ic_category.png"))), size=(18,18))
        for cat in cats_ordenadas:
            color = "#E53935" if cat == "Sin Categoría" else "transparent"
            btn = ctk.CTkButton(self.lista_cats, image=ic_cat, text=f" {cat}", font=("Segoe UI", 13, "bold"), fg_color=color, hover_color="#3F51B5", border_width=1, border_color=self.accent_color, text_color=("#FFFFFF" if cat == "Sin Categoría" else self.txt_color), anchor="w", height=40, command=lambda c=cat: self.mostrar_detalle(c))
            btn.pack(fill="x", padx=10, pady=5)

        if cats_ordenadas:
            self.mostrar_detalle(cats_ordenadas[0])

    def mostrar_detalle(self, categoria):
        for w in self.right_panel.winfo_children(): w.destroy()

        productos = self.categorias_db[categoria]
        header_zone = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        header_zone.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header_zone, text=categoria.upper(), font=("Segoe UI", 26, "bold"), text_color=self.accent_color).pack(side="left")
        
        if self.current_user == "Administrador" and categoria != "Sin Categoría":
            tools = ctk.CTkFrame(header_zone, fg_color="transparent")
            tools.pack(side="right")
            ic_edit = ctk.CTkImage(Image.open(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "ic_edit.png"))), size=(16,16))
            ic_del = ctk.CTkImage(Image.open(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "ic_delete.png"))), size=(16,16))
            
            ctk.CTkButton(tools, image=ic_edit, text=" Editar", width=70, fg_color="transparent", border_width=1, border_color="#8892B0", text_color="#8892B0", hover_color="#E2E8F0", command=lambda: self.editar_categoria(categoria)).pack(side="left", padx=5)
            ctk.CTkButton(tools, image=ic_del, text=" Borrar", width=70, fg_color="transparent", border_width=1, border_color="#E53935", text_color="#E53935", hover_color="#FFEBEE", command=lambda: self.borrar_categoria(categoria)).pack(side="left")

        ic_box = ctk.CTkImage(Image.open(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "ic_dispatch.png"))), size=(18,18))
        lbl_info = ctk.CTkLabel(self.right_panel, image=ic_box, text=f" Se encontraron {len(productos)} tipos de productos en esta ubicación", font=("Segoe UI", 14), text_color="#546E7A", compound="left")
        lbl_info.pack(anchor="w", pady=(0, 15))
        lista = ctk.CTkScrollableFrame(self.right_panel, fg_color=self.panel_bg, corner_radius=10, border_width=1, border_color="#E2E8F0")
        lista.pack(fill="both", expand=True)

        if not productos:
            ctk.CTkLabel(lista, text="No hay productos en esta categoría.", font=("Segoe UI", 14, "italic"), text_color=self.txt_color).pack(pady=40)
        else:
            for p in productos:
                item_frame = ctk.CTkFrame(lista, fg_color="transparent")
                item_frame.pack(fill="x", pady=8, padx=10)
                ctk.CTkLabel(item_frame, text=p['prod'], font=("Segoe UI", 15, "bold"), text_color=self.txt_color).pack(side="left")
                color_stock = "#2E7D32" if p['stock'] > 0 else "#E53935"
                ctk.CTkLabel(item_frame, text=f"Stock: {p['stock']:,.2f} {p['unidad']}", font=("Segoe UI", 14, "bold"), text_color=color_stock).pack(side="right")

    def crear_categoria(self):
        win = ctk.CTkToplevel(self)
        win.title("Nueva Categoría")
        win.geometry("350x200")
        win.configure(fg_color=self.bg_color)
        win.grab_set()

        ctk.CTkLabel(win, text="Nombre de la nueva categoría:", text_color=self.txt_color, font=("Segoe UI", 13)).pack(pady=(25,5))
        nombre_var = ctk.StringVar()
        ctk.CTkEntry(win, textvariable=nombre_var, width=250, height=35).pack()

        def guardar():
            nombre = nombre_var.get().strip()
            if not nombre: return messagebox.showerror("Error", "Nombre requerido.")
            
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (nombre,))
                conn.commit()
                conn.close()
                
                self.categorias_db = self.cargar_datos_db()
                self.construir_panel_izquierdo()
                self.mostrar_detalle(nombre)
                win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Nombre duplicado.")

        ctk.CTkButton(win, text="Crear Categoría", command=guardar, fg_color=self.accent_color, hover_color="#3F51B5", font=("Segoe UI", 13, "bold"), height=35).pack(pady=25)

    def editar_categoria(self, cat_actual):
        win = ctk.CTkToplevel(self)
        win.title("Editar Categoría")
        win.geometry("350x200")
        win.configure(fg_color=self.bg_color)
        win.grab_set()

        ctk.CTkLabel(win, text="Nuevo Nombre:", text_color=self.txt_color, font=("Segoe UI", 13)).pack(pady=(25,5))
        nombre_var = ctk.StringVar(value=cat_actual)
        ctk.CTkEntry(win, textvariable=nombre_var, width=250, height=35).pack()

        def guardar():
            n_nombre = nombre_var.get().strip()
            if not n_nombre: return messagebox.showerror("Error", "Nombre requerido.")
            
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE categories SET name = ? WHERE name = ?", (n_nombre, cat_actual))
                conn.commit()
                conn.close()
                
                self.categorias_db = self.cargar_datos_db()
                self.construir_panel_izquierdo()
                self.mostrar_detalle(n_nombre)
                win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Ya existe esa categoría.")

        ctk.CTkButton(win, text="Guardar Cambios", command=guardar, fg_color=self.accent_color, hover_color="#3F51B5", font=("Segoe UI", 13, "bold"), height=35).pack(pady=25)

    def borrar_categoria(self, cat_actual):
        if messagebox.askyesno("Confirmar", f"¿Eliminar la categoría '{cat_actual}'?"):
            conn = get_connection()
            cursor = conn.cursor()
            
            # Obtener ID de 'Sin Categoría'
            cursor.execute("SELECT id FROM categories WHERE name = 'Sin Categoría'")
            s_row = cursor.fetchone()
            if not s_row:
                cursor.execute("INSERT INTO categories (name) VALUES ('Sin Categoría')")
                sin_cat_id = cursor.lastrowid
            else:
                sin_cat_id = s_row['id']
                
            cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_actual,))
            c_row = cursor.fetchone()
            if c_row:
                c_id = c_row['id']
                cursor.execute("UPDATE products SET category_id = ? WHERE category_id = ?", (sin_cat_id, c_id))
                cursor.execute("DELETE FROM categories WHERE id = ?", (c_id,))
                conn.commit()
            conn.close()
            
            self.categorias_db = self.cargar_datos_db()
            self.construir_panel_izquierdo()
            self.mostrar_detalle("Sin Categoría")
            show_toast(self.master, "Categoría Eliminada. Productos movidos a 'Sin Categoría'.", color_fondo="#E53935")