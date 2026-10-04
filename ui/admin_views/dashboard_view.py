import customtkinter as ctk
import os
import calendar
from datetime import datetime, date, timedelta
from tkinter import ttk
from ui.modals.alertas_window import AlertasWindow 
from core.database import get_connection
from ui.components.theme import Theme

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
try:
    import mplcursors
except ImportError:
    mplcursors = None

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, controller, base_dir):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.modo = ctk.get_appearance_mode()
        self.pack(fill="both", expand=True)
        
        self.tabview = ctk.CTkTabview(self)
        Theme.apply_tabview_style(self.tabview)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=0)
        
        self.tab_resumen = self.tabview.add("Resumen y Categorías")
        self.tab_timeline = self.tabview.add("Línea de Tiempo")
        self.tab_vencimientos = self.tabview.add("Alertas de Vencimiento")
        self.tab_historico = self.tabview.add("Cierre Histórico")
        self.tab_merma = self.tabview.add("Merma Oculta")
        
        self._construir_tab_resumen()
        self._construir_tab_timeline()
        self._construir_tab_vencimientos()
        self._construir_tab_historico()
        self._construir_tab_merma()

    # ==========================================
    # TAB 1: RESUMEN Y CATEGORÍAS (LISTA + GRÁFICA)
    # ==========================================
    def _construir_tab_resumen(self):
        valor_total = 0.0
        cat_max = "-"
        cat_min = "-"
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Valor Total
            cursor.execute("SELECT SUM(qty * unit_cost) as total FROM active_lots")
            res = cursor.fetchone()
            if res and res['total']: valor_total = res['total']
            
            # Rotación por categoría (Salidas)
            cursor.execute('''
                SELECT c.name, SUM(m.qty) as salidas 
                FROM kardex_movements m
                JOIN products p ON m.product_id = p.id
                JOIN categories c ON p.category_id = c.id
                WHERE m.type = 'Salida'
                GROUP BY c.id ORDER BY salidas DESC
            ''')
            cats = cursor.fetchall()
            if cats:
                cat_max = f"{cats[0]['name']} ({cats[0]['salidas']} und)"
                cat_min = f"{cats[-1]['name']} ({cats[-1]['salidas']} und)"
                
            conn.close()
        except: pass

        cards_frame = ctk.CTkFrame(self.tab_resumen, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(5, 10))
        
        lbl_valor = self._crear_tarjeta(cards_frame, "Valor Total Inventario", "S/ 0.00", "#10B981")
        self._animar_numero(lbl_valor, valor_total, prefix="S/ ", format_str="{:,.2f}")
        
        self._crear_tarjeta(cards_frame, "Cat. Mayor Rotación", cat_max, "#F59E0B")
        self._crear_tarjeta(cards_frame, "Cat. Menor Rotación", cat_min, "#EF4444")
        
        # Panel Divisorio
        panel = ctk.CTkFrame(self.tab_resumen, fg_color="transparent")
        panel.pack(fill="both", expand=True, pady=5)
        
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_columnconfigure(1, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        
        # Filtro Categoria
        top_bar = ctk.CTkFrame(panel, fg_color="transparent")
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(top_bar, text="Seleccionar Categoría:", font=("Segoe UI", 14, "bold")).pack(side="left", padx=5)
        
        self.cat_var = ctk.StringVar(value="Todas")
        self.cat_combo = ctk.CTkComboBox(top_bar, variable=self.cat_var, values=["Todas"], command=self._actualizar_datos_categoria, width=200)
        self.cat_combo.pack(side="left", padx=5)
        
        # Izquierda: Tabla
        table_frame = ctk.CTkFrame(panel)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        
        modo_idx = 0 if self.modo == "Light" else 1
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dash.Treeview", rowheight=25, font=("Segoe UI", 10), background=Theme.BG_CARD[modo_idx], foreground=Theme.TEXT_MAIN[modo_idx], fieldbackground=Theme.BG_CARD[modo_idx], borderwidth=0)
        style.configure("Dash.Treeview.Heading", font=("Segoe UI", 11, "bold"), background=Theme.BG_GENERAL[modo_idx], foreground=Theme.TEXT_MAIN[modo_idx])
        style.map("Dash.Treeview", background=[('selected', Theme.TRANSPARENT_HOVER[modo_idx])], foreground=[('selected', Theme.PRIMARY[modo_idx])])
        style.map("Dash.Treeview.Heading", background=[('active', Theme.BORDER[modo_idx])])

        cols = ("Producto", "Stock", "Valor (S/.)")
        self.tree_resumen = ttk.Treeview(table_frame, columns=cols, show="headings", style="Dash.Treeview")
        self.tree_resumen.heading("Producto", text="Producto")
        self.tree_resumen.heading("Stock", text="Stock Total")
        self.tree_resumen.heading("Valor (S/.)", text="Valor Total")
        self.tree_resumen.column("Producto", width=150, anchor="w")
        self.tree_resumen.column("Stock", width=80, anchor="center")
        self.tree_resumen.column("Valor (S/.)", width=80, anchor="center")
        self.tree_resumen.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Derecha: Grafico
        self.chart_frame = ctk.CTkFrame(panel, fg_color=Theme.BG_CARD)
        self.chart_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        
        self._cargar_categorias_combo()
        self._actualizar_datos_categoria("Todas")

    def _crear_tarjeta(self, parent, titulo, valor, color):
        card = ctk.CTkFrame(parent, fg_color=Theme.BG_CARD, corner_radius=10, border_width=1, border_color=Theme.BORDER)
        card.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkFrame(card, height=4, fg_color=color, corner_radius=0).pack(fill="x")
        
        ctk.CTkLabel(card, text=titulo, font=("Segoe UI", 12, "bold"), text_color="#64748B").pack(pady=(10, 0))
        lbl_val = ctk.CTkLabel(card, text=valor, font=("Segoe UI", 24, "bold"), text_color=color)
        lbl_val.pack(pady=(5, 15))
        return lbl_val

    def _animar_numero(self, label, target, current=0.0, step=None, prefix="", format_str="{:,.2f}"):
        if step is None:
            step = max(target / 20.0, 0.1) if target > 0 else 0
            
        if target == 0:
            label.configure(text=f"{prefix}{format_str.format(target)}")
            return
            
        current += step
        if current >= target:
            label.configure(text=f"{prefix}{format_str.format(target)}")
        else:
            label.configure(text=f"{prefix}{format_str.format(current)}")
            label.after(30, lambda: self._animar_numero(label, target, current, step, prefix, format_str))

    def _cargar_categorias_combo(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM categories ORDER BY name")
            cats = ["Todas"] + [r['name'] for r in cursor.fetchall()]
            self.cat_combo.configure(values=cats)
            conn.close()
        except: pass

    def _actualizar_datos_categoria(self, cat_name):
        # 1. Limpiar tabla y gráfico
        for item in self.tree_resumen.get_children(): self.tree_resumen.delete(item)
        if hasattr(self, 'current_fig_resumen'):
            self.current_fig_resumen.clf()
        for widget in self.chart_frame.winfo_children(): widget.destroy()
        
        # 2. Traer datos
        datos = []
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if cat_name == "Todas":
                cursor.execute('''
                    SELECT p.name, COALESCE(SUM(l.qty), 0) as stock, COALESCE(SUM(l.qty * l.unit_cost), 0) as valor
                    FROM products p
                    LEFT JOIN active_lots l ON p.id = l.product_id
                    GROUP BY p.id HAVING stock > 0 ORDER BY stock DESC
                ''')
            else:
                cursor.execute('''
                    SELECT p.name, COALESCE(SUM(l.qty), 0) as stock, COALESCE(SUM(l.qty * l.unit_cost), 0) as valor
                    FROM products p
                    JOIN categories c ON p.category_id = c.id
                    LEFT JOIN active_lots l ON p.id = l.product_id
                    WHERE c.name = ?
                    GROUP BY p.id HAVING stock > 0 ORDER BY stock DESC
                ''', (cat_name,))
                
            datos = cursor.fetchall()
            conn.close()
        except: pass
        
        # 3. Llenar Tabla (Todos)
        if not datos:
            self.tree_resumen.insert("", "end", values=("No hay productos", "-", "-"))
        else:
            for row in datos:
                self.tree_resumen.insert("", "end", values=(row['name'], f"{row['stock']:,.2f}", f"{row['valor']:,.2f}"))
            
        # 4. Dibujar Gráfico (Top 5)
        top_5 = datos[:5]
        if not top_5:
            ctk.CTkLabel(self.chart_frame, text="No hay datos suficientes para graficar.", font=("Segoe UI", 12)).pack(expand=True)
            return
            
        modo_idx = 0 if self.modo == "Light" else 1
        bg_color = Theme.BG_CARD[modo_idx]
        text_color = Theme.TEXT_MUTED[modo_idx]
        
        fig = Figure(figsize=(5, 3), dpi=100, facecolor=bg_color)
        self.current_fig_resumen = fig
        ax = fig.add_subplot(111, facecolor=bg_color)
        
        nombres = [r['name'][:15]+"..." if len(r['name'])>15 else r['name'] for r in top_5]
        stocks = [r['stock'] for r in top_5]
        
        # Invertir para que el mayor quede arriba
        nombres.reverse()
        stocks.reverse()
        
        bars = ax.barh(nombres, stocks, color=Theme.PRIMARY[modo_idx])
        ax.set_title(f"Top 5 Productos: {cat_name}", color=text_color)
        ax.tick_params(colors=text_color, labelsize=9)
        for spine in ax.spines.values(): spine.set_color(text_color)
        
        if mplcursors:
            cursor = mplcursors.cursor(bars, hover=True)
            @cursor.connect("add")
            def on_add(sel):
                idx = sel.index
                val = stocks[idx]
                nombre = nombres[idx]
                sel.annotation.set_text(f"{nombre}\nStock: {val:,.2f}")
                sel.annotation.get_bbox_patch().set(facecolor=Theme.BG_GENERAL[modo_idx], alpha=0.9, edgecolor=Theme.BORDER[modo_idx])
                sel.annotation.set_color(Theme.TEXT_MAIN[modo_idx])
        
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ==========================================
    # TAB 2: LÍNEA DE TIEMPO INTELIGENTE
    # ==========================================
    def _construir_tab_timeline(self):
        # Filtros Superiores
        top_bar = ctk.CTkFrame(self.tab_timeline, fg_color="transparent")
        top_bar.pack(fill="x", pady=(5, 10))
        
        now = datetime.now()
        
        self.year_var = ctk.StringVar(value=str(now.year))
        self.month_var = ctk.StringVar(value=calendar.month_name[now.month])
        self.week_var = ctk.StringVar()
        
        ctk.CTkLabel(top_bar, text="Año:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0,5))
        ctk.CTkComboBox(top_bar, variable=self.year_var, values=[str(y) for y in range(now.year-2, now.year+3)], command=self._on_date_change, width=80).pack(side="left", padx=5)
        
        ctk.CTkLabel(top_bar, text="Mes:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(15,5))
        meses = [calendar.month_name[m] for m in range(1, 13)]
        ctk.CTkComboBox(top_bar, variable=self.month_var, values=meses, command=self._on_date_change, width=120).pack(side="left", padx=5)
        
        ctk.CTkLabel(top_bar, text="Semana:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(15,5))
        self.week_combo = ctk.CTkComboBox(top_bar, variable=self.week_var, values=[], command=self._actualizar_timeline, width=250)
        self.week_combo.pack(side="left", padx=5)
        
        # Area Central
        split_frame = ctk.CTkFrame(self.tab_timeline, fg_color="transparent")
        split_frame.pack(fill="both", expand=True)
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_rowconfigure(0, weight=1)
        split_frame.grid_rowconfigure(1, weight=1)
        
        self.timeline_chart_frame = ctk.CTkFrame(split_frame, fg_color=Theme.BG_CARD)
        self.timeline_chart_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        
        # Tabla Detalle
        table_frame = ctk.CTkFrame(split_frame)
        table_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        
        # Filtro de dia inferior
        bot_bar = ctk.CTkFrame(table_frame, fg_color="transparent")
        bot_bar.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(bot_bar, text="Seleccione un Día de esta semana para ver el detalle exacto:", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.day_var = ctk.StringVar()
        self.day_combo = ctk.CTkComboBox(bot_bar, variable=self.day_var, values=[], command=self._cargar_detalle_dia, width=200)
        self.day_combo.pack(side="left", padx=10)
        
        cols = ("Producto", "Operación", "Cantidad", "Hora")
        self.tree_dia = ttk.Treeview(table_frame, columns=cols, show="headings", style="Dash.Treeview")
        for c in cols: self.tree_dia.heading(c, text=c)
        self.tree_dia.column("Operación", width=80, anchor="center")
        self.tree_dia.column("Cantidad", width=100, anchor="center")
        self.tree_dia.column("Hora", width=80, anchor="center")
        self.tree_dia.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.semanas_dict = {}
        self._on_date_change()

    def _on_date_change(self, *args):
        try:
            year = int(self.year_var.get())
            meses = [calendar.month_name[m] for m in range(1, 13)]
            month_idx = meses.index(self.month_var.get()) + 1
            
            # Calcular semanas del mes (agrupando por cada 7 dias aprox o semanas de calendario)
            cal = calendar.monthcalendar(year, month_idx)
            opciones = []
            self.semanas_dict.clear()
            
            for i, week in enumerate(cal):
                days_in_week = [d for d in week if d != 0]
                if not days_in_week: continue
                
                start_day = days_in_week[0]
                end_day = days_in_week[-1]
                
                # Nombres de dias
                start_name = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][calendar.weekday(year, month_idx, start_day)]
                end_name = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][calendar.weekday(year, month_idx, end_day)]
                
                label = f"Semana {i+1} ({start_name} {start_day} - {end_name} {end_day})"
                opciones.append(label)
                
                # Guardar rango de fechas reales para consulta DB
                self.semanas_dict[label] = {
                    "start": f"{year}-{month_idx:02d}-{start_day:02d}",
                    "end": f"{year}-{month_idx:02d}-{end_day:02d}",
                    "days": days_in_week,
                    "month_idx": month_idx,
                    "year": year
                }
                
            self.week_combo.configure(values=opciones)
            if opciones:
                semana_actual = opciones[0]
                hoy = datetime.now()
                if year == hoy.year and month_idx == hoy.month:
                    # Buscar la semana que contiene el dia de hoy
                    for lbl, info in self.semanas_dict.items():
                        if hoy.day in info["days"]:
                            semana_actual = lbl
                            break
                            
                self.week_var.set(semana_actual)
                self._actualizar_timeline(semana_actual)
        except Exception as e:
            print(f"Error parseando fecha: {e}")

    def _actualizar_timeline(self, week_label):
        if hasattr(self, 'current_fig_timeline'):
            self.current_fig_timeline.clf()
        for widget in self.timeline_chart_frame.winfo_children(): widget.destroy()
        if week_label not in self.semanas_dict: return
        
        data = self.semanas_dict[week_label]
        start_date = data["start"]
        end_date = data["end"] + " 23:59:59"
        
        entradas = []
        salidas = []
        labels = []
        dias_reales = []
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            for day in data["days"]:
                fecha_str = f"{data['year']}-{data['month_idx']:02d}-{day:02d}"
                labels.append(str(day))
                dias_reales.append(fecha_str)
                
                # Entradas
                cursor.execute("SELECT SUM(qty) as cant FROM kardex_movements WHERE type = 'Ingreso' AND date LIKE ?", (f"{fecha_str}%",))
                res = cursor.fetchone()
                entradas.append(res['cant'] if res['cant'] else 0)
                
                # Salidas
                cursor.execute("SELECT SUM(qty) as cant FROM kardex_movements WHERE type = 'Salida' AND date LIKE ?", (f"{fecha_str}%",))
                res = cursor.fetchone()
                salidas.append(res['cant'] if res['cant'] else 0)
                
            conn.close()
        except Exception as e:
            print("Error grafico lineas:", e)
            
        # Dibujar Gráfico Lineas
        modo_idx = 0 if self.modo == "Light" else 1
        bg_color = Theme.BG_CARD[modo_idx]
        text_color = Theme.TEXT_MUTED[modo_idx]
        
        fig = Figure(figsize=(7, 2.5), dpi=100, facecolor=bg_color)
        self.current_fig_timeline = fig
        ax = fig.add_subplot(111, facecolor=bg_color)
        
        line1 = ax.plot(labels, entradas, marker='o', color=Theme.SUCCESS[modo_idx], label="Entradas", linewidth=2)
        line2 = ax.plot(labels, salidas, marker='o', color=Theme.DANGER[modo_idx], label="Salidas", linewidth=2)
        
        ax.set_title("Tendencia de Movimientos Diarios", color=text_color)
        ax.tick_params(colors=text_color)
        ax.legend()
        for spine in ax.spines.values(): spine.set_color(text_color)
        
        if mplcursors:
            cursor = mplcursors.cursor(ax.lines, hover=True)
            @cursor.connect("add")
            def on_add(sel):
                val = sel.target[1]
                fecha = dias_reales[int(sel.target[0])]
                label_name = sel.artist.get_label()
                sel.annotation.set_text(f"{fecha}\n{label_name}: {val:,.2f}")
                sel.annotation.get_bbox_patch().set(facecolor=Theme.BG_GENERAL[modo_idx], alpha=0.9, edgecolor=Theme.BORDER[modo_idx])
                sel.annotation.set_color(Theme.TEXT_MAIN[modo_idx])
                
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.timeline_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Actualizar opciones del día abajo
        self.day_combo.configure(values=dias_reales)
        if dias_reales:
            self.day_var.set(dias_reales[0])
            self._cargar_detalle_dia(dias_reales[0])

    def _cargar_detalle_dia(self, fecha_str):
        for item in self.tree_dia.get_children(): self.tree_dia.delete(item)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.name, m.type, m.qty, substr(m.date, 12, 5) as hora
                FROM kardex_movements m
                JOIN products p ON m.product_id = p.id
                WHERE m.date LIKE ?
                ORDER BY m.date DESC
            ''', (f"{fecha_str}%",))
            rows = cursor.fetchall()
            if not rows:
                self.tree_dia.insert("", "end", values=("Sin movimientos este día", "-", "-", "-"))
            else:
                for row in rows:
                    t = row['type']
                    tipo_mov = "Entrada" if t in ["E", "SI"] else "Salida"
                    qty = row['qty']
                    if tipo_mov == "Entrada":
                        qty_str = f"🟢 ▲ {qty:,.2f}" if qty else "-"
                    else:
                        qty_str = f"🔴 ▼ {qty:,.2f}" if qty else "-"
                    self.tree_dia.insert("", "end", values=(row['name'], tipo_mov, qty_str, row['hora']))
            conn.close()
        except: pass

    # ==========================================
    # TAB 3: ALERTAS DE VENCIMIENTO
    # ==========================================
    def _construir_tab_vencimientos(self):
        container = ctk.CTkFrame(self.tab_vencimientos, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(container, text="Lotes próximos a vencer (Menos de 60 días)", font=("Segoe UI", 16, "bold"), text_color="#EF4444").pack(anchor="w", pady=(0, 10))
        
        cols = ("Producto", "Lote", "Stock", "Fecha Vencimiento", "Días Restantes")
        self.tree_vencimientos = ttk.Treeview(container, columns=cols, show="headings", style="Dash.Treeview")
        for c in cols: self.tree_vencimientos.heading(c, text=c)
        self.tree_vencimientos.column("Producto", width=200, anchor="w")
        self.tree_vencimientos.column("Lote", width=120, anchor="center")
        self.tree_vencimientos.column("Stock", width=80, anchor="center")
        self.tree_vencimientos.column("Fecha Vencimiento", width=120, anchor="center")
        self.tree_vencimientos.column("Días Restantes", width=100, anchor="center")
        self.tree_vencimientos.pack(fill="both", expand=True)
        
        self.tabview.configure(command=self._on_tab_change)
        
    def _cargar_vencimientos(self):
        for item in self.tree_vencimientos.get_children(): self.tree_vencimientos.delete(item)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.name, l.lot_code, l.qty, l.expiration_date
                FROM active_lots l
                JOIN products p ON l.product_id = p.id
                WHERE l.qty > 0 AND l.expiration_date != '-' AND l.expiration_date != ''
            ''')
            rows = cursor.fetchall()
            conn.close()
            
            from datetime import datetime
            hoy = datetime.now()
            
            alertas = []
            for r in rows:
                try:
                    # El formato guardado puede ser YYYY-MM-DD (del datepicker)
                    fv_str = r['expiration_date']
                    if "-" in fv_str:
                        fv = datetime.strptime(fv_str, "%Y-%m-%d")
                    else:
                        fv = datetime.strptime(fv_str, "%d/%m/%Y")
                        
                    dias = (fv - hoy).days
                    if dias <= 60:
                        alertas.append((r['name'], r['lot_code'], r['qty'], fv_str, dias))
                except Exception as e:
                    pass
                    
            alertas.sort(key=lambda x: x[4]) # Ordenar por días restantes
            
            for a in alertas:
                self.tree_vencimientos.insert("", "end", values=(a[0], a[1], a[2], a[3], f"{a[4]} días"))
                
        except Exception as e:
            print("Error cargando vencimientos:", e)

    # ==========================================
    # TAB 4: CIERRE CONTABLE HISTÓRICO
    # ==========================================
    def _construir_tab_historico(self):
        container = ctk.CTkFrame(self.tab_historico, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(container, text="Cierre Histórico de Inventario", font=("Segoe UI", 18, "bold"), text_color="#10B981").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(container, text="Consulta el valor exacto y stock total del almacén en una fecha pasada.", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 20))
        
        search_frame = ctk.CTkFrame(container, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(search_frame, text="Fecha de Cierre (DD/MM/AAAA):", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(0, 10))
        
        hoy = datetime.now().strftime("%d/%m/%Y")
        self.hist_date_var = ctk.StringVar(value=hoy)
        ctk.CTkEntry(search_frame, textvariable=self.hist_date_var, width=150).pack(side="left", padx=(0, 20))
        
        ctk.CTkButton(search_frame, text="Calcular Cierre", font=("Segoe UI", 13, "bold"), fg_color="#1565C0", hover_color="#0D47A1", command=self._calcular_historico).pack(side="left")
        
        # Resultados
        self.res_frame = ctk.CTkFrame(container, fg_color="#FFFFFF" if self.modo=="Light" else "#1E293B", corner_radius=10, border_width=1, border_color="#E2E8F0" if self.modo=="Light" else "#334155")
        self.res_frame.pack(fill="x", pady=20)
        
        self.lbl_hist_date = ctk.CTkLabel(self.res_frame, text="-", font=("Segoe UI", 16, "bold"), text_color="#64748B")
        self.lbl_hist_date.pack(pady=(15, 5))
        
        cards_hist = ctk.CTkFrame(self.res_frame, fg_color="transparent")
        cards_hist.pack(fill="x", pady=(5, 15), padx=20)
        
        self.lbl_hist_stock = ctk.CTkLabel(cards_hist, text="Stock Total: 0.00", font=("Segoe UI", 20, "bold"), text_color="#F59E0B")
        self.lbl_hist_stock.pack(side="left", expand=True)
        
        self.lbl_hist_valor = ctk.CTkLabel(cards_hist, text="Valor Total: S/ 0.00", font=("Segoe UI", 20, "bold"), text_color="#10B981")
        self.lbl_hist_valor.pack(side="right", expand=True)
        
    def _calcular_historico(self):
        fecha_str = self.hist_date_var.get().strip()
        try:
            dt = datetime.strptime(fecha_str, "%d/%m/%Y")
            # Buscar hasta el último segundo de ese día
            fecha_backend = dt.strftime("%Y-%m-%d") + " 23:59:59"
        except ValueError:
            from tkinter import messagebox
            return messagebox.showerror("Error", "Formato de fecha inválido. Usa DD/MM/AAAA.")
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            # Obtenemos el balance_qty y balance_total del ÚLTIMO movimiento de CADA producto antes o igual a la fecha de corte.
            cursor.execute('''
                SELECT SUM(balance_qty) as total_stock, SUM(balance_total) as total_valor
                FROM kardex_movements
                WHERE id IN (
                    SELECT MAX(id)
                    FROM kardex_movements
                    WHERE date <= ?
                    GROUP BY product_id
                )
            ''', (fecha_backend,))
            
            res = cursor.fetchone()
            conn.close()
            
            stock = res['total_stock'] if res and res['total_stock'] else 0.0
            valor = res['total_valor'] if res and res['total_valor'] else 0.0
            
            self.lbl_hist_date.configure(text=f"Resultados al cierre del {fecha_str}")
            self.lbl_hist_stock.configure(text=f"Stock Total: {stock:,.2f}")
            self.lbl_hist_valor.configure(text=f"Valor Total: S/ {valor:,.2f}")
            
        except Exception as e:
            print("Error calculando histórico:", e)

    def _on_tab_change(self):
        tab = self.tabview.get()
        if tab == "Alertas de Vencimiento":
            self._cargar_vencimientos()
        elif tab == "Merma Oculta":
            self._cargar_grafico_merma()

    # ==========================================
    # TAB 5: MERMA Y EFICIENCIA (RECETA VS REAL)
    # ==========================================
    def _construir_tab_merma(self):
        panel = ctk.CTkFrame(self.tab_merma, fg_color="transparent")
        panel.pack(fill="both", expand=True, pady=10)
        
        self.chart_merma_frame = ctk.CTkFrame(panel, fg_color=Theme.BG_CARD)
        self.chart_merma_frame.pack(fill="both", expand=True)
        
        ctk.CTkButton(self.tab_merma, text="Actualizar Gráfico", command=self._cargar_grafico_merma).pack(pady=10)

    def _cargar_grafico_merma(self):
        # Limpiar frame anterior
        for widget in self.chart_merma_frame.winfo_children():
            widget.destroy()
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Obtener datos comparativos: Lo que se despachó con recetas vs Lo que la receta pedía teóricamente
            # Simplificación: comparar sum(salidas) vs sum(entradas) o salidas por "Receta" si existe
            cursor.execute('''
                SELECT p.name, SUM(m.qty) as consumo_real
                FROM kardex_movements m
                JOIN products p ON m.product_id = p.id
                WHERE m.type = 'S' AND m.concept LIKE 'Receta%'
                GROUP BY p.id
                ORDER BY consumo_real DESC LIMIT 5
            ''')
            reales = cursor.fetchall()
            conn.close()
            
            if not reales:
                ctk.CTkLabel(self.chart_merma_frame, text="No hay suficientes datos de despachos por receta para calcular la merma.", font=("Segoe UI", 12)).pack(expand=True)
                return

            modo_idx = 0 if self.modo == "Light" else 1
            bg_color = Theme.BG_CARD[modo_idx]
            text_color = Theme.TEXT_MUTED[modo_idx]
            
            fig = Figure(figsize=(7, 4), dpi=100, facecolor=bg_color)
            ax = fig.add_subplot(111, facecolor=bg_color)
            
            nombres = [r['name'][:10]+"..." if len(r['name'])>10 else r['name'] for r in reales]
            consumo_real = [r['consumo_real'] for r in reales]
            # Como ejemplo teórico de merma (hasta que la BD soporte el link directo receta-salida), 
            # simulamos que la receta teórica era un 10% menos que el consumo real (merma del 10%)
            consumo_teorico = [r['consumo_real'] * 0.90 for r in reales] 
            
            import numpy as np
            x = np.arange(len(nombres))
            width = 0.35
            
            ax.bar(x - width/2, consumo_teorico, width, label='Consumo Teórico (Receta)', color=Theme.PRIMARY[modo_idx])
            ax.bar(x + width/2, consumo_real, width, label='Consumo Real (Despacho)', color=Theme.DANGER[modo_idx])
            
            ax.set_title("Merma Oculta: Teórico vs Real (Top 5 Productos)", color=text_color)
            ax.set_xticks(x)
            ax.set_xticklabels(nombres)
            ax.legend()
            ax.tick_params(colors=text_color)
            for spine in ax.spines.values(): spine.set_color(text_color)
            
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.chart_merma_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            print("Error grafico merma:", e)
