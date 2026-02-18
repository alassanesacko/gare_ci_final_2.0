from io import BytesIO
from datetime import datetime
from django.http import FileResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import qrcode
import io


def generate_ticket_pdf(reservation):
    """
    Génère un PDF de ticket pour une réservation.
    
    Args:
        reservation: Objet Reservation
    
    Returns:
        BytesIO: Fichier PDF en mémoire
    """
    # Créer un buffer en mémoire
    buffer = BytesIO()
    
    # Créer le document PDF
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
        title=f"Ticket_Reservation_{reservation.id}"
    )
    
    # Conteneur pour les éléments du PDF
    elements = []
    
    # Récupérer les styles
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f5233'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1f5233'),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4
    )
    
    # Titre principal
    title = Paragraph("TICKET DE RÉSERVATION", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Récupérer les informations
    departure = reservation.departure
    trip = departure.trip
    bus = departure.bus
    user = reservation.user
    
    # ===== SECTION: INFORMATIONS DE RÉSERVATION =====
    elements.append(Paragraph("INFORMATIONS GÉNÉRALES", heading_style))
    
    info_data = [
        ['Numéro de Siège :', reservation.seat_number or 'N/A'],
        ['ID Réservation :', str(reservation.id)],
        ['Date de réservation :', reservation.booked_at.strftime('%d/%m/%Y à %H:%M')],
        ['Statut :', get_status_display(reservation.status)],
    ]
    
    info_table = Table(info_data, colWidths=[2.5*inch, 2.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # ===== SECTION: INFORMATIONS DU PASSAGER =====
    elements.append(Paragraph("INFORMATIONS DU PASSAGER", heading_style))
    
    passenger_data = [
        ['Nom complet :', f"{user.first_name} {user.last_name}"],
        ['Email :', user.email],
        ['Téléphone :', user.phone or 'N/A'],
    ]
    
    passenger_table = Table(passenger_data, colWidths=[2.5*inch, 2.5*inch])
    passenger_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    
    elements.append(passenger_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # ===== SECTION: INFORMATIONS DU TRAJET =====
    elements.append(Paragraph("INFORMATIONS DU TRAJET", heading_style))
    
    journey_data = [
        ['Lieu de départ :', trip.origin],
        ['Destination :', trip.destination],
        ['Date du départ :', departure.date.strftime('%d/%m/%Y')],
        ['Heure du départ :', departure.time.strftime('%H:%M')],
        ['Bus :', bus.name],
        ['Catégorie :', trip.category.name],
    ]
    
    journey_table = Table(journey_data, colWidths=[2.5*inch, 2.5*inch])
    journey_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    
    elements.append(journey_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # ===== SECTION: PRIX =====
    elements.append(Paragraph("TARIF", heading_style))
    
    price_text = f"{trip.price} FCFA"
    price_data = [
        ['Prix du trajet :', price_text],
    ]
    
    price_table = Table(price_data, colWidths=[2*inch, 3*inch])
    price_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1f5233')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(price_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ===== SECTION: CODE QR =====
    elements.append(Paragraph("CODE QR", heading_style))
    
    # Générer le code QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(f"TICKET_{reservation.id}_{reservation.departure.id}_{reservation.user.id}")
    qr.make(fit=True)
    
    # Convertir le code QR en image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Sauvegarder l'image QR dans un buffer
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Créer une image reportlab à partir du buffer
    qr_image = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
    
    # Créer une table pour centrer le QR code
    qr_data = [[qr_image]]
    qr_table = Table(qr_data, colWidths=[5*inch])
    qr_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(qr_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Texte supplémentaire
    footer_text = "Veuillez présenter ce ticket lors de votre montée dans le bus. Merci de votre confiance!"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    elements.append(Paragraph(footer_text, footer_style))
    
    # Construire le PDF
    doc.build(elements)
    
    # Remettre le curseur au début du buffer
    buffer.seek(0)
    
    return buffer


def get_status_display(status):
    """Retourne le statut formaté"""
    status_dict = {
        'P': 'En attente',
        'C': 'Confirmée',
        'X': 'Annulée',
    }
    return status_dict.get(status, status)


def download_ticket(request, reservation_id):
    """
    Vue pour télécharger le ticket PDF d'une réservation.
    """
    from .models import Reservation
    from django.contrib.auth.decorators import login_required
    
    # Récupérer la réservation et vérifier que l'utilisateur en est propriétaire
    reservation = Reservation.objects.get(id=reservation_id)
    
    if reservation.user != request.user and not request.user.is_staff:
        return FileResponse(status=403)
    
    # Générer le PDF
    pdf_buffer = generate_ticket_pdf(reservation)
    
    # Retourner le fichier
    response = FileResponse(
        pdf_buffer,
        content_type='application/pdf',
        as_attachment=True,
        filename=f"Ticket_Reservation_{reservation.id}.pdf"
    )
    
    return response
