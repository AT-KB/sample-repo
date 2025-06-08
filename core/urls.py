from django.urls import path
from .views import analysis_view

urlpatterns = [
    path("", analysis_view, name="analysis"),
]
