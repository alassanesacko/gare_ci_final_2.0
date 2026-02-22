from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from trips.models import Arret, Bus, Segment, Trip, Ville


class DashboardTripStepsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="admin",
            password="adminpass123",
            is_staff=True,
        )

        self.abj = Ville.objects.create(nom="Abidjan", code="ABJ")
        self.bke = Ville.objects.create(nom="Bouake", code="BKE")
        self.krh = Ville.objects.create(nom="Korhogo", code="KRH")

        self.arret_abj = Arret.objects.create(ville=self.abj, nom="Gare AdjamE", adresse="AdjamE")
        self.arret_bke = Arret.objects.create(ville=self.bke, nom="Gare Bouake", adresse="Bouake")
        self.arret_krh = Arret.objects.create(ville=self.krh, nom="Gare Korhogo", adresse="Korhogo")

        self.seg_abj_bke = Segment.objects.create(
            arret_depart=self.arret_abj,
            arret_arrivee=self.arret_bke,
            distance_km=350,
            duree_minutes=240,
        )
        self.seg_bke_krh = Segment.objects.create(
            arret_depart=self.arret_bke,
            arret_arrivee=self.arret_krh,
            distance_km=250,
            duree_minutes=180,
        )

    def _base_trip_payload(self):
        return {
            "nom": "Abidjan - Korhogo via Bouake",
            "ville_depart": str(self.abj.pk),
            "ville_arrivee": str(self.krh.pk),
            "arret_depart": str(self.arret_abj.pk),
            "arret_arrivee": str(self.arret_krh.pk),
            "price": "6000",
            "actif": "on",
            "etapes-TOTAL_FORMS": "2",
            "etapes-INITIAL_FORMS": "0",
            "etapes-MIN_NUM_FORMS": "0",
            "etapes-MAX_NUM_FORMS": "1000",
        }

    def test_trip_create_with_valid_stopover_steps(self):
        self.client.login(username="admin", password="adminpass123")
        payload = self._base_trip_payload()
        payload.update(
            {
                "etapes-0-ordre": "1",
                "etapes-0-segment": str(self.seg_abj_bke.pk),
                "etapes-1-ordre": "2",
                "etapes-1-segment": str(self.seg_bke_krh.pk),
            }
        )

        response = self.client.post(reverse("dashboard:trip_add"), data=payload)

        self.assertEqual(response.status_code, 302)
        trip = Trip.objects.get(nom="Abidjan - Korhogo via Bouake")
        self.assertEqual(trip.etapetrajet_set.count(), 2)
        self.assertFalse(trip.est_direct)
        self.assertEqual(trip.duree_totale, 420)

    def test_trip_create_rejects_non_contiguous_steps(self):
        self.client.login(username="admin", password="adminpass123")
        payload = self._base_trip_payload()
        payload.update(
            {
                "etapes-0-ordre": "1",
                "etapes-0-segment": str(self.seg_bke_krh.pk),
                "etapes-1-ordre": "2",
                "etapes-1-segment": str(self.seg_abj_bke.pk),
            }
        )

        response = self.client.post(reverse("dashboard:trip_add"), data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Trip.objects.count(), 0)
        self.assertContains(response, "Les segments ne sont pas continus")


class DashboardReferenceDataViewsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="admin",
            password="adminpass123",
            is_staff=True,
        )

    def test_staff_can_access_new_reference_pages(self):
        self.client.login(username="admin", password="adminpass123")

        self.assertEqual(self.client.get(reverse("dashboard:ville_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("dashboard:arret_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("dashboard:segment_list")).status_code, 200)


class DashboardDepartureFormTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="admin",
            password="adminpass123",
            is_staff=True,
        )

        self.ville = Ville.objects.create(nom="Abidjan", code="ABJ")
        self.arret_depart = Arret.objects.create(ville=self.ville, nom="Gare A", adresse="A")
        self.arret_arrivee = Arret.objects.create(ville=self.ville, nom="Gare B", adresse="B")
        self.trip = Trip.objects.create(
            nom="Abidjan intra",
            ville_depart=self.ville,
            ville_arrivee=self.ville,
            arret_depart=self.arret_depart,
            arret_arrivee=self.arret_arrivee,
            price=1000,
        )
        self.bus = Bus.objects.create(immatriculation="AB-123-CD", modele="Test", capacite=50)

    def test_departure_form_uses_datetime_local_inputs(self):
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(reverse("dashboard:departure_add"))
        self.assertContains(response, 'name="date_depart"', html=False)
        self.assertContains(response, 'name="date_arrivee_estimee"', html=False)
        self.assertContains(response, 'type="datetime-local"', count=2, html=False)

    def test_departure_form_rejects_places_above_bus_capacity(self):
        self.client.login(username="admin", password="adminpass123")
        now = timezone.localtime(timezone.now()).replace(second=0, microsecond=0)
        arrival = now + timedelta(hours=3)
        payload = {
            "trip": str(self.trip.pk),
            "bus": str(self.bus.pk),
            "date_depart": now.strftime("%Y-%m-%dT%H:%M"),
            "date_arrivee_estimee": arrival.strftime("%Y-%m-%dT%H:%M"),
            "places_disponibles": "80",
            "actif": "on",
        }

        response = self.client.post(reverse("dashboard:departure_add"), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ne peut pas depasser la capacite du bus", html=False)
