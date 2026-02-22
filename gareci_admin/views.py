from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.core.mail import send_mail

from trips.models import Arret, Bus, Category, Departure, Segment, Trip, Ville
from .models import Conducteur
from reservations.models import ContactMessage, Reservation, ReservationStatus
from gareci_admin.utils import StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin 
from .forms import ArretForm, ContactReplyForm, DepartureAdminForm, EtapeTrajetFormSet, SegmentForm, TripAdminForm, VilleForm
from django.contrib.auth import get_user_model


# Gestion des Bus
class BusListView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin , ListView):
    model = Bus
    template_name = 'dashboard/bus_list.html'
    active_tab_value ='buses'
    breadcrumb_title ='Liste de Bus'
    

class BusCreateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin , CreateView):
    model = Bus
    fields = ['immatriculation', 'modele', 'capacite', 'categorie', 'annee_fabrication', 'en_service', 'photo', 'derniere_revision']
    template_name = 'dashboard/bus_form.html'
    active_tab_value ='buses'
    breadcrumb_title = 'Bus > Ajouter Bus'
    success_url = reverse_lazy('dashboard:bus_list')

class BusUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , UpdateView):
    model = Bus
    fields = ['immatriculation', 'modele', 'capacite', 'categorie', 'annee_fabrication', 'en_service', 'photo', 'derniere_revision']
    template_name = 'dashboard/bus_form.html'
    active_tab_value ='buses'
    breadcrumb_title = 'Bus > Modifier Bus'
    success_url = reverse_lazy('dashboard:bus_list')

class BusDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , DeleteView):
    model = Bus
    template_name = 'dashboard/bus_confirm_delete.html'
    active_tab_value ='buses'
    breadcrumb_title = 'Bus > Suppression Bus'
    success_url = reverse_lazy('dashboard:bus_list')

# Gestion des Categories
class CategoryListView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , ListView):
    model = Category
    template_name = 'dashboard/category_list.html'
    active_tab_value ='categories'
    breadcrumb_title = 'Categories'

class CategoryCreateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , CreateView):
    model = Category
    fields = ['nom', 'niveau', 'prix_multiplicateur', 'a_wifi', 'a_climatisation', 'a_prise_usb', 'a_wc', 'a_repas', 'a_couchette']
    template_name = 'dashboard/category_form.html'

    active_tab_value ='categories'
    breadcrumb_title = 'Categories > Ajouter Categories'
    success_url = reverse_lazy('dashboard:category_list')

class CategoryUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , UpdateView):
    model = Category
    fields = ['nom', 'niveau', 'prix_multiplicateur', 'a_wifi', 'a_climatisation', 'a_prise_usb', 'a_wc', 'a_repas', 'a_couchette']
    template_name = 'dashboard/category_form.html'
    active_tab_value ='categories'
    breadcrumb_title = 'Categories > Modifier Categories'
    success_url = reverse_lazy('dashboard:category_list')

class CategoryDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , DeleteView):
    model = Category
    template_name = 'dashboard/category_confirm_delete.html'
    active_tab_value ='categories'
    breadcrumb_title = 'Categories > Suppression Categories'
    success_url = reverse_lazy('dashboard:category_list')


# Gestion des Villes
class VilleListView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, ListView):
    model = Ville
    template_name = "dashboard/ville_list.html"
    active_tab_value = "villes"
    breadcrumb_title = "Villes"


class VilleCreateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, CreateView):
    model = Ville
    form_class = VilleForm
    template_name = "dashboard/ville_form.html"
    active_tab_value = "villes"
    breadcrumb_title = "Villes > Ajouter Ville"
    success_url = reverse_lazy("dashboard:ville_list")


class VilleUpdateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, UpdateView):
    model = Ville
    form_class = VilleForm
    template_name = "dashboard/ville_form.html"
    active_tab_value = "villes"
    breadcrumb_title = "Villes > Modifier Ville"
    success_url = reverse_lazy("dashboard:ville_list")


