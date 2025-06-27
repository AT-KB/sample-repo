from django.urls import path
from . import views

urlpatterns = [
    # ルートパス '' にメインの分析ビューを割り当て
    path('', views.main_analysis_view, name='main_analysis'),
]
