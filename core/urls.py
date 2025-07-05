# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_analysis_view, name='main_analysis'),
    path('api/industries/', views.IndustryListAPIView.as_view(), name='api-industries'),
    path('api/industries/<int:pk>/tickers/', views.IndustryTickerAPIView.as_view(), name='api-industry-tickers'),
    path('api/tickers/search/', views.TickerSearchAPIView.as_view(), name='api-ticker-search'),
]
