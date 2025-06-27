# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_analysis_view, name='main_analysis'),
]
