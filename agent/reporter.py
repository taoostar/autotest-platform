#!/usr/bin/env python3
"""
测试结果报告器
生成测试报告并上报到平台
"""

import json
import logging
import os
import time
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """测试报告器"""

    def __init__(self, platform_url: str, api_token: str):
        self.platform_url = platform_url
        self.api_token = api_token
        self.reports_dir = 'reports'
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_report(
        self,
        task_id: int,
        result_id: int,
        execution_result,
        performance_data: List[Dict],
        env_vars: Dict[str, str]
    ) -> str:
        """生成HTML报告

        Args:
            task_id: 任务ID
            result_id: 结果ID
            execution_result: 执行结果
            performance_data: 性能数据列表
            env_vars: 环境变量

        Returns:
            str: 报告文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.reports_dir, f'report_{task_id}_{timestamp}.html')

        # 计算性能统计
        stats = self._calculate_stats(performance_data)

        # 生成HTML
        html = self._build_html(
            task_id=task_id,
            result_id=result_id,
            execution_result=execution_result,
            stats=stats,
            performance_data=performance_data,
            env_vars=env_vars
        )

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"报告已生成: {report_file}")
        return report_file

    def _calculate_stats(self, performance_data: List[Dict]) -> Dict:
        """计算性能统计"""
        if not performance_data:
            return {}

        cpu_values = [p.get('cpu', 0) for p in performance_data]
        memory_values = [p.get('memory', 0) for p in performance_data]

        return {
            'cpu_avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            'cpu_max': max(cpu_values) if cpu_values else 0,
            'memory_avg': sum(memory_values) / len(memory_values) if memory_values else 0,
            'memory_max': max(memory_values) if memory_values else 0,
            'samples': len(performance_data)
        }

    def _build_html(
        self,
        task_id: int,
        result_id: int,
        execution_result,
        stats: Dict,
        performance_data: List[Dict],
        env_vars: Dict[str, str]
    ) -> str:
        """构建HTML报告"""
        status_color = 'green' if execution_result.exit_code == 0 else 'red'
        status_text = '通过' if execution_result.exit_code == 0 else '失败'

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>测试报告 - Task {task_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .status {{ display: inline-block; padding: 5px 15px; border-radius: 4px; color: white; background: {status_color}; }}
        .section {{ margin-bottom: 30px; }}
        .section h3 {{ border-left: 4px solid #1890ff; padding-left: 10px; margin-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #f5f5f5; }}
        .metric {{ display: inline-block; margin-right: 30px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #1890ff; }}
        .metric-label {{ color: #666; font-size: 14px; }}
        pre {{ background: #f5f5f5; padding: 15px; border-radius: 4px; overflow-x: auto; }}
        .env-var {{ display: inline-block; background: #e6f7ff; padding: 3px 8px; border-radius: 4px; margin: 2px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>测试报告</h1>
        <p>任务ID: {task_id} | 结果ID: {result_id}</p>
        <span class="status">{status_text}</span>
    </div>

    <div class="section">
        <h3>执行概览</h3>
        <div class="metric">
            <div class="metric-value">{execution_result.duration:.2f}s</div>
            <div class="metric-label">执行时长</div>
        </div>
        <div class="metric">
            <div class="metric-value">{execution_result.exit_code}</div>
            <div class="metric-label">退出码</div>
        </div>
        <div class="metric">
            <div class="metric-value">{stats.get('cpu_avg', 0):.1f}%</div>
            <div class="metric-label">CPU平均</div>
        </div>
        <div class="metric">
            <div class="metric-value">{stats.get('memory_avg', 0):.1f}%</div>
            <div class="metric-label">内存平均</div>
        </div>
    </div>

    <div class="section">
        <h3>环境变量</h3>
        <div>
            {''.join(f'<span class="env-var">{k}={v}</span>' for k, v in env_vars.items())}
        </div>
    </div>

    <div class="section">
        <h3>执行结果</h3>
        <table>
            <tr><th>项目</th><th>值</th></tr>
            <tr><td>Summary</td><td>{execution_result.summary or 'N/A'}</td></tr>
            <tr><td>Error Type</td><td>{execution_result.error_type or 'N/A'}</td></tr>
            <tr><td>Error Message</td><td><pre>{execution_result.error_message or 'N/A'}</pre></td></tr>
        </table>
    </div>

    <div class="section">
        <h3>标准输出</h3>
        <pre>{execution_result.stdout or '(无)'}</pre>
    </div>

    <div class="section">
        <h3>错误输出</h3>
        <pre>{execution_result.stderr or '(无)'}</pre>
    </div>

    <div class="section">
        <h3>性能数据 ({stats.get('samples', 0)} 个样本)</h3>
        <table>
            <tr>
                <th>时间</th>
                <th>CPU %</th>
                <th>内存 %</th>
                <th>IO读 MB</th>
                <th>IO写 MB</th>
                <th>文件描述符</th>
            </tr>
"""

        for p in performance_data:
            ts = p.get('timestamp', '')
            html += f"""            <tr>
                <td>{ts}</td>
                <td>{p.get('cpu', 0):.1f}</td>
                <td>{p.get('memory', 0):.1f}</td>
                <td>{p.get('io_read_mb', 0):.2f}</td>
                <td>{p.get('io_write_mb', 0):.2f}</td>
                <td>{p.get('fd_count', 0)}</td>
            </tr>
"""

        html += """        </table>
    </div>
</body>
</html>"""

        return html

    def upload_report(self, report_path: str, task_id: int) -> bool:
        """上传报告到平台

        Args:
            report_path: 报告文件路径
            task_id: 任务ID

        Returns:
            bool: 是否上传成功
        """
        try:
            import requests

            with open(report_path, 'rb') as f:
                files = {'file': (os.path.basename(report_path), f, 'text/html')}
                data = {'task_id': task_id}

                response = requests.post(
                    f'{self.platform_url}/api/tasks/{task_id}/report',
                    files=files,
                    data=data,
                    headers={'Authorization': f'Bearer {self.api_token}'},
                    timeout=30
                )

            if response.status_code == 200:
                logger.info(f"报告上传成功: {report_path}")
                return True
            else:
                logger.error(f"报告上传失败: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"报告上传异常: {e}")
            return False


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    from executor import ExecutionResult

    reporter = TestReporter('http://localhost:5000', 'test_token')

    result = ExecutionResult(
        exit_code=0,
        stdout='Test passed!',
        stderr='',
        duration=1.5,
        summary='1 passed',
        error_type=None,
        error_message=None
    )

    perf_data = [
        {'cpu': 10.5, 'memory': 45.2, 'io_read_mb': 1.2, 'io_write_mb': 0.5, 'fd_count': 5, 'timestamp': '2024-01-01 10:00:00'},
        {'cpu': 12.3, 'memory': 46.1, 'io_read_mb': 1.5, 'io_write_mb': 0.6, 'fd_count': 5, 'timestamp': '2024-01-01 10:00:05'},
    ]

    report_path = reporter.generate_report(1, 1, result, perf_data, {'ENV': 'test'})
    print(f"Report generated: {report_path}")