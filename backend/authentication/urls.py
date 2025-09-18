from django.urls import path, include
from .views import CreateQRView, VerifyOTPView

urlpatterns = [
    path("create-qr/", CreateQRView.as_view(), name="create-qr"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
]
