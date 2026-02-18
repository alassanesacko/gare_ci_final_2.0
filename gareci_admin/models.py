from django.db import models
from django.utils import timezone


class Conducteur(models.Model):
	nom = models.CharField(max_length=150)
	prenom = models.CharField(max_length=150)
	date_de_naissance = models.DateField(null=True, blank=True)
	email = models.EmailField(null=True, blank=True)
	contact = models.CharField(max_length=50, null=True, blank=True)
	permis = models.CharField(max_length=100, null=True, blank=True)
	actif = models.BooleanField(default=True)
	date_embauche = models.DateField(null=True, blank=True)
	bus = models.ForeignKey('trips.Bus', on_delete=models.SET_NULL, null=True, blank=True, related_name='conducteurs')

	class Meta:
		verbose_name = 'Conducteur'
		verbose_name_plural = 'Conducteurs'

	def __str__(self):
		return f"{self.prenom} {self.nom}"


class Gare(models.Model):
	nom = models.CharField(max_length=200)
	ville = models.CharField(max_length=150)
	adresse = models.CharField(max_length=300, null=True, blank=True)
	description = models.TextField(null=True, blank=True)
	commentaire = models.TextField(null=True, blank=True)

	class Meta:
		verbose_name = 'Gare'
		verbose_name_plural = 'Gares'

	def __str__(self):
		return f"{self.nom} — {self.ville}"

