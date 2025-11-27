# ============================================================
# 文件3: core/urls.py
# Core App的URL配置
# ============================================================

from django.urls import path, include
from core.views import auth_views

urlpatterns = [
    # 认证相关（Person D）
    path('', auth_views.home, name='home'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('register/', auth_views.register_view, name='register'),
    
    # Student模块 (Person B添加后取消注释)
    # path('student/', include('core.urls.student_urls')),
    
    # Mentor模块 (Person C添加后取消注释)
    # path('mentor/', include('core.urls.mentor_urls')),
    
    # Admin模块 (Person D添加后取消注释)
    # path('admin-panel/', include('core.urls.admin_urls')),
]