from django.urls import path
from .views import analysis_view, stock_analysis_view, candlestick_analysis_view

urlpatterns = [
    path('', analysis_view, name='analysis'),
    path('stock/', stock_analysis_view, name='stock_analysis'),
    path('candlestick/', candlestick_analysis_view, name='candlestick_analysis'),
]