class VilleDeleteView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, DeleteView):
    model = Ville
    template_name = "dashboard/ville_confirm_delete.html"
    active_tab_value = "villes"
    breadcrumb_title = "Villes > Suppression Ville"
    success_url = reverse_lazy("dashboard:ville_list")


# Gestion des Arrets
class ArretListView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, ListView):
    model = Arret
    template_name = "dashboard/arret_list.html"
    active_tab_value = "arrets"
    breadcrumb_title = "Arrets"


class ArretCreateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, CreateView):
    model = Arret
    form_class = ArretForm
    template_name = "dashboard/arret_form.html"
    active_tab_value = "arrets"
    breadcrumb_title = "Arrets > Ajouter Arret"
    success_url = reverse_lazy("dashboard:arret_list")


class ArretUpdateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, UpdateView):
    model = Arret
    form_class = ArretForm
    template_name = "dashboard/arret_form.html"
    active_tab_value = "arrets"
    breadcrumb_title = "Arrets > Modifier Arret"
    success_url = reverse_lazy("dashboard:arret_list")


class ArretDeleteView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, DeleteView):
    model = Arret
    template_name = "dashboard/arret_confirm_delete.html"
    active_tab_value = "arrets"
    breadcrumb_title = "Arrets > Suppression Arret"
    success_url = reverse_lazy("dashboard:arret_list")


# Gestion des Segments
class SegmentListView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, ListView):
    model = Segment
    template_name = "dashboard/segment_list.html"
    active_tab_value = "segments"
    breadcrumb_title = "Segments"


class SegmentCreateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, CreateView):
    model = Segment
    form_class = SegmentForm
    template_name = "dashboard/segment_form.html"
    active_tab_value = "segments"
    breadcrumb_title = "Segments > Ajouter Segment"
    success_url = reverse_lazy("dashboard:segment_list")


class SegmentUpdateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, UpdateView):
    model = Segment
    form_class = SegmentForm
    template_name = "dashboard/segment_form.html"
    active_tab_value = "segments"
    breadcrumb_title = "Segments > Modifier Segment"
    success_url = reverse_lazy("dashboard:segment_list")


class SegmentDeleteView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, DeleteView):
    model = Segment
    template_name = "dashboard/segment_confirm_delete.html"
    active_tab_value = "segments"
    breadcrumb_title = "Segments > Suppression Segment"
    success_url = reverse_lazy("dashboard:segment_list")


# Gestion des Conducteurs
class ConducteurListView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, ListView):
    model = Conducteur
    template_name = 'dashboard/conducteur_list.html'
    active_tab_value = 'conducteurs'
    breadcrumb_title = 'Conducteurs'


class ConducteurCreateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, CreateView):
    model = Conducteur
    fields = ['nom', 'prenom', 'cin', 'telephone', 'email', 'date_embauche', 'numero_permis', 'type_permis', 'date_expiration_permis', 'statut', 'photo']
    template_name = 'dashboard/conducteur_form.html'
    active_tab_value = 'conducteurs'
    breadcrumb_title = 'Conducteurs > Ajouter Conducteur'
    success_url = reverse_lazy('dashboard:conducteur_list')


class ConducteurUpdateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, UpdateView):
    model = Conducteur
    fields = ['nom', 'prenom', 'cin', 'telephone', 'email', 'date_embauche', 'numero_permis', 'type_permis', 'date_expiration_permis', 'statut', 'photo']
    template_name = 'dashboard/conducteur_form.html'
    active_tab_value = 'conducteurs'
    breadcrumb_title = 'Conducteurs > Modifier Conducteur'
    success_url = reverse_lazy('dashboard:conducteur_list')


class ConducteurDeleteView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, DeleteView):
    model = Conducteur
    template_name = 'dashboard/conducteur_confirm_delete.html'
    active_tab_value = 'conducteurs'
    breadcrumb_title = 'Conducteurs > Suppression Conducteur'
    success_url = reverse_lazy('dashboard:conducteur_list')

