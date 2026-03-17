"""Authentication views: JWT login/refresh, profile, password change."""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.serializers.auth import (
    ChangePasswordSerializer,
    MeResponseSerializer,
    UserProfileSerializer,
)


class LoginView(TokenObtainPairView):
    """Obtain JWT access + refresh tokens.

    Returns tokens along with user profile and default tenant info.
    """

    permission_classes = (AllowAny,)


class RefreshView(TokenRefreshView):
    """Refresh an expired access token using a valid refresh token."""

    permission_classes = (AllowAny,)


class MeView(APIView):
    """Current user profile with tenant context.

    GET  — return user, current tenant, and all memberships.
    PATCH — update editable profile fields (email, first/last name).
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        data = {"user": request.user}
        serializer = MeResponseSerializer(data, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Password updated."}, status=status.HTTP_200_OK)
