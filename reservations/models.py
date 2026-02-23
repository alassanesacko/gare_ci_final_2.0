import io
import random
import string
import uuid

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone

from trips.models import Bus, Depart


class ReservationStatus(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", "En attente"
    CONFIRMEE = "CONFIRMEE", "Confirmee"
    ANNULEE = "ANNULEE", "Annulee"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    reply = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)


class Reservation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    depart = models.ForeignKey(
        Depart,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    date_voyage = models.DateField(help_text="Date choisie par le client pour voyager")
    ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=25,
        choices=ReservationStatus.choices,
        default=ReservationStatus.EN_ATTENTE,
    )
    booked_at = models.DateTimeField(auto_now_add=True)
    seat_number = models.CharField(max_length=10, blank=True, null=True, verbose_name="Numero de siege")
    reference = models.CharField(max_length=12, unique=True, blank=True)
    nombre_places = models.PositiveSmallIntegerField(default=1)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Reservation #{self.id} - {self.depart}"

    @property
    def heure_depart(self):
        return self.depart.heure_depart

    @property
    def heure_arrivee(self):
        return self.depart.heure_arrivee

    @property
    def trip(self):
        return self.depart.trip

    @property
    def datetime_depart(self):
        from datetime import datetime

        return timezone.make_aware(datetime.combine(self.date_voyage, self.depart.heure_depart))

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)

    def generate_reference(self):
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=12))

    def confirmer(self):
        self.status = ReservationStatus.CONFIRMEE
        self.save()

    def annuler(self):
        self.status = ReservationStatus.ANNULEE
        self.save()


class Ticket(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    num_seiges = models.PositiveIntegerField(default=1)
    prix = models.DecimalField(max_digits=8, decimal_places=2)
    code_qr_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    code_qr = models.ImageField(upload_to="qrcodes/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.user} - {self.bus}"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.code_qr:
            qr_data = str(self.code_qr_uuid)
            img = qrcode.make(qr_data)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            filename = f"ticket_{self.code_qr_uuid}.png"
            self.code_qr.save(filename, ContentFile(buffer.getvalue()), save=False)
            buffer.close()
            super().save(update_fields=["code_qr"])


class Paiement(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        REUSSI = "REUSSI", "Reussi"
        ECHOUE = "ECHOUE", "Echoue"
        ANNULE = "ANNULE", "Annule"

    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name="paiement")
    montant = models.DecimalField(max_digits=8, decimal_places=2)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    reference_paiement = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.reference_paiement:
            self.reference_paiement = "PAY-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)
