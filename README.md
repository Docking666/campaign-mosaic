# CampaignMosaic 🎯

> 多平台活动数据自动整合与日报生成器 — 终结手工搬数据的噩梦

[![Daily Report](https://github.com/YOUR_USERNAME/campaign-mosaic/actions/workflows/daily_report.yml/badge.svg)](https://github.com/YOUR_USERNAME/campaign-mosaic/actions/workflows/daily_report.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 功能亮点

- 📡 **多源数据拉取** — 对接有赞、友盟、百度统计、巨量引擎等主流运营平台 API
- 🧹 **智能数据清洗** — 自动对齐时区、补齐缺失日期、统一指标口径
- 📊 **可视化报告** — 基于 Chart.js 生成精美 HTML 日报，移动端适配
- 📬 **多渠道推送** — 支持邮件、飞书、钉钉、企业微信机器人通知
- ⏰ **定时自动执行** — GitHub Actions 免费托管，每天自动生成并推送报告
- ⚙️ **配置驱动** — 只需编辑 YAML 配置文件，无需编写代码
- 🔌 **插件化架构** — 新增数据源只需添加一个适配器类

## 🚀 快速开始

### 方式一：Fork 后一键部署（推荐）

1. **Fork 本仓库** → https://github.com/Docking666/campaign-mosaic/fork

2. **启用 GitHub Pages**
   - 进入仓库 Settings → Pages
   - Source 选择 "GitHub Actions"

3. **配置 Secrets**
   - 进入 Settings → Secrets and variables → Actions
   - 添加以下 Secrets（至少配置一个数据源）：

   | Secret 名称 | 说明 | 必需 |
   |---|---|---|
   | `YOUZAN_API_KEY` | 有赞开放平台 API Key | 可选 |
   | `UMENG_APP_KEY` | 友盟 App Key | 可选 |
   | `JULIANG_ACCOUNT_ID` | 巨量引擎广告账户 ID | 可选 |
   | `FEISHU_BOT_WEBHOOK` | 飞书机器人 Webhook 地址 | 可选 |
   | `SMTP_PASSWORD` | 邮箱 SMTP 授权密码 | 可选 |

4. **手动触发首次运行**
   - 进入 Actions 页面
   - 选择 "CampaignMosaic Daily Report" 工作流
   - 点击 "Run workflow"

5. **查看报告**
   - 等待工作流执行完成
   - 访问 `https://Docking666.github.io/campaign-mosaic` 查看在线报告
   - （将 `Docking666` 替换为你的 GitHub 用户名）

### 方式二：本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/campaign-mosaic.git
cd campaign-mosaic

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置
cp config.example.yaml config.yaml
cp .env.example .env
# 编辑 config.yaml 和 .env，填入你的配置

# 5. 运行（使用示例数据演示）
python -m campaign_mosaic.main --demo

# 6. 运行（使用自定义配置）
python -m campaign_mosaic.main --config config.yaml
```

## 📁 项目结构

```
campaign-mosaic/
├── .github/workflows/
│   └── daily_report.yml          # GitHub Actions 定时任务
├── campaign_mosaic/
│   ├── __init__.py
│   ├── main.py                   # 主入口
│   ├── adapters/                 # 数据源适配器（插件）
│   │   ├── base.py               # 适配器基类
│   │   ├── youzan.py             # 有赞交易数据
│   │   ├── umeng.py              # 友盟用户行为
│   │   ├── baidu_tongji.py       # 百度统计流量
│   │   ├── juliang.py            # 巨量引擎广告
│   │   └── csv_import.py         # CSV/HTTP 通用导入
│   ├── templates/
│   │   └── minimal.html          # HTML报告模板
│   └── utils/
│       ├── config_loader.py      # 配置加载器
│       ├── data_processor.py     # 数据清洗与指标计算
│       ├── report_generator.py   # 报告生成引擎
│       └── notifier.py           # 通知推送模块
├── sample_data/                  # 示例数据
├── config.example.yaml           # 配置示例
├── .env.example                  # 环境变量示例
├── requirements.txt              # Python 依赖
└── README.md
```

## ⚙️ 配置说明

编辑 `config.yaml` 来定义你的活动：

```yaml
campaign:
  name: "618年中大促"
  start_date: "2026-05-20"
  end_date: "2026-06-18"

data_sources:
  youzan:
    enabled: true
    api_key: ${YOUZAN_API_KEY}     # 从环境变量读取
  umeng:
    enabled: true
    app_key: ${UMENG_APP_KEY}
  juliang:
    enabled: true
    account_id: ${JULIANG_ACCOUNT_ID}

metrics:
  - name: "日活用户(DAU)"
    source: "umeng.dau"
  - name: "交易金额"
    source: "youzan.revenue"
  - name: "ROI"
    formula: "youzan.revenue / juliang.cost"   # 支持公式计算

notifications:
  email:
    enabled: true
    smtp_server: "smtp.feishu.com"
    receivers: ["boss@example.com"]
  feishu_bot:
    enabled: true
    webhook_url: ${FEISHU_BOT_WEBHOOK}
```

### 环境变量

在 `.env` 文件或 GitHub Secrets 中配置：

```bash
YOUZAN_API_KEY=your_youzan_api_key
UMENG_APP_KEY=your_umeng_app_key
JULIANG_ACCOUNT_ID=your_juliang_account_id
FEISHU_BOT_WEBHOOK=https://open.feishu.cn/...
SMTP_PASSWORD=your_smtp_password
```

## 🔌 扩展新数据源

只需 3 步即可添加新的数据源插件：

1. 在 `campaign_mosaic/adapters/` 下创建新文件，继承 `BaseAdapter`：

```python
from .base import BaseAdapter
import pandas as pd
from datetime import date

class MyPlatformAdapter(BaseAdapter):
    ADAPTER_NAME = "my_platform"

    def fetch_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        # 调用你的平台 API
        return pd.DataFrame({
            "date": [...],
            "my_platform.metric1": [...],
        })
```

2. 在 `main.py` 的 `ADAPTER_REGISTRY` 中注册：

```python
ADAPTER_REGISTRY = {
    ...
    "my_platform": "campaign_mosaic.adapters.my_platform.MyPlatformAdapter",
}
```

3. 在 `config.yaml` 中启用：

```yaml
data_sources:
  my_platform:
    enabled: true
    api_key: ${MY_PLATFORM_KEY}
```

## 📋 报告预览

运行后会生成精美的 HTML 报告，包含：

- 📊 **概览卡片** — 昨日核心指标 + 环比变化
- 📈 **趋势折线图** — 活动期内每日指标走势
- 📊 **汇总柱状图** — 各指标累计值对比
- 🍩 **占比饼图** — 指标均值分布
- 📋 **明细表格** — 按日拆分的完整数据

### 🌐 GitHub Pages 在线访问

部署后，报告会自动发布到 GitHub Pages：

```
https://<你的GitHub用户名>.github.io/campaign-mosaic
```

**特性：**
- ✅ 完全免费，无需额外服务器
- ✅ 自动 HTTPS 加密
- ✅ 支持自定义域名（可选）
- ✅ 每天自动更新最新报告

## 🛡️ 安全说明

- 所有 API 密钥通过环境变量或 GitHub Secrets 加载
- 仓库内不包含任何真实凭证
- 各插件使用官方开放 API，遵守调用频率限制
- `.env` 文件已加入 `.gitignore`

## 📄 License

[MIT](LICENSE)

---

**Made with ❤️ by CampaignMosaic Team**
