import customtkinter as ctk
from tkinter import ttk, messagebox
import os
import json
from datetime import datetime
from core.kardex_manager import KardexManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class RecepcionMasivaWindow(ctk.CTkToplevel):
    def __init__(self, master, current_user):
        super().__init__(master)
        self.title("📦 Recepción Masiva (Guías y Donaciones)")
        self.geometry("950x700")
        self.current_user = current_user
        self.lista_temporal = [] 
        self.grab_set()
        
        self.modo = ctk.get_appearance_mode()
        self.configure(fg_color=("#F5F7FA", "#121212"))
        self.text_color = ("#263238", "white")
        
        self._setup_ui()

    def _get_productos(self):
        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM products WHERE is_active = 1 ORDER BY name ASC")
            names = [row['name'] for row in cursor.fetchall()]
            conn.close()
            return names if names else ["-- No hay productos --"]
        except:
            return ["-- No hay productos --"]

    def _on_motivo_change(self, value):
        if hasattr(self, 'entry_costo'):
            if value == "Donación":
                self.entry_costo.delete(0, 'end')
                self.entry_costo.insert(0, "0")
                self.entry_costo.configure(state="disabled")
            else:
                self.entry_costo.configure(state="normal")

    def _setup_ui(self):
        # ==========================================
        # 1. CABECERA DEL DOCUMENTO (GLOBAL)
        # ==========================================
        header_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#1E1E2F"), corner_radius=10, border_width=1, border_color="#E2E8F0")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="1. Datos Generales del Documento", font=("Segoe UI", 15, "bold"), text_color="#1565C0").pack(anchor="w", padx=20, pady=(15, 5))
        
        row_header_1 = ctk.CTkFrame(header_frame, fg_color="transparent")
        row_header_1.pack(fill="x", padx=20, pady=(0, 10))
        
        from ui.tooltip import crear_label_con_ayuda
        
        crear_label_con_ayuda(row_header_1, "N° Guía/Doc:", "El código oficial del papel que acompaña la mercadería (ej. Factura F001-23).", font=("Segoe UI", 12)).pack(side="left")
        self.entry_doc = ctk.CTkEntry(row_header_1, width=130, placeholder_text="Ej: TS01-00000022")
        self.entry_doc.pack(side="left", padx=(5, 15))
        
        crear_label_con_ayuda(row_header_1, "Donante/RUC:", "Persona o empresa que entregó o vendió el producto.", font=("Segoe UI", 12)).pack(side="left")
        self.entry_prov = ctk.CTkEntry(row_header_1, width=180, placeholder_text="Ej: 20200200200 o Juan")
        self.entry_prov.pack(side="left", padx=(5, 15))
        
        crear_label_con_ayuda(row_header_1, "Motivo (Sunat):", "La razón legal por la que entra el producto al almacén.", font=("Segoe UI", 12)).pack(side="left")
        self.combo_motivo = ctk.CTkOptionMenu(row_header_1, values=["Compra", "Donación", "Traslado", "Otros"], width=110, command=self._on_motivo_change)
        self.combo_motivo.pack(side="left", padx=5)

        row_header_2 = ctk.CTkFrame(header_frame, fg_color="transparent")
        row_header_2.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(row_header_2, text="Observaciones:", font=("Segoe UI", 12, "bold"), text_color="#F57C00").pack(side="left")
        self.entry_detalle = ctk.CTkEntry(row_header_2, placeholder_text="Escriba aquí los detalles largos de la colecta, donación u observaciones...")
        self.entry_detalle.pack(side="left", fill="x", expand=True, padx=(5, 0))

        row_header_3a = ctk.CTkFrame(header_frame, fg_color="transparent")
        row_header_3a.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(row_header_3a, text="Transporte:", font=("Segoe UI", 12)).pack(side="left")
        self.entry_transporte = ctk.CTkEntry(row_header_3a, width=200, placeholder_text="Conductor")
        self.entry_transporte.pack(side="left", padx=(5, 10))
        
        self.entry_vehiculo = ctk.CTkEntry(row_header_3a, width=150, placeholder_text="Vehículo/Placa")
        self.entry_vehiculo.pack(side="left", padx=(0, 10))
        
        self.entry_licencia = ctk.CTkEntry(row_header_3a, width=150, placeholder_text="Licencia")
        self.entry_licencia.pack(side="left", padx=(0, 5))
        
        row_header_3b = ctk.CTkFrame(header_frame, fg_color="transparent")
        row_header_3b.pack(fill="x", padx=20, pady=(0, 15))

        crear_label_con_ayuda(row_header_3b, "Punto de Partida:", "Lugar físico desde donde salió la mercadería antes de llegar al almacén.", font=("Segoe UI", 12)).pack(side="left", padx=(0, 20))
        self.entry_partida = ctk.CTkEntry(row_header_3b, placeholder_text="Punto de Partida (Obligatorio)")
        self.entry_partida.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        row_header_3c = ctk.CTkFrame(header_frame, fg_color="transparent")
        row_header_3c.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(row_header_3c, text="Punto de Llegada:", font=("Segoe UI", 12)).pack(side="left", padx=(0, 20))
        self.lbl_llegada = ctk.CTkLabel(row_header_3c, text="Av. Pedro Miotta Nº180, San Juan de Miraflores, Lima Perú", font=("Segoe UI", 12, "bold"), text_color="#1E293B", anchor="w")
        self.lbl_llegada.pack(side="left", fill="x", expand=True)

        # ==========================================
        # 2. AGREGAR PRODUCTOS AL DETALLE
        # ==========================================
        detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        detail_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(detail_frame, text="2. Agregar Productos a la Lista", font=("Segoe UI", 15, "bold"), text_color="#1565C0").pack(anchor="w", pady=(5, 10))
        
        row_prod = ctk.CTkFrame(detail_frame, fg_color="transparent")
        row_prod.pack(fill="x")
        
        ctk.CTkLabel(row_prod, text="Producto:").pack(side="left")
        self.combo_prod = ctk.CTkOptionMenu(row_prod, values=self._get_productos(), width=180)
        self.combo_prod.pack(side="left", padx=5)
        
        ctk.CTkLabel(row_prod, text="Cant:").pack(side="left", padx=(10, 0))
        self.entry_cant = ctk.CTkEntry(row_prod, width=70)
        self.entry_cant.pack(side="left", padx=5)
        
        crear_label_con_ayuda(row_prod, "Costo (S/):", "Lo que costó cada unidad. Si es donación, se coloca un precio referencial estimado.").pack(side="left", padx=(10, 0))
        self.entry_costo = ctk.CTkEntry(row_prod, width=80, placeholder_text="0.00")
        self.entry_costo.pack(side="left", padx=5)
        
        # CORRECCIÓN: Vencimiento obligatorio, sin placeholder de "Opcional"
        crear_label_con_ayuda(row_prod, "Vence (DD/MM/AAAA):", "Fecha máxima en la que el producto puede ser consumido con seguridad.").pack(side="left", padx=(10, 0))
        self.entry_venc = ctk.CTkEntry(row_prod, width=130, placeholder_text="Obligatorio")
        self.entry_venc.pack(side="left", padx=5)
        
        ctk.CTkButton(row_prod, text="➕ Agregar", font=("Segoe UI", 12, "bold"), fg_color="#2E7D32", hover_color="#1B5E20", width=100, command=self._agregar_lista).pack(side="right", padx=(10, 0))

        # ==========================================
        # 4. BOTÓN PROCESAR (Se hace pack primero en el bottom para asegurar visibilidad)
        # ==========================================
        ctk.CTkButton(self, text="📄 Finalizar y Previsualizar Documento", font=("Segoe UI", 14, "bold"), height=45, fg_color="#1565C0", hover_color="#0D47A1", command=self._mostrar_previsualizacion).pack(side="bottom", fill="x", padx=20, pady=(0, 20))

        # ==========================================
        # 3. TABLA TEMPORAL
        # ==========================================
        table_container = ctk.CTkFrame(self, fg_color="#FFFFFF" if self.modo == "Light" else "#1E1E2F", corner_radius=10, border_width=1, border_color="#E2E8F0")
        table_container.pack(fill="both", expand=True, padx=20, pady=15)
        
        cols = ("Producto", "Cantidad", "Costo Unit.", "Subtotal", "Vencimiento")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=8)
        
        self.tree.heading("Producto", text="Producto")
        self.tree.heading("Cantidad", text="Cantidad")
        self.tree.heading("Costo Unit.", text="Costo Unit.")
        self.tree.heading("Subtotal", text="Subtotal")
        self.tree.heading("Vencimiento", text="Vencimiento")

        self.tree.column("Producto", width=200, anchor="w")
        self.tree.column("Cantidad", width=80, anchor="center")
        self.tree.column("Costo Unit.", width=100, anchor="center")
        self.tree.column("Subtotal", width=100, anchor="center")
        self.tree.column("Vencimiento", width=120, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def _agregar_lista(self):
        doc = self.entry_doc.get().strip()
        prov = self.entry_prov.get().strip()
        
        if not doc or not prov:
            return messagebox.showerror("Faltan Datos", "Por favor, llene el N° de Documento y el Donante/RUC en la sección superior antes de agregar productos.")

        prod = self.combo_prod.get()
        cant = self.entry_cant.get().strip()
        venc = self.entry_venc.get().strip()
        costo_str = self.entry_costo.get().strip()
        
        # CORRECCIÓN: Validación estricta para que ningún campo esté vacío
        if not cant or not venc or not costo_str:
            return messagebox.showerror("Faltan Datos", "Debe llenar todos los campos obligatorios del producto (Cantidad, Costo y Vencimiento).")
        
        if not cant.replace('.','',1).isdigit(): return messagebox.showerror("Error", "Cantidad inválida.")
        try: costo_float = float(costo_str)
        except ValueError: return messagebox.showerror("Error", "Costo inválido.")
        try: datetime.strptime(venc, "%d/%m/%Y")
        except ValueError: return messagebox.showerror("Error", "Fecha inválida (Use DD/MM/AAAA).")

        motivo_base = self.combo_motivo.get()
        detalle_extra = self.entry_detalle.get().strip()
        
        # Datos del transporte
        t_cond = self.entry_transporte.get().strip()
        t_veh = self.entry_vehiculo.get().strip()
        t_lic = self.entry_licencia.get().strip()
        t_part = self.entry_partida.get().strip()
        t_lleg = "Av. Pedro Miotta Nº180, San Juan de Miraflores, Lima Perú"
        
        if not t_part:
            return messagebox.showerror("Faltan Datos", "El Punto de Partida del transporte es obligatorio.")
            
        transporte_str = f" | Transp: {t_cond}, {t_veh}, Lic:{t_lic}, De:{t_part} A:{t_lleg}"
        
        motivo_final = f"{motivo_base} - {detalle_extra}" if detalle_extra else motivo_base
        motivo_final += transporte_str

        item = {
            "documento": doc,
            "origen": prov,
            "motivo": motivo_final, 
            "producto": prod, 
            "cantidad": cant, 
            "costo": costo_float, 
            "vencimiento": venc,
            "conductor": t_cond,
            "vehiculo": t_veh,
            "licencia": t_lic,
            "partida": t_part
        }
        self.lista_temporal.append(item)
        
        subtotal = float(cant) * costo_float
        self.tree.insert("", "end", values=(prod, cant, f"S/ {costo_float:.2f}", f"S/ {subtotal:.2f}", venc))
        
        self.entry_cant.delete(0, 'end')
        self.entry_venc.delete(0, 'end')
        self.entry_costo.delete(0, 'end')
        self.entry_cant.focus()

    # =======================================================
    # PREVISUALIZACIÓN ESTILO "GUÍA DE REMISIÓN"
    # =======================================================
    def _mostrar_previsualizacion(self):
        if not self.lista_temporal:
            return messagebox.showwarning("Aviso", "No hay productos en la lista.")

        datos_globales = self.lista_temporal[0]
        total_items = len(self.lista_temporal)
        valor_total_doc = sum(float(item['cantidad']) * float(item['costo']) for item in self.lista_temporal)
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        
        prev_win = ctk.CTkToplevel(self)
        prev_win.title("📄 Previsualización de Guía de Remisión")
        prev_win.geometry("850x700")
        prev_win.transient(self)
        prev_win.grab_set()
        # El fondo general es oscuro/claro, pero el papel será blanco puro
        prev_win.configure(fg_color=("#F5F7FA", "#121212"))

        # --- EL "PAPEL A4" ---
        paper = ctk.CTkFrame(prev_win, fg_color="white", corner_radius=0, border_width=1, border_color="#D1D5DB")
        paper.pack(fill="both", expand=True, padx=40, pady=(20, 10))

        # --- MEMBRETE SUPERIOR (Idéntico a documentos formales) ---
        header_paper = ctk.CTkFrame(paper, fg_color="transparent")
        header_paper.pack(fill="x", padx=30, pady=30)
        
        # Izquierda (Datos Empresa)
        left_header = ctk.CTkFrame(header_paper, fg_color="transparent")
        left_header.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(left_header, text="ALMACÉN INMACULADA", font=("Segoe UI", 22, "bold"), text_color="black").pack(anchor="w")
        ctk.CTkLabel(left_header, text="Registro Interno de Recepción de Bienes", font=("Segoe UI", 12), text_color="#546E7A").pack(anchor="w")
        ctk.CTkLabel(left_header, text=f"Operador Responsable: {self.current_user}", font=("Segoe UI", 12), text_color="black").pack(anchor="w", pady=(10, 0))

        # Derecha (El clásico recuadro de RUC y N° Guía)
        right_header = ctk.CTkFrame(header_paper, fg_color="white", border_width=2, border_color="black", corner_radius=8)
        right_header.pack(side="right", ipadx=20, ipady=10)
        ctk.CTkLabel(right_header, text="SISTEMA DE RECEPCIÓN", font=("Segoe UI", 13, "bold"), text_color="black").pack(pady=(5, 0))
        ctk.CTkLabel(right_header, text="DOCUMENTO DE REFERENCIA", font=("Segoe UI", 11), text_color="black").pack()
        ctk.CTkLabel(right_header, text=f"N° {datos_globales['documento']}", font=("Segoe UI", 18, "bold"), text_color="#D32F2F").pack(pady=(5, 0))

        # --- DATOS DEL TRASLADO / REMITENTE ---
        info_frame = ctk.CTkFrame(paper, fg_color="transparent")
        info_frame.pack(fill="x", padx=30, pady=10)
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)
        
        left_info = ctk.CTkFrame(info_frame, fg_color="transparent")
        left_info.grid(row=0, column=0, sticky="nw", padx=(0, 10))
        
        motivo_limpio = datos_globales['motivo'].split(' | Transp:')[0]
        ctk.CTkLabel(left_info, text=f"Fecha de Recepción: {fecha_actual}", font=("Segoe UI", 12, "bold"), text_color="black").pack(anchor="w", pady=2)
        ctk.CTkLabel(left_info, text=f"Donante / Origen: {datos_globales['origen']}", font=("Segoe UI", 12, "bold"), text_color="black").pack(anchor="w", pady=2)
        ctk.CTkLabel(left_info, text=f"Motivo / Observaciones: {motivo_limpio}", font=("Segoe UI", 12, "bold"), text_color="black").pack(anchor="w", pady=2)
        
        partida = datos_globales.get('partida', '-') or '-'
        ctk.CTkLabel(left_info, text="De (Punto de Partida):", font=("Segoe UI", 12, "bold"), text_color="black").pack(anchor="w", pady=(5, 0))
        ctk.CTkLabel(left_info, text=partida, font=("Segoe UI", 12), text_color="black", wraplength=350, justify="left").pack(anchor="w")
        
        ctk.CTkLabel(left_info, text="A (Punto de Llegada):", font=("Segoe UI", 12, "bold"), text_color="black").pack(anchor="w", pady=(5, 0))
        ctk.CTkLabel(left_info, text="Av. Pedro Miotta Nº180, San Juan de Miraflores, Lima Perú", font=("Segoe UI", 12), text_color="black", wraplength=350, justify="left").pack(anchor="w")
        
        right_info = ctk.CTkFrame(info_frame, fg_color="transparent")
        right_info.grid(row=0, column=1, sticky="nw", padx=(10, 0))
        
        ctk.CTkLabel(right_info, text="Transporte:", font=("Segoe UI", 13, "bold"), text_color="black").pack(anchor="w", pady=(0, 5))
        cond = datos_globales.get('conductor', '') or '-'
        veh = datos_globales.get('vehiculo', '') or '-'
        lic = datos_globales.get('licencia', '') or '-'
        ctk.CTkLabel(right_info, text=f"Conductor: {cond}", font=("Segoe UI", 12), text_color="black").pack(anchor="w", pady=2)
        ctk.CTkLabel(right_info, text=f"Vehículo/Placa: {veh}", font=("Segoe UI", 12), text_color="black").pack(anchor="w", pady=2)
        ctk.CTkLabel(right_info, text=f"Licencia: {lic}", font=("Segoe UI", 12), text_color="black").pack(anchor="w", pady=2)

        # --- DATOS DEL BIEN TRANSPORTADO (Tabla de estilo documento) ---
        ctk.CTkLabel(paper, text="Datos del bien recepcionado", font=("Segoe UI", 12, "bold"), text_color="black", anchor="w").pack(fill="x", padx=30, pady=(15, 5))
        
        table_frame = ctk.CTkFrame(paper, fg_color="white", border_width=1, border_color="black", corner_radius=0)
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        
        style = ttk.Style()
        style.configure("Paper.Treeview", background="white", foreground="black", fieldbackground="white", rowheight=25, borderwidth=0)
        style.configure("Paper.Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#F3F4F6", foreground="black")
        
        cols = ("DESCRIPCIÓN", "CANTIDAD", "VENCE", "P. UNIT", "TOTAL")
        tree_prev = ttk.Treeview(table_frame, columns=cols, show="headings", style="Paper.Treeview", height=8)
        for col in cols: tree_prev.heading(col, text=col)
        tree_prev.column("DESCRIPCIÓN", width=250, anchor="w"); tree_prev.column("CANTIDAD", width=80, anchor="center")
        tree_prev.column("VENCE", width=90, anchor="center"); tree_prev.column("P. UNIT", width=90, anchor="center")
        tree_prev.column("TOTAL", width=90, anchor="center")
        
        for item in self.lista_temporal:
            sub = float(item['cantidad']) * float(item['costo'])
            tree_prev.insert("", "end", values=(item['producto'], item['cantidad'], item['vencimiento'], f"S/{item['costo']:.2f}", f"S/{sub:.2f}"))
            
        tree_prev.pack(fill="both", expand=True, padx=1, pady=1)

        ctk.CTkLabel(paper, text=f"Total Ítems: {total_items}   |   Valorización Total: S/ {valor_total_doc:,.2f}", font=("Segoe UI", 13, "bold"), text_color="black").pack(anchor="e", padx=30, pady=10)

        # --- BOTONES EXTERNOS AL PAPEL ---
        btn_frame = ctk.CTkFrame(prev_win, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        ctk.CTkButton(btn_frame, text="⬅️ Modificar Documento", font=("Segoe UI", 13, "bold"), fg_color="transparent", border_width=1, border_color="#D32F2F", text_color="#D32F2F", command=prev_win.destroy).pack(side="left", expand=True, padx=10, fill="x")
        ctk.CTkButton(btn_frame, text="✅ Validar e Ingresar al Kardex", font=("Segoe UI", 13, "bold"), fg_color="#2E7D32", hover_color="#1B5E20", command=lambda: self._ejecutar_guardado(prev_win)).pack(side="right", expand=True, padx=10, fill="x")

    def _ejecutar_guardado(self, prev_win):
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        datos_globales = self.lista_temporal[0]
        id_operacion = f"{datos_globales['documento']}" 
        
        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM document_history WHERE doc_number = ? AND doc_type = 'Recepción'", (id_operacion,))
            if cursor.fetchone():
                conn.close()
                messagebox.showerror("Guía Duplicada", f"La Guía de Remisión N° {id_operacion} ya fue registrada anteriormente. No se pueden registrar documentos duplicados.")
                return
            conn.close()
        except Exception as e:
            print("Error validando historial SQLite:", e)

        log_seguridad = {
            "id_operacion": id_operacion,
            "estado": "Pendiente de Validación", 
            "fecha_registro": fecha_actual,
            "ejecutado_por": self.current_user,
            "origen_global": datos_globales['origen'],
            "motivo_global": datos_globales['motivo'],
            "total_items": len(self.lista_temporal),
            "detalles": []
        }

        try:
            for item in self.lista_temporal:
                temp_manager = KardexManager(item['producto'])
                if not temp_manager.product_id:
                    raise Exception(f"Producto {item['producto']} no encontrado en la base de datos.")
                
                dt = datetime.now()
                fecha_actual = dt.strftime("%Y-%m-%d %H:%M:%S")
                
                if str(item['costo']).strip() == "": item['costo'] = "0"
                
                lote_auto = id_operacion
                if 'lote' in item and item['lote'].strip():
                    lote_auto = item['lote'].strip()
                    
                dt_venc = datetime.strptime(item['vencimiento'], "%d/%m/%Y")
                venc_backend = dt_venc.strftime("%Y-%m-%d")
                
                # El KardexManager se instanció solo para validar que el producto exista (líneas previas)
                # No registramos la entrada en kardex_movements aún. Se registrará cuando el Admin lo valide.
                
                log_seguridad["detalles"].append({
                    "producto": item['producto'],
                    "cantidad": float(item['cantidad']),
                    "costo_unitario": item['costo'],
                    "vencimiento": venc_backend,
                    "lote_asignado": lote_auto
                })

            # Insertar en el historial
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO document_history (user, doc_type, doc_number, date, products, status, origen_global, motivo_global)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.current_user,
                "Recepción",
                id_operacion,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                json.dumps(log_seguridad["detalles"]),
                "Pendiente de Validación",
                log_seguridad["origen_global"],
                log_seguridad["motivo_global"]
            ))
            
            # Todo salió bien, confirmamos la transacción
            conn.commit()
            conn.close()
            
        except Exception as e:
            try:
                conn.rollback()
                conn.close()
            except: pass
            self.btn_guardar.configure(state="normal")
            return messagebox.showerror("Error Guardando", f"Se canceló toda la recepción debido a un error:\n{str(e)}")
            
        messagebox.showinfo("Operación Exitosa", "Documento archivado y procesado exitosamente.")
        prev_win.destroy()
        self.destroy()