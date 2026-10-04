import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os, json, random, re
from datetime import datetime
from PIL import Image
from core.database import get_connection
from ui.components.toast import show_toast

# Importamos las ventanas adicionales
from ui.windows.recepcion_masiva import RecepcionMasivaWindow
from ui.windows.vale_despacho import ValeDespachoWindow
# PON ESTO:
from ui.modals.alertas_window import AlertasWindow
from ui.modals.zonas_window import ZonasWindow
from ui.modals.categorias_window import CategoriasWindow

# Como este archivo está dentro de 'ui', retrocedemos un nivel para llegar a la raíz
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class KardexSelector(ctk.CTkFrame):
    def __init__(self, master, on_select, current_user, on_logout):
        super().__init__(master, fg_color="transparent")
        self.master = master
        self.on_select = on_select
        self.current_user = current_user
        self.on_logout = on_logout
        self.is_guest = (current_user == "Invitado")
        self.pack(fill="both", expand=True)

        modo = ctk.get_appearance_mode()
        bg_color = "#121212" if modo == "Dark" else "#F4F7FB"
        card_bg = "#1E1E2F" if modo == "Dark" else "#FFFFFF"
        txt_color = "#FFFFFF" if modo == "Dark" else "#121212"
        sub_txt = "#94A3B8" if modo == "Dark" else "#546E7A"
        title_color = "#38BDF8" if modo == "Dark" else "#0073C2"

        main_layout = ctk.CTkFrame(self, fg_color=bg_color, corner_radius=0)
        main_layout.pack(fill="both", expand=True)

        self.card = ctk.CTkFrame(main_layout, fg_color=card_bg, corner_radius=15, border_width=1, border_color="#333344" if modo == "Dark" else "#E2E8F0", width=520, height=745)
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        ribbon = ctk.CTkFrame(self.card, height=6, corner_radius=0, fg_color="transparent")
        ribbon.pack(fill="x", padx=25, pady=(15, 0))
        ctk.CTkFrame(ribbon, fg_color="#0073C2", corner_radius=5, height=6).pack(side="left", fill="x", expand=True, padx=2)
        ctk.CTkFrame(ribbon, fg_color="#FFC107", corner_radius=5, height=6).pack(side="left", fill="x", expand=True, padx=2)
        ctk.CTkFrame(ribbon, fg_color="#4CAF50", corner_radius=5, height=6).pack(side="left", fill="x", expand=True, padx=2)

        logos_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        logos_frame.pack(pady=(10, 0))

        try:
            ruta_ciudad = os.path.join(BASE_DIR, "ui", "assets", "logo_ciudad.png")
            img_c = Image.open(ruta_ciudad)
            logo_ciudad = ctk.CTkImage(light_image=img_c, dark_image=img_c, size=(200, 142))
            ctk.CTkLabel(logos_frame, image=logo_ciudad, text="").pack(pady=(0, 5))
            
            frases = [
                "Administrando con el corazón para nutrir su futuro",
                "Acogiendo con amor y esperanza desde 1955",
                "Más que un albergue, una gran familia que abraza",
                "Organizando hoy lo que construirá su mañana",
                "Cuidando los detalles que transforman sus vidas"
            ]
            ctk.CTkLabel(self.card, text=f'"{random.choice(frases)}"', font=("Segoe UI", 13, "italic"), text_color=sub_txt).pack(pady=(0, 5))
            ctk.CTkLabel(self.card, text=f"Sesión activa: {self.current_user}", font=("Segoe UI", 14, "bold"), text_color=title_color).pack(pady=(0, 5))

        except Exception:
            ctk.CTkLabel(self.card, text="Almacén Inmaculada", font=("Segoe UI", 26, "bold"), text_color=title_color).pack(pady=(20, 10))

        opciones = self._list_kardex_names()
        self.combo_kardex = ctk.CTkOptionMenu(
            self.card, values=opciones, font=("Segoe UI", 15), width=340, height=45, 
            fg_color="#2A2D43" if modo == "Dark" else "#F9FBFD", 
            text_color=txt_color, 
            button_color="#0073C2", button_hover_color="#005A9E"
        )
        self.combo_kardex.set(opciones[0] if opciones else "")
        self.combo_kardex.pack(pady=(10, 5))

        btn_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        btn_frame.pack(pady=0)

        # Cargar Iconos
        ic_add = ctk.CTkImage(Image.open(os.path.join(BASE_DIR, "ui", "assets", "ic_add.png")), size=(18,18))
        ic_alert = ctk.CTkImage(Image.open(os.path.join(BASE_DIR, "ui", "assets", "ic_alert.png")), size=(18,18))
        ic_zone = ctk.CTkImage(Image.open(os.path.join(BASE_DIR, "ui", "assets", "ic_zone.png")), size=(18,18))
        ic_cat = ctk.CTkImage(Image.open(os.path.join(BASE_DIR, "ui", "assets", "ic_category.png")), size=(18,18))
        ic_rec = ctk.CTkImage(Image.open(os.path.join(BASE_DIR, "ui", "assets", "ic_receive.png")), size=(18,18))
        ic_des = ctk.CTkImage(Image.open(os.path.join(BASE_DIR, "ui", "assets", "ic_dispatch.png")), size=(18,18))

        # Botones Principales
        ctk.CTkButton(btn_frame, text="Abrir Producto", font=("Segoe UI", 14, "bold"), fg_color="#0073C2", hover_color="#005A9E", width=165, height=40, command=self.open_kardex).grid(row=0, column=0, padx=5, pady=5)
        btn_crear = ctk.CTkButton(btn_frame, image=ic_add, text=" Crear Nuevo", font=("Segoe UI", 14, "bold"), fg_color="#2E7D32", hover_color="#1B5E20", width=165, height=40, command=self.create_kardex_window)
        btn_crear.grid(row=0, column=1, padx=5, pady=5)
        
        # --- SEPARACION DE BOTONES (HERRAMIENTAS) ---
        tools_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        tools_frame.pack(pady=5, fill="x", expand=True, padx=10)
        tools_frame.grid_columnconfigure(0, weight=1)
        tools_frame.grid_columnconfigure(1, weight=1)

        # Fila 0: Alertas (Ocupa todo el ancho)
        btn_alertas = ctk.CTkButton(tools_frame, image=ic_alert, text=" Radar de Alertas", font=("Segoe UI", 13, "bold"), fg_color="#E53935", hover_color="#C62828", text_color="#FFFFFF", height=35, command=lambda: AlertasWindow(self.master, self.current_user))
        btn_alertas.grid(row=0, column=0, columnspan=2, pady=3, sticky="ew")
        
        # Fila 1: Zonas y Categorias (Lectura visual)
        btn_zonas = ctk.CTkButton(tools_frame, image=ic_zone, text=" Zonas", font=("Segoe UI", 13, "bold"), fg_color="#F57C00", hover_color="#E65100", text_color="#FFFFFF", height=35, command=lambda: ZonasWindow(self.master, self.current_user))
        btn_zonas.grid(row=1, column=0, padx=(0, 3), pady=3, sticky="ew")
        
        btn_categorias = ctk.CTkButton(tools_frame, image=ic_cat, text=" Categorías", font=("Segoe UI", 13, "bold"), fg_color="#5C6BC0", hover_color="#3F51B5", text_color="#FFFFFF", height=35, command=lambda: CategoriasWindow(self.master, self.current_user))
        btn_categorias.grid(row=1, column=1, padx=(3, 0), pady=3, sticky="ew")
        
        # Fila 2: Movimientos Masivos (Entrada y Salida)
        btn_recepcion = ctk.CTkButton(tools_frame, image=ic_rec, text=" Recepción de lotes", font=("Segoe UI", 13, "bold"), fg_color="#8E44AD", hover_color="#732D91", text_color="#FFFFFF", height=35, command=lambda: RecepcionMasivaWindow(self.master, self.current_user))
        btn_recepcion.grid(row=2, column=0, padx=(0, 3), pady=(3, 0), sticky="ew")

        btn_despacho = ctk.CTkButton(tools_frame, image=ic_des, text=" Vale de Despacho", font=("Segoe UI", 13, "bold"), fg_color="#2E7D32", hover_color="#1B5E20", text_color="#FFFFFF", height=35, command=lambda: ValeDespachoWindow(self.master, self.current_user))
        btn_despacho.grid(row=2, column=1, padx=(3, 0), pady=(3, 0), sticky="ew")

        # Fila 3: Preparar Receta
        from ui.windows.user_recipe_view import UserRecipeView
        btn_receta = ctk.CTkButton(tools_frame, text="🍲 Preparar Receta / Fórmula", font=("Segoe UI", 13, "bold"), fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF", height=35, command=lambda: UserRecipeView(self.master, self.current_user))
        btn_receta.grid(row=3, column=0, columnspan=2, pady=(5, 0), sticky="ew")

        # ====================================================
        # BLOQUEO ABSOLUTO PARA INVITADOS
        # ====================================================
        if self.is_guest: 
            btn_crear.configure(state="disabled")
            btn_alertas.configure(state="disabled")
            btn_zonas.configure(state="disabled")
            btn_categorias.configure(state="disabled")
            btn_recepcion.configure(state="disabled")
            btn_despacho.configure(state="disabled")
            btn_receta.configure(state="disabled")

        bottom_nav = ctk.CTkFrame(self.card, fg_color="transparent")
        bottom_nav.pack(pady=(10, 5))
        
        ctk.CTkButton(bottom_nav, text="🔄 Actualizar Lista", font=("Segoe UI", 11, "bold"), fg_color="transparent", border_width=1, border_color="#0073C2" if modo == "Light" else "#38BDF8", text_color=title_color, hover_color="#E0F2FE" if modo == "Light" else "#1E293B", width=165, height=30, command=self.refresh_list).grid(row=0, column=0, padx=5)
        ctk.CTkButton(bottom_nav, text="Cerrar Sesión", font=("Segoe UI", 11, "bold"), fg_color="transparent", border_width=1, border_color="#E53935", text_color="#E53935", hover_color="#FFEBEE" if modo == "Light" else "#4A1C1C", width=165, height=30, command=self.on_logout).grid(row=0, column=1, padx=5)

        badge_bg = "#FFFFFF" if modo == "Dark" else "transparent"
        badge_border = 1 if modo == "Dark" else 0
        
        creditos_badge = ctk.CTkFrame(self.card, fg_color=badge_bg, corner_radius=10, border_width=badge_border, border_color="#333344")
        creditos_badge.pack(pady=(5, 15), padx=40, fill="x")

        ctk.CTkLabel(creditos_badge, text="Con el respaldo académico de:", font=("Segoe UI", 11, "italic"), text_color=sub_txt).pack(pady=(5, 0))
        try:
            ruta_uni = os.path.join(BASE_DIR, "ui", "assets", "logo_uni.png")
            img_u = Image.open(ruta_uni)
            logo_uni = ctk.CTkImage(light_image=img_u, dark_image=img_u, size=(90, 36))
            ctk.CTkLabel(creditos_badge, image=logo_uni, text="").pack(pady=(0, 10))
        except Exception:
            pass
        # Iniciar buscador de notificaciones (Buzón)
        NOTIFICATIONS_FILE = os.path.join(BASE_DIR, "data", "notificaciones.json")
        self._check_notifications(NOTIFICATIONS_FILE)

    def _list_kardex_names(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM products WHERE is_active = 1 ORDER BY name ASC")
            nombres = [row['name'] for row in cursor.fetchall()]
            conn.close()
            return nombres if nombres else ["-- Sin Archivos --"]
        except Exception:
            return ["-- Sin Archivos --"]

    def refresh_list(self):
        opciones = self._list_kardex_names()
        self.combo_kardex.configure(values=opciones)
        self.combo_kardex.set(opciones[0] if opciones else "")
        show_toast(self.master, "Lista actualizada", color_fondo="#10B981")


    def open_kardex(self):
        name = self.combo_kardex.get().strip()
        if not name or name == "-- Sin Archivos --": return show_toast(self.master, "No hay producto seleccionado", color_fondo="#E53935")
        self.on_select(name)

    def borrar_kardex_fisico(self):
        if self.is_guest: return messagebox.showerror("Acceso Denegado", "Los invitados no pueden borrar archivos")
        name = self.combo_kardex.get().strip()
        if not name or name == "-- Sin Archivos --": return messagebox.showerror("Error", "Seleccione un Kardex")
        if not messagebox.askyesno("ADVERTENCIA", f"¿Desactivar el Producto '{name}'?\nYa no aparecerá en las listas, pero su historial de movimientos se mantendrá en la base de datos."): return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET is_active = 0 WHERE name = ?", (name,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Desactivado", f"El Producto '{name}' ha sido desactivado")
            self.refresh_list()
        except Exception as e: messagebox.showerror("Error", f"No se pudo eliminar:\n{e}")

    def create_kardex_window(self):
        modo = ctk.get_appearance_mode()
        bg_window = "#1E1E2F" if modo == "Dark" else "#FFFFFF"
        txt_color = "#FFFFFF" if modo == "Dark" else "#121212"
        title_color = "#38BDF8" if modo == "Dark" else "#0073C2"

        win = ctk.CTkToplevel(self.master)
        win.title("Crear Nuevo Producto")
        win.geometry("450x450") 
        win.configure(fg_color=bg_window)
        win.grab_set()

        ctk.CTkLabel(win, text="Datos del Producto (Modo Rapido)", font=("Segoe UI", 18, "bold"), text_color=title_color).pack(pady=(20, 15))
        form = ctk.CTkFrame(win, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)

        ctk.CTkLabel(form, text="Nombre del Producto (Ej: Cebolla China):", anchor="w", font=("Segoe UI", 12, "bold"), text_color=txt_color).pack(fill="x")
        prod_entry = ctk.CTkEntry(form, height=35)
        prod_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form, text="Prefijo del Paquete (Ej: CEB):", anchor="w", text_color=txt_color).pack(fill="x")
        prefijo_entry = ctk.CTkEntry(form, height=35, placeholder_text="CEB")
        prefijo_entry.pack(fill="x", pady=(0, 15))

        row_frame = ctk.CTkFrame(form, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 15))
        
        col1 = ctk.CTkFrame(row_frame, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(col1, text="Unidades:", anchor="w", text_color=txt_color).pack(fill="x")
        unidades = ["Kilogramos (Kg)", "Gramos (g)", "Litros (L)", "Unidades (Und)"]
        unidad_combo = ctk.CTkOptionMenu(col1, values=unidades, height=35, fg_color="#0073C2")
        unidad_combo.pack(fill="x")

        col2 = ctk.CTkFrame(row_frame, fg_color="transparent")
        col2.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(col2, text="Stock Minimo:", anchor="w", text_color=txt_color).pack(fill="x")
        stock_min_entry = ctk.CTkEntry(col2, height=35)
        stock_min_entry.insert(0, "10") 
        stock_min_entry.pack(fill="x")

        col3 = ctk.CTkFrame(row_frame, fg_color="transparent")
        col3.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(col3, text="Stock Máximo:", anchor="w", text_color=txt_color).pack(fill="x")
        stock_max_entry = ctk.CTkEntry(col3, height=35)
        stock_max_entry.insert(0, "100") 
        stock_max_entry.pack(fill="x")

        # --- SELECTORES DE ZONA Y CATEGORIA (Solo Admin) ---
        zone_var = ctk.StringVar(value="Sin Asignar")
        cat_var = ctk.StringVar(value="Sin Categoría")
        
        if self.current_user == "Administrador":
            ctk.CTkLabel(form, text="Asignación (Administrador):", font=("Segoe UI", 12, "bold"), text_color=txt_color).pack(pady=(15, 5))
            
            # Traer zonas y categorias
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM zones ORDER BY name")
            zonas = [r['name'] for r in cursor.fetchall()]
            cursor.execute("SELECT name FROM categories ORDER BY name")
            cats = [r['name'] for r in cursor.fetchall()]
            conn.close()
            
            admin_row = ctk.CTkFrame(form, fg_color="transparent")
            admin_row.pack(fill="x")
            
            z_frame = ctk.CTkFrame(admin_row, fg_color="transparent")
            z_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
            ctk.CTkLabel(z_frame, text="Zona:", text_color=txt_color).pack(anchor="w")
            ctk.CTkComboBox(z_frame, values=zonas, variable=zone_var, height=30).pack(fill="x")
            
            c_frame = ctk.CTkFrame(admin_row, fg_color="transparent")
            c_frame.pack(side="right", fill="x", expand=True, padx=(5, 0))
            ctk.CTkLabel(c_frame, text="Categoría:", text_color=txt_color).pack(anchor="w")
            ctk.CTkComboBox(c_frame, values=cats, variable=cat_var, height=30).pack(fill="x")
        else:
            ctk.CTkLabel(form, text="Nota: La Zona y Categoria seran asignadas por Administracion.", font=("Segoe UI", 10, "italic"), text_color="#D32F2F").pack(pady=(15, 0))

        def create():
            prod_name = prod_entry.get().strip()
            if not prod_name: return messagebox.showerror("Error", "Ingrese el nombre del producto.")
            
            if prod_name.upper().startswith("VAL-") or prod_name.upper().startswith("REC-"):
                return messagebox.showwarning("Aviso de Sistema", "Los prefijos 'VAL-' y 'REC-' están reservados exclusivamente para los Códigos de Vales de Despacho y Recetas respectivamente.\n\nPor favor, elija un nombre distinto.")
            
            safe_id = prod_name.upper().replace(" ", "_")
            import re
            safe_id = re.sub(r'[^\w\-]', '', safe_id)

            prefijo = prefijo_entry.get().strip().upper()
            if not prefijo: prefijo = "PAQ"
            else: prefijo = prefijo[:3]
            
            if prefijo in ("VAL", "REC"):
                return messagebox.showwarning("Aviso de Sistema", "Los prefijos 'VAL' y 'REC' están reservados exclusivamente para Vales de Despacho y Recetas.\n\nPor favor, elija otro prefijo.")
            
            try: stock_m = float(stock_min_entry.get().strip())
            except ValueError: stock_m = 10.0
            
            try: stock_max = float(stock_max_entry.get().strip())
            except ValueError: stock_max = 100.0

            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM products WHERE name = ?", (safe_id,))
                if cursor.fetchone():
                    conn.close()
                    return messagebox.showerror("Producto ya Existe", "Ya existe un registro con este nombre.")
                    
                # Buscar id de zona elegida
                cursor.execute("SELECT id FROM zones WHERE name = ?", (zone_var.get(),))
                z_row = cursor.fetchone()
                if not z_row: # Si no existe (el usuario tipeó una nueva), crearla
                    cursor.execute("INSERT INTO zones (name) VALUES (?)", (zone_var.get(),))
                    z_id = cursor.lastrowid
                else:
                    z_id = z_row['id']
                
                # Buscar id de categoria elegida
                cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_var.get(),))
                c_row = cursor.fetchone()
                if not c_row: # Si no existe, crearla
                    cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat_var.get(),))
                    c_id = cursor.lastrowid
                else:
                    c_id = c_row['id']
                
                cursor.execute('''
                    INSERT INTO products (name, unit, zone_id, category_id, prefix, min_stock, max_stock, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (safe_id, unidad_combo.get(), z_id, c_id, prefijo, stock_m, stock_max, datetime.now().strftime("%Y-%m-%d %H:%M")))
                
                conn.commit()
                conn.close()
                
                show_toast(self.master, f"Producto {safe_id} creado", color_fondo="#2E7D32")
                win.destroy()
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el producto:\n{e}")

        ic_save = ctk.CTkImage(Image.open(os.path.join(BASE_DIR, "ui", "assets", "ic_save.png")), size=(18,18))
        ctk.CTkButton(win, image=ic_save, text=" Guardar Producto", font=("Segoe UI", 15, "bold"), fg_color="#2E7D32", hover_color="#1B5E20", height=45, command=create).pack(pady=20, padx=30, fill="x")
    # ====================================================
    # SISTEMA DE NOTIFICACIONES (ESTILO GMAIL)
    # ====================================================
    def _check_notifications(self, ruta_archivo=None):
        self.notificaciones_pendientes = []
        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notifications WHERE user = ? AND status = 'unread'", (self.current_user,))
            self.notificaciones_pendientes = [dict(row) for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"Error cargando notificaciones SQLite: {e}")

        if hasattr(self, 'btn_notif'): 
            self.btn_notif.destroy()
            
        if self.notificaciones_pendientes:
            num = len(self.notificaciones_pendientes)
            self.btn_notif = ctk.CTkButton(
                self.card, text=f"🔔({num})", font=("Segoe UI", 12, "bold"), fg_color="#D32F2F", hover_color="#B71C1C", text_color="white", corner_radius=20, width=110, height=35, 
                command=self._open_inbox
            )
            self.btn_notif.place(relx=0.95, rely=0.03, anchor="ne")

    # VISTA 1: El Inbox (Lista de correos)
    def _open_inbox(self):
        self.win_inbox = ctk.CTkToplevel(self.master)
        self.win_inbox.title("🔔")
        self.win_inbox.geometry("450x500")
        self.win_inbox.grab_set()
        self.win_inbox.configure(fg_color="#F5F7FA" if ctk.get_appearance_mode() == "Light" else "#121212")

        ctk.CTkLabel(self.win_inbox, text="Mensajes del Administrador", font=("Segoe UI", 18, "bold")).pack(pady=(20, 10))

        scroll = ctk.CTkScrollableFrame(self.win_inbox, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=5)

        for notif in self.notificaciones_pendientes:
            # Estilo "Correo no leído" (Fondo blanco, texto bold)
            item = ctk.CTkFrame(scroll, fg_color="#FFFFFF" if ctk.get_appearance_mode() == "Light" else "#1E1E2F", corner_radius=5, border_width=1, border_color="#D32F2F")
            item.pack(fill="x", pady=3)
            
            ctk.CTkLabel(item, text="Comunicado Administrativo", font=("Segoe UI", 12, "bold"), text_color="#D32F2F").pack(anchor="w", padx=10, pady=(5, 0))
            ctk.CTkLabel(item, text=f"Fecha: {notif.get('date')} - Clic para leer detalles...", font=("Segoe UI", 10, "italic")).pack(anchor="w", padx=10, pady=(0, 5))
            
            # Botón invisible para abrir el mensaje
            btn_overlay = ctk.CTkButton(item, text=" ", fg_color="transparent", hover_color="#FEE2E2", command=lambda n=notif: self._open_mensaje_detallado(n))
            btn_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            btn_overlay.configure(cursor="hand2")

    # VISTA 2: El Mensaje Abierto (El Detalle Exacto)
    def _open_mensaje_detallado(self, notif):
        win_msg = ctk.CTkToplevel(self.win_inbox)
        win_msg.title(f"Mensaje")
        win_msg.geometry("400x350")
        win_msg.grab_set()
        win_msg.configure(fg_color="#FFFFFF" if ctk.get_appearance_mode() == "Light" else "#1E1E2F")

        # Remitente
        header = ctk.CTkFrame(win_msg, fg_color="#F1F5F9" if ctk.get_appearance_mode() == "Light" else "#0F172A", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="De: Administración", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=20, pady=(15, 0))
        ctk.CTkLabel(header, text=f"Asunto: Observación / Citación", font=("Segoe UI", 11)).pack(anchor="w", padx=20, pady=(0, 15))

        # Cuerpo del mensaje
        cuerpo = ctk.CTkFrame(win_msg, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=20, pady=20)
        
        # FORZAMOS EL COLOR PARA QUE NUNCA SE VUELVA INVISIBLE
        txt_color = "#121212" if ctk.get_appearance_mode() == "Light" else "#FFFFFF"
        
        ctk.CTkLabel(cuerpo, text="Detalle de la Observacion:", font=("Segoe UI", 12, "bold"), text_color=txt_color).pack(anchor="w")
        ctk.CTkLabel(cuerpo, text=notif.get('message', ''), font=("Segoe UI", 13), justify="left", wraplength=350, text_color=txt_color).pack(anchor="w", pady=10)
        
        def marcar_leido():
            try:
                from core.database import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE notifications SET status = 'read' WHERE id = ?", (notif['id'],))
                conn.commit()
                conn.close()
            except Exception as e:
                print("Error marcando como leido", e)
            
            win_msg.destroy()
            self.win_inbox.destroy()
            
            # Recargamos la campana (para actualizar el número)
            self._check_notifications(None)

        ctk.CTkButton(win_msg, text="✔️ Entendido (Marcar Leído)", font=("Segoe UI", 12, "bold"), fg_color="#2E7D32", hover_color="#1B5E20", height=40, command=marcar_leido).pack(side="bottom", fill="x", padx=20, pady=20)

    def check_new_messages(self, event=None):
        show_toast(self.master, "Actualizando bandeja...", "#1565C0")
        self._check_notifications(None)