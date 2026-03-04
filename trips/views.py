# trips/views.py
import json
from datetime import datetime

from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from .models import Depart, Trip, Ville


def home(request):
    """Page d'accueil publique (client) avec formulaire de recherche."""
    villes = Ville.objects.order_by("nom")
    villes_json = json.dumps(list(villes.values("id", "nom")))
    today = timezone.localdate()
    # Récupérer les trois premiers départs actifs, triés par heure de départ
    popular_departs = Depart.objects.filter(actif=True).select_related("trip", "trip__ville_depart", "trip__ville_arrivee").order_by("heure_depart")[:3]
    return render(
        request,
        "trips/home.html",
        {
            "villes": villes,
            "villes_json": villes_json,
            "today": today,
            "active_tab": "home",
            "popular_trips": [
                {
                    "ville_depart": depart.trip.ville_depart,
                    "ville_arrivee": depart.trip.ville_arrivee,
                    "price": depart.prix,
                }
                for depart in popular_departs
            ],
        },
    )


def search_results(request):
    ville_depart_raw = request.GET.get("ville_depart", "").strip()
    ville_arrivee_raw = request.GET.get("ville_arrivee", "").strip()
    heure_depart_str = request.GET.get("heure_depart", "").strip()
    nb_passagers_raw = request.GET.get("nb_passagers", "").strip()
    type_voyage = request.GET.get("type_voyage", "aller_simple").strip() or "aller_simple"
    date_aller_str = request.GET.get("date", "").strip()
    date_retour_str = request.GET.get("date_retour", "").strip()

    resultats = []
    date_recherche = timezone.localdate()
    ville_depart_nom = ville_depart_raw
    ville_arrivee_nom = ville_arrivee_raw

    try:
        nb_passagers = max(1, int(nb_passagers_raw or "1"))
    except ValueError:
        nb_passagers = 1

    heure_depart = None
    if heure_depart_str:
        try:
            heure_depart = datetime.strptime(heure_depart_str, "%H:%M").time()
        except ValueError:
            heure_depart = None

    if date_aller_str:
        try:
            date_recherche = datetime.strptime(date_aller_str, "%Y-%m-%d").date()
        except ValueError:
            date_recherche = timezone.localdate()

    ville_depart_id = None
    ville_arrivee_id = None

    if ville_depart_raw.isdigit():
        ville_depart_id = int(ville_depart_raw)
        ville_depart_obj = Ville.objects.filter(pk=ville_depart_id).first()
        if ville_depart_obj:
            ville_depart_nom = ville_depart_obj.nom

    if ville_arrivee_raw.isdigit():
        ville_arrivee_id = int(ville_arrivee_raw)
        ville_arrivee_obj = Ville.objects.filter(pk=ville_arrivee_id).first()
        if ville_arrivee_obj:
            ville_arrivee_nom = ville_arrivee_obj.nom

    if ville_depart_raw or ville_arrivee_raw:
        query = Q(actif=True)

        if ville_depart_id is not None:
            query &= Q(trip__arret_depart__ville_id=ville_depart_id)
        elif ville_depart_nom:
            query &= Q(trip__arret_depart__ville__nom__icontains=ville_depart_nom)

        if ville_arrivee_id is not None:
            query &= (
                Q(trip__arret_arrivee__ville_id=ville_arrivee_id)
                | Q(trip__etapetrajet__segment__arret_arrivee__ville_id=ville_arrivee_id)
            )
        elif ville_arrivee_nom:
            query &= (
                Q(trip__arret_arrivee__ville__nom__icontains=ville_arrivee_nom)
                | Q(trip__etapetrajet__segment__arret_arrivee__ville__nom__icontains=ville_arrivee_nom)
            )

        if heure_depart:
            query &= Q(heure_depart=heure_depart)

        departs = Depart.objects.filter(query).select_related(
            "trip__arret_depart__ville",
            "trip__arret_arrivee__ville",
            "bus__categorie",
        ).prefetch_related(
            "trip__etapetrajet_set__segment__arret_arrivee__ville",
        ).distinct().order_by("heure_depart")

        for depart in departs:
            places = depart.places_disponibles_pour(date_recherche)
            if places >= nb_passagers:
                escales = []
                escales_seen = set()
                ville_finale = depart.trip.arret_arrivee.ville.nom
                for etape in depart.trip.etapetrajet_set.all():
                    ville_etape = etape.segment.arret_arrivee.ville.nom
                    if ville_etape == ville_finale or ville_etape in escales_seen:
                        continue
                    escales_seen.add(ville_etape)
                    escales.append(ville_etape)

                resultats.append({
                    "depart": depart,
                    "places": places,
                    "date":   date_recherche,
                    "escales": escales,
                    "escales_str": ", ".join(escales),
                })

    return render(request, "trips/search_results.html", {
        "resultats":        resultats,
        "date_recherche":   date_recherche,
        "date_str":         date_recherche.isoformat(),
        "ville_depart_nom": ville_depart_nom,
        "ville_arrivee_nom": ville_arrivee_nom,
        "nb_passagers":     nb_passagers,
        "type_voyage":      type_voyage,
        "date_retour_str":  date_retour_str,
        "heure_depart_str": heure_depart_str,
        "villes":           Ville.objects.all().order_by("nom"),
        "nb_resultats":     len(resultats),
        "today":            timezone.localdate(),
    })


def about(request):
    """Page A propos publique."""
    return render(request, "about.html", {"active_tab": "about"})


def cgv(request):
    """Page Conditions generales de vente."""
    return render(request, "cgv.html", {"active_tab": "cgv"})
