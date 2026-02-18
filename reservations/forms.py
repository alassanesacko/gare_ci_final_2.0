
from django import forms
from .models import ContactMessage, Reservation

class ContactForm(forms.ModelForm):
    """Formulaire de contact (section Contact)."""
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
