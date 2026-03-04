from django.template.loader import render_to_string
from weasyprint import HTML
from io import BytesIO

def generer_billet_pdf(reservation):
    from .ticket import get_tickets_context
    context = get_tickets_context(reservation)
    html_string = render_to_string("reservations/billet.html", context)
    pdf_file = BytesIO()
    HTML(string=html_string, base_url=None).write_pdf(pdf_file)
    return pdf_file.getvalue()
