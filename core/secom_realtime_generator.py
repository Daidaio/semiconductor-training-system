# -*- coding: utf-8 -*-
"""
SECOM 即時數據生成器 (SECOM Real-time Data Generator)

基於 SECOM 數據集的統計特性，生成逐秒變動的真實參數

功能:
1. 載入 SECOM 數據集並分析統計特性
2. 使用自回歸模型 (AR) 生成平滑的逐秒數據
3. 保持 SECOM 的均值、標準差、相關性
4. 支援故障注入時的參數漂移

基於: SECOM (SEmiCONductor Manufacturing) Dataset
來源: UCI Machine Learning Repository
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time


@dataclass
class ParameterStatistics:
    """參數統計特性"""
    name: str
    mean: float
    std: float
    min_val: float
    max_val: float
    autocorr: float = 0.95  # 自相關係數 (時間相關性)


class SECOMRealtimeGenerator:
    """SECOM 即時數據生成器"""

    def __init__(self, secom_csv_path: str):
        """
        初始化生成器

        Args:
            secom_csv_path: SECOM 數據集路徑
        """
        self.secom_path = secom_csv_path
        self.param_stats: Dict[str, ParameterStatistics] = {}
        self.current_values: Dict[str, float] = {}
        self.mapping = self._create_parameter_mapping()

        # 載入並分析 SECOM 數據
        self._load_secom_statistics()

    def _create_parameter_mapping(self) -> Dict[str, str]:
        """
        創建模擬參數到 SECOM 欄位的映射

        Returns:
            映射字典 {sim_param_name: secom_column}
        """
        # 根據領域知識映射模擬參數到 SECOM 欄位
        # SECOM 有 590 個感測器，我們選擇代表性的幾個
        return {
            'cooling_flow': '10',      # 冷卻流量 (流量相關感測器)
            'lens_temp': '50',         # 溫度感測器
            'vacuum_pressure': '100',  # 壓力感測器
            'light_intensity': '150',  # 光學強度
            'stage_position_x': '200', # X 軸位置
            'stage_position_y': '201', # Y 軸位置
            'filter_pressure_drop': '250', # 過濾器壓降
            'alignment_error': '300'   # 對準誤差
        }

    def _load_secom_statistics(self):
        """載入 SECOM 數據並計算統計特性"""
        try:
            # 讀取 SECOM 數據
            df = pd.read_csv(self.secom_path)

            # 為每個模擬參數計算統計量
            for sim_param, secom_col in self.mapping.items():
                if secom_col in df.columns:
                    col_data = df[secom_col].dropna()

                    if len(col_data) > 0:
                        # 計算統計量
                        mean = col_data.mean()
                        std = col_data.std()
                        min_val = col_data.min()
                        max_val = col_data.max()

                        # 計算自相關係數 (lag=1)
                        autocorr = col_data.autocorr(lag=1) if len(col_data) > 1 else 0.95
                        if pd.isna(autocorr):
                            autocorr = 0.95

                        self.param_stats[sim_param] = ParameterStatistics(
                            name=sim_param,
                            mean=mean,
                            std=std,
                            min_val=min_val,
                            max_val=max_val,
                            autocorr=autocorr
                        )

                        # 初始化當前值（標準化到模擬尺度）
                        self.current_values[sim_param] = self.normalize_secom_to_simulation_scale(sim_param, mean)

            print(f"[OK] 已載入 {len(self.param_stats)} 個參數的 SECOM 統計特性")

        except Exception as e:
            print(f"[WARN] 無法載入 SECOM 數據: {e}")
            print("[INFO] 使用預設統計特性")
            self._use_default_statistics()

    def _use_default_statistics(self):
        """使用預設統計特性（當 SECOM 數據不可用時）"""
        defaults = {
            'cooling_flow': (5.0, 0.5, 0.0, 10.0),
            'lens_temp': (23.0, 1.0, 20.0, 30.0),
            'vacuum_pressure': (1.0e-6, 5.0e-7, 0.0, 1.0e-4),
            'light_intensity': (100.0, 5.0, 0.0, 120.0),
            'stage_position_x': (0.0, 10.0, -1000.0, 1000.0),
            'stage_position_y': (0.0, 10.0, -1000.0, 1000.0),
            'filter_pressure_drop': (50.0, 10.0, 0.0, 200.0),
            'alignment_error': (0.0, 2.0, -10.0, 10.0)
        }

        for param, (mean, std, min_val, max_val) in defaults.items():
            self.param_stats[param] = ParameterStatistics(
                name=param,
                mean=mean,
                std=std,
                min_val=min_val,
                max_val=max_val,
                autocorr=0.95
            )
            self.current_values[param] = mean

    def normalize_secom_to_simulation_scale(self, param_name: str, secom_value: float) -> float:
        """
        將 SECOM 數值重新標準化到模擬尺度

        Args:
            param_name: 參數名稱
            secom_value: SECOM 原始值

        Returns:
            標準化後的值
        """
        # 定義模擬參數的目標範圍
        sim_ranges = {
            'cooling_flow': (5.0, 0.5),  # (mean, std)
            'lens_temp': (23.0, 1.0),
            'vacuum_pressure': (1.0e-6, 5.0e-7),
            'light_intensity': (100.0, 5.0),
            'stage_position_x': (0.0, 10.0),
            'stage_position_y': (0.0, 10.0),
            'filter_pressure_drop': (50.0, 10.0),
            'alignment_error': (0.0, 2.0)
        }

        if param_name not in self.param_stats or param_name not in sim_ranges:
            return secom_value

        # 獲取 SECOM 統計量
        secom_stats = self.param_stats[param_name]
        sim_mean, sim_std = sim_ranges[param_name]

        # Z-score 標準化 + 重新縮放
        if secom_stats.std > 0:
            z_score = (secom_value - secom_stats.mean) / secom_stats.std
            normalized = sim_mean + z_score * sim_std
        else:
            normalized = sim_mean

        return normalized

    def generate_next_values(self, dt: float = 1.0,
                            drift: Dict[str, float] = None,
                            use_normalization: bool = True) -> Dict[str, float]:
        """
        生成下一秒的參數值 (使用自回歸模型)

        Args:
            dt: 時間間隔 (秒)
            drift: 參數漂移 {param_name: drift_rate}
            use_normalization: 是否標準化到模擬尺度

        Returns:
            下一秒的參數值
        """
        next_values = {}

        for param_name, stats in self.param_stats.items():
            current = self.current_values[param_name]

            # AR(1) 模型: X_t = φ * X_{t-1} + (1-φ) * μ + ε
            # φ: 自相關係數, μ: 均值, ε: 白噪聲
            phi = stats.autocorr

            # 趨向均值的力量
            mean_reversion = (1 - phi) * stats.mean

            # 白噪聲
            noise = np.random.normal(0, stats.std * np.sqrt(1 - phi**2))

            # 下一個值
            next_val = phi * current + mean_reversion + noise

            # 標準化到模擬尺度
            if use_normalization:
                next_val = self.normalize_secom_to_simulation_scale(param_name, next_val)

            # 加入漂移 (故障情況)
            if drift and param_name in drift:
                drift_amount = drift[param_name] * dt
                next_val += drift_amount

            # 獲取標準化後的範圍
            if use_normalization:
                sim_ranges = {
                    'cooling_flow': (0.0, 10.0),
                    'lens_temp': (20.0, 30.0),
                    'vacuum_pressure': (0.0, 1.0e-4),
                    'light_intensity': (0.0, 120.0),
                    'stage_position_x': (-1000.0, 1000.0),
                    'stage_position_y': (-1000.0, 1000.0),
                    'filter_pressure_drop': (0.0, 200.0),
                    'alignment_error': (-10.0, 10.0)
                }
                min_val, max_val = sim_ranges.get(param_name, (stats.min_val, stats.max_val))
            else:
                min_val, max_val = stats.min_val, stats.max_val

            # 限制在合理範圍內
            next_val = np.clip(next_val, min_val, max_val)

            next_values[param_name] = next_val
            self.current_values[param_name] = next_val

        return next_values

    def inject_fault_drift(self, param_name: str, target_value: float,
                          duration: float = 60.0) -> Dict[str, float]:
        """
        注入故障漂移 (平滑過渡到目標值)

        Args:
            param_name: 參數名稱
            target_value: 目標值
            duration: 過渡時間 (秒)

        Returns:
            漂移速率字典
        """
        if param_name not in self.current_values:
            return {}

        current = self.current_values[param_name]
        drift_rate = (target_value - current) / duration

        return {param_name: drift_rate}

    def reset_to_normal(self, param_name: str):
        """
        重置參數到正常值 (均值)

        Args:
            param_name: 參數名稱
        """
        if param_name in self.param_stats:
            self.current_values[param_name] = self.param_stats[param_name].mean

    def get_statistics_summary(self) -> str:
        """
        獲取統計摘要

        Returns:
            統計摘要字串
        """
        summary = "SECOM 參數統計特性:\n"
        summary += "=" * 70 + "\n"

        for param_name, stats in self.param_stats.items():
            summary += f"\n{param_name}:\n"
            summary += f"  均值: {stats.mean:.4f}\n"
            summary += f"  標準差: {stats.std:.4f}\n"
            summary += f"  範圍: [{stats.min_val:.4f}, {stats.max_val:.4f}]\n"
            summary += f"  自相關: {stats.autocorr:.4f}\n"

        return summary


if __name__ == "__main__":
    # 測試 SECOM 即時生成器
    print("=" * 70)
    print("SECOM 即時數據生成器測試")
    print("=" * 70)

    # 尋找 SECOM 數據集
    import os
    secom_paths = ["../uci-secom.csv", "../../uci-secom.csv", "uci-secom.csv"]
    secom_path = None
    for path in secom_paths:
        if os.path.exists(path):
            secom_path = path
            break

    if not secom_path:
        print("[WARN] 找不到 SECOM 數據集，使用預設值")
        secom_path = "dummy.csv"

    generator = SECOMRealtimeGenerator(secom_path)

    # 顯示統計摘要
    print("\n" + generator.get_statistics_summary())

    # 測試逐秒生成
    print("\n" + "=" * 70)
    print("逐秒生成測試 (正常情況)")
    print("=" * 70)
    print(f"{'時間':>6s} | {'冷卻流量':>10s} | {'溫度':>10s} | {'真空壓力':>12s} | {'光強':>10s}")
    print("-" * 70)

    for i in range(10):
        values = generator.generate_next_values(dt=1.0)
        print(f"{i+1:>6d}s | {values['cooling_flow']:>10.4f} | "
              f"{values['lens_temp']:>10.4f} | "
              f"{values['vacuum_pressure']:>12.6e} | "
              f"{values['light_intensity']:>10.2f}")
        time.sleep(0.1)

    # 測試故障注入
    print("\n" + "=" * 70)
    print("故障注入測試 (冷卻流量下降)")
    print("=" * 70)

    # 注入故障: 冷卻流量降至 3.5
    drift = generator.inject_fault_drift('cooling_flow', 3.5, duration=10.0)
    print(f"注入故障: 冷卻流量 → 3.5 L/min (10秒過渡)")
    print("-" * 70)

    for i in range(15):
        values = generator.generate_next_values(dt=1.0, drift=drift)
        print(f"{i+1:>6d}s | {values['cooling_flow']:>10.4f} | "
              f"{values['lens_temp']:>10.4f}")
        time.sleep(0.1)

        # 10 秒後停止漂移
        if i == 9:
            drift = {}
            print("-" * 70)
            print("故障穩定，停止漂移")
            print("-" * 70)

    print("\n測試完成！")
