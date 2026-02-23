from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from trips.models import Depart

from .forms import ReservationForm
from .models import ContactMessage, Paiement, Reservation, ReservationStatus
from .services import ReservationService
from .ticket import generate_ticket_pdf


@login_required
def reservation_list(request):
    statut = request.GET.get("statut", "").strip().upper()
    reservations = Reservation.objects.filter(user=request.user).select_related(
        "depart",
        "depart__trip",
        "depart__bus",
    )
    allowed_filters = {
        ReservationStatus.CONFIRMEE,
        ReservationStatus.EN_ATTENTE_VALIDATION,
        ReservationStatus.ANNULEE,
    }
    if statut in allowed_filters:
        reservations = reservations.filter(status=statut)

    return render(
        request,
        "reservations/reservation_list.html",
        {
            "reservations": reservations.order_by("-booked_at"),
            "active_tab": "reservation",
            "current_statut": statut,
        },
    )


@login_required
def reserve(request, depart_id, date_str):
    depart = get_object_or_404(
        Depart.objects.select_related(
            "trip",
            "trip__arret_depart__ville",
            "trip__arret_arrivee__ville",
            "bus",
            "bus__categorie",
        ).prefetch_related("trip__etapetrajet_set__segment__arret_arrivee__ville"),
        id=depart_id,
        actif=True,
    )

    try:
        date_voyage = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as exc:
        raise Http404 from exc

    places_dispo = depart.places_disponibles_pour(date_voyage)

    if request.method == "POST":
        form = ReservationForm(request.POST, places_disponibles=places_dispo)
        if form.is_valid():
            try:
                reservation = ReservationService.creer(
                    depart_id=depart.id,
                    date_voyage=date_voyage,
                    utilisateur=request.user,
                    nombre_places=form.cleaned_data["nombre_places"],
                )
                return redirect("reservations:attente_validation", reservation_id=reservation.id)
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))
    else:
        form = ReservationForm(places_disponibles=places_dispo)

    etapes = list(depart.trip.etapetrajet_set.all())
    if len(etapes) <= 1:
        type_trajet = "Direct"
        escales = []
    else:
        escales = []
        for etape in etapes[:-1]:
            ville_nom = etape.segment.arret_arrivee.ville.nom
            if ville_nom not in escales:
                escales.append(ville_nom)
        type_trajet = "Escale"

    return render(
        request,
        "reservations/reserve.html",
        {
            "depart": depart,
            "date_voyage": date_voyage,
            "places_dispo": places_dispo,
            "form": form,
            "type_trajet": type_trajet,
            "escales": escales,
        },
    )


@login_required
def attente_validation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    return render(request, "reservations/attente_validation.html", {"reservation": reservation})


@login_required
@require_POST
def annuler_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    if reservation.status == ReservationStatus.CONFIRMEE:
        reservation.annuler()
    statut = request.GET.get("statut", "").strip()
    redirect_url = "reservations:list"
    if statut:
        return redirect(f"{redirect_url}?statut={statut}")
    return redirect(redirect_url)


@login_required
def message_list(request):
    user_messages = ContactMessage.objects.filter(email=request.user.email).order_by("-submitted_at")
    return render(
        request,
        "reservations/message_list.html",
        {"messages": user_messages, "active_tab": "message"},
    )


@login_required
@require_POST
def delete_message(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk, email=request.user.email)
    msg.delete()
    return redirect("reservations:messages")


@login_required
def telecharger_billet(request, pk):
    reservation = get_object_or_404(Reservation.objects.select_related("user"), pk=pk)

    if reservation.user != request.user:
        return HttpResponse(status=403)

    if reservation.status != ReservationStatus.CONFIRMEE:
        return HttpResponse(status=400)

    pdf_buffer = generate_ticket_pdf(reservation)
    filename_ref = reservation.reference or f"RES-{reservation.id}"
    response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="billet_{filename_ref}.pdf"'
    return response


@login_required
def paiement(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

    if reservation.status == ReservationStatus.EN_ATTENTE_VALIDATION:
        return render(request, "reservations/attente_validation.html", {"reservation": reservation})

    if reservation.status == ReservationStatus.REJETEE:
        return render(request, "reservations/reservation_rejetee.html", {"reservation": reservation})

    if reservation.status == ReservationStatus.EXPIREE:
        return render(request, "reservations/paiement_expire.html", {"reservation": reservation})

    if reservation.status == ReservationStatus.VALIDEE:
        paiement_obj, _ = Paiement.objects.get_or_create(
            reservation=reservation,
            defaults={"montant": reservation.prix_total},
        )
        return render(
            request,
            "reservations/paiement.html",
            {"reservation": reservation, "paiement": paiement_obj},
        )

    return redirect("reservations:list")


@login_required
@require_POST
def traiter_paiement(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    try:
        paiement_obj = reservation.paiement
    except Paiement.DoesNotExist:
        return HttpResponse(status=404)

    if getattr(reservation, "est_expiree", False):
        return redirect("reservations:paiement_echec")

    action = request.POST.get("action")
    if action == "payer":
        paiement_obj.statut = Paiement.Statut.REUSSI
        paiement_obj.save()
        reservation.confirmer()
        return redirect("reservations:paiement_succes")
    if action == "echouer":
        paiement_obj.statut = Paiement.Statut.ECHOUE
        paiement_obj.save()
        return redirect("reservations:paiement_echec")
    return HttpResponse(status=400)


def paiement_succes(request):
    return render(request, "reservations/paiement_succes.html")


def paiement_echec(request):
    return render(request, "reservations/paiement_echec.html")


def contact(request):
    if request.user.is_authenticated:
        default_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        default_email = request.user.email or ""
    else:
        default_name = ""
        default_email = ""

    form_data = {
        "nom_complet": default_name,
        "email": default_email,
        "sujet": "",
        "message": "",
    }
    errors = {}

    if request.method == "POST":
        form_data = {
            "nom_complet": request.POST.get("nom_complet", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "sujet": request.POST.get("sujet", "").strip(),
            "message": request.POST.get("message", "").strip(),
        }

        if not form_data["nom_complet"]:
            errors["nom_complet"] = "Le nom complet est obligatoire."
        if not form_data["email"]:
            errors["email"] = "L'email est obligatoire."
        if not form_data["sujet"]:
            errors["sujet"] = "Le sujet est obligatoire."
        if not form_data["message"]:
            errors["message"] = "Le message est obligatoire."

        if not errors:
            contact_msg = ContactMessage.objects.create(
                name=form_data["nom_complet"],
                email=form_data["email"],
                message=f"Sujet: {form_data['sujet']}\n\n{form_data['message']}",
            )

            admin_email = getattr(settings, "CONTACT_ADMIN_EMAIL", None)
            if not admin_email:
                admins = getattr(settings, "ADMINS", ())
                admin_email = admins[0][1] if admins else getattr(settings, "DEFAULT_FROM_EMAIL", None)

            if admin_email:
                send_mail(
                    subject=f"[Contact GareCI] {form_data['sujet']}",
                    message=(
                        f"Nouveau message de contact\n\n"
                        f"Nom: {contact_msg.name}\n"
                        f"Email: {contact_msg.email}\n"
                        f"Sujet: {form_data['sujet']}\n\n"
                        f"Message:\n{form_data['message']}"
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[admin_email],
                    fail_silently=True,
                )

            messages.success(
                request,
                "Votre message a bien ete envoye, nous vous repondrons sous 24h",
            )
            return redirect("reservations:contact")

    return render(
        request,
        "reservations/contact.html",
        {
            "form_data": form_data,
            "errors": errors,
            "active_tab": "contact",
        },
    )
