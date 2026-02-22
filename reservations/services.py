from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.conf import settings

from trips.models import Departure
from .models import Reservation, ReservationStatus, Ticket
from gareci_admin.models import PolitiqueReservation


class ReservationService:
    @classmethod
    def creer(cls, departure_id, utilisateur, nombre_places):
        """Crée une réservation en respectant la politique.

        Lève ValueError en cas d'invalidation.
        """
        politique = PolitiqueReservation.get_active()

        with transaction.atomic():
            # Verrouiller le départ
            departure = (
                Departure.objects.select_for_update()
                .select_related('trip', 'bus', 'trip__ville_depart', 'trip__ville_arrivee')
                .get(id=departure_id)
            )

            now = timezone.now()
            delta = departure.date_depart - now

            # Vérifier délai max (pas trop tôt)
            max_days = politique.delai_max_avant_depart
            if delta.days > max_days:
                raise ValueError(f"Réservation trop anticipée. Maximum {max_days} jours avant le départ.")

            # Vérifier délai min (pas trop tard)
            min_hours = politique.delai_min_avant_depart
            if delta.total_seconds() < min_hours * 3600:
                raise ValueError(f"Réservation trop proche du départ. Minimum {min_hours} heures avant le départ.")

            # Vérifier places_max_par_reservation
            if nombre_places < 1 or nombre_places > politique.places_max_par_reservation:
                raise ValueError(f"Le nombre de places doit être entre 1 et {politique.places_max_par_reservation}.")

            # Vérifier reservations_max_par_client
            active_statuses = [ReservationStatus.EN_ATTENTE_VALIDATION, ReservationStatus.VALIDEE, ReservationStatus.CONFIRMEE]
            existing_count = Reservation.objects.filter(user=utilisateur, status__in=[s.value for s in active_statuses]).count()
            if existing_count >= politique.reservations_max_par_client:
                raise ValueError("Nombre maximum de réservations atteintes pour ce client.")

            # Vérifier places disponibles
            if departure.places_disponibles < nombre_places:
                raise ValueError("Pas assez de places disponibles pour ce départ.")

            # Calculer prix total: trip.price * nombre_places * category multiplier (si disponible)
            trip = departure.trip
            base_price = Decimal(getattr(trip, 'price', 0) or 0)
            multiplier = Decimal(1)
            if getattr(departure.bus, 'categorie', None) and getattr(departure.bus.categorie, 'prix_multiplicateur', None) is not None:
                multiplier = Decimal(departure.bus.categorie.prix_multiplicateur)
            prix_total = (base_price * Decimal(nombre_places) * multiplier).quantize(Decimal('0.01'))

            # Créer un Ticket associé (pour compatibilité du modèle)
            ticket = Ticket.objects.create(
                bus=departure.bus,
                user=utilisateur,
                num_seiges=nombre_places,
                prix=prix_total,
            )

            # Créer la réservation en attente
            reservation = Reservation.objects.create(
                user=utilisateur,
                departure=departure,
                ticket=ticket,
                status=ReservationStatus.EN_ATTENTE_VALIDATION,
                nombre_places=nombre_places,
                prix_total=prix_total,
                expires_at=now + timezone.timedelta(minutes=politique.delai_paiement_minutes),
            )

            # Bloquer les places (décrémenter)
            departure.places_disponibles = departure.places_disponibles - nombre_places
            departure.save()

            # Notifier les admins
            User = get_user_model()
            admin_emails = list(User.objects.filter(is_staff=True).values_list('email', flat=True))
            if admin_emails:
                try:
                    send_mail(
                        subject=f"Nouvelle réservation #{reservation.id}",
                        message=f"Une nouvelle réservation a été créée par {utilisateur}. Référence: {reservation.reference if hasattr(reservation, 'reference') else reservation.id}.",
                        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
                        recipient_list=admin_emails,
                        fail_silently=True,
                    )
                except Exception:
                    pass

            return reservation

    @classmethod
    def calculer_penalite(cls, reservation):
        """Calcule le montant de la pénalité d'annulation pour une réservation."""
        politique = PolitiqueReservation.get_active()
        pct = Decimal(politique.penalite_annulation_pct) / Decimal(100)
        montant = (Decimal(reservation.prix_total) * pct).quantize(Decimal('0.01'))
        return montant
