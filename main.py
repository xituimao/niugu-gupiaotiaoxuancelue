#!/usr/bin/env python3
"""
牛股选股策略主程序

运行此脚本即可执行完整的选股流程并生成报告：
  1. 构建最近10日板块龙虎榜
  2. 从积分最高的5个板块各选出3只个股
  3. 将结果保存到 report/YYYY-MM-DD/ 目录
"""

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
