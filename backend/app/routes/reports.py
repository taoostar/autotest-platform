from flask import Blueprint, request, jsonify, render_template_string, make_response
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models.task import TestTask, TaskResult

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    """获取概览统计"""
    days = request.args.get('days', 7, type=int)

    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days-1)

    # 今日统计
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today + timedelta(days=1), datetime.min.time())

    today_tasks = TestTask.query.filter(
        TestTask.created_at >= today_start,
        TestTask.created_at < today_end
    ).all()

    today_stats = {
        'success': sum(1 for t in today_tasks if t.status == 'success'),
        'failed': sum(1 for t in today_tasks if t.status == 'failed'),
        'running': sum(1 for t in today_tasks if t.status == 'running'),
        'pending': sum(1 for t in today_tasks if t.status == 'pending'),
        'cancelled': sum(1 for t in today_tasks if t.status == 'cancelled'),
    }

    # 7天趋势
    trend = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day + timedelta(days=1), datetime.min.time())

        tasks = TestTask.query.filter(
            TestTask.created_at >= day_start,
            TestTask.created_at < day_end
        ).all()

        total = len(tasks)
        passed = sum(1 for t in tasks if t.status == 'success')

        trend.append({
            'date': day.isoformat(),
            'total': total,
            'passed': passed,
            'pass_rate': (passed / total * 100) if total > 0 else 0
        })

    return jsonify({
        'today': today_stats,
        'trend': trend
    })


@reports_bp.route('/trend', methods=['GET'])
@jwt_required()
def get_trend():
    """获取趋势数据"""
    days = request.args.get('days', 7, type=int)
    trend_type = request.args.get('type', 'pass_rate')  # pass_rate/total/duration

    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days-1)

    trend = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day + timedelta(days=1), datetime.min.time())

        tasks = TestTask.query.filter(
            TestTask.created_at >= day_start,
            TestTask.created_at < day_end
        ).all()

        total = len(tasks)
        passed = sum(1 for t in tasks if t.status == 'success')
        failed = sum(1 for t in tasks if t.status == 'failed')
        avg_duration = sum(t.duration or 0 for t in tasks) / total if total > 0 else 0

        if trend_type == 'pass_rate':
            value = (passed / total * 100) if total > 0 else 0
        elif trend_type == 'total':
            value = total
        elif trend_type == 'duration':
            value = round(avg_duration, 2)
        else:
            value = total

        trend.append({
            'date': day.isoformat(),
            'value': value
        })

    return jsonify({
        'type': trend_type,
        'data': trend
    })


@reports_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task_report(task_id):
    """获取任务报告"""
    task = TestTask.query.get_or_404(task_id)
    results = TaskResult.query.filter_by(task_id=task_id).all()

    summary = {
        'total': len(results),
        'passed': sum(1 for r in results if r.status == 'passed'),
        'failed': sum(1 for r in results if r.status == 'failed'),
        'error': sum(1 for r in results if r.status == 'error'),
        'cancelled': sum(1 for r in results if r.status == 'cancelled'),
    }

    return jsonify({
        'task': task.to_dict(),
        'summary': summary,
        'results': [r.to_dict() for r in results]
    })


@reports_bp.route('/<int:task_id>/export', methods=['GET'])
@jwt_required()
def export_report(task_id):
    """导出报告"""
    task = TestTask.query.get_or_404(task_id)
    results = TaskResult.query.filter_by(task_id=task_id).all()

    if task.status in ['pending', 'running']:
        return jsonify({'error': '任务进行中，无法导出'}), 400

    summary = {
        'total': len(results),
        'passed': sum(1 for r in results if r.status == 'passed'),
        'failed': sum(1 for r in results if r.status == 'failed'),
        'pass_rate': (sum(1 for r in results if r.status == 'passed') / len(results) * 100) if results else 0
    }

    # 返回HTML报告
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>测试报告 - Task #{task.id}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
            .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
            .summary {{ display: flex; gap: 20px; margin-bottom: 30px; }}
            .card {{ padding: 20px; background: #f5f5f5; border-radius: 8px; flex: 1; text-align: center; }}
            .metric {{ font-size: 32px; font-weight: bold; margin-bottom: 8px; }}
            .passed {{ color: #52c41a; }}
            .failed {{ color: #ff4d4f; }}
            .rate {{ color: #1890ff; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #667eea; color: white; }}
            tr:hover {{ background: #f5f5f5; }}
            .footer {{ margin-top: 30px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>测试报告 - Task #{task.id}</h1>
            <p>计划ID: {task.plan_id} | Agent: {task.agent_id or '-'} | 触发: {task.trigger_type}</p>
            <p>开始时间: {task.started_at.isoformat() if task.started_at else '-'} | 结束时间: {task.finished_at.isoformat() if task.finished_at else '-'}</p>
        </div>
        <div class="summary">
            <div class="card">
                <div class="metric">{summary['total']}</div>
                <div>总用例</div>
            </div>
            <div class="card">
                <div class="metric passed">{summary['passed']}</div>
                <div>通过</div>
            </div>
            <div class="card">
                <div class="metric failed">{summary['failed']}</div>
                <div>失败</div>
            </div>
            <div class="card">
                <div class="metric rate">{summary['pass_rate']:.1f}%</div>
                <div>通过率</div>
            </div>
        </div>
        <table>
            <tr>
                <th>ID</th>
                <th>用例ID</th>
                <th>状态</th>
                <th>耗时</th>
                <th>错误类型</th>
                <th>错误信息</th>
            </tr>
    """

    for r in results:
        status_class = 'passed' if r.status == 'passed' else 'failed'
        error_msg = (r.error_message or '').replace('<', '&lt;').replace('>', '&gt;')
        html += f"""
            <tr>
                <td>{r.id}</td>
                <td>{r.case_id}</td>
                <td class="{status_class}">{r.status}</td>
                <td>{r.duration:.2f}s</td>
                <td>{r.error_type or '-'}</td>
                <td>{error_msg[:200]}</td>
            </tr>
        """

    html += """
        </table>
        <div class="footer">
            <p>生成时间: """ + datetime.utcnow().isoformat() + """ | AutoTest Platform</p>
        </div>
    </body>
    </html>
    """

    response = make_response(html)
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = f'attachment; filename=report_task_{task_id}.html'
    return response