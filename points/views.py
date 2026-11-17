from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsNetworkManager, IsPointAdmin
from datetime import datetime, timedelta
from accounts.permissions import IsPointAdmin

from rest_framework.response import Response
from rest_framework.views import APIView
from bookings.constants import BOOKING_DURATION_HOURS
from bookings.models import Booking
from .serializers import NetworkWithPointsSerializer
from .models import Point
from .serializers import PointSerializer


class PointListView(generics.ListAPIView):
    serializer_class = PointSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Point.objects.filter(is_active=True).select_related("network")


class PointDetailView(generics.RetrieveAPIView):
    serializer_class = PointSerializer
    permission_classes = [IsAuthenticated]
    queryset = Point.objects.filter(is_active=True).select_related("network")


class MyPointView(generics.RetrieveAPIView):
    """US-A01: администратор точки видит только свою точку."""
    serializer_class = PointSerializer
    permission_classes = [IsPointAdmin]

    def get_object(self):
        return self.request.user.profile.point


class MyNetworkView(generics.RetrieveAPIView):
    """US-M01: менеджер сети видит только свою сеть (и её активные точки)."""
    serializer_class = NetworkWithPointsSerializer
    permission_classes = [IsNetworkManager]

    def get_object(self):
        return self.request.user.profile.network


class PointTablesView(generics.ListAPIView):
    """
    US-G04: столики точки + флаг is_available на запрошенные date/time.
    Без параметров — просто список столиков (is_available = null).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None  # переопределим get

    def get(self, request, pk):
        point = Point.objects.filter(pk=pk, is_active=True).first()
        if not point:
            return Response({"detail": "Точка не найдена"}, status=404)

        date_str = request.query_params.get("date")
        time_str = request.query_params.get("time")

        tables = point.tables.filter(is_active=True)

        result = []
        if date_str and time_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                start = datetime.strptime(time_str, "%H:%M").time()
                end_dt = datetime.combine(date, start) + timedelta(hours=BOOKING_DURATION_HOURS)
                end = end_dt.time()
            except ValueError:
                return Response(
                    {"detail": "Ожидается date=YYYY-MM-DD и time=HH:MM"},
                    status=400,
                )
            busy_table_ids = set(
                Booking.objects.filter(
                    table__point=point,
                    date=date,
                    status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
                    start_time__lt=end,
                    end_time__gt=start,
                ).values_list("table_id", flat=True)
            )
            for t in tables:
                result.append({
                    "id": t.id, "name": t.name, "seats": t.seats,
                    "is_available": t.id not in busy_table_ids,
                })
        else:
            for t in tables:
                result.append({
                    "id": t.id, "name": t.name, "seats": t.seats,
                    "is_available": None,
                })
        return Response(result)

class MyPointTablesView(APIView):
    """
    US-A04: администратор точки видит схему зала — список столиков своей точки
    с индикацией занятости на выбранные date/time и информацией о том, кто занял.
    """
    permission_classes = [IsPointAdmin]

    def get(self, request):
        point = request.user.profile.point
        tables = point.tables.filter(is_active=True).order_by("name")

        date_str = request.query_params.get("date")
        time_str = request.query_params.get("time")

        # Если параметры не переданы — отдаём просто список без занятости
        if not (date_str and time_str):
            return Response([
                {
                    "id": t.id, "name": t.name, "seats": t.seats,
                    "is_available": None, "busy_booking": None,
                }
                for t in tables
            ])

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start = datetime.strptime(time_str, "%H:%M").time()
            end_dt = datetime.combine(date, start) + timedelta(hours=BOOKING_DURATION_HOURS)
            end = end_dt.time()
        except ValueError:
            return Response(
                {"detail": "Ожидается date=YYYY-MM-DD и time=HH:MM"},
                status=400,
            )

        # Все активные брони точки на этот интервал — одним запросом
        active_bookings = (
            Booking.objects.filter(
                point=point,
                date=date,
                status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
                start_time__lt=end,
                end_time__gt=start,
            )
            .select_related("user", "table")
        )
        busy_by_table = {b.table_id: b for b in active_bookings}

        result = []
        for t in tables:
            busy = busy_by_table.get(t.id)
            if busy:
                result.append({
                    "id": t.id, "name": t.name, "seats": t.seats,
                    "is_available": False,
                    "busy_booking": {
                        "id": busy.id,
                        "user_username": busy.user.username,
                        "start_time": busy.start_time.strftime("%H:%M"),
                        "end_time": busy.end_time.strftime("%H:%M"),
                        "status": busy.status,
                        "status_display": busy.get_status_display(),
                    },
                })
            else:
                result.append({
                    "id": t.id, "name": t.name, "seats": t.seats,
                    "is_available": True,
                    "busy_booking": None,
                })
        return Response(result)