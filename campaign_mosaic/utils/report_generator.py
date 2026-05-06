"""
报告生成引擎
使用 Jinja2 模板生成 HTML 报告，内嵌 Chart.js 图表
"""

import json
from datetime import date
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape


class ReportGenerator:
    """HTML报告生成器"""

    def __init__(self, config: dict):
        """
        Args:
            config: config.yaml 中 report 段的配置
        """
        self.config = config
        self.template_name = config.get("template", "minimal")
        self.output_dir = Path(config.get("output_dir", "./reports"))

        # 设置模板环境
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html"]),
        )

    def generate(
        self,
        report_data: dict,
        campaign_name: str,
        output_filename: Optional[str] = None,
    ) -> str:
        """
        生成HTML报告

        Args:
            report_data: DataProcessor.get_report_data() 返回的数据
            campaign_name: 活动名称
            output_filename: 输出文件名（不含路径），默认自动生成

        Returns:
            生成的HTML文件路径
        """
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 选择模板
        template_file = f"{self.template_name}.html"
        try:
            template = self.env.get_template(template_file)
        except Exception:
            template = self.env.get_template("minimal.html")

        # 准备模板数据
        template_data = {
            "campaign_name": campaign_name,
            "metrics": report_data.get("metrics", []),
            "trend": report_data.get("trend", {}),
            "date_range": report_data.get("date_range", {}),
            "summary": report_data.get("summary", {}),
            "generated_at": date.today().strftime("%Y-%m-%d %H:%M"),
        }

        # 将趋势数据转为JSON（供Chart.js使用）
        trend_json = {}
        for key, value in report_data.get("trend", {}).items():
            trend_json[key] = {
                "dates": value["dates"],
                "values": value["values"],
            }
        template_data["trend_json"] = json.dumps(trend_json, ensure_ascii=False)

        # 渲染HTML
        html_content = template.render(**template_data)

        # 生成输出文件名
        if not output_filename:
            today = date.today().strftime("%Y%m%d")
            output_filename = f"report_{today}.html"

        output_path = self.output_dir / output_filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"[ReportGenerator] 报告已生成: {output_path}")
        return str(output_path)

    def generate_markdown_summary(self, report_data: dict, campaign_name: str) -> str:
        """
        生成Markdown格式的简要报告（用于IM推送）

        Returns:
            Markdown格式的报告文本
        """
        lines = [
            f"## 📊 {campaign_name} - 日报",
            f"",
            f"**日期范围**: {report_data['date_range']['start']} ~ {report_data['date_range']['end']}",
            f"**活动天数**: {report_data['date_range']['days']} 天",
            f"",
            f"### 核心指标",
        ]

        for metric in report_data.get("metrics", []):
            arrow = "📈" if metric["change_pct"] >= 0 else "📉"
            change = f"+{metric['change_pct']}%" if metric["change_pct"] >= 0 else f"{metric['change_pct']}%"
            lines.append(
                f"- **{metric['name']}**: {metric['value']:,.2f}  {arrow} 环比 {change}"
            )

        lines.append("")
        lines.append(f"_生成时间: {date.today().strftime('%Y-%m-%d %H:%M')}_")

        return "\n".join(lines)
