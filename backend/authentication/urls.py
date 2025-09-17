from django.urls import path, include
from .views import CreateQRView

urlpatterns = [
    path("create-qr/", CreateQRView.as_view(), name="create-qr"),
]