# Gestion des Trajets (Trip)
class TripListView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , ListView):
    model = Trip
    template_name = 'dashboard/trip_list.html'
    active_tab_value ='trips'
    breadcrumb_title = 'Trajets'

    def get_queryset(self):
        return (
            Trip.objects.select_related("ville_depart", "ville_arrivee", "arret_depart", "arret_arrivee")
            .prefetch_related("etapetrajet_set__segment__arret_depart", "etapetrajet_set__segment__arret_arrivee")
            .order_by("nom")
        )

class TripCreateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , CreateView):
    model = Trip
    form_class = TripAdminForm
    template_name = 'dashboard/trip_form.html'
    active_tab_value ='trips'
    breadcrumb_title = 'Trajets > Ajouter Trajets'
    success_url = reverse_lazy('dashboard:trip_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["etape_formset"] = EtapeTrajetFormSet(self.request.POST, prefix="etapes")
        else:
            context["etape_formset"] = EtapeTrajetFormSet(prefix="etapes")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        etape_formset = context["etape_formset"]
        etape_formset.expected_trip_start_id = form.cleaned_data["arret_depart"].id
        etape_formset.expected_trip_end_id = form.cleaned_data["arret_arrivee"].id
        if not etape_formset.is_valid():
            return self.form_invalid(form)

        self.object = form.save()
        etape_formset.instance = self.object
        etape_formset.save()
        return redirect(self.success_url)

class TripUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , UpdateView):
    model = Trip
    form_class = TripAdminForm
    template_name = 'dashboard/trip_form.html'
    active_tab_value ='trips'
    breadcrumb_title = 'Trajets > Modifier Trajets'
    success_url = reverse_lazy('dashboard:trip_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["etape_formset"] = EtapeTrajetFormSet(
                self.request.POST,
                instance=self.object,
                prefix="etapes",
            )
        else:
            context["etape_formset"] = EtapeTrajetFormSet(
                instance=self.object,
                prefix="etapes",
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        etape_formset = context["etape_formset"]
        etape_formset.expected_trip_start_id = form.cleaned_data["arret_depart"].id
        etape_formset.expected_trip_end_id = form.cleaned_data["arret_arrivee"].id
        if not etape_formset.is_valid():
            return self.form_invalid(form)

        self.object = form.save()
        etape_formset.instance = self.object
        etape_formset.save()
        return redirect(self.success_url)

class TripDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , DeleteView):
    model = Trip
    template_name = 'dashboard/trip_confirm_delete.html'
    active_tab_value ='trips'
    breadcrumb_title = 'Trajets > Suppression Trajets'
    success_url = reverse_lazy('dashboard:trip_list')

# Gestion des Departs (Departure)
class DepartureListView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , ListView):
    model = Departure
    template_name = 'dashboard/departure_list.html'
    active_tab_value ='departures'
    breadcrumb_title = 'Departs'


    def get_queryset(self):
        return Departure.objects.select_related('trip', 'bus').order_by('date_depart')

class DepartureCreateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , CreateView):
    model = Departure
    form_class = DepartureAdminForm
    template_name = 'dashboard/departure_form.html'
    active_tab_value ='departures'
    breadcrumb_title = 'Departs > Ajouter Departs'
    success_url = reverse_lazy('dashboard:departure_list')

class DepartureUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , UpdateView):
    model = Departure
    form_class = DepartureAdminForm
    template_name = 'dashboard/departure_form.html'
    active_tab_value ='departures'
    breadcrumb_title = 'Departs > Modifier Departs'
    success_url = reverse_lazy('dashboard:departure_list')

class DepartureDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , DeleteView):
    model = Departure
    template_name = 'dashboard/departure_confirm_delete.html'
    active_tab_value ='departures'
    breadcrumb_title = 'Departs > Suppression Departs'
    success_url = reverse_lazy('dashboard:departure_list')

# Consultation des Messages clients
class MessageListView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , ListView):
    model = ContactMessage
    template_name = 'dashboard/message_list.html'
    active_tab_value ='messages'
    breadcrumb_title = 'Messages'
    context_object_name = 'messages'
    ordering = ['-submitted_at']

