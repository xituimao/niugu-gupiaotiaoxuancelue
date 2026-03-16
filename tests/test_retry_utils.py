"""
测试重试工具模块
"""

import unittest
from unittest.mock import Mock, patch
import time

from src.retry_utils import retry_on_exception, retry_with_fallback


class TestRetryOnException(unittest.TestCase):
    """测试 retry_on_exception 装饰器"""

    def test_success_on_first_try(self):
        """函数首次成功执行，不应重试"""
        mock_func = Mock(return_value="success")
        decorated = retry_on_exception(max_retries=3)(mock_func)

        result = decorated()

        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 1)

    def test_success_after_retries(self):
        """函数在重试后成功"""
        mock_func = Mock(side_effect=[Exception("error1"), Exception("error2"), "success"])
        decorated = retry_on_exception(max_retries=3, initial_delay=0.01)(mock_func)

        result = decorated()

        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)

    def test_max_retries_exceeded(self):
        """达到最大重试次数后抛出异常"""
        mock_func = Mock(side_effect=Exception("persistent error"))
        decorated = retry_on_exception(max_retries=2, initial_delay=0.01)(mock_func)

        with self.assertRaises(Exception) as context:
            decorated()

        self.assertIn("persistent error", str(context.exception))
        # 首次尝试 + 2次重试 = 3次调用
        self.assertEqual(mock_func.call_count, 3)

    def test_specific_exception_only(self):
        """只重试特定类型的异常"""

        class CustomError(Exception):
            pass

        mock_func = Mock(side_effect=ValueError("wrong error type"))
        decorated = retry_on_exception(
            max_retries=3, exceptions=(CustomError,), initial_delay=0.01
        )(mock_func)

        with self.assertRaises(ValueError):
            decorated()

        # 不应重试，因为异常类型不匹配
        self.assertEqual(mock_func.call_count, 1)

    def test_exponential_backoff(self):
        """测试指数退避延迟"""
        mock_func = Mock(side_effect=[Exception("e1"), Exception("e2"), "success"])

        with patch("time.sleep") as mock_sleep:
            decorated = retry_on_exception(
                max_retries=3, initial_delay=1.0, backoff_factor=2.0
            )(mock_func)

            result = decorated()

            self.assertEqual(result, "success")
            # 应该有2次sleep调用：第一次1秒，第二次2秒
            self.assertEqual(mock_sleep.call_count, 2)
            mock_sleep.assert_any_call(1.0)
            mock_sleep.assert_any_call(2.0)


class TestRetryWithFallback(unittest.TestCase):
    """测试 retry_with_fallback 函数"""

    def test_returns_result_on_success(self):
        """成功时返回函数结果"""
        func = Mock(return_value="result")

        result = retry_with_fallback(
            func, fallback="fallback", max_retries=2, initial_delay=0.01
        )

        self.assertEqual(result, "result")
        self.assertEqual(func.call_count, 1)

    def test_returns_fallback_on_failure(self):
        """失败时返回fallback值"""
        func = Mock(side_effect=Exception("error"))

        result = retry_with_fallback(
            func, fallback="fallback", max_retries=2, initial_delay=0.01
        )

        self.assertEqual(result, "fallback")
        # 首次尝试 + 2次重试 = 3次调用
        self.assertEqual(func.call_count, 3)


if __name__ == "__main__":
    unittest.main()
