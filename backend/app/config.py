import os
from datetime import timedelta

class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'autotest-platform-secret-key-2026')

    # 数据库
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/autotest'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT配置 - 记住登录状态，不过期
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-2026')
    JWT_ACCESS_TOKEN_EXPIRES = False  # 不过期
    JWT_TOKEN_LOCATION = ['cookies', 'headers']
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_HTTP_ONLY = True
    JWT_COOKIE_SAMESITE = 'Lax'

    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Flask-SocketIO
    SOCKETIO_MESSAGE_QUEUE = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # 日志
    LOG_MAX_SIZE_MB = int(os.getenv('LOG_MAX_SIZE_MB', 10))
    LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', 30))


class TestConfig(Config):
    """测试配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/autotest_test'
    WTF_CSRF_ENABLED = False