from django.conf import settings
from django.db import models


class Profile(models.Model):
    ROLE_GUEST = "guest"
    ROLE_POINT_ADMIN = "point_admin"
    ROLE_NETWORK_MANAGER = "network_manager"
    ROLE_CHOICES = [
        (ROLE_GUEST, "Гость"),
        (ROLE_POINT_ADMIN, "Администратор точки"),
        (ROLE_NETWORK_MANAGER, "Менеджер сети"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default=ROLE_GUEST)
    phone = models.CharField(max_length=20, blank=True)

    point = models.ForeignKey(
        "points.Point",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="admins",
        verbose_name="Точка (для администратора точки)",
    )
    network = models.ForeignKey(
        "points.Network",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="managers",
        verbose_name="Сеть (для менеджера сети)",
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"