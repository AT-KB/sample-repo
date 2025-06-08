from django.urls import path
from .views import stock_analysis_view, candlestick_analysis_view

urlpatterns = [
    path('', stock_analysis_view, name='stock_analysis'),
    path('candlestick/', candlestick_analysis_view, name='candlestick_analysis'),
]
