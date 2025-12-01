# core/views/mentor_views.py

from datetime import datetime
from django.contrib import messages
from django.db import connection
from django.db.models import Avg, Count, Q, Max
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.models import (
    Attempt,
    HaveTopic,
    Mentor,
    Problem,
    Resource,
    ResourceTopic,
    Student,
    Topic,
    User,
    Access,
)
from core.utils.nl2sql import nl_to_sql


def _get_current_mentor(request):
    """從 session 獲取當前登入的 Mentor"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None, redirect("login")

    try:
        mentor = Mentor.objects.select_related("user").get(user_id=user_id)
    except Mentor.DoesNotExist:
        messages.error(request, "You are not registered as a mentor.")
        return None, redirect("home")

    return mentor, None


# ==================== 1. Mentor Dashboard - Dynamic SQL ⭐ ====================

def mentor_dashboard(request):
    """Mentor 控制台 - 使用 MentorActivityDashboard View"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    # 查詢 MentorActivityDashboard View
    dashboard_data = None
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, mentor_name, problems_created,
                   resources_uploaded, students_mentored, avg_student_score
            FROM MentorActivityDashboard
            WHERE user_id = %s
            """,
            [mentor.user_id],
        )
        row = cursor.fetchone()
        if row:  # 👈 檢查是否有資料
            dashboard_data = {
                "user_id": row[0],
                "name": row[1],
                "problems_created": row[2],
                "resources_uploaded": row[3],
                "students_mentored": row[4],
                "avg_student_score": row[5],
            }
        else:
            # 如果 View 沒有資料，使用預設值
            dashboard_data = {
                "user_id": mentor.user_id,
                "name": mentor.user.name,
                "problems_created": 0,
                "resources_uploaded": 0,
                "students_mentored": 0,
                "avg_student_score": 0,
            }

    # 待 review 的 attempts (score < 60 且沒有 feedback)
    pending_reviews = (
        Attempt.objects.filter(
            problem__user=mentor,
            feedback__isnull=True,
        )
        .filter(Q(feedback="") | Q(feedback__isnull=True))
        .select_related("student__user", "problem")
        .order_by("submit_time")[:10]
    )

    # 最近創建的問題
    recent_problems = (
        Problem.objects.filter(user=mentor)
        .order_by("-create_time")[:5]
    )

    context = {
        "dashboard_data": dashboard_data,
        "pending_reviews": pending_reviews,
        "recent_problems": recent_problems,
    }
    return render(request, "core/mentor_dashboard.html", context)


# ==================== 2. Create Problem (手動創建) ====================

def create_problem(request):
    """手動創建問題"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        correct_answer = request.POST.get("correct_answer", "").strip()
        difficulty = request.POST.get("difficulty", "Easy")
        scenario_no = request.POST.get("scenario_no", "").strip()
        topic_names = request.POST.getlist("topics")

        # 驗證必填欄位
        if not title or not correct_answer:
            messages.error(request, "Title and Correct Answer are required.")
            return redirect("create_problem")

        # 創建 Problem
        problem = Problem.objects.create(
            user=mentor,
            title=title,
            description=description,
            correct_answer=correct_answer,
            difficulty=difficulty,
            scenario_id=int(scenario_no) if scenario_no else None,
        )

        # 處理 Topics - 用 raw SQL
        for topic_name in topic_names:
            topic_name = topic_name.strip()
            if topic_name:
                topic, _ = Topic.objects.get_or_create(
                    topic_name=topic_name,
                    defaults={"description": ""}
                )
                
                # 用 raw SQL 創建 HaveTopic
                with connection.cursor() as cursor:
                    try:
                        cursor.execute(
                            "INSERT INTO Have_topic (problem_id, topic_name) VALUES (%s, %s)",
                            [problem.problem_id, topic.topic_name]
                        )
                    except Exception:
                        # 如果已存在，忽略錯誤
                        pass

        messages.success(request, f"Problem '{title}' created successfully!")
        return redirect("my_problems")

    # GET: 顯示表單
    topics = Topic.objects.all().order_by("topic_name")
    context = {"topics": topics}
    return render(request, "core/create_problem.html", context)


# ==================== 3. My Problems - Dynamic SQL ⭐ ====================

