def get_tickets_context(reservation):
    """
    Étend get_ticket_context() existant pour les billets multiples.
    Retourne le même contexte + la liste 'billets'
    avec 1 entrée par place réservée.

    Chaque billet a :
    - numero    : position dans la liste (1, 2, 3...)
    - total     : nombre total de billets (= nombre_places)
    - siege     : numéro de siège individuel
    - reference : REF_RESERVATION-N (ex: KX9A2B7C1D3F-1)
    - qr_b64    : QR code propre à ce billet
    """
    contexte = get_ticket_context(reservation)
    billets = []
    # Assign seats using ReservationService.attribuer_sieges if available
    try:
        from .services import ReservationService
        sieges = ReservationService.attribuer_sieges(reservation)
    except Exception:
        sieges = list(range(1, reservation.nombre_places + 1))
    for idx, siege in enumerate(sieges, start=1):
        ref_billet = f"{reservation.reference}-{siege}"
        billets.append({
            'numero':    idx,
            'total':     reservation.nombre_places,
            'siege':     siege,
            'reference': ref_billet,
            'qr_b64':    _build_qr_base64(ref_billet),
        })
    contexte['billets'] = billets
    # Ajoute la distance totale du trajet (en km)
    try:
        etapes = list(reservation.depart.trip.etapetrajet_set.all())
        distance = sum(etape.segment.distance_km for etape in etapes)
    except Exception:
        distance = None
    contexte['distance_km'] = distance
    return contexte
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
