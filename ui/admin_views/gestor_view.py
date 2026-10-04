import customtkinter as ctk
import os
import sqlite3
from tkinter import messagebox
from core.database import get_connection

class GestorView(ctk.CTkFrame):
    def __init__(self, parent, controller, base_dir):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.modo = ctk.get_appearance_mode()
        self.pack(fill="both", expand=True)
        
        self._construir_ui()

    def _construir_ui(self):
        txt_main = "#0F172A" if self.modo == "Light" else "#FFFFFF"
        ctk.CTkLabel(self, text="Gestor de Zonas, Categorias y Destinos", font=("Segoe UI", 26, "bold"), text_color=txt_main).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Administra ubicaciones, clasificaciones y destinos predeterminados.", font=("Segoe UI", 14), text_color="#64748B").pack(anchor="w", pady=(0, 20))

        # Contenedor Principal
        container = ctk.CTkFrame(self, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0" if self.modo=="Light" else "#334155")
        container.pack(fill="both", expand=True)

        # Interruptor (Segmented Button)
        self.filtro_var = ctk.StringVar(value="Zonas Fisicas")
        self.filtro_btn = ctk.CTkSegmentedButton(
            container, 
            values=["Zonas Fisicas", "Categorias", "Destinos Predeterminados"], 
            variable=self.filtro_var, 
            command=self._cargar_lista
        )
        from ui.components.theme import Theme
        Theme.apply_segmented_button_style(self.filtro_btn)
        self.filtro_btn.pack(fill="x", padx=20, pady=20)

        # Formulario de Agregar
        form_frame = ctk.CTkFrame(container, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.entry_nuevo = ctk.CTkEntry(form_frame, placeholder_text="Escriba el nombre del nuevo elemento...", height=40)
        self.entry_nuevo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(form_frame, text="Agregar", font=("Segoe UI", 13, "bold"), fg_color="#10B981", hover_color="#059669", height=40, width=100, command=self._agregar_item).pack(side="right")

        # Lista Scrollable
        self.scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=15, pady=10)

        self._cargar_lista()

    def _cargar_lista(self, *args):
        for widget in self.scroll.winfo_children():
            widget.destroy()
            
        conn = get_connection()
        cursor = conn.cursor()
        
        if self.filtro_var.get() == "Zonas Fisicas":
            cursor.execute("SELECT id, name FROM zones ORDER BY name")
        elif self.filtro_var.get() == "Categorias":
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
        else:
            cursor.execute("SELECT id, name FROM destinations ORDER BY name")
            
        datos = cursor.fetchall()
        conn.close()

        if not datos:
            ctk.CTkLabel(self.scroll, text="No hay elementos registrados.", text_color="#64748B", font=("Segoe UI", 13, "italic")).pack(pady=20)
            return

        for fila in datos:
            id_item = fila['id']
            nombre = fila['name']
            
            item_frame = ctk.CTkFrame(self.scroll, fg_color="#F8FAFC" if self.modo == "Light" else "#0F172A", corner_radius=6, border_width=1, border_color="#E2E8F0" if self.modo=="Light" else "#334155")
            item_frame.pack(fill="x", pady=3)
            
            ctk.CTkLabel(item_frame, text=nombre, font=("Segoe UI", 14, "bold")).pack(side="left", padx=15, pady=10)
            
            # Botones
            btn_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=15)
            
            # No se puede eliminar ni editar los default si están asignados de manera crítica, pero dejaremos editar su nombre si quieren.
            if nombre not in ("Sin Asignar", "Sin Categoría"):
                ctk.CTkButton(btn_frame, text="Eliminar", font=("Segoe UI", 11, "bold"), fg_color="transparent", border_width=1, border_color="#EF4444", text_color="#EF4444", hover_color="#FEE2E2" if self.modo=="Light" else "#4A1C1C", width=70, height=28, command=lambda i=id_item, n=nombre: self._eliminar_item(i, n)).pack(side="right", padx=(5, 0))
                
            ctk.CTkButton(btn_frame, text="Editar", font=("Segoe UI", 11, "bold"), fg_color="transparent", border_width=1, border_color="#38BDF8", text_color="#38BDF8", hover_color="#E0F2FE" if self.modo=="Light" else "#1E293B", width=70, height=28, command=lambda i=id_item, n=nombre: self._editar_item(i, n)).pack(side="right", padx=0)

    def _agregar_item(self):
        nuevo_valor = self.entry_nuevo.get().strip()
        if not nuevo_valor:
            return messagebox.showwarning("Aviso", "El campo no puede estar vacío.")
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            if self.filtro_var.get() == "Zonas Fisicas":
                cursor.execute("INSERT INTO zones (name) VALUES (?)", (nuevo_valor,))
            elif self.filtro_var.get() == "Categorias":
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (nuevo_valor,))
            else:
                cursor.execute("INSERT INTO destinations (name) VALUES (?)", (nuevo_valor,))
            conn.commit()
            conn.close()
            
            self.entry_nuevo.delete(0, 'end')
            self.controller.mostrar_toast(f"Agregado correctamente", color_fondo="#10B981")
            self._cargar_lista()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Este elemento ya existe en la base de datos.")

    def _editar_item(self, id_item, nombre_actual):
        dialog = ctk.CTkInputDialog(text="Ingrese el nuevo nombre:", title="Editar")
        nuevo_nombre = dialog.get_input()
        
        if not nuevo_nombre or nuevo_nombre.strip() == "":
            return
            
        nuevo_nombre = nuevo_nombre.strip()
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            if self.filtro_var.get() == "Zonas Fisicas":
                cursor.execute("UPDATE zones SET name = ? WHERE id = ?", (nuevo_nombre, id_item))
            elif self.filtro_var.get() == "Categorias":
                cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (nuevo_nombre, id_item))
            else:
                cursor.execute("UPDATE destinations SET name = ? WHERE id = ?", (nuevo_nombre, id_item))
            conn.commit()
            conn.close()
            
            self.controller.mostrar_toast(f"Actualizado correctamente", color_fondo="#3B82F6")
            self._cargar_lista()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Ya existe un elemento con ese nombre.")

    def _eliminar_item(self, id_item, nombre):
        if not messagebox.askyesno("Confirmar", f"¿Seguro que desea eliminar '{nombre}'?\n\nLos productos asociados a este elemento se moverán a una ubicación/categoría temporal."):
            return
            
        conn = get_connection()
        cursor = conn.cursor()
        
        if self.filtro_var.get() == "Zonas Fisicas":
            # Obtener o crear ID de 'Sin Asignar'
            cursor.execute("SELECT id FROM zones WHERE name = 'Sin Asignar'")
            row = cursor.fetchone()
            if not row:
                cursor.execute("INSERT INTO zones (name) VALUES ('Sin Asignar')")
                fallback_id = cursor.lastrowid
            else:
                fallback_id = row['id']
                
            cursor.execute("UPDATE products SET zone_id = ? WHERE zone_id = ?", (fallback_id, id_item))
            cursor.execute("DELETE FROM zones WHERE id = ?", (id_item,))
            
        elif self.filtro_var.get() == "Categorias":
            # Obtener o crear ID de 'Sin Categoría'
            cursor.execute("SELECT id FROM categories WHERE name = 'Sin Categoría'")
            row = cursor.fetchone()
            if not row:
                cursor.execute("INSERT INTO categories (name) VALUES ('Sin Categoría')")
                fallback_id = cursor.lastrowid
            else:
                fallback_id = row['id']
                
            cursor.execute("UPDATE products SET category_id = ? WHERE category_id = ?", (fallback_id, id_item))
            cursor.execute("DELETE FROM categories WHERE id = ?", (id_item,))
            
        else:
            # Eliminar Destino (no necesita reasignar productos)
            cursor.execute("DELETE FROM destinations WHERE id = ?", (id_item,))

        conn.commit()
        conn.close()
            
        self.controller.mostrar_toast("Elemento eliminado", color_fondo="#EF4444")
        self._cargar_lista()