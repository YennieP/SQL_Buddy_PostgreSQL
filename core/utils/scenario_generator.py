# core/utils/scenario_generator.py

import json
import os
import re
from typing import List, Dict

import google.generativeai as genai
from django.db import transaction
from django.utils import timezone

from core.models import User, Mentor, Problem, Scenario, Topic, HaveTopic

def _get_model():
    """每次调用时初始化，确保读取最新的环境变量"""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    return genai.GenerativeModel(
        model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
        generation_config={"response_mime_type": "application/json"},
    )


def _get_system_llm_mentor() -> Mentor:
    """
    AI 生成题目使用的固定系统账号：
        name:  GeminiGenerator
        email: llm.generator@gmail.com
    首次调用时自动创建，后续复用同一账号。
    """
    user, _ = User.objects.get_or_create(
        email="llm.generator@gmail.com",
        defaults={
            "name": "GeminiGenerator",
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
    """创建 Topic 并建立 Have_topic 关联，忽略重复"""
    for name in topic_names:
        name = (name or "").strip()
        if not name:
            continue
        topic, _ = Topic.objects.get_or_create(
            topic_name=name,
            defaults={"description": ""},
        )
        HaveTopic.objects.get_or_create(problem=problem, topic=topic)


def _call_llm_for_scenario(
    scenario: Scenario,
    difficulty: str,
    num_problems: int,
) -> List[Dict]:
    """
    调用 Gemini 根据场景生成 SQL 题目，返回结构：
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
    prompt = f"""
You are helping to design SQL practice problems for a SQL learning platform.

The core tables are:

1) Problem table:
   CREATE TABLE Problem (
       problem_id INT PRIMARY KEY AUTO_INCREMENT,
       user_id INT NOT NULL,
       correct_answer TEXT NOT NULL,
       create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       title VARCHAR(200) NOT NULL,
       difficulty ENUM('Easy', 'Medium', 'Hard') NOT NULL,
       scenario_no INT,
       description TEXT
   );

2) Topic table:
   CREATE TABLE Topic (
       topic_name VARCHAR(100) PRIMARY KEY,
       description TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

3) Have_topic table (relationship between Problem and Topic):
   CREATE TABLE Have_topic (
       problem_id INT,
       topic_name VARCHAR(100),
       PRIMARY KEY (problem_id, topic_name)
   );

For each generated problem:
- title must be at most 200 characters.
- topics must be short strings (each <= 100 characters) suitable for Topic.topic_name.
- The SQL must be a valid MySQL SELECT query stored in Problem.correct_answer.
- Difficulty will be stored as 'Easy', 'Medium', or 'Hard'. Do NOT include difficulty in JSON.
Return data that can be directly stored into these tables without violating constraints.

We have the following learning scenario for a student:

Scenario description:
{scenario.scenario_description}

Please create {num_problems} SQL query problem(s) in English for this scenario.

For each problem return a JSON object with:
- title: short problem title (<= 200 characters)
- description: start with a complete database schema in this exact format:
    Schema:
    Table1(field1, field2, ...)
    Table2(field1, field2, ...)
    ...
  Rules for schema:
  - Only include tables needed for the problem.
  - Table and column names MUST match the SQL answer exactly.
  - Keep tables small (2-8 columns each).
  - Use meaningful names related to the scenario.
  After the schema, include a plain-English problem statement.
- correct_sql: a valid MySQL SELECT statement matching the schema exactly.
- topics: a list of 1-3 short topic tags (<= 100 characters each).

All problems should have difficulty "{difficulty}".

Return a single JSON object:
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

    response = _get_model().generate_content(prompt)
    data = json.loads(response.text)

    problems_data = data.get("problems", [])
    if not isinstance(problems_data, list) or not problems_data:
        raise ValueError("Gemini did not return a valid 'problems' list.")

    return problems_data


def _scenario_description_is_meaningful(desc: str) -> bool:
    """过滤过于简短或无意义的场景描述（如 '123'、'sdf'）"""
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

    # 当前每次固定生成 1 道题，后续可调整
    num_problems = 1

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
            title       = (pdata.get("title")       or "").strip()
            description = (pdata.get("description") or "").strip()
            correct_sql = (pdata.get("correct_sql") or "").strip()
            topics      = pdata.get("topics") or []

            if not title or not correct_sql:
                continue

            if len(title) > 200:
                title = title[:197] + "..."

            topics = [(t[:100] if t and len(t) > 100 else t) for t in topics]

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