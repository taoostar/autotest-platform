from flask import request
from flask_socketio import emit, disconnect
from app import socketio, redis_client, db
from app.models.agent import Agent
from app.models.task import TestTask, PerformanceLog
from datetime import datetime
import json

# 存储在线Agent连接
online_agents = {}


@socketio.on('connect', namespace='/ws/agent')
def agent_connect():
    """Agent连接"""
    token = request.args.get('token')
    if not token:
        disconnect()
        return

    # 验证Agent token（简化版：使用agent_id作为token）
    try:
        agent_id = int(token)
        agent = Agent.query.get(agent_id)
        if not agent:
            disconnect()
            return
    except ValueError:
        disconnect()
        return

    # 更新Agent状态
    agent.status = 'online'
    agent.last_heartbeat = datetime.utcnow()
    agent.ip_address = request.remote_addr
    from app import db
    db.session.commit()

    online_agents[request.sid] = agent_id

    emit('connected', {'agent_id': agent_id, 'status': 'online'})
    print(f'Agent {agent_id} connected')


@socketio.on('disconnect', namespace='/ws/agent')
def agent_disconnect():
    """Agent断开连接"""
    if request.sid in online_agents:
        agent_id = online_agents.pop(request.sid)

        from app import db
        agent = Agent.query.get(agent_id)
        if agent:
            agent.status = 'offline'
            db.session.commit()

        print(f'Agent {agent_id} disconnected')


@socketio.on('heartbeat', namespace='/ws/agent')
def agent_heartbeat(data):
    """Agent心跳"""
    if request.sid not in online_agents:
        return

    agent_id = online_agents[request.sid]

    from app import db
    agent = Agent.query.get(agent_id)
    if agent:
        agent.status = 'online'
        agent.last_heartbeat = datetime.utcnow()
        agent.current_load = data.get('load', 0)
        db.session.commit()

    emit('heartbeat_ack', {'timestamp': datetime.utcnow().isoformat()})


@socketio.on('task_result', namespace='/ws/agent')
def handle_task_result(data):
    """处理Agent上报的任务结果"""
    if request.sid not in online_agents:
        return

    agent_id = online_agents[request.sid]
    task_id = data.get('task_id')
    status = data.get('status')

    from app import db
    task = TestTask.query.get(task_id)
    if task:
        task.status = status
        if status in ['success', 'failed', 'cancelled']:
            task.finished_at = datetime.utcnow()
            if task.started_at:
                task.duration = (task.finished_at - task.started_at).total_seconds()
        db.session.commit()

    print(f'Task {task_id} result: {status}')


@socketio.on('task_ack', namespace='/ws/agent')
def handle_task_ack(data):
    """处理Agent任务接收确认"""
    if request.sid not in online_agents:
        return

    task_id = data.get('task_id')
    result_id = data.get('result_id')
    status = data.get('status')

    print(f'Task {task_id} (result {result_id}) acknowledged: {status}')


@socketio.on('task_complete', namespace='/ws/agent')
def handle_task_complete(data):
    """处理Agent任务完成报告"""
    if request.sid not in online_agents:
        return

    agent_id = online_agents[request.sid]
    task_id = data.get('task_id')
    result_id = data.get('result_id')
    status = data.get('status')

    try:
        from app.models.task import TaskResult

        # 更新结果记录
        result = db.session.get(TaskResult, result_id)
        if result:
            result.status = status
            result.exit_code = data.get('exit_code')
            result.duration = data.get('duration')
            result.error_type = data.get('error_type')
            result.error_message = data.get('error_message')
            result.stack_trace = data.get('stack_trace')
            result.perf_summary = data.get('perf_summary')  # 性能汇总
            result.finished_at = datetime.utcnow()

        db.session.commit()

        # 检查是否有下一个任务需要发送（串行模式）
        queue_data = redis_client.get(f'task_queue:{task_id}')
        if queue_data:
            queue_info = json.loads(queue_data)
            remaining = queue_info.get('cases', [])

            if remaining:
                # 取出下一个任务发送
                next_case = remaining.pop(0)
                next_case['agent_id'] = agent_id

                # 存储更新后的队列
                redis_client.setex(
                    f'task_queue:{task_id}',
                    3600,
                    json.dumps({
                        'cases': remaining,
                        'sent': queue_info.get('sent', 1) + 1,
                        'total': queue_info.get('total', 0)
                    })
                )

                # 发送下一个任务给 Agent
                socketio.emit('task_assign', next_case, namespace='/ws/agent')
                print(f'Task {task_id}: sent next case, {len(remaining)} remaining')
                return

        # 没有更多任务，检查任务是否全部完成
        task = db.session.get(TestTask, task_id)
        if task:
            db.session.refresh(task)
            pending_results = TaskResult.query.filter_by(task_id=task_id).filter(
                TaskResult.status.in_(['pending', 'running'])
            ).count()

            if pending_results == 0 and task.status not in ['success', 'failed', 'cancelled']:
                # 所有用例完成，汇总结果
                all_results = TaskResult.query.filter_by(task_id=task_id).all()
                failed_count = sum(1 for r in all_results if r.status == 'failed')
                error_count = sum(1 for r in all_results if r.status == 'error')

                if error_count > 0 or failed_count > 0:
                    task.status = 'failed'
                else:
                    task.status = 'success'
                task.finished_at = datetime.utcnow()
                if task.started_at:
                    task.duration = (task.finished_at - task.started_at).total_seconds()
                db.session.commit()

                # 清理 Redis 队列数据
                redis_client.delete(f'task_queue:{task_id}')

    except Exception as e:
        print(f'ERROR in task_complete: {e}')
        db.session.rollback()

    print(f'Task {task_id} (result {result_id}) completed: {status}')


