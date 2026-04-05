from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
import redis

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO()
redis_client = None
scheduler = None


def create_app(config_name='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_name)

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, supports_credentials=True)

    # 初始化Redis（可选，无Redis时跳过）
    global redis_client
    try:
        redis_client = redis.from_url(app.config['REDIS_URL'])
    except Exception as e:
        print(f"Redis连接失败，跳过: {e}")
        redis_client = None

    # SocketIO message_queue需要Redis，如果没有Redis则不用
    socketio.init_app(app, cors_allowed_origins="*", message_queue=app.config.get('SOCKETIO_MESSAGE_QUEUE') if redis_client else None)

    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.teams import teams_bp
    from app.routes.projects import projects_bp
    from app.routes.modules import modules_bp
    from app.routes.cases import cases_bp
    from app.routes.plans import plans_bp
    from app.routes.tasks import tasks_bp
    from app.routes.agents import agents_bp
    from app.routes.schedules import schedules_bp
    from app.routes.webhooks import webhooks_bp
    from app.routes.reports import reports_bp
    from app.routes.audit import audit_bp
    from app.routes.configs import configs_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(teams_bp, url_prefix='/api/v1/teams')
    app.register_blueprint(projects_bp, url_prefix='/api/v1/projects')
    app.register_blueprint(modules_bp, url_prefix='/api/v1')
    app.register_blueprint(cases_bp, url_prefix='/api/v1')
    app.register_blueprint(plans_bp, url_prefix='/api/v1')
    app.register_blueprint(tasks_bp, url_prefix='/api/v1/tasks')
    app.register_blueprint(agents_bp, url_prefix='/api/v1/agents')
    app.register_blueprint(schedules_bp, url_prefix='/api/v1/schedules')
    app.register_blueprint(webhooks_bp, url_prefix='/api/v1/webhooks')
    app.register_blueprint(reports_bp, url_prefix='/api/v1/reports')
    app.register_blueprint(audit_bp, url_prefix='/api/v1/audit-logs')
    app.register_blueprint(configs_bp, url_prefix='/api/v1/system-configs')

    # WebSocket事件
    from app.agents import websocket_events

    # 初始化调度器
    from app.scheduler import init_scheduler, shutdown_scheduler
    init_scheduler(socketio, app)

    # 注册shutdown hook
    import atexit
    atexit.register(shutdown_scheduler)

    @app.route('/api/v1/health')
    def health():
        return {'status': 'ok'}

    return app