"""
配置加载器
解析 config.yaml，处理环境变量引用
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class ConfigLoader:
    """配置加载与管理"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config = {}
        self.env_vars = {}
        self._load_env()
        self._load_config()

    def _load_env(self):
        """加载 .env 文件中的环境变量"""
        load_dotenv()
        self.env_vars = dict(os.environ)

    def _load_config(self):
        """加载并解析 YAML 配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # 递归解析环境变量引用
        self.config = self._resolve_env_vars(self.config)

    def _resolve_env_vars(self, obj: Any) -> Any:
        """递归解析配置中的 ${VAR} 环境变量引用"""
        if isinstance(obj, str):
            return self._resolve_env_string(obj)
        elif isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(item) for item in obj]
        return obj

    def _resolve_env_string(self, value: str) -> str:
        """解析字符串中的环境变量引用"""
        pattern = r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}"

        def replacer(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return re.sub(pattern, replacer, value)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号分隔的嵌套路径）"""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    @property
    def campaign(self) -> dict:
        return self.config.get("campaign", {})

    @property
    def data_sources(self) -> dict:
        return self.config.get("data_sources", {})

    @property
    def metrics(self) -> list:
        return self.config.get("metrics", [])

    @property
    def report(self) -> dict:
        return self.config.get("report", {})

    @property
    def notifications(self) -> dict:
        return self.config.get("notifications", {})