@socketio.on('task_cancelled', namespace='/ws/agent')
def handle_task_cancelled(data):
    """处理Agent任务取消确认"""
    if request.sid not in online_agents:
        return

    task_id = data.get('task_id')

    from app import db
    from app.models.task import TaskResult

    # 更新所有相关结果状态
    TaskResult.query.filter_by(task_id=task_id).update({'status': 'cancelled'})

    task = TestTask.query.get(task_id)
    if task:
        task.status = 'cancelled'
        task.finished_at = datetime.utcnow()
        if task.started_at:
            task.duration = (task.finished_at - task.started_at).total_seconds()

    db.session.commit()
    print(f'Task {task_id} cancelled')


@socketio.on('log', namespace='/ws/agent')
def handle_log(data):
    """处理Agent上报的日志"""
    if request.sid not in online_agents:
        return

    task_id = data.get('task_id')
    content = data.get('content')
    result_id = data.get('result_id')

    # 存储到Redis
    log_key = f'task_logs:{task_id}'
    if result_id:
        log_key = f'task_logs:{task_id}:{result_id}'

    log_entry = json.dumps({
        'content': content,
        'timestamp': datetime.utcnow().isoformat()
    })
    redis_client.rpush(log_key, log_entry)

    # 广播给前端
    emit('task_log', {
        'task_id': task_id,
        'result_id': result_id,
        'content': content,
        'timestamp': datetime.utcnow().isoformat()
    }, namespace='/ws/agent', broadcast=True)


@socketio.on('performance', namespace='/ws/agent')
def handle_performance(data):
    """处理Agent上报的性能数据"""
    if request.sid not in online_agents:
        return

    agent_id = online_agents[request.sid]
    task_id = data.get('task_id')
    result_id = data.get('result_id')

    system_data = data.get('system', {})
    process_data = data.get('process')

    from app import db
    perf_log = PerformanceLog(
        task_id=task_id,
        result_id=result_id,
        agent_id=agent_id,
        cpu_percent=system_data.get('cpu'),
        memory_percent=system_data.get('memory'),
        load_avg_1=system_data.get('load_avg', [0, 0, 0])[0] if system_data.get('load_avg') else None,
        load_avg_5=system_data.get('load_avg', [0, 0, 0])[1] if system_data.get('load_avg') else None,
        load_avg_15=system_data.get('load_avg', [0, 0, 0])[2] if system_data.get('load_avg') else None,
        process_data=process_data,
        fd_count=system_data.get('fd_count')
    )
    db.session.add(perf_log)
    db.session.commit()

    # 广播给前端
    emit('performance', perf_log.to_dict(), namespace='/ws/client', broadcast=True)


# 前端WebSocket连接（用于实时日志）
@socketio.on('connect', namespace='/ws/client')
def client_connect():
    """前端客户端连接"""
    emit('connected', {'status': 'ok'})


@socketio.on('subscribe_task', namespace='/ws/client')
def subscribe_task(data):
    """订阅任务日志"""
    task_id = data.get('task_id')
    emit('subscribed', {'task_id': task_id})
