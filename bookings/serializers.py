from datetime import datetime, time, timedelta

from django.utils import timezone
from rest_framework import serializers

from points.models import Point, Table

from .constants import (
    BOOKING_DURATION_HOURS,
    CLOSE_HOUR,
    OPEN_HOUR,
    TIME_STEP_HOURS,
)
from .models import Booking


class BookingReadSerializer(serializers.ModelSerializer):
    point_name = serializers.CharField(source="point.name", read_only=True)
    point_address = serializers.CharField(source="point.address", read_only=True)
    table_name = serializers.CharField(source="table.name", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "user_username",
            "point", "point_name", "point_address",
            "table", "table_name",
            "date", "start_time", "end_time",
            "status", "status_display", "created_at",
        ]


class BookingCreateSerializer(serializers.Serializer):
    """US-G05: создание брони. US-G06: проверка занятости — во вьюхе."""
    point = serializers.IntegerField()
    table = serializers.IntegerField()
    date = serializers.DateField()
    time = serializers.TimeField(format="%H:%M")

    def validate_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("Нельзя бронировать на прошедшую дату")
        return value

    def validate_point(self, value):
        if not Point.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError("Точка не найдена или недоступна")
        return value

    def validate_table(self, value):
        if not Table.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError("Столик не найден или недоступен")
        return value

    def validate(self, attrs):
        # ---- шаг времени ----
        t = attrs["time"]
        if t.minute != 0:
            raise serializers.ValidationError(
                {"time": f"Время должно быть кратно {TIME_STEP_HOURS} часу (минуты = 00)"}
            )

        # ---- рабочие часы ----
        start_dt = datetime.combine(attrs["date"], t)
        end_dt = start_dt + timedelta(hours=BOOKING_DURATION_HOURS)
        open_dt = datetime.combine(attrs["date"], time(OPEN_HOUR, 0))
        close_dt = datetime.combine(attrs["date"], time(CLOSE_HOUR, 0))
        if start_dt < open_dt or end_dt > close_dt:
            raise serializers.ValidationError(
                {"time": f"Бронирование возможно с {OPEN_HOUR}:00 до {CLOSE_HOUR}:00 "
                         f"(длительность {BOOKING_DURATION_HOURS} ч)"}
            )
        attrs["end_time"] = end_dt.time()

        # ---- столик принадлежит выбранной точке ----
        table = Table.objects.filter(pk=attrs["table"]).select_related("point").first()
        if table and table.point_id != attrs["point"]:
            raise serializers.ValidationError(
                {"table": "Столик не принадлежит выбранной точке"}
            )
        return attrs