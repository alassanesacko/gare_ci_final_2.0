from django.db import models
from django.conf import settings
from trips.models import Departure, Bus
import uuid
import io
import qrcode
from django.core.files.base import ContentFile

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    reply = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)

    

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('P', 'En attente'),
        ('C', 'Confirmée'),
        ('X', 'Annulée'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    departure = models.ForeignKey(Departure, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    booked_at = models.DateTimeField(auto_now_add=True)
    seat_number = models.CharField(max_length=10, blank=True, null=True, verbose_name="Numéro de siège")

    def __str__(self):
        return f"Réservation #{self.id} - {self.departure}"


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
