from django.template.loader import render_to_string
from django.http import HttpResponse
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO

def generate_purchase_receipt(compra):
    """
    Genera un PDF con el detalle de la compra en formato de boleta.
    """
    # Crear un buffer para el PDF
    buffer = BytesIO()
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Contenedor para los elementos del PDF
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Center',
        parent=styles['Heading1'],
        alignment=1,  # 0=Left, 1=Center, 2=Right
    ))
    
    # Título
    elements.append(Paragraph("Conecta Saber", styles['Center']))
    elements.append(Paragraph("Comprobante de Compra", styles['Center']))
    elements.append(Spacer(1, 20))
    
    # Información de la compra
    fecha = compra.fecha_compra.strftime("%d/%m/%Y %H:%M:%S")
    
    # Datos para la tabla
    data = [
        ['Nº de Compra:', str(compra.id)],
        ['Fecha:', fecha],
        ['Estudiante:', compra.estudiante.nombre_completo],
        ['Email:', compra.estudiante.email],
        ['Curso:', compra.curso.titulo],
        ['Precio:', f"${compra.monto_pagado:,.2f}"],
    ]
    
    # Crear tabla
    table = Table(data, colWidths=[120, 300])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Nota al pie
    elements.append(Paragraph(
        "Este documento es un comprobante de compra válido.",
        styles['Normal']
    ))
    
    # Generar PDF
    doc.build(elements)
    
    # Obtener el valor del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf