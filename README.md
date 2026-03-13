# niugu-gupiaotiaoxuancelue

这是一个专门设计的牛股选股项目，基于东方财富数据，通过资金流向分析构建板块龙虎榜，并从中筛选潜力个股。

## 选股思路

### 第1部分：形成板块龙虎榜
1. 每次执行获取最近10个交易日每日行业板块净入资金排名，每日保留前10个板块。
2. 按排名打分：第1名+9分，第2名+8分……第10名+0分。
3. 汇总所有日期的积分，形成按综合积分排名的板块龙虎榜。

### 第2部分：获取个股
1. 从板块龙虎榜积分最高的5个板块依次获取成分股。
2. 将成分股按5日涨幅降序排列，保留前15个。
3. 从前15中取涨幅最小的5只，再按最新价升序取价格最低的3只——每个板块获取3只个股。

### 第3部分：返回个股清单
将选出的个股按板块汇总，保存到 `report/YYYY-MM-DD/` 目录下的 Markdown 和 CSV 文件。

## 安装

### 环境要求
- Python 3.10+

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/xituimao/niugu-gupiaotiaoxuancelue.git
cd niugu-gupiaotiaoxuancelue

# 安装依赖
pip install -r requirements.txt
```

## 使用

```bash
python main.py
```

执行后，报告文件保存在 `report/YYYY-MM-DD/` 目录（`YYYY-MM-DD` 为运行日期）：
- `report.md`：含板块龙虎榜和个股清单的 Markdown 报告
- `stocks.csv`：个股清单 CSV 文件（UTF-8 with BOM，兼容 Excel 直接打开）

## 项目结构

```
niugu-gupiaotiaoxuancelue/
├── main.py                    # 主程序入口
├── requirements.txt           # 依赖包
├── docs/
│   └── architecture.md        # 系统架构说明
├── src/
│   ├── sector_ranking.py      # 第1部分：板块龙虎榜
│   ├── stock_selector.py      # 第2部分：个股选取
│   └── report_generator.py   # 第3部分：报告生成
├── tests/
│   ├── conftest.py            # pytest 配置（缓存清理 fixture）
│   └── test_stock_selection.py  # 单元测试
└── report/                    # 输出报告目录（自动创建，不入库）
```

## 测试

```bash
pip install pytest
python -m pytest tests/ -v
```

## GitHub Actions 自动化

本项目配置了 GitHub Actions 工作流，可以每天自动运行选股程序并通过邮件发送报告。

### 功能特性

- **定时运行**：每天北京时间 14:00 自动执行
- **邮件通知**：自动将报告发送到指定邮箱
- **报告存档**：在 GitHub Actions 中保留 30 天的报告工件
- **手动触发**：支持在 GitHub Actions 页面手动运行

### 配置步骤

1. **设置邮件密码 Secret**
   - 进入仓库的 **Settings** → **Secrets and variables** → **Actions**
   - 点击 **New repository secret**
   - 添加 Secret：
     - Name: `EMAIL_PASSWORD`
     - Secret: 邮箱授权密码

2. **查看工作流**
   - 工作流配置文件：`.github/workflows/daily-stock-report.yml`
   - 详细文档：`.github/workflows/README.md`

3. **手动运行**
   - 进入仓库的 **Actions** 页面
   - 选择 **每日牛股选股报告** 工作流
   - 点击 **Run workflow** 按钮

更多配置详情请参考 [GitHub Actions 工作流文档](.github/workflows/README.md)。

## 数据来源

数据通过 [akshare](https://akshare.akfamily.xyz/) 从东方财富网获取：
- 行业板块历史资金流：`stock_sector_fund_flow_hist`
- 板块成分股：`stock_board_industry_cons_em`
- 个股5日涨跌幅：`stock_individual_fund_flow_rank`
