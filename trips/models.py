from django.db import models
from django.utils import timezone


class Category(models.Model):
    class Niveau(models.TextChoices):
        ECONOMIQUE = "ECONOMIQUE", "Economique"
        CONFORT = "CONFORT", "Confort"
        VIP = "VIP", "VIP"
        NUIT = "NUIT", "Nuit"

    # Legacy column still present in DB.
    name = models.CharField(max_length=100, blank=True, default="")
    nom = models.CharField(max_length=100)
    niveau = models.CharField(max_length=20, choices=Niveau.choices, default=Niveau.ECONOMIQUE)
    prix_multiplicateur = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    a_wifi = models.BooleanField(default=False)
    a_climatisation = models.BooleanField(default=False)
    a_prise_usb = models.BooleanField(default=False)
    a_wc = models.BooleanField(default=False)
    a_repas = models.BooleanField(default=False)
    a_couchette = models.BooleanField(default=False)

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.nom and self.name:
            self.nom = self.name
        if not self.name and self.nom:
            self.name = self.nom
        super().save(*args, **kwargs)


class Bus(models.Model):
    # Legacy columns still present in DB.
    name = models.CharField(max_length=100, blank=True, default="")
    capacity = models.PositiveIntegerField(default=0)
    immatriculation = models.CharField(max_length=50, unique=True)
    modele = models.CharField(max_length=150, blank=True)
    capacite = models.PositiveIntegerField()
    categorie = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="buses")
    annee_fabrication = models.PositiveIntegerField(null=True, blank=True)
    en_service = models.BooleanField(default=True)
    photo = models.ImageField(upload_to="buses/", null=True, blank=True)
    derniere_revision = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.immatriculation

    def save(self, *args, **kwargs):
        if not self.immatriculation and self.name:
            self.immatriculation = self.name
        if not self.name and self.immatriculation:
            self.name = self.immatriculation
        if not self.capacite and self.capacity:
            self.capacite = self.capacity
        if not self.capacity and self.capacite:
            self.capacity = self.capacite
        super().save(*args, **kwargs)


class Ville(models.Model):
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.nom


class Arret(models.Model):
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.nom} - {self.ville.nom}"


class Segment(models.Model):
    arret_depart = models.ForeignKey(Arret, on_delete=models.CASCADE, related_name="segments_depart")
    arret_arrivee = models.ForeignKey(Arret, on_delete=models.CASCADE, related_name="segments_arrivee")
    distance_km = models.DecimalField(max_digits=10, decimal_places=2)
    duree_minutes = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.arret_depart} -> {self.arret_arrivee}"


def get_default_category_pk():
    category, _ = Category.objects.get_or_create(
        nom="Standard",
        defaults={"name": "Standard"},
    )
    return category.pk


class Trip(models.Model):
    nom = models.CharField(max_length=100)
    # Legacy columns still present in DB schema; keep mapped to avoid insert failures.
    origin = models.CharField(max_length=100, blank=True, default="")
    destination = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="legacy_trips",
        default=get_default_category_pk,
    )
    ville_depart = models.ForeignKey(Ville, on_delete=models.CASCADE, related_name="trips_depart")
    ville_arrivee = models.ForeignKey(Ville, on_delete=models.CASCADE, related_name="trips_arrivee")
    arret_depart = models.ForeignKey(Arret, on_delete=models.CASCADE, related_name="trips_depart")
    arret_arrivee = models.ForeignKey(Arret, on_delete=models.CASCADE, related_name="trips_arrivee")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actif = models.BooleanField(default=True)

    @property
    def est_direct(self):
        return self.etapetrajet_set.count() == 1

    @property
    def duree_totale(self):
        total = 0
        for etape in self.etapetrajet_set.order_by("ordre"):
            total += etape.segment.duree_minutes
        return total

    def __str__(self):
        return self.nom


class EtapeTrajet(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE)
    ordre = models.PositiveIntegerField()

    class Meta:
        ordering = ["ordre"]
        unique_together = ("trip", "ordre")

    def __str__(self):
        return f"{self.trip.nom} - Etape {self.ordre}"


class Departure(models.Model):
    # Legacy columns still present in DB schema.
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    date_depart = models.DateTimeField()
    date_arrivee_estimee = models.DateTimeField()
    places_disponibles = models.PositiveIntegerField()
    actif = models.BooleanField(default=True)

    def get_remaining_seats(self):
        total_seats = self.bus.capacite
        booked_seats = self.reservation_set.filter(status__in=["EN_ATTENTE_VALIDATION", "VALIDEE", "CONFIRMEE"]).count()
        return total_seats - booked_seats

    def get_next_seat_number(self):
        booked_count = self.reservation_set.filter(status__in=["EN_ATTENTE_VALIDATION", "VALIDEE", "CONFIRMEE"]).count()
        if booked_count >= self.bus.capacite:
            return None
        return str(booked_count + 1)

    def __str__(self):
        return f"{self.trip.nom} ({self.date_depart})"

    def save(self, *args, **kwargs):
        if self.date_depart:
            local_departure = timezone.localtime(self.date_depart) if timezone.is_aware(self.date_depart) else self.date_depart
            self.date = local_departure.date()
            self.time = local_departure.time().replace(microsecond=0)

        self.is_active = bool(self.actif)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["date_depart"]
