"""
个股选取模块

第2部分：获取个股
1. 从板块龙虎榜积分最高的5个板块依次获取成分股。
2. 将成分股按"5日涨幅"降序排列，保留前15个。
3. 从前15中取涨幅最小的5个，再按最新价升序取最低的3个——每个板块获取3只个股。
"""

import logging

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)

_five_day_gains_cache: pd.DataFrame | None = None


def get_five_day_gains() -> pd.DataFrame:
    """
    获取全市场所有A股的5日涨跌幅数据（带缓存，同次运行只拉取一次）。

    返回 DataFrame，包含 '代码' 和 '5日涨跌幅' 两列。
    """
    global _five_day_gains_cache
    if _five_day_gains_cache is not None:
        return _five_day_gains_cache

    logger.info("正在获取全市场5日涨跌幅数据...")
    try:
        df = ak.stock_individual_fund_flow_rank(indicator="5日")
        df = df[["代码", "名称", "最新价", "5日涨跌幅"]].copy()
        df["5日涨跌幅"] = pd.to_numeric(df["5日涨跌幅"], errors="coerce")
        df["最新价"] = pd.to_numeric(df["最新价"], errors="coerce")
        _five_day_gains_cache = df
        return df
    except Exception as exc:
        logger.warning("获取5日涨跌幅数据失败: %s", exc)
        return pd.DataFrame(columns=["代码", "名称", "最新价", "5日涨跌幅"])


def get_sector_constituent_stocks(sector_name: str) -> pd.DataFrame:
    """
    获取指定行业板块的成分股列表。

    返回包含 '代码'、'名称'、'最新价' 等字段的 DataFrame。
    """
    try:
        df = ak.stock_board_industry_cons_em(symbol=sector_name)
        df["最新价"] = pd.to_numeric(df["最新价"], errors="coerce")
        return df
    except Exception as exc:
        logger.warning("获取板块 %s 成分股失败: %s", sector_name, exc)
        return pd.DataFrame(columns=["代码", "名称", "最新价"])


def select_stocks_for_sector(
    sector_name: str,
    top_list_size: int = 15,
    bottom_pool_size: int = 5,
    final_count: int = 3,
) -> pd.DataFrame:
    """
    按选股规则从单个板块中挑选个股。

    规则：
    1. 获取板块所有成分股，与5日涨幅数据合并。
    2. 按5日涨幅降序排列，保留前 `top_list_size` 个（默认15个）。
    3. 从这15个中取涨幅最小的 `bottom_pool_size` 个（默认5个）。
    4. 对这5个按最新价升序排列，取前 `final_count` 个（默认3个）。

    :param sector_name: 板块名称
    :param top_list_size: 按涨幅保留的最多股票数（默认15）
    :param bottom_pool_size: 从保留列表末尾取的候选股数量（默认5）
    :param final_count: 最终每板块选出的股票数（默认3）
    :return: 选出的个股 DataFrame，包含板块名称列
    """
    logger.info("正在处理板块: %s", sector_name)
    constituent_df = get_sector_constituent_stocks(sector_name)
    if constituent_df.empty:
        logger.warning("板块 %s 无成分股数据，跳过", sector_name)
        return pd.DataFrame()

    five_day_df = get_five_day_gains()

    # 合并5日涨跌幅
    merged = constituent_df.merge(
        five_day_df[["代码", "5日涨跌幅"]],
        on="代码",
        how="left",
    )

    # 去除无5日涨幅数据的股票
    merged = merged.dropna(subset=["5日涨跌幅"])
    if merged.empty:
        logger.warning("板块 %s 的成分股均无5日涨幅数据，跳过", sector_name)
        return pd.DataFrame()

    # 步骤2：按5日涨幅降序，取前15
    merged = merged.sort_values("5日涨跌幅", ascending=False).reset_index(drop=True)
    top_list = merged.head(top_list_size)

    if len(top_list) < bottom_pool_size:
        bottom_pool = top_list
    else:
        # 步骤3：从前15中取涨幅最小的5个
        bottom_pool = top_list.tail(bottom_pool_size)

    # 步骤4：从涨幅最小的5个中，按最新价升序取最低的3个
    bottom_pool = bottom_pool.dropna(subset=["最新价"])
    selected = bottom_pool.sort_values("最新价", ascending=True).head(final_count)

    if selected.empty:
        return pd.DataFrame()

    selected = selected.copy()
    selected.insert(0, "板块", sector_name)
    selected = selected.reset_index(drop=True)
    return selected


def get_selected_stocks(
    sector_dragon_tiger: pd.DataFrame,
    top_sectors: int = 5,
) -> pd.DataFrame:
    """
    从板块龙虎榜中取积分最高的 `top_sectors` 个板块，依次选股并合并返回。

    :param sector_dragon_tiger: sector_ranking.get_sector_dragon_tiger_list() 的返回值
    :param top_sectors: 取前几个板块（默认5个）
    :return: 汇总后的个股清单 DataFrame
    """
    if sector_dragon_tiger.empty:
        logger.warning("板块龙虎榜为空，无法选股")
        return pd.DataFrame()

    top_sector_names = sector_dragon_tiger["板块名称"].head(top_sectors).tolist()
    logger.info("板块龙虎榜前%d名: %s", top_sectors, top_sector_names)

    all_stocks: list[pd.DataFrame] = []
    for sector in top_sector_names:
        selected = select_stocks_for_sector(sector)
        if not selected.empty:
            all_stocks.append(selected)

    if not all_stocks:
        logger.warning("未能从任何板块中选出股票")
        return pd.DataFrame()

    result = pd.concat(all_stocks, ignore_index=True)
    return result
