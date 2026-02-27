from django.db import models
from django.utils import timezone
from django.db import models


class Conducteur(models.Model):
	TYPE_PERMIS = [
		('D', 'D'),
		('DE', 'DE'),
	]
	STATUT = [
		
		('ACTIF', 'Actif'),
		('CONGE', 'En congé'),
		('SUSPENDU', 'Suspendu'),
	]

	nom = models.CharField(max_length=150)
	prenom = models.CharField(max_length=150)
	cin = models.CharField(max_length=50, unique=True)
	telephone = models.CharField(max_length=50, null=True, blank=True)
	email = models.EmailField(null=True, blank=True)
	date_embauche = models.DateField(null=True, blank=True)
	numero_permis = models.CharField(max_length=100, null=True, blank=True)
	type_permis = models.CharField(max_length=3, choices=TYPE_PERMIS, null=True, blank=True)
	date_expiration_permis = models.DateField(null=True, blank=True)
	statut = models.CharField(max_length=10, choices=STATUT, default='ACTIF')
	photo = models.ImageField(upload_to='conducteurs/', null=True, blank=True)
	bus = models.OneToOneField('trips.Bus', on_delete=models.SET_NULL, null=True, blank=True, related_name='conducteur')

	class Meta:
		verbose_name = 'Conducteur'
		verbose_name_plural = 'Conducteurs'

	def __str__(self):
		return f"{self.prenom} {self.nom}"

	@property
	def permis_valide(self):
		if not self.date_expiration_permis:
			return False
		return self.date_expiration_permis >= timezone.now().date()

	@property
	def disponible(self):
		# Simple check: disponible si statut ACTIF (affectations gérées ailleurs)
		return self.statut == 'ACTIF'


class AffectationConducteur(models.Model):
	ROLE = [
		('PRINCIPAL', 'Principal'),
		('REMPLACANT', 'Remplaçant'),
	]

	departure = models.ForeignKey('trips.Depart', on_delete=models.CASCADE, related_name='affectations_conducteurs')
	conducteur = models.ForeignKey(Conducteur, on_delete=models.CASCADE, related_name='affectations')
	role = models.CharField(max_length=12, choices=ROLE, default='PRINCIPAL')

	class Meta:
		verbose_name = 'Affectation Conducteur'
		verbose_name_plural = 'Affectations Conducteurs'

	def __str__(self):
		return f"{self.departure} - {self.conducteur} ({self.role})"



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


class PolitiqueReservation(models.Model):
	"""Singleton model to store reservation policy settings."""
	delai_max_avant_depart = models.PositiveIntegerField(default=90, help_text='Nombre de jours maximum avant le départ pour réserver')
	delai_min_avant_depart = models.PositiveIntegerField(default=2, help_text='Nombre d\'heures minimum avant le départ pour réserver')
	places_max_par_reservation = models.PositiveIntegerField(default=10)
	reservations_max_par_client = models.PositiveIntegerField(default=5)
	annulation_gratuite_heures = models.PositiveIntegerField(default=24)
	penalite_annulation_pct = models.PositiveIntegerField(default=20)
	delai_paiement_minutes = models.PositiveIntegerField(default=30)
	active = models.BooleanField(default=True)

	class Meta:
		verbose_name = 'Politique de réservation'
		verbose_name_plural = 'Politiques de réservation'

	def __str__(self):
		return f"Politique (active={self.active})"

	@classmethod
	def get_active(cls):
		obj = cls.objects.filter(active=True).first()
		if obj:
			return obj
		# create default policy if none
		return cls.objects.create()

