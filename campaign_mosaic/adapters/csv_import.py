"""
CSV/HTTP 通用数据导入适配器
支持从本地CSV文件或远程HTTP接口导入自定义数据
"""

from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import requests

from .base import BaseAdapter


class CsvImportAdapter(BaseAdapter):
    """CSV/HTTP 通用数据导入适配器"""

    ADAPTER_NAME = "csv_import"

    def __init__(self, config: dict, env_vars: dict):
        super().__init__(config, env_vars)
        self.file_path = config.get("file_path", "")
        self.url = config.get("url", "")
        self.date_column = config.get("date_column", "date")
        self.metric_columns = config.get("metric_columns", [])

    def validate_config(self) -> bool:
        return bool(self.file_path) or bool(self.url)

    def fetch_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """
        从CSV文件或HTTP接口导入数据

        Returns:
            DataFrame with columns: [date, csv_import.*]
        """
        try:
            if self.url:
                df = self._fetch_from_url()
            elif self.file_path:
                df = self._fetch_from_file()
            else:
                return pd.DataFrame(columns=["date"])

            if df.empty:
                return pd.DataFrame(columns=["date"])

            # 确保有date列
            if self.date_column in df.columns:
                df = df.rename(columns={self.date_column: "date"})
            elif "date" not in df.columns:
                df["date"] = pd.date_range(start_date, end_date)

            # 转换日期
            df["date"] = pd.to_datetime(df["date"]).dt.date

            # 过滤日期范围
            df = df[
                (df["date"] >= start_date) & (df["date"] <= end_date)
            ].reset_index(drop=True)

            # 为列名添加前缀
            prefix = f"{self.ADAPTER_NAME}."
            rename_map = {}
            for col in df.columns:
                if col != "date" and not col.startswith(prefix):
                    rename_map[col] = f"{prefix}{col}"
            df = df.rename(columns=rename_map)

            return df

        except Exception as e:
            print(f"[CsvImportAdapter] 数据导入失败: {e}")
            return pd.DataFrame(columns=["date"])

    def _fetch_from_file(self) -> pd.DataFrame:
        """从本地CSV文件读取"""
        file_path = Path(self.file_path)
        if not file_path.exists():
            print(f"[CsvImportAdapter] 文件不存在: {self.file_path}")
            return pd.DataFrame()

        return pd.read_csv(file_path)

    def _fetch_from_url(self) -> pd.DataFrame:
        """从HTTP接口获取CSV数据"""
        response = requests.get(self.url, timeout=30)
        response.raise_for_status()

        # 尝试解析为CSV
        from io import StringIO
        return pd.read_csv(StringIO(response.text))

    def get_metric_columns(self) -> list:
        if self.metric_columns:
            return [f"{self.ADAPTER_NAME}.{col}" for col in self.metric_columns]
        return []
