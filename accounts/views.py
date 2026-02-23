from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.urls import reverse
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from reservations.models import Reservation, ReservationStatus

from .forms import CustomUserCreationForm, EmailOrUsernameAuthenticationForm, ProfileEditForm
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from reservations.views import contact as reservations_contact


def _style_password_form(password_form):
    for field in password_form.fields.values():
        css = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = (css + " form-control").strip()
    return password_form


def signup(request):
    """Inscription d'un nouveau client."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Inscription reussie! Vous pouvez maintenant vous connecter.")
                return redirect('accounts:login')
            except IntegrityError as e:
                if 'username' in str(e):
                    messages.error(request, "Ce nom d'utilisateur est deja utilise.")
                elif 'email' in str(e):
                    messages.error(request, "Cet email est deja utilise.")
                else:
                    messages.error(request, "Une erreur est survenue lors de l'inscription. Veuillez reessayer.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


class CustomLoginRedirectView(LoginView):
    """Vue de connexion avec redirection selon le role."""

    template_name = 'accounts/login.html'
    authentication_form = EmailOrUsernameAuthenticationForm

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse('dashboard:index')
        return reverse('trips:home')


class CustomLogoutView(LogoutView):
    next_page = 'trips:home'


@login_required
def profile(request):
    confirmed = Reservation.objects.filter(
        user=request.user,
        status=ReservationStatus.CONFIRMEE,
    )
    nb_voyages = confirmed.count()
    total_depense = confirmed.aggregate(total=Sum("prix_total"))["total"] or 0
    nb_villes = confirmed.values("departure__trip__arret_arrivee__ville").distinct().count()

    context = {
        "active_tab": "profile",
        "nb_voyages": nb_voyages,
        "total_depense": total_depense,
        "nb_villes": nb_villes,
        "edit_form": ProfileEditForm(instance=request.user),
        "password_form": _style_password_form(PasswordChangeForm(user=request.user)),
    }
    return render(request, "accounts/profile.html", context)


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis a jour avec succes.")
            return redirect("accounts:profile")
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = ProfileEditForm(instance=request.user)

    confirmed = Reservation.objects.filter(
        user=request.user,
        status=ReservationStatus.CONFIRMEE,
    )
    context = {
        "active_tab": "profile",
        "nb_voyages": confirmed.count(),
        "total_depense": confirmed.aggregate(total=Sum("prix_total"))["total"] or 0,
        "nb_villes": confirmed.values("departure__trip__arret_arrivee__ville").distinct().count(),
        "edit_form": form,
        "password_form": _style_password_form(PasswordChangeForm(user=request.user)),
    }
    return render(request, "accounts/profile.html", context)


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Mot de passe modifie avec succes.")
            return redirect("accounts:profile")
        messages.error(request, "Impossible de modifier le mot de passe. Verifiez les champs.")
    else:
        form = PasswordChangeForm(user=request.user)

    confirmed = Reservation.objects.filter(
        user=request.user,
        status=ReservationStatus.CONFIRMEE,
    )
    context = {
        "active_tab": "profile",
        "nb_voyages": confirmed.count(),
        "total_depense": confirmed.aggregate(total=Sum("prix_total"))["total"] or 0,
        "nb_villes": confirmed.values("departure__trip__arret_arrivee__ville").distinct().count(),
        "edit_form": ProfileEditForm(instance=request.user),
        "password_form": _style_password_form(form),
    }
    return render(request, "accounts/profile.html", context)


def contact(request):
    return reservations_contact(request)
