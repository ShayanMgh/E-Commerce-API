import logging
from rest_framework import permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import SignupSerializer, UserSerializer

log = logging.getLogger("users.api")

class SignupView(generics.CreateAPIView):
    """
    Public signup endpoint.
    Logs new registrations at INFO level.
    """
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        log.info("Signup user=email=%s id=%s", user.email, user.id)

class MeView(APIView):
    """
    Return current authenticated user profile.
    """
    def get(self, request):
        log.debug("Profile fetch user_id=%s", request.user.id)
        return Response(UserSerializer(request.user).data)

class LoginView(TokenObtainPairView):
    """
    JWT login (obtain tokens). Adds simple INFO log on success.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            log.info("Issued JWT user_email=%s", request.data.get("email") or request.data.get("username"))
        else:
            log.warning("JWT issue failed status=%s", response.status_code)
        return response

class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
