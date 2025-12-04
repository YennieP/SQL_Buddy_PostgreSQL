# core/views/student_views.py

from datetime import datetime

from django.contrib import messages
from django.db import connection
from django.db.models import Avg, Count, Max
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render

from core.models import (
    Access,
    Attempt,
    Problem,
    Scenario,
    Student,
    Topic,
    User,
    Resource,
    HaveTopic,
)
from core.utils.sql_evaluator import evaluate_sql_answer
from core.utils.scenario_generator import generate_problems_simple

from django.db import connection
from core.utils.nl2sql import nl_to_sql

def _get_current_student(request):
    """from session fetch loged Student """
    user_id = request.session.get("user_id")
    if not user_id:
        return None, redirect("login")

    try:
        student = Student.objects.select_related("user").get(user_id=user_id)
    except Student.DoesNotExist:
        messages.error(request, "You are not registered as a student.")
        return None, redirect("home")

    return student, None


# 1) Student Dashboard

def student_dashboard(request):
    student, redirect_resp = _get_current_student(request)
    if redirect_resp:
        return redirect_resp

    # 1.StudentPerformanceSummary 
    summary = None
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, name, email,
                   problems_attempted,
                   average_score,
                   highest_score,
                   total_attempts
            FROM StudentPerformanceSummary
            WHERE user_id = %s
            """,
            [student.user_id],
        )
        row = cursor.fetchone()
        if row:
            summary = {
                "user_id": row[0],
                "name": row[1],
                "email": row[2],
                "problems_attempted": row[3],
                "average_score": row[4],
                "highest_score": row[5],
                "total_attempts": row[6],
            }

    # 2.recent attempts
    recent_attempts = (
        Attempt.objects.filter(student=student)
        .select_related("problem")
        .order_by("-submit_time")[:10]
    )

    # 3.problem recommendation
    # easy/medium problem haven't been attempted
    attempted_problem_ids = (
        Attempt.objects.filter(student=student)
        .values_list("problem_id", flat=True)
        .distinct()
    )
    recommended_problems = (
        Problem.objects.exclude(problem_id__in=attempted_problem_ids)
        .filter(difficulty__in=["Easy", "Medium"])
        .order_by("difficulty", "problem_id")[:5]
    )
    problems_passed = (
        Attempt.objects.filter(student=student, score=100.0)
        .values('problem_id')
        .distinct()
        .count()
    )

    context = {
        "summary": summary,
        "recent_attempts": recent_attempts,
        "recommended_problems": recommended_problems,

        "student_name": summary["name"] if summary else request.session.get('user_name', 'Student'),
        "user_name": summary["name"] if summary else request.session.get('user_name', 'Student'),
        "user_role": "Student",
        "total_attempts": summary["total_attempts"] if summary else 0,
        "avg_score": round(summary["average_score"], 1) if (summary and summary["average_score"]) else 0,
        "problems_passed": problems_passed,
    }
    return render(request, "core/student_dashboard.html", context)


# 2) Browse Problems and dynamic filter

def browse_problems(request):
    student, redirect_resp = _get_current_student(request)
    if redirect_resp:
        return redirect_resp

    difficulty = request.GET.get("difficulty")
    topic_name = request.GET.get("topic")
    attempted = request.GET.get("attempted")  # "yes" "no" None
    generated = request.GET.get("generated")

    qs = (
        Problem.objects
        .all()
        .select_related("user", "scenario")
        .prefetch_related("havetopic_set__topic")
    )

    if difficulty:
        qs = qs.filter(difficulty=difficulty)

    if generated == "scenario":
        qs = qs.filter(scenario__isnull=False)
    elif generated == "normal":
        qs = qs.filter(scenario__isnull=True)

    #fuzzy match
    if topic_name:
        qs = qs.filter(havetopic__topic__topic_name__icontains=topic_name).distinct()

    if attempted == "yes":
        qs = qs.filter(attempt__student=student).distinct()
    elif attempted == "no":
        qs = qs.exclude(attempt__student=student).distinct()

    problems = qs.order_by("difficulty", "problem_id")

    topics = Topic.objects.all().order_by("topic_name")
    #scenarios = Scenario.objects.filter(student=student).order_by("-created_at")

    context = {
        "problems": problems,
        "topics": topics,
        #"scenarios": scenarios,
        "selected_difficulty": difficulty or "",
        "selected_topic": topic_name or "",
        "selected_attempted": attempted or "",
        "selected_generated": generated or "",
    }
    return render(request, "core/browse_problems.html", context)


# 3) Problem Detail

def problem_detail(request, problem_id):
    student, redirect_resp = _get_current_student(request)
    if redirect_resp:
        return redirect_resp

    problem = get_object_or_404(
        Problem.objects.select_related("user", "scenario"), pk=problem_id
    )

    attempts = (
        Attempt.objects.filter(student=student, problem=problem)
        .order_by("-submit_time", "-attempt_no")
    )

    context = {
        "problem": problem,
        "attempts": attempts,
    }
    return render(request, "core/problem_detail.html", context)


# 4) Submit Attempt

def submit_attempt(request, problem_id):
    student, redirect_resp = _get_current_student(request)
    if redirect_resp:
        return redirect_resp

    problem = get_object_or_404(Problem, pk=problem_id)

    if request.method == "POST":
        student_sql = request.POST.get("student_sql", "").strip()
        if not student_sql:
            messages.error(request, "SQL cannot be empty.")
            return redirect("problem_detail", problem_id=problem.problem_id)

        try:
            score, details = evaluate_sql_answer(
                student_sql=student_sql,
                correct_sql=problem.correct_answer,
            )
        except Exception as e:
            messages.error(request, f"Error while evaluating SQL: {e}")
            return redirect("problem_detail", problem_id=problem.problem_id)

        # obtain next attempt_no
        last_attempt = (
            Attempt.objects.filter(student=student, problem=problem)
            .order_by("-attempt_no")
            .first()
        )
        next_attempt_no = 1 if not last_attempt else last_attempt.attempt_no + 1

        Attempt.objects.create(
            student=student,
            problem=problem,
            attempt_no=next_attempt_no,
            mentor=None,
            score=score,
            feedback=None,
        )

        messages.success(
            request,
            f"Attempt submitted. Score: {score}.",
        )

        return redirect("problem_detail", problem_id=problem.problem_id)

    # not a POST, jump to problem_detail page.
    return redirect("problem_detail", problem_id=problem_id)


# 5) My Attempts Dynamic filter

def my_attempts(request):
    student, redirect_resp = _get_current_student(request)
    if redirect_resp:
        return redirect_resp

    qs = Attempt.objects.filter(student=student).select_related("problem")

    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    score_min = request.GET.get("score_min")
    score_max = request.GET.get("score_max")
    difficulty = request.GET.get("difficulty")
    has_feedback = request.GET.get("has_feedback")  # yes no None

    if date_from:
        qs = qs.filter(submit_time__date__gte=date_from)
    if date_to:
        qs = qs.filter(submit_time__date__lte=date_to)

    if score_min:
        qs = qs.filter(score__gte=score_min)
    if score_max:
        qs = qs.filter(score__lte=score_max)

    if difficulty:
        qs = qs.filter(problem__difficulty=difficulty)

    if has_feedback == "yes":
        qs = qs.exclude(feedback__isnull=True).exclude(feedback="")
    elif has_feedback == "no":
        qs = qs.filter(feedback__isnull=True) | qs.filter(feedback="")

    attempts = qs.order_by("-submit_time", "-attempt_no")

    
    stats = qs.aggregate(
        avg_score=Avg("score"),
        high_score_count=Count("attempt_no", filter=Q(score__gte=90)),
        total_attempts=Count("attempt_no"),
    )
    
    high_score_pct = None
    if stats["total_attempts"]:
        high_score_pct = stats["high_score_count"] * 100.0 / stats["total_attempts"]

    context = {
        "attempts": attempts,
        "stats": stats,
        "high_score_pct": high_score_pct,
        "filters": {
            "date_from": date_from or "",
            "date_to": date_to or "",
            "score_min": score_min or "",
            "score_max": score_max or "",
            "difficulty": difficulty or "",
            "has_feedback": has_feedback or "",
        },
    }
    return render(request, "core/my_attempts.html", context)


# 6) Scenario Management

def scenario_list(request):
    student, redirect_resp = _get_current_student(request)
    if redirect_resp:
        return redirect_resp

    scenarios = Scenario.objects.filter(student=student).order_by("-created_at")
    
    for idx, s in enumerate(scenarios, start=1):
        s.display_index = idx
    
    return render(
        request,
        "core/scenario_list.html",
        {"scenarios": scenarios},
    )


def scenario_create(request):
    student, redirect_resp = _get_current_student(request)
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        desc = request.POST.get("description", "").strip()
        if not desc:
            messages.error(request, "Description cannot be empty.")
        else:
            scenario = Scenario.objects.create(
                student=student,
                scenario_description=desc,
            )
            messages.success(request, "Scenario created.")
            return redirect("scenario_detail", scenario_no=scenario.scenario_no)

    return render(request, "core/scenario_create.html")


def scenario_detail(request, scenario_no):
    student, redirect_resp = _get_current_student(request)
    if redirect_resp:
        return redirect_resp

    scenario = get_object_or_404(
        Scenario.objects.filter(student=student), pk=scenario_no
    )
    
    # calculate the display number of a scenario for a student
    all_scenarios = Scenario.objects.filter(student=student).order_by("created_at")
    for idx, s in enumerate(all_scenarios, start=1):
        if s.scenario_no == scenario.scenario_no:
            scenario.display_index = idx
            break

    problems = Problem.objects.filter(scenario=scenario).order_by("problem_id")

    context = {
        "scenario": scenario,
        "problems": problems,
    }
    return render(request, "core/scenario_detail.html", context)

@require_POST
def scenario_delete(request, scenario_no):
    student, redirect_resp = _get_current_student(request)
    if redirect_resp:
        return redirect_resp

    scenario = get_object_or_404(
        Scenario.objects.filter(student=student),
        pk=scenario_no
    )

    problems = Problem.objects.filter(scenario=scenario)

    # check if any attempt has been made
    has_attempts = Attempt.objects.filter(problem__in=problems).exists()
    if has_attempts:
        messages.error(
            request,
            "This scenario has problems that have been attempted. You cannot delete it."
        )
        return redirect("scenario_detail", scenario_no=scenario.scenario_no)

    problems.delete()
    scenario.delete()
    messages.success(request, "Scenario and its problems have been deleted.")
    return redirect("scenario_list")

# 7) Generate Scenario Problems by LLM

def generate_scenario_problems_view(request, scenario_no):
    student, redirect_resp = _get_current_student(request)
    if redirect_resp:
        return redirect_resp

    scenario = get_object_or_404(
        Scenario.objects.filter(student=student), pk=scenario_no
    )

    if request.method == "POST":
        num_problems = int(request.POST.get("num_problems", "3"))
        difficulty = request.POST.get("difficulty", "Easy")

        try:
            created = generate_problems_simple(
                scenario=scenario,
                difficulty=difficulty,
                num_problems=num_problems,
            )
        except Exception as e:
            messages.error(request, f"Failed to generate problems: {e}")
            return redirect("scenario_detail", scenario_no=scenario.scenario_no)

        messages.success(
            request,
            f"Generated {len(created)} problems for this scenario.",
        )
        return redirect("scenario_detail", scenario_no=scenario.scenario_no)

    return render(
        request,
        "core/generate_problems.html",
        {"scenario": scenario},
    )


# 8) Natural language query chatbot-style

#!!!this is now included in the student module, you can modify later to suit Mentor/Admin
def nl_query_view(request):
    student, redirect_resp = _get_current_student(request)
    if redirect_resp:
        return redirect_resp

    chat_history = request.session.get("nl_chat_history", [])

    if request.method == "GET" and request.GET.get("clear") == "1":
        chat_history = []
        request.session["nl_chat_history"] = chat_history
        request.session.modified = True
        return render(request, "core/nl_query.html", {"chat_history": chat_history})

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
                sql, explanation = nl_to_sql(
                    user_query,
                    current_student_id=student.user_id,
                )
            except Exception as e:
                error = f"Failed to generate SQL: {e}"
                sql = ""
                explanation = ""
                columns = []
                rows = []
            else:
                lowered = sql.lower()
                if not lowered.startswith("select"):
                    error = "Only SELECT queries are allowed in this demo."
                    columns = []
                    rows = []
                elif any(
                    keyword in lowered
                    for keyword in [
                        "insert",
                        "update",
                        "delete",
                        "drop",
                        "alter",
                        "truncate",
                        "create",
                    ]
                ):
                    error = "Only read-only SELECT queries are allowed."
                    columns = []
                    rows = []
                else:
                    try:
                        from django.db import connection

                        with connection.cursor() as cursor:
                            cursor.execute(sql)
                            columns = [col[0] for col in cursor.description]
                            raw_rows = cursor.fetchall()
                            rows = [[str(cell) for cell in r] for r in raw_rows]
                    except Exception as e:
                        error = f"Error while executing SQL: {e}"
                        columns = []
                        rows = []

        chat_history.append(
            {
                "user_query": user_query,
                "sql": sql,
                "explanation": explanation,
                "columns": columns,
                "rows": rows,
                "error": error,
            }
        )
        request.session["nl_chat_history"] = chat_history
        request.session.modified = True

        return redirect("nl_query")

    context = {
        "chat_history": chat_history,
    }
    return render(request, "core/nl_query.html", context)