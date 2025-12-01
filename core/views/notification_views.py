# core/views/notification_views.py

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db import connection

from core.models import (
    Notification,
    Receive,
    Send,
    User,
    Student,
    Mentor,
)


def _get_current_user(request):
    """從 session 獲取當前登入的 User（任何角色都可用）"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None, redirect("login")

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return None, redirect("home")

    return user, None


# ==================== 12. Notification Center ====================

def notification_center(request):
    """查詢當前用戶的所有通知"""
    user, redirect_resp = _get_current_user(request)
    if redirect_resp:
        return redirect_resp

    notifications = []
    
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT n.noti_id, n.send_time, s.sender_id
            FROM Notification n
            JOIN Receive r ON n.noti_id = r.noti_id
            LEFT JOIN Send s ON n.noti_id = s.noti_id
            WHERE r.receiver_id = %s
            ORDER BY n.send_time DESC
            """,
            [user.user_id]
        )
        
        rows = cursor.fetchall()
        for row in rows:
            noti_id, send_time, sender_id = row
            
            sender_name = "System"
            if sender_id:
                try:
                    sender = User.objects.get(user_id=sender_id)
                    sender_name = sender.name
                except User.DoesNotExist:
                    pass
            
            notifications.append({
                "noti_id": noti_id,
                "send_time": send_time,
                "sender_name": sender_name,
                "sender_id": sender_id,
            })

    context = {
        "notifications": notifications,
        "total_count": len(notifications),
    }
    return render(request, "core/notification_center.html", context)


# ==================== 13. Send Notification (Admin 功能) ====================

def send_notification(request):
    """發送通知（Admin 功能）"""
    user, redirect_resp = _get_current_user(request)
    if redirect_resp:
        return redirect_resp

    # 檢查是否為 Admin（簡單檢查）
    try:
        from core.models import Admin
        admin = Admin.objects.get(user_id=user.user_id)
    except Admin.DoesNotExist:
        messages.error(request, "Only admins can send notifications.")
        return redirect("home")

    if request.method == "POST":
        recipient_type = request.POST.get("recipient_type")  # "all_students", "all_mentors", "specific"
        specific_user_id = request.POST.get("specific_user_id", "").strip()
        message_content = request.POST.get("message", "").strip()

        if not message_content:
            messages.error(request, "Message cannot be empty.")
            return redirect("send_notification")

        # 1. 創建 Notification 記錄
        notification = Notification.objects.create()

        # 2. 創建 Send 記錄
        Send.objects.create(sender=user, notification=notification)

        # 3. 批量創建 Receive 記錄
        receivers = []

        if recipient_type == "all_students":
            # 所有 Students
            students = Student.objects.select_related("user").all()
            receivers = [student.user for student in students]

        elif recipient_type == "all_mentors":
            # 所有 Mentors
            mentors = Mentor.objects.select_related("user").all()
            receivers = [mentor.user for mentor in mentors]

        elif recipient_type == "all_users":
            # 所有用戶
            receivers = User.objects.all()

        elif recipient_type == "specific" and specific_user_id:
            # 特定用戶
            try:
                specific_user = User.objects.get(user_id=specific_user_id)
                receivers = [specific_user]
            except User.DoesNotExist:
                messages.error(request, f"User with ID {specific_user_id} not found.")
                return redirect("send_notification")

        else:
            messages.error(request, "Invalid recipient selection.")
            return redirect("send_notification")

        # 批量創建 Receive
        for receiver in receivers:
            Receive.objects.create(receiver=receiver, notification=notification)

        messages.success(
            request,
            f"Notification sent to {len(receivers)} user(s) successfully!"
        )
        return redirect("notification_center")

    # GET: 顯示表單
    # 獲取所有用戶列表（用於 specific 選項）
    all_users = User.objects.all().order_by("name")

    context = {
        "all_users": all_users,
    }
    return render(request, "core/send_notification.html", context)


# ==================== 14. Mark Notification as Read ====================

@require_POST
def mark_notification_read(request, noti_id):
    """標記通知為已讀"""
    user, redirect_resp = _get_current_user(request)
    if redirect_resp:
        return redirect_resp

    # 查找當前用戶的該通知
    try:
        receive = Receive.objects.get(
            receiver=user,
            notification_id=noti_id
        )
    except Receive.DoesNotExist:
        messages.error(request, "Notification not found.")
        return redirect("notification_center")

    # 目前 Receive 表沒有 is_read 欄位
    # 如果需要，可以在資料庫加一個 is_read BOOLEAN 欄位
    # 這裡先簡單處理：刪除該 Receive 記錄（表示已讀並移除）
    
    # 選項1: 刪除 Receive（表示已讀並移除通知）
    receive.delete()
    messages.success(request, "Notification marked as read and removed.")

    # 選項2: 如果資料庫有 is_read 欄位，可以這樣做：
    # receive.is_read = True
    # receive.save()
    # messages.success(request, "Notification marked as read.")

    return redirect("notification_center")


# ==================== 15. Delete Notification (額外功能) ====================

@require_POST
def delete_notification(request, noti_id):
    """刪除通知"""
    user, redirect_resp = _get_current_user(request)
    if redirect_resp:
        return redirect_resp

    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM Receive WHERE receiver_id = %s AND noti_id = %s",
            [user.user_id, noti_id]
        )
    
    messages.success(request, "Notification deleted.")
    return redirect("notification_center")


# ==================== 16. Notification Detail (額外功能) ====================

def notification_detail(request, noti_id):
    """查看通知詳情"""
    user, redirect_resp = _get_current_user(request)
    if redirect_resp:
        return redirect_resp

    # 檢查用戶是否有權查看此通知
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM Receive WHERE receiver_id = %s AND noti_id = %s",
            [user.user_id, noti_id]
        )
        has_access = cursor.fetchone()[0] > 0
    
    if not has_access:
        messages.error(request, "Notification not found.")
        return redirect("notification_center")

    # 查詢通知詳情
    notification = get_object_or_404(Notification, noti_id=noti_id)

    # 查找發送者
    sender = None
    try:
        send = Send.objects.select_related("sender").get(notification=notification)
        sender = send.sender
    except Send.DoesNotExist:
        pass

    # 查找所有接收者
    all_receivers = []
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT u.user_id, u.name, u.email
            FROM Receive r
            JOIN User u ON r.receiver_id = u.user_id
            WHERE r.noti_id = %s
            ORDER BY u.name
            """,
            [noti_id]
        )
        
        for row in cursor.fetchall():
            all_receivers.append({
                "user_id": row[0],
                "name": row[1],
                "email": row[2],
            })

    context = {
        "notification": notification,
        "sender": sender,
        "all_receivers": all_receivers,
        "receiver_count": len(all_receivers),
    }
    return render(request, "core/notification_detail.html", context)