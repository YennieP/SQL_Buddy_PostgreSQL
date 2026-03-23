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
    user_id = request.session.get("user_id")
    if not user_id:
        return None, redirect("login")
    try:
        mentor = Mentor.objects.select_related("user").get(user_id=user_id)
    except Mentor.DoesNotExist:
        messages.error(request, "You are not registered as a mentor.")
        return None, redirect("home")
    return mentor, None


def mentor_dashboard(request):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    dashboard_data = None
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, mentor_name, problems_created,
                   resources_uploaded, students_mentored, avg_student_score
            FROM mentoractivitydashboard
            WHERE user_id = %s
            """,
            [mentor.user_id],
        )
        row = cursor.fetchone()
        if row:
            dashboard_data = {
                "user_id": row[0],
                "name": row[1],
                "problems_created": row[2],
                "resources_uploaded": row[3],
                "students_mentored": row[4],
                "avg_student_score": row[5],
            }
        else:
            dashboard_data = {
                "user_id": mentor.user_id,
                "name": mentor.user.name,
                "problems_created": 0,
                "resources_uploaded": 0,
                "students_mentored": 0,
                "avg_student_score": 0,
            }

    pending_reviews = (
        Attempt.objects.filter(problem__user=mentor, feedback__isnull=True)
        .filter(Q(feedback="") | Q(feedback__isnull=True))
        .select_related("student__user", "problem")
        .order_by("submit_time")[:10]
    )

    recent_problems = (
        Problem.objects.filter(user=mentor).order_by("-create_time")[:5]
    )

    feedback_given_count = (
        Attempt.objects.filter(problem__user=mentor, feedback__isnull=False)
        .exclude(feedback="").count()
    )

    context = {
        "dashboard_data": dashboard_data,
        "pending_reviews": pending_reviews,
        "recent_problems": recent_problems,
        "user_name": dashboard_data["name"] if dashboard_data else request.session.get("user_name", "Mentor"),
        "user_role": "Mentor",
        "mentor_name": dashboard_data["name"] if dashboard_data else request.session.get("user_name", "Mentor"),
        "problems_created": dashboard_data["problems_created"] if dashboard_data else 0,
        "students_helped": dashboard_data["students_mentored"] if dashboard_data else 0,
        "feedback_given": feedback_given_count,
    }
    return render(request, "core/mentor_dashboard.html", context)


def create_problem(request):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        print("POST data:", dict(request.POST))  # 临时调试
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        correct_answer = request.POST.get("correct_answer", "").strip()
        difficulty = request.POST.get("difficulty", "Easy")
        scenario_no = request.POST.get("scenario_no", "").strip()
        topic_names = request.POST.getlist("topics")

        if not title or not correct_answer:
            messages.error(request, "Title and Correct Answer are required.")
            return redirect("create_problem")

        try:
            problem = Problem.objects.create(
                user=mentor,
                title=title,
                description=description,
                correct_answer=correct_answer,
                difficulty=difficulty,
                scenario_id=int(scenario_no) if scenario_no else None,
            )
        except Exception as e:
            messages.error(request, f"Failed to create problem: {e}")
            return redirect("create_problem")

        # 处理 Topics（表名全小写）
        for t_name in topic_names:
            t_name = t_name.strip()
            if not t_name:
                continue
            topic, _ = Topic.objects.get_or_create(
                topic_name=t_name,
                defaults={"description": ""}
            )
            with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        "INSERT INTO have_topic (problem_id, topic_name) VALUES (%s, %s)",
                        [problem.problem_id, topic.topic_name]
                    )
                except Exception:
                    pass  # 已存在时忽略

        messages.success(request, f"Problem '{title}' created successfully!")
        return redirect("my_problems")

    topics = Topic.objects.all().order_by("topic_name")
    return render(request, "core/create_problem.html", {"topics": topics})


def my_problems(request):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    qs = Problem.objects.filter(user=mentor).select_related("scenario")

    difficulty = request.GET.get("difficulty")
    topic_name = request.GET.get("topic")
    date_from  = request.GET.get("date_from")
    date_to    = request.GET.get("date_to")
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

    problems_with_stats = []
    for problem in qs:
        attempts = Attempt.objects.filter(problem=problem)
        total_attempts  = attempts.count()
        avg_score       = attempts.aggregate(Avg("score"))["score__avg"] or 0
        pass_count      = attempts.filter(score__gte=60).count()
        pass_rate       = (pass_count / total_attempts * 100) if total_attempts > 0 else 0
        unique_students = attempts.values("student").distinct().count()

        if min_attempts and total_attempts < int(min_attempts):
            continue
        if max_attempts and total_attempts > int(max_attempts):
            continue

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT topic_name FROM have_topic WHERE problem_id = %s",
                [problem.problem_id]
            )
            topics = [row[0] for row in cursor.fetchall()]

        problems_with_stats.append({
            "problem": problem,
            "total_attempts": total_attempts,
            "avg_score": round(avg_score, 2),
            "pass_rate": round(pass_rate, 2),
            "unique_students": unique_students,
            "topics": topics,
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


def problem_analytics(request, problem_id):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    problem = get_object_or_404(Problem.objects.filter(user=mentor), pk=problem_id)
    attempts = Attempt.objects.filter(problem=problem)

    total_attempts = attempts.count()
    avg_score      = attempts.aggregate(Avg("score"))["score__avg"] or 0
    high_scores    = attempts.filter(score__gte=90).count()
    medium_scores  = attempts.filter(score__gte=60, score__lt=90).count()
    low_scores     = attempts.filter(score__lt=60).count()
    recent_attempts = attempts.select_related("student__user").order_by("-submit_time")[:10]

    context = {
        "problem": problem,
        "total_attempts": total_attempts,
        "avg_score": round(avg_score, 2),
        "high_scores": high_scores,
        "medium_scores": medium_scores,
        "low_scores": low_scores,
        "recent_attempts": recent_attempts,
    }
    return render(request, "core/problem_analytics.html", context)


def review_attempts(request):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    qs = Attempt.objects.filter(problem__user=mentor).select_related(
        "student__user", "problem", "mentor__user"
    )

    has_feedback = request.GET.get("has_feedback")
    score_min    = request.GET.get("score_min")
    score_max    = request.GET.get("score_max")
    problem_id   = request.GET.get("problem_id")
    student_id   = request.GET.get("student_id")

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


@require_POST
def add_feedback(request, attempt_no):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    attempt = get_object_or_404(
        Attempt.objects.filter(problem__user=mentor), attempt_no=attempt_no
    )

    feedback = request.POST.get("feedback", "").strip()
    if not feedback:
        messages.error(request, "Feedback cannot be empty.")
        return redirect("review_attempts")

    attempt.mentor = mentor
    attempt.feedback = feedback
    attempt.save(update_fields=["mentor", "feedback"])
    messages.success(request, "Feedback added successfully!")
    return redirect("review_attempts")


def upload_resource(request):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        title        = request.POST.get("title", "").strip()
        res_type     = request.POST.get("res_type", "Article")
        resource_url = request.POST.get("resource_url", "").strip()
        topic_names  = request.POST.getlist("topics")

        if not title or not resource_url:
            messages.error(request, "Title and URL are required.")
            return redirect("upload_resource")

        try:
            resource = Resource.objects.create(
                user=mentor, title=title, res_type=res_type, resource_url=resource_url,
            )
        except Exception as e:
            messages.error(request, f"Failed to upload resource: {e}")
            return redirect("upload_resource")

        for t_name in topic_names:
            t_name = t_name.strip()
            if not t_name:
                continue
            topic, _ = Topic.objects.get_or_create(
                topic_name=t_name, defaults={"description": ""}
            )
            with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        "INSERT INTO resourcetopic (resource_id, topic_name) VALUES (%s, %s)",
                        [resource.resource_id, topic.topic_name]
                    )
                except Exception:
                    pass

        messages.success(request, f"Resource '{title}' uploaded successfully!")
        return redirect("my_resources")

    topics = Topic.objects.all().order_by("topic_name")
    return render(request, "core/upload_resource.html", {"topics": topics})


def my_resources(request):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    resources = Resource.objects.filter(user=mentor).order_by("-uploaded_time")
    resources_with_stats = []

    for resource in resources:
        access_count    = Access.objects.filter(resource=resource).count()
        unique_students = (
            Access.objects.filter(resource=resource).values("student").distinct().count()
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT topic_name FROM resourcetopic WHERE resource_id = %s",
                [resource.resource_id]
            )
            topics = [row[0] for row in cursor.fetchall()]

        resources_with_stats.append({
            "resource": resource,
            "access_count": access_count,
            "unique_students": unique_students,
            "topics": topics,
        })

    return render(request, "core/my_resources.html", {"resources_with_stats": resources_with_stats})


def resource_analytics(request, resource_id):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    resource = get_object_or_404(Resource.objects.filter(user=mentor), pk=resource_id)

    accesses = []
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT a.access_time, s.user_id, u.name
            FROM access a
            JOIN student s ON a.student_id = s.user_id
            JOIN "user" u ON s.user_id = u.user_id
            WHERE a.resource_id = %s
            ORDER BY a.access_time DESC
            """,
            [resource_id]
        )
        for row in cursor.fetchall():
            accesses.append({
                "access_time": row[0],
                "student_id":  row[1],
                "student_name": row[2],
            })

    context = {
        "resource": resource,
        "total_accesses": len(accesses),
        "unique_students": len(set(a["student_id"] for a in accesses)),
        "accesses": accesses,
    }
    return render(request, "core/resource_analytics.html", context)


