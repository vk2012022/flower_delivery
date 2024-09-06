from pathlib import Path
from decouple import config

# Определение пути к проекту
BASE_DIR = Path(__file__).resolve().parent.parent

# Настройки безопасности
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=True, cast=bool)

# Токен старого бота
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')

# Токен и ID для нового бота администратора
NEW_BOT_TOKEN = config('NEW_BOT_TOKEN')
NEW_BOT_ADMIN_ID = config('NEW_BOT_ADMIN_ID')

ALLOWED_HOSTS = []

# Приложения Django
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'orders',
    'telegram_bot',
]

# Остальные настройки...
# Средства посредников (middlewares)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Основной URLconf
ROOT_URLCONF = 'flower_delivery.urls'

# Настройки шаблонов
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Настройки WSGI
WSGI_APPLICATION = 'flower_delivery.wsgi.application'

# Настройки базы данных (по умолчанию SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Настройки аутентификации
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Настройки языка и времени
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Статические файлы (CSS, JavaScript, изображения)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Путь для медиафайлов (если используются)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Настройки логина
LOGIN_REDIRECT_URL = 'catalog'  # Перенаправление на страницу каталога после входа
LOGOUT_REDIRECT_URL = 'login'  # Перенаправление на страницу логина после выхода

# Настройка для хранения медиафайлов и других файлов
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
