import customtkinter as ctk
from tkinter import ttk, messagebox

class UsersView(ctk.CTkFrame):
    def __init__(self, parent, controller, user_manager):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.user_manager = user_manager
        self.modo = ctk.get_appearance_mode()
        self.pack(fill="both", expand=True)
        
        self._construir_usuarios()
        self.refresh_users_table()

    def _construir_usuarios(self):
        ctk.CTkLabel(self, text="Gestión de Personal", font=("Segoe UI", 26, "bold"), text_color="#0F172A" if self.modo=="Light" else "white").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self, text="Administra los usuarios del sistema, sus accesos y contraseñas.", font=("Segoe UI", 14), text_color="#64748B").pack(anchor="w", pady=(0, 20))

        # --- Contenedor Superior: Formularios ---
        forms_frame = ctk.CTkFrame(self, fg_color="transparent")
        forms_frame.pack(fill="x", pady=10)
        forms_frame.grid_columnconfigure(0, weight=1)
        forms_frame.grid_columnconfigure(1, weight=1)

        # 1. Crear Usuario
        card_crear = ctk.CTkFrame(forms_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        card_crear.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(card_crear, text="Alta de Nuevo Operario", font=("Segoe UI", 16, "bold"), text_color="#2E7D32").pack(pady=(15, 5))
        
        entry_nuevo = ctk.CTkEntry(card_crear, placeholder_text="Nombre del trabajador (Ej: Carlos)", width=250, height=35)
        entry_nuevo.pack(pady=5)
        
        entry_pass = ctk.CTkEntry(card_crear, placeholder_text="Contraseña Manual (Opcional)", width=250, height=35)
        entry_pass.pack(pady=5)

        def generar_usuario_manual():
            u = entry_nuevo.get().strip()
            p = entry_pass.get().strip()
            if not u: return messagebox.showerror("Error", "El nombre no puede estar vacío.")
            if not p: return messagebox.showerror("Error", "Ingrese una contraseña manual o use el botón de Generar Automática.")
            try:
                if self.user_manager.exists(u):
                    raise ValueError("Este usuario ya existe en el sistema.")
                self.user_manager.add_user_plain(u, p)
                self.controller.mostrar_toast(f"Usuario {u} creado")
                messagebox.showinfo("Éxito", f"Usuario {u} creado con la contraseña manual.")
                entry_nuevo.delete(0, 'end')
                entry_pass.delete(0, 'end')
                self.refresh_users_table()
            except ValueError as e: messagebox.showerror("Error", str(e))
            except Exception as e: messagebox.showerror("Error", f"Ocurrió un error: {e}")

        def generar_usuario_auto():
            u = entry_nuevo.get().strip()
            if not u: return messagebox.showerror("Error", "El nombre no puede estar vacío.")
            try:
                nuevo_pin = self.user_manager.generate_and_save_secure_password(u) 
                self.controller.mostrar_toast(f"Usuario {u} creado")
                messagebox.showinfo("Clave Generada", f"Operador: {u}\nClave Segura Asignada: {nuevo_pin}\n\nEntregue esta clave al trabajador.")
                entry_nuevo.delete(0, 'end')
                entry_pass.delete(0, 'end')
                self.refresh_users_table()
            except ValueError as e: messagebox.showerror("Error", str(e))
            except Exception as e: messagebox.showerror("Error", f"Ocurrió un error: {e}")

        btn_box = ctk.CTkFrame(card_crear, fg_color="transparent")
        btn_box.pack(pady=(5, 15))
        ctk.CTkButton(btn_box, text="Crear (Manual)", font=("Segoe UI", 12, "bold"), fg_color="#1976D2", hover_color="#1565C0", height=35, command=generar_usuario_manual).pack(side="left", padx=5)
        ctk.CTkButton(btn_box, text="Generar Automática", font=("Segoe UI", 12, "bold"), fg_color="#2E7D32", hover_color="#1B5E20", height=35, command=generar_usuario_auto).pack(side="left", padx=5)

        # 2. Resetear Clave
        card_claves = ctk.CTkFrame(forms_frame, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        card_claves.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        ctk.CTkLabel(card_claves, text="Resetear Contraseña", font=("Segoe UI", 16, "bold"), text_color="#F57C00").pack(pady=(15, 5))
        ctk.CTkLabel(card_claves, text="Genera una nueva contraseña automática.", font=("Segoe UI", 12), text_color="#64748B").pack(pady=(0, 10))

        entry_existente = ctk.CTkEntry(card_claves, placeholder_text="Nombre del operario", width=250, height=35)
        entry_existente.pack(pady=5)

        def resetear_pin():
            u = entry_existente.get().strip()
            if not u: return messagebox.showerror("Error", "Ingrese el nombre del operario.")
            if messagebox.askyesno("Confirmación", f"¿Generar NUEVA clave para '{u}'?"):
                try:
                    nuevo_pin = self.user_manager.reset_password(u)
                    self.controller.mostrar_toast(f"Clave reseteada")
                    messagebox.showinfo("Clave Reseteada", f"La NUEVA clave para '{u}' es:\n\n{nuevo_pin}")
                    entry_existente.delete(0, 'end')
                except ValueError: messagebox.showerror("Error", "El usuario no existe.")

        ctk.CTkButton(card_claves, text="Resetear Clave Automática", font=("Segoe UI", 12, "bold"), fg_color="#F57C00", hover_color="#E65100", height=35, width=200, command=resetear_pin).pack(pady=(10, 15))


        # --- Tabla de Usuarios ---
        ctk.CTkLabel(self, text="Lista de Usuarios", font=("Segoe UI", 18, "bold"), text_color="#0F172A" if self.modo=="Light" else "white").pack(anchor="w", pady=(15, 5))
        
        table_container = ctk.CTkFrame(self, fg_color="#FFFFFF" if self.modo == "Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0")
        table_container.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("ID", "Usuario", "Estado", "Fecha de Creación", "Último Acceso")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=8)
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)

        scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self._apply_tree_style()

        def toggle_status():
            sel = self.tree.selection()
            if not sel: return messagebox.showwarning("Aviso", "Selecciona un usuario de la tabla.")
            item = self.tree.item(sel[0])
            u = item['values'][1]
            try:
                self.user_manager.toggle_user_status(u)
                self.refresh_users_table()
                self.controller.mostrar_toast(f"Estado de {u} actualizado")
            except ValueError as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(self, text="Activar / Desactivar Usuario Seleccionado", font=("Segoe UI", 13, "bold"), fg_color="#D32F2F", hover_color="#B71C1C", height=40, command=toggle_status).pack(pady=10)

    def _apply_tree_style(self):
        panel_bg = "#FFFFFF" if self.modo == "Light" else "#1E293B"
        text_color = "#0F172A" if self.modo == "Light" else "#FFFFFF"
        header_bg = "#F8FAFC" if self.modo == "Light" else "#2A2D43"
        header_fg = "#1E293B" if self.modo == "Light" else "#FFFFFF"
        
        style = ttk.Style()
        style.theme_use("default")
        
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=header_bg, foreground=header_fg, borderwidth=0)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30, borderwidth=0, background=panel_bg, foreground=text_color, fieldbackground=panel_bg)
        style.map("Treeview", background=[('selected', '#E0F2FE' if self.modo=="Light" else "#334155")])
        
        if self.modo == "Dark":
            self.tree.tag_configure('par', background='#1E293B', foreground='#FFFFFF')
            self.tree.tag_configure('impar', background='#2A2D43', foreground='#FFFFFF')
            self.tree.tag_configure('inactivo', background='#3F2222', foreground='#FF9999')
        else:
            self.tree.tag_configure('par', background='#FFFFFF', foreground='#121212')
            self.tree.tag_configure('impar', background='#F8FAFC', foreground='#121212')  
            self.tree.tag_configure('inactivo', background='#FFEEEE', foreground='#D32F2F')

    def refresh_users_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        users = self.user_manager.get_all_users()
        for idx, u in enumerate(users):
            estado_txt = "Activo" if u.get('is_active') == 1 else "Inactivo"
            created = u.get('created_at') or "-"
            last = u.get('last_login') or "-"
            
            tag = 'inactivo' if u.get('is_active') == 0 else ('par' if idx % 2 == 0 else 'impar')
            
            self.tree.insert("", "end", values=(
                u.get('id'),
                u.get('username'),
                estado_txt,
                created,
                last
            ), tags=(tag,))