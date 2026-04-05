from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json
from app import db
from app.models.task import TestTask, TaskResult
from app.models.audit import AuditLog

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('', methods=['GET'])
@jwt_required()
def list_tasks():
    """获取任务列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    status = request.args.get('status', '')
    plan_id = request.args.get('plan_id', type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = TestTask.query

    if status:
        query = query.filter_by(status=status)
    if plan_id:
        query = query.filter_by(plan_id=plan_id)
    if start_date:
        query = query.filter(TestTask.created_at >= start_date)
    if end_date:
        query = query.filter(TestTask.created_at <= end_date)

    pagination = query.order_by(TestTask.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    return jsonify({
        'tasks': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'page': page,
        'page_size': page_size
    })


@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """创建测试任务"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    plan_id = data.get('plan_id')
    agent_id = data.get('agent_id')

    if not plan_id:
        return jsonify({'error': 'plan_id不能为空'}), 400

    # 验证计划存在
    from app.models.plan import TestPlan
    TestPlan.query.get_or_404(plan_id)

    # 验证Agent存在（如果指定）
    if agent_id:
        from app.models.agent import Agent
        Agent.query.get_or_404(agent_id)

    task = TestTask(
        plan_id=plan_id,
        agent_id=agent_id,
        trigger_type=data.get('trigger_type', 'manual'),
        env_vars_override=data.get('env_vars_override', {}),
        timeout_override=data.get('timeout_override'),
        concurrency=data.get('concurrency', 1),
        created_by=current_user_id
    )
    db.session.add(task)
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='create',
        resource_type='task',
        resource_id=task.id,
        details={'plan_id': plan_id, 'trigger_type': task.trigger_type},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(task.to_dict()), 201


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """获取任务详情"""
    task = TestTask.query.get_or_404(task_id)
    return jsonify(task.to_dict(include_results=True))


@tasks_bp.route('/<int:task_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_task(task_id):
    """取消任务"""
    current_user_id = int(get_jwt_identity())

    task = TestTask.query.get_or_404(task_id)

    if task.status not in ['pending', 'running']:
        return jsonify({'error': '任务已结束，无法取消'}), 400

    task.status = 'cancelled'
    task.finished_at = datetime.utcnow()
    if task.started_at:
        task.duration = (task.finished_at - task.started_at).total_seconds()
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='cancel',
        resource_type='task',
        resource_id=task.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(task.to_dict())


@tasks_bp.route('/<int:task_id>/retry', methods=['POST'])
@jwt_required()
def retry_task(task_id):
    """重试任务"""
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())

    original = TestTask.query.get_or_404(task_id)

    if original.status not in ['failed', 'cancelled']:
        return jsonify({'error': '只能重试失败或取消的任务'}), 400

    # 创建新任务
    new_task = TestTask(
        plan_id=original.plan_id,
        agent_id=data.get('agent_id', original.agent_id),
        trigger_type='manual',
        env_vars_override=data.get('env_vars_override', original.env_vars_override),
        timeout_override=data.get('timeout_override', original.timeout_override),
        concurrency=data.get('concurrency', original.concurrency),
        created_by=current_user_id
    )
    db.session.add(new_task)
    db.session.commit()

    # 更新原任务
    original.status = f'retried:{new_task.id}'

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='retry',
        resource_type='task',
        resource_id=new_task.id,
        details={'original_task_id': task_id},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(new_task.to_dict()), 201


@tasks_bp.route('/<int:task_id>/results', methods=['GET'])
@jwt_required()
def get_task_results(task_id):
    """获取任务结果"""
    task = TestTask.query.get_or_404(task_id)
    results = TaskResult.query.filter_by(task_id=task_id).all()
    return jsonify({
        'task': task.to_dict(),
        'results': [r.to_dict() for r in results],
        'summary': {
            'passed': sum(1 for r in results if r.status == 'passed'),
            'failed': sum(1 for r in results if r.status == 'failed'),
            'error': sum(1 for r in results if r.status == 'error'),
            'cancelled': sum(1 for r in results if r.status == 'cancelled'),
        }
    })


@tasks_bp.route('/<int:task_id>/logs', methods=['GET'])
@jwt_required()
def get_task_logs(task_id):
    """获取任务日志"""
    result_id = request.args.get('result_id', type=int)

    from app import redis_client

    # 从Redis获取日志
    log_key = f'task_logs:{task_id}'
    if result_id:
        log_key = f'task_logs:{task_id}:{result_id}'

    logs = redis_client.lrange(log_key, 0, -1)

    return jsonify({
        'logs': [log.decode() if isinstance(log, bytes) else log for log in logs]
    })


