from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.schedule import ScheduledTask
from app.models.audit import AuditLog
from croniter import croniter

schedules_bp = Blueprint('schedules', __name__)


@schedules_bp.route('', methods=['GET'])
@jwt_required()
def list_schedules():
    """获取定时任务列表"""
    schedules = ScheduledTask.query.order_by(ScheduledTask.created_at.desc()).all()
    return jsonify([s.to_dict() for s in schedules])


@schedules_bp.route('', methods=['POST'])
@jwt_required()
def create_schedule():
    """创建定时任务"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    plan_id = data.get('plan_id')
    cron_expression = data.get('cron_expression', '').strip()

    if not plan_id:
        return jsonify({'error': 'plan_id不能为空'}), 400
    if not cron_expression:
        return jsonify({'error': 'cron_expression不能为空'}), 400

    # 验证cron表达式
    try:
        croniter(cron_expression)
    except ValueError:
        return jsonify({'error': '无效的cron表达式'}), 400

    # 验证计划存在
    from app.models.plan import TestPlan
    TestPlan.query.get_or_404(plan_id)

    # 验证Agent存在（如果指定）
    agent_id = data.get('agent_id')
    if agent_id:
        from app.models.agent import Agent
        Agent.query.get_or_404(agent_id)

    schedule = ScheduledTask(
        plan_id=plan_id,
        cron_expression=cron_expression,
        timezone=data.get('timezone', 'Asia/Shanghai'),
        enabled=data.get('enabled', True),
        agent_id=agent_id,
        created_by=current_user_id
    )
    db.session.add(schedule)
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='create',
        resource_type='schedule',
        resource_id=schedule.id,
        details={'plan_id': plan_id, 'cron': cron_expression},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(schedule.to_dict()), 201


@schedules_bp.route('/<int:schedule_id>', methods=['PUT'])
@jwt_required()
def update_schedule(schedule_id):
    """更新定时任务"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    schedule = ScheduledTask.query.get_or_404(schedule_id)

    if 'cron_expression' in data:
        try:
            croniter(data['cron_expression'])
        except ValueError:
            return jsonify({'error': '无效的cron表达式'}), 400
        schedule.cron_expression = data['cron_expression']

    if 'timezone' in data:
        schedule.timezone = data['timezone']
    if 'enabled' in data:
        schedule.enabled = data['enabled']
    if 'agent_id' in data:
        schedule.agent_id = data['agent_id']

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='schedule',
        resource_id=schedule.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(schedule.to_dict())


@schedules_bp.route('/<int:schedule_id>', methods=['DELETE'])
@jwt_required()
def delete_schedule(schedule_id):
    """删除定时任务"""
    current_user_id = int(get_jwt_identity())

    schedule = ScheduledTask.query.get_or_404(schedule_id)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='delete',
        resource_type='schedule',
        resource_id=schedule.id,
        details={'cron': schedule.cron_expression},
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(schedule)
    db.session.commit()

    return jsonify({'message': '删除成功'})


@schedules_bp.route('/<int:schedule_id>/enable', methods=['POST'])
@jwt_required()
def enable_schedule(schedule_id):
    """启用定时任务"""
    schedule = ScheduledTask.query.get_or_404(schedule_id)
    schedule.enabled = True
    db.session.commit()
    return jsonify(schedule.to_dict())


@schedules_bp.route('/<int:schedule_id>/disable', methods=['POST'])
@jwt_required()
def disable_schedule(schedule_id):
    """禁用定时任务"""
    schedule = ScheduledTask.query.get_or_404(schedule_id)
    schedule.enabled = False
    db.session.commit()
    return jsonify(schedule.to_dict())