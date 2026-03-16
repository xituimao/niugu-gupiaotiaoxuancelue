# GitHub Actions 工作流配置说明

## 每日牛股选股报告 (daily-stock-report.yml)

此工作流会在每天北京时间 14:00 自动运行，执行股票选股分析并通过邮件发送报告。

### 运行时间

- **定时任务**: 每天 UTC 时间 06:00 (北京时间 14:00)
- **手动触发**: 可以在 GitHub Actions 页面手动运行

### 配置步骤

#### 1. 设置邮件密码 Secret

需要在 GitHub 仓库中设置以下 Secret：

1. 进入仓库的 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. 添加以下 Secret：
   - **Name**: `EMAIL_PASSWORD`
   - **Secret**: `YHnLCubcV4ULHR7X` (邮箱授权密码)

#### 2. 邮件配置信息

- **发件人**: aistockreport@yeah.net
- **收件人**: sx3964117@126.com
- **SMTP服务器**: smtp.yeah.net
- **端口**: 465 (SSL)
- **授权密码**: 通过 GitHub Secret `EMAIL_PASSWORD` 配置

### 工作流步骤

1. **检出代码**: 从仓库获取最新代码
2. **设置 Python 环境**: 安装 Python 3.10
3. **安装依赖**: 安装 requirements.txt 中的依赖包
4. **运行选股程序**: 执行 `main.py` 生成选股报告
5. **获取报告文件**: 读取生成的报告内容
6. **发送邮件报告**: 通过 SMTP 发送邮件，包含报告内容和 CSV 附件
7. **上传报告为工件**: 将报告保存为 GitHub Actions 工件，保留 30 天

### 报告内容

- **Markdown 报告**: 包含板块排名和选股结果的详细报告
- **CSV 附件**: 选中股票的详细数据表格

### 手动运行

如需手动运行工作流：

1. 进入仓库的 **Actions** 页面
2. 选择 **每日牛股选股报告** 工作流
3. 点击 **Run workflow** 按钮
4. 选择分支并确认运行

### 故障排查

- **邮件发送失败**: 检查 GitHub Secret `EMAIL_PASSWORD` 是否正确配置
- **报告生成失败**: 查看 Actions 运行日志，检查数据源是否可访问
- **定时任务未运行**: GitHub Actions 在高负载时可能会延迟，通常在预定时间的 10-15 分钟内会执行

### 注意事项

- GitHub Actions 的免费额度为每月 2000 分钟（公共仓库无限制）
- 工作流运行记录会保留 90 天
- 报告工件会保留 30 天
- 邮件中的时间戳使用 GitHub Actions 运行时间
