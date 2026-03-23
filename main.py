#!/usr/bin/env python3
"""
牛股选股策略主程序

运行此脚本即可执行完整的选股流程并生成报告：
  1. 构建最近10日板块龙虎榜
  2. 从积分最高的5个板块各选出3只个股
  3. 将结果保存到 report/YYYY-MM-DD/ 目录
"""

# 在导入 akshare 之前为 requests.Session 补丁，确保所有 HTTP 请求携带浏览器风格的
# 请求头。akshare 的 request_with_retry 工具函数创建 requests.Session 时未设置
# User-Agent，导致东方财富 API 的编号子域名（如 17.push2.eastmoney.com、
# 29.push2.eastmoney.com）以 RemoteDisconnected 关闭连接。此脚本仅用于股票数据
# 采集，对所有会话统一注入请求头是修复各 akshare 函数问题的最简可靠方案。
import requests as _requests

_orig_session_init = _requests.Session.__init__


def _patched_session_init(self, *args, **kwargs):
    _orig_session_init(self, *args, **kwargs)
    self.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://data.eastmoney.com/",
        }
    )


_requests.Session.__init__ = _patched_session_init

import logging
import sys
from datetime import datetime

from src.sector_ranking import get_sector_dragon_tiger_list
from src.stock_selector import get_selected_stocks
from src.report_generator import save_report, print_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    today = datetime.now()
    logger.info("===== 牛股选股策略开始执行 =====")

    # 第1部分：构建板块龙虎榜
    logger.info("第1部分：构建板块龙虎榜（最近10个交易日）...")
    sector_dragon_tiger = get_sector_dragon_tiger_list(days=10, top_per_day=10)
    if sector_dragon_tiger.empty:
        logger.error("未能获取板块龙虎榜数据，程序退出")
        sys.exit(1)

    logger.info("板块龙虎榜（前10名）:\n%s", sector_dragon_tiger.head(10).to_string())

    # 第2部分：从前5板块各选3只个股
    logger.info("第2部分：从积分最高的5个板块各选取个股...")
    selected_stocks = get_selected_stocks(sector_dragon_tiger, top_sectors=5)
    if selected_stocks.empty:
        logger.warning("未能选出任何个股")

    # 第3部分：生成并保存报告
    logger.info("第3部分：生成报告...")
    paths = save_report(selected_stocks, sector_dragon_tiger, date=today)
    print_report(selected_stocks, sector_dragon_tiger, date=today)

    logger.info("===== 报告已生成 =====")
    for fmt, path in paths.items():
        logger.info("  [%s] %s", fmt.upper(), path)


if __name__ == "__main__":
    main()
