import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import os

class LoginScreen:
    def __init__(self, master, on_login_success, on_guest_login, user_manager, trial_status="PERMANENT"):
        self.master = master
        self.on_login_success = on_login_success
        self.on_guest_login = on_guest_login
        self.user_manager = user_manager
        
        # Variable para controlar ventanas múltiples (Punto 4)
        self.active_modal = None

        # --- PALETA CORPORATIVA ---
        self.bg_color = "#F5F7FA"
        self.card_bg = "#FFFFFF"
        self.text_main = "#263238"
        self.text_sub = "#90A4AE"
        self.color_primary = "#1565C0"
        self.color_danger = "#D32F2F"
        
        self.master.configure(fg_color=self.bg_color)

        main_layout = ctk.CTkFrame(self.master, fg_color="transparent")
        main_layout.pack(fill="both", expand=True)

        self.card = ctk.CTkFrame(main_layout, corner_radius=16, width=420, height=720, fg_color=self.card_bg, border_width=1, border_color="#E2E8F0")
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        ribbon = ctk.CTkFrame(self.card, height=6, corner_radius=0, fg_color="transparent")
        ribbon.pack(fill="x", padx=24, pady=(24, 0))
        ctk.CTkFrame(ribbon, fg_color=self.color_primary, height=6, corner_radius=3).pack(side="left", fill="x", expand=True, padx=2)
        ctk.CTkFrame(ribbon, fg_color="#F57C00", height=6, corner_radius=3).pack(side="left", fill="x", expand=True, padx=2)
        ctk.CTkFrame(ribbon, fg_color="#2E7D32", height=6, corner_radius=3).pack(side="left", fill="x", expand=True, padx=2)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ruta_ciudad = os.path.join(base_dir, "ui", "assets", "logo_ciudad.png")
        ruta_uni = os.path.join(base_dir, "ui", "assets", "logo_uni.png")

        try:
            img_c = Image.open(ruta_ciudad)
            logo_c = ctk.CTkImage(light_image=img_c, dark_image=img_c, size=(220, 156))
            ctk.CTkLabel(self.card, image=logo_c, text="").pack(pady=(20, 10))
        except Exception:
            ctk.CTkLabel(self.card, text="Almacén Inmaculada", font=("Segoe UI", 24, "bold"), text_color=self.color_primary).pack(pady=(20, 10))

        self.frame_operador = ctk.CTkFrame(self.card, fg_color="transparent")
        self.frame_admin = ctk.CTkFrame(self.card, fg_color="transparent")
        
        self._build_operador_view()
        self._build_admin_view()
        
        self.frame_operador.pack(fill="both", expand=True)

        creditos_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        creditos_frame.pack(side="bottom", pady=(0, 24)) 
        
        try:
            img_u = Image.open(ruta_uni)
            logo_u = ctk.CTkImage(light_image=img_u, dark_image=img_u, size=(120, 48))
            ctk.CTkLabel(creditos_frame, image=logo_u, text="").pack()
        except Exception:
            ctk.CTkLabel(creditos_frame, text="FIIS - UNI", font=("Segoe UI", 11, "bold"), text_color=self.text_sub).pack()

        if trial_status != "PERMANENT":
            warning_text = f"Modo de Prueba: {trial_status} días restantes."
            ctk.CTkLabel(self.master, text=warning_text, font=("Segoe UI", 12, "bold"), text_color=self.color_danger).pack(side="bottom", pady=15)

    # =======================================================
    # VISTA 1: MODO OPERADOR (CORREGIDO PUNTOS 1 y 2)
    # =======================================================
    def _build_operador_view(self):
        ctk.CTkLabel(self.frame_operador, text="Acceso Operativo", font=("Segoe UI", 18, "bold"), text_color=self.text_main).pack(pady=(0, 24))

        # Puntos 1: Input de usuario estilo Google (Privacidad)
        ctk.CTkLabel(self.frame_operador, text="Usuario", font=("Segoe UI", 13, "bold"), text_color=self.text_sub).pack(anchor="w", padx=48)
        self.user_entry = ctk.CTkEntry(self.frame_operador, placeholder_text="Ingrese su nombre de usuario", width=320, height=45, font=("Segoe UI", 14), fg_color="#F8FAFC", border_color="#E2E8F0", text_color=self.text_main)
        self.user_entry.pack(pady=(4, 16))

        # Punto 2: Eliminada la pista de los 6 dígitos (Seguridad)
        ctk.CTkLabel(self.frame_operador, text="Contraseña", font=("Segoe UI", 13, "bold"), text_color=self.text_sub).pack(anchor="w", padx=48)
        self.pin_entry = ctk.CTkEntry(self.frame_operador, show="*", width=320, height=45, font=("Segoe UI", 24, "bold"), fg_color="#F8FAFC", border_color="#E2E8F0", text_color=self.text_main, justify="center")
        self.pin_entry.pack(pady=(4, 24))

        ctk.CTkButton(self.frame_operador, text="Ingresar al Sistema", font=("Segoe UI", 14, "bold"), width=320, height=45, fg_color=self.color_primary, hover_color="#0D47A1", command=self.login_operador).pack(pady=(0, 12))
        
        def guest_login_with_schedule():
            if not self._check_schedule():
                return messagebox.showwarning("Fuera de Horario\n", "El sistema se encuentra fuera del horario laboral\nLunes a Viernes, 08:00 a 18:00")
            self.on_guest_login()

        ctk.CTkButton(self.frame_operador, text="Entrar como Invitado", font=("Segoe UI", 13, "bold"), width=320, height=40, fg_color="transparent", border_width=1, border_color=self.color_primary, text_color=self.color_primary, hover_color="#E3F2FD", command=guest_login_with_schedule).pack(pady=(0, 16))

        ctk.CTkButton(self.frame_operador, text="🔒 Acceso Administrativo", font=("Segoe UI", 12, "underline"), fg_color="transparent", text_color=self.text_sub, hover_color="#F8FAFC", command=self.switch_to_admin).pack(pady=(10, 0))
        self.master.bind('<Return>', lambda event: self.login_operador())

    def _check_schedule(self):
        from datetime import datetime
        import json, os
        
        # 1. Chequear si hay override activo
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        override_file = os.path.join(base_dir, "data", "override_horario.json")
        if os.path.exists(override_file):
            try:
                with open(override_file, "r") as f:
                    data = json.load(f)
                    valid_until_str = data.get("valid_until")
                    if valid_until_str:
                        valid_until = datetime.strptime(valid_until_str, "%Y-%m-%d %H:%M:%S")
                        if datetime.now() < valid_until:
                            return True  # Aprobado por el Administrador
            except:
                pass

        # 2. Flujo normal (L-V 8am-6pm)
        now = datetime.now()
        # Lunes=0, Viernes=4. Restricción L-V, 8am a 6pm
        if now.weekday() > 4:
            return False
        if not (8 <= now.hour < 18):
            return False
        return True

    def login_operador(self):
        if not self._check_schedule():
            return messagebox.showwarning("Fuera de Horario", "El sistema se encuentra fuera del horario laboral (Lunes a Viernes, 08:00 a 18:00).")

        username = self.user_entry.get().strip()
        pin = self.pin_entry.get().strip()
        
        if not username: return messagebox.showerror("Error", "Ingrese su nombre de usuario.")
        if not pin: return messagebox.showerror("Error", "Ingrese su contraseña.")
        
        try:
            if self.user_manager.authenticate(username, pin):
                self.master.unbind('<Return>')
                self.on_login_success(username)
            else:
                self.pin_entry.delete(0, 'end')
                messagebox.showerror("Acceso Denegado", "Credenciales incorrectas.")
        except Exception as e:
            self.pin_entry.delete(0, 'end')
            messagebox.showerror("Bloqueo de Seguridad", str(e))

    # =======================================================
    # VISTA 2: MODO ADMINISTRADOR (CORREGIDO PUNTO 3)
    # =======================================================
    # =======================================================
    # VISTA 2: MODO ADMINISTRADOR (MUDADO AL PANEL INTERNO)
    # =======================================================
    def _build_admin_view(self):
        ctk.CTkLabel(self.frame_admin, text="Panel de Dirección", font=("Segoe UI", 18, "bold"), text_color=self.color_danger).pack(pady=(0, 24))

        ctk.CTkLabel(self.frame_admin, text="Clave Maestra de Ingreso:", font=("Segoe UI", 13, "bold"), text_color=self.text_sub).pack(anchor="w", padx=48)
        self.master_entry = ctk.CTkEntry(self.frame_admin, show="*", width=320, height=45, font=("Segoe UI", 14), fg_color="#F8FAFC", border_color=self.color_danger, text_color=self.text_main)
        self.master_entry.pack(pady=(4, 24))

        ctk.CTkButton(self.frame_admin, text="Iniciar Sesión (Admin)", font=("Segoe UI", 14, "bold"), width=320, height=45, fg_color=self.color_danger, hover_color="#B71C1C", command=self.login_admin).pack(pady=(0, 20))

        # ❌ Se eliminaron los botones de "Gestión de Personal". Ahora están dentro del Panel Admin.
        
        ctk.CTkButton(self.frame_admin, text="⬅ Volver a Operadores", font=("Segoe UI", 12, "underline"), fg_color="transparent", text_color=self.text_sub, hover_color="#F8FAFC", command=self.switch_to_operador).pack(pady=(10, 0))

        
    def login_admin(self):
        clave = self.master_entry.get().strip()
        if not clave: return messagebox.showerror("Error", "Ingrese la Clave Maestra")
        
        try:
            if self.user_manager.authenticate("Administrador", clave):
                self.master.unbind('<Return>')
                self.on_login_success("Administrador")
            else:
                self.master_entry.delete(0, 'end')
                messagebox.showerror("Seguridad", "Clave Maestra incorrecta")
        except Exception as e:
            self.master_entry.delete(0, 'end')
            messagebox.showerror("Bloqueo de Seguridad", str(e))

    def switch_to_admin(self):
        self.frame_operador.pack_forget()
        self.frame_admin.pack(fill="both", expand=True)
        self.master.bind('<Return>', lambda event: self.login_admin())

    def switch_to_operador(self):
        self.master_entry.delete(0, 'end') # Limpiamos la clave por seguridad
        self.frame_admin.pack_forget()
        self.frame_operador.pack(fill="both", expand=True)
        self.master.bind('<Return>', lambda event: self.login_operador())


    # =======================================================
    # HERRAMIENTAS DE ADMIN (CORREGIDAS PUNTOS 4 y 5)
    # =======================================================
    def open_user_generator(self):
        # Punto 4: Bloqueo de múltiples ventanas
        if self.active_modal and self.active_modal.winfo_exists():
            self.active_modal.focus()
            return
            
        self.active_modal = ctk.CTkToplevel(self.master)
        self.active_modal.title("🔐 Alta de Usuario")
        self.active_modal.geometry("380x300")
        self.active_modal.transient(self.master)
        self.active_modal.grab_set()
        self.active_modal.configure(fg_color="#F5F7FA")

        ctk.CTkLabel(self.active_modal, text="Nombre del Nuevo Operador:", font=("Segoe UI", 13, "bold"), text_color="#263238").pack(pady=(24, 4))
        u_entry = ctk.CTkEntry(self.active_modal, width=280, height=40, font=("Segoe UI", 14), fg_color="#FFFFFF", border_color="#E2E8F0", text_color="#263238")
        u_entry.pack(pady=(0, 16))

        # Punto 3: Pide la Clave Maestra EN EL MOMENTO de la acción
        ctk.CTkLabel(self.active_modal, text="Clave Maestra de Autorización:", font=("Segoe UI", 13, "bold"), text_color="#D32F2F").pack(pady=(0, 4))
        mk_entry = ctk.CTkEntry(self.active_modal, show="*", width=280, height=40, font=("Segoe UI", 14), fg_color="#FFFFFF", border_color="#D32F2F")
        mk_entry.pack(pady=(0, 24))

        def generate_pin():
            u = u_entry.get().strip()
            mk = mk_entry.get().strip()
            
            # Punto 5: Validación de cadena vacía
            if not u: return messagebox.showerror("Error", "El nombre de usuario no puede estar vacío")
            
            if not self.user_manager.authenticate("Administrador", mk):
                mk_entry.delete(0, 'end')
                return messagebox.showerror("Acceso Denegado", "Clave maestra incorrecta")
                
            try:
                nuevo_pin = self.user_manager.generate_and_save_6digit(u) 
                messagebox.showinfo("Seguridad", f"Operador: {u}\nNuevo PIN asignado: {nuevo_pin}\n\nEntregue este PIN al trabajador")
                self.active_modal.destroy()
            except ValueError: messagebox.showerror("Error", "Este usuario ya existe")
            except Exception as e: messagebox.showerror("Error", f"Ocurrió un error: {e}")

        ctk.CTkButton(self.active_modal, text="Autorizar y Generar", font=("Segoe UI", 14, "bold"), width=280, height=45, fg_color="#2E7D32", hover_color="#1B5E20", command=generate_pin).pack()

    def open_forgot_password(self):
        # Punto 4: Bloqueo de múltiples ventanas
        if self.active_modal and self.active_modal.winfo_exists():
            self.active_modal.focus()
            return
            
        self.active_modal = ctk.CTkToplevel(self.master)
        self.active_modal.title("🛡️ Recuperación de Clave")
        self.active_modal.geometry("380x350")
        self.active_modal.transient(self.master)
        self.active_modal.grab_set()
        self.active_modal.configure(fg_color="#F5F7FA")

        ctk.CTkLabel(self.active_modal, text="Nombre del Operador:", font=("Segoe UI", 13, "bold"), text_color="#263238").pack(pady=(24, 4))
        u_entry = ctk.CTkEntry(self.active_modal, width=280, height=40, font=("Segoe UI", 14), fg_color="#FFFFFF", border_color="#E2E8F0", text_color="#263238")
        u_entry.pack(pady=(0, 16))

        # Punto 3: Pide la Clave Maestra EN EL MOMENTO
        ctk.CTkLabel(self.active_modal, text="Clave Maestra de Autorización:", font=("Segoe UI", 13, "bold"), text_color="#D32F2F").pack(pady=(0, 4))
        mk_entry = ctk.CTkEntry(self.active_modal, show="*", width=280, height=40, font=("Segoe UI", 14), fg_color="#FFFFFF", border_color="#D32F2F")
        mk_entry.pack(pady=(0, 24))

        def ver_pin():
            u = u_entry.get().strip()
            mk = mk_entry.get().strip()
            if not u: return messagebox.showerror("Error", "El nombre de usuario no puede estar vacío")
            if not self.user_manager.authenticate("Administrador", mk): return messagebox.showerror("Acceso Denegado", "Clave maestra incorrecta")
            
            try:
                pin_actual = self.user_manager.get_password(u)
                messagebox.showinfo("Auditoría", f"La clave actual del operador '{u}' es:\n\n{pin_actual}")
                self.active_modal.destroy()
            except ValueError: messagebox.showerror("Error", "El usuario no existe.")

        def resetear_pin():
            u = u_entry.get().strip()
            mk = mk_entry.get().strip()
            if not u: return messagebox.showerror("Error", "El nombre de usuario no puede estar vacío") # Punto 5
            if not self.user_manager.authenticate("Administrador", mk): return messagebox.showerror("Acceso Denegado", "Clave maestra incorrecta")
            
            if messagebox.askyesno("Confirmar", f"¿Generar NUEVA clave para '{u}'?"):
                try:
                    nuevo_pin = self.user_manager.reset_password(u)
                    messagebox.showinfo("Éxito", f"La NUEVA clave para '{u}' es:\n\n{nuevo_pin}")
                    self.active_modal.destroy()
                except ValueError: messagebox.showerror("Error", "El usuario no existe")

        botones_frame = ctk.CTkFrame(self.active_modal, fg_color="transparent")
        botones_frame.pack(fill="x", padx=48)

        ctk.CTkButton(botones_frame, text="👁️ Ver Clave Actual", font=("Segoe UI", 12, "bold"), height=40, fg_color="#1565C0", hover_color="#0D47A1", command=ver_pin).pack(fill="x", pady=(0, 12))
        ctk.CTkButton(botones_frame, text="🔄 Resetear Clave", font=("Segoe UI", 12, "bold"), height=40, fg_color="#F57C00", hover_color="#E65100", command=resetear_pin).pack(fill="x")


