from django.db import models


class Network(models.Model):
    name = models.CharField("Название сети", max_length=120, unique=True)

    class Meta:
        verbose_name = "Сеть"
        verbose_name_plural = "Сети"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Point(models.Model):
    """Точка сети — конкретное кафе."""
    network = models.ForeignKey(
        Network,
        on_delete=models.CASCADE,
        related_name="points",
        verbose_name="Сеть",
    )
    name = models.CharField("Название", max_length=120)
    city = models.CharField("Город", max_length=80, db_index=True, default="Воронеж")
    address = models.CharField("Адрес", max_length=255)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    is_active = models.BooleanField("Доступна для брони", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Точка"
        verbose_name_plural = "Точки"
        ordering = ["city", "name"]

    def __str__(self):
        return f"{self.name} ({self.city})"

class Table(models.Model):
    """Столик в точке. US-G04: выбор столика с учётом занятости."""
    point = models.ForeignKey(
        Point, on_delete=models.CASCADE, related_name="tables", verbose_name="Точка"
    )
    name = models.CharField("Название/номер", max_length=50)
    seats = models.PositiveIntegerField("Мест", default=2)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Столик"
        verbose_name_plural = "Столики"
        ordering = ["point", "name"]
        unique_together = [("point", "name")]

    def __str__(self):
        return f"{self.point.name} / {self.name} ({self.seats} мест)"