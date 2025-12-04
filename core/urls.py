# ============================================================
# 文件3: core/urls.py
# Core App的URL配置
# ============================================================

from django.urls import path, include
from core.views import auth_views
from core.views import student_views
from core.views import mentor_views
from core.views import notification_views

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
    # Dashboard
    path("mentor/dashboard/", mentor_views.mentor_dashboard, name="mentor_dashboard"),

    # Problem 管理
    path("mentor/problems/", mentor_views.my_problems, name="my_problems"),
    path("mentor/problems/create/", mentor_views.create_problem, name="create_problem"),
    path("mentor/problems/<int:problem_id>/edit/", mentor_views.edit_problem, name="edit_problem"),
    path("mentor/problems/<int:problem_id>/delete/", mentor_views.delete_problem, name="delete_problem"),
    path("mentor/problems/<int:problem_id>/analytics/", mentor_views.problem_analytics, name="problem_analytics"),

    # Review Attempts
    path("mentor/attempts/review/", mentor_views.review_attempts, name="review_attempts"),
    path("mentor/attempts/<int:attempt_no>/feedback/", mentor_views.add_feedback, name="add_feedback"),

    # Resource 管理
    path("mentor/resources/", mentor_views.my_resources, name="my_resources"),
    path("mentor/resources/upload/", mentor_views.upload_resource, name="upload_resource"),
    path("mentor/resources/<int:resource_id>/analytics/", mentor_views.resource_analytics, name="resource_analytics"),

    # Natural Language Query
    path("mentor/nl_query/", mentor_views.mentor_nl_query, name="mentor_nl_query"),

    # ==================== Notification 模塊 (Person C) ====================
    path("notifications/", notification_views.notification_center, name="notification_center"),
    path("notifications/send/", notification_views.send_notification, name="send_notification"),
    path("notifications/<int:noti_id>/read/", notification_views.mark_notification_read, name="mark_notification_read"),
    path("notifications/<int:noti_id>/delete/", notification_views.delete_notification, name="delete_notification"),
    path("notifications/<int:noti_id>/", notification_views.notification_detail, name="notification_detail"),
    
    # Admin模块 (Person D添加后取消注释)
    # path('admin-panel/', include('core.urls.admin_urls')),
    path('admin/dashboard/', auth_views.admin_dashboard, name='admin_dashboard'),  # 临时指向home或创建空view
]