class MessageReplyView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , UpdateView):
    model = ContactMessage
    form_class = ContactReplyForm
    template_name = 'dashboard/message_form.html'
    active_tab_value ='messages'
    breadcrumb_title = 'Messages > Reponse Messages'
    success_url = reverse_lazy('dashboard:message_list')

    def form_valid(self, form):
        response = form.save(commit=False)
        response.replied_at = timezone.now()
        # Verification de la reponse
        if not response.reply:
            return self.form_invalid(form)
        
        response.save()
        
        # Envoi de l'email au client
        try:
            send_mail(
                subject='Reponse a votre message de contact - Gareci',
                message=f"""Bonjour {response.name},

Voici notre reponse a votre message du {response.submitted_at}:

{response.reply}

Cordialement,
L'equipe Gareci""",
                from_email=None,  # Utilise DEFAULT_FROM_EMAIL
                recipient_list=[response.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Erreur d'envoi d'email: {e}")  # Pour debug
            
        return super().form_valid(form)

class MessageDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , DeleteView):
    model = ContactMessage
    template_name = 'dashboard/message_confirm_delete.html'
    active_tab_value ='messages'
    breadcrumb_title = 'Messages > Suppression Messages'
    success_url = reverse_lazy('dashboard:message_list')

# Consultation des Reservations clients
class ReservationAdminListView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , ListView):
    model = Reservation
    template_name = 'dashboard/reservation_list.html'
    active_tab_value ='reservations'
    breadcrumb_title = 'Reservations '
    context_object_name = 'reservations'
    ordering = ['-booked_at']

class ReservationAdminUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , UpdateView):
    model = Reservation
    fields = ['status']
    template_name = 'dashboard/reservation_form.html'
    active_tab_value ='reservations'
    breadcrumb_title = 'Reservations > Modifier Reservations'

    def get_success_url(self):
        return reverse_lazy('dashboard:reservation_list')

class ReservationAdminDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , DeleteView):
    model = Reservation
    template_name = 'dashboard/reservation_confirm_delete.html'
    active_tab_value ='reservations'
    breadcrumb_title = 'Reservations > Suppression Reservations'
    success_url = reverse_lazy('dashboard:reservation_list')

class ReservationAdminConfirmView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , TemplateView):
    active_tab_value ='departures'
    def post(self, request, pk, *args, **kwargs):
        reservation = get_object_or_404(Reservation, pk=pk)
        reservation.status = ReservationStatus.CONFIRMEE
        reservation.save()
        return redirect('dashboard:reservation_list')

# Vue du Tableau de Bord
class DashboardView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , TemplateView):
    template_name = 'dashboard/dashboard.html'
    active_tab_value ='dashboard'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        CustomUser = get_user_model()
        context['empty'] = []  # Liste vide pour le filtre default_if_none
        # Statistiques rapides
        context['total_reservations'] = Reservation.objects.count()
        context['total_users'] = CustomUser.objects.count()
        
        # Departs a venir (sans limite de 7 jours) avec statistiques
        upcoming_departures = Departure.objects.select_related(
            'trip', 'bus'
        ).prefetch_related(
            'reservation_set'
        ).filter(
            date_depart__date__gte=today,
        ).order_by('date_depart')

        context['upcoming_trips'] = upcoming_departures.count()
        
        # Liste complete des departs pour le tableau principal
        context['object_list'] = Departure.objects.select_related('trip', 'bus').all().order_by('-date_depart')
        # Reservations recentes (10 dernieres)
        recent_reservations = Reservation.objects.select_related(
            'user',
            'departure__trip',
            'departure__bus'
        ).filter(
            status__in=[ReservationStatus.EN_ATTENTE_VALIDATION, ReservationStatus.VALIDEE, ReservationStatus.CONFIRMEE]  # Uniquement les reservations actives
        ).order_by('-booked_at')[:10]
        context['recent_reservations'] = recent_reservations
        # Messages recents (5 derniers sans reponse)
        recent_messages = ContactMessage.objects.filter(
            replied_at__isnull=True
        ).order_by('-submitted_at')[:5]
        context['recent_messages'] = recent_messages
        return context

def user_list(request):
    # Logique pour afficher la liste des utilisateurs
    return render(request, 'gareci_admin/user_list.html')
