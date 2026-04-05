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

        def callback(task_id, data, result_id=None):
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
            self.assertIn('system', data)
            self.assertIn('cpu', data['system'])
            self.assertIn('memory', data['system'])

    def test_collector_data_values(self):
        """测试采集数据值的合理性"""
        collector = PerformanceCollector()
        collected_data = []

        def callback(task_id, data, result_id=None):
            collected_data.append(data)

        collector.start(1, callback)
        time.sleep(7)  # 等待至少一个采样周期
        collector.stop()

        for data in collected_data:
            # 系统CPU和内存在0-100之间
            self.assertGreaterEqual(data['system']['cpu'], 0)
            self.assertLessEqual(data['system']['cpu'], 100)
            self.assertGreaterEqual(data['system']['memory'], 0)
            self.assertLessEqual(data['system']['memory'], 100)


if __name__ == '__main__':
    unittest.main()