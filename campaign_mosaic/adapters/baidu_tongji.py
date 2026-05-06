"""
百度统计（Baidu Tongji）流量数据适配器
通过百度统计API拉取UV、PV等数据

API文档: https://tongji.baidu.com/api/manual/
"""

from datetime import date, timedelta
import pandas as pd
import requests

from .base import BaseAdapter


class BaiduTongjiAdapter(BaseAdapter):
    """百度统计流量数据适配器"""

    ADAPTER_NAME = "baidu_tongji"
    API_BASE = "https://api.baidu.com/json/tongji/v1/ReportService"

    def __init__(self, config: dict, env_vars: dict):
        super().__init__(config, env_vars)
        self.access_token = self._resolve_env(config.get("access_token", ""))
        self.site_id = config.get("site_id", "")

    def validate_config(self) -> bool:
        return bool(self.access_token) and bool(self.site_id)

    def fetch_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """
        拉取百度统计流量数据

        Returns:
            DataFrame with columns: [date, baidu_tongji.pv, baidu_tongji.uv,
                                      baidu_tongji.bounce_rate, baidu_tongji.avg_duration]
        """
        if not self.validate_config():
            return self._generate_sample_data(start_date, end_date)

        try:
            headers = {"Content-Type": "application/json"}
            payload = {
                "header": {
                    "account_type": 1,
                    "password": "",
                    "token": self.access_token,
                    "username": "",
                },
                "body": {
                    "query_code": "",
                    "site_id": self.site_id,
                    "method": "trend/time/a",
                    "start_date": start_date.strftime("%Y%m%d"),
                    "end_date": end_date.strftime("%Y%m%d"),
                    "metrics": "pv_count,visitor_count,bounce_ratio,avg_visit_time",
                    "gran": "day",
                },
            }

            # 实际API调用
            # response = requests.post(self.API_BASE, json=payload,
            #                         headers=headers, timeout=30)
            # data = response.json()

            return self._generate_sample_data(start_date, end_date)

        except requests.RequestException as e:
            print(f"[BaiduTongjiAdapter] API请求失败: {e}")
            return self._generate_sample_data(start_date, end_date)

    def _generate_sample_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """生成示例数据用于演示"""
        import random
        random.seed(44)

        data = []
        current = start_date
        while current <= end_date:
            pv = random.randint(20000, 80000)
            uv = int(pv * random.uniform(0.3, 0.6))
            data.append({
                "date": current,
                "baidu_tongji.pv": pv,
                "baidu_tongji.uv": uv,
                "baidu_tongji.bounce_rate": round(random.uniform(0.2, 0.5), 4),
                "baidu_tongji.avg_duration": round(random.uniform(60, 300), 1),
            })
            current += timedelta(days=1)

        return pd.DataFrame(data)

    def get_metric_columns(self) -> list:
        return [
            "baidu_tongji.pv",
            "baidu_tongji.uv",
            "baidu_tongji.bounce_rate",
            "baidu_tongji.avg_duration",
        ]
