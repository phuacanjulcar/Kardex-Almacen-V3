import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

class ExitWindow:
    def __init__(self, master, manager, current_user, on_success=None):
        self.master = master
        self.manager = manager
        self.current_user = current_user
        self.on_success = on_success

        self.win = ctk.CTkToplevel(master)
        self.win.title("Registrar Salida")
        self.win.geometry("500x650")
        self.win.attributes("-alpha", 0.0) # Start invisible
        self.win.grab_set()

        from ui.theme import Theme
        self.win.configure(fg_color=Theme.BG_GENERAL)

        self.lotes_disp = [l for l in self.manager.inventory_lots if l.get("status", "Disponible") == "Disponible"]
        if not self.lotes_disp:
            messagebox.showerror("Sin Stock", "El almacen esta vacio. No hay paquetes disponibles para retirar.")
            self.win.destroy()
            return

        form = ctk.CTkFrame(self.win, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=20)

        hoy = datetime.now().strftime("%d/%m/%Y")
        hora_act = datetime.now().strftime("%H:%M")
        
        self.fecha_var = ctk.StringVar(value=hoy)
        self.hora_var = ctk.StringVar(value=hora_act)
        self.qty_var = ctk.StringVar()

        def parse_date(d_str):
            try: return datetime.strptime(d_str, "%Y-%m-%d")
            except: return datetime.max
        self.lotes_disp.sort(key=lambda x: parse_date(x.get("fv", "")))

        self.lotes_dict = {}
        for l in self.lotes_disp:
            lid = l.get("lote_id", "Sin Cod.")
            qty = l.get("qty", 0)
            fv = l.get("fv", "-")
            text = f"{lid} (Stock: {qty} | Vence: {fv})"
            self.lotes_dict[text] = lid
            
        self.lote_sel_var = ctk.StringVar(value=list(self.lotes_dict.keys())[0])

        from ui.tooltip import crear_label_con_ayuda
        
        crear_label_con_ayuda(form, "Lote / Paquete a Descontar", "El grupo específico de productos del cual se restarán unidades. El sistema sugiere siempre el más próximo a vencer (FEFO).", font=("Segoe UI", 13, "bold"), text_color=Theme.PRIMARY).pack(anchor="w")
        ctk.CTkLabel(form, text="* El sistema te sugiere el mas proximo a vencer", font=("Segoe UI", 10, "italic"), text_color=Theme.DANGER).pack(anchor="w")
        ctk.CTkOptionMenu(form, variable=self.lote_sel_var, values=list(self.lotes_dict.keys()), height=40, font=("Segoe UI", 13)).pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form, text="Fecha de Salida (DD/MM/AAAA)", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkEntry(form, textvariable=self.fecha_var, height=35).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Hora (HH:MM)", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkEntry(form, textvariable=self.hora_var, height=35).pack(fill="x", pady=(0, 10))

        # --- TIPO DE SALIDA / MOTIVO ---
        crear_label_con_ayuda(form, "Motivo de Salida", "Razón por la cual el producto abandona el almacén.", font=("Segoe UI", 12, "bold"), text_color=Theme.PRIMARY).pack(anchor="w")
        motivos = [
            "Consumo Regular", 
            "Despacho Externo / Proyectos", 
            "Merma", 
            "Devolución a Proveedor"
        ]
        if self.current_user == "Administrador":
            motivos.append("Ajuste de Inventario Físico (-)")
            
        self.motivo_var = ctk.StringVar(value=motivos[0])
        self.motivo_combo = ctk.CTkOptionMenu(form, variable=self.motivo_var, values=motivos, height=35, command=self._on_motivo_change)
        self.motivo_combo.pack(fill="x", pady=(0, 2))
        
        self.lbl_motivo_desc = ctk.CTkLabel(form, text="", font=("Segoe UI", 11, "italic"), text_color=Theme.TEXT_MUTED)
        self.lbl_motivo_desc.pack(anchor="w", pady=(0, 10))
        # ---------------------------------

        crear_label_con_ayuda(form, "Destino / Uso (Escribe o Selecciona)", "El lugar, comedor o área que recibirá y utilizará el producto.", font=("Segoe UI", 12)).pack(anchor="w")
        destinos = ["Despacho General"]
        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM destinations ORDER BY name ASC")
            rows = cursor.fetchall()
            conn.close()
            if rows:
                destinos = [r['name'] for r in rows]
        except Exception as e:
            print("Error cargando destinos en exit_window:", e)
            
        self.destino_combo = ctk.CTkComboBox(form, values=destinos, height=35)
        if destinos:
            self.destino_combo.set(destinos[0])
        self.destino_combo.pack(fill="x", pady=(0, 10))

        # --- NUEVO: DOBLE FIRMA ---
        crear_label_con_ayuda(form, "Persona que Recibe (Nombre / Firma)", "Nombre de quien se hace responsable de llevarse el producto.", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.receptor_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.receptor_var, height=35).pack(fill="x", pady=(0, 15))
        # --------------------------

        unidad_txt = self.manager.metadata.get('Unidad', 'Unidades')
        ctk.CTkLabel(form, text=f"Cantidad a Sacar ({unidad_txt})", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ctk.CTkEntry(form, textvariable=self.qty_var, height=40).pack(fill="x", pady=(0, 25))

        self.btn_save = ctk.CTkButton(form, text="Registrar Salida", fg_color=Theme.DANGER, hover_color=Theme.DANGER_HOVER, height=45, font=("Segoe UI", 15, "bold"), command=self.save)
        self.btn_save.pack(fill="x")
        
        self._on_motivo_change(self.motivo_var.get())

    def _on_motivo_change(self, value):
        desc = ""
        if "Consumo" in value:
            desc = "Salida diaria de insumos hacia la cocina o comedor."
        elif "Despacho" in value:
            desc = "Envíos a otras sedes, obras o eventos externos."
        elif "Merma" in value:
            desc = "Pérdida por daño o vencimiento (Requiere clave de Admin)."
        elif "Devolución" in value:
            desc = "Retorno de mercadería defectuosa al proveedor."
        elif "Ajuste" in value:
            desc = "Regularización de faltantes por robo o pérdida."
            
        if hasattr(self, 'lbl_motivo_desc'):
            self.lbl_motivo_desc.configure(text=desc)

    def save(self):
        self.btn_save.configure(state="disabled")
        self.win.update()
        try:
            self._save_logic()
        finally:
            if self.win.winfo_exists():
                self.btn_save.configure(state="normal")

    def _save_logic(self):
        fecha_ui = self.fecha_var.get().strip()
        hora = self.hora_var.get().strip()
        destino = self.destino_combo.get().strip()
        qty_str = self.qty_var.get().strip()
        
        lote_text = self.lote_sel_var.get()
        lote_id = self.lotes_dict.get(lote_text)
        
        # --- NUEVO: Motor FEFO Pre-selectivo con Excepción ---
        lote_recomendado = list(self.lotes_dict.values())[0]
        if lote_id != lote_recomendado:
            msg_fefo = (f"ATENCIÓN FEFO:\n\n"
                        f"El sistema recomienda despachar el lote {lote_recomendado} "
                        f"porque vence más pronto.\n\n"
                        f"Has seleccionado {lote_id}.\n\n"
                        f"¿Estás seguro de saltar la sugerencia FEFO?\n"
                        f"(Ej: Hazlo solo si el lote que seleccionaste ya tiene el empaque abierto)")
            if not messagebox.askyesno("Advertencia FEFO", msg_fefo):
                return
        # -----------------------------------------------------

        if not fecha_ui or not hora or not qty_str or not destino: 
            return messagebox.showerror("Error", "Completa todos los campos.")

        try:
            dt_fecha = datetime.strptime(fecha_ui, "%d/%m/%Y")
            fecha_backend = dt_fecha.strftime("%Y-%m-%d")
            datetime.strptime(hora, "%H:%M")
        except ValueError:
            return messagebox.showerror("Formato Invalido", "La fecha debe ser DD/MM/AAAA y la hora HH:MM")

        try:
            qty = float(qty_str)
            if qty <= 0:
                return messagebox.showerror("Error", "La cantidad debe ser mayor a cero.")
                
            unidad_medida = self.manager.metadata.get('Unidad', '')
            if unidad_medida == "Unidades (Und)":
                if not float(qty).is_integer():
                    return messagebox.showerror("Logica Invalida", "No puedes registrar decimales en 'Unidades'.")

            motivo = self.motivo_var.get()
            
            # --- NUEVO: APROBACIÓN ESTRICTA DE MERMAS ---
            if "Merma" in motivo:
                dialog = ctk.CTkInputDialog(text="Autorización requerida.\nIngresa la Clave Maestra de Administrador:", title="Autorizar Merma")
                clave = dialog.get_input()
                if not self.manager.user_manager.authenticate("Administrador", clave):
                    return messagebox.showerror("Autorización Denegada", "Clave incorrecta. No se puede registrar la merma.")
                motivo = f"{motivo} (Autorizado por Admin)"
            # --------------------------------------------

            receptor = self.receptor_var.get().strip()
            if not receptor:
                return messagebox.showerror("Error", "Debes ingresar el nombre de la persona que recibe.")
            
            destino_final = f"{destino} | Recibe: {receptor}"

            ok, msg = self.manager.register_exit(f"{fecha_backend} {hora}", qty, destino_final, self.current_user, lote_id, concept=motivo)
            if not ok: 
                return messagebox.showerror("Stock Insuficiente", msg)

            messagebox.showinfo("Exito", f"Salida del paquete {lote_id} registrada correctamente.")

            self.win.destroy()
            if self.on_success: self.on_success()
            
        except ValueError:
            return messagebox.showerror("Error", "Cantidad invalida. Ingresa un numero valido.")