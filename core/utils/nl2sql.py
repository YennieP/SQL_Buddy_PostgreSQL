# core/utils/nl2sql.py

import os
import json
from typing import Tuple

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
    system_prompt = f"""
{SCHEMA_DESCRIPTION}

Rules for the SQL you generate:
- Return exactly ONE MySQL SELECT statement.
- DO NOT use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, or other write operations.
- The query must be syntactically valid MySQL.
- Prefer simple, clear joins and column names.
- When the user asks about "my ..." data, use the current student's id if provided:
  - current_student_id = {current_student_id}
  - In Attempt table, student_id stores the student id.
  - In Scenario table, student_id also stores the student id.
- Limit result size reasonably if the query might return too many rows (for example use LIMIT 100).
- You must NEVER reference tables or columns that are not in the schema above.
- You must NEVER modify data.
- If the user asks something impossible or ambiguous, choose a reasonable interpretation and still output a SELECT.
    
You must output a JSON object with two fields:
- "sql": the SELECT statement as a string
- "explanation": a short natural language explanation of what this SQL does
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        temperature=0.0,
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    sql = (data.get("sql") or "").strip()
    explanation = (data.get("explanation") or "").strip()

    return sql, explanation