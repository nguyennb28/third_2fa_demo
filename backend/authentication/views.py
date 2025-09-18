from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
import io
import base64
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework_simplejwt.authentication import JWTAuthentication


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
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        device_id = request.data.get("device_id")
        otp_key = request.data.get("otp_key")

        if not device_id or not otp_key:
            return Response(
                {
                    "error": "Need device_id and otp_key",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find device
        device = TOTPDevice.objects.filter(
            id=device_id, confirmed=False
        ).get()


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


"""
    THỰC RA VIẾT VỚI MỤC ĐÍCH LUYỆN TẬP CHỨ KHÔNG CẦN
    PHẢI VIẾT class LoginView này làm gì cho nó đau đầu

"""


class LoginView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        otp_key = request.data.get("otp_key")

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {
                    "error": "Wrong username or password",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()

        if not device:
            return Response(
                {
                    "error": "Not found device",
                    "message": "Contact admin to support",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not otp_key:
            return Response(
                {"requires_2fa": True, "message": "Required OTP Key"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not device.verify_token(otp_key):
            return Response(
                {
                    "error": "Wrong OTP Key",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "has_2fa": True,
                "message": "Successfully!",
            },
            status=status.HTTP_200_OK,
        )


class CreateUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request):
        if not request.user:
            return Response(
                {"error": "Not logged in "},
                status=status.HTTP_403_FORBIDDEN,
            )
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and password required!!!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # User is exist ???
        check_user = User.objects.filter(username=username).exists()
        if check_user:
            print(check_user)
            return Response(
                {"error": "User already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_user = User.objects.create_user(
                username=username,
                password=password,
                is_active=True,
                is_staff=True,
            )
            # Create device TOTP for account
            device = self.create_totp_device(new_user)
            qr_image = self.create_qr(device)

            return Response(
                {
                    "success": True,
                    "message": "Account created successfully",
                    "new_user_id": new_user.id,
                    "device_id": device.id,
                    "qr_code": f"data:image/png;base64,{qr_image}",
                    "status": "Deactive - Scan QR",
                    "instructions": [
                        "1. Đưa thông tin tài khoản cho user",
                        "2. Yêu cầu có app Google Authenticator",
                        "3. Scan QR bằng Google Authenticator",
                    ],
                }
            )
        except Exception as e:
            return Response(
                {
                    "error": "Error creating account",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def create_totp_device(self, user):
        device = TOTPDevice.objects.create(
            user=user,
            name=f"{user.username}-device",
            confirmed=False,
        )
        return device

    def create_qr(self, device):
        qr_url = device.config_url
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_image = base64.b64encode(buffer.getvalue()).decode()

        return qr_image
