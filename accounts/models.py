
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé. Hérite de AbstractUser (nom d'utilisateur, email, etc.).
    """
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Numéro de téléphone")
    
    def __str__(self):
        return self.username
