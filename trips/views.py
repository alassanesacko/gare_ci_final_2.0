# trips/views.py
from datetime import datetime

from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from .models import Depart, Trip, Ville


def home(request):
    """Page d'accueil publique (client)."""
    villes = Ville.objects.order_by("nom")
    popular_trips = (
        Trip.objects.filter(actif=True)
        .select_related("ville_depart", "ville_arrivee")
        .annotate(reservations_count=Count("departs__reservations"))
        .order_by("-reservations_count", "price")[:6]
    )
    return render(
        request,
        "trips/home.html",
        {
            "villes": villes,
            "popular_trips": popular_trips,
            "active_tab": "home",
        },
    )


def search_results(request):
    ville_depart_query = (request.GET.get("ville_depart") or "").strip()
    ville_arrivee_query = (request.GET.get("ville_arrivee") or "").strip()
    date_str = (request.GET.get("date") or "").strip()
    resultats = []
    try:
        date_recherche = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else timezone.localdate()
    except ValueError:
        date_recherche = timezone.localdate()
    date_str = date_recherche.isoformat()

    departs = Depart.objects.filter(actif=True)
    if ville_depart_query:
        departs = departs.filter(trip__arret_depart__ville__nom__icontains=ville_depart_query)
    if ville_arrivee_query:
        departs = departs.filter(trip__arret_arrivee__ville__nom__icontains=ville_arrivee_query)

    departs = (
        departs.select_related(
            "trip__arret_depart__ville",
            "trip__arret_arrivee__ville",
            "bus__categorie",
        )
        .prefetch_related("trip__etapetrajet_set__segment__arret_arrivee__ville")
        .order_by("heure_depart")
    )

    for depart in departs:
        places = depart.places_disponibles_pour(date_recherche)
        if places > 0:
            resultats.append(
                {
                    "depart": depart,
                    "places": places,
                }
            )

    context = {
        "resultats": resultats,
        "date_recherche": date_recherche,
        "date_str": date_str,
        "ville_depart_query": ville_depart_query,
        "ville_arrivee_query": ville_arrivee_query,
        "villes": Ville.objects.all().order_by("nom"),
        "nb_resultats": len(resultats),
    }
    return render(request, "trips/search_results.html", context)


def about(request):
    """Page A propos publique."""
    return render(request, "about.html", {"active_tab": "about"})


def cgv(request):
    """Page Conditions generales de vente."""
    return render(request, "cgv.html", {"active_tab": "cgv"})
