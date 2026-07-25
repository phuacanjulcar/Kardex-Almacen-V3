import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

class EntryWindow:
    def __init__(self, master, manager, current_user, on_success=None):
        self.master = master
        self.manager = manager
        self.current_user = current_user
        self.on_success = on_success

        self.win = ctk.CTkToplevel(master)
        self.win.title("📥 Registrar Entrada")
        self.win.geometry("500x650")
        self.win.grab_set()

        from ui.theme import Theme
        self.win.configure(fg_color=Theme.BG_GENERAL)

        form = ctk.CTkFrame(self.win, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=20)

        # Variables
        hoy = datetime.now().strftime("%d/%m/%Y")
        hora_act = datetime.now().strftime("%H:%M")
        
        self.fecha_var = ctk.StringVar(value=hoy)
        self.hora_var = ctk.StringVar(value=hora_act)
        self.prov_var = ctk.StringVar()
        self.venc_var = ctk.StringVar()
        self.qty_var = ctk.StringVar()
        self.costo_var = ctk.StringVar()

        # --- TIPO DE INGRESO ---
        ctk.CTkLabel(form, text="Tipo de Ingreso", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.tipo_ingreso_var = ctk.StringVar(value="Compra a Proveedor")
        tipos_ingreso = [
            "Compra a Proveedor", 
            "Donación", 
            "Devolución de Área"
        ]
        if self.current_user == "Administrador":
            tipos_ingreso.append("Ajuste de Inventario Físico (+)")
            
        self.tipo_combo = ctk.CTkOptionMenu(form, variable=self.tipo_ingreso_var, values=tipos_ingreso, command=self._on_tipo_change)
        self.tipo_combo.pack(fill="x", pady=(0, 2))
        
        self.lbl_tipo_desc = ctk.CTkLabel(form, text="", font=("Segoe UI", 11, "italic"), text_color=Theme.TEXT_MUTED)
        self.lbl_tipo_desc.pack(anchor="w", pady=(0, 10))

        # UI Elements
        ctk.CTkLabel(form, text="Código de Lote / Paquete", font=("Segoe UI", 12, "bold"), text_color=Theme.PRIMARY).pack(anchor="w")
        
        lote_frame = ctk.CTkFrame(form, fg_color="transparent")
        lote_frame.pack(fill="x", pady=(0, 10))
        
        self.prefijo_base = self.manager.metadata.get('Prefijo', 'PAQ')[:3].upper() + "-"
        self.lbl_prefijo = ctk.CTkLabel(lote_frame, text=self.prefijo_base, font=("Segoe UI", 16, "bold"), text_color=Theme.PRIMARY)
        self.lbl_prefijo.pack(side="left")
        
        # --- NUEVO AUTOGENERADOR INTELIGENTE (Busca el número mayor) ---
        max_num = 0
        for ev in self.manager.kardex_data:
            l_id = ev.get("lote_id", "")
            if l_id.startswith(self.prefijo_base):
                try:
                    num = int(l_id.replace(self.prefijo_base, ""))
                    if num > max_num: max_num = num
                except ValueError:
                    pass
        siguiente = max_num + 1
        
        self.num_lote_var = ctk.StringVar(value=f"{siguiente:06d}")
        self.entry_lote = ctk.CTkEntry(lote_frame, textvariable=self.num_lote_var, height=35, font=("Segoe UI", 14, "bold"), state="disabled")
        self.entry_lote.pack(side="left", fill="x", expand=True, padx=(5,0))
        # -------------------------------------------------------------

        ctk.CTkLabel(form, text="Fecha de Entrada (DD/MM/AAAA)", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkEntry(form, textvariable=self.fecha_var, height=35).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Hora (HH:MM)", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkEntry(form, textvariable=self.hora_var, height=35).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Proveedor / Origen", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkEntry(form, textvariable=self.prov_var, height=35).pack(fill="x", pady=(0, 10))

        self.marca_var = ctk.StringVar()
        ctk.CTkLabel(form, text="Marca / Detalles del Lote (Opcional)", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkEntry(form, textvariable=self.marca_var, height=35, placeholder_text="Ej: Valle Norte, Empaque Azul...").pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Fecha de Vencimiento (DD/MM/AAAA)", font=("Segoe UI", 12, "bold"), text_color="#D32F2F").pack(anchor="w")
        ctk.CTkEntry(form, textvariable=self.venc_var, height=35, placeholder_text="Ej: 31/12/2026").pack(fill="x", pady=(0, 10))

        row_frame = ctk.CTkFrame(form, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 20))

        unidad_txt = self.manager.metadata.get('Unidad', 'Unidades')
        
        col1 = ctk.CTkFrame(row_frame, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(col1, text=f"Cantidad - {unidad_txt}", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkEntry(col1, textvariable=self.qty_var, height=35).pack(fill="x")

        col2 = ctk.CTkFrame(row_frame, fg_color="transparent")
        col2.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(col2, text="Costo Total/Unit (S/)", font=("Segoe UI", 12)).pack(anchor="w")
        self.entry_costo = ctk.CTkEntry(col2, textvariable=self.costo_var, height=35)
        self.entry_costo.pack(fill="x")

        self.btn_save = ctk.CTkButton(form, text="Registrar Entrada", fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, height=40, font=("Segoe UI", 14, "bold"), command=self.save)
        self.btn_save.pack(fill="x", pady=(10,0))
        
        self._on_tipo_change(self.tipo_ingreso_var.get())

    def _on_tipo_change(self, value):
        desc = ""
        if value == "Donación":
            self.lbl_prefijo.configure(text="DON-")
            self.costo_var.set("0.00")
            self.entry_costo.configure(state="disabled")
            desc = "Ingreso de bienes sin costo monetario (Costo cero)."
        elif "Ajuste" in value:
            self.lbl_prefijo.configure(text="AJU-")
            self.costo_var.set("0.00")
            self.entry_costo.configure(state="disabled")
            desc = "Regularización de sobrantes tras un conteo físico."
        elif "Devolución" in value:
            self.lbl_prefijo.configure(text="DEV-")
            self.entry_costo.configure(state="normal")
            desc = "Reingreso de insumos no utilizados por la cocina/comedor."
        else: # Compra a Proveedor
            self.lbl_prefijo.configure(text=self.prefijo_base)
            self.entry_costo.configure(state="normal")
            desc = "Ingreso de mercadería adquirida con costo monetario."
            
        if hasattr(self, 'lbl_tipo_desc'):
            self.lbl_tipo_desc.configure(text=desc)
            
    def save(self):
        self.btn_save.configure(state="disabled")
        self.win.update()
        try:
            self._save_logic()
        finally:
            if self.win.winfo_exists():
                self.btn_save.configure(state="normal")

    def _save_logic(self):
        tipo_ingreso = self.tipo_ingreso_var.get()
        if tipo_ingreso == "Donación":
            pref = "DON-"
        elif "Ajuste" in tipo_ingreso:
            pref = "AJU-"
        elif "Transferencia" in tipo_ingreso:
            pref = "TRF-"
        elif "Devolución" in tipo_ingreso:
            pref = "DEV-"
        elif "Reubicación" in tipo_ingreso:
            pref = "REU-"
        else:
            pref = self.prefijo_base
        
        num_str = self.num_lote_var.get().strip()
        lote_final = f"{pref}{num_str}"
        
        fecha_ui = self.fecha_var.get().strip()
        hora = self.hora_var.get().strip()
        prov = self.prov_var.get().strip() or "Inventario General"
        venc_ui = self.venc_var.get().strip()
        qty_str = self.qty_var.get().strip()
        cu_str = self.costo_var.get().strip()

        if not num_str or not fecha_ui or not hora or not qty_str or not cu_str or not venc_ui: 
            return messagebox.showerror("Error", "Todos los campos son obligatorios.")

        # --- PROTECCIÓN CONTRA LOTES REPETIDOS ---
        for ev in self.manager.kardex_data:
            if ev.get("type") in ["E", "SI"] and ev.get("lote_id") == lote_final:
                return messagebox.showerror("Lote Duplicado", f"El paquete {lote_final} ya fue registrado anteriormente.\nPor favor usa un número diferente.")

        try:
            dt_fecha = datetime.strptime(fecha_ui, "%d/%m/%Y")
            dt_venc = datetime.strptime(venc_ui, "%d/%m/%Y")
            
            fecha_backend = dt_fecha.strftime("%Y-%m-%d")
            venc_backend = dt_venc.strftime("%Y-%m-%d")
            datetime.strptime(hora, "%H:%M")
        except ValueError:
            return messagebox.showerror("Formato Inválido", "Las fechas deben ser DD/MM/AAAA (Ejemplo: 31/12/2026)")

        try:
            qty, cu = float(qty_str), float(cu_str)
            if qty <= 0:
                return messagebox.showerror("Error", "La cantidad debe ser mayor a cero.")
                
            unidad_medida = self.manager.metadata.get('Unidad', '')
            if unidad_medida == "Unidades (Und)":
                if not float(qty).is_integer():
                    return messagebox.showerror("Lógica Inválida", "No puedes registrar decimales en 'Unidades'.")

            marca = self.marca_var.get().strip()
            base_concept = tipo_ingreso
            final_concept = f"{base_concept} (Marca: {marca})" if marca else base_concept

            ok, msg = self.manager.register_entry(
                fecha=f"{fecha_backend} {hora}", 
                qty=qty, 
                unit_cost=cu, 
                prov=prov, 
                venc=venc_backend, 
                user=self.current_user, 
                lote_id=lote_final,
                concept=final_concept,
                lot_status="En Cuarentena" if tipo_ingreso == "Donación" else "Disponible"
            )
            
            if not ok:
                return messagebox.showerror("Error", msg)
                
            messagebox.showinfo("Éxito", f"Entrada del Paquete '{lote_final}' registrada correctamente.")
            self.win.destroy()
            if self.on_success: self.on_success()
            
        except ValueError:
            messagebox.showerror("Error", "Error numérico. Verifica que cantidad y costo sean válidos.")