from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, redis_client
from app.models.webhook import Webhook
from app.models.task import TestTask
from app.models.audit import AuditLog
import time

webhooks_bp = Blueprint('webhooks', __name__)


@webhooks_bp.route('', methods=['GET'])
@jwt_required()
def list_webhooks():
    """获取Webhook列表"""
    webhooks = Webhook.query.order_by(Webhook.created_at.desc()).all()
    return jsonify([w.to_dict() for w in webhooks])


@webhooks_bp.route('', methods=['POST'])
@jwt_required()
def create_webhook():
    """创建Webhook"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    name = data.get('name', '').strip()
    plan_id = data.get('plan_id')

    if not name:
        return jsonify({'error': 'name不能为空'}), 400
    if not plan_id:
        return jsonify({'error': 'plan_id不能为空'}), 400

    # 验证计划存在
    from app.models.plan import TestPlan
    TestPlan.query.get_or_404(plan_id)

    webhook = Webhook(
        name=name,
        plan_id=plan_id,
        created_by=current_user_id
    )
    db.session.add(webhook)
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='create',
        resource_type='webhook',
        resource_id=webhook.id,
        details={'name': name},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(webhook.to_dict()), 201


@webhooks_bp.route('/<int:webhook_id>', methods=['GET'])
@jwt_required()
def get_webhook(webhook_id):
    """获取Webhook详情"""
    webhook = Webhook.query.get_or_404(webhook_id)
    return jsonify(webhook.to_dict())


@webhooks_bp.route('/<int:webhook_id>', methods=['PUT'])
@jwt_required()
def update_webhook(webhook_id):
    """更新Webhook"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    webhook = Webhook.query.get_or_404(webhook_id)

    if 'name' in data:
        webhook.name = data['name'].strip()

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='webhook',
        resource_id=webhook.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(webhook.to_dict())


@webhooks_bp.route('/<int:webhook_id>', methods=['DELETE'])
@jwt_required()
def delete_webhook(webhook_id):
    """删除Webhook"""
    current_user_id = int(get_jwt_identity())

    webhook = Webhook.query.get_or_404(webhook_id)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='delete',
        resource_type='webhook',
        resource_id=webhook.id,
        details={'name': webhook.name},
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(webhook)
    db.session.commit()

    return jsonify({'message': '删除成功'})


@webhooks_bp.route('/trigger/<token>', methods=['POST'])
def trigger_webhook(token):
    """触发Webhook"""
    # 查找webhook
    webhook = Webhook.query.filter_by(token=token).first()
    if not webhook:
        return jsonify({'error': '无效的token'}), 404

    # 限流：1分钟内最多10次
    rate_key = f'webhook_rate:{token}'
    current_count = redis_client.get(rate_key)

    if current_count and int(current_count) >= 10:
        return jsonify({'error': '触发过于频繁，请稍后再试'}), 429

    # 增加计数
    pipe = redis_client.pipeline()
    pipe.incr(rate_key)
    pipe.expire(rate_key, 60)
    pipe.execute()

    # 获取请求数据
    data = request.get_json() or {}
    task_id = data.get('task_id')

    # 如果指定了task_id，创建关联的任务
    if task_id:
        task = TestTask(
            plan_id=webhook.plan_id,
            trigger_type='webhook',
            created_by=webhook.created_by
        )
    else:
        task = TestTask(
            plan_id=webhook.plan_id,
            trigger_type='webhook',
            created_by=webhook.created_by
        )

    db.session.add(task)
    db.session.commit()

    return jsonify({
        'message': '触发成功',
        'task_id': task.id,
        'status': task.status
    })