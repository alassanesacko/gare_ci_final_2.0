from datetime import time
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from trips.models import Arret, Bus, Category, Depart, EtapeTrajet, Segment, Trip, Ville


class TripUseCaseTests(TestCase):
    def setUp(self):
        # Villes
        self.abidjan = Ville.objects.create(nom="Abidjan", code="ABJ")
        self.bouake = Ville.objects.create(nom="Bouake", code="BKE")
        self.korhogo = Ville.objects.create(nom="Korhogo", code="KRH")

        # Arrets
        self.gare_abidjan = Arret.objects.create(
            ville=self.abidjan,
            nom="Gare d'Adjame",
            adresse="Adjame, Abidjan",
        )
        self.gare_bouake = Arret.objects.create(
            ville=self.bouake,
            nom="Gare de Bouake",
            adresse="Centre-ville, Bouake",
        )
        self.gare_korhogo = Arret.objects.create(
            ville=self.korhogo,
            nom="Gare de Korhogo",
            adresse="Korhogo centre",
        )

        # Segments reutilisables
        self.seg_abj_bke = Segment.objects.create(
            arret_depart=self.gare_abidjan,
            arret_arrivee=self.gare_bouake,
            distance_km=350,
            duree_minutes=240,
        )
        self.seg_bke_krh = Segment.objects.create(
            arret_depart=self.gare_bouake,
            arret_arrivee=self.gare_korhogo,
            distance_km=250,
            duree_minutes=180,
        )

    def test_trajet_direct_abidjan_bouake(self):
        trip_direct = Trip.objects.create(
            nom="Abidjan - Bouake Express",
            ville_depart=self.abidjan,
            ville_arrivee=self.bouake,
            arret_depart=self.gare_abidjan,
            arret_arrivee=self.gare_bouake,
            price=3500,
        )
        EtapeTrajet.objects.create(trip=trip_direct, segment=self.seg_abj_bke, ordre=1)

        self.assertTrue(trip_direct.est_direct)
        self.assertEqual(trip_direct.duree_totale, 240)
        self.assertEqual(trip_direct.etapetrajet_set.count(), 1)

    def test_trajet_avec_escale_abidjan_korhogo_via_bouake(self):
        trip_escale = Trip.objects.create(
            nom="Abidjan - Korhogo via Bouake",
            ville_depart=self.abidjan,
            ville_arrivee=self.korhogo,
            arret_depart=self.gare_abidjan,
            arret_arrivee=self.gare_korhogo,
            price=6000,
        )
        EtapeTrajet.objects.create(trip=trip_escale, segment=self.seg_abj_bke, ordre=1)
        EtapeTrajet.objects.create(trip=trip_escale, segment=self.seg_bke_krh, ordre=2)

        self.assertFalse(trip_escale.est_direct)
        self.assertEqual(trip_escale.duree_totale, 420)
        self.assertEqual(
            list(trip_escale.etapetrajet_set.values_list("ordre", flat=True)),
            [1, 2],
        )


class SearchResultsViaEscaleTests(TestCase):
    def setUp(self):
        self.abidjan = Ville.objects.create(nom="Abidjan", code="ABJ")
        self.toumodi = Ville.objects.create(nom="Toumodi", code="TMD")
        self.yamoussoukro = Ville.objects.create(nom="Yamoussoukro", code="YAK")

        self.gare_abidjan = Arret.objects.create(
            ville=self.abidjan,
            nom="Gare Abidjan",
            adresse="Adjame",
        )
        self.gare_toumodi = Arret.objects.create(
            ville=self.toumodi,
            nom="Gare Toumodi",
            adresse="Centre",
        )
        self.gare_yamoussoukro = Arret.objects.create(
            ville=self.yamoussoukro,
            nom="Gare Yamoussoukro",
            adresse="Centre",
        )

        segment_abj_tmd = Segment.objects.create(
            arret_depart=self.gare_abidjan,
            arret_arrivee=self.gare_toumodi,
            distance_km=190,
            duree_minutes=120,
        )
        segment_tmd_yak = Segment.objects.create(
            arret_depart=self.gare_toumodi,
            arret_arrivee=self.gare_yamoussoukro,
            distance_km=40,
            duree_minutes=30,
        )

        trip = Trip.objects.create(
            nom="Abidjan - Yamoussoukro via Toumodi",
            ville_depart=self.abidjan,
            ville_arrivee=self.yamoussoukro,
            arret_depart=self.gare_abidjan,
            arret_arrivee=self.gare_yamoussoukro,
            price=Decimal("6000.00"),
            actif=True,
        )
        EtapeTrajet.objects.create(trip=trip, segment=segment_abj_tmd, ordre=1)
        EtapeTrajet.objects.create(trip=trip, segment=segment_tmd_yak, ordre=2)

        categorie = Category.objects.create(nom="Standard")
        bus = Bus.objects.create(
            immatriculation="AB-001-CI",
            modele="Toyota",
            capacite=50,
            categorie=categorie,
        )
        Depart.objects.create(
            trip=trip,
            bus=bus,
            heure_depart=time(8, 0),
            heure_arrivee=time(12, 0),
            prix=Decimal("6000.00"),
            actif=True,
        )
        Depart.objects.create(
            trip=trip,
            bus=bus,
            heure_depart=time(9, 30),
            heure_arrivee=time(13, 30),
            prix=Decimal("6500.00"),
            actif=True,
        )

    def test_search_by_stopover_city_returns_trip(self):
        response = self.client.get(
            reverse("trips:search_results"),
            {"ville_depart": "Abidjan", "ville_arrivee": "Toumodi"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["resultats"]), 2)
        self.assertContains(response, "Abidjan -> Yamoussoukro")
        self.assertContains(response, "1 escale(s)")
        self.assertContains(response, "(Toumodi)")
        self.assertNotContains(response, "Toumodi,")

    def test_search_by_departure_time_filters_results(self):
        response = self.client.get(
            reverse("trips:search_results"),
            {
                "ville_depart": "Abidjan",
                "ville_arrivee": "Toumodi",
                "heure_depart": "09:30",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["resultats"]), 1)
        self.assertContains(response, "09:30")
        self.assertNotContains(response, "08:00")
