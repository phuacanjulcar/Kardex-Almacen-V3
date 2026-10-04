import customtkinter as ctk
from tkinter import ttk, messagebox
import os
from ui.windows.entry_window import EntryWindow
from ui.windows.exit_window import ExitWindow
from ui.components.theme import Theme

class MainScreen(ctk.CTkFrame):
    def __init__(self, master, manager, current_user, on_logout, on_back):
        super().__init__(master)
        self.manager = manager
        self.current_user = current_user
        self.on_logout = on_logout
        self.on_back = on_back 
        
        self.pack(fill="both", expand=True)
        self.modo = ctk.get_appearance_mode()
        self.font_size = 9 # Tamaño de letra base para la tabla
        self._setup_ui()
        self.refresh_data()

        # ==========================================
        # NUEVO: ATAJOS DE TECLADO
        # ==========================================
        # Solo activamos Entradas/Salidas si no es invitado
        if self.current_user != "Invitado":
            self.master.bind('<Control-e>', lambda event: self._open_entry())
            self.master.bind('<Control-s>', lambda event: self._open_exit())
        
        # Eliminado el atajo global de Escape para evitar conflictos con modales
    # ==========================================
    # FASE 1: IDENTIDAD VISUAL CORPORATIVA (ERP)
    # Migrado a Theme centralizado en ui/theme.py

    def _setup_ui(self):
        self.configure(fg_color=Theme.BG_GENERAL)
        panel_bg = Theme.BG_CARD
        text_color = Theme.TEXT_MAIN

        # --- CONTENEDOR PRINCIPAL (Márgenes de 24px) ---
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=24, pady=24)

        # ==========================================
        # 1. MENÚ LATERAL COLAPSABLE (SIDEBAR)
        # ==========================================
        self.sidebar = ctk.CTkFrame(main_container, fg_color=panel_bg, width=220, corner_radius=12)
        self.sidebar.pack(side="left", fill="y", padx=(0, 24))
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="Almacén Inmaculada", font=("Segoe UI", 16, "bold"), text_color=Theme.PRIMARY).pack(pady=(24, 8))
        ctk.CTkLabel(self.sidebar, text=f"👤 {self.current_user}", font=("Segoe UI", 12), text_color=Theme.TEXT_MUTED).pack(pady=(0, 24))

        # --- BOTONES DEL MENÚ (Con jerarquía de color) ---
        btn_font = ("Segoe UI", 13, "bold")
        btn_pad = {"padx": 16, "pady": 6}

        if self.current_user != "Invitado":
            # Botones de Acción (Sin Emojis y sin Recepción Masiva)
            ctk.CTkButton(self.sidebar, text="Registrar Entrada", font=btn_font, fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, anchor="w", command=self._open_entry).pack(fill="x", **btn_pad)
            ctk.CTkButton(self.sidebar, text="Registrar Salida", font=btn_font, fg_color=Theme.WARNING, hover_color=Theme.WARNING_HOVER, anchor="w", command=self._open_exit).pack(fill="x", **btn_pad)
            
            ctk.CTkButton(self.sidebar, text="(?) Glosario de Ayuda", font=btn_font, fg_color="#3B82F6", hover_color="#2563EB", text_color="white", anchor="w", command=self._abrir_glosario).pack(fill="x", **btn_pad)
            
            ctk.CTkButton(self.sidebar, text="Bandeja de Mensajes", font=btn_font, fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER, text_color="white", anchor="w", command=self._open_message_inbox).pack(fill="x", **btn_pad)

            ctk.CTkFrame(self.sidebar, height=1, fg_color=Theme.BORDER).pack(fill="x", padx=16, pady=16) # Separador visual
            
            # Exportaciones (Transparentes y sin emojis)
            exp_btn_style = {"fg_color": "transparent", "text_color": Theme.TEXT_MUTED, "hover_color": Theme.TRANSPARENT_HOVER}
            ctk.CTkButton(self.sidebar, text="Exportar PDF", font=("Segoe UI", 12), command=self._export_pdf, anchor="w", **exp_btn_style).pack(fill="x", **btn_pad)
            ctk.CTkButton(self.sidebar, text="Exportar Excel", font=("Segoe UI", 12), command=self._export_excel, anchor="w", **exp_btn_style).pack(fill="x", **btn_pad)
            
            ctk.CTkFrame(self.sidebar, height=1, fg_color="#E2E8F0").pack(fill="x", padx=16, pady=16) # Separador visual
            
            if self.current_user == "Administrador":
                ctk.CTkButton(self.sidebar, text="Archivos Generales", font=btn_font, fg_color="#1E293B", text_color="white", hover_color="#334155", anchor="w", command=self._open_archivos).pack(fill="x", **btn_pad)
        
        # Zona Inferior del Sidebar
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=16, pady=24)
        
        # --- Switch Inteligente de Modo Oscuro ---
        self.switch_var = ctk.IntVar(value=1 if self.modo == "Dark" else 0)
        self.switch_theme = ctk.CTkSwitch(
            bottom_frame, 
            text="🌙 Modo Oscuro", 
            font=("Segoe UI", 12, "bold"),
            variable=self.switch_var,
            text_color=Theme.TEXT_MUTED,
            progress_color=Theme.PRIMARY,
            command=self._toggle_theme
        )
        self.switch_theme.pack(pady=(0, 20), anchor="w", padx=4)

        ctk.CTkButton(bottom_frame, text="📂 Cambiar Kardex", font=btn_font, fg_color="transparent", text_color=text_color, border_width=1, border_color="#E2E8F0", height=35, command=self.on_back).pack(fill="x", pady=(0, 8))
        ctk.CTkButton(bottom_frame, text="🚪 Salir", font=btn_font, fg_color=Theme.DANGER, hover_color=Theme.DANGER_HOVER, text_color="white", height=35, command=self.on_logout).pack(fill="x")

        # ==========================================
        # 2. ÁREA CENTRAL DE CONTENIDO
        # ==========================================
        content_area = ctk.CTkFrame(main_container, fg_color="transparent")
        content_area.pack(side="left", fill="both", expand=True)

        # Título estilo Migas de Pan (Breadcrumbs)
        self.lbl_title = ctk.CTkLabel(content_area, text="Cargando...", font=("Segoe UI", 20, "bold"), text_color=text_color)
        self.lbl_title.pack(anchor="w", pady=(0, 24))

        # --- TARJETAS KPI (Layout de 4 columnas) ---
        kpi_frame = ctk.CTkFrame(content_area, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, 24))

        def crear_tarjeta(parent, titulo, var_nombre, color_valor):
            card = ctk.CTkFrame(parent, fg_color=panel_bg, corner_radius=12, border_width=1, border_color=Theme.BORDER)
            card.pack(side="left", fill="both", expand=True, padx=(0, 16) if titulo != "Valor Total" else 0)
            ctk.CTkLabel(card, text=titulo, font=("Segoe UI", 12), text_color=Theme.TEXT_MUTED).pack(pady=(16, 0), padx=16, anchor="w")
            lbl_valor = ctk.CTkLabel(card, text="...", font=("Segoe UI", 22, "bold"), text_color=color_valor)
            lbl_valor.pack(pady=(0, 16), padx=16, anchor="w")
            setattr(self, var_nombre, lbl_valor) # Guardamos la referencia para actualizarla luego

        crear_tarjeta(kpi_frame, "Stock Actual", "kpi_stock", Theme.PRIMARY)
        crear_tarjeta(kpi_frame, "Estado del Producto", "kpi_estado", Theme.SUCCESS)
        crear_tarjeta(kpi_frame, "Último Movimiento", "kpi_fecha", Theme.TEXT_MAIN)
        crear_tarjeta(kpi_frame, "Valor Total", "kpi_valor", Theme.WARNING)

        # --- CONTROLES DE ZOOM Y TITULO DE TABLA ---
        header_table_frame = ctk.CTkFrame(content_area, fg_color="transparent")
        header_table_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header_table_frame, text="Historial de Movimientos", font=("Segoe UI", 16, "bold"), text_color=text_color).pack(side="left")
        
        def zoom_in():
            if self.font_size < 16:
                self.font_size += 1
                self._apply_tree_style()
                
        def zoom_out():
            if self.font_size > 7:
                self.font_size -= 1
                self._apply_tree_style()
                
        ctk.CTkButton(header_table_frame, text="+ Tamaño ➕", font=("Segoe UI", 11, "bold"), fg_color=Theme.BORDER, text_color=text_color, hover_color=Theme.TRANSPARENT_HOVER, width=90, height=30, command=zoom_in).pack(side="right", padx=(10, 0))
        ctk.CTkButton(header_table_frame, text="- Tamaño ➖", font=("Segoe UI", 11, "bold"), fg_color=Theme.BORDER, text_color=text_color, hover_color=Theme.TRANSPARENT_HOVER, width=90, height=30, command=zoom_out).pack(side="right")

        # --- TABLA DE KARDEX ---
        table_container = ctk.CTkFrame(content_area, fg_color=panel_bg, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        table_container.pack(fill="both", expand=True)

        cols = ("Fecha y Hora", "Operación", "Detalle", "Lote / Paquete", "Marca", "Vencimiento", "Destino", "Cantidad", "Costo Unitario", "Documento", "Horas extra", "Stock Actual", "Valor Total", "Estado")
        ancho_cols = {"Fecha y Hora": 120, "Operación": 80, "Detalle": 150, "Lote / Paquete": 100, "Marca": 120, "Vencimiento": 90, "Destino": 150, "Cantidad": 90, "Costo Unitario": 90, "Documento": 120, "Horas extra": 50, "Stock Actual": 90, "Valor Total": 90, "Estado": 100}
       
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=15)
        for col, ancho in ancho_cols.items():
            self.tree.heading(col, text=col)
            
            if col in ["Cantidad", "Costo Unitario", "Stock Actual", "Valor Total", "Horas extra"]:
                align = "e"
            elif col in ["Detalle", "Destino", "Marca", "Documento", "Lote / Paquete"]:
                align = "w"
            else:
                align = "center"
                
            self.tree.column(col, width=ancho, minwidth=ancho, anchor=align, stretch=True)
            
        if self.current_user != "Administrador":
            self.tree["displaycolumns"] = ("Fecha y Hora", "Operación", "Detalle", "Lote / Paquete", "Marca", "Vencimiento", "Destino", "Cantidad", "Costo Unitario", "Documento", "Stock Actual", "Valor Total", "Estado")

        scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        # Márgenes internos para la tabla
        scroll.pack(side="right", fill="y", pady=12, padx=(0, 12))
        self.tree.pack(fill="both", expand=True, padx=12, pady=12)

        self._apply_tree_style()

    def _apply_tree_style(self):
        modo_idx = 0 if self.modo == "Light" else 1
        panel_bg = Theme.BG_CARD[modo_idx]
        text_color = Theme.TEXT_MAIN[modo_idx]
        header_bg = "#F8FAFC" if self.modo == "Light" else "#1E293B"
        header_fg = "#1E293B" if self.modo == "Light" else "#F8FAFC"
        hover_bg = Theme.BORDER[modo_idx]
        
        style = ttk.Style()
        style.theme_use("default")
        
        # Eliminamos bordes para un look más limpio (flat design)
        style.configure("Treeview.Heading", font=("Segoe UI", max(9, self.font_size), "bold"), background=header_bg, foreground=header_fg, borderwidth=0)
        style.map("Treeview.Heading", background=[('active', hover_bg)], foreground=[('active', header_fg)])
        
        style.configure("Treeview", font=("Segoe UI", self.font_size), rowheight=max(25, self.font_size * 3), borderwidth=0, background=panel_bg, foreground=text_color, fieldbackground=panel_bg)
        style.map("Treeview", background=[('selected', Theme.TRANSPARENT_HOVER[modo_idx])], foreground=[('selected', Theme.PRIMARY[modo_idx])])
        
        if self.modo == "Dark":
            self.tree.tag_configure('par', background=Theme.BG_CARD[1], foreground=Theme.TEXT_MAIN[1])
            self.tree.tag_configure('impar', background=Theme.BG_GENERAL[1], foreground=Theme.TEXT_MAIN[1])
        else:
            self.tree.tag_configure('par', background=Theme.BG_CARD[0], foreground=Theme.TEXT_MAIN[0])
            self.tree.tag_configure('impar', background=Theme.BG_GENERAL[0], foreground=Theme.TEXT_MAIN[0])  



    def _set_theme(self, mode):
        self.modo = mode
        ctk.set_appearance_mode(mode)
        self._apply_tree_style()

    def _toggle_theme(self):
        nuevo_modo = "Dark" if self.switch_var.get() == 1 else "Light"
        self._set_theme(nuevo_modo)

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        meta = getattr(self.manager, 'metadata', {})
        producto = meta.get('Producto', 'Desconocido')
        unidad = meta.get('Unidad', 'Und')
        ubicacion = meta.get('Ubicacion', 'Sin Asignar')
        categoria = meta.get('Categoria', 'Sin Categoría')
        stock_minimo = float(meta.get('Stock_Minimo', 10))
        
        # Formato de Migas de Pan (Breadcrumbs)
        title_text = f"Inventario > {categoria} > {producto}"
        self.lbl_title.configure(text=title_text)

        lista_kardex = getattr(self.manager, 'print_rows', [])
        if not lista_kardex:
            lista_kardex = getattr(self.manager, 'kardex_data', [])
        
        # --- NUEVO: OBTENER DATOS PARA LOS KPI ---
        stock_actual = 0
        valor_total = 0
        ultima_fecha = "-"
        estado_global = "Sin Datos"
        color_estado = Theme.TEXT_MUTED

        if lista_kardex:
            # Tomamos el último registro para el resumen global
            ultimo_reg = lista_kardex[-1]
            stock_actual = float(ultimo_reg.get('CantidadSaldo', 0) or 0)
            valor_total = ultimo_reg.get('TotalSaldo', 0)
            ultima_fecha = ultimo_reg.get('Fecha', '-').split(' ')[0] # Solo la fecha, sin hora
            
            if stock_actual > stock_minimo:
                estado_global = "Óptimo"
                color_estado = Theme.SUCCESS
            elif 0 < stock_actual <= stock_minimo:
                estado_global = "Crítico"
                color_estado = Theme.WARNING
            elif stock_actual == 0:
                estado_global = "Agotado"
                color_estado = Theme.DANGER

        # --- ACTUALIZAR TARJETAS KPI EN PANTALLA ---
        self.kpi_stock.configure(text=f"{stock_actual:,.2f} {unidad}")
        self.kpi_valor.configure(text=f"S/ {float(valor_total):,.2f}" if valor_total else "S/ 0.00")
        self.kpi_fecha.configure(text=ultima_fecha)
        self.kpi_estado.configure(text=estado_global, text_color=color_estado)

        # --- LLENAR LA TABLA ---
        for index, row in enumerate(lista_kardex):
            qty = float(row.get('Cantidad', 0) or row.get('CantidadSalida', 0) or 0)
            uc = row.get('Precio_Unitario')
            stock = float(row.get('CantidadSaldo', 0) or 0)
            total = row.get('TotalSaldo')
            
            if stock > stock_minimo:
                estado_txt = "✅ Con Stock"
            elif 0 < stock <= stock_minimo:
                estado_txt = "⚠️ Poco Stock"
            elif stock == 0:
                estado_txt = "❌ Agotado"
            else:
                estado_txt = "❗ Negativo (Error)"

            qty_str = f"{qty:,.2f}" if qty else "-"
            cost_str = f"S/ {float(uc):,.2f}" if uc is not None and uc != "" else "-"
            stock_str = f"{stock:,.2f}"
            val_str = f"S/ {float(total):,.2f}" if total is not None and total != "" else "-"
            etiqueta = 'par' if index % 2 == 0 else 'impar'
            
            ext_h_str = "Sí 🟠" if row.get("out_of_hours", 0) == 1 else "-"
            t = row.get("type", "")
            concepto_raw = row.get('Concepto') or '-'
            doc_str = row.get('Documento')
            doc_str = doc_str if doc_str is not None else "-"
            
            tipo_mov = "Entrada" if t in ["E", "SI"] else "Salida"
            
            if tipo_mov == "Entrada":
                qty_str = f"▲ {qty:,.2f}" if qty else "-"
            else:
                qty_str = f"▼ {qty:,.2f}" if qty else "-"
            
            self.tree.insert("", "end", values=(
                row.get('Fecha') or '-',
                tipo_mov,
                concepto_raw,
                row.get('Lote') or '-',
                row.get('Marca') or '-', 
                row.get('Fecha_Vencimiento') or '-',
                row.get('Destino') or '-',
                qty_str,
                cost_str,
                doc_str,
                ext_h_str,
                stock_str,
                val_str,
                estado_txt
            ), tags=(etiqueta,))

    def _open_entry(self):
        if self.current_user == "Invitado":
            return messagebox.showerror("Acceso Denegado", "Los invitados solo pueden visualizar información.")
        EntryWindow(self, self.manager, self.current_user, self.refresh_data)

    def _open_exit(self):
        if self.current_user == "Invitado":
            return messagebox.showerror("Acceso Denegado", "Los invitados solo pueden visualizar información.")
        from ui.windows.exit_window import ExitWindow
        ExitWindow(self, self.manager, self.current_user, self.refresh_data)

    def _open_message_inbox(self):
        from ui.windows.message_inbox_window import MessageInboxWindow
        doc_ref = ""
        sel = self.tree.selection()
        if sel:
            idx = self.tree.index(sel[0])
            lista_kardex = getattr(self.manager, 'print_rows', [])
            if not lista_kardex:
                lista_kardex = getattr(self.manager, 'kardex_data', [])
            if idx < len(lista_kardex):
                doc_ref = lista_kardex[idx].get('Guia', '')
                if doc_ref is None or doc_ref == "-": 
                    doc_ref = ""
                else:
                    doc_ref = str(doc_ref)
        MessageInboxWindow(self, self.current_user, doc_ref)

    def _open_archivos(self):
        # Abrir la vista de Archivos Generales en una ventana Toplevel
        win = ctk.CTkToplevel(self)
        win.title("Archivos Generales")
        win.geometry("900x600")
        win.transient(self.master)
        
        from ui.admin_views.files_view import FilesView
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # FilesView asume que su parent es un frame usualmente, pero aquí se le puede pasar `win`
        fv = FilesView(win, self, base_dir)
        fv.pack(fill="both", expand=True, padx=20, pady=20)
        
    def _open_recepcion_masiva(self): # Si tienes esta función en main_screen.py
        if self.current_user == "Invitado":
            return messagebox.showerror("Acceso Denegado", "Los invitados solo pueden visualizar información.")
        # ... código para abrir Recepción Masiva ...    

        
    def _delete_row(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecciona una fila para eliminar.")
        idx = self.tree.index(sel[0])
        if messagebox.askyesno("Confirmar", "¿Eliminar este registro?"):
            self.manager.delete_event_at_index(idx)
            self.refresh_data()

    def _export_excel(self):
        try:
            self.manager.export_to_excel()
            messagebox.showinfo("Exportar", "Reporte Excel generado.")
        except AttributeError:
            messagebox.showwarning("Aviso", "Función no implementada en kardex_manager.py")

    def _export_pdf(self):
        try:
            self.manager.export_to_pdf()
            messagebox.showinfo("Exportar", "Reporte PDF generado.")
        except AttributeError:
            messagebox.showwarning("Aviso", "Función no implementada en kardex_manager.py")

    def _edit_properties(self):
        win = ctk.CTkToplevel(self)
        win.title("Editar Propiedades")
        win.geometry("450x540") 
        win.grab_set()

        form = ctk.CTkFrame(win, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(form, text="Nombre del Producto:", font=("Segoe UI", 13)).pack(anchor="w")
        nombre_var = ctk.StringVar(value=self.manager.metadata.get('Producto', ''))
        ctk.CTkEntry(form, textvariable=nombre_var, height=35).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Prefijo del Paquete (Ej: PPH para Papa Huayro):", font=("Segoe UI", 13)).pack(anchor="w")
        prefijo_var = ctk.StringVar(value=self.manager.metadata.get('Prefijo', 'PAQ'))
        ctk.CTkEntry(form, textvariable=prefijo_var, height=35).pack(fill="x", pady=(0, 10))

        row_frame = ctk.CTkFrame(form, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 10))
        
        col1 = ctk.CTkFrame(row_frame, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(col1, text="Unidad de Medida:", font=("Segoe UI", 13)).pack(anchor="w")
        unidades = ["Kilogramos (Kg)", "Gramos (g)", "Litros (L)", "Unidades (Und)"]
        uni_combo = ctk.CTkOptionMenu(col1, values=unidades, height=35)
        uni_combo.set(self.manager.metadata.get('Unidad', 'Unidades (Und)'))
        uni_combo.pack(fill="x")

        col2 = ctk.CTkFrame(row_frame, fg_color="transparent")
        col2.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(col2, text="Stock Mínimo (Alerta):", font=("Segoe UI", 13)).pack(anchor="w")
        stock_min_var = ctk.StringVar(value=str(self.manager.metadata.get('Stock_Minimo', 10)))
        ctk.CTkEntry(col2, textvariable=stock_min_var, height=35).pack(fill="x")

        ctk.CTkLabel(form, text="Ubicación / Zona:", font=("Segoe UI", 13)).pack(anchor="w")
        zonas_disp = []
        if os.path.exists("data/zonas_config.json"):
            import json
            with open("data/zonas_config.json", "r", encoding="utf-8") as f:
                zonas_disp = list(json.load(f).keys())
        if "Sin Asignar" not in zonas_disp:
            zonas_disp.insert(0, "Sin Asignar")
            
        zona_actual = self.manager.metadata.get('Ubicacion', 'Sin Asignar')
        if zona_actual not in zonas_disp: zonas_disp.append(zona_actual)
        
        zona_combo = ctk.CTkOptionMenu(form, values=zonas_disp, height=35)
        zona_combo.set(zona_actual)
        zona_combo.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Categoría:", font=("Segoe UI", 13)).pack(anchor="w")
        categorias_disp = []
        if os.path.exists("data/categorias_config.json"):
            import json
            with open("data/categorias_config.json", "r", encoding="utf-8") as f:
                categorias_disp = list(json.load(f).keys())
        if "Sin Categoría" not in categorias_disp:
            categorias_disp.insert(0, "Sin Categoría")
        
        cat_actual = self.manager.metadata.get('Categoria', 'Sin Categoría')
        if cat_actual not in categorias_disp: categorias_disp.append(cat_actual)
        
        cat_combo = ctk.CTkOptionMenu(form, values=categorias_disp, height=35)
        cat_combo.set(cat_actual)
        cat_combo.pack(fill="x", pady=(0, 25))

        def guardar():
            self.manager.metadata['Producto'] = nombre_var.get().strip()
            
            pref = prefijo_var.get().strip().upper()
            if not pref: pref = "PAQ"
            else: pref = pref[:3]
            self.manager.metadata['Prefijo'] = pref
            
            self.manager.metadata['Unidad'] = uni_combo.get()
            self.manager.metadata['Ubicacion'] = zona_combo.get()
            self.manager.metadata['Categoria'] = cat_combo.get()
            
            try: self.manager.metadata['Stock_Minimo'] = float(stock_min_var.get().strip())
            except ValueError: pass
            
            self.manager.save()
            self.refresh_data()
            win.destroy()
            messagebox.showinfo("Éxito", "Propiedades actualizadas")

        ctk.CTkButton(form, text="Guardar Cambios", command=guardar, height=40, font=("Segoe UI", 14, "bold")).pack(fill="x")

    def _abrir_glosario(self):
        win = ctk.CTkToplevel(self)
        win.title("Glosario de Ayuda")
        win.geometry("500x600")
        win.grab_set()

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="📖 Glosario del Sistema", font=("Segoe UI", 20, "bold")).pack(pady=(0, 20))

        terminos = {
            "FIFO (Primero en Entrar, Primero en Salir)": "Si dos lotes no tienen fecha de vencimiento o vencen el mismo día, el sistema consumirá automáticamente el lote que llegó primero al almacén.",
            "FEFO (Primero en Vencer, Primero en Salir)": "Al registrar una salida automática, el sistema siempre buscará y consumirá primero el lote que esté más próximo a vencerse.",
            "Lote / Paquete": "El código identificador único que se le pone a la mercadería cuando ingresa, para saber exactamente cuándo vence y cuánto costó.",
            "Merma (Ajuste por Pérdida)": "Salida de productos por vencimiento, rotura o robo. Esta operación descuenta stock pero requiere obligatoriamente tu contraseña de Administrador.",
            "Saldo (Stock Actual)": "Es la cantidad física que debe haber en el almacén en este momento preciso (Entradas menos Salidas).",
            "Anulación Segura (Historial Intacto)": "Cuando anulas un movimiento o desactivas un producto, el sistema lo oculta de las listas pero NUNCA borra su historial. Así siempre podrás auditar lo que pasó."
        }

        for termino, definicion in terminos.items():
            ctk.CTkLabel(scroll, text=termino, font=("Segoe UI", 14, "bold"), text_color="#3B82F6").pack(anchor="w", pady=(10, 2))
            lbl_def = ctk.CTkLabel(scroll, text=definicion, font=("Segoe UI", 12), justify="left", wraplength=420)
            lbl_def.pack(anchor="w", pady=(0, 10))

        ctk.CTkButton(win, text="Cerrar", command=win.destroy).pack(pady=20)
