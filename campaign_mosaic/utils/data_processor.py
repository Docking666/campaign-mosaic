"""
数据清洗与指标计算层
负责合并多源数据、日期对齐、衍生指标计算
"""

from datetime import date, timedelta
from typing import Optional
import pandas as pd
import re


class DataProcessor:
    """数据清洗与指标计算处理器"""

    def __init__(self, metrics_config: list):
        """
        Args:
            metrics_config: config.yaml 中 metrics 段的配置列表
        """
        self.metrics_config = metrics_config
        self.computed_metrics = {}  # 缓存计算结果

    def merge_dataframes(
        self, dataframes: list[pd.DataFrame], start_date: date, end_date: date
    ) -> pd.DataFrame:
        """
        合并多个数据源的DataFrame

        Args:
            dataframes: 各适配器返回的DataFrame列表
            start_date: 活动开始日期
            end_date: 活动结束日期

        Returns:
            合并后的DataFrame，按日期对齐
        """
        if not dataframes:
            return pd.DataFrame()

        # 创建完整日期范围
        date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        base_df = pd.DataFrame({"date": date_range.date})

        # 逐个合并
        for df in dataframes:
            if df.empty:
                continue
            df_copy = df.copy()
            df_copy["date"] = pd.to_datetime(df_copy["date"]).dt.date
            base_df = base_df.merge(df_copy, on="date", how="left")

        # 补齐缺失日期（已在merge中通过left join处理）
        # 数值列填充0，其他列填充NaN
        for col in base_df.columns:
            if col != "date" and base_df[col].dtype in ["float64", "int64"]:
                base_df[col] = base_df[col].fillna(0)

        return base_df

    def compute_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        根据配置计算衍生指标

        Args:
            df: 合并后的原始数据DataFrame

        Returns:
            添加了衍生指标列的DataFrame
        """
        if df.empty:
            return df

        for metric in self.metrics_config:
            if "formula" in metric:
                metric_name = metric["name"]
                formula = metric["formula"]

                try:
                    # 解析公式中的列引用（如 youzan.revenue）
                    # 替换为DataFrame列引用
                    computed_col = self._evaluate_formula(df, formula)

                    if computed_col is not None:
                        df[metric_name] = computed_col
                        self.computed_metrics[metric_name] = formula
                        print(f"[DataProcessor] 计算衍生指标: {metric_name} = {formula}")
                except Exception as e:
                    print(f"[DataProcessor] 指标计算失败 [{metric_name}]: {e}")
                    df[metric_name] = 0

        return df

    def _evaluate_formula(self, df: pd.DataFrame, formula: str) -> Optional[pd.Series]:
        """
        安全地评估公式表达式

        支持的运算符: +, -, *, /
        支持的引用格式: adapter.metric（如 youzan.revenue）
        """
        # 提取公式中的列引用
        column_refs = re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)", formula)

        # 检查所有引用列是否存在
        for ref in column_refs:
            if ref not in df.columns:
                print(f"[DataProcessor] 公式引用的列不存在: {ref}")
                return None

        # 构建安全的表达式（将列引用替换为 df["col"]）
        safe_formula = formula
        for ref in column_refs:
            safe_formula = safe_formula.replace(ref, f'df["{ref}"]')

        # 安全评估
        try:
            result = eval(safe_formula, {"df": df, "__builtins__": {}})
            if isinstance(result, pd.Series):
                return result.round(4)
            return pd.Series([result] * len(df))
        except ZeroDivisionError:
            return pd.Series([0.0] * len(df))
        except Exception as e:
            print(f"[DataProcessor] 公式评估错误: {e}")
            return None

    def calculate_summary(self, df: pd.DataFrame) -> dict:
        """
        计算汇总统计信息

        Returns:
            包含各指标汇总数据的字典
        """
        if df.empty:
            return {}

        summary = {}
        metric_columns = [col for col in df.columns if col != "date"]

        for col in metric_columns:
            col_data = pd.to_numeric(df[col], errors="coerce")
            summary[col] = {
                "total": round(col_data.sum(), 2),
                "avg": round(col_data.mean(), 2),
                "max": round(col_data.max(), 2),
                "min": round(col_data.min(), 2),
                "latest": round(col_data.iloc[-1], 2) if len(col_data) > 0 else 0,
                "previous": round(col_data.iloc[-2], 2) if len(col_data) > 1 else 0,
                "change_pct": self._calc_change_pct(col_data),
            }

        return summary

    def _calc_change_pct(self, series: pd.Series) -> float:
        """计算最新值相对于前一天的环比变化百分比"""
        if len(series) < 2:
            return 0.0
        current = series.iloc[-1]
        previous = series.iloc[-2]
        if previous == 0:
            return 0.0
        return round((current - previous) / previous * 100, 2)

    def get_report_data(self, df: pd.DataFrame) -> dict:
        """
        准备报告渲染所需的数据结构

        Returns:
            包含所有报告数据的字典
        """
        summary = self.calculate_summary(df)

        # 构建指标列表（按config中的顺序）
        metrics_list = []
        for metric in self.metrics_config:
            name = metric["name"]
            source = metric.get("source", "")

            # 查找对应的列名
            col_name = source if source in df.columns else name

            if col_name in summary:
                info = summary[col_name]
                metrics_list.append({
                    "name": name,
                    "source": col_name,
                    "value": float(info["latest"]),
                    "total": float(info["total"]),
                    "avg": float(info["avg"]),
                    "change_pct": float(info["change_pct"]),
                    "is_positive": bool(info["change_pct"] >= 0),
                })

        # 准备趋势数据
        trend_data = {}
        for col in df.columns:
            if col != "date":
                trend_data[col] = {
                    "dates": [str(d) for d in df["date"].tolist()],
                    "values": [round(float(v), 2) for v in df[col].tolist()],
                }

        return {
            "metrics": metrics_list,
            "trend": trend_data,
            "summary": summary,
            "date_range": {
                "start": str(df["date"].iloc[0]) if len(df) > 0 else "",
                "end": str(df["date"].iloc[-1]) if len(df) > 0 else "",
                "days": len(df),
            },
            "raw_df": df,
        }
