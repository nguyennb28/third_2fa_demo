"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django_otp.admin import OTPAdminSite
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from authentication.views import CustomTokenObtainPairView


class OTPAdmin(OTPAdminSite):
    pass


admin_site = OTPAdmin(name="OTPAdmin")

for model_cls, model_admin in admin.site._registry.items():
    admin_site.register(model_cls, model_admin.__class__)

urlpatterns = [
    # path("admin/", admin.site.urls),
    path("admin/", admin_site.urls),
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token"),
    path("api/refresh/token/", TokenRefreshView.as_view(), name="refresh-token"),
]
