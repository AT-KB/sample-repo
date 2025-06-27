# myapp/urls.py
from django.contrib import admin
from django.urls import path, include
from core.views import health_check

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]
