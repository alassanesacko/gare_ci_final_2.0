# trips/views.py
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from .models import Depart, Trip, Ville


def home(request):
    """Page d'accueil publique (client) avec formulaire de recherche."""
    villes = Ville.objects.order_by("nom")
    today = timezone.localdate()
    # Récupérer les trois premiers départs actifs, triés par heure de départ
    popular_departs = Depart.objects.filter(actif=True).select_related("trip", "trip__ville_depart", "trip__ville_arrivee").order_by("heure_depart")[:3]
    return render(
        request,
        "trips/home.html",
        {
            "villes": villes,
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
    ville_depart_nom  = request.GET.get("ville_depart", "").strip()
    ville_arrivee_nom = request.GET.get("ville_arrivee", "").strip()
    resultats         = []
    date_recherche    = timezone.localdate()

    if ville_depart_nom or ville_arrivee_nom:
        query = Q(actif=True)
        
        if ville_depart_nom:
            query &= Q(trip__arret_depart__ville__nom__icontains=ville_depart_nom)
        
        if ville_arrivee_nom:
            query &= Q(trip__arret_arrivee__ville__nom__icontains=ville_arrivee_nom)
        
        departs = Depart.objects.filter(query).select_related(
            "trip__arret_depart__ville",
            "trip__arret_arrivee__ville",
            "bus__categorie",
        ).order_by("heure_depart")

        for depart in departs:
            places = depart.places_disponibles_pour(date_recherche)
            if places > 0:
                resultats.append({
                    "depart": depart,
                    "places": places,
                    "date":   date_recherche,
                })

    return render(request, "trips/search_results.html", {
        "resultats":        resultats,
        "date_recherche":   date_recherche,
        "date_str":         date_recherche.isoformat(),
        "ville_depart_nom": ville_depart_nom,
        "ville_arrivee_nom": ville_arrivee_nom,
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
