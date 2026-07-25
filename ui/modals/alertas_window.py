import customtkinter as ctk
from tkinter import messagebox
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AlertasWindow(ctk.CTkToplevel):
    def __init__(self, master, current_user):
        super().__init__(master)
        self.title("Panel de Alertas")
        self.geometry("650x650")
        self.configure(fg_color="#F0F4F8")
        self.transient(master)
        self.attributes("-alpha", 0.0)
        self.grab_set()

        ctk.CTkLabel(self, text="Radar de Alertas", font=("Segoe UI", 22, "bold"), text_color="#E53935").pack(pady=(20, 5))
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.cargar_alertas()

    def cargar_alertas(self):
        productos_alertas = {}

        try:
            from core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            # Obtener lotes por vencer
            cursor.execute('''
                SELECT p.name, z.name as zone_name, l.lot_code, l.expiration_date, l.qty
                FROM active_lots l
                JOIN products p ON l.product_id = p.id
                LEFT JOIN zones z ON p.zone_id = z.id
                WHERE l.expiration_date IS NOT NULL AND l.expiration_date != '-' AND l.expiration_date != ''
            ''')
            
            lots = cursor.fetchall()
            
            # Obtener totales de stock para min/max
            cursor.execute('''
                SELECT p.name, z.name as zone_name, p.min_stock, p.max_stock, COALESCE(SUM(l.qty), 0) as total_stock
                FROM products p
                LEFT JOIN active_lots l ON p.id = l.product_id
                LEFT JOIN zones z ON p.zone_id = z.id
                GROUP BY p.id
            ''')
            stock_info = cursor.fetchall()
            
            conn.close()
            
            hoy = datetime.now().date()
            for row in lots:
                fv = row['expiration_date'].strip()
                try:
                    dt = datetime.strptime(fv, "%Y-%m-%d").date()
                    dias = (dt - hoy).days
                    
                    if dias <= 30:
                        prod = row['name']
                        if prod not in productos_alertas:
                            productos_alertas[prod] = {
                                "ubic": row['zone_name'] or "Sin Asignar",
                                "lotes": [],
                                "stock_alert": None
                            }
                        productos_alertas[prod]["lotes"].append({
                            "lote_id": row['lot_code'] or "Sin Cód.",
                            "fv": fv,
                            "dias": dias,
                            "stock": float(row['qty'] or 0)
                        })
                except:
                    pass
                    
            for prod in productos_alertas:
                productos_alertas[prod]["lotes"].sort(key=lambda x: x["dias"])
                
            for st in stock_info:
                prod = st['name']
                total = float(st['total_stock'])
                min_s = float(st['min_stock'] or 0)
                max_s = float(st['max_stock'] or 999999)
                
                alert_type = None
                if total < min_s: alert_type = ("BAJO STOCK MÍNIMO", "#EF4444", f"Stock: {total} < Min: {min_s}")
                elif total > max_s: alert_type = ("SOBRE STOCK MÁXIMO", "#F59E0B", f"Stock: {total} > Max: {max_s}")
                
                if alert_type:
                    if prod not in productos_alertas:
                        productos_alertas[prod] = {
                            "ubic": st['zone_name'] or "Sin Asignar",
                            "lotes": [],
                            "stock_alert": alert_type
                        }
                    else:
                        productos_alertas[prod]["stock_alert"] = alert_type
                
        except Exception as e:
            print(f"Error cargando alertas de SQLite: {e}")

        if not productos_alertas:
            ctk.CTkLabel(self.scroll, text="🎉 ¡Todo excelente! No hay vencimientos cercanos ni problemas de stock.", font=("Segoe UI", 15, "italic"), text_color="#2D3436").pack(pady=50)
            return

        lista_final = list(productos_alertas.items())
        
        def _get_urgency(item):
            lotes = item[1]["lotes"]
            if lotes: return lotes[0]["dias"]
            return 999
            
        lista_final.sort(key=_get_urgency)

        for prod_name, info in lista_final:
            lotes = info["lotes"]
            stock_alert = info.get("stock_alert")
            
            peor_dia = lotes[0]["dias"] if lotes else 999
            
            if peor_dia < 0: color, estado_gral, icono = "#C62828", "PRODUCTO CON LOTES VENCIDOS", "💀"
            elif peor_dia == 0: color, estado_gral, icono = "#E65100", "¡TIENE LOTES QUE VENCEN HOY!", "🚨"
            elif peor_dia <= 15: color, estado_gral, icono = "#F57C00", "RIESGO CRÍTICO", "⚠️"
            elif peor_dia <= 30: color, estado_gral, icono = "#FBC02D", "ALERTA TEMPRANA", "🔔"
            else: color, estado_gral, icono = stock_alert[1] if stock_alert else "#64748B", "ALERTA DE STOCK", "📦"
            
            if not lotes and stock_alert:
                color, estado_gral, icono = stock_alert[1], stock_alert[0], "📦"
            
            card = ctk.CTkFrame(self.scroll, fg_color="#FFFFFF", border_width=2, border_color=color, corner_radius=10)
            card.pack(fill="x", pady=8)
            
            top_frame = ctk.CTkFrame(card, fg_color="transparent")
            top_frame.pack(fill="x", padx=15, pady=(10, 5))
            ctk.CTkLabel(top_frame, text=f"{icono} {prod_name}", font=("Segoe UI", 16, "bold"), text_color="#121212").pack(side="left")
            ctk.CTkLabel(top_frame, text=estado_gral, font=("Segoe UI", 12, "bold"), text_color=color).pack(side="right")
            
            ctk.CTkLabel(card, text=f"📍 Ubicación: {info['ubic']}", font=("Segoe UI", 12), text_color="#546E7A").pack(anchor="w", padx=15, pady=(0, 5))
            
            if stock_alert:
                ctk.CTkLabel(card, text=f"📊 {stock_alert[0]}: {stock_alert[2]}", font=("Segoe UI", 12, "bold"), text_color=stock_alert[1]).pack(anchor="w", padx=15, pady=(0, 10))
            
            if not lotes: continue
            
            lots_frame = ctk.CTkFrame(card, fg_color="#F8FAFC", corner_radius=5)
            lots_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            for lot in lotes:
                d = lot["dias"]
                
                # --- LÓGICA GRAMATICAL Y DE URGENCIA ---
                if d < 0:
                    l_color = "#C62828"
                    l_est = "Vencido hace 1 día" if d == -1 else f"Vencido hace {abs(d)} días"
                elif d == 0:
                    l_color, l_est = "#E65100", "¡Vence HOY!"
                elif d == 1:
                    l_color, l_est = "#F57C00", "Vence mañana"
                elif d <= 15: 
                    l_color, l_est = "#F57C00", f"Vence en {d} días"
                else: 
                    l_color, l_est = "#FBC02D", f"Vence en {d} días"
                # ---------------------------------------

                row = ctk.CTkFrame(lots_frame, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=4)
                
                ctk.CTkLabel(row, text=f"📦 {lot['lote_id']}  |  Stock: {lot['stock']:,.2f}", font=("Segoe UI", 13, "bold"), text_color="#334155").pack(side="left")
                ctk.CTkLabel(row, text=l_est, font=("Segoe UI", 12, "bold"), text_color=l_color).pack(side="right")
