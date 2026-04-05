#!/usr/bin/env python3
"""
性能数据采集器
采集CPU、内存、IO、文件描述符等数据
支持系统性能和指定进程的性能监控
"""

import logging
import os
import threading
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class PerformanceCollector:
    """性能数据采集器"""

    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.send_callback: Optional[Callable] = None
        self.task_id: Optional[int] = None
        self.result_id: Optional[int] = None
        self.process_keyword: Optional[str] = None
        self.interval = 5  # 采集间隔（秒）
        self._perf_samples = []  # 存储采样用于汇总

    def start(self, task_id: int, send_callback: Callable, result_id: int = None, process_keyword: str = None):
        """开始采集

        Args:
            task_id: 任务ID
            send_callback: 发送数据的回调函数
            result_id: 用例结果ID（用于关联性能数据）
            process_keyword: 进程关键字（用于匹配目标进程）
        """
        self.running = True
        self.send_callback = send_callback
        self.task_id = task_id
        self.result_id = result_id
        self.process_keyword = process_keyword
        self._perf_samples = []
        self.thread = threading.Thread(target=self._collect_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"性能采集已启动: task_id={task_id}, keyword={process_keyword}")

    def stop(self):
        """停止采集"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("性能采集已停止")

    def get_summary(self):
        """计算性能汇总"""
        if not self._perf_samples:
            return None

        system_cpus = [s['system']['cpu'] for s in self._perf_samples if s.get('system')]
        system_memories = [s['system']['memory'] for s in self._perf_samples if s.get('system')]
        system_loads = []
        for s in self._perf_samples:
            if s.get('system') and s['system'].get('load_avg'):
                system_loads.append(max(s['system']['load_avg']))

        summary = {
            'system': {
                'cpu_avg': round(sum(system_cpus) / len(system_cpus), 2) if system_cpus else 0,
                'cpu_max': max(system_cpus) if system_cpus else 0,
                'memory_avg': round(sum(system_memories) / len(system_memories), 2) if system_memories else 0,
                'memory_max': max(system_memories) if system_memories else 0,
                'load_avg_max': round(max(system_loads), 2) if system_loads else 0
            }
        }

        # 进程汇总
        process_samples = [s.get('process') for s in self._perf_samples if s.get('process')]
        if process_samples and self.process_keyword:
            proc_cpus = [p['cpu'] for p in process_samples]
            proc_memories = [p['memory'] for p in process_samples]
            proc_fds = [p['fd_count'] for p in process_samples]
            summary['process'] = {
                'keyword': self.process_keyword,
                'cpu_avg': round(sum(proc_cpus) / len(proc_cpus), 2),
                'cpu_max': max(proc_cpus),
                'memory_avg': round(sum(proc_memories) / len(proc_memories), 2),
                'memory_max': max(proc_memories),
                'fd_count_max': max(proc_fds)
            }

        return summary

    def _find_target_process(self):
        """根据关键字查找目标进程

        Returns:
            psutil.Process 对象或 None
        """
        if not self.process_keyword:
            return None

        try:
            import psutil
        except ImportError:
            logger.warning("psutil未安装，无法采集进程性能数据")
            return None

        candidates = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline') or [])
                if self.process_keyword in cmdline:
                    candidates.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not candidates:
            return None

        # 取 CPU 使用率最高的
        try:
            return max(candidates, key=lambda p: p.cpu_percent())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def _collect_loop(self):
        """采集循环"""
        try:
            import psutil
        except ImportError:
            logger.warning("psutil未安装，无法采集性能数据")
            return

        while self.running:
            try:
                # 系统性能
                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory().percent
                try:
                    load_avg = os.getloadavg()
                except Exception:
                    load_avg = (0, 0, 0)

                # 系统级文件描述符总数
                try:
                    fd_count = len(psutil.Process().open_files())
                except Exception:
                    fd_count = 0

                # 进程性能
                process_info = None
                if self.process_keyword:
                    target = self._find_target_process()
                    if target:
                        try:
                            process_info = {
                                'keyword': self.process_keyword,
                                'pid': target.pid,
                                'cpu': target.cpu_percent(),
                                'memory': target.memory_percent(),
                                'fd_count': target.num_fds(),
                                'status': target.status()
                            }
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                perf_data = {
                    'system': {
                        'cpu': cpu,
                        'memory': memory,
                        'load_avg': list(load_avg),
                        'fd_count': fd_count
                    },
                    'process': process_info
                }

                self._perf_samples.append(perf_data)

                if self.send_callback and self.task_id:
                    self.send_callback(self.task_id, perf_data, self.result_id)

            except Exception as e:
                logger.error(f"性能采集错误: {e}")

            time.sleep(self.interval)


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    collector = PerformanceCollector()

    def test_callback(task_id, data, result_id=None):
        print(f"Task {task_id}: CPU={data['system']['cpu']:.1f}%, Memory={data['system']['memory']:.1f}%")
        if data.get('process'):
            print(f"  Process: {data['process']}")

    collector.start(1, test_callback, result_id=1, process_keyword='python')
    time.sleep(12)
    collector.stop()
    print(f"Summary: {collector.get_summary()}")
    print("Test completed")
