# ============================================================
# 文件3: core/urls.py
# Core App的URL配置
# ============================================================

from django.urls import path, include
from core.views import auth_views
from core.views import student_views

urlpatterns = [
    # 认证相关（Person D）
    path('', auth_views.home, name='home'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('register/', auth_views.register_view, name='register'),
    
    # Student模块 (Person B添加后取消注释)
    # path('student/', include('core.urls.student_urls')),
    path("student/dashboard/", student_views.student_dashboard, name="student_dashboard"),
    path("student/problems/", student_views.browse_problems, name="browse_problems"),
    path("student/problems/<int:problem_id>/", student_views.problem_detail, name="problem_detail"),
    path("student/problems/<int:problem_id>/submit/", student_views.submit_attempt, name="submit_attempt"),
    path("student/attempts/", student_views.my_attempts, name="my_attempts"),
    
    path("student/scenarios/", student_views.scenario_list, name="scenario_list"),
    path("student/scenarios/create/", student_views.scenario_create, name="scenario_create"),
    path("student/scenarios/<int:scenario_no>/", student_views.scenario_detail, name="scenario_detail"),
    path("student/scenarios/<int:scenario_no>/generate/", student_views.generate_scenario_problems_view, name="generate_scenario_problems"),
    path("student/scenarios/<int:scenario_no>/delete/", student_views.scenario_delete, name="scenario_delete",),
    path("student/nl_query/", student_views.nl_query_view, name="nl_query"),
   
    # Mentor模块 (Person C添加后取消注释)
    # path('mentor/', include('core.urls.mentor_urls')),
    
    # Admin模块 (Person D添加后取消注释)
    # path('admin-panel/', include('core.urls.admin_urls')),
]