def my_problems(request):
    """Mentor 的問題列表 - 動態過濾 + 統計"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    # 基礎查詢
    qs = Problem.objects.filter(user=mentor).select_related("scenario")

    # 動態過濾條件
    difficulty = request.GET.get("difficulty")
    topic_name = request.GET.get("topic")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    min_attempts = request.GET.get("min_attempts")
    max_attempts = request.GET.get("max_attempts")

    if difficulty:
        qs = qs.filter(difficulty=difficulty)

    if topic_name:
        qs = qs.filter(havetopic__topic__topic_name__icontains=topic_name).distinct()

    if date_from:
        qs = qs.filter(create_time__date__gte=date_from)

    if date_to:
        qs = qs.filter(create_time__date__lte=date_to)

    # 附加統計信息（JOIN Attempt）
    problems_with_stats = []
    for problem in qs:
        attempts = Attempt.objects.filter(problem=problem)
        
        total_attempts = attempts.count()
        avg_score = attempts.aggregate(Avg("score"))["score__avg"] or 0
        pass_count = attempts.filter(score__gte=60).count()
        pass_rate = (pass_count / total_attempts * 100) if total_attempts > 0 else 0
        unique_students = attempts.values("student").distinct().count()

        # 過濾嘗試次數
        if min_attempts and total_attempts < int(min_attempts):
            continue
        if max_attempts and total_attempts > int(max_attempts):
            continue

        # 👇 查詢這個 Problem 的 Topics
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT topic_name FROM Have_topic WHERE problem_id = %s",
                [problem.problem_id]
            )
            topics = [row[0] for row in cursor.fetchall()]

        problems_with_stats.append({
            "problem": problem,
            "total_attempts": total_attempts,
            "avg_score": round(avg_score, 2),
            "pass_rate": round(pass_rate, 2),
            "unique_students": unique_students,
            "topics": topics,  # 👈 加這個
        })

    topics = Topic.objects.all().order_by("topic_name")

    context = {
        "problems_with_stats": problems_with_stats,
        "topics": topics,
        "filters": {
            "difficulty": difficulty or "",
            "topic": topic_name or "",
            "date_from": date_from or "",
            "date_to": date_to or "",
            "min_attempts": min_attempts or "",
            "max_attempts": max_attempts or "",
        },
    }
    return render(request, "core/my_problems.html", context)


# ==================== 4. Problem Analytics ====================

def problem_analytics(request, problem_id):
    """單個問題的詳細分析"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    problem = get_object_or_404(
        Problem.objects.filter(user=mentor),
        pk=problem_id
    )

    attempts = Attempt.objects.filter(problem=problem)

    # 統計數據
    total_attempts = attempts.count()
    avg_score = attempts.aggregate(Avg("score"))["score__avg"] or 0
    high_scores = attempts.filter(score__gte=90).count()
    medium_scores = attempts.filter(score__gte=60, score__lt=90).count()
    low_scores = attempts.filter(score__lt=60).count()

    # 最近嘗試
    recent_attempts = attempts.select_related("student__user").order_by("-submit_time")[:10]

    context = {
        "problem": problem,
        "total_attempts": total_attempts,
        "avg_score": round(avg_score, 2),
        "high_scores": high_scores,      # 👈 直接傳遞變數
        "medium_scores": medium_scores,  # 👈 直接傳遞變數
        "low_scores": low_scores,        # 👈 直接傳遞變數
        "recent_attempts": recent_attempts,
    }
    return render(request, "core/problem_analytics.html", context)


# ==================== 5. Review Attempts - Dynamic SQL ⭐ ====================

