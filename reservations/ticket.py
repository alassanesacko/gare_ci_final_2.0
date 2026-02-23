from io import BytesIO
import base64

import qrcode
from django.template.loader import render_to_string


def _build_qr_base64(payload: str) -> str:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def generate_ticket_pdf(reservation):
    """Genere le billet PDF WeasyPrint pour une reservation confirmee."""
    depart = reservation.depart
    trip = depart.trip
    bus = depart.bus
    user = reservation.user

    etapes = list(trip.etapetrajet_set.all())
    if len(etapes) <= 1:
        type_trajet = "Direct"
        escales_villes = ""
    else:
        escales = []
        for etape in etapes[:-1]:
            nom = etape.segment.arret_arrivee.ville.nom
            if nom not in escales:
                escales.append(nom)
        type_trajet = "Via " + ", ".join(escales) if escales else "Via"
        escales_villes = ", ".join(escales)

    reference = reservation.reference or f"RES-{reservation.id}"
    qr_b64 = _build_qr_base64(reference)

    context = {
        "reservation": reservation,
        "reference": reference,
        "depart": depart,
        "trip": trip,
        "bus": bus,
        "user": user,
        "type_trajet": type_trajet,
        "escales_villes": escales_villes,
        "qr_b64": qr_b64,
    }

    html = render_to_string("reservations/ticket_pdf.html", context)
    pdf_io = BytesIO()
    from weasyprint import HTML

    HTML(string=html).write_pdf(target=pdf_io)
    pdf_io.seek(0)
    return pdf_io
