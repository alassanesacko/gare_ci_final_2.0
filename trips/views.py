# trips/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Departure
from .forms import TripSearchForm
from reservations.forms import ContactForm  # form de contact défini dans reservations
from django.db.models import Q


def home(request):
    """
    Page d'accueil publique. Affiche un formulaire de recherche et les départs actifs.
    Gère aussi l'envoi du formulaire de contact (section Contact).
    """
    search_form = TripSearchForm(request.GET or None)
    contact_form = ContactForm()
    if request.method == 'POST':
        # Traitement du formulaire de contact (nom, email, message)
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            contact_form.save()
            return redirect('trips:home')
    # Liste des départs actifs
    departures = Departure.objects.filter(actif=True)
    return render(request, 'home.html', {
        'search_form': search_form,
        'contact_form': contact_form,
        'departures': departures,
        'active_tab': 'home'
    })

def search_results(request):
    """
    Affiche les résultats de la recherche de trajets (basé sur GET).
    Filtre les départs actifs selon origine, destination et date.
    Si aucun filtre n'est renseigné, affiche tous les départs actifs (même logique que la page d'accueil).
    """
    origin = request.GET.get('origin', '').strip()
    destination = request.GET.get('destination', '').strip()
    date = request.GET.get('date', '').strip()
    results = Departure.objects.filter(actif=True)
    if origin and destination:
        results = results.filter(
            Q(trip__ville_depart__nom__icontains=origin)
            & Q(trip__ville_arrivee__nom__icontains=destination)
        )
    elif origin:
        results = results.filter(trip__ville_depart__nom__icontains=origin)
    elif destination:
        results = results.filter(trip__ville_arrivee__nom__icontains=destination)
    if date:
        results = results.filter(date_depart__date=date)
    return render(request, 'trips/search_results.html', {'results': results})
