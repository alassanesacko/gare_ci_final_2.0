from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse
from django.db import IntegrityError
from .forms import CustomUserCreationForm
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

def signup(request):
    """Inscription d'un nouveau client."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, "Inscription réussie! Vous pouvez maintenant vous connecter.")
                return redirect('accounts:login')
            except IntegrityError as e:
                # Gère les erreurs de contrainte unique (nom d'utilisateur ou email duplicé)
                if 'username' in str(e):
                    messages.error(request, "Ce nom d'utilisateur est déjà utilisé.")
                elif 'email' in str(e):
                    messages.error(request, "Cet email est déjà utilisé.")
                else:
                    messages.error(request, "Une erreur est survenue lors de l'inscription. Veuillez réessayer.")
        else:
            # Les erreurs du formulaire sont automatiquement affichées dans le template
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

class CustomLoginRedirectView(LoginView):
    """
    Vue de connexion : redirige automatiquement vers l'accueil (client) ou le dashboard (staff).
    """
    template_name = 'accounts/login.html'
    
    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_success_url(self):
        # Si l'utilisateur est staff, redirige vers le tableau de bord admin
        if self.request.user.is_staff:
            return reverse('dashboard:index')
        # Sinon (client), on renvoie vers la page d'accueil publique
        return reverse('trips:home')

class CustomLogoutView(LogoutView):
    next_page = 'trips:home'  # après déconnexion, retourne à l'accueil public
