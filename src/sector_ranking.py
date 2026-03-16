"""
板块龙虎榜模块

第1部分：形成板块龙虎榜
1. 获取最近10个交易日每日行业板块净入资金排名，每日保留前10个板块。
2. 按排名打分：第1名+9分，第2名+8分，……第10名+0分。
3. 汇总每个板块的总积分，形成板块龙虎榜（按综合积分降序排列）。
"""

import logging
from datetime import datetime

import akshare as ak
import pandas as pd

from src.retry_utils import retry_on_exception

logger = logging.getLogger(__name__)


@retry_on_exception(max_retries=3, backoff_factor=2.0, initial_delay=1.0)
def get_all_sector_names() -> list[str]:
    """获取所有行业板块名称列表（带重试机制）。"""
    df = ak.stock_board_industry_name_em()
    return df["板块名称"].tolist()


def get_sector_historical_flows(sector_name: str) -> pd.DataFrame:
    """
    获取指定行业板块的历史每日主力净流入数据（带重试机制）。

    返回 DataFrame，包含 '日期' 和 '主力净流入-净额' 两列。
    """
    @retry_on_exception(max_retries=3, backoff_factor=2.0, initial_delay=1.0)
    def _fetch() -> pd.DataFrame:
        df = ak.stock_sector_fund_flow_hist(symbol=sector_name)
        df["日期"] = pd.to_datetime(df["日期"])
        df["主力净流入-净额"] = pd.to_numeric(df["主力净流入-净额"], errors="coerce")
        return df[["日期", "主力净流入-净额"]].dropna()

    try:
        return _fetch()
    except Exception as exc:
        logger.warning("获取板块 %s 历史资金流数据失败（已重试）: %s", sector_name, exc)
        return pd.DataFrame(columns=["日期", "主力净流入-净额"])


def get_recent_trading_dates(all_dates: list, days: int = 10) -> list:
    """从已知交易日期列表中取最近 `days` 个交易日。"""
    sorted_dates = sorted(set(all_dates), reverse=True)
    return sorted_dates[:days]


def build_daily_rankings(days: int = 10, top_per_day: int = 10) -> list[dict]:
    """
    构建最近 `days` 个交易日的板块净入资金排名列表。

    每个元素为 {'date': date, 'sectors': ['板块1', '板块2', ...]}，
    列表按净入资金从高到低排序，保留前 `top_per_day` 个板块。

    :param days: 取最近多少个交易日
    :param top_per_day: 每日保留排名前几的板块
    :return: 每日排名列表（按日期升序）
    """
    logger.info("开始获取所有行业板块名称...")
    sector_names = get_all_sector_names()
    logger.info("共获取到 %d 个行业板块，开始拉取历史资金流数据...", len(sector_names))

    # 汇总所有板块的历史数据：{date: {sector: net_flow}}
    flow_by_date: dict[datetime, dict[str, float]] = {}

    for idx, name in enumerate(sector_names, 1):
        logger.info("正在获取板块 [%d/%d]: %s", idx, len(sector_names), name)
        df = get_sector_historical_flows(name)
        for _, row in df.iterrows():
            date = row["日期"]
            flow_by_date.setdefault(date, {})[name] = row["主力净流入-净额"]

    if not flow_by_date:
        logger.warning("未获取到任何板块历史资金流数据")
        return []

    recent_dates = get_recent_trading_dates(list(flow_by_date.keys()), days=days)

    daily_rankings: list[dict] = []
    for date in sorted(recent_dates):
        day_flows = flow_by_date.get(date, {})
        sorted_sectors = sorted(day_flows.items(), key=lambda x: x[1], reverse=True)
        top_sectors = [s for s, _ in sorted_sectors[:top_per_day]]
        daily_rankings.append({"date": date, "sectors": top_sectors})
        logger.debug(
            "日期 %s 前%d板块: %s",
            date.strftime("%Y-%m-%d"),
            top_per_day,
            top_sectors,
        )

    return daily_rankings


def score_sectors(daily_rankings: list[dict], top_per_day: int = 10) -> pd.DataFrame:
    """
    按每日排名给板块打分并汇总，生成板块龙虎榜。

    打分规则：当日排名第1名+(top_per_day-1)分，第2名+(top_per_day-2)分，……
    最后一名+0分。默认 top_per_day=10 时，第1名+9分，第10名+0分。
    分数基于固定排名位置，与当日实际上榜数量无关。

    :param daily_rankings: build_daily_rankings() 的返回值
    :param top_per_day: 每日保留的板块数，决定第1名的基础分（默认10）
    :return: 板块龙虎榜 DataFrame
    """
    scores: dict[str, int] = {}

    for day in daily_rankings:
        sectors = day["sectors"]  # 已按净入资金从高到低排列
        for rank_idx, sector in enumerate(sectors):
            # 第1名(rank_idx=0)得 top_per_day-1 分；最后一名得0分；最多取非负值
            score = max(0, top_per_day - 1 - rank_idx)
            scores[sector] = scores.get(sector, 0) + score

    result = pd.DataFrame(
        {"板块名称": list(scores.keys()), "综合积分": list(scores.values())}
    )
    result = result.sort_values("综合积分", ascending=False).reset_index(drop=True)
    result.index = result.index + 1
    result.index.name = "排名"
    return result


def get_sector_dragon_tiger_list(
    days: int = 10,
    top_per_day: int = 10,
) -> pd.DataFrame:
    """
    一键生成板块龙虎榜。

    :param days: 取最近多少个交易日（默认10日）
    :param top_per_day: 每日保留排名前几的板块（默认10个）
    :return: 按综合积分降序排列的板块龙虎榜 DataFrame
    """
    daily_rankings = build_daily_rankings(days=days, top_per_day=top_per_day)
    if not daily_rankings:
        return pd.DataFrame(columns=["板块名称", "综合积分"])
    return score_sectors(daily_rankings, top_per_day=top_per_day)
