#!/usr/bin/env python3
"""
测试性能采集器
"""

import unittest
import sys
import os
import time

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collector import PerformanceCollector


class TestPerformanceCollector(unittest.TestCase):
    """性能采集器测试"""

    def test_collector_init(self):
        """测试采集器初始化"""
        collector = PerformanceCollector()

        self.assertFalse(collector.running)
        self.assertIsNone(collector.thread)
        self.assertIsNone(collector.send_callback)
        self.assertIsNone(collector.task_id)
        self.assertEqual(collector.interval, 5)

    def test_collector_start_stop(self):
        """测试采集器启动和停止"""
        collector = PerformanceCollector()
        collected_data = []

        def callback(task_id, data):
            collected_data.append(data)

        collector.start(1, callback)
        self.assertTrue(collector.running)
        self.assertIsNotNone(collector.thread)

        # 等待采集一些数据
        time.sleep(12)

        collector.stop()
        self.assertFalse(collector.running)

        # 应该采集到至少1个数据点
        self.assertGreater(len(collected_data), 0)

        # 验证数据结构
        for data in collected_data:
            self.assertIn('cpu', data)
            self.assertIn('memory', data)
            self.assertIn('io_read_mb', data)
            self.assertIn('io_write_mb', data)
            self.assertIn('fd_count', data)

    def test_collector_data_values(self):
        """测试采集数据值的合理性"""
        collector = PerformanceCollector()
        collected_data = []

        def callback(task_id, data):
            collected_data.append(data)

        collector.start(1, callback)
        time.sleep(7)  # 等待至少一个采样周期
        collector.stop()

        for data in collected_data:
            # CPU和内存应该在0-100之间
            self.assertGreaterEqual(data['cpu'], 0)
            self.assertLessEqual(data['cpu'], 100)
            self.assertGreaterEqual(data['memory'], 0)
            self.assertLessEqual(data['memory'], 100)

            # IO和FD应该是非负数
            self.assertGreaterEqual(data['io_read_mb'], 0)
            self.assertGreaterEqual(data['io_write_mb'], 0)
            self.assertGreaterEqual(data['fd_count'], 0)


if __name__ == '__main__':
    unittest.main()