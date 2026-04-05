"""
APScheduler 定时任务调度器
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
socketio_instance = None


def init_scheduler(socketio: SocketIO, app):
    """初始化调度器

    Args:
        socketio: SocketIO实例
        app: Flask应用实例
    """
    global socketio_instance
    socketio_instance = socketio

    # 检查调度器是否已经在运行
    if scheduler.running:
        logger.info("调度器已在运行中，跳过初始化")
        return

    # 添加定时检查任务（每分钟检查一次）
    try:
        scheduler.add_job(
            func=check_scheduled_tasks,
            trigger='cron',
            second=0,
            id='check_schedules',
            replace_existing=True,
            kwargs={'app': app}
        )
    except Exception as e:
        logger.warning(f"添加定时任务失败: {e}")

    # 启动调度器
    try:
        scheduler.configure(timezone='Asia/Shanghai')
        scheduler.start()
        logger.info("调度器已启动")
    except Exception as e:
        logger.warning(f"启动调度器失败: {e}")


def check_scheduled_tasks(app):
    """检查并执行到期的定时任务

    Args:
        app: Flask应用实例
    """
    with app.app_context():
        from app.models.schedule import ScheduledTask
        from app.models.task import TestTask
        from app import db

        try:
            # 获取所有启用的定时任务
            schedules = ScheduledTask.query.filter_by(enabled=True).all()

            for schedule in schedules:
                try:
                    # 计算下次执行时间
                    trigger = CronTrigger.from_crontab(
                        schedule.cron_expression,
                        timezone=schedule.timezone or 'Asia/Shanghai'
                    )
                    next_run = trigger.get_next_fire_time(None, datetime.now())

                    # 如果没有最近执行记录或下次执行时间已到
                    if not schedule.last_run_at:
                        # 首次执行
                        execute_schedule(schedule)
                        schedule.last_run_at = datetime.utcnow()
                        db.session.commit()
                        logger.info(f"执行定时任务 {schedule.id}: {schedule.cron_expression}")
                    else:
                        # 检查是否应该执行
                        now = datetime.utcnow()
                        # 简单检查：如果当前时间分钟数匹配cron表达式
                        from croniter import croniter
                        cron = croniter(schedule.cron_expression, schedule.last_run_at)
                        next_expected = cron.get_next(datetime)
                        if next_expected <= now:
                            execute_schedule(schedule)
                            schedule.last_run_at = datetime.utcnow()
                            db.session.commit()
                            logger.info(f"执行定时任务 {schedule.id}: {schedule.cron_expression}")

                except Exception as e:
                    logger.error(f"检查定时任务 {schedule.id} 失败: {e}")
                    db.session.rollback()

        except Exception as e:
            logger.error(f"获取定时任务列表失败: {e}")


def execute_schedule(schedule):
    """执行定时任务

    Args:
        schedule: ScheduledTask实例
    """
    from app import db
    from app.models.task import TestTask

    try:
        # 创建测试任务
        task = TestTask(
            plan_id=schedule.plan_id,
            agent_id=schedule.agent_id,
            trigger_type='schedule',
            created_by=schedule.created_by
        )
        db.session.add(task)
        db.session.commit()

        logger.info(f"创建任务 {task.id} 用于定时计划 {schedule.id}")

        # 通过WebSocket通知前端
        if socketio_instance:
            socketio_instance.emit('schedule_triggered', {
                'schedule_id': schedule.id,
                'task_id': task.id,
                'timestamp': datetime.utcnow().isoformat()
            }, namespace='/ws/client')

    except Exception as e:
        logger.error(f"执行定时任务 {schedule.id} 失败: {e}")
        raise


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("调度器已关闭")