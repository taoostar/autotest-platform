#!/usr/bin/env python3
"""
测试报告器
"""

import unittest
import sys
import os
import tempfile
import shutil

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reporter import ReportGenerator
from executor import ExecutionResult


class TestTestReporter(unittest.TestCase):
    """测试报告器测试"""

    def setUp(self):
        self.reporter = ReportGenerator('http://localhost:5000', 'test_token')
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # 清理测试目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_reporter_init(self):
        """测试报告器初始化"""
        self.assertEqual(self.reporter.platform_url, 'http://localhost:5000')
        self.assertEqual(self.reporter.api_token, 'test_token')
        self.assertEqual(self.reporter.reports_dir, 'reports')

    def test_calculate_stats_empty(self):
        """测试空数据统计"""
        stats = self.reporter._calculate_stats([])

        self.assertEqual(stats, {})

    def test_calculate_stats(self):
        """测试数据统计"""
        performance_data = [
            {'cpu': 10.0, 'memory': 20.0, 'io_read_mb': 1.0, 'io_write_mb': 0.5, 'fd_count': 5, 'timestamp': '2024-01-01 10:00:00'},
            {'cpu': 20.0, 'memory': 30.0, 'io_read_mb': 2.0, 'io_write_mb': 1.0, 'fd_count': 6, 'timestamp': '2024-01-01 10:00:05'},
        ]

        stats = self.reporter._calculate_stats(performance_data)

        self.assertEqual(stats['cpu_avg'], 15.0)
        self.assertEqual(stats['cpu_max'], 20.0)
        self.assertEqual(stats['memory_avg'], 25.0)
        self.assertEqual(stats['memory_max'], 30.0)
        self.assertEqual(stats['samples'], 2)

    def test_generate_report_success(self):
        """测试生成成功报告"""
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

        report_path = self.reporter.generate_report(1, 1, result, perf_data, {'ENV': 'test'})

        self.assertTrue(os.path.exists(report_path))
        self.assertTrue('report_1_' in os.path.basename(report_path))
        self.assertTrue('.html' in os.path.basename(report_path))

        # 验证HTML内容
        with open(report_path, 'r') as f:
            content = f.read()
            self.assertIn('测试报告', content)
            self.assertIn('通过', content)
            self.assertIn('1 passed', content)

    def test_generate_report_failure(self):
        """测试生成失败报告"""
        result = ExecutionResult(
            exit_code=1,
            stdout='',
            stderr='AssertionError: 1 != 2',
            duration=0.5,
            summary='1 failed',
            error_type='AssertionError',
            error_message='AssertionError: 1 != 2'
        )

        perf_data = []

        report_path = self.reporter.generate_report(1, 1, result, perf_data, {})

        self.assertTrue(os.path.exists(report_path))

        with open(report_path, 'r') as f:
            content = f.read()
            self.assertIn('失败', content)
            self.assertIn('AssertionError', content)

    def test_build_html_structure(self):
        """测试HTML结构"""
        result = ExecutionResult(
            exit_code=0,
            stdout='Test passed!',
            stderr='',
            duration=1.5,
            summary='1 passed'
        )

        html = self.reporter._build_html(
            task_id=1,
            result_id=1,
            execution_result=result,
            stats={'cpu_avg': 10.0, 'memory_avg': 45.0, 'samples': 2},
            performance_data=[],
            env_vars={'TEST': 'value'}
        )

        # 验证HTML结构
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('<html>', html)
        self.assertIn('<head>', html)
        self.assertIn('<body>', html)
        self.assertIn('测试报告', html)
        self.assertIn('TEST=value', html)
        self.assertIn('执行概览', html)
        self.assertIn('性能数据', html)


if __name__ == '__main__':
    unittest.main()