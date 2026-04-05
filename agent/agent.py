#!/usr/bin/env python3
"""
AutoTest Platform - Agent Client
运行在测试机上，负责接收任务并执行测试用例
"""

import json
import logging
import os
import signal
import socket
import sys
import time
import threading
from datetime import datetime

import socketio

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentNamespace(socketio.ClientNamespace):
    """Agent WebSocket命名空间"""

    def __init__(self, agent):
        super().__init__('/ws/agent')
        self.agent = agent

    def on_connect(self):
        logger.info("已连接到平台 /ws/agent")
        self.agent._register()

    def on_disconnect(self):
        logger.info("与平台断开连接")

    def on_connected(self, data):
        logger.info(f"Agent注册成功，状态: {data.get('status')}")

    def on_heartbeat_ack(self, data):
        pass

    def on_task_assign(self, data):
        logger.info(f"收到任务: {data.get('task_id')}")
        self.agent._handle_task_assign(data)

    def on_task_cancel(self, data):
        logger.info(f"收到取消任务: {data.get('task_id')}")
        self.agent._handle_task_cancel(data)


class Agent:
    """测试Agent"""

    def __init__(self, config_path='config.yaml'):
        self.config = self._load_config(config_path)
        self.agent_id = self.config['agent_id']
        self.platform_url = self.config['platform_url']
        self.heartbeat_interval = self.config.get('heartbeat_interval', 30)
        self.performance_interval = self.config.get('performance_interval', 5)

        self.running = True
        self.current_task = None
        self.sio = None

        from executor import Executor
        from collector import PerformanceCollector

        self.executor = Executor()
        self.performance_collector = PerformanceCollector()

        # 信号处理
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _load_config(self, config_path):
        """加载配置"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _handle_shutdown(self, signum, frame):
        """处理关闭信号"""
        logger.info("收到关闭信号，正在停止Agent...")
        self.running = False
        if self.sio:
            self.sio.disconnect()

    def connect(self):
        """连接到平台WebSocket"""
        self.sio = socketio.Client()

        # 注册命名空间
        self.ns = AgentNamespace(self)
        self.sio.register_namespace(self.ns)

        while self.running:
            try:
                # 构建带token的URL
                url = f"{self.platform_url}?token={self.agent_id}"
                logger.info(f"正在连接到平台: {url}")
                self.sio.connect(
                    url,
                    transports=['websocket'],
                    wait=False
                )
                self.sio.wait()
            except Exception as e:
                logger.error(f"连接失败: {e}")
                if self.running:
                    time.sleep(5)

    def _register(self):
        """注册Agent"""
        hostname = socket.gethostname()
        os_type = 'linux' if sys.platform.startswith('linux') else 'windows'

        self.sio.emit('register', {
            'agent_id': self.agent_id,
            'hostname': hostname,
            'os_type': os_type,
            'labels': self.config.get('labels', [])
        }, namespace='/ws/agent')
        logger.info("已发送注册信息")

    def _send_heartbeat(self):
        """发送心跳"""
        try:
            import psutil
            load = psutil.cpu_percent() / 100.0
        except:
            load = 0

        self.sio.emit('heartbeat', {
            'agent_id': self.agent_id,
            'status': 'idle' if not self.current_task else 'busy',
            'load': load
        }, namespace='/ws/agent')

    def _handle_task_assign(self, data):
        """处理任务下发"""
        task_id = data.get('task_id')
        result_id = data.get('result_id', 1)
        logger.info(f"处理任务: {task_id}, result_id: {result_id}")

        # 确认接收
        self.sio.emit('task_ack', {
            'type': 'task_ack',
            'task_id': task_id,
            'result_id': result_id,
            'status': 'received'
        }, namespace='/ws/agent')

        # 执行任务
        self.current_task = task_id
        thread = threading.Thread(target=self._execute_task, args=(data, result_id))
        thread.daemon = True
        thread.start()

    def _execute_task(self, task_data, result_id):
        """执行任务"""
        task_id = task_data.get('task_id')
        script_content = task_data.get('script_content', '')
        script_type = task_data.get('script_type', 'python')
        timeout = task_data.get('timeout', 300)
        env_vars = task_data.get('env_vars', {})

        def log_callback(content):
            """日志回调"""
            if self.sio and self.running:
                try:
                    self.sio.emit('log', {
                        'type': 'log',
                        'task_id': task_id,
                        'result_id': result_id,
                        'content': content,
                        'timestamp': datetime.utcnow().isoformat()
                    }, namespace='/ws/agent')
                except Exception as e:
                    logger.error(f"发送性能数据失败: {e}")

        try:
            # 启动性能采集
            def perf_callback(tid, data):
                if self.sio and self.running:
                    try:
                        self.sio.emit('performance', {
                            'type': 'performance',
                            'task_id': tid,
                            'agent_id': self.agent_id,
                            **data,
                            'timestamp': datetime.utcnow().isoformat()
                        }, namespace='/ws/agent')
                    except:
                        pass

            self.performance_collector.start(task_id, perf_callback)

            # 执行脚本
            result = self.executor.execute(
                script_content,
                script_type,
                timeout,
                env_vars,
                log_callback
            )

            # 上报结果
            self._report_result(task_id, result_id, result)

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            self._report_error(task_id, result_id, str(e))

        finally:
            self.performance_collector.stop()
            self.current_task = None

    def _report_result(self, task_id, result_id, result):
        """上报执行结果"""
        self.sio.emit('task_complete', {
            'type': 'task_complete',
            'task_id': task_id,
            'result_id': result_id,
            'status': 'passed' if result.exit_code == 0 else 'failed',
            'exit_code': result.exit_code,
            'duration': result.duration,
            'summary': result.summary,
            'error_type': result.error_type,
            'error_message': result.error_message,
            'stack_trace': result.stack_trace,
            'screenshots': result.screenshots or []
        }, namespace='/ws/agent')
        logger.info(f"任务 {task_id} 完成: {result.summary}")

    def _report_error(self, task_id, result_id, error_msg):
        """上报执行错误"""
        self.sio.emit('task_complete', {
            'type': 'task_complete',
            'task_id': task_id,
            'result_id': result_id,
            'status': 'error',
            'exit_code': -1,
            'duration': 0,
            'error_type': 'ExecutionError',
            'error_message': error_msg
        }, namespace='/ws/agent')

    def _handle_task_cancel(self, data):
        """处理取消任务"""
        task_id = data.get('task_id')
        logger.info(f"收到取消任务: {task_id}")

        if self.current_task == task_id:
            self.executor.cancel()
            self.sio.emit('task_cancelled', {
                'type': 'task_cancelled',
                'task_id': task_id
            }, namespace='/ws/agent')

    def run(self):
        """运行Agent"""
        logger.info(f"启动Agent {self.agent_id}")
        self.connect()


if __name__ == '__main__':
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
    agent = Agent(config_path)
    agent.run()