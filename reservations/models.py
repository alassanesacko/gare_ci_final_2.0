from django.db import models
from django.conf import settings
from trips.models import Departure, Bus
import uuid
import io
import qrcode
from django.core.files.base import ContentFile
from django.utils import timezone
import string
import random


class ReservationStatus(models.TextChoices):
    EN_ATTENTE_VALIDATION = 'EN_ATTENTE_VALIDATION', 'En attente de validation'
    VALIDEE = 'VALIDEE', 'Validée'
    CONFIRMEE = 'CONFIRMEE', 'Confirmée'
    REJETEE = 'REJETEE', 'Rejetée'
    ANNULEE = 'ANNULEE', 'Annulée'
    EXPIREE = 'EXPIREE', 'Expirée'


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    reply = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)

    

class Reservation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    departure = models.ForeignKey(Departure, on_delete=models.CASCADE)
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE)
    status = models.CharField(max_length=25, choices=ReservationStatus.choices, default=ReservationStatus.EN_ATTENTE_VALIDATION)
    booked_at = models.DateTimeField(auto_now_add=True)
    seat_number = models.CharField(max_length=10, blank=True, null=True, verbose_name="Numéro de siège")
    reference = models.CharField(max_length=12, unique=True, blank=True)
    nombre_places = models.PositiveSmallIntegerField(default=1)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2)
    expires_at = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)
    validee_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_reservations')
    validee_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Réservation #{self.id} - {self.departure}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)

    def generate_reference(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

    @property
    def est_expiree(self):
        return timezone.now() > self.expires_at

    def valider(self, admin_user):
        self.status = ReservationStatus.VALIDEE
        self.validee_par = admin_user
        self.validee_at = timezone.now()
        self.save()
        # Notifier le client par email
        # send_email(self.user.email, 'Réservation validée', ...)

    def rejeter(self, admin_user, motif):
        self.status = ReservationStatus.REJETEE
        self.validee_par = admin_user
        self.validee_at = timezone.now()
        self.motif_rejet = motif
        self.save()
        # Remettre les places disponibles
        self.departure.places_disponibles += self.nombre_places
        self.departure.save()
        # Notifier le client

    def confirmer(self):
        self.status = ReservationStatus.CONFIRMEE
        self.save()
        # Après paiement Stripe

    def annuler(self):
        self.status = ReservationStatus.ANNULEE
        self.save()
        # Remettre les places
        self.departure.places_disponibles += self.nombre_places
        self.departure.save()
        # Notifier le client


class Ticket(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    num_seiges = models.PositiveIntegerField(default=1)
    prix = models.DecimalField(max_digits=8, decimal_places=2)
    code_qr_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    code_qr = models.ImageField(upload_to='qrcodes/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.user} - {self.bus}"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.code_qr:
            # generate QR code image from UUID
            qr_data = str(self.code_qr_uuid)
            img = qrcode.make(qr_data)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            filename = f"ticket_{self.code_qr_uuid}.png"
            self.code_qr.save(filename, ContentFile(buffer.getvalue()), save=False)
            buffer.close()
            super().save(update_fields=['code_qr'])


class Paiement(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        REUSSI = 'REUSSI', 'Réussi'
        ECHOUE = 'ECHOUE', 'Échoué'
        ANNULE = 'ANNULE', 'Annulé'

    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='paiement')
    montant = models.DecimalField(max_digits=8, decimal_places=2)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    reference_paiement = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.reference_paiement:
            import random, string
            self.reference_paiement = 'PAY-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)
