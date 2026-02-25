from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Formulaire de creation d'un nouvel utilisateur."""

    email = forms.EmailField(required=True, label="Adresse email")
    nom_prenom = forms.CharField(
        max_length=255,
        required=True,
        label="Nom et prenom",
        help_text="Exemple: Kouassi Jean",
    )

    class Meta:
        model = CustomUser
        fields = ["email", "username", "nom_prenom", "password1", "password2"]

    def clean_username(self):
        """Valide que le nom d'utilisateur n'existe pas deja."""
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError(
                "Ce nom d'utilisateur est deja utilise. Veuillez en choisir un autre.",
                code="username_exists",
            )
        return username

    def clean_email(self):
        """Valide que l'email n'existe pas deja."""
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(
                "Cet email est deja associe a un compte. Veuillez en utiliser un autre ou vous connecter.",
                code="email_exists",
            )
        return email

    def clean_nom_prenom(self):
        nom_prenom = " ".join(self.cleaned_data.get("nom_prenom", "").split())
        if len(nom_prenom.split()) < 2:
            raise ValidationError("Saisissez au moins un nom et un prenom.")
        return nom_prenom.upper()

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data["nom_prenom"].strip()
        parts = full_name.split()
        user.last_name = parts[0]
        user.first_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """Formulaire de modification de l'utilisateur."""

    class Meta:
        model = CustomUser
        fields = ["username", "email", "phone", "first_name", "last_name", "is_active", "is_staff"]


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Nom d'utilisateur ou email",
        widget=forms.TextInput(attrs={"autofocus": True}),
    )

    def clean(self):
        identifier = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if identifier and password:
            login_username = identifier
            if "@" in identifier:
                UserModel = get_user_model()
                matched_username = (
                    UserModel.objects.filter(email__iexact=identifier)
                    .values_list("username", flat=True)
                    .first()
                )
                if matched_username:
                    login_username = matched_username

            self.user_cache = authenticate(
                self.request,
                username=login_username,
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "phone", "email"]
        labels = {
            "first_name": "Prenom",
            "last_name": "Nom",
            "phone": "Telephone",
            "email": "Email",
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return email
        qs = CustomUser.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Cet email est deja utilise par un autre compte.")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " form-control").strip()
