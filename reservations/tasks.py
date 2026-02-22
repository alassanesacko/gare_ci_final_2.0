from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Reservation, ReservationStatus


@shared_task
def expirer_reservations():
    now = timezone.now()
    reservation_ids = list(
        Reservation.objects.filter(
            status=ReservationStatus.VALIDEE,
            expires_at__lt=now,
        ).values_list('id', flat=True)
    )

    expirees = 0
    for reservation_id in reservation_ids:
        with transaction.atomic():
            reservation = (
                Reservation.objects.select_for_update()
                .select_related('departure')
                .filter(id=reservation_id)
                .first()
            )
            if not reservation:
                continue
            if reservation.status != ReservationStatus.VALIDEE:
                continue
            if not reservation.expires_at or reservation.expires_at >= now:
                continue

            reservation.departure.places_disponibles = F('places_disponibles') + reservation.nombre_places
            reservation.departure.save(update_fields=['places_disponibles'])

            reservation.status = ReservationStatus.EXPIREE
            reservation.save(update_fields=['status'])
            expirees += 1

    return expirees


@shared_task
def envoyer_rappels_voyage():
    demain = timezone.localdate() + timedelta(days=1)

    reservations = (
        Reservation.objects.select_related('user', 'departure', 'departure__trip')
        .filter(
            status=ReservationStatus.CONFIRMEE,
            departure__date_depart__date=demain,
        )
        .exclude(user__email='')
    )

    rappels_envoyes = 0
    for reservation in reservations:
        depart = timezone.localtime(reservation.departure.date_depart)
        trajet = reservation.departure.trip.nom
        send_mail(
            subject='Rappel de voyage - GareCI',
            message=(
                f"Bonjour {reservation.user.get_full_name() or reservation.user.username},\n\n"
                f"Ceci est un rappel pour votre voyage '{trajet}' le {depart.strftime('%d/%m/%Y à %H:%M')}.\n"
                f"Référence de réservation: {reservation.reference}.\n\n"
                'Bon voyage avec GareCI.'
            ),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[reservation.user.email],
            fail_silently=True,
        )
        rappels_envoyes += 1

    return rappels_envoyes
