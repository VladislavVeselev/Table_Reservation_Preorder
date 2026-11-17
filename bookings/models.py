from django.conf import settings
from django.db import models

from points.models import Point, Table


class Booking(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Ожидает подтверждения"),
        (STATUS_CONFIRMED, "Подтверждена"),
        (STATUS_REJECTED, "Отклонена"),
        (STATUS_CANCELLED, "Отменена"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Гость",
    )
    point = models.ForeignKey(
        Point, on_delete=models.PROTECT, related_name="bookings", verbose_name="Точка"
    )
    table = models.ForeignKey(
        Table, on_delete=models.PROTECT, related_name="bookings", verbose_name="Столик"
    )
    date = models.DateField("Дата")
    start_time = models.TimeField("Время начала")
    end_time = models.TimeField("Время окончания")
    status = models.CharField(
        "Статус", max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Бронь"
        verbose_name_plural = "Брони"
        ordering = ["-date", "-start_time"]
        indexes = [models.Index(fields=["table", "date"])]

    def __str__(self):
        return f"{self.table} — {self.date} {self.start_time:%H:%M}-{self.end_time:%H:%M}"