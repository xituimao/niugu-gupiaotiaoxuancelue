# 系统架构说明

## 架构概览

本项目采用三层管道（Pipeline）架构，每层独立、职责单一：

```
数据获取层（akshare API）
        ↓
业务逻辑层（sector_ranking / stock_selector）
        ↓
输出层（report_generator）
```

## 模块说明

### `src/sector_ranking.py` — 板块龙虎榜

| 函数 | 职责 |
|------|------|
| `get_all_sector_names()` | 从东方财富获取所有行业板块名称 |
| `get_sector_historical_flows(name)` | 获取单个板块的历史每日主力净流入数据 |
| `build_daily_rankings(days, top_per_day)` | 聚合所有板块历史数据，构建每日排名列表 |
| `score_sectors(daily_rankings, top_per_day)` | 按固定排名位置打分，生成综合积分排名 |
| `get_sector_dragon_tiger_list(days, top_per_day)` | 公开入口：一键返回板块龙虎榜 |

**打分规则**：每日排名第1名得 `top_per_day - 1` 分（默认9分），第2名得8分，……最后一名得0分，各日积分累加得综合积分。分数基于固定排名位置，与当日实际上榜数量无关。

### `src/stock_selector.py` — 个股选取

| 函数 | 职责 |
|------|------|
| `_fetch_five_day_gains()` | 从东方财富获取全市场5日涨跌幅（带 LRU 缓存） |
| `get_five_day_gains()` | 公开入口，带异常处理 |
| `get_sector_constituent_stocks(name)` | 获取板块成分股 |
| `select_stocks_for_sector(name, ...)` | 从单个板块按规则筛选个股 |
| `get_selected_stocks(dragon_tiger, top_sectors)` | 从前N个板块各选股并合并 |

**选股规则**（每个板块）：
1. 获取所有成分股并关联5日涨跌幅
2. 按5日涨幅降序取前15名
3. 从前15名中取涨幅最小的5名
4. 从5名候选中按价格升序取最低3名

### `src/report_generator.py` — 报告生成

| 函数 | 职责 |
|------|------|
| `get_report_dir(date)` | 返回（并创建）当日报告目录 |
| `_format_markdown(stocks, dragon_tiger, date)` | 将结果格式化为 Markdown 字符串（纯函数） |
| `_format_csv(stocks)` | 将个股清单序列化为 CSV 字符串（纯函数） |
| `save_report(stocks, dragon_tiger, date)` | 将报告保存为文件 |
| `print_report(stocks, dragon_tiger, date)` | 将报告打印到控制台 |

## 数据流

```
akshare APIs
    │
    ├── stock_board_industry_name_em()        → 板块名称列表
    ├── stock_sector_fund_flow_hist(name)     → 板块历史资金流
    ├── stock_board_industry_cons_em(name)    → 板块成分股
    └── stock_individual_fund_flow_rank("5日") → 全市场5日涨跌幅
             │
             ▼
    build_daily_rankings()
             │
             ▼
    score_sectors()  →  板块龙虎榜
             │
             ▼
    get_selected_stocks()  →  个股清单
             │
             ▼
    save_report()  →  report/YYYY-MM-DD/{report.md, stocks.csv}
```

## 缓存策略

- **5日涨跌幅数据**（`_fetch_five_day_gains`）：使用 `functools.lru_cache(maxsize=1)` 进程级缓存，同次运行只拉取一次，可通过 `_fetch_five_day_gains.cache_clear()` 重置。
- **板块历史数据**：无缓存，每次运行重新拉取。

## 错误处理

所有网络请求均有 `try/except` 保护：
- 板块历史资金流获取失败 → 返回空 DataFrame，记录 WARNING 日志，跳过该板块
- 成分股获取失败 → 返回空 DataFrame，跳过该板块
- 5日涨跌幅获取失败 → 返回空 DataFrame，后续板块合并步骤自动跳过

## 扩展点

- **数据源**：替换 `src/sector_ranking.py` 和 `src/stock_selector.py` 中的 akshare 调用即可接入其他数据源
- **打分规则**：修改 `score_sectors()` 中的打分逻辑（`top_per_day` 参数可调）
- **选股规则**：`select_stocks_for_sector()` 的参数均可配置（`top_list_size`、`bottom_pool_size`、`final_count`）
- **输出格式**：在 `report_generator.py` 中新增输出格式（如 Excel、HTML）
