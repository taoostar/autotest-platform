#!/usr/bin/env python3
"""
测试执行器
"""

import unittest
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from executor import Executor, ExecutionResult


class TestExecutor(unittest.TestCase):
    """执行器测试"""

    def setUp(self):
        self.executor = Executor()

    def test_execute_python_success(self):
        """测试Python脚本执行成功"""
        script = '''
def add(a, b):
    return a + b

result = add(1, 2)
assert result == 3, f"Expected 3, got {result}"
print("Test passed!")
'''
        result = self.executor.execute(script, 'python', 30, {})

        self.assertEqual(result.exit_code, 0)
        self.assertIn('Test passed!', result.stdout)
        self.assertIsNotNone(result.duration)
        self.assertGreater(result.duration, 0)

    def test_execute_python_failure(self):
        """测试Python脚本执行失败"""
        script = '''
def test_fail():
    assert 1 == 2, "1 should equal 2"
print("This should not print")

test_fail()
'''
        result = self.executor.execute(script, 'python', 30, {})

        self.assertNotEqual(result.exit_code, 0)
        self.assertIsNotNone(result.error_message)

    def test_execute_shell_success(self):
        """测试Shell脚本执行成功"""
        script = '''
echo "Hello, World!"
exit 0
'''
        result = self.executor.execute(script, 'shell', 30, {})

        self.assertEqual(result.exit_code, 0)
        self.assertIn('Hello, World!', result.stdout)

    def test_execute_shell_failure(self):
        """测试Shell脚本执行失败"""
        script = '''
echo "This will fail"
exit 1
'''
        result = self.executor.execute(script, 'shell', 30, {})

        self.assertNotEqual(result.exit_code, 0)

    def test_execute_javascript_success(self):
        """测试JavaScript脚本执行成功"""
        script = '''
function add(a, b) {
    return a + b;
}
console.log("Result:", add(1, 2));
'''
        result = self.executor.execute(script, 'javascript', 30, {})

        self.assertEqual(result.exit_code, 0)
        self.assertIn('Result:', result.stdout)

    def test_execute_with_env_vars(self):
        """测试带环境变量执行"""
        script = '''
import os
value = os.environ.get('TEST_VAR', 'not found')
print(f"TEST_VAR={value}")
assert value == "test_value", f"Expected 'test_value', got '{value}'"
'''
        result = self.executor.execute(script, 'python', 30, {'TEST_VAR': 'test_value'})

        self.assertEqual(result.exit_code, 0)
        self.assertIn('TEST_VAR=test_value', result.stdout)

    def test_execute_cancel(self):
        """测试取消执行"""
        script = '''
import time
for i in range(100):
    print(i)
    time.sleep(0.5)
'''
        self.executor.execute(script, 'python', 10, {})
        self.executor.cancel()

        # 取消后再次执行应该可以正常完成
        script2 = '''
print("After cancel")
'''
        result = self.executor.execute(script2, 'python', 30, {})
        self.assertEqual(result.exit_code, 0)

    def test_build_command(self):
        """测试命令构建"""
        cmd = self.executor._build_command('python', '/tmp/test.py')
        self.assertEqual(cmd, ['python3', '/tmp/test.py'])

        cmd = self.executor._build_command('shell', '/tmp/test.sh')
        self.assertEqual(cmd, ['bash', '/tmp/test.sh'])

        cmd = self.executor._build_command('javascript', '/tmp/test.js')
        self.assertEqual(cmd, ['node', '/tmp/test.js'])

    def test_get_suffix(self):
        """测试文件后缀"""
        self.assertEqual(self.executor._get_suffix('python'), '.py')
        self.assertEqual(self.executor._get_suffix('shell'), '.sh')
        self.assertEqual(self.executor._get_suffix('javascript'), '.js')


class TestExecutionResult(unittest.TestCase):
    """执行结果测试"""

    def test_execution_result_creation(self):
        """测试结果创建"""
        result = ExecutionResult(
            exit_code=0,
            stdout='test output',
            stderr='',
            duration=1.5,
            summary='1 passed'
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, 'test output')
        self.assertEqual(result.duration, 1.5)
        self.assertEqual(result.summary, '1 passed')
        self.assertIsNone(result.error_type)


if __name__ == '__main__':
    unittest.main()