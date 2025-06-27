from django.contrib import admin
from django.urls import path, include
from core.views import health_check

urlpatterns = [
    # ヘルスチェック専用エンドポイント
    path("health/", health_check, name="health_check"),

    # Django管理画面
    path("admin/", admin.site.urls),

    # その他のアプリケーションURLはcore.urlsに含める
    path("", include("core.urls")),
]
