from datetime import timedelta
from decimal import Decimal
from threading import Barrier, Thread

from django.core.exceptions import ValidationError
from django.db import close_old_connections
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from accounts.models import CustomUser
from gareci_admin.models import PolitiqueReservation
from reservations.models import Paiement, Reservation, ReservationStatus, Ticket
from reservations.services import ReservationService
from trips.models import Arret, Bus, Category, Departure, Trip, Ville


class ReservationTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='test123',
            email='testuser@example.com',
        )

        self.ville_depart = Ville.objects.create(nom='Abidjan', code='ABJ')
        self.ville_arrivee = Ville.objects.create(nom='Yamoussoukro', code='YAK')
        self.arret_depart = Arret.objects.create(
            ville=self.ville_depart,
            nom='Gare Abidjan',
            adresse='Plateau',
        )
        self.arret_arrivee = Arret.objects.create(
            ville=self.ville_arrivee,
            nom='Gare Yamoussoukro',
            adresse='Centre',
        )

        self.trip = Trip.objects.create(
            nom='Abidjan -> Yamoussoukro',
            ville_depart=self.ville_depart,
            ville_arrivee=self.ville_arrivee,
            arret_depart=self.arret_depart,
            arret_arrivee=self.arret_arrivee,
            price=Decimal('10000.00'),
            actif=True,
        )

        self.category = Category.objects.create(
            nom='Confort',
            niveau=Category.Niveau.CONFORT,
            prix_multiplicateur=Decimal('1.00'),
        )
        self.bus = Bus.objects.create(
            immatriculation='AB-123-CD',
            modele='Iveco',
            capacite=50,
            categorie=self.category,
        )
        self.departure = Departure.objects.create(
            trip=self.trip,
            bus=self.bus,
            date_depart=timezone.now() + timedelta(days=10),
            date_arrivee_estimee=timezone.now() + timedelta(days=10, hours=4),
            places_disponibles=10,
            actif=True,
        )

        PolitiqueReservation.objects.all().delete()
        self.politique = PolitiqueReservation.objects.create(
            delai_max_avant_depart=90,
            delai_min_avant_depart=2,
            places_max_par_reservation=5,
            reservations_max_par_client=3,
            delai_paiement_minutes=30,
            active=True,
        )

    def _create_ticket(self, user=None, num_seiges=1, prix=Decimal('10000.00')):
        return Ticket.objects.create(
            bus=self.bus,
            user=user or self.user,
            num_seiges=num_seiges,
            prix=prix,
        )

    def _create_reservation(
        self,
        *,
        user=None,
        status=ReservationStatus.EN_ATTENTE,
        nombre_places=1,
        expires_at=None,
        departure=None,
        prix_total=Decimal('10000.00'),
    ):
        return Reservation.objects.create(
            utilisateur=user or self.user,
            depart=departure or self.departure,
            date_voyage=timezone.localdate(),
            statut=status,
            nombre_places=nombre_places,
            prix_total=prix_total,
        )

    # TESTS ReservationService.creer()
    def test_reservation_nominale(self):
        reservation = ReservationService.creer(
            departure_id=self.departure.id,
            utilisateur=self.user,
            nombre_places=2,
        )

        self.assertTrue(Reservation.objects.filter(id=reservation.id).exists())
        self.assertEqual(reservation.statut, ReservationStatus.EN_ATTENTE)
        self.assertEqual(reservation.nombre_places, 2)
        self.assertEqual(reservation.prix_total, self.departure.trip.price * 2)

        self.departure.refresh_from_db()
        self.assertEqual(self.departure.places_disponibles, 8)

        self.assertTrue(reservation.reference)
        self.assertEqual(len(reservation.reference), 12)
        self.assertIsNotNone(reservation.expires_at)

    def test_surbooking(self):
        with self.assertRaises(ValidationError):
            ReservationService.creer(
                departure_id=self.departure.id,
                utilisateur=self.user,
                nombre_places=15,
            )

        self.departure.refresh_from_db()
        self.assertEqual(self.departure.places_disponibles, 10)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_trop_tot(self):
        self.departure.date_depart = timezone.now() + timedelta(days=120)
        self.departure.save(update_fields=['date_depart'])

        expected_opening_date = (timezone.now() + timedelta(days=30)).date()
        with self.assertRaisesMessage(ValidationError, str(expected_opening_date)):
            ReservationService.creer(
                departure_id=self.departure.id,
                utilisateur=self.user,
                nombre_places=1,
            )

        self.assertEqual(Reservation.objects.count(), 0)

    def test_trop_tard(self):
        self.departure.date_depart = timezone.now() + timedelta(hours=1)
        self.departure.save(update_fields=['date_depart'])

        with self.assertRaises(ValidationError):
            ReservationService.creer(
                departure_id=self.departure.id,
                utilisateur=self.user,
                nombre_places=1,
            )

        self.assertEqual(Reservation.objects.count(), 0)

    def test_trop_de_places(self):
        with self.assertRaises(ValidationError):
            ReservationService.creer(
                departure_id=self.departure.id,
                utilisateur=self.user,
                nombre_places=6,
            )

        self.assertEqual(Reservation.objects.count(), 0)

    def test_trop_de_reservations_actives(self):
        self._create_reservation(status=ReservationStatus.CONFIRMEE)
        self._create_reservation(status=ReservationStatus.CONFIRMEE)
        self._create_reservation(status=ReservationStatus.EN_ATTENTE)
        initial_count = Reservation.objects.count()

        with self.assertRaises(ValidationError):
            ReservationService.creer(
                departure_id=self.departure.id,
                utilisateur=self.user,
                nombre_places=1,
            )

        self.assertEqual(Reservation.objects.count(), initial_count)

    def test_atomicite_surbooking_concurrent(self):
        barrier = Barrier(2)
        results = []

        def worker():
            close_old_connections()
            barrier.wait()
            try:
                reservation = ReservationService.creer(
                    departure_id=self.departure.id,
                    utilisateur=self.user,
                    nombre_places=8,
                )
                results.append(('ok', reservation.id))
            except Exception as exc:
                results.append(('err', str(exc)))
            finally:
                close_old_connections()

        t1 = Thread(target=worker)
        t2 = Thread(target=worker)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        success_count = sum(1 for status, _ in results if status == 'ok')
        self.assertEqual(success_count, 1)

        self.departure.refresh_from_db()
        self.assertGreaterEqual(self.departure.places_disponibles, 0)

    # TESTS Paiement simulé
    def test_paiement_reussi(self):
        reservation = self._create_reservation(
            status=ReservationStatus.CONFIRMEE,
            expires_at=timezone.now() + timedelta(hours=1),
            prix_total=Decimal('20000.00'),
            nombre_places=2,
        )
        paiement = Paiement.objects.create(
            reservation=reservation,
            montant=reservation.prix_total,
            statut=Paiement.Statut.EN_ATTENTE,
        )

        self.client.login(username='testuser', password='test123')
        response = self.client.post(
            reverse('reservations:traiter_paiement', args=[reservation.id]),
            {'action': 'payer'},
        )

        paiement.refresh_from_db()
        reservation.refresh_from_db()
        self.assertEqual(paiement.statut, Paiement.Statut.REUSSI)
        self.assertEqual(reservation.statut, ReservationStatus.CONFIRMEE)
        self.assertRedirects(response, reverse('reservations:paiement_succes'))

    def test_paiement_echec(self):
        reservation = self._create_reservation(
            status=ReservationStatus.CONFIRMEE,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        paiement = Paiement.objects.create(
            reservation=reservation,
            montant=reservation.prix_total,
            statut=Paiement.Statut.EN_ATTENTE,
        )

        self.client.login(username='testuser', password='test123')
        response = self.client.post(
            reverse('reservations:traiter_paiement', args=[reservation.id]),
            {'action': 'echouer'},
        )

        paiement.refresh_from_db()
        reservation.refresh_from_db()
        self.assertEqual(paiement.statut, Paiement.Statut.ECHOUE)
        self.assertEqual(reservation.status, ReservationStatus.CONFIRMEE)
        self.assertRedirects(response, reverse('reservations:paiement_echec'))

    def test_paiement_reservation_non_validee(self):
        reservation = self._create_reservation(status=ReservationStatus.EN_ATTENTE)

        self.client.login(username='testuser', password='test123')
        response = self.client.get(reverse('reservations:paiement', args=[reservation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reservations/attente_validation.html')
        self.assertNotContains(response, 'Confirmer le paiement')

    def test_paiement_expire(self):
        reservation = self._create_reservation(
            status=ReservationStatus.CONFIRMEE,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        Paiement.objects.create(
            reservation=reservation,
            montant=reservation.prix_total,
            statut=Paiement.Statut.EN_ATTENTE,
        )

        self.client.login(username='testuser', password='test123')
        response = self.client.post(
            reverse('reservations:traiter_paiement', args=[reservation.id]),
            {'action': 'payer'},
        )

        possible_redirects = [reverse('reservations:paiement_echec')]
        try:
            possible_redirects.append(reverse('reservations:paiement_expire'))
        except NoReverseMatch:
            pass

        self.assertIn(response.url, possible_redirects)
        self.assertEqual(Paiement.objects.filter(statut=Paiement.Statut.REUSSI).count(), 0)

    def test_paiement_autre_utilisateur(self):
        user_a = CustomUser.objects.create_user(
            username='user_a',
            password='test123',
            email='usera@example.com',
        )
        user_b = CustomUser.objects.create_user(
            username='user_b',
            password='test123',
            email='userb@example.com',
        )
        reservation = self._create_reservation(user=user_a, status=ReservationStatus.CONFIRMEE)

        self.client.login(username='user_b', password='test123')
        response = self.client.get(reverse('reservations:paiement', args=[reservation.id]))

        self.assertEqual(response.status_code, 404)

    # TESTS PolitiqueReservation
    def test_get_active_cree_si_absente(self):
        PolitiqueReservation.objects.all().delete()

        politique = PolitiqueReservation.get_active()

        self.assertIsNotNone(politique)
        self.assertEqual(PolitiqueReservation.objects.count(), 1)
        self.assertEqual(politique.delai_max_avant_depart, 90)
        self.assertEqual(
            politique.places_max_par_reservation,
            PolitiqueReservation._meta.get_field('places_max_par_reservation').default,
        )

    def test_get_active_retourne_existante(self):
        PolitiqueReservation.objects.all().delete()
        created = PolitiqueReservation.objects.create(
            delai_max_avant_depart=60,
            active=True,
        )

        first = PolitiqueReservation.get_active()
        second = PolitiqueReservation.get_active()

        self.assertEqual(first.id, created.id)
        self.assertEqual(second.id, created.id)
        self.assertEqual(first.delai_max_avant_depart, 60)

    def test_une_seule_politique_active(self):
        PolitiqueReservation.objects.all().delete()
        first = PolitiqueReservation.objects.create(active=True, delai_max_avant_depart=60)
        second = PolitiqueReservation.objects.create(active=True, delai_max_avant_depart=30)

        active = PolitiqueReservation.get_active()

        self.assertIn(active.id, {first.id, second.id})
        self.assertEqual(active.id, first.id)

    def test_politique_impact_reservation(self):
        self.politique.delai_max_avant_depart = 5
        self.politique.save(update_fields=['delai_max_avant_depart'])

        with self.assertRaises(ValidationError):
            ReservationService.creer(
                departure_id=self.departure.id,
                utilisateur=self.user,
                nombre_places=1,
            )

        self.politique.delai_max_avant_depart = 15
        self.politique.save(update_fields=['delai_max_avant_depart'])

        reservation = ReservationService.creer(
            departure_id=self.departure.id,
            utilisateur=self.user,
            nombre_places=1,
        )
        self.assertTrue(Reservation.objects.filter(id=reservation.id).exists())

    # TESTS Reservation (méthodes du modèle)
    def test_valider(self):
        admin_user = CustomUser.objects.create_user(
            username='admin_user',
            password='test123',
            email='admin@example.com',
            is_staff=True,
        )
        reservation = self._create_reservation(
            status=ReservationStatus.EN_ATTENTE,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

        reservation.valider(admin_user)
        reservation.refresh_from_db()

        self.assertEqual(reservation.status, ReservationStatus.CONFIRMEE)
        self.assertEqual(reservation.validee_par, admin_user)
        self.assertIsNotNone(reservation.validee_at)
        self.assertGreater(reservation.expires_at, timezone.now())

    def test_rejeter(self):
        reservation = self._create_reservation(
            status=ReservationStatus.EN_ATTENTE,
            nombre_places=3,
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        self.departure.places_disponibles = 7
        self.departure.save(update_fields=['places_disponibles'])
        admin_user = CustomUser.objects.create_user(
            username='admin_rejet',
            password='test123',
            is_staff=True,
        )

        reservation.rejeter(admin_user, motif='Bus complet')
        reservation.refresh_from_db()
        self.departure.refresh_from_db()

        self.assertEqual(reservation.statut, ReservationStatus.EN_ATTENTE)
        self.assertEqual(reservation.motif_rejet, 'Bus complet')
        self.assertEqual(self.departure.places_disponibles, 10)

    def test_annuler_confirmee(self):
        reservation = self._create_reservation(
            status=ReservationStatus.CONFIRMEE,
            nombre_places=2,
        )
        self.departure.places_disponibles = 8
        self.departure.save(update_fields=['places_disponibles'])

        reservation.annuler()
        reservation.refresh_from_db()
        self.departure.refresh_from_db()

        self.assertEqual(reservation.status, ReservationStatus.ANNULEE)
        self.assertEqual(self.departure.places_disponibles, 10)

    def test_annuler_en_attente(self):
        reservation = self._create_reservation(
            status=ReservationStatus.EN_ATTENTE,
            nombre_places=2,
        )
        initial_places = self.departure.places_disponibles

        reservation.annuler()
        reservation.refresh_from_db()
        self.departure.refresh_from_db()

        self.assertEqual(reservation.status, ReservationStatus.ANNULEE)
        self.assertEqual(self.departure.places_disponibles, initial_places)

    def test_est_expiree(self):
        reservation_expiree = self._create_reservation(
            status=ReservationStatus.VALIDEE,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        self.assertTrue(reservation_expiree.est_expiree)

        reservation_non_expiree = self._create_reservation(
            status=ReservationStatus.VALIDEE,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.assertFalse(reservation_non_expiree.est_expiree)

        reservation_confirmee = self._create_reservation(
            status=ReservationStatus.CONFIRMEE,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        self.assertFalse(reservation_confirmee.est_expiree)

    def test_reference_unique(self):
        references = set()
        for index in range(50):
            user = CustomUser.objects.create_user(
                username=f'user_ref_{index}',
                password='test123',
                email=f'user_ref_{index}@example.com',
            )
            reservation = self._create_reservation(
                user=user,
                status=ReservationStatus.EN_ATTENTE,
            )
            references.add(reservation.reference)
            self.assertEqual(len(reservation.reference), 12)

        self.assertEqual(len(references), 50)
