from django.contrib import admin

from .models import Network, Point, Table


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


class TableInline(admin.TabularInline):
    model = Table
    extra = 1


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "address", "is_active", "network")
    list_filter = ("is_active", "city", "network")
    search_fields = ("name", "address", "city")
    list_editable = ("is_active",)
    inlines = [TableInline]