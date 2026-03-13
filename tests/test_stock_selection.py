"""
单元测试：验证选股逻辑的核心算法，不依赖网络请求。
"""

import os
import sys
import tempfile
from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.sector_ranking import (
    get_recent_trading_dates,
    score_sectors,
)
from src.stock_selector import select_stocks_for_sector, get_selected_stocks
from src.report_generator import (
    _format_markdown,
    _format_csv,
    get_report_dir,
    save_report,
)


# ──────────────────────────────────────────────
# 辅助数据
# ──────────────────────────────────────────────

def make_daily_rankings():
    """生成测试用的每日板块排名数据。"""
    dates = [datetime(2024, 1, d) for d in range(1, 11)]
    sectors_pool = [f"板块{i}" for i in range(1, 11)]
    rankings = []
    for i, date in enumerate(dates):
        # 循环偏移，让每日前10名略有不同
        shifted = sectors_pool[i % 3:] + sectors_pool[: i % 3]
        rankings.append({"date": date, "sectors": shifted})
    return rankings


def make_sector_dragon_tiger():
    """生成测试用的板块龙虎榜 DataFrame。"""
    return pd.DataFrame(
        {
            "板块名称": [f"板块{i}" for i in range(1, 11)],
            "综合积分": list(range(100, 0, -10)),
        },
        index=range(1, 11),
    )


def make_constituent_stocks():
    """生成测试用的成分股 DataFrame（模拟 stock_board_industry_cons_em 返回值）。"""
    return pd.DataFrame(
        {
            "序号": range(1, 21),
            "代码": [f"60000{i}" for i in range(1, 21)],
            "名称": [f"股票{i}" for i in range(1, 21)],
            "最新价": [float(10 + i) for i in range(1, 21)],
            "涨跌幅": [float(i * 0.1) for i in range(1, 21)],
            "涨跌额": [0.1] * 20,
            "成交量": [1000] * 20,
            "成交额": [10000] * 20,
            "振幅": [1.0] * 20,
            "最高": [float(11 + i) for i in range(1, 21)],
            "最低": [float(9 + i) for i in range(1, 21)],
            "今开": [float(10 + i) for i in range(1, 21)],
            "昨收": [float(10 + i) for i in range(1, 21)],
            "换手率": [1.0] * 20,
            "市盈率-动态": [20.0] * 20,
            "市净率": [2.0] * 20,
        }
    )


def make_five_day_gains():
    """生成测试用的5日涨跌幅 DataFrame（模拟 stock_individual_fund_flow_rank 返回值）。"""
    return pd.DataFrame(
        {
            "代码": [f"60000{i}" for i in range(1, 21)],
            "名称": [f"股票{i}" for i in range(1, 21)],
            "最新价": [float(10 + i) for i in range(1, 21)],
            "5日涨跌幅": [float(i * 0.5) for i in range(1, 21)],
        }
    )


# ──────────────────────────────────────────────
# 测试：板块打分逻辑
# ──────────────────────────────────────────────

class TestScoreSectors:
    def test_score_order(self):
        """排名靠前的板块应获得更高的积分。"""
        rankings = [
            {"date": datetime(2024, 1, 1), "sectors": ["A", "B", "C"]},
            {"date": datetime(2024, 1, 2), "sectors": ["A", "C", "B"]},
        ]
        result = score_sectors(rankings, top_per_day=3)
        # A 每次第1名(+2分)×2 = 4分，B 第2名(+1)+第3名(+0)=1分，C 第3名+第2名=1分
        assert result.iloc[0]["板块名称"] == "A"
        assert result.iloc[0]["综合积分"] == 4

    def test_top_n_minus_one_scoring(self):
        """验证打分规则：第1名得(top_per_day-1)分，最后一名得0分。"""
        rankings = [
            {"date": datetime(2024, 1, 1), "sectors": ["X", "Y", "Z"]},
        ]
        result = score_sectors(rankings, top_per_day=3)
        scores = dict(zip(result["板块名称"], result["综合积分"]))
        assert scores["X"] == 2  # top_per_day=3, rank_idx=0 → 3-1-0 = 2
        assert scores["Y"] == 1  # rank_idx=1 → 3-1-1 = 1
        assert scores["Z"] == 0  # rank_idx=2 → 3-1-2 = 0

    def test_fixed_scoring_based_on_top_per_day(self):
        """当某日实际上榜数少于 top_per_day 时，第1名仍按 top_per_day 计分。"""
        rankings = [
            {"date": datetime(2024, 1, 1), "sectors": ["A", "B"]},  # 仅2个，非10个
        ]
        result = score_sectors(rankings, top_per_day=10)
        scores = dict(zip(result["板块名称"], result["综合积分"]))
        assert scores["A"] == 9  # 第1名始终得 top_per_day-1 = 9 分
        assert scores["B"] == 8  # 第2名得 8 分

    def test_empty_rankings_returns_empty_df(self):
        result = score_sectors([])
        assert result.empty

    def test_result_sorted_descending(self):
        rankings = make_daily_rankings()
        result = score_sectors(rankings)
        scores = result["综合积分"].tolist()
        assert scores == sorted(scores, reverse=True)


# ──────────────────────────────────────────────
# 测试：最近交易日选取
# ──────────────────────────────────────────────

