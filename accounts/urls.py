from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('register/', views.signup, name='register'),
    path('login/', views.CustomLoginRedirectView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/password/', views.change_password, name='change_password'),
    path('contact/', views.contact, name='contact'),
]
