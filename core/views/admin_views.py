# core/views/admin_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password

from core.models import User, Student, Mentor, Admin, Problem


def _get_current_admin(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None, redirect("login")

    try:
        admin = Admin.objects.select_related("user").get(user_id=user_id)
    except Admin.DoesNotExist:
        messages.error(request, "You are not authorized as admin.")
        return None, redirect("home")

    return admin, None


def admin_dashboard(request):
    admin, redirect_resp = _get_current_admin(request)
    if redirect_resp:
        return redirect_resp

    # ban / unban / edit
    if request.method == "POST":
        action = request.POST.get("action")

        # 1. Create new user
        if action == "create":
            username = request.POST.get("username", "").strip()
            email = request.POST.get("email", "").strip()
            password = request.POST.get("password", "").strip()
            role = request.POST.get("role", "").strip()  # student / mentor / admin

            if not username or not email or not password or not role:
                messages.error(request, "All fields are required.")
                return redirect("admin_dashboard")

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered.")
                return redirect("admin_dashboard")

            try:
                user = User.objects.create(
                    name=username,
                    email=email,
                    password=make_password(password),
                    status='active',
                )

                if role == "student":
                    Student.objects.create(user=user)
                elif role == "mentor":
                    Mentor.objects.create(user=user, expertise_area="General")
                elif role == "admin":
                    Admin.objects.create(user=user, admin_level="Standard")
                else:
                    messages.error(request, "Invalid role.")
                    user.delete()
                    return redirect("admin_dashboard")

                messages.success(
                    request,
                    f"User '{username}' created as {role}."
                )
            except Exception as e:
                messages.error(request, f"Failed to create user: {e}")

            return redirect("admin_dashboard")

        # 2. Ban / Unban
        elif action in ("ban", "unban"):
            user_id = request.POST.get("user_id")
            if not user_id:
                messages.error(request, "Missing user id.")
                return redirect("admin_dashboard")

            user = get_object_or_404(User, user_id=user_id)

            new_status = "banned" if action == "ban" else "active"
            User.objects.filter(user_id=user_id).update(status=new_status)

            messages.success(
                request,
                f"User '{user.name}' status updated to {new_status}."
            )
            return redirect("admin_dashboard")

        # 3. edit info
        elif action == "edit":
            user_id = request.POST.get("user_id")
            name = request.POST.get("edit_name", "").strip()
            email = request.POST.get("edit_email", "").strip()
            status = request.POST.get("edit_status", "").strip()
            new_password = request.POST.get("edit_password", "").strip()

            if not user_id:
                messages.error(request, "Missing user id.")
                return redirect("admin_dashboard")

            user = get_object_or_404(User, user_id=user_id)

            # check if email exists
            if email and email != user.email:
                if User.objects.filter(email=email).exclude(user_id=user_id).exists():
                    messages.error(request, "Email already used by another user.")
                    return redirect("admin_dashboard")

            if name:
                user.name = name
            if email:
                user.email = email
            if status in ("active", "banned"):
                user.status = status
            if new_password:
                user.password = make_password(new_password)

            try:
                user.save()
                messages.success(request, f"User '{user.name}' updated successfully.")
            except Exception as e:
                messages.error(request, f"Failed to update user: {e}")

            return redirect("admin_dashboard")

    # ========= GET 请求 展示 dashboard =========

    user_qs = User.objects.all().order_by("user_id")

    users_data = []
    for u in user_qs:
        if Student.objects.filter(user=u).exists():
            role = "student"
        elif Mentor.objects.filter(user=u).exists():
            role = "mentor"
        elif Admin.objects.filter(user=u).exists():
            role = "admin"
        else:
            role = "unknown"

        row = {
            "id": getattr(u, "user_id", u.pk),
            "username": u.name,
            "email": u.email,
            "role": role,
            "status": getattr(u, "status", "active") or "active",
            "joined_date": getattr(u, "created_at", None),
        }
        users_data.append(row)

    total_users = len(users_data)
    banned_users = len([u for u in users_data if u["status"] == "banned"])
    active_users = total_users - banned_users
    total_problems = Problem.objects.count()

    # filter
    role_filter = request.GET.get("role") or ""
    status_filter = request.GET.get("status") or ""
    search = request.GET.get("search") or ""

    filtered_users = users_data

    if role_filter:
        filtered_users = [u for u in filtered_users if u["role"] == role_filter]

    if status_filter:
        filtered_users = [u for u in filtered_users if u["status"] == status_filter]

    if search:
        s = search.lower()
        filtered_users = [
            u for u in filtered_users
            if s in (u["username"] or "").lower()
            or s in (u["email"] or "").lower()
        ]

    context = {
        "admin": admin,
        "users": filtered_users,
        "total_users": total_users,
        "active_users": active_users,
        "banned_users": banned_users,
        "total_problems": total_problems,

        "user_name": admin.user.name if admin else "Admin",
        "user_role": "Admin",
    }
    return render(request, "core/admin_dashboard.html", context)