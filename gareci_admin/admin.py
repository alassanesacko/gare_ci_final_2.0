from django.contrib import admin
from .models import Conducteur, Gare


@admin.register(Conducteur)
class ConducteurAdmin(admin.ModelAdmin):
	list_display = ('prenom', 'nom', 'email', 'contact', 'actif', 'date_embauche', 'bus')
	list_filter = ('actif',)
	search_fields = ('nom', 'prenom', 'email', 'contact')


@admin.register(Gare)
class GareAdmin(admin.ModelAdmin):
	list_display = ('nom', 'ville', 'adresse')
	search_fields = ('nom', 'ville')
