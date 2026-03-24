# =============================================================
# sqlbuddy/settings.py
# Django 项目配置文件
# 支持环境：本地开发（DEBUG=True）+ Railway 生产（DEBUG=False）
# 数据库：PostgreSQL（Railway 托管）
# =============================================================

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================
# 1. 核心安全配置
# =============================================================

DEBUG = os.getenv("DEBUG", "True") == "True"

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

_hosts_raw = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in _hosts_raw.split(",") if h.strip()]

_railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if _railway_domain and _railway_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_railway_domain)


# =============================================================
# 2. 已安装的 App
# =============================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap5",
    "core.apps.CoreConfig",
]


# =============================================================
# 3. 中间件
# =============================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =============================================================
# 4. URL 和模板配置
# =============================================================
ROOT_URLCONF = "sqlbuddy.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.user_role",
            ],
        },
    },
]

WSGI_APPLICATION = "sqlbuddy.wsgi.application"


# =============================================================
# 5. 数据库配置 — PostgreSQL
# =============================================================
DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     os.getenv("DB_NAME",     "sqlbuddy"),
        "USER":     os.getenv("DB_USER",     "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST":     os.getenv("DB_HOST",     "localhost"),
        "PORT":     os.getenv("DB_PORT",     "5432"),
        "CONN_MAX_AGE": 60,
    }
}

_db_url = os.getenv("DATABASE_URL")
if _db_url:
    DATABASES["default"] = dj_database_url.config(
        default=_db_url,
        conn_max_age=60,
        ssl_require=not DEBUG,
    )


# =============================================================
# 6. 必要环境变量检查
# =============================================================
REQUIRED_ENV_VARS = ["GEMINI_API_KEY"]
_missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
if _missing and not DEBUG:
    raise ValueError(f"Missing required environment variables: {', '.join(_missing)}")


# =============================================================
# 7. 密码验证规则
# =============================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
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
USE_TZ        = True


# =============================================================
# 9. 静态文件配置
# =============================================================
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "core" / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# =============================================================
# 10. 其他 Django 配置
# =============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK          = "bootstrap5"


# =============================================================
# 11. Gemini 配置
# =============================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# =============================================================
# 12. 认证 & Session 配置
# =============================================================
LOGIN_URL           = "login"
LOGIN_REDIRECT_URL  = "home"
LOGOUT_REDIRECT_URL = "login"

SESSION_COOKIE_AGE              = 1800
SESSION_SAVE_EVERY_REQUEST      = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# =============================================================
# 13. 生产环境安全加固
# =============================================================
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER   = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS             = "DENY"
    SESSION_COOKIE_SECURE       = True
    CSRF_COOKIE_SECURE          = True
    # CSRF 信任域名：支持多个域名用逗号分隔
    _csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
    if _csrf_origins:
        CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",")]


# =============================================================
# 14. 日志配置
# =============================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "WARNING",
            "propagate": False,
        },
    },
}