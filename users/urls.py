from django.urls import path
from .views import SignupView, MeView, LoginView, RefreshView

urlpatterns = [
    path("auth/signup", SignupView.as_view(), name="signup"),
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/refresh", RefreshView.as_view(), name="token_refresh"),
    path("me", MeView.as_view(), name="me"),
]
