from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
import qrcode
import base64
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .models import Reservation, ReservationStatus


def generate_ticket_pdf(reservation):
    """Génère un PDF de ticket pour une réservation en utilisant WeasyPrint.

    Retourne un BytesIO contenant le PDF.
    """
    # Préparer le QR code en base64 pour l'embed dans le HTML
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr_data = reservation.reference if getattr(reservation, 'reference', None) else f"RES-{reservation.id}"
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_b64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

    # Contexte pour le template
    departure = reservation.departure
    trip = getattr(departure, 'trip', None)
    bus = getattr(departure, 'bus', None)
    user = reservation.user

    context = {
        'company_name': 'GareCI',
        'reservation': reservation,
        'user': user,
        'trip': trip,
        'departure': departure,
        'bus': bus,
        'qr_b64': qr_b64,
        'qr_data': qr_data,
    }

    html_string = render_to_string('reservations/ticket_pdf.html', context)

    pdf_io = BytesIO()
    try:
        from weasyprint import HTML  # Import paresseux: évite le crash au démarrage Django
        HTML(string=html_string).write_pdf(target=pdf_io)
        pdf_io.seek(0)
        return pdf_io
    except Exception:
        # Fallback PDF minimal si les libs système WeasyPrint ne sont pas installées
        return _generate_ticket_pdf_fallback(reservation, qr_data)


def _generate_ticket_pdf_fallback(reservation, qr_data):
    pdf_io = BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=A4)
    width, height = A4

    y = height - 60
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Ticket de voyage - GareCI")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Reservation: {reservation.reference or reservation.id}")
    y -= 20
    c.drawString(50, y, f"Client: {reservation.user}")
    y -= 20
    c.drawString(50, y, f"Statut: {get_status_display(reservation.status)}")
    y -= 20
    c.drawString(50, y, f"Depart: {reservation.departure.date_depart}")
    y -= 20
    c.drawString(50, y, f"QR: {qr_data}")

    c.showPage()
    c.save()
    pdf_io.seek(0)
    return pdf_io


def get_status_display(status):
    """Retourne le statut formaté"""
    # Compatible avec l'ancien format ou le nouveau TextChoices
    if hasattr(status, 'label'):
        return status.label
    mapping = {
        'EN_ATTENTE_VALIDATION': 'En attente',
        'VALIDEE': 'Validée',
        'CONFIRMEE': 'Confirmée',
        'REJETEE': 'Rejetée',
        'ANNULEE': 'Annulée',
        'EXPIREE': 'Expirée',
        'P': 'En attente',
        'C': 'Confirmée',
        'X': 'Annulée',
    }
    return mapping.get(status, status)


from django.contrib.auth.decorators import login_required


@login_required
def download_ticket(request, reservation_id):
    """Vue pour télécharger le ticket PDF d'une réservation.

    Vérifie que la réservation est confirmée et que l'utilisateur est le propriétaire.
    Retourne HttpResponse contenant le PDF.
    """
    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return HttpResponse(status=404)

    # Vérifier propriétaire
    if reservation.user != request.user and not request.user.is_staff:
        return HttpResponse(status=403)

    # Vérifier statut CONFIRMEE
    if reservation.status != ReservationStatus.CONFIRMEE and str(reservation.status) != 'CONFIRMEE':
        return HttpResponse(status=400)

    pdf_io = generate_ticket_pdf(reservation)
    response = HttpResponse(pdf_io.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=Ticket_Reservation_{reservation.id}.pdf'
    return response