def mentor_nl_query(request):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    chat_history = request.session.get("mentor_nl_chat_history", [])

    if request.method == "GET" and request.GET.get("clear") == "1":
        request.session["mentor_nl_chat_history"] = []
        request.session.modified = True
        return render(request, "core/mentor_nl_query.html", {"chat_history": []})

    error = None
    if request.method == "POST":
        user_query = request.POST.get("query", "").strip()
        if not user_query:
            error = "Query cannot be empty."
            sql, explanation, columns, rows = "", "", [], []
        else:
            try:
                sql, explanation = nl_to_sql(user_query, current_student_id=None)
            except Exception as e:
                error = f"Failed to generate SQL: {e}"
                sql, explanation, columns, rows = "", "", [], []
            else:
                lowered = sql.lower()
                if not lowered.startswith("select"):
                    error = "Only SELECT queries are allowed."
                    columns, rows = [], []
                elif any(k in lowered for k in ["insert","update","delete","drop","alter","truncate","create"]):
                    error = "Only read-only SELECT queries are allowed."
                    columns, rows = [], []
                else:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(sql)
                            columns = [col[0] for col in cursor.description]
                            rows = [[str(cell) for cell in r] for r in cursor.fetchall()]
                    except Exception as e:
                        error = f"Error while executing SQL: {e}"
                        columns, rows = [], []

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

    return render(request, "core/mentor_nl_query.html", {"chat_history": chat_history})


def edit_problem(request, problem_id):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    problem = get_object_or_404(Problem.objects.filter(user=mentor), pk=problem_id)

    if request.method == "POST":
        problem.title          = request.POST.get("title", "").strip()
        problem.description    = request.POST.get("description", "").strip()
        problem.correct_answer = request.POST.get("correct_answer", "").strip()
        problem.difficulty     = request.POST.get("difficulty", "Easy")

        if problem.title and problem.correct_answer:
            problem.save()
            messages.success(request, "Problem updated successfully!")
            return redirect("my_problems")
        else:
            messages.error(request, "Title and Correct Answer are required.")

    return render(request, "core/edit_problem.html", {"problem": problem})


@require_POST
def delete_problem(request, problem_id):
    mentor, redirect_resp = _get_current_mentor(request)
    if redirect_resp:
        return redirect_resp

    problem = get_object_or_404(Problem.objects.filter(user=mentor), pk=problem_id)

    if Attempt.objects.filter(problem=problem).exists():
        messages.error(request, "This problem has been attempted by students. You cannot delete it.")
        return redirect("my_problems")

    problem.delete()
    messages.success(request, "Problem deleted successfully!")
    return redirect("my_problems")