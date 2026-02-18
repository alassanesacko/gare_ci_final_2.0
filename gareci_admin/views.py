from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.core.mail import send_mail
from django.utils.timezone import now
from datetime import timedelta, datetime

from trips.models import Bus, Category, Trip, Departure
from reservations.models import ContactMessage, Reservation
from gareci_admin.utils import StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin 
from .forms import ContactReplyForm
from django.contrib.auth import get_user_model


# Gestion des Bus
class BusListView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin , ListView):
    model = Bus
    template_name = 'dashboard/bus_list.html'
    active_tab_value ='buses'
    breadcrumb_title ='Liste de Bus'
    

class BusCreateView(StaffRequiredMixin, ActiveTabMixin, BreadcrumbMixin , CreateView):
    model = Bus
    fields = ['name', 'capacity']
    template_name = 'dashboard/bus_form.html'
    active_tab_value ='buses'
    breadcrumb_title = 'Bus > Ajouter Bus'
    success_url = reverse_lazy('dashboard:bus_list')

class BusUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , UpdateView):
    model = Bus
    fields = ['name', 'capacity']
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

# Gestion des Catégories
class CategoryListView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , ListView):
    model = Category
    template_name = 'dashboard/category_list.html'
    active_tab_value ='categories'
    breadcrumb_title = 'Catégories'

class CategoryCreateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , CreateView):
    model = Category
    fields = ['name']
    template_name = 'dashboard/category_form.html'
    template_name = 'home.html'

    active_tab_value ='categories'
    breadcrumb_title = 'Catégories > Ajouter Catégories'
    success_url = reverse_lazy('dashboard:category_list')

class CategoryUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , UpdateView):
    model = Category
    fields = ['name']
    template_name = 'dashboard/category_form.html'
    active_tab_value ='categories'
    breadcrumb_title = 'Catégories > Modifier Catégories'
    success_url = reverse_lazy('dashboard:category_list')

class CategoryDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , DeleteView):
    model = Category
    template_name = 'dashboard/category_confirm_delete.html'
    active_tab_value ='categories'
    breadcrumb_title = 'Catégories > Suppression Catégories'
    success_url = reverse_lazy('dashboard:category_list')

# Gestion des Trajets (Trip)
class TripListView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , ListView):
    model = Trip
    template_name = 'dashboard/trip_list.html'
    active_tab_value ='trips'
    breadcrumb_title = 'Trajets'

class TripCreateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , CreateView):
    model = Trip
    fields = ['origin', 'destination', 'category', 'description', 'price']
    template_name = 'dashboard/trip_form.html'
    active_tab_value ='trips'
    breadcrumb_title = 'Trajets > Ajouter Trajets'
    success_url = reverse_lazy('dashboard:trip_list')

class TripUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , UpdateView):
    model = Trip
    fields = ['origin', 'destination', 'category', 'description', 'price']
    template_name = 'dashboard/trip_form.html'
    active_tab_value ='trips'
    breadcrumb_title = 'Trajets > Modifier Trajets'
    success_url = reverse_lazy('dashboard:trip_list')

class TripDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , DeleteView):
    model = Trip
    template_name = 'dashboard/trip_confirm_delete.html'
    active_tab_value ='trips'
    breadcrumb_title = 'Trajets > Suppression Trajets'
    success_url = reverse_lazy('dashboard:trip_list')

# Gestion des Départs (Departure)
class DepartureListView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , ListView):
    model = Departure
    template_name = 'dashboard/departure_list.html'
    active_tab_value ='departures'
    breadcrumb_title = 'Départs'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        end_date = today + timedelta(days=7)
        upcoming_departures = Departure.objects.select_related('trip', 'bus').prefetch_related('reservation_set').filter(
            date__gte=today,
            date__lte=end_date,
        ).order_by('date', 'time')

        departures_by_date = {}
        for departure in upcoming_departures:
            date_str = departure.date.strftime('%Y-%m-%d')
            if date_str not in departures_by_date:
                departures_by_date[date_str] = []

            reservations_count = departure.reservation_set.filter(status__in=['P', 'C']).count()
            bus_capacity = departure.bus.capacity
            available_seats = max(0, bus_capacity - reservations_count)
            occupancy_rate = (reservations_count / bus_capacity * 100) if bus_capacity > 0 else 0

            departure_info = {
                'departure': departure,
                'reservations_count': reservations_count,
                'available_seats': available_seats,
                'occupancy_rate': min(100, occupancy_rate)
            }
            departures_by_date[date_str].append(departure_info)

        context['departures_by_date'] = departures_by_date
        context['date_range'] = [today + timedelta(days=x) for x in range(8)]
        context['empty'] = []  # pour éviter erreur si aucun départ
        return context

    def get_queryset(self):
        return Departure.objects.filter(date__gte=now()).order_by('date', 'time')

class DepartureCreateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , CreateView):
    model = Departure
    fields = ['trip', 'bus', 'date', 'time', 'is_active']
    template_name = 'dashboard/departure_form.html'
    active_tab_value ='departures'
    breadcrumb_title = 'Départs > Ajouter Départs'
    success_url = reverse_lazy('dashboard:departure_list')

class DepartureUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , UpdateView):
    model = Departure
    fields = ['trip', 'bus', 'date', 'time', 'is_active']
    template_name = 'dashboard/departure_form.html'
    active_tab_value ='departures'
    breadcrumb_title = 'Départs > Modifier Départs'
    success_url = reverse_lazy('dashboard:departure_list')

class DepartureDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , DeleteView):
    model = Departure
    template_name = 'dashboard/departure_confirm_delete.html'
    active_tab_value ='departures'
    breadcrumb_title = 'Départs > Suppression Départs'
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
        # Vérification de la réponse
        if not response.reply:
            return self.form_invalid(form)
        
        response.save()
        
        # Envoi de l'email au client
        try:
            send_mail(
                subject='Réponse à votre message de contact - Gareci',
                message=f"""Bonjour {response.name},

Voici notre réponse à votre message du {response.submitted_at}:

{response.reply}

Cordialement,
L'équipe Gareci""",
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

# Consultation des Réservations clients
class ReservationAdminListView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , ListView):
    model = Reservation
    template_name = 'dashboard/reservation_list.html'
    active_tab_value ='reservations'
    breadcrumb_title = 'Réservations '
    context_object_name = 'reservations'
    ordering = ['-booked_at']

class ReservationAdminUpdateView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , UpdateView):
    model = Reservation
    fields = ['status']
    template_name = 'dashboard/reservation_form.html'
    active_tab_value ='reservations'
    breadcrumb_title = 'Réservations  > Modifier Réservations '

    def get_success_url(self):
        return reverse_lazy('dashboard:reservation_list')

class ReservationAdminDeleteView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , DeleteView):
    model = Reservation
    template_name = 'dashboard/reservation_confirm_delete.html'
    active_tab_value ='reservations'
    breadcrumb_title = 'Réservations  > Suppression Réservations '
    success_url = reverse_lazy('dashboard:reservation_list')

class ReservationAdminConfirmView(StaffRequiredMixin,ActiveTabMixin, BreadcrumbMixin , TemplateView):
    active_tab_value ='departures'
    def post(self, request, pk, *args, **kwargs):
        reservation = get_object_or_404(Reservation, pk=pk)
        reservation.status = 'C'
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
        
        # Départs à venir (7 prochains jours) avec statistiques
        end_date = today + timedelta(days=7)
        upcoming_departures = Departure.objects.select_related(
            'trip', 'bus'
        ).prefetch_related(
            'reservation_set'
        ).filter(
            date__gte=today,
            date__lte=end_date,
        ).order_by('date', 'time')
        
        # Organiser les départs par date
        departures_by_date = {}
        for departure in upcoming_departures:
            date_str = departure.date.strftime('%Y-%m-%d')
            if date_str not in departures_by_date:
                departures_by_date[date_str] = []
            # Utiliser une seule requête pour compter les réservations actives
            reservations_count = departure.reservation_set.all().filter(
                status__in=['P', 'C']
            ).count()
            bus_capacity = departure.bus.capacity
            available_seats = max(0, bus_capacity - reservations_count)
            occupancy_rate = (reservations_count / bus_capacity * 100) if bus_capacity > 0 else 0
              # Ajouter les informations enrichies
            departure_info = {
                'departure': departure,
                'reservations_count': reservations_count,
                'available_seats': available_seats,
                'occupancy_rate': min(100, occupancy_rate)  # Plafonner à 100%
            }
            departures_by_date[date_str].append(departure_info)
            
        context['date_range'] = [today + timedelta(days=i) for i in range(7)]
        context['departures_by_date'] = departures_by_date
        context['upcoming_trips'] = upcoming_departures.count()
        
        # Liste complète des départs pour le tableau principal
        context['object_list'] = Departure.objects.select_related('trip', 'bus').all().order_by('-date', '-time')
        # Réservations récentes (10 dernières)
        recent_reservations = Reservation.objects.select_related(
            'user',
            'departure__trip',
            'departure__bus'
        ).filter(
            status__in=['P', 'C']  # Uniquement les réservations actives
        ).order_by('-booked_at')[:10]
        context['recent_reservations'] = recent_reservations
        # Messages récents (5 derniers sans réponse)
        recent_messages = ContactMessage.objects.filter(
            replied_at__isnull=True
        ).order_by('-submitted_at')[:5]
        context['recent_messages'] = recent_messages
        return context

def user_list(request):
    # Logique pour afficher la liste des utilisateurs
    return render(request, 'gareci_admin/user_list.html')