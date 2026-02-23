from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]


class ReservationForm(forms.Form):
    nombre_places = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        label="Nombre de places",
    )

    def __init__(self, *args, places_disponibles=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.places_disponibles = places_disponibles
        if places_disponibles is not None:
            self.fields["nombre_places"].widget.attrs.update({
                "max": places_disponibles,
                "min": 1,
            })

    def clean_nombre_places(self):
        n = self.cleaned_data["nombre_places"]
        if self.places_disponibles is not None and n > self.places_disponibles:
            raise forms.ValidationError(
                f"Seulement {self.places_disponibles} place(s) disponible(s)."
            )
        return n
