# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_analysis_view, name='main_analysis'),
    path('api/industries/', views.IndustryListAPIView.as_view()),
    path('api/industries/<int:pk>/tickers/', views.IndustryTickerAPIView.as_view()),
]
