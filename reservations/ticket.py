from io import BytesIO
import base64

import qrcode


def _build_qr_base64(payload: str) -> str:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def get_ticket_context(reservation):
    """Retourne le contexte pour afficher le billet."""
    depart = reservation.depart
    trip = depart.trip
    bus = depart.bus
    utilisateur = reservation.utilisateur

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

    return {
        "reservation": reservation,
        "reference": reference,
        "depart": depart,
        "trip": trip,
        "bus": bus,
        "utilisateur": utilisateur,
        "type_trajet": type_trajet,
        "escales_villes": escales_villes,
        "qr_b64": qr_b64,
    }
