"""
网络请求重试工具模块

提供装饰器和函数用于处理网络请求的重试逻辑，包括指数退避策略。
"""

import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_on_exception(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: tuple = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    装饰器：在函数抛出异常时自动重试，使用指数退避策略。

    :param max_retries: 最大重试次数（不包括首次尝试）
    :param backoff_factor: 退避因子，每次重试延迟时间乘以此因子
    :param initial_delay: 首次重试前的延迟时间（秒）
    :param exceptions: 需要重试的异常类型元组
    :return: 装饰后的函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None

            # 首次尝试 + max_retries 次重试
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc

                    if attempt < max_retries:
                        logger.warning(
                            "函数 %s 执行失败 (尝试 %d/%d): %s，将在 %.1f 秒后重试...",
                            getattr(func, "__name__", "unknown"),
                            attempt + 1,
                            max_retries + 1,
                            exc,
                            delay,
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            "函数 %s 执行失败，已达最大重试次数 %d: %s",
                            getattr(func, "__name__", "unknown"),
                            max_retries + 1,
                            exc,
                        )

            # 所有重试都失败，抛出最后一次异常
            if last_exception:
                raise last_exception

            # 理论上不会到达这里，但为了类型检查
            raise RuntimeError(
                f"函数 {getattr(func, '__name__', 'unknown')} 未能成功执行且未捕获异常"
            )

        return wrapper

    return decorator


def retry_with_fallback(
    func: Callable[..., T],
    fallback: T,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    执行函数并在失败时重试，如果所有重试都失败则返回fallback值。

    :param func: 要执行的函数
    :param fallback: 失败时返回的默认值
    :param max_retries: 最大重试次数
    :param backoff_factor: 退避因子
    :param initial_delay: 首次重试延迟
    :param exceptions: 需要重试的异常类型
    :param args: 传递给func的位置参数
    :param kwargs: 传递给func的关键字参数
    :return: 函数执行结果或fallback值
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as exc:
            last_exception = exc

            if attempt < max_retries:
                logger.warning(
                    "函数 %s 执行失败 (尝试 %d/%d): %s，将在 %.1f 秒后重试...",
                    getattr(func, "__name__", "unknown"),
                    attempt + 1,
                    max_retries + 1,
                    exc,
                    delay,
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(
                    "函数 %s 执行失败，已达最大重试次数 %d: %s，返回fallback值",
                    getattr(func, "__name__", "unknown"),
                    max_retries + 1,
                    exc,
                )

    return fallback
