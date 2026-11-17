from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsPointAdmin
from points.models import Point, Table

from .models import Booking
from .serializers import BookingCreateSerializer, BookingReadSerializer
from .services import create_booking_atomic


class BookingListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """US-G07: мои брони."""
        qs = Booking.objects.filter(user=request.user).select_related("point", "table")
        return Response(BookingReadSerializer(qs, many=True).data)

    def post(self, request):
        """US-G05 + US-G06."""
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        point = Point.objects.get(pk=data["point"])
        table = Table.objects.select_related("point").get(pk=data["table"])

        booking, error = create_booking_atomic(
            user=request.user, point=point, table=table,
            date=data["date"], start_time=data["time"], end_time=data["end_time"],
        )
        if error == "busy":
            return Response(
                {"detail": "Этот столик уже занят на выбранное время",
                 "code": "table_busy"},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            BookingReadSerializer(booking).data,
            status=status.HTTP_201_CREATED,
        )


# ============ АДМИН ТОЧКИ (US-A02 / US-A03) ============

class PointBookingsView(APIView):
    """US-A02: админ точки видит брони только своей точки."""
    permission_classes = [IsPointAdmin]

    def get(self, request):
        point = request.user.profile.point
        qs = (
            Booking.objects.filter(point=point)
            .select_related("point", "table", "user")
            .order_by("-date", "-start_time")
        )
        # опциональный фильтр по статусу: ?status=pending
        status_filter = request.query_params.get("status")
        if status_filter in dict(Booking.STATUS_CHOICES):
            qs = qs.filter(status=status_filter)
        return Response(BookingReadSerializer(qs, many=True).data)


class BookingConfirmView(APIView):
    """US-A03: подтвердить бронь своей точки."""
    permission_classes = [IsPointAdmin]

    def post(self, request, pk):
        booking = self._get_own_booking(request, pk)
        if not booking:
            return Response({"detail": "Бронь не найдена"}, status=status.HTTP_404_NOT_FOUND)
        if booking.status != Booking.STATUS_PENDING:
            return Response(
                {"detail": "Подтвердить можно только бронь в статусе 'Ожидает подтверждения'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booking.status = Booking.STATUS_CONFIRMED
        booking.save(update_fields=["status"])
        return Response(BookingReadSerializer(booking).data)

    def _get_own_booking(self, request, pk):
        return Booking.objects.filter(
            pk=pk, point=request.user.profile.point
        ).first()


class BookingRejectView(APIView):
    """US-A03: отклонить бронь своей точки."""
    permission_classes = [IsPointAdmin]

    def post(self, request, pk):
        booking = Booking.objects.filter(
            pk=pk, point=request.user.profile.point
        ).first()
        if not booking:
            return Response({"detail": "Бронь не найдена"}, status=status.HTTP_404_NOT_FOUND)
        if booking.status != Booking.STATUS_PENDING:
            return Response(
                {"detail": "Отклонить можно только бронь в статусе 'Ожидает подтверждения'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booking.status = Booking.STATUS_REJECTED
        booking.save(update_fields=["status"])
        return Response(BookingReadSerializer(booking).data)