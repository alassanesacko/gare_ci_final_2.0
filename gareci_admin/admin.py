from django.contrib import admin
from .models import Conducteur, Gare


@admin.register(Conducteur)
class ConducteurAdmin(admin.ModelAdmin):
	list_display = ('prenom', 'nom', 'email', 'telephone', 'statut', 'date_embauche')
	list_filter = ('statut', 'type_permis')
	search_fields = ('nom', 'prenom', 'email', 'telephone', 'cin')


@admin.register(Gare)
class GareAdmin(admin.ModelAdmin):
	list_display = ('nom', 'ville', 'adresse')
	search_fields = ('nom', 'ville')
