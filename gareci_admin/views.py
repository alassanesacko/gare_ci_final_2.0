from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from reservations.models import ContactMessage, Reservation, ReservationStatus
from django.http import HttpResponse
from .models import Conducteur
from gareci_admin.utils import StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin 
from .forms import ArretForm, ContactReplyForm, DepartForm, EtapeTrajetFormSet, SegmentForm, TripAdminForm, VilleForm
from django.contrib.auth import get_user_model
from trips.models import Bus, Category, Ville, Arret, Segment, Trip, Depart


class CreateSuccessMessageMixin:
    success_message = None

    def get_success_message(self):
        if self.success_message:
            return self.success_message
        return f"{self.model._meta.verbose_name.capitalize()} ajoute avec succes."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message())
        return response


class UpdateSuccessMessageMixin:
    success_message = None

    def get_success_message(self):
        if self.success_message:
            return self.success_message
        return f"{self.model._meta.verbose_name.capitalize()} modifie avec succes."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message())
        return response


class DeleteSuccessMessageMixin:
    success_message = None

    def get_success_message(self):
        if self.success_message:
            return self.success_message
        return f"{self.model._meta.verbose_name.capitalize()} supprime avec succes."

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, self.get_success_message())
        return response


# Gestion des Bus
class BusListView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin , ListView):
    model = Bus
    template_name = 'dashboard/bus_list.html'
    active_tab_value ='buses'
    breadcrumb_title ='Liste de Bus'
    

class BusCreateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, CreateSuccessMessageMixin, CreateView):
    model = Bus
    fields = ['immatriculation', 'modele', 'capacite', 'categorie', 'annee_fabrication', 'en_service', 'photo', 'derniere_revision']
    template_name = 'dashboard/bus_form.html'
    active_tab_value ='buses'
    breadcrumb_title = 'Bus > Ajouter Bus'
    success_url = reverse_lazy('dashboard:bus_list')

class BusUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin, UpdateSuccessMessageMixin, UpdateView):
    model = Bus
    fields = ['immatriculation', 'modele', 'capacite', 'categorie', 'annee_fabrication', 'en_service', 'photo', 'derniere_revision']
    template_name = 'dashboard/bus_form.html'
    active_tab_value ='buses'
    breadcrumb_title = 'Bus > Modifier Bus'
    success_url = reverse_lazy('dashboard:bus_list')

class BusDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin, DeleteSuccessMessageMixin, DeleteView):
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

class CategoryCreateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin, CreateSuccessMessageMixin, CreateView):
    model = Category
    fields = ['nom', 'niveau', 'prix_multiplicateur', 'a_wifi', 'a_climatisation', 'a_prise_usb', 'a_wc', 'a_repas', 'a_couchette']
    template_name = 'dashboard/category_form.html'

    active_tab_value ='categories'
    breadcrumb_title = 'Categories > Ajouter Categories'
    success_url = reverse_lazy('dashboard:category_list')

class CategoryUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin, UpdateSuccessMessageMixin, UpdateView):
    model = Category
    fields = ['nom', 'niveau', 'prix_multiplicateur', 'a_wifi', 'a_climatisation', 'a_prise_usb', 'a_wc', 'a_repas', 'a_couchette']
    template_name = 'dashboard/category_form.html'
    active_tab_value ='categories'
    breadcrumb_title = 'Categories > Modifier Categories'
    success_url = reverse_lazy('dashboard:category_list')

class CategoryDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin, DeleteSuccessMessageMixin, DeleteView):
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


class VilleCreateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, CreateSuccessMessageMixin, CreateView):
    model = Ville
    form_class = VilleForm
    template_name = "dashboard/ville_form.html"
    active_tab_value = "villes"
    breadcrumb_title = "Villes > Ajouter Ville"
    success_url = reverse_lazy("dashboard:ville_list")


class VilleUpdateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, UpdateSuccessMessageMixin, UpdateView):
    model = Ville
    form_class = VilleForm
    template_name = "dashboard/ville_form.html"
    active_tab_value = "villes"
    breadcrumb_title = "Villes > Modifier Ville"
    success_url = reverse_lazy("dashboard:ville_list")


class VilleDeleteView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, DeleteSuccessMessageMixin, DeleteView):
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


class ArretCreateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, CreateSuccessMessageMixin, CreateView):
    model = Arret
    form_class = ArretForm
    template_name = "dashboard/arret_form.html"
    active_tab_value = "arrets"
    breadcrumb_title = "Arrets > Ajouter Arret"
    success_url = reverse_lazy("dashboard:arret_list")


class ArretUpdateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, UpdateSuccessMessageMixin, UpdateView):
    model = Arret
    form_class = ArretForm
    template_name = "dashboard/arret_form.html"
    active_tab_value = "arrets"
    breadcrumb_title = "Arrets > Modifier Arret"
    success_url = reverse_lazy("dashboard:arret_list")


class ArretDeleteView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, DeleteSuccessMessageMixin, DeleteView):
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


class SegmentCreateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, CreateSuccessMessageMixin, CreateView):
    model = Segment
    form_class = SegmentForm
    template_name = "dashboard/segment_form.html"
    active_tab_value = "segments"
    breadcrumb_title = "Segments > Ajouter Segment"
    success_url = reverse_lazy("dashboard:segment_list")


class SegmentUpdateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, UpdateSuccessMessageMixin, UpdateView):
    model = Segment
    form_class = SegmentForm
    template_name = "dashboard/segment_form.html"
    active_tab_value = "segments"
    breadcrumb_title = "Segments > Modifier Segment"
    success_url = reverse_lazy("dashboard:segment_list")


class SegmentDeleteView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, DeleteSuccessMessageMixin, DeleteView):
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


class ConducteurCreateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, CreateSuccessMessageMixin, CreateView):
    model = Conducteur
    fields = ['nom', 'prenom', 'cin', 'telephone', 'email', 'date_embauche', 'numero_permis', 'type_permis', 'date_expiration_permis', 'statut', 'photo']
    template_name = 'dashboard/conducteur_form.html'
    active_tab_value = 'conducteurs'
    breadcrumb_title = 'Conducteurs > Ajouter Conducteur'
    success_url = reverse_lazy('dashboard:conducteur_list')


class ConducteurUpdateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, UpdateSuccessMessageMixin, UpdateView):
    model = Conducteur
    fields = ['nom', 'prenom', 'cin', 'telephone', 'email', 'date_embauche', 'numero_permis', 'type_permis', 'date_expiration_permis', 'statut', 'photo']
    template_name = 'dashboard/conducteur_form.html'
    active_tab_value = 'conducteurs'
    breadcrumb_title = 'Conducteurs > Modifier Conducteur'
    success_url = reverse_lazy('dashboard:conducteur_list')


class ConducteurDeleteView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin, DeleteSuccessMessageMixin, DeleteView):
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
        messages.success(self.request, "Trajet ajoute avec succes.")
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
        messages.success(self.request, "Trajet modifie avec succes.")
        return redirect(self.success_url)

class TripDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin, DeleteSuccessMessageMixin, DeleteView):
    model = Trip
    template_name = 'dashboard/trip_confirm_delete.html'
    active_tab_value ='trips'
    breadcrumb_title = 'Trajets > Suppression Trajets'
    success_url = reverse_lazy('dashboard:trip_list')

@staff_member_required(login_url="accounts:login")
def depart_list(request):
    today = timezone.localdate()
    departs = (
        Depart.objects.select_related(
            "trip__arret_depart__ville",
            "trip__arret_arrivee__ville",
            "bus",
        )
        .order_by("trip", "heure_depart")
    )
    for depart in departs:
        depart.places_du_jour = depart.places_disponibles_pour(today)
    return render(
        request,
        "dashboard/depart_list.html",
        {
            "departs": departs,
            "today": today,
            "active_tab": "departures",
            "breadcrumb_title": "Departs",
        },
    )


@staff_member_required(login_url="accounts:login")
def depart_create(request):
    if request.method == "POST":
        form = DepartForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Depart cree avec succes.")
            return redirect("dashboard:depart_list")
    else:
        form = DepartForm()

    return render(
        request,
        "dashboard/depart_form.html",
        {
            "form": form,
            "active_tab": "departures",
            "breadcrumb_title": "Departs > Nouveau depart",
        },
    )


@staff_member_required(login_url="accounts:login")
def depart_edit(request, pk):
    depart = get_object_or_404(Depart, pk=pk)

    if request.method == "POST":
        form = DepartForm(request.POST, instance=depart)
        if form.is_valid():
            form.save()
            messages.success(request, "Depart modifie avec succes.")
            return redirect("dashboard:depart_list")
    else:
        form = DepartForm(instance=depart)

    return render(
        request,
        "dashboard/depart_form.html",
        {
            "form": form,
            "object": depart,
            "active_tab": "departures",
            "breadcrumb_title": "Departs > Modifier depart",
        },
    )


