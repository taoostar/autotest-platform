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

        # 任务队列管理（支持串行/并行执行）
        self.pending_tasks = []           # 待执行任务队列
        self.running_tasks = {}          # {result_id: task_data} 正在执行的任务
        self.max_concurrency = 10       # Agent 最大并发数

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

    def _process_next_serial(self):
        """串行模式：处理下一个任务"""
        if not self.pending_tasks:
            return

        # 检查是否正在执行任务
        if self.running_tasks:
            return  # 已有任务在执行，等待完成

        task = self.pending_tasks.pop(0)
        self._start_task(task)

    def _start_task(self, task_data):
        """启动任务执行"""
        result_id = task_data.get('result_id')
        self.running_tasks[result_id] = task_data
        self.current_task = task_data.get('task_id')

        thread = threading.Thread(target=self._execute_task, args=(task_data, result_id))
        thread.daemon = True
        thread.start()

    def _execute_task(self, task_data, result_id):
        """执行任务"""
        task_id = task_data.get('task_id')
        script_content = task_data.get('script_content', '')
        script_type = task_data.get('script_type', 'python')
        timeout = task_data.get('timeout', 300)
        env_vars = task_data.get('env_vars', {})
        process_keyword = task_data.get('process_keyword')  # 进程关键字
        logger.info(f"_execute_task: process_keyword={process_keyword}, task_data keys={list(task_data.keys())}")

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
                    logger.error(f"发送日志失败: {e}")

        try:
            # 启动性能采集
            def perf_callback(tid, data, rid=None):
                if self.sio and self.running:
                    try:
                        self.sio.emit('performance', {
                            'type': 'performance',
                            'task_id': tid,
                            'result_id': rid or result_id,
                            'agent_id': self.agent_id,
                            **data,
                            'timestamp': datetime.utcnow().isoformat()
                        }, namespace='/ws/agent')
                    except:
                        pass

            self.performance_collector.start(
                task_id, perf_callback,
                result_id=result_id,
                process_keyword=process_keyword
            )

            # 执行脚本
            result = self.executor.execute(
                script_content,
                script_type,
                timeout,
                env_vars,
                log_callback
            )

            # 获取性能汇总
            perf_summary = self.performance_collector.get_summary()

            # 上报结果
            self._report_result(task_id, result_id, result, perf_summary)

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            self._report_error(task_id, result_id, str(e))

        finally:
            self.performance_collector.stop()
            # 从运行中移除
            if result_id in self.running_tasks:
                del self.running_tasks[result_id]

            # 串行模式：完成后处理下一个任务
            if task_data.get('concurrency') == 1:
                self.current_task = None
                self._process_next_serial()
            else:
                # 并行模式：检查是否有等待的任务
                if self.pending_tasks:
                    next_task = self.pending_tasks.pop(0)
                    self._start_task(next_task)
                elif not self.running_tasks:
                    self.current_task = None

    def _handle_task_assign(self, data):
        """处理任务下发"""
        task_id = data.get('task_id')
        result_id = data.get('result_id', 1)
        concurrency = data.get('concurrency', 1)  # 1=串行, >1=并行
        logger.info(f"处理任务: {task_id}, result_id: {result_id}, concurrency={concurrency}, keyword={data.get('process_keyword')}")

        # 确认接收
        self.sio.emit('task_ack', {
            'type': 'task_ack',
            'task_id': task_id,
            'result_id': result_id,
            'status': 'received'
        }, namespace='/ws/agent')

        if concurrency == 1:
            # 串行模式：加入待执行队列
            self.pending_tasks.append(data)
            self._process_next_serial()
        else:
            # 并行模式：直接执行（受 max_concurrency 限制）
            if len(self.running_tasks) < self.max_concurrency:
                self._start_task(data)
            else:
                # 队列已满，等待
                self.pending_tasks.append(data)

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
            def perf_callback(tid, data, rid=None):
                if self.sio and self.running:
                    try:
                        self.sio.emit('performance', {
                            'type': 'performance',
                            'task_id': tid,
                            'result_id': rid,
                            'agent_id': self.agent_id,
                            **data,
                            'timestamp': datetime.utcnow().isoformat()
                        }, namespace='/ws/agent')
                    except:
                        pass

            self.performance_collector.start(task_id, perf_callback, result_id=task_id)

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

    def _report_result(self, task_id, result_id, result, perf_summary=None):
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
            'screenshots': result.screenshots or [],
            'perf_summary': perf_summary
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