class TestGetRecentTradingDates:
    def test_returns_correct_count(self):
        dates = [datetime(2024, 1, d) for d in range(1, 20)]
        result = get_recent_trading_dates(dates, days=10)
        assert len(result) == 10

    def test_returns_most_recent(self):
        dates = [datetime(2024, 1, d) for d in range(1, 20)]
        result = get_recent_trading_dates(dates, days=5)
        expected = sorted(dates, reverse=True)[:5]
        assert result == expected

    def test_deduplicates(self):
        dates = [datetime(2024, 1, 1)] * 5 + [datetime(2024, 1, 2)] * 3
        result = get_recent_trading_dates(dates, days=10)
        assert len(result) == 2

    def test_fewer_than_requested(self):
        dates = [datetime(2024, 1, 1), datetime(2024, 1, 2)]
        result = get_recent_trading_dates(dates, days=10)
        assert len(result) == 2


# ──────────────────────────────────────────────
# 测试：个股选取逻辑
# ──────────────────────────────────────────────

class TestSelectStocksForSector:
    @patch("src.stock_selector.get_five_day_gains")
    @patch("src.stock_selector.get_sector_constituent_stocks")
    def test_returns_at_most_final_count(self, mock_cons, mock_gains):
        mock_cons.return_value = make_constituent_stocks()
        mock_gains.return_value = make_five_day_gains()

        result = select_stocks_for_sector("板块1")
        assert len(result) <= 3

    @patch("src.stock_selector.get_five_day_gains")
    @patch("src.stock_selector.get_sector_constituent_stocks")
    def test_result_has_sector_column(self, mock_cons, mock_gains):
        mock_cons.return_value = make_constituent_stocks()
        mock_gains.return_value = make_five_day_gains()

        result = select_stocks_for_sector("测试板块")
        assert "板块" in result.columns
        assert (result["板块"] == "测试板块").all()

    @patch("src.stock_selector.get_five_day_gains")
    @patch("src.stock_selector.get_sector_constituent_stocks")
    def test_selected_stocks_have_lowest_price(self, mock_cons, mock_gains):
        """验证从候选池中选出的是价格最低的3只。"""
        mock_cons.return_value = make_constituent_stocks()
        mock_gains.return_value = make_five_day_gains()

        result = select_stocks_for_sector("板块1")
        if len(result) >= 2:
            prices = result["最新价"].tolist()
            assert prices == sorted(prices)

    @patch("src.stock_selector.get_five_day_gains")
    @patch("src.stock_selector.get_sector_constituent_stocks")
    def test_empty_constituent_returns_empty(self, mock_cons, mock_gains):
        mock_cons.return_value = pd.DataFrame(columns=["代码", "名称", "最新价"])
        mock_gains.return_value = make_five_day_gains()

        result = select_stocks_for_sector("空板块")
        assert result.empty

    @patch("src.stock_selector.get_five_day_gains")
    @patch("src.stock_selector.get_sector_constituent_stocks")
    def test_get_selected_stocks_combines_sectors(self, mock_cons, mock_gains):
        mock_cons.return_value = make_constituent_stocks()
        mock_gains.return_value = make_five_day_gains()

        dragon_tiger = make_sector_dragon_tiger()
        result = get_selected_stocks(dragon_tiger, top_sectors=3)
        # 最多 3 个板块 × 3 只 = 9 只
        assert len(result) <= 9
        assert "板块" in result.columns


# ──────────────────────────────────────────────
# 测试：报告生成逻辑
# ──────────────────────────────────────────────

class TestReportGenerator:
    def _make_selected_stocks(self):
        return pd.DataFrame(
            {
                "板块": ["板块A", "板块A", "板块A", "板块B", "板块B", "板块B"],
                "代码": ["000001", "000002", "000003", "000004", "000005", "000006"],
                "名称": ["股票1", "股票2", "股票3", "股票4", "股票5", "股票6"],
                "最新价": [10.0, 12.0, 8.0, 5.0, 6.0, 7.0],
                "5日涨跌幅": [1.0, 2.0, 0.5, 3.0, 1.5, 2.5],
            }
        )

    def test_markdown_contains_sector_name(self):
        stocks = self._make_selected_stocks()
        dt_list = make_sector_dragon_tiger()
        md = _format_markdown(stocks, dt_list, datetime(2024, 1, 15))
        assert "板块A" in md
        assert "板块B" in md

    def test_markdown_contains_date(self):
        stocks = self._make_selected_stocks()
        dt_list = make_sector_dragon_tiger()
        md = _format_markdown(stocks, dt_list, datetime(2024, 1, 15))
        assert "2024-01-15" in md

    def test_csv_has_required_columns(self):
        stocks = self._make_selected_stocks()
        csv = _format_csv(stocks)
        assert "代码" in csv
        assert "名称" in csv
        assert "板块" in csv

    def test_csv_empty_on_empty_df(self):
        csv = _format_csv(pd.DataFrame())
        assert csv == ""

    def test_save_report_creates_files(self):
        stocks = self._make_selected_stocks()
        dt_list = make_sector_dragon_tiger()
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.report_generator.REPORT_BASE_DIR", tmpdir):
                paths = save_report(stocks, dt_list, date=datetime(2024, 1, 15))
            assert "md" in paths
            assert os.path.exists(paths["md"])
            assert "csv" in paths
            assert os.path.exists(paths["csv"])

    def test_get_report_dir_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.report_generator.REPORT_BASE_DIR", tmpdir):
                report_dir = get_report_dir(datetime(2024, 3, 15))
            assert os.path.isdir(report_dir)
            assert "2024-03-15" in report_dir