def review_attempts(request):
    """查看和過濾需要 review 的 attempts"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    # 只看自己問題的 attempts
    qs = Attempt.objects.filter(problem__user=mentor).select_related(
        "student__user", "problem", "mentor__user"
    )

    # 動態過濾
    has_feedback = request.GET.get("has_feedback")
    score_min = request.GET.get("score_min")
    score_max = request.GET.get("score_max")
    problem_id = request.GET.get("problem_id")
    student_id = request.GET.get("student_id")

    if has_feedback == "no":
        qs = qs.filter(Q(feedback__isnull=True) | Q(feedback=""))
    elif has_feedback == "yes":
        qs = qs.exclude(feedback__isnull=True).exclude(feedback="")

    if score_min:
        qs = qs.filter(score__gte=score_min)
    if score_max:
        qs = qs.filter(score__lte=score_max)

    if problem_id:
        qs = qs.filter(problem_id=problem_id)

    if student_id:
        qs = qs.filter(student_id=student_id)

    attempts = qs.order_by("-submit_time")

    # 獲取該 Mentor 的所有問題（用於過濾器）
    problems = Problem.objects.filter(user=mentor).order_by("title")

    context = {
        "attempts": attempts,
        "problems": problems,
        "filters": {
            "has_feedback": has_feedback or "",
            "score_min": score_min or "",
            "score_max": score_max or "",
            "problem_id": problem_id or "",
            "student_id": student_id or "",
        },
    }
    return render(request, "core/review_attempts.html", context)


# ==================== 6. Add Feedback ⭐ ====================

@require_POST
def add_feedback(request, attempt_no):
    """為 Attempt 添加 Feedback"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    attempt = get_object_or_404(
        Attempt.objects.filter(problem__user=mentor),
        attempt_no=attempt_no
    )

    feedback = request.POST.get("feedback", "").strip()
    if not feedback:
        messages.error(request, "Feedback cannot be empty.")
        return redirect("review_attempts")

    # 更新 Attempt 的兩個欄位
    attempt.mentor = mentor
    attempt.feedback = feedback
    attempt.save(update_fields=["mentor", "feedback"])

    messages.success(request, "Feedback added successfully!")
    return redirect("review_attempts")


# ==================== 7. Upload Resource ====================

def upload_resource(request):
    """上傳學習資源"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        res_type = request.POST.get("res_type", "Article")
        resource_url = request.POST.get("resource_url", "").strip()
        topic_names = request.POST.getlist("topics")

        if not title or not resource_url:
            messages.error(request, "Title and URL are required.")
            return redirect("upload_resource")

        # 創建 Resource
        resource = Resource.objects.create(
            user=mentor,
            title=title,
            res_type=res_type,
            resource_url=resource_url,
        )

        # 處理 Topics - 用 raw SQL
        for topic_name in topic_names:
            topic_name = topic_name.strip()
            if topic_name:
                topic, _ = Topic.objects.get_or_create(
                    topic_name=topic_name,
                    defaults={"description": ""}
                )
                
                # 用 raw SQL 創建 ResourceTopic
                with connection.cursor() as cursor:
                    try:
                        cursor.execute(
                            "INSERT INTO ResourceTopic (resource_id, topic_name) VALUES (%s, %s)",
                            [resource.resource_id, topic.topic_name]
                        )
                    except Exception:
                        # 如果已存在，忽略錯誤
                        pass

        messages.success(request, f"Resource '{title}' uploaded successfully!")
        return redirect("my_resources")

    # GET: 顯示表單
    topics = Topic.objects.all().order_by("topic_name")
    context = {"topics": topics}
    return render(request, "core/upload_resource.html", context)


# ==================== 8. My Resources ====================

def my_resources(request):
    """查看 Mentor 上傳的資源 + 訪問統計 + Topics"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    resources = Resource.objects.filter(user=mentor).order_by("-uploaded_time")

    # 附加訪問統計 + Topics
    resources_with_stats = []
    for resource in resources:
        access_count = Access.objects.filter(resource=resource).count()
        unique_students = (
            Access.objects.filter(resource=resource)
            .values("student")
            .distinct()
            .count()
        )
        
        # 👇 查詢這個 Resource 的 Topics（新增的部分）
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT topic_name FROM ResourceTopic WHERE resource_id = %s",
                [resource.resource_id]
            )
            topics = [row[0] for row in cursor.fetchall()]
        
        resources_with_stats.append({
            "resource": resource,
            "access_count": access_count,
            "unique_students": unique_students,
            "topics": topics,  # 👈 加這個
        })

    context = {"resources_with_stats": resources_with_stats}
    return render(request, "core/my_resources.html", context)


# ==================== 9. Resource Analytics ====================

