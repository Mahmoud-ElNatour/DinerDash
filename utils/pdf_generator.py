import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from models import Settings

def generate_receipt(order, bill):
    """Generate a PDF receipt for the order"""
    
    # Create receipts directory if it doesn't exist
    receipts_dir = os.path.join('static', 'receipts')
    os.makedirs(receipts_dir, exist_ok=True)
    
    # Generate filename
    filename = f"receipt_{order.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(receipts_dir, filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    normal_style = styles['Normal']
    right_align_style = ParagraphStyle(
        'RightAlign',
        parent=styles['Normal'],
        alignment=TA_RIGHT
    )
    
    # Get settings
    settings = Settings.query.first()
    currency = settings.currency if settings else 'USD'
    receipt_note = settings.receipt_note if settings else 'Thank you for your visit!'
    
    # Title
    story.append(Paragraph("DINER POS RECEIPT", title_style))
    story.append(Spacer(1, 20))
    
    # Order details
    order_info = [
        ['Order ID:', str(order.id)],
        ['Date:', order.date.strftime('%Y-%m-%d %H:%M:%S')],
        ['Order Type:', order.order_type.value],
        ['Waiter:', order.user.full_name],
    ]
    
    if order.customer:
        order_info.append(['Customer:', order.customer.name])
    
    if order.table:
        order_info.append(['Table:', order.table.number])
    
    order_table = Table(order_info, colWidths=[2*inch, 3*inch])
    order_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(order_table)
    story.append(Spacer(1, 20))
    
    # Items table
    items_data = [['Item', 'Qty', 'Price', 'Total']]
    
    for item in order.items:
        items_data.append([
            item.item.name,
            str(item.quantity),
            f"{currency} {item.price:.2f}",
            f"{currency} {item.total:.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[3*inch, 0.8*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Totals
    subtotal = order.total
    discount = order.discount
    tax_amount = bill.tax_applied
    final_total = order.final_total
    
    totals_data = [
        ['Subtotal:', f"{currency} {subtotal:.2f}"],
        ['Discount:', f"{currency} {discount:.2f}"],
        ['Tax:', f"{currency} {tax_amount:.2f}"],
        ['', ''],
        ['TOTAL:', f"{currency} {final_total:.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[2*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 3), 'Helvetica'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 3), 10),
        ('FONTSIZE', (0, 4), (-1, 4), 12),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 3), (-1, 3), 1, colors.black),
    ]))
    
    story.append(totals_table)
    story.append(Spacer(1, 20))
    
    # Payment info
    payment_info = [
        ['Payment Method:', bill.payment_method],
        ['Payment Date:', bill.payment_date.strftime('%Y-%m-%d %H:%M:%S')],
        ['Amount Paid:', f"{currency} {bill.total_paid:.2f}"]
    ]
    
    payment_table = Table(payment_info, colWidths=[2*inch, 2*inch])
    payment_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(payment_table)
    story.append(Spacer(1, 30))
    
    # Footer note
    story.append(Paragraph(receipt_note, ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=12
    )))
    
    # Customer loyalty points if applicable
    if order.customer:
        points_earned = int(order.final_total / 10)
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Points Earned: {points_earned}", ParagraphStyle(
            'Center',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=10
        )))
        story.append(Paragraph(f"Total Points: {order.customer.points}", ParagraphStyle(
            'Center',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=10
        )))
    
    # Build PDF
    doc.build(story)
    
    return f"receipts/{filename}"
