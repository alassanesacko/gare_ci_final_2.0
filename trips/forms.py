
from django import forms

class TripSearchForm(forms.Form):
    origin = forms.CharField(label='Ville de départ', max_length=100, required=False)
    destination = forms.CharField(label='Ville d\'arrivée', max_length=100, required=False)
    date = forms.DateField(label='Date', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
