from rest_framework.permissions import BasePermission

from .models import Profile


class IsPointAdmin(BasePermission):
    """US-A01: только администратор точки, и только со своей точкой."""
    message = "Доступно только администратору точки"

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == Profile.ROLE_POINT_ADMIN
            and request.user.profile.point_id is not None
        )


class IsNetworkManager(BasePermission):
    """US-M01: только менеджер сети, и только со своей сетью."""
    message = "Доступно только менеджеру сети"

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == Profile.ROLE_NETWORK_MANAGER
            and request.user.profile.network_id is not None
        )