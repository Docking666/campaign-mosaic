"""
CampaignMosaic 主入口
负责编排整个数据拉取、清洗、报告生成和通知推送流程
"""

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# 将项目根目录添加到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from campaign_mosaic.utils.config_loader import ConfigLoader
from campaign_mosaic.utils.data_processor import DataProcessor
from campaign_mosaic.utils.report_generator import ReportGenerator
from campaign_mosaic.utils.notifier import NotificationManager

# 适配器注册表
ADAPTER_REGISTRY = {
    "youzan": "campaign_mosaic.adapters.youzan.YouzanAdapter",
    "umeng": "campaign_mosaic.adapters.umeng.UmengAdapter",
    "baidu_tongji": "campaign_mosaic.adapters.baidu_tongji.BaiduTongjiAdapter",
    "juliang": "campaign_mosaic.adapters.juliang.JuliangAdapter",
    "csv_import": "campaign_mosaic.adapters.csv_import.CsvImportAdapter",
}


def import_adapter_class(class_path: str):
    """动态导入适配器类"""
    module_path, class_name = class_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def run(config_path: str = "config.yaml"):
    """
    执行CampaignMosaic主流程

    Args:
        config_path: 配置文件路径
    """
    print("=" * 60)
    print("  CampaignMosaic - 多平台活动数据自动整合与日报生成器")
    print("=" * 60)
    print()

    # 1. 加载配置
    print("[1/5] 加载配置...")
    try:
        loader = ConfigLoader(config_path)
    except FileNotFoundError as e:
        print(f"❌ 配置文件加载失败: {e}")
        sys.exit(1)

    campaign = loader.campaign
    campaign_name = campaign.get("name", "未命名活动")
    start_date = date.fromisoformat(campaign.get("start_date", date.today().isoformat()))
    end_date = date.fromisoformat(campaign.get("end_date", date.today().isoformat()))

    print(f"  活动: {campaign_name}")
    print(f"  日期: {start_date} ~ {end_date}")
    print()

    # 2. 数据拉取
    print("[2/5] 拉取数据...")
    dataframes = []
    errors = []
    data_sources = loader.data_sources

    for source_name, source_config in data_sources.items():
        if not source_config.get("enabled", False):
            print(f"  ⏭️  {source_name}: 已跳过（未启用）")
            continue

        if source_name not in ADAPTER_REGISTRY:
            print(f"  ⚠️  {source_name}: 未知的数据源，跳过")
            errors.append(f"未知数据源: {source_name}")
            continue

        try:
            adapter_class = import_adapter_class(ADAPTER_REGISTRY[source_name])
            adapter = adapter_class(source_config, loader.env_vars)

            if not adapter.validate_config():
                print(f"  ⚠️  {source_name}: 配置不完整，使用示例数据")
                errors.append(f"{source_name}: 配置不完整")

            df = adapter.fetch_data(start_date, end_date)
            if not df.empty:
                dataframes.append(df)
                print(f"  ✅ {source_name}: 获取 {len(df)} 条数据")
            else:
                print(f"  ⚠️  {source_name}: 无数据返回")
                errors.append(f"{source_name}: 无数据")

        except Exception as e:
            print(f"  ❌ {source_name}: {e}")
            errors.append(f"{source_name}: {e}")

    if not dataframes:
        print("  ❌ 没有获取到任何数据，退出")
        sys.exit(1)

    print()

    # 3. 数据清洗与合并
    print("[3/5] 清洗与合并数据...")
    processor = DataProcessor(loader.metrics)
    merged_df = processor.merge_dataframes(dataframes, start_date, end_date)
    merged_df = processor.compute_derived_metrics(merged_df)
    print(f"  合并后数据: {len(merged_df)} 行 x {len(merged_df.columns)} 列")
    print()

    # 4. 生成报告
    print("[4/5] 生成报告...")
    report_generator = ReportGenerator(loader.report)
    report_data = processor.get_report_data(merged_df)

    html_path = report_generator.generate(report_data, campaign_name)
    md_summary = report_generator.generate_markdown_summary(report_data, campaign_name)
    print(f"  HTML报告: {html_path}")
    print()

    # 5. 发送通知
    print("[5/5] 发送通知...")
    notifier = NotificationManager(loader.notifications)

    # 如果有错误，发送告警
    if errors:
        alert_msg = "以下数据源出现问题：\n" + "\n".join(f"- {e}" for e in errors)
        notifier.send_alert(alert_msg)

    # 发送报告通知
    subject = f"📊 {campaign_name} - 日报 {date.today().strftime('%Y-%m-%d')}"
    notification_results = notifier.send_all(subject, Path(html_path).read_text(encoding="utf-8"), md_summary)

    for channel, success in notification_results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {channel}")

    print()
    print("=" * 60)
    print("  ✅ 执行完成！")
    print(f"  📄 报告文件: {html_path}")
    print("=" * 60)

    return html_path


def main():
    """CLI入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="CampaignMosaic - 多平台活动数据自动整合与日报生成器"
    )
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="配置文件路径（默认: config.yaml）",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="使用示例配置运行演示",
    )

    args = parser.parse_args()

    if args.demo:
        # 使用示例配置运行演示
        demo_config = str(PROJECT_ROOT / "config.example.yaml")
        if Path(demo_config).exists():
            run(demo_config)
        else:
            print("❌ 示例配置文件不存在")
            sys.exit(1)
    else:
        run(args.config)


if __name__ == "__main__":
    main()
