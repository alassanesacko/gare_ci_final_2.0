# gareci_admin/urls.py
from django.urls import path
from .views import (
    BusListView, BusCreateView, BusUpdateView, BusDeleteView,
    CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView,
    TripListView, TripCreateView, TripUpdateView, TripDeleteView,
    DepartureListView, DepartureCreateView, DepartureUpdateView, DepartureDeleteView,
    MessageListView, ReservationAdminListView,
    ReservationAdminUpdateView,
    ReservationAdminDeleteView,
    ReservationAdminConfirmView,
    DashboardView,
    MessageReplyView, MessageDeleteView,
    user_list
)

app_name = 'dashboard'
urlpatterns = [
    path('', DashboardView.as_view(), name='index'),  # Page d'accueil du dashboard (tableau de bord complet)
    # Bus
    path('buses/', BusListView.as_view(), name='bus_list'),
    path('buses/add/', BusCreateView.as_view(), name='bus_add'),
    path('buses/<int:pk>/edit/', BusUpdateView.as_view(), name='bus_edit'),
    path('buses/<int:pk>/delete/', BusDeleteView.as_view(), name='bus_delete'),
    # Catégories
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/add/', CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
    # Trajets
    path('trips/', TripListView.as_view(), name='trip_list'),
    path('trips/add/', TripCreateView.as_view(), name='trip_add'),
    path('trips/<int:pk>/edit/', TripUpdateView.as_view(), name='trip_edit'),
    path('trips/<int:pk>/delete/', TripDeleteView.as_view(), name='trip_delete'),
    # Départs
    path('departures/', DepartureListView.as_view(), name='departure_list'),
    path('departures/add/', DepartureCreateView.as_view(), name='departure_add'),
    path('departures/<int:pk>/edit/', DepartureUpdateView.as_view(), name='departure_edit'),
    path('departures/<int:pk>/delete/', DepartureDeleteView.as_view(), name='departure_delete'),
    # Messages et Réservations
    path('messages/', MessageListView.as_view(), name='message_list'),
    path('messages/<int:pk>/reply/', MessageReplyView.as_view(), name='message_reply'),
    path('messages/<int:pk>/delete/', MessageDeleteView.as_view(), name='message_delete'),
    path('reservations/', ReservationAdminListView.as_view(), name='reservation_list'),
    path('reservations/<int:pk>/edit/', ReservationAdminUpdateView.as_view(), name='reservation_edit'),
    path('reservations/<int:pk>/delete/', ReservationAdminDeleteView.as_view(), name='reservation_delete'),
    path('reservations/<int:pk>/confirm/', ReservationAdminConfirmView.as_view(), name='reservation_confirm'),
    
]
