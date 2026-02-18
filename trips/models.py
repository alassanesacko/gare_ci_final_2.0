from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Bus(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Trip(models.Model):
    origin = models.CharField(max_length=100)       # Ville de départ
    destination = models.CharField(max_length=100)  # Ville d'arrivée
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Prix du trajet

    def __str__(self):
        return f"{self.origin} \u2192 {self.destination}"

class Departure(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def get_remaining_seats(self):
        """Calcule le nombre de places restantes pour ce départ."""
        total_seats = self.bus.capacity
        booked_seats = self.reservation_set.filter(status__in=['P', 'C']).count()  # Compte les réservations en attente et confirmées
        return total_seats - booked_seats
    
    def get_next_seat_number(self):
        """Génère le prochain numéro de siège disponible (numéro simple)."""
        booked_count = self.reservation_set.filter(status__in=['P', 'C']).count()
        # Vérifier que le numéro de siège ne dépasse pas la capacité du bus
        if booked_count >= self.bus.capacity:
            return None  # Aucune place disponible
        # Retourner le prochain numéro simple (1, 2, 3, 4, ...)
        return str(booked_count + 1)

    def __str__(self):
        return f"{self.trip.origin} → {self.trip.destination} ({self.date} {self.time})"

    class Meta:
        ordering = ['date', 'time']  # Tri par défaut par date puis heure