@staff_member_required(login_url="accounts:login")
def depart_delete(request, pk):
    depart = get_object_or_404(Depart, pk=pk)

    if request.method == "POST":
        depart.delete()
        messages.success(request, "Depart supprime.")
        return redirect("dashboard:depart_list")

    return render(
        request,
        "dashboard/depart_confirm_delete.html",
        {
            "object": depart,
            "active_tab": "departures",
            "breadcrumb_title": "Departs > Suppression depart",
        },
    )

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

        messages.success(self.request, "Reponse envoyee avec succes.")
        return super().form_valid(form)

class MessageDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin, DeleteSuccessMessageMixin, DeleteView):
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
    ordering = ['-created_at']

class ReservationAdminUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin, UpdateSuccessMessageMixin, UpdateView):
    model = Reservation
    fields = ['statut', 'utilisateur', 'date_voyage', 'depart', 'nombre_places', 'prix_total', 'paiement']
    template_name = 'dashboard/reservation_form.html'
    active_tab_value ='reservations'
    breadcrumb_title = 'Reservations > Modifier Reservations'

    def get_success_url(self):
        return reverse_lazy('dashboard:reservation_list')

class ReservationAdminDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin, DeleteSuccessMessageMixin, DeleteView):
    model = Reservation
    template_name = 'dashboard/reservation_confirm_delete.html'
    active_tab_value ='reservations'
    breadcrumb_title = 'Reservations > Suppression Reservations'
    success_url = reverse_lazy('dashboard:reservation_list')

class ReservationAdminConfirmView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , TemplateView):
    active_tab_value ='departures'
    def post(self, request, pk, *args, **kwargs):
        reservation = get_object_or_404(Reservation, pk=pk)
        reservation.statut = ReservationStatus.CONFIRMEE
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
        upcoming_departures = Depart.objects.select_related(
            'trip', 'bus'
        ).prefetch_related(
            'reservations'
        ).filter(
            actif=True,
        ).order_by('heure_depart')

        context['upcoming_trips'] = upcoming_departures.count()
        
        # Liste complete des departs pour le tableau principal
        context['object_list'] = Depart.objects.select_related('trip', 'bus').all().order_by('heure_depart')
        # Reservations recentes (10 dernieres)
        recent_reservations = Reservation.objects.select_related(
            'utilisateur',
            'depart__trip',
            'depart__bus'
        ).filter(
            statut__in=[ReservationStatus.EN_ATTENTE, ReservationStatus.CONFIRMEE]  # Uniquement les reservations actives
        ).order_by('-created_at')[:10]
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

@staff_member_required
def reservation_list(request):
    reservations = Reservation.objects.filter(
        statut__in=[
            ReservationStatus.EN_ATTENTE,
            ReservationStatus.CONFIRMEE,
        ]
    ).select_related(
        'depart__trip__arret_depart__ville',
        'depart__trip__arret_arrivee__ville',
        'depart__bus__categorie',
        'utilisateur',
    ).order_by('date_voyage', 'depart__heure_depart')

    reservations_par_date = {}
    for resa in reservations:
        date = resa.date_voyage
        if date not in reservations_par_date:
            reservations_par_date[date] = []
        reservations_par_date[date].append(resa)

    contexte_dates = []
    for date in sorted(reservations_par_date.keys()):
        resas = reservations_par_date[date]
        contexte_dates.append({
            'date':          date,
            'reservations':  resas,
            'nb_confirmees': sum(
                1 for r in resas
                if r.statut == ReservationStatus.CONFIRMEE
            ),
            'nb_en_attente': sum(
                1 for r in resas
                if r.statut == ReservationStatus.EN_ATTENTE
            ),
            'recettes':      sum(
                r.prix_total for r in resas
                if r.statut == ReservationStatus.CONFIRMEE
            ),
        })

    return render(request, 'dashboard/reservation_list.html', {
        'dates': contexte_dates,
    })

@staff_member_required
def admin_voir_billet(request, reservation_id):
    from reservations.ticket import generer_billet_pdf
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        statut=ReservationStatus.CONFIRMEE
    )
    pdf_bytes = generer_billet_pdf(reservation)
    response  = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="billet_{reservation.reference}.pdf"'
    )
    return response
