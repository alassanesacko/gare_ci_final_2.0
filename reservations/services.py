from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from gareci_admin.models import PolitiqueReservation
from trips.models import Depart

from .models import Reservation, ReservationStatus, Ticket


class ReservationService:
    @staticmethod
    @transaction.atomic
    def creer(depart_id, date_voyage, utilisateur, nombre_places):
        politique = PolitiqueReservation.get_active()
        depart = Depart.objects.select_for_update().get(id=depart_id)
        maintenant = timezone.now()
        datetime_depart = timezone.make_aware(datetime.combine(date_voyage, depart.heure_depart))

        if not depart.actif:
            raise ValidationError("Ce depart n'est plus disponible.")
        if datetime_depart <= maintenant:
            raise ValidationError("Impossible de reserver un depart passe.")

        jours_avant = (date_voyage - maintenant.date()).days
        if jours_avant > politique.delai_max_avant_depart:
            date_ouverture = date_voyage - timedelta(days=politique.delai_max_avant_depart)
            raise ValidationError(
                f"Les reservations pour ce depart ouvrent le {date_ouverture.strftime('%d/%m/%Y')}."
            )

        heures_avant = (datetime_depart - maintenant).total_seconds() / 3600
        if heures_avant < politique.delai_min_avant_depart:
            raise ValidationError(
                f"Les reservations sont fermees {politique.delai_min_avant_depart}h avant le depart."
            )

        if nombre_places > politique.places_max_par_reservation:
            raise ValidationError(f"Maximum {politique.places_max_par_reservation} places par reservation.")

        active_statuses = [
            ReservationStatus.EN_ATTENTE_VALIDATION,
            ReservationStatus.VALIDEE,
            ReservationStatus.CONFIRMEE,
        ]
        reservations_actives = Reservation.objects.filter(
            user=utilisateur,
            status__in=[s.value for s in active_statuses],
        ).count()
        if reservations_actives >= politique.reservations_max_par_client:
            raise ValidationError(
                f"Vous avez deja {politique.reservations_max_par_client} reservations actives."
            )

        places_dispo = depart.places_disponibles_pour(date_voyage)
        if places_dispo < nombre_places:
            raise ValidationError(
                f"Seulement {places_dispo} place(s) disponible(s) pour ce depart ce jour-la."
            )

        prix_total = (Decimal(depart.prix) * Decimal(nombre_places)).quantize(Decimal("0.01"))

        ticket = Ticket.objects.create(
            bus=depart.bus,
            user=utilisateur,
            num_seiges=nombre_places,
            prix=prix_total,
        )

        reservation = Reservation.objects.create(
            depart=depart,
            date_voyage=date_voyage,
            user=utilisateur,
            ticket=ticket,
            nombre_places=nombre_places,
            prix_total=prix_total,
            expires_at=maintenant + timedelta(minutes=politique.delai_paiement_minutes),
        )

        User = get_user_model()
        admin_emails = list(User.objects.filter(is_staff=True).values_list("email", flat=True))
        if admin_emails:
            try:
                send_mail(
                    subject=f"Nouvelle reservation #{reservation.id}",
                    message=(
                        f"Une nouvelle reservation a ete creee par {utilisateur}. "
                        f"Reference: {getattr(reservation, 'reference', reservation.id)}."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, "DEFAULT_FROM_EMAIL") else None,
                    recipient_list=admin_emails,
                    fail_silently=True,
                )
            except Exception:
                pass

        return reservation

    @classmethod
    def calculer_penalite(cls, reservation):
        politique = PolitiqueReservation.get_active()
        datetime_depart = reservation.datetime_depart
        heures_avant = (datetime_depart - timezone.now()).total_seconds() / 3600
        if heures_avant >= politique.annulation_gratuite_heures:
            return Decimal("0")
        return (Decimal(reservation.prix_total) * Decimal(politique.penalite_annulation_pct) / Decimal("100")).quantize(
            Decimal("0.01")
        )
