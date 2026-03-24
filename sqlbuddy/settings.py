# =============================================================
# sqlbuddy/settings.py
# Django 项目配置文件
# 支持环境：本地开发（DEBUG=True）+ Railway 生产（DEBUG=False）
# 数据库：PostgreSQL（Railway 托管）
# =============================================================

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url   # 解析 DATABASE_URL 字符串（Railway 自动注入）

# -------------------------------------------------------------
# 0. 加载 .env 文件
#    本地开发时从项目根目录的 .env 读取环境变量
#    生产环境（Railway）直接从系统环境变量读取，.env 不会上传
# -------------------------------------------------------------
load_dotenv()

# 项目根目录（manage.py 所在的那一层）
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================
# 1. 核心安全配置
# =============================================================

# DEBUG 模式
#   本地：.env 里设 DEBUG=True，开启调试页面和详细报错
#   生产：Railway 里设 DEBUG=False，绝不在线上暴露错误详情
DEBUG = os.getenv("DEBUG", "True") == "True"

# SECRET_KEY — Django 用于加密 session、CSRF token 等
#   生产环境必须设置，且不能泄露
#   本地开发可用任意字符串，但生产如果忘记设置会直接报错而非静默使用弱密钥
_secret = os.getenv("SECRET_KEY")
if not _secret:
    if not DEBUG:
        raise ValueError(
            "SECRET_KEY environment variable must be set in production! "
            "Run: python -c \"from django.core.management.utils import "
            "get_random_secret_key; print(get_random_secret_key())\""
        )
    _secret = "django-insecure-local-dev-only-do-not-use-in-production"
SECRET_KEY = _secret

# ALLOWED_HOSTS — 允许访问本服务的域名/IP
#   Railway 会自动注入 RAILWAY_PUBLIC_DOMAIN（如 sqlbuddy.railway.app）
#   本地开发只需要 localhost 和 127.0.0.1
_hosts_raw = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in _hosts_raw.split(",") if h.strip()]

_railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")   # Railway 自动注入
if _railway_domain and _railway_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_railway_domain)


# =============================================================
# 2. 已安装的 App
# =============================================================
INSTALLED_APPS = [
    # Django 内置 App
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方：Bootstrap5 表单样式
    "crispy_forms",
    "crispy_bootstrap5",
    # 本项目的核心 App
    "core.apps.CoreConfig",
]


# =============================================================
# 3. 中间件
#    顺序很重要，不要随意调换
# =============================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise 必须紧跟 SecurityMiddleware
    # 负责在生产环境直接 serve 静态文件，不需要 Nginx
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",        # CSRF 防护
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # 防点击劫持
]


# =============================================================
# 4. URL 和模板配置
# =============================================================
ROOT_URLCONF = "sqlbuddy.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # 全局模板目录
        "APP_DIRS": True,                   # 同时搜索各 App 的 templates/ 目录
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # 自定义：向所有模板注入 user_id / user_name / user_role
                "core.context_processors.user_role",
            ],
        },
    },
]

WSGI_APPLICATION = "sqlbuddy.wsgi.application"


# =============================================================
# 5. 数据库配置 — PostgreSQL
#
#   优先级：
#     1. DATABASE_URL（Railway 自动注入，生产环境用这个）
#     2. 单独的 DB_* 环境变量（本地开发手动配置）
# =============================================================
DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     os.getenv("DB_NAME",     "sqlbuddy"),
        "USER":     os.getenv("DB_USER",     "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST":     os.getenv("DB_HOST",     "localhost"),
        "PORT":     os.getenv("DB_PORT",     "5432"),
        # 连接池：复用数据库连接，避免每次请求都重新握手
        "CONN_MAX_AGE": 60,
    }
}

# Railway 会自动注入 DATABASE_URL，格式如：
#   postgres://user:pass@host:5432/dbname
# 如果存在，覆盖上面的手动配置
_db_url = os.getenv("DATABASE_URL")
if _db_url:
    DATABASES["default"] = dj_database_url.config(
        default=_db_url,
        conn_max_age=60,
        ssl_require=not DEBUG,  # 生产环境强制 SSL 连接数据库
    )


# =============================================================
# 6. 必要环境变量检查
#    生产环境启动时，如果关键变量缺失则直接报错，而不是悄悄用空值
# =============================================================
REQUIRED_ENV_VARS = ["GEMINI_API_KEY"]
_missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
if _missing and not DEBUG:
    raise ValueError(f"Missing required environment variables: {', '.join(_missing)}")


# =============================================================
# 7. 密码验证规则
# =============================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 6},
    },
]


# =============================================================
# 8. 国际化 & 时区
# =============================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE     = "America/Los_Angeles"
USE_I18N      = True
USE_TZ        = True    # 数据库存 UTC，显示时转换为 TIME_ZONE


# =============================================================
# 9. 静态文件配置
#    开发环境：Django 自动 serve（DEBUG=True 时）
#    生产环境：WhiteNoise 负责 serve，collectstatic 收集到 STATIC_ROOT
# =============================================================
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"          # collectstatic 输出目录
STATICFILES_DIRS = [BASE_DIR / "core" / "static"]  # 开发时的静态文件来源

# WhiteNoise：压缩 + 添加内容 hash（浏览器缓存友好）
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# =============================================================
# 10. 其他 Django 配置
# =============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Crispy Forms — 使用 Bootstrap 5 样式渲染表单
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK          = "bootstrap5"


# =============================================================
# 11. GEMINI 配置
#     用于 NL→SQL 自然语言查询 和 场景题目生成
# =============================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# =============================================================
# 12. 认证 & Session 配置
#     注：本项目使用自定义 session 认证，非 Django 内置 auth
# =============================================================
LOGIN_URL          = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

SESSION_COOKIE_AGE         = 1800   # session 超时：30 分钟无操作自动登出
SESSION_SAVE_EVERY_REQUEST = True   # 每次请求刷新超时计时器
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # 关闭浏览器不立即登出


# =============================================================
# 13. 生产环境安全加固
#     只在 DEBUG=False（Railway 生产）时启用，本地开发不干扰
# =============================================================
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER  = True   # 响应头：X-XSS-Protection
    SECURE_CONTENT_TYPE_NOSNIFF = True  # 响应头：X-Content-Type-Options
    X_FRAME_OPTIONS             = "DENY"  # 禁止 iframe 嵌套（防点击劫持）
    SESSION_COOKIE_SECURE       = True   # Session Cookie 只通过 HTTPS 传输
    CSRF_COOKIE_SECURE          = True   # CSRF Cookie 只通过 HTTPS 传输


# =============================================================
# 14. 日志配置
#     本地：输出 DEBUG 级别的 SQL 查询，便于调试 N+1 问题
#     生产：只输出 WARNING 以上，减少噪音
# =============================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        # 数据库查询日志
        # 本地开发设为 DEBUG 可以看到所有 SQL，帮助发现 N+1 查询
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "WARNING",
            "propagate": False,
        },
    },
}