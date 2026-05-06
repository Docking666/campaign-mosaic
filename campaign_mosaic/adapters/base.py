"""
数据源适配器基类
所有平台插件必须继承此基类并实现 fetch_data 方法
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
import pandas as pd


class BaseAdapter(ABC):
    """数据源适配器基类"""

    # 适配器唯一标识（如 'youzan', 'umeng'）
    ADAPTER_NAME: str = "base"

    def __init__(self, config: dict, env_vars: dict):
        """
        初始化适配器

        Args:
            config: 该数据源在 config.yaml 中的配置段
            env_vars: 环境变量字典（用于解析 ${VAR} 引用）
        """
        self.config = config
        self.env_vars = env_vars

    def _resolve_env(self, value: str) -> str:
        """解析环境变量引用，如 ${YOUZAN_API_KEY}"""
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            return self.env_vars.get(var_name, "")
        return value

    @abstractmethod
    def fetch_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """
        从数据源拉取数据

        Args:
            start_date: 活动开始日期
            end_date: 活动结束日期

        Returns:
            DataFrame，必须包含 'date' 列和至少一个指标列
            指标列命名格式: adapter_name.metric_name（如 'youzan.revenue'）
        """
        pass

    def validate_config(self) -> bool:
        """验证配置是否完整，子类可覆写"""
        return True

    def get_metric_columns(self) -> list:
        """返回该适配器提供的所有指标列名"""
        return []
