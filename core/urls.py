from django.urls import path
from .views import main_analysis_view

urlpatterns = [
    path('analysis/', main_analysis_view, name='analysis'),
]