def resource_analytics(request, resource_id):
    """單個資源的訪問分析"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    resource = get_object_or_404(
        Resource.objects.filter(user=mentor),
        pk=resource_id
    )

    # 用 raw SQL 查詢訪問記錄
    accesses = []
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT a.access_time, s.user_id, u.name
            FROM Access a
            JOIN Student s ON a.student_id = s.user_id
            JOIN User u ON s.user_id = u.user_id
            WHERE a.resource_id = %s
            ORDER BY a.access_time DESC
            """,
            [resource_id]
        )
        
        for row in cursor.fetchall():
            access_time, student_id, student_name = row
            accesses.append({
                "access_time": access_time,
                "student_id": student_id,
                "student_name": student_name,
            })

    total_accesses = len(accesses)
    unique_students = len(set(a["student_id"] for a in accesses))

    context = {
        "resource": resource,
        "total_accesses": total_accesses,
        "unique_students": unique_students,
        "accesses": accesses,
    }
    return render(request, "core/resource_analytics.html", context)


# ==================== 10. Natural Language Query - Open SQL ⭐ ====================

def mentor_nl_query(request):
    """Mentor 專用的 Natural Language Query"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    chat_history = request.session.get("mentor_nl_chat_history", [])

    # 清空歷史
    if request.method == "GET" and request.GET.get("clear") == "1":
        chat_history = []
        request.session["mentor_nl_chat_history"] = chat_history
        request.session.modified = True
        return render(request, "core/mentor_nl_query.html", {"chat_history": chat_history})

    error = None

    if request.method == "POST":
        user_query = request.POST.get("query", "").strip()
        if not user_query:
            error = "Query cannot be empty."
            sql = ""
            explanation = ""
            columns = []
            rows = []
        else:
            try:
                # Mentor 不是 student，所以傳 None
                sql, explanation = nl_to_sql(user_query, current_student_id=None)
            except Exception as e:
                error = f"Failed to generate SQL: {e}"
                sql = ""
                explanation = ""
                columns = []
                rows = []
            else:
                lowered = sql.lower()
                if not lowered.startswith("select"):
                    error = "Only SELECT queries are allowed."
                    columns = []
                    rows = []
                elif any(
                    keyword in lowered
                    for keyword in [
                        "insert", "update", "delete", "drop",
                        "alter", "truncate", "create",
                    ]
                ):
                    error = "Only read-only SELECT queries are allowed."
                    columns = []
                    rows = []
                else:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(sql)
                            columns = [col[0] for col in cursor.description]
                            raw_rows = cursor.fetchall()
                            rows = [[str(cell) for cell in r] for r in raw_rows]
                    except Exception as e:
                        error = f"Error while executing SQL: {e}"
                        columns = []
                        rows = []

        chat_history.append({
            "user_query": user_query,
            "sql": sql,
            "explanation": explanation,
            "columns": columns,
            "rows": rows,
            "error": error,
        })
        request.session["mentor_nl_chat_history"] = chat_history
        request.session.modified = True

        return redirect("mentor_nl_query")

    context = {"chat_history": chat_history}
    return render(request, "core/mentor_nl_query.html", context)


# ==================== 11. Edit Problem (額外功能) ====================

def edit_problem(request, problem_id):
    """編輯問題"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    problem = get_object_or_404(
        Problem.objects.filter(user=mentor),
        pk=problem_id
    )

    if request.method == "POST":
        problem.title = request.POST.get("title", "").strip()
        problem.description = request.POST.get("description", "").strip()
        problem.correct_answer = request.POST.get("correct_answer", "").strip()
        problem.difficulty = request.POST.get("difficulty", "Easy")
        
        if problem.title and problem.correct_answer:
            problem.save()
            messages.success(request, "Problem updated successfully!")
            return redirect("my_problems")
        else:
            messages.error(request, "Title and Correct Answer are required.")

    context = {"problem": problem}
    return render(request, "core/edit_problem.html", context)


# ==================== 12. Delete Problem (額外功能) ====================

@require_POST
def delete_problem(request, problem_id):
    """刪除問題"""
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    problem = get_object_or_404(
        Problem.objects.filter(user=mentor),
        pk=problem_id
    )

    # 檢查是否有 attempts
    has_attempts = Attempt.objects.filter(problem=problem).exists()
    if has_attempts:
        messages.error(
            request,
            "This problem has been attempted by students. You cannot delete it."
        )
        return redirect("my_problems")

    problem.delete()
    messages.success(request, "Problem deleted successfully!")
    return redirect("my_problems")