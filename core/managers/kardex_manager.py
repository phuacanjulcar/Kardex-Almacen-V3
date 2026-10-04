import os
import sqlite3
from datetime import datetime
from core.database import get_connection

class KardexManager:
    def __init__(self, product_id_or_filepath):
        # Para compatibilidad temporal: Si llega un path de JSON, tratamos de sacar el nombre
        if isinstance(product_id_or_filepath, str) and product_id_or_filepath.endswith(".json"):
            name = os.path.splitext(os.path.basename(product_id_or_filepath))[0]
            self.product_name = name
        else:
            self.product_name = str(product_id_or_filepath)
            
        self.product_id = None
        self.method = "FEFO"
        self.kardex_data = []     
        self.print_rows = []      
        self.inventory_lots = []  
        self.balance = {"qty": 0, "total_cost": 0, "unit_cost": 0}
        self.metadata = {
            "name": self.product_name, "created_at": "", "Producto": self.product_name,
            "Unidad": "Unds", "Ubicacion": "Sin Asignar", "Categoria": "Sin Categoría",
            "Prefijo": "PAQ", "Stock_Minimo": 10, "Stock_Maximo": 100
        }
        self.load()

    def load(self):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Obtener Metadata del Producto
        cursor.execute("""
            SELECT p.*, z.name as zone_name, c.name as category_name
            FROM products p
            LEFT JOIN zones z ON p.zone_id = z.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.name = ?
        """, (self.product_name,))
        prod = cursor.fetchone()
        
        if not prod:
            conn.close()
            return
            
        self.product_id = prod['id']
        self.metadata = {
            "name": prod['name'],
            "Producto": prod['name'],
            "Unidad": prod['unit'],
            "Ubicacion": prod['zone_name'] or "Sin Asignar",
            "Categoria": prod['category_name'] or "Sin Categoría",
            "Prefijo": prod['prefix'],
            "Stock_Minimo": prod['min_stock'],
            "Stock_Maximo": prod['max_stock'],
            "created_at": prod['created_at']
        }
        
        # Obtener Movimientos (kardex_data)
        cursor.execute("""
            SELECT * FROM kardex_movements 
            WHERE product_id = ? 
            ORDER BY date ASC, (CASE WHEN type = 'SI' THEN 0 WHEN type = 'E' THEN 1 ELSE 2 END) ASC, id ASC
        """, (self.product_id,))
        
        moves = cursor.fetchall()
        self.kardex_data = []
        for m in moves:
            self.kardex_data.append({
                "db_id": m['id'],
                "type": m['type'],
                "Fecha_Hora": m['date'],
                "qty": float(m['qty'] or 0),
                "unit_cost": float(m['unit_cost'] or 0) if m['unit_cost'] is not None else None,
                "Registrado_Por": m['origin_dest'], # En el viejo app se mezclaban
                "Proveedor": m['origin_dest'],
                "Fecha_Vencimiento": m['expiration_date'],
                "Concepto": m['concept'],
                "lote_id": m['lot_code'],
                "Guia_Remision": m['document'],
                "lot_status": m['lot_status'] if 'lot_status' in m.keys() else 'Disponible',
                "out_of_hours": m['out_of_hours'] if 'out_of_hours' in m.keys() else 0
            })
            
        conn.close()
        self._recalculate_exact_logic()

    def save(self):
        if not self.product_id:
            return
            
        # Re-escribir los movimientos y lotes es ineficiente pero mantiene la compatibilidad
        # exacta con la lógica anterior de FEFO en memoria sin romper la UI actual.
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Eliminar lotes actuales y reescribir
        cursor.execute("DELETE FROM active_lots WHERE product_id = ?", (self.product_id,))
        for lot in self.inventory_lots:
            cursor.execute('''
                INSERT INTO active_lots (product_id, lot_code, qty, unit_cost, expiration_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.product_id, lot.get("lote_id", ""), lot["qty"], lot["unit_cost"], lot.get("fv", ""), lot.get("status", "Disponible")))
            
        # 2. Las inserciones de movimientos ahora se hacen directamente en register_entry / exit
        # por lo que save() sólo sincroniza lotes activos para reportes rápidos.
        conn.commit()
        conn.close()

    def _update_balance_from_lots(self):
        tq = sum(l["qty"] for l in self.inventory_lots)
        tc = sum(l["qty"] * l["unit_cost"] for l in self.inventory_lots)
        self.balance["qty"] = tq
        self.balance["total_cost"] = tc
        self.balance["unit_cost"] = (tc / tq) if tq > 0 else 0.0

    def _new_row(self):
        return {
            "Fecha": "", "Lote": "-", "Proveedor": "", "Concepto": "", "Fecha_Vencimiento": "",
            "Cantidad": "", "Precio_Unitario": "", "CantidadSaldo": "", "TotalSaldo": "",
            "Estatus": "Stock disponible", "Event_Index": None,
            "CantidadSalida": 0, "Salida_Costo_Total": 0,
            "Masivo": "-", "Guia": "-"
        }

    def register_entry(self, fecha, qty, unit_cost, prov, venc, user, lote_id, masivo=False, guia="-", lot_status="Disponible", concept="Entrada", db_conn=None):
        if not self.product_id: return False, "No existe producto"
        
        real_ts = datetime.now()
        real_timestamp_str = real_ts.strftime("%Y-%m-%d %H:%M:%S")
        out_of_hours = 1 if not (8 <= real_ts.hour <= 18) or not fecha.startswith(real_ts.strftime("%Y-%m-%d")) else 0

        conn = db_conn or get_connection()
        cursor = conn.cursor()
        
        # Insertar primero en active_lots para probar la unicidad (evita TOCTOU al crear lotes)
        try:
            cursor.execute('''
                INSERT INTO active_lots (product_id, lot_code, qty, unit_cost, expiration_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.product_id, lote_id, float(qty), float(unit_cost), venc, lot_status))
        except sqlite3.IntegrityError:
            if not db_conn: conn.close()
            return False, f"El lote {lote_id} ya existe en el sistema. Alguien más pudo haberlo creado justo ahora."
        
        cursor.execute('''
            INSERT INTO kardex_movements (product_id, date, lot_code, type, concept, document, origin_dest, expiration_date, qty, unit_cost, user, lot_status, real_timestamp, out_of_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.product_id, fecha, lote_id, "E", concept, guia, prov, venc, float(qty), float(unit_cost), user, lot_status, real_timestamp_str, out_of_hours))
        
        if not db_conn:
            conn.commit()
            conn.close()
            self.load()
            
        return True, ""

    def register_exit(self, fecha, qty, destino, user, lote_id, concept="Salida"):
        if not self.product_id: return False, "No existe el producto"
        qty = float(qty)
        
        real_ts = datetime.now()
        real_timestamp_str = real_ts.strftime("%Y-%m-%d %H:%M:%S")
        out_of_hours = 1 if not (8 <= real_ts.hour <= 18) or not fecha.startswith(real_ts.strftime("%Y-%m-%d")) else 0

        conn = get_connection()
        cursor = conn.cursor()
        
        # Bloqueo atómico (Atomic Update) para Condición de Carrera
        # SQLite actualizará la fila SOLO si el stock es suficiente
        cursor.execute('''
            UPDATE active_lots 
            SET qty = qty - ? 
            WHERE product_id = ? AND lot_code = ? AND qty >= ?
        ''', (qty, self.product_id, lote_id, qty))
        
        if cursor.rowcount == 0:
            # Si afectó 0 filas, significa que no había stock suficiente o no existe el lote
            conn.close()
            return False, f"Stock insuficiente en el paquete {lote_id} o alguien más lo retiró."

        # Insertar movimiento histórico si el update funcionó
        cursor.execute('''
            INSERT INTO kardex_movements (product_id, date, lot_code, type, concept, origin_dest, qty, user, real_timestamp, out_of_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.product_id, fecha, lote_id, "S", concept, destino, qty, user, real_timestamp_str, out_of_hours))
        
        conn.commit()
        conn.close()
        
        self.load()
        return True, ""

    def delete_event_at_index(self, index):
        if not (0 <= index < len(self.print_rows)): return
        ev_i = self.print_rows[index].get("Event_Index")
        if ev_i is None or not (0 <= ev_i < len(self.kardex_data)): return
        
        db_id = self.kardex_data[ev_i].get("db_id")
        tipo = self.kardex_data[ev_i].get("type")
        lote_id = self.kardex_data[ev_i].get("lote_id")
        
        if db_id:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Soft Delete the movement
            cursor.execute("""
                UPDATE kardex_movements 
                SET type = 'Anulado', concept = 'Movimiento Anulado', lot_status = 'Anulado', 
                    qty = 0, unit_cost = 0, total_cost = 0, balance_qty = 0, balance_total = 0 
                WHERE id = ?
            """, (db_id,))
            
            # Si era un Ingreso, anular el lote activo para que no pueda ser usado
            if tipo in ["E", "SI"] and lote_id:
                cursor.execute("""
                    UPDATE active_lots 
                    SET status = 'Anulado', qty = 0 
                    WHERE lot_code = ? AND product_id = ?
                """, (lote_id, self.product_id))
                
            conn.commit()
            conn.close()
        
        self.load()

    def _recalculate_exact_logic(self, sim_exit_qty=None):
        self.print_rows, self.inventory_lots = [], []
        self.balance = {"qty": 0, "total_cost": 0, "unit_cost": 0}
        self.lot_brands = {}

        for idx, ev in enumerate(self.kardex_data):
            tipo = ev.get("type")
            fecha = ev.get("Fecha_Hora", "")
            qty = float(ev.get("qty", 0) or 0)
            uc = float(ev.get("unit_cost", 0) or 0) if ev.get("unit_cost") is not None else None
            prov = ev.get("Proveedor", "")
            venc = ev.get("Fecha_Vencimiento", "")
            concepto = ev.get("Concepto", "")
            
            if tipo in ["SI", "E"]:
                if uc is None: continue
                lote_id = ev.get("lote_id", "Sin Cód.")
                l_status = ev.get("lot_status", "Disponible")
                
                # Extraer Marca de concepto si existe
                marca_val = prov
                if " (Marca: " in concepto and concepto.endswith(")"):
                    parts = concepto.split(" (Marca: ")
                    if len(parts) == 2:
                        concepto = parts[0]
                        marca_val = parts[1][:-1]
                self.lot_brands[lote_id] = marca_val

                self.inventory_lots.append({"qty": qty, "unit_cost": uc, "date": fecha, "fv": venc, "lote_id": lote_id, "status": l_status})
                self._update_balance_from_lots()
                
                row = self._new_row()
                row.update({"Fecha": fecha, "Lote": lote_id, "Destino": "-", "Marca": marca_val, "Proveedor": prov, "Concepto": concepto, "Fecha_Vencimiento": venc, "Cantidad": qty, "Precio_Unitario": uc, "CantidadSaldo": self.balance["qty"], "TotalSaldo": self.balance["total_cost"], "Estatus": f"Stock {l_status.lower()}", "Event_Index": idx, "Documento": ev.get("Guia_Remision", "-"), "out_of_hours": ev.get("out_of_hours", 0), "type": tipo})
                self.print_rows.append(row)

            elif tipo == "S":
                rem = qty
                lote_req = ev.get("lote_id")
                used = []

                if lote_req:
                    for i in range(len(self.inventory_lots)-1, -1, -1):
                        lot = self.inventory_lots[i]
                        if lot.get("lote_id") == lote_req:
                            if rem <= 0: break
                            actual = min(rem, lot["qty"])
                            used.append({"qty": actual, "uc": lot["unit_cost"], "fv": lot["fv"], "lote_id": lote_req})
                            lot["qty"] -= actual
                            rem -= actual
                            if lot["qty"] <= 0: self.inventory_lots.pop(i)
                else:
                    self.inventory_lots.sort(key=lambda x: (x.get("fv",""), x.get("date","")))
                    for i in range(len(self.inventory_lots)-1, -1, -1):
                        lot = self.inventory_lots[i]
                        if rem <= 0: break
                        actual = min(rem, lot["qty"])
                        used.append({"qty": actual, "uc": lot["unit_cost"], "fv": lot["fv"], "lote_id": lot.get("lote_id","")})
                        lot["qty"] -= actual
                        rem -= actual
                        if lot["qty"] <= 0: self.inventory_lots.pop(i)

                self._update_balance_from_lots()
                
                if used:
                    for u in used:
                        r = self._new_row()
                        r.update({"Fecha": fecha, "Lote": u["lote_id"], "Destino": prov, "Marca": self.lot_brands.get(u["lote_id"], "-"), "Proveedor": prov, "Concepto": concepto, "Fecha_Vencimiento": u["fv"], "CantidadSalida": u["qty"], "Salida_Costo_Total": u["qty"]*u["uc"], "CantidadSaldo": self.balance["qty"], "TotalSaldo": self.balance["total_cost"], "Estatus": "Salida Registrada", "Event_Index": idx, "Documento": ev.get("Guia_Remision", "-"), "out_of_hours": ev.get("out_of_hours", 0), "type": tipo})
                        self.print_rows.append(r)
                else:
                    r = self._new_row()
                    r.update({"Fecha": fecha, "Destino": prov, "Marca": "-", "Concepto": concepto, "CantidadSalida": qty, "CantidadSaldo": self.balance["qty"], "TotalSaldo": self.balance["total_cost"], "Estatus": "Salida sin stock", "Event_Index": idx, "out_of_hours": ev.get("out_of_hours", 0), "type": tipo})
                    self.print_rows.append(r)
            
            elif tipo == "Anulado":
                r = self._new_row()
                r.update({"Fecha": fecha, "Destino": "-", "Marca": "-", "Proveedor": "-", "Concepto": concepto, "Cantidad": 0, "Precio_Unitario": 0, "CantidadSaldo": self.balance["qty"], "TotalSaldo": self.balance["total_cost"], "Estatus": "Movimiento Anulado", "Event_Index": idx, "Documento": ev.get("Guia_Remision", "-"), "out_of_hours": ev.get("out_of_hours", 0), "type": tipo})
                self.print_rows.append(r)
        
        self.save()

    def get_resumen(self):
        val = sum(l["qty"]*l["unit_cost"] for l in self.inventory_lots)
        return {"total_qty": self.balance["qty"], "total_value": val}

    def simulate_issue(self, req_qty):
        req_qty = float(req_qty)
        if req_qty <= 0: return None
        if req_qty > self.balance["qty"]: return None

        sim_lots = [{"qty": l["qty"], "uc": l["unit_cost"], "fv": l.get("fv","")} for l in self.inventory_lots]
        sim_lots = [{"qty": l["qty"], "uc": l["unit_cost"], "fv": l.get("fv",""), "date": l.get("date","")} for l in self.inventory_lots]
        sim_lots.sort(key=lambda x: (x["fv"], x["date"]))
        rem = req_qty
        costo = 0.0
        used = []

        for lot in sim_lots:
            if lot["qty"] <= 0:
                continue
            actual = min(rem, lot["qty"])
            costo += actual * lot["uc"]
            used.append({"qty": actual, "uc": lot["uc"]})
            rem -= actual
            if rem <= 0: break

        return {"costo_total": costo, "lotes_usados": used}

    def export_to_excel(self):
        import pandas as pd
        import os
        ruta_salida = os.path.join(os.path.expanduser("~"), "Desktop", f"Kardex_{self.product_name}.xlsx")
        
        df = pd.DataFrame(self.print_rows)
        # Limpiar columnas no deseadas o renombrarlas
        cols_a_exportar = ["Fecha", "Concepto", "Guia", "Lote", "Fecha_Vencimiento", "Cantidad", "Precio_Unitario", "CantidadSalida", "Salida_Costo_Total", "CantidadSaldo", "TotalSaldo", "Estatus"]
        df = df[[c for c in cols_a_exportar if c in df.columns]]
        df = df.rename(columns={"Concepto": "Detalle_Operacion", "Guia": "Documento_Referencia"})
        
        df.to_excel(ruta_salida, index=False)
        return ruta_salida

    def export_to_pdf(self):
        from fpdf import FPDF
        import os
        
        ruta_salida = os.path.join(os.path.expanduser("~"), "Desktop", f"Kardex_{self.product_name}.pdf")
        
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, f"Reporte de Kardex - Producto: {self.product_name}", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 8)
        # Cabeceras
        headers = ["Fecha", "Detalle", "Lote", "Entrada Qty", "Salida Qty", "Saldo Qty", "Estatus"]
        col_widths = [35, 60, 40, 25, 25, 25, 40]
        
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 8, str(h), border=1, align='C')
        pdf.ln()
        
        pdf.set_font("Arial", size=8)
        for row in self.print_rows:
            pdf.cell(col_widths[0], 8, str(row.get('Fecha', ''))[:16], border=1)
            pdf.cell(col_widths[1], 8, str(row.get('Concepto', ''))[:30], border=1)
            pdf.cell(col_widths[2], 8, str(row.get('Lote', '')), border=1)
            pdf.cell(col_widths[3], 8, str(row.get('Cantidad', '')), border=1, align='R')
            pdf.cell(col_widths[4], 8, str(row.get('CantidadSalida', '')), border=1, align='R')
            pdf.cell(col_widths[5], 8, str(row.get('CantidadSaldo', '')), border=1, align='R')
            pdf.cell(col_widths[6], 8, str(row.get('Estatus', '')), border=1)
            pdf.ln()
            
        pdf.output(ruta_salida)
        return ruta_salida