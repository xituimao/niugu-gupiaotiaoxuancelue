"""
报告生成模块

第3部分：返回个股清单
将前两步获取到的个股按板块合并到一个表格中，并写到本地文档。
文件统一放在项目目录的 report/YYYY-MM-DD/ 目录下。
"""

import logging
import os
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

REPORT_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "report")


def get_report_dir(date: datetime | None = None) -> str:
    """返回当日报告目录路径（不存在则创建）。"""
    if date is None:
        date = datetime.now()
    date_str = date.strftime("%Y-%m-%d")
    report_dir = os.path.join(REPORT_BASE_DIR, date_str)
    os.makedirs(report_dir, exist_ok=True)
    return report_dir


def _format_markdown(
    selected_stocks: pd.DataFrame,
    sector_dragon_tiger: pd.DataFrame,
    date: datetime,
) -> str:
    """将选股结果格式化为 Markdown 文本。"""
    lines: list[str] = []
    lines.append(f"# 牛股选股报告 {date.strftime('%Y-%m-%d')}")
    lines.append("")

    # 板块龙虎榜汇总
    lines.append("## 一、板块龙虎榜（前10名）")
    lines.append("")
    if not sector_dragon_tiger.empty:
        top10 = sector_dragon_tiger.head(10)
        lines.append("| 排名 | 板块名称 | 综合积分 |")
        lines.append("|------|----------|----------|")
        for rank, row in top10.iterrows():
            lines.append(f"| {rank} | {row['板块名称']} | {row['综合积分']} |")
    else:
        lines.append("*暂无数据*")
    lines.append("")

    # 个股清单
    lines.append("## 二、个股清单")
    lines.append("")
    if selected_stocks.empty:
        lines.append("*暂无数据*")
    else:
        for sector, group in selected_stocks.groupby("板块", sort=False):
            lines.append(f"### {sector}")
            lines.append("")
            lines.append("| 代码 | 名称 | 最新价 | 5日涨跌幅(%) |")
            lines.append("|------|------|--------|-------------|")
            for _, row in group.iterrows():
                code = row.get("代码", "-")
                name = row.get("名称", "-")
                price = row.get("最新价", "-")
                gain = row.get("5日涨跌幅", "-")
                if isinstance(price, float):
                    price = f"{price:.2f}"
                if isinstance(gain, float):
                    gain = f"{gain:.2f}"
                lines.append(f"| {code} | {name} | {price} | {gain} |")
            lines.append("")

    lines.append("---")
    lines.append(f"*生成时间：{date.strftime('%Y-%m-%d %H:%M:%S')}*")
    return "\n".join(lines)


def _format_csv(selected_stocks: pd.DataFrame) -> str:
    """将选股结果转换为 CSV 文本。"""
    if selected_stocks.empty:
        return ""
    cols = [c for c in ["板块", "代码", "名称", "最新价", "5日涨跌幅"] if c in selected_stocks.columns]
    return selected_stocks[cols].to_csv(index=False)


def save_report(
    selected_stocks: pd.DataFrame,
    sector_dragon_tiger: pd.DataFrame,
    date: datetime | None = None,
) -> dict[str, str]:
    """
    将选股结果保存为 Markdown 和 CSV 文件。

    :param selected_stocks: stock_selector.get_selected_stocks() 的返回值
    :param sector_dragon_tiger: sector_ranking.get_sector_dragon_tiger_list() 的返回值
    :param date: 报告日期（默认今日）
    :return: 包含各文件路径的字典 {'md': '...', 'csv': '...'}
    """
    if date is None:
        date = datetime.now()

    report_dir = get_report_dir(date)
    paths: dict[str, str] = {}

    # Markdown 报告
    md_path = os.path.join(report_dir, "report.md")
    md_content = _format_markdown(selected_stocks, sector_dragon_tiger, date)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    paths["md"] = md_path
    logger.info("Markdown报告已保存: %s", md_path)

    # CSV 个股清单
    if not selected_stocks.empty:
        csv_path = os.path.join(report_dir, "stocks.csv")
        csv_content = _format_csv(selected_stocks)
        with open(csv_path, "w", encoding="utf-8-sig") as f:
            f.write(csv_content)
        paths["csv"] = csv_path
        logger.info("CSV个股清单已保存: %s", csv_path)

    return paths


def print_report(
    selected_stocks: pd.DataFrame,
    sector_dragon_tiger: pd.DataFrame,
    date: datetime | None = None,
) -> None:
    """将报告内容输出到控制台。"""
    if date is None:
        date = datetime.now()
    print(_format_markdown(selected_stocks, sector_dragon_tiger, date))
