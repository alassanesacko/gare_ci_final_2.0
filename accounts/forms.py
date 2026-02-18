
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """Formulaire de création d'un nouvel utilisateur."""
    email = forms.EmailField(required=True, label="Adresse email")
    phone = forms.CharField(max_length=20, required=False, label="Numéro de téléphone (optionnel)")
    first_name = forms.CharField(max_length=30, required=True, label="Prénom")
    last_name = forms.CharField(max_length=150, required=True, label="Nom de famille")
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'password1', 'password2']
    
    def clean_username(self):
        """Valide que le nom d'utilisateur n'existe pas déjà."""
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError(
                "Ce nom d'utilisateur est déjà utilisé. Veuillez en choisir un autre.",
                code='username_exists'
            )
        return username
    
    def clean_email(self):
        """Valide que l'email n'existe pas déjà."""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(
                "Cet email est déjà associé à un compte. Veuillez en utiliser un autre ou vous connecter.",
                code='email_exists'
            )
        return email

class CustomUserChangeForm(UserChangeForm):
    """Formulaire de modification de l'utilisateur."""
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'first_name', 'last_name', 'is_active', 'is_staff']
