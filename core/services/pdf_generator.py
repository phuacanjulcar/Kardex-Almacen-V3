import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from num2words import num2words
from core.database import get_connection

class PDFGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='Center', alignment=1, fontSize=14, spaceAfter=10, fontName="Helvetica-Bold"))
        self.styles.add(ParagraphStyle(name='Right', alignment=2, fontSize=10, spaceAfter=10))

    def _get_product_zone(self, product_name):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT z.name FROM products p 
                LEFT JOIN zones z ON p.zone_id = z.id 
                WHERE p.name = ?
            ''', (product_name,))
            row = cursor.fetchone()
            conn.close()
            return row['name'] if row and row['name'] else "Sin Zona"
        except Exception as e:
            return "Sin Zona"

    def format_fecha_lima(self, date_str):
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            return f"Lima, {dt.day} de {meses[dt.month-1]} de {dt.year}"
        except:
            return f"Lima, {date_str}"

    def generar_guia_remision(self, doc, output_path=None):
        if not output_path:
            output_path = os.path.join(self.output_dir, f"Guia_{doc.get('doc_number', 'SN')}.pdf")
        
        pdf = SimpleDocTemplate(output_path, pagesize=A4)
        elements = []
        
        elements.append(Paragraph("ALMACÉN INMACULADA", self.styles['Center']))
        elements.append(Paragraph(f"GUÍA DE REMISIÓN (RECEPCIÓN)", self.styles['Center']))
        elements.append(Spacer(1, 0.5*cm))
        
        elements.append(Paragraph(self.format_fecha_lima(doc.get('date', '')), self.styles['Right']))
        elements.append(Spacer(1, 0.5*cm))
        
        info_data = [
            ["N° Documento:", doc.get('doc_number', '')],
            ["Proveedor/Origen:", doc.get('origen_global', '')],
            ["Motivo/Observación:", doc.get('motivo_global', '')],
            ["Operario:", doc.get('user', '')]
        ]
        t_info = Table(info_data, colWidths=[4*cm, 10*cm])
        t_info.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ]))
        elements.append(t_info)
        elements.append(Spacer(1, 1*cm))
        
        try:
            detalles = json.loads(doc.get('products', '[]'))
        except:
            detalles = []
            
        is_donacion = "donacion" in doc.get('motivo_global', '').lower() or "donación" in doc.get('motivo_global', '').lower()

        table_data = [["Descripción", "Cantidad", "Costo U.", "Subtotal"]]
        total = 0.0
        
        for item in detalles:
            cant = float(item.get('cantidad', 0))
            if is_donacion:
                costo_str = "0.00"
                subtotal_str = "0.00"
            else:
                costo_u = float(item.get('costo_unitario', 0))
                subtotal = cant * costo_u
                total += subtotal
                costo_str = f"S/ {costo_u:.2f}"
                subtotal_str = f"S/ {subtotal:.2f}"
                
            table_data.append([item.get('producto', ''), f"{cant}", costo_str, subtotal_str])
            
        t_detalles = Table(table_data, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
        t_detalles.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t_detalles)
        elements.append(Spacer(1, 1*cm))
        
        if is_donacion:
            total_text = "SON: CERO SOLES (ES DONACIÓN)"
            elements.append(Paragraph(total_text, self.styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(f"<b>TOTAL S/. 0.00</b>", self.styles['Right']))
        else:
            try:
                entero = int(total)
                decimales = int(round((total - entero) * 100))
                letras = num2words(entero, lang='es').upper()
                total_text = f"SON: {letras} CON {decimales:02d}/100 SOLES"
            except Exception as e:
                total_text = f"TOTAL:"
            
            elements.append(Paragraph(total_text, self.styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(f"<b>TOTAL S/. {total:.2f}</b>", self.styles['Right']))
            
        pdf.build(elements)
        return output_path

    def generar_vale_despacho(self, doc, output_path=None):
        if not output_path:
            output_path = os.path.join(self.output_dir, f"Vale_{doc.get('doc_number', 'SN')}.pdf")
            
        pdf = SimpleDocTemplate(output_path, pagesize=A4)
        elements = []
        
        elements.append(Paragraph("ALMACÉN INMACULADA", self.styles['Center']))
        if doc.get('doc_type') == 'Receta':
            titulo = "RECETA DE PRODUCCIÓN (DESPACHADA)"
            label_doc = "N° Receta:"
        else:
            titulo = "VALE DE DESPACHO (VALIDADO)"
            label_doc = "N° Vale:"
            
        elements.append(Paragraph(titulo, self.styles['Center']))
        elements.append(Spacer(1, 0.5*cm))
        
        elements.append(Paragraph(self.format_fecha_lima(doc.get('date', '')), self.styles['Right']))
        elements.append(Spacer(1, 0.5*cm))
        
        info_data = [
            [label_doc, doc.get('doc_number', '')],
            ["Destino:", doc.get('origen_global', '')],
            ["Operario:", doc.get('user', '')]
        ]
        t_info = Table(info_data, colWidths=[4*cm, 10*cm])
        t_info.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ]))
        elements.append(t_info)
        elements.append(Spacer(1, 1*cm))
        
        try:
            detalles = json.loads(doc.get('products', '[]'))
        except:
            detalles = []
            
        table_data = [["Descripción", "Zona/Ubicación", "Lote", "Cantidad"]]
        
        for item in detalles:
            zona = self._get_product_zone(item.get('producto', ''))
            table_data.append([item.get('producto', ''), zona, item.get('lote_asignado', ''), str(item.get('cantidad', 0))])
            
        t_detalles = Table(table_data, colWidths=[6.5*cm, 4*cm, 3.5*cm, 3*cm])
        t_detalles.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t_detalles)
        
        # --- NUEVO: ESPACIO PARA FIRMA DE CONFORMIDAD ---
        elements.append(Spacer(1, 2*cm))
        sig_data = [
            ["_____________________________________"],
            ["Recibí Conforme (Firma)"],
            ["Nombre / DNI / Sello: _________________"]
        ]
        t_sig = Table(sig_data, colWidths=[8*cm], hAlign='CENTER')
        t_sig.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(t_sig)
        # -------------------------------------------------
        
        pdf.build(elements)
        return output_path
        
    def generar_receta(self, receta, output_path=None):
        if not output_path:
            output_path = os.path.join(self.output_dir, f"Receta_{receta.get('name', 'SN')}.pdf")
            
        pdf = SimpleDocTemplate(output_path, pagesize=A4)
        elements = []
        
        elements.append(Paragraph("ALMACÉN INMACULADA", self.styles['Center']))
        elements.append(Paragraph(f"RECETA DE PRODUCCIÓN / ARMADO", self.styles['Center']))
        elements.append(Spacer(1, 0.5*cm))
        
        info_data = [
            ["Nombre Receta:", receta.get('name', '')],
            ["Creado por:", receta.get('created_by', '')],
            ["Fecha Creación:", receta.get('created_at', '')]
        ]
        t_info = Table(info_data, colWidths=[4*cm, 10*cm])
        t_info.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ]))
        elements.append(t_info)
        elements.append(Spacer(1, 1*cm))
        
        table_data = [["Descripción del Producto", "Zona/Ubicación", "Cantidad Requerida"]]
        
        for item in receta.get('items', []):
            zona = self._get_product_zone(item.get('product_name', ''))
            table_data.append([item.get('product_name', ''), zona, str(item.get('quantity', 0))])
            
        t_detalles = Table(table_data, colWidths=[7*cm, 6*cm, 4*cm])
        t_detalles.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t_detalles)
        
        pdf.build(elements)
        return output_path
