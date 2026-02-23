from django.urls import path
from .views import (
    reservation_list, reserve, attente_validation, annuler_reservation, message_list, delete_message, telecharger_billet,
    paiement, traiter_paiement, paiement_succes, paiement_echec, contact,
)

app_name = 'reservations'
urlpatterns = [
    path('list/', reservation_list, name='list'),
    path('reserver/<int:depart_id>/<str:date_str>/', reserve, name='reserve'),
    path('attente-validation/<int:reservation_id>/', attente_validation, name='attente_validation'),
    path('annuler/<int:reservation_id>/', annuler_reservation, name='annuler'),
    path('messages/', message_list, name='messages'),
    path('contact/', contact, name='contact'),
    path('messages/delete/<int:pk>/', delete_message, name='delete_message'),
    path('download/<int:pk>/', telecharger_billet, name='download_ticket'),
    path('billet/<int:pk>/', telecharger_billet, name='telecharger_billet'),
    path('paiement/<int:reservation_id>/', paiement, name='paiement'),
    path('paiement/<int:reservation_id>/traiter/', traiter_paiement, name='traiter_paiement'),
    path('paiement/succes/', paiement_succes, name='paiement_succes'),
    path('paiement/echec/', paiement_echec, name='paiement_echec'),
]
