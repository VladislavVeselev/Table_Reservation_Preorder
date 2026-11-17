from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Profile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        Profile.objects.create(user=user, role=Profile.ROLE_GUEST)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs["username"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Неверный логин или пароль")
        if not user.is_active:
            raise serializers.ValidationError("Аккаунт отключён")
        attrs["user"] = user
        return attrs


class MeSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)
    role_display = serializers.CharField(
        source="profile.get_role_display", read_only=True
    )
    point = serializers.SerializerMethodField()
    network = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email",
            "role", "role_display",
            "point", "network",
        ]

    def get_point(self, obj):
        profile = getattr(obj, "profile", None)
        if not profile or not profile.point_id:
            return None
        return {"id": profile.point_id, "name": profile.point.name}

    def get_network(self, obj):
        profile = getattr(obj, "profile", None)
        if not profile or not profile.network_id:
            return None
        return {"id": profile.network_id, "name": profile.network.name}
