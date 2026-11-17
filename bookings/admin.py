from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "point", "table", "date", "start_time", "end_time", "status")
    list_filter = ("status", "date", "point")
    search_fields = ("user__username", "point__name", "table__name")
    date_hierarchy = "date"