from django.urls import path
from .views import (
    reservation_list, reserve_departure, message_list, delete_message, download_ticket,
    paiement, traiter_paiement, paiement_succes, paiement_echec,
)

app_name = 'reservations'
urlpatterns = [
    path('list/', reservation_list, name='list'),
    path('reserve/<int:departure_id>/', reserve_departure, name='reserve'),
    path('messages/', message_list, name='messages'),
    path('messages/delete/<int:pk>/', delete_message, name='delete_message'),
    path('download/<int:pk>/', download_ticket, name='download_ticket'),
    path('paiement/<int:reservation_id>/', paiement, name='paiement'),
    path('paiement/<int:reservation_id>/traiter/', traiter_paiement, name='traiter_paiement'),
    path('paiement/succes/', paiement_succes, name='paiement_succes'),
    path('paiement/echec/', paiement_echec, name='paiement_echec'),
]
