# core/utils/nl2sql.py

import os
import json
from typing import Tuple

import google.generativeai as genai

def _get_model():
    """每次调用时初始化，确保读取最新的环境变量"""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    return genai.GenerativeModel(
        model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
        generation_config={"response_mime_type": "application/json"},
    )


SCHEMA_DESCRIPTION = """
You are generating safe, read-only MySQL queries for the SQL Buddy project.

The main tables look like this (simplified, only columns):

User(user_id, name, email, password, created_at)
Student(user_id, enrollment_date, total_problems_attempted)
Mentor(user_id, expertise_area, problems_created)
Admin(user_id, admin_level)

Topic(topic_name, description, created_at)
Scenario(scenario_no, student_id, scenario_description, created_at)

Problem(problem_id, user_id, correct_answer, create_time, title, difficulty, scenario_no, description)

Attempt(student_id, problem_id, attempt_no, mentor_id, score, submit_time, feedback)

Resource(resource_id, user_id, title, res_type, uploaded_time, resource_url)
Have_topic(problem_id, topic_name)
ResourceTopic(resource_id, topic_name)
Access(resource_id, student_id, access_time)

Notification(noti_id, send_time)
Send(sender_id, noti_id)
Receive(receiver_id, noti_id)

Important joins:
- Student.user_id = User.user_id
- Mentor.user_id  = User.user_id
- Admin.user_id   = User.user_id
- Scenario.student_id = Student.user_id
- Problem.user_id = Mentor.user_id
- Attempt.student_id = Student.user_id
- Attempt.problem_id = Problem.problem_id
- Have_topic.problem_id = Problem.problem_id
- Have_topic.topic_name = Topic.topic_name
""".strip()


def nl_to_sql(user_query: str, current_student_id: int | None) -> Tuple[str, str]:
    prompt = f"""
{SCHEMA_DESCRIPTION}

Rules for the SQL you generate:
- Return exactly ONE MySQL SELECT statement.
- DO NOT use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, or other write operations.
- The query must be syntactically valid MySQL.
- Prefer simple, clear joins and column names.
{"- The current user is a student with student_id = " + str(current_student_id) + ". When the user says 'my', use this exact integer in the WHERE clause." if current_student_id is not None else "- There is no current student context. Do NOT use any placeholder like [current_student_id] in the SQL. Write general queries only."}
- Limit result size reasonably if the query might return too many rows (use LIMIT 100).
- You must NEVER reference tables or columns that are not in the schema above.
- You must NEVER modify data.
- If the user asks something impossible or ambiguous, choose a reasonable interpretation and still output a SELECT.

You must output a JSON object with exactly two fields:
- "sql": the SELECT statement as a string
- "explanation": a short natural language explanation of what this SQL does

User question: {user_query}
""".strip()

    response = _get_model().generate_content(prompt)
    data = json.loads(response.text)

    sql         = (data.get("sql")         or "").strip()
    explanation = (data.get("explanation") or "").strip()

    return sql, explanation