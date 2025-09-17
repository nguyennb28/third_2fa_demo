from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate
from django_otp.plugins.otp_totp.models import TOTPDevice


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    otp_key = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        otp_key = attrs.get("otp_key")

        user = authenticate(username=username, password=password)

        # Check authentication user
        if not user:
            raise serializers.ValidationError("Invalid username or password")

        totp_device = TOTPDevice.objects.filter(user=user, confirmed=True).first()

        # Check user has 2fa
        if totp_device:
            if not otp_key:
                raise serializers.ValidationError(
                    {
                        "otp_key": "OTP key is required for this user",
                        "requires_2fa": True,
                    }
                )

            # Verify OTP key
            if not totp_device.verify_token(otp_key):
                raise serializers.ValidationError(
                    {
                        "otp_key": "Invalid OTP key",
                    }
                )

        data = super().validate(
            {
                "username": username,
                "password": password,
            }
        )

        data["has_2fa"] = bool(totp_device)

        return data
