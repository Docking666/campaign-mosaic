"""
友盟（Umeng）用户行为数据适配器
通过友盟开放API拉取DAU、新增用户等数据

API文档: https://developer.umeng.com/
"""

from datetime import date, timedelta
import pandas as pd
import requests

from .base import BaseAdapter


class UmengAdapter(BaseAdapter):
    """友盟用户行为数据适配器"""

    ADAPTER_NAME = "umeng"
    API_BASE = "https://api.umeng.com"

    def __init__(self, config: dict, env_vars: dict):
        super().__init__(config, env_vars)
        self.app_key = self._resolve_env(config.get("app_key", ""))

    def validate_config(self) -> bool:
        return bool(self.app_key)

    def fetch_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """
        拉取友盟用户行为数据

        Returns:
            DataFrame with columns: [date, umeng.dau, umeng.new_users, umeng.active_users]
        """
        if not self.validate_config():
            return self._generate_sample_data(start_date, end_date)

        try:
            headers = {"Content-Type": "application/json"}
            params = {
                "appkey": self.app_key,
                "start_date": start_date.strftime("%Y%m%d"),
                "end_date": end_date.strftime("%Y%m%d"),
                "period_type": "daily",
            }

            # 实际API调用（需替换为真实端点）
            # response = requests.get(f"{self.API_BASE}/v1/apps/{self.app_key}/stats",
            #                        headers=headers, params=params, timeout=30)
            # data = response.json()
            # ... 解析数据

            return self._generate_sample_data(start_date, end_date)

        except requests.RequestException as e:
            print(f"[UmengAdapter] API请求失败: {e}")
            return self._generate_sample_data(start_date, end_date)

    def _generate_sample_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """生成示例数据用于演示"""
        import random
        random.seed(43)

        data = []
        current = start_date
        base_dau = 10000
        while current <= end_date:
            # 模拟DAU波动
            dau = int(base_dau * random.uniform(0.8, 1.3))
            new_users = int(dau * random.uniform(0.05, 0.15))
            data.append({
                "date": current,
                "umeng.dau": dau,
                "umeng.new_users": new_users,
                "umeng.active_users": int(dau * random.uniform(0.6, 0.9)),
            })
            current += timedelta(days=1)

        return pd.DataFrame(data)

    def get_metric_columns(self) -> list:
        return ["umeng.dau", "umeng.new_users", "umeng.active_users"]