@tasks_bp.route('/<int:task_id>/performance', methods=['GET'])
@jwt_required()
def get_task_performance(task_id):
    """获取性能数据"""
    from app.models.task import PerformanceLog

    logs = PerformanceLog.query.filter_by(task_id=task_id).order_by(PerformanceLog.timestamp).all()

    timeline = [log.to_dict() for log in logs]

    # 汇总
    if logs:
        summary = {
            'cpu_avg': sum(l.cpu_percent or 0 for l in logs) / len(logs),
            'memory_avg': sum(l.memory_percent or 0 for l in logs) / len(logs),
            'io_wait_avg': sum(l.io_wait or 0 for l in logs) / len(logs),
            'fd_count_max': max(l.fd_count or 0 for l in logs),
        }
    else:
        summary = {}

    return jsonify({
        'summary': summary,
        'timeline': timeline
    })


@tasks_bp.route('/<int:task_id>/dispatch', methods=['POST'])
@jwt_required()
def dispatch_task(task_id):
    """分发任务到Agent"""
    from app import socketio, redis_client
    from app.models.agent import Agent
    from app.models.case import TestCase, CaseVersion
    from app.models.plan import TestPlan, TestPlanCase

    task = TestTask.query.get_or_404(task_id)

    if task.status != 'pending':
        return jsonify({'error': '任务已分发或已完成'}), 400

    # 获取任务关联的Agent
    agent_id = task.agent_id

    # 如果没有指定Agent，自动分配一个在线Agent
    if not agent_id:
        agent = Agent.query.filter_by(status='online').first()
        if not agent:
            return jsonify({'error': '没有可用的在线Agent'}), 400
        agent_id = agent.id
        task.agent_id = agent_id
        db.session.commit()
    else:
        agent = Agent.query.get(agent_id)
        if agent.status != 'online':
            return jsonify({'error': '指定的Agent不在线'}), 400

    # 获取计划中的用例
    plan_cases = TestPlanCase.query.filter_by(plan_id=task.plan_id).order_by(TestPlanCase.order_index).all()

    if not plan_cases:
        return jsonify({'error': '计划中没有用例'}), 400

    # 创建任务结果记录，并建立case_id到result_id的映射
    case_to_result_id = {}
    for pc in plan_cases:
        case = TestCase.query.get(pc.case_id)
        if case:
            result = TaskResult(
                task_id=task_id,
                case_id=pc.case_id,
                status='pending'
            )
            db.session.add(result)
            db.session.flush()  # 获取result.id
            case_to_result_id[pc.case_id] = result.id

    # 获取计划的env_vars并合并任务级别的覆盖
    plan = TestPlan.query.get(task.plan_id)
    env_vars = plan.env_vars or {}
    if task.env_vars_override:
        env_vars.update(task.env_vars_override)

    db.session.commit()

    # 获取用例脚本内容
    case_scripts = []
    for pc in plan_cases:
        case = TestCase.query.get(pc.case_id)
        if case:
            version = CaseVersion.query.filter_by(case_id=case.id, is_latest=True).first()
            script_content = version.code_content if version else ''
            timeout = task.timeout_override or case.timeout

            case_scripts.append({
                'case_id': case.id,
                'result_id': case_to_result_id.get(case.id),
                'case_name': case.name,
                'script_content': script_content,
                'script_type': case.script_type,
                'timeout': timeout,
                'priority': case.priority
            })

    # 按优先级排序
    case_scripts.sort(key=lambda x: x['priority'])

    # 通过WebSocket发送任务给Agent（每个用例一条消息）
    dispatched_cases = []
    for case_info in case_scripts:
        dispatch_data = {
            'type': 'task_assign',
            'task_id': task_id,
            'result_id': case_info['result_id'],  # 使用实际的TaskResult ID
            'agent_id': agent_id,
            'case_id': case_info['case_id'],
            'case_name': case_info['case_name'],
            'script_content': case_info['script_content'],
            'script_type': case_info['script_type'],
            'env_vars': env_vars,
            'timeout': case_info['timeout'],
            'priority': case_info['priority']
        }

        # 存储任务信息到Redis，用于追踪
        redis_client.setex(f'task_dispatch:{task_id}:{case_info["case_id"]}', 3600, json.dumps(dispatch_data))

        # 发送WebSocket消息
        socketio.emit('task_assign', dispatch_data, namespace='/ws/agent')
        dispatched_cases.append(case_info['case_id'])

    # 更新任务状态
    task.status = 'running'
    task.started_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': '任务已分发',
        'task': task.to_dict(),
        'agent_id': agent_id,
        'dispatched_cases': dispatched_cases
    })