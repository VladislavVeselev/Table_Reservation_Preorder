from rest_framework import serializers

from .models import Network, Point


class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Network
        fields = ["id", "name"]


class PointSerializer(serializers.ModelSerializer):
    network = NetworkSerializer(read_only=True)

    class Meta:
        model = Point
        fields = ["id", "name", "city", "address", "phone", "is_active", "network"]


class NetworkWithPointsSerializer(serializers.ModelSerializer):
    points = serializers.SerializerMethodField()

    class Meta:
        model = Network
        fields = ["id", "name", "points"]

    def get_points(self, obj):
        qs = obj.points.filter(is_active=True).order_by("name")
        return [
            {"id": p.id, "name": p.name, "city": p.city, "address": p.address}
            for p in qs
        ]