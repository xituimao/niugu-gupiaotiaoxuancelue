"""
pytest 配置：每个测试前后清除 LRU 缓存，避免测试间状态污染。
"""

import pytest


@pytest.fixture(autouse=True)
def clear_lru_caches():
    """每个测试用例前后清除 stock_selector 模块的 LRU 缓存。"""
    import src.stock_selector as ss

    ss._fetch_five_day_gains.cache_clear()
    yield
    ss._fetch_five_day_gains.cache_clear()
