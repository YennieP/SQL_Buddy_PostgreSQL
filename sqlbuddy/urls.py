# ============================================================
# 文件2: sqlbuddy/urls.py (你的项目名是sqlbuddy)
# 主URL配置
# ============================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path("admin/", admin.site.urls),
    path('django-admin/', admin.site.urls),
    path("", include("core.urls")),
]

# 开发环境下serve static files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
