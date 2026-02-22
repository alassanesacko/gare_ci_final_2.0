from django.test import TestCase

from trips.models import Arret, EtapeTrajet, Segment, Trip, Ville


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
