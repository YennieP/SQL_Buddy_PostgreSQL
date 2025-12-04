# core/views/auth_views.py
"""
认证相关views: 登录、注册、登出
Person D负责
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from core.models import User, Student, Mentor, Admin


def home(request):
    """首页"""
    return render(request, 'core/home.html')


def login_view(request):
    """
    用户登录
    支持Student, Mentor, Admin三种角色
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            
            # 密码验证
            # Phase 4的密码可能是明文或hash，都尝试
            password_valid = False
            
            # 尝试1: 直接比较（如果Phase 4用的明文）
            if user.password == password:
                password_valid = True
            # 尝试2: Django hash验证
            elif check_password(password, user.password):
                password_valid = True
            
            if password_valid:
                # 设置session
                request.session['user_id'] = user.user_id
                request.session['user_name'] = user.name
                request.session['user_email'] = user.email
                request.session['user_role'] = user.get_role()
                
                messages.success(request, f'Welcome back, {user.name}!')
                
                # 根据角色跳转到对应dashboard
                role = user.get_role()
                if role == 'Student':
                    return redirect('student_dashboard')  # 等Person B添加后改为student_dashboard
                elif role == 'Mentor':
                    return redirect('mentor_dashboard')  # 等Person C添加后改为mentor_dashboard
                elif role == 'Admin':
                    return redirect('admin_dashboard')  # 等你添加admin后改为admin_dashboard
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Invalid password')
                
        except User.DoesNotExist:
            messages.error(request, 'User not found. Please check your email.')
    
    return render(request, 'core/login.html')


def logout_view(request):
    """用户登出"""
    user_name = request.session.get('user_name', 'User')
    request.session.flush()  # 清除所有session数据
    messages.success(request, f'Goodbye, {user_name}!')
    return redirect('login')


def register_view(request):
    """
    用户注册
    可以注册为Student或Mentor
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role')  # 'student' or 'mentor'
        
        # 验证
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'core/register.html')
        
        # 检查email是否已存在
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'core/register.html')
        
        try:
            # 创建User
            user = User.objects.create(
                name=name,
                email=email,
                password=make_password(password)  # Hash密码
            )
            
            # 根据角色创建对应的子类
            if role == 'student':
                Student.objects.create(user=user)
                role_name = 'Student'
            elif role == 'mentor':
                Mentor.objects.create(
                    user=user,
                    expertise_area='General'  # 默认值
                )
                role_name = 'Mentor'
            else:
                messages.error(request, 'Invalid role')
                user.delete()
                return render(request, 'core/register.html')
            
            messages.success(
                request, 
                f'Registration successful! You are now a {role_name}. Please login.'
            )
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'core/register.html')

def admin_dashboard(request):
    """Admin Dashboard - 临时占位"""
    return render(request, 'core/admin_dashboard.html', {
        'admin': request.session.get('user_name', 'Admin')
    })