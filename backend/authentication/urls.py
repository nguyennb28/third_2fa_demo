from django.urls import path, include
from .views import (
    CreateQRView,
    VerifyOTPView,
    LoginView,
    CreateUserView,
)

urlpatterns = [
    path("create-qr/", CreateQRView.as_view(), name="create-qr"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("custom-login/", LoginView.as_view(), name="custom-login"),
    path(
        "add-account/", CreateUserView.as_view(), name="add-account"
    ),
]
