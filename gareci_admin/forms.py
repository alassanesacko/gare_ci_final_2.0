from django import forms
from reservations.models import ContactMessage

class ContactReplyForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['reply']
        labels = {
            'reply': 'Réponse à envoyer au client',
        }
        widgets = {
            'reply': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Votre réponse...'}),
        }
