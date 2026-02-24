from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]


class ReservationForm(forms.Form):
    nombre_places = forms.ChoiceField(
        choices=[(i, f"{i} place{'s' if i > 1 else ''}") for i in range(1, 6)],
        initial=1,
        label="Nombre de places",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, places_disponibles=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.places_disponibles = places_disponibles
        if places_disponibles is not None and places_disponibles < 5:
            # Limiter les choix au nombre de places disponibles
            self.fields["nombre_places"].choices = [
                (i, f"{i} place{'s' if i > 1 else ''}")
                for i in range(1, min(places_disponibles + 1, 6))
            ]
        # Remove label since we display it in template
        self.fields["nombre_places"].label = ""

    def clean_nombre_places(self):
        n = int(self.cleaned_data["nombre_places"])
        if self.places_disponibles is not None and n > self.places_disponibles:
            raise forms.ValidationError(
                f"Seulement {self.places_disponibles} place(s) disponible(s)."
            )
        return n
