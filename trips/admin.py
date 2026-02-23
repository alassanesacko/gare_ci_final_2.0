from django.contrib import admin
from .models import Trip, Bus, Category, Depart, Ville, Arret, Segment, EtapeTrajet

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('nom', 'niveau', 'prix_multiplicateur')
    search_fields = ('nom',)

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('immatriculation', 'modele', 'capacite', 'en_service')
    search_fields = ('immatriculation', 'modele')
    list_filter = ('en_service', 'categorie')

@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code')
    search_fields = ('nom', 'code')

@admin.register(Arret)
class ArretAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville', 'adresse')
    search_fields = ('nom', 'ville__nom')
    list_filter = ('ville',)

@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display = ('arret_depart', 'arret_arrivee', 'distance_km', 'duree_minutes')
    search_fields = ('arret_depart__nom', 'arret_arrivee__nom')
    list_filter = ('distance_km', 'duree_minutes')

@admin.register(EtapeTrajet)
class EtapeTrajetAdmin(admin.ModelAdmin):
    list_display = ('trip', 'segment', 'ordre')
    search_fields = ('trip__nom', 'segment__arret_depart__nom')
    list_filter = ('ordre',)

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville_depart', 'ville_arrivee', 'price', 'actif')
    search_fields = ('nom', 'ville_depart__nom', 'ville_arrivee__nom')
    list_filter = ('ville_depart', 'ville_arrivee', 'actif')

@admin.register(Depart)
class DepartAdmin(admin.ModelAdmin):
    list_display = ("trip", "bus", "heure_depart", "heure_arrivee", "prix", "actif")
    search_fields = ("trip__nom", "bus__immatriculation")
    list_filter = ("actif",)
