from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
import io
import base64


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    # Create QR Code for scan by Google Authenticator
    """
        1. Create device in database
        2. Create QR 
        3. Send QR to frontend
    """


class CreateQRView(APIView):
    def post(self, request):
        try:
            user = request.user

            device = TOTPDevice.objects.create(
                user=user, name=f"{user.username}-device", confirmed=False
            )

            qr_url = device.config_url
            qr_code_image = qrcode.QRCode(version=1, box_size=10, border=5)
            qr_code_image.add_data(qr_url)
            qr_code_image.make(fit=True)

            img = qr_code_image.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="JPG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            return Response(
                {
                    "success": True,
                    "message": "QR code generated successfully",
                    "qr_code": f"data:image/png;base64,{img_base64}",
                    "device_id": device.id,
                    "secret": device.bin_key.hex(),
                    "instructions": "Scan this QR code with Google Authenticator app",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "error": True,
                    "message": "Failed to generate QR code",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyOTPView(APIView):
    def post(self, request):
        device_id = request.data.get("device_id")
        otp_key = request.data.get("otp_key")

        # Find device
        device = TOTPDevice.objects.filter(
            id=device_id, user=request.user, confirmed=False
        )

        if device.verify_token(otp_key):
            device.confirmed = True
            device.save()

            return Response(
                {"message": "2FA enabled successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Wrong OTP key"},
                status=status.HTTP_400_BAD_REQUEST,
            )
