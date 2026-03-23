# SQL Buddy 🧠

> [English](README.md) | **中文文档**

一个 AI 驱动的 SQL 学习平台。学生可以通过交互式题目、场景化挑战和自然语言查询助手来练习 SQL。

**在线演示：** [your-app.railway.app](https://your-app.railway.app)

> **原始 MySQL 版本：** [SQL_Buddy (MySQL + GCP)](https://github.com/YennieP/SQL_Buddy)

---

## 核心功能

- **角色权限系统** — Student、Mentor、Admin 三种角色，各有独立 Dashboard 和权限边界
- **AI 生成题目** — Mentor 输入真实业务场景描述，GPT-4o-mini 自动生成对应难度的 SQL 题目
- **自然语言 SQL 助手** — 学生用中文或英文提问，AI 生成并执行只读 SQL，结果以聊天界面呈现
- **结构化 SQL 评分** — 基于 F1 算法对 FROM / SELECT / WHERE 三个子句分别打分，支持部分得分
- **Mentor 反馈系统** — Mentor 审阅学生答题记录并添加针对性文字反馈
- **学习资源库** — Mentor 上传文章、视频、教程，按 SQL 主题打标签
- **管理后台** — 用户管理（角色分配、封禁/解封、信息编辑）

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | Python 3.11、Django 4.2 |
| 数据库 | PostgreSQL（Railway 托管） |
| AI 集成 | OpenAI GPT-4o-mini API |
| 前端 | Django Templates、Bootstrap 5 |
| 部署 | Railway |
| 认证 | 基于 Session 的自定义认证，密码使用 Django `make_password` / `check_password` 哈希存储 |

---

## 项目结构

```
SQL_Buddy/
│
├── sqlbuddy/                      # Django 项目配置
│   ├── settings.py                # 环境感知配置（本地开发 / 生产）
│   ├── urls.py                    # 根路由
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                          # 核心 Django App
│   ├── models.py                  # 15 个模型（managed=False，映射已有数据库表）
│   │
│   ├── views/                     # 按角色拆分的视图
│   │   ├── auth_views.py          # 登录、登出、注册
│   │   ├── student_views.py       # Dashboard、题目、答题记录、场景、自然语言查询
│   │   ├── mentor_views.py        # 题目管理、反馈、资源、数据分析
│   │   ├── admin_views.py         # 用户管理（封禁 / 解封 / 创建）
│   │   └── notification_views.py  # 通知中心
│   │
│   ├── utils/                     # 业务逻辑层
│   │   ├── nl2sql.py              # 自然语言 → SQL（OpenAI，仅允许 SELECT）
│   │   ├── sql_evaluator.py       # 基于 F1 的结构化评分算法
│   │   └── scenario_generator.py  # 根据场景 AI 生成题目
│   │
│   ├── templates/core/            # HTML 模板（Bootstrap 5）
│   │   ├── base.html
│   │   ├── base_dashboard.html
│   │   ├── student_dashboard.html
│   │   ├── mentor_dashboard.html
│   │   ├── admin_dashboard.html
│   │   ├── browse_problems.html
│   │   ├── problem_detail.html
│   │   ├── nl_query.html          # 聊天机器人界面
│   │   └── ...
│   │
│   ├── static/                    # CSS、JS、图片
│   ├── urls.py                    # App 级路由（30+ 条路径）
│   ├── context_processors.py      # 向所有模板注入 Session 用户信息
│   └── apps.py
│
├── db/                            # 数据库脚本（PostgreSQL）
│   ├── dbDDL.sql                  # 建表：15 张表、3 个视图、5 个触发器
│   ├── dbDML.sql                  # 种子数据：22 个用户、10 道题、30 条答题记录
│   ├── dbSQL.sql                  # 8 条分析查询（JOIN、CTE、子查询、窗口函数）
│   └── dbDROP.sql                 # 全量清理脚本
│
├── staticfiles/                   # 静态文件收集目录（自动生成，已 gitignore）
├── manage.py
├── requirements.txt
├── Procfile                       # Railway / Gunicorn 启动命令
├── railway.json                   # Railway 部署配置
├── .env.example                   # 环境变量模板
├── .gitignore
├── README.md                      # English documentation
└── README.zh.md                   # 中文文档（本文件）
```

---

## 数据库结构

15 张表，采用 User 继承模式（User → Student / Mentor / Admin）：

```
User ──┬── Student ──── Scenario ──── Problem ──── Have_topic ── Topic
       ├── Mentor  ──────────────────────────┘
       └── Admin                      └────── Attempt

Mentor ──── Resource ──── ResourceTopic ── Topic
                      └── Access ── Student

User ──── Send ──── Notification ──── Receive ──── User
```

主要设计决策：
- 所有模型使用 `managed=False`，Django 只读映射，不接管迁移，SQL 文件是表结构的唯一来源
- `Attempt` 使用复合主键 `(student_id, problem_id, attempt_no)`
- 3 个数据库 View 支撑各角色 Dashboard：`StudentPerformanceSummary`、`MentorActivityDashboard`、`ProblemStatistics`
- 5 个触发器保障数据完整性：Mentor 反馈约束、计数级联更新、高分通知、删除保护

---

## 本地开发

### 前置条件
- Python 3.11+
- PostgreSQL 15+

### 启动步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-username/sql-buddy.git
cd sql-buddy

# 2. 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate.bat       # Windows CMD
venv\Scripts\Activate.ps1       # Windows PowerShell

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入数据库信息和 OpenAI API Key

# 5. 初始化数据库
psql -U postgres -c "CREATE DATABASE sqlbuddy;"
psql -U postgres -d sqlbuddy -f db/dbDDL.sql
psql -U postgres -d sqlbuddy -f db/dbDML.sql

# 6. 启动开发服务器
python manage.py runserver
```

访问 [http://localhost:8000](http://localhost:8000)

### 演示账号

直接访问 `/register/` 注册新账号即可开始体验。或使用以下种子数据账号（需先运行密码迁移脚本）：

| 角色 | 邮箱 |
|------|------|
| 学生 | pizza4life@email.com |
| 导师 | copypaste@email.com |
| 管理员 | dank.memes@email.com |

---

## 环境变量说明

将 `.env.example` 复制为 `.env` 并填写：

```env
# Django
SECRET_KEY=你的密钥（用 python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 生成）
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL（本地）
DB_NAME=sqlbuddy
DB_USER=postgres
DB_PASSWORD=你的密码
DB_HOST=localhost
DB_PORT=5432

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

> 生产环境（Railway）会自动注入 `DATABASE_URL`，无需手动配置各 `DB_*` 变量。

---

## 部署到 Railway

1. 将代码推送到 GitHub
2. 在 Railway 创建新项目 → **Add PostgreSQL** 服务
3. 连接 GitHub 仓库，Railway 自动识别 `Procfile`
4. 在 Railway 控制台设置环境变量：`OPENAI_API_KEY`、`SECRET_KEY`、`DEBUG=False`
5. `DATABASE_URL` 由 Railway 自动注入，无需手动填写数据库配置
6. 通过 Railway 的 PostgreSQL Shell 初始化数据库：
   ```sql
   \i db/dbDDL.sql
   \i db/dbDML.sql
   ```

---

## 技术亮点（面试参考）

**为什么用 `managed=False`？**
数据库表结构是作为数据库课程项目独立设计的（含触发器、存储过程、视图），Django 模型仅做映射而不接管迁移，保持 SQL 脚本作为 Schema 的唯一来源，体现了 ORM 与原生 SQL 的混合使用能力。

**为什么不用 Django 内置认证？**
`User` 表是自定义设计（不是 `auth_user`），使用 Django 的 `make_password` / `check_password` 手动管理 Session，在不依赖内置认证框架的前提下实现了安全的密码哈希存储。

**F1 评分算法的价值？**
纯字符串比对会因列顺序不同、别名差异等误判正确答案。F1 算法对 FROM（40%）、SELECT（30%）、WHERE（30%）分别计算精确率和召回率，支持部分得分，更贴近真实 SQL 评测场景。