# trips/urls.py
from django.urls import path
from .views import about, cgv, home, search_results

app_name = 'trips'
urlpatterns = [
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('cgv/', cgv, name='cgv'),
    path('recherche/', search_results, name='search_results'),
]
