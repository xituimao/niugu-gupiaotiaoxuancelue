# GitHub Actions 配置完成说明

## 已完成的工作

✅ 已创建 GitHub Actions 工作流配置文件
✅ 已配置每天北京时间 14:00 自动运行
✅ 已配置邮件发送功能
✅ 已更新项目文档

## 需要手动完成的步骤

### 重要：设置邮件密码 Secret

为了让 GitHub Actions 能够发送邮件，您需要在 GitHub 仓库中添加一个 Secret：

1. 打开仓库页面：https://github.com/xituimao/niugu-gupiaotiaoxuancelue

2. 点击顶部菜单的 **Settings**（设置）

3. 在左侧菜单找到 **Secrets and variables** → **Actions**

4. 点击 **New repository secret** 按钮

5. 填写以下信息：
   - **Name**（名称）: `EMAIL_PASSWORD`
   - **Secret**（密钥）: `YHnLCubcV4ULHR7X`

6. 点击 **Add secret** 保存

### 测试工作流

设置完 Secret 后，您可以手动触发一次工作流来测试：

1. 进入仓库的 **Actions** 页面

2. 在左侧选择 **每日牛股选股报告** 工作流

3. 点击右侧的 **Run workflow** 按钮

4. 选择分支（通常是 `main` 或当前分支）

5. 点击绿色的 **Run workflow** 按钮确认

6. 等待几分钟，查看运行结果

7. 检查 sx3964117@126.com 邮箱是否收到测试邮件

## 工作流详情

### 运行时间
- **自动运行**: 每天 UTC 时间 06:00（北京时间 14:00）
- **手动运行**: 随时可以在 Actions 页面手动触发

### 邮件配置
- **发件人**: aistockreport@yeah.net
- **收件人**: sx3964117@126.com
- **SMTP 服务器**: smtp.yeah.net (端口 465, SSL)

### 报告内容
- 邮件正文：Markdown 格式的选股报告
- 附件：stocks.csv（选中股票的详细数据）

### 工作流步骤
1. 检出代码
2. 设置 Python 3.10 环境
3. 安装项目依赖
4. 运行选股程序（main.py）
5. 读取生成的报告文件
6. 通过 SMTP 发送邮件
7. 上传报告为 GitHub Actions 工件（保留 30 天）

## 文件清单

已创建和修改的文件：

- `.github/workflows/daily-stock-report.yml` - 工作流配置文件
- `.github/workflows/README.md` - 工作流详细文档
- `README.md` - 更新了 GitHub Actions 使用说明

## 故障排查

如果遇到问题：

1. **邮件未发送**
   - 检查 `EMAIL_PASSWORD` Secret 是否正确设置
   - 查看 Actions 运行日志中的错误信息

2. **程序运行失败**
   - 查看 Actions 日志中的详细错误
   - 检查数据源 API 是否可访问

3. **定时任务未执行**
   - GitHub Actions 可能会延迟 10-15 分钟
   - 公共仓库无免费额度限制
   - 私有仓库每月有 2000 分钟免费额度

## 注意事项

- 工作流运行记录保留 90 天
- 报告工件保留 30 天
- 可以随时在 Actions 页面查看历史运行记录
- 每次运行大约需要 1-2 分钟

## 参考文档

- [GitHub Actions 工作流文档](.github/workflows/README.md)
- [项目主 README](README.md)
