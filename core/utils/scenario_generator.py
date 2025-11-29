# core/utils/scenario_generator.py

import json
import os
import re
from typing import List, Dict

from django.db import transaction
from django.utils import timezone

from core.models import User, Mentor, Problem, Scenario, Topic, HaveTopic

from openai import OpenAI

client = client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _get_system_llm_mentor() -> Mentor:
    """
    A fixed account for LLM problem generation:
        name:  OpenAIGenerator
        email: llm.generator@gmail.com

    When creating at first time:
        1 if User not exsit, create User
        2 if Mentor not exsit, create Mentor
    Use this same account for problem generation.
    """
    user, _ = User.objects.get_or_create(
        email="llm.generator@gmail.com",
        defaults={
            "name": "OpenAIGenerator",
            "password": "llm_system_generated",
        },
    )

    mentor, _ = Mentor.objects.get_or_create(
        user=user,
        defaults={
            "expertise_area": "System Generated Problems",
            "problems_created": 0,
        },
    )

    return mentor


def handle_llm_topics(problem: Problem, topic_names: List[str]):
    """
    create new topic and update have_topic
    """
    for name in topic_names:
        name = (name or "").strip()
        if not name:
            continue

        topic, _created = Topic.objects.get_or_create(
            topic_name=name,
            defaults={"description": ""},
        )
        # use unique_together to avoid repeating
        HaveTopic.objects.get_or_create(problem=problem, topic=topic)


def _call_llm_for_scenario(
    scenario: Scenario,
    difficulty: str,
    num_problems: int,
) -> List[Dict]:
    """
        [
          {
            "title": "...",
            "description": "...",
            "correct_sql": "...",
            "topics": ["...", ...]
          },
          ...
        ]
    """

    # clarify the table structure to avoid invalid field value
    system_prompt = (
        "You are helping to design SQL practice problems for a MySQL learning platform.\n"
        "The core tables are:\n\n"
        "1) Problem table:\n"
        "   CREATE TABLE Problem (\n"
        "       problem_id INT PRIMARY KEY AUTO_INCREMENT,\n"
        "       user_id INT NOT NULL,\n"
        "       correct_answer TEXT NOT NULL,\n"
        "       create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n"
        "       title VARCHAR(200) NOT NULL,\n"
        "       difficulty ENUM('Easy', 'Medium', 'Hard') NOT NULL,\n"
        "       scenario_no INT,\n"
        "       description TEXT\n"
        "   );\n\n"
        "2) Topic table:\n"
        "   CREATE TABLE Topic (\n"
        "       topic_name VARCHAR(100) PRIMARY KEY,\n"
        "       description TEXT,\n"
        "       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
        "   );\n\n"
        "3) Have_topic table (relationship between Problem and Topic):\n"
        "   CREATE TABLE Have_topic (\n"
        "       problem_id INT,\n"
        "       topic_name VARCHAR(100),\n"
        "       PRIMARY KEY (problem_id, topic_name)\n"
        "   );\n\n"
        "For each generated problem:\n"
        "- title must be at most 200 characters.\n"
        "- topics must be short strings (each <= 100 characters) suitable for Topic.topic_name.\n"
        "- The SQL must be a valid MySQL SELECT query that could be stored in Problem.correct_answer.\n"
        "- Difficulty will be stored as 'Easy', 'Medium', or 'Hard'. You do not need to output difficulty in JSON.\n"
        "You must return data that can be directly stored into these tables without violating their constraints."
    )

    user_prompt = f"""
We have the following learning scenario for a student:

Scenario description:
{scenario.scenario_description}

Please create {num_problems} SQL query problems in English for this scenario.

For each problem return a JSON object with:
- title: short problem title (<= 200 characters)
- A description **starting with a complete database schema** in this exact format:
    Schema: \n
    Table1(field1, field2, …)\n
    Table2(field1, field2, …)\n
    …
    Rules for schema:
    - Only include tables needed for the problem.
    - Table and column names MUST match the SQL answer.
    - Keep tables small (2–8 columns each).
    - Use meaningful names related to the scenario.

- After the schema, include a plain-English problem statement.
- A valid MySQL SELECT statement that matches the schema exactly.
- A list of 1–3 short topic tags (<= 100 characters each).

All problems should have difficulty "{difficulty}", but you do not need to include difficulty
in the JSON since the application will store it separately.

Return a single JSON object with this structure:

{{
  "problems": [
    {{
      "title": "...",
      "description": "...",
      "correct_sql": "...",
      "topics": ["...", "..."]
    }}
  ]
}}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    problems_data = data.get("problems", [])
    if not isinstance(problems_data, list) or not problems_data:
        raise ValueError("LLM did not return a valid 'problems' list.")

    return problems_data


def _scenario_description_is_meaningful(desc: str) -> bool:
    """
    insure meaningful scenario
    avoid strings like '123' 'sdf' with no meaning.
    """
    desc = (desc or "").strip()
    if len(desc) < 10:
        return False

    alnum_count = sum(1 for c in desc if c.isalnum())
    if alnum_count < 3:
        return False

    if re.fullmatch(r"[A-Za-z0-9]{1,6}", desc):
        return False

    return True


def generate_problems_simple(
    scenario: Scenario,
    difficulty: str = "Easy",
    num_problems: int = 3,
) -> List[Problem]:

    # fixed problem number, can adjust later.
    num_problems = 1

    # check if the scenario is valid.
    desc = (scenario.scenario_description or "").strip()
    if not _scenario_description_is_meaningful(desc):
        raise ValueError(
            "Scenario description is too vague or meaningless. "
            "Please provide a clearer scenario description with a concrete context "
            "(for example, 'A student course enrollment system with tables Student, Course, Enrollment')."
        )

    difficulty = (difficulty or "Easy").capitalize()
    if difficulty not in ["Easy", "Medium", "Hard"]:
        difficulty = "Easy"

    mentor = _get_system_llm_mentor()

    problems_data = _call_llm_for_scenario(
        scenario=scenario,
        difficulty=difficulty,
        num_problems=num_problems,
    )

    created_problems: List[Problem] = []

    with transaction.atomic():
        for pdata in problems_data:
            title = (pdata.get("title") or "").strip()
            description = (pdata.get("description") or "").strip()
            correct_sql = (pdata.get("correct_sql") or "").strip()
            topics = pdata.get("topics") or []

            if not title or not correct_sql:
                continue

            # cut the length of title to avoid being too long
            if len(title) > 200:
                title = title[:197] + "..."

            topics = [
                (t[:100] if t and len(t) > 100 else t)
                for t in topics
            ]

            problem = Problem.objects.create(
                user=mentor,
                correct_answer=correct_sql,
                create_time=timezone.now(),
                title=title,
                difficulty=difficulty,
                scenario=scenario,
                description=description or None,
            )

            handle_llm_topics(problem, topics)
            created_problems.append(problem)

    return created_problems