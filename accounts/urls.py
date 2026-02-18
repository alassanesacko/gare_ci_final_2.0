
from django.urls import path
from .views import signup, CustomLoginRedirectView, CustomLogoutView

app_name = 'accounts'
urlpatterns = [
    path('register/', signup, name='register'),
    path('login/', CustomLoginRedirectView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]
