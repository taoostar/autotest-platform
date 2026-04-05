#!/usr/bin/env python3
"""
测试用例执行器
支持Python/Shell/JavaScript脚本执行
"""

import logging
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """执行结果"""
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    summary: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    screenshots: list = None


class Executor:
    """用例执行器"""

    # 脚本类型对应的执行命令
    EXECUTORS = {
        'python': ['python3', '{script}'],
        'python3': ['python3', '{script}'],
        'shell': ['bash', '{script}'],
        'bash': ['bash', '{script}'],
        'javascript': ['node', '{script}'],
        'js': ['node', '{script}'],
    }

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.cancelled = False

    def execute(self, script_content: str, script_type: str,
                timeout: int, env_vars: Dict[str, str], log_callback=None) -> ExecutionResult:
        """
        执行脚本

        Args:
            script_content: 脚本内容
            script_type: 脚本类型 (python/shell/javascript)
            timeout: 超时时间（秒）
            env_vars: 环境变量
            log_callback: 日志回调函数

        Returns:
            ExecutionResult: 执行结果
        """
        self.cancelled = False
        start_time = time.time()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=self._get_suffix(script_type),
            delete=False
        ) as f:
            f.write(script_content)
            script_path = f.name

        try:
            # 构建命令
            cmd = self._build_command(script_type, script_path)

            # 设置环境变量
            env = os.environ.copy()
            env.update(env_vars)

            # 执行
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )

            # 实时读取输出
            stdout_lines = []
            stderr_lines = []

            try:
                # 读取stdout
                import select
                while True:
                    reads = [self.process.stdout.fileno(), self.process.stderr.fileno()]
                    ret = select.select(reads, [], [], 0.1)

                    if self.process.stdout.fileno() in ret[0]:
                        line = self.process.stdout.readline()
                        if line:
                            stdout_lines.append(line)
                            if log_callback:
                                log_callback(line.strip())
                            if 'PASSED' in line or 'FAILED' in line or 'passed' in line or 'failed' in line:
                                logger.info(line.strip())

                    if self.process.stderr.fileno() in ret[0]:
                        line = self.process.stderr.readline()
                        if line:
                            stderr_lines.append(line)
                            if log_callback:
                                log_callback(f"[ERROR] {line.strip()}")

                    # 检查进程是否结束
                    if self.process.poll() is not None:
                        break

                exit_code = self.process.returncode
                stdout = ''.join(stdout_lines)
                stderr = ''.join(stderr_lines)

            except Exception as e:
                # Windows或其他不支持select的平台，回退到普通方式
                stdout, stderr = self.process.communicate()
                exit_code = self.process.returncode
                if log_callback:
                    for line in stdout.split('\n'):
                        if line.strip():
                            log_callback(line.strip())

            duration = time.time() - start_time

            # 解析结果
            result = self._parse_result(
                exit_code, stdout, stderr, duration
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"执行异常: {e}")

            return ExecutionResult(
                exit_code=-1,
                stdout='',
                stderr=str(e),
                duration=duration,
                error_type=type(e).__name__,
                error_message=str(e)
            )

        finally:
            # 清理临时文件
            try:
                os.unlink(script_path)
            except:
                pass

    def _build_command(self, script_type: str, script_path: str) -> list:
        """构建执行命令"""
        template = self.EXECUTORS.get(script_type, ['python3', '{script}'])
        return [cmd.replace('{script}', script_path) for cmd in template]

    def _get_suffix(self, script_type: str) -> str:
        """获取文件后缀"""
        suffixes = {
            'python': '.py',
            'python3': '.py',
            'shell': '.sh',
            'bash': '.sh',
            'javascript': '.js',
            'js': '.js'
        }
        return suffixes.get(script_type, '.txt')

    def _parse_result(self, exit_code: int, stdout: str,
                     stderr: str, duration: float) -> ExecutionResult:
        """解析执行结果"""
        # 尝试从stdout解析pytest结果
        summary = None
        if 'passed' in stdout or 'failed' in stdout:
            for line in stdout.split('\n'):
                if 'passed' in line or 'failed' in line:
                    summary = line.strip()
                    break

        # 确定错误信息
        error_type = None
        error_message = None
        stack_trace = None

        if exit_code != 0:
            if 'AssertionError' in stderr:
                error_type = 'AssertionError'
                error_message = self._extract_error_message(stderr, 'AssertionError')
                stack_trace = stderr
            elif 'Error' in stderr:
                error_type = 'Error'
                error_message = self._extract_error_message(stderr, 'Error')
                stack_trace = stderr
            else:
                error_type = 'ExecutionError'
                error_message = stderr[:500] if stderr else 'Unknown error'
                stack_trace = stderr

        return ExecutionResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration=duration,
            summary=summary or (f"Exit code: {exit_code}"),
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            screenshots=[]
        )

    def _extract_error_message(self, text: str, error_type: str) -> str:
        """提取错误信息"""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if error_type in line:
                # 返回该行及后续几行
                return '\n'.join(lines[i:i+3])
        return text[:200]

    def cancel(self):
        """取消执行"""
        self.cancelled = True
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


if __name__ == '__main__':
    # 简单测试
    import logging
    logging.basicConfig(level=logging.INFO)
    
    executor = Executor()
    
    # 测试Python脚本
    script = '''
def test_example():
    assert 1 + 1 == 2
    print("Test passed!")

test_example()
'''
    
    result = executor.execute(script, 'python', 30, {})
    print(f"Exit code: {result.exit_code}")
    print(f"Duration: {result.duration:.2f}s")
    print(f"Summary: {result.summary}")
