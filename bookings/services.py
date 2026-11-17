from django.db import transaction

from points.models import Table

from .models import Booking


# US-G06: занятыми считаются pending + confirmed
ACTIVE_STATUSES = [Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]


def is_table_busy(table, date, start_time, end_time):
    return Booking.objects.filter(
        table=table,
        date=date,
        status__in=ACTIVE_STATUSES,
        start_time__lt=end_time,
        end_time__gt=start_time,
    ).exists()


def create_booking_atomic(user, point, table, date, start_time, end_time):
    with transaction.atomic():
        Table.objects.select_for_update().get(pk=table.pk)
        if is_table_busy(table, date, start_time, end_time):
            return None, "busy"
        booking = Booking.objects.create(
            user=user, point=point, table=table,
            date=date, start_time=start_time, end_time=end_time,
            status=Booking.STATUS_PENDING,   # <-- pending
        )
        return booking, None