#!/usr/bin/env python3
"""
性能数据采集器
采集CPU、内存、IO、文件描述符等数据
"""

import logging
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
        self.interval = 5  # 采集间隔（秒）

    def start(self, task_id: int, send_callback: Callable):
        """开始采集
        
        Args:
            task_id: 任务ID
            send_callback: 发送数据的回调函数
        """
        self.running = True
        self.send_callback = send_callback
        self.task_id = task_id
        self.thread = threading.Thread(target=self._collect_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"性能采集已启动: task_id={task_id}")

    def stop(self):
        """停止采集"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("性能采集已停止")

    def _collect_loop(self):
        """采集循环"""
        try:
            import psutil
        except ImportError:
            logger.warning("psutil未安装，无法采集性能数据")
            return

        while self.running:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)

                # 内存使用率
                memory = psutil.virtual_memory()
                memory_percent = memory.percent

                # IO统计
                try:
                    io = psutil.disk_io_counters()
                    io_read_mb = io.read_bytes / (1024 * 1024) if io else 0
                    io_write_mb = io.write_bytes / (1024 * 1024) if io else 0
                except:
                    io_read_mb = 0
                    io_write_mb = 0

                # 文件描述符数量
                try:
                    process = psutil.Process()
                    fd_count = len(process.open_files())
                except:
                    fd_count = 0

                # 发送数据
                if self.send_callback and self.task_id:
                    self.send_callback(self.task_id, {
                        'cpu': cpu_percent,
                        'memory': memory_percent,
                        'io_read_mb': io_read_mb,
                        'io_write_mb': io_write_mb,
                        'fd_count': fd_count
                    })

                time.sleep(self.interval)

            except Exception as e:
                logger.error(f"性能采集错误: {e}")
                time.sleep(self.interval)


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    collector = PerformanceCollector()
    
    def test_callback(task_id, data):
        print(f"Task {task_id}: CPU={data['cpu']:.1f}%, Memory={data['memory']:.1f}%")
    
    collector.start(1, test_callback)
    time.sleep(12)
    collector.stop()
    print("Test completed")
