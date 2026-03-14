# -*- coding: utf-8 -*-
"""
物理耦合模型 (Physics Coupling Model)
實現設備參數間的物理關聯，提升數位孿生真實性

核心物理關係:
1. 熱力學耦合: 冷卻流量 → 溫度 → 熱膨脹 → 對準誤差
2. 流體動力學: 真空壓力 → 氣流 → 粒子污染
3. 光學耦合: 溫度 → 折射率 → 光學強度/對準
4. 機械耦合: 溫度 → 熱膨脹 → 機械尺寸變化 → 定位誤差
5. 化學耦合: 溫度/壓力 → 化學反應速率 → 污染生成

基於論文: "Digital twin driven intelligent manufacturing" 的物理實體層強化
"""

import numpy as np
from typing import Dict, Tuple, List
from dataclasses import dataclass
import time


@dataclass
class PhysicalConstants:
    """物理常數"""
    # 熱膨脹係數 (silicon wafer: ~2.6e-6 /°C)
    thermal_expansion_coef: float = 2.6e-6

    # 熱傳導時間常數 (秒)
    thermal_time_constant: float = 60.0

    # 光學材料折射率溫度係數 (CaF2: ~-3.5e-6 /°C)
    refractive_index_temp_coef: float = -3.5e-6

    # 真空系統洩漏率 (Torr/s per Pa pressure drop increase)
    vacuum_leak_rate: float = 1e-8

    # 過濾器堵塞對流量的影響係數
    filter_flow_impact: float = 0.001


class PhysicsCouplingModel:
    """物理耦合模型 - 計算參數間的相互影響"""

    def __init__(self):
        """初始化物理模型"""
        self.constants = PhysicalConstants()
        self.last_update_time = time.time()

        # 記錄參數歷史 (用於計算變化率)
        self.history = {
            'cooling_flow': [],
            'lens_temp': [],
            'vacuum_pressure': [],
            'filter_pressure_drop': []
        }
        self.history_length = 10  # 保留最近 10 筆記錄

    def update_coupled_parameters(self, current_state: Dict[str, float],
                                  dt: float = 1.0) -> Dict[str, float]:
        """
        根據物理耦合關係更新參數

        Args:
            current_state: 當前狀態 (來自感測器的原始讀數)
            dt: 時間間隔 (秒)

        Returns:
            耦合後的狀態 (包含二次效應)
        """
        # 複製狀態避免修改原始值
        coupled_state = current_state.copy()

        # 更新歷史記錄
        self._update_history(current_state)

        # === 1. 熱力學耦合 ===
        temp_change = self._compute_thermal_coupling(
            current_state.get('cooling_flow', 5.0),
            current_state.get('lens_temp', 23.0),
            dt
        )
        coupled_state['lens_temp'] = current_state.get('lens_temp', 23.0) + temp_change

        # === 2. 熱膨脹 → 對準誤差 ===
        alignment_change = self._compute_thermal_expansion_effect(
            coupled_state['lens_temp'],
            current_state.get('alignment_error', 0.0)
        )
        coupled_state['alignment_error'] = current_state.get('alignment_error', 0.0) + alignment_change

        # === 3. 溫度 → 光學性能 ===
        optical_change = self._compute_optical_thermal_effect(
            coupled_state['lens_temp'],
            current_state.get('light_intensity', 100.0)
        )
        coupled_state['light_intensity'] = current_state.get('light_intensity', 100.0) + optical_change

        # === 4. 過濾器 → 冷卻流量 ===
        flow_reduction = self._compute_filter_impact(
            current_state.get('filter_pressure_drop', 50.0),
            current_state.get('cooling_flow', 5.0)
        )
        coupled_state['cooling_flow'] = current_state.get('cooling_flow', 5.0) - flow_reduction

        # === 5. 壓降 → 真空洩漏 ===
        vacuum_change = self._compute_vacuum_leak_effect(
            current_state.get('filter_pressure_drop', 50.0),
            current_state.get('vacuum_pressure', 1.0e-6),
            dt
        )
        coupled_state['vacuum_pressure'] = current_state.get('vacuum_pressure', 1.0e-6) + vacuum_change

        # === 6. 真空不良 → 污染增加 → 光學衰減 ===
        contamination_effect = self._compute_contamination_effect(
            coupled_state['vacuum_pressure'],
            current_state.get('light_intensity', 100.0)
        )
        coupled_state['light_intensity'] -= contamination_effect

        # === 7. 溫度梯度 → 機械應力 → X/Y 軸誤差 ===
        temp_gradient = self._compute_temperature_gradient(coupled_state['lens_temp'])
        coupled_state['stage_position_x'] = current_state.get('stage_position_x', 0.0) + temp_gradient * 0.001
        coupled_state['stage_position_y'] = current_state.get('stage_position_y', 0.0) + temp_gradient * 0.0008

        return coupled_state

    def _compute_thermal_coupling(self, cooling_flow: float, current_temp: float,
                                  dt: float) -> float:
        """
        計算冷卻流量對溫度的影響
        基於熱平衡方程: Q_in = Q_out + Q_storage

        Args:
            cooling_flow: 冷卻流量 (L/min)
            current_temp: 當前溫度 (°C)
            dt: 時間間隔 (秒)

        Returns:
            溫度變化量 (°C)
        """
        nominal_flow = 5.0  # 標準流量
        nominal_temp = 23.0  # 標準溫度

        # 流量偏差導致的熱移除能力變化
        flow_deficit = (nominal_flow - cooling_flow) / nominal_flow

        # 溫度變化率 (°C/s) = K * 流量偏差
        # 使用一階延遲模型: dT/dt = (T_target - T_current) / tau
        heat_input_rate = 0.01  # 設備自身發熱 (°C/s)
        heat_removal_rate = (cooling_flow / nominal_flow) * 0.01

        net_heat_rate = heat_input_rate - heat_removal_rate

        # 一階延遲響應
        tau = self.constants.thermal_time_constant
        temp_change = net_heat_rate * dt * (1 - np.exp(-dt / tau))

        return temp_change

    def _compute_thermal_expansion_effect(self, temperature: float,
                                         current_error: float) -> float:
        """
        計算熱膨脹對對準誤差的影響

        Args:
            temperature: 溫度 (°C)
            current_error: 當前對準誤差 (nm)

        Returns:
            誤差變化量 (nm)
        """
        nominal_temp = 23.0
        delta_T = temperature - nominal_temp

        # 假設光學元件尺寸 ~300mm
        component_size = 300.0  # mm

        # 熱膨脹: ΔL = α * L * ΔT
        thermal_expansion = (self.constants.thermal_expansion_coef *
                           component_size * 1e6 *  # 轉換為 nm
                           delta_T)

        # 對準誤差增量 (假設 10% 的膨脹轉化為誤差)
        alignment_change = thermal_expansion * 0.1

        return alignment_change

    def _compute_optical_thermal_effect(self, temperature: float,
                                       current_intensity: float) -> float:
        """
        計算溫度對光學強度的影響 (折射率變化)

        Args:
            temperature: 溫度 (°C)
            current_intensity: 當前光強 (%)

        Returns:
            光強變化量 (%)
        """
        nominal_temp = 23.0
        delta_T = temperature - nominal_temp

        # 折射率變化: Δn = dn/dT * ΔT
        refractive_index_change = self.constants.refractive_index_temp_coef * delta_T

        # 假設光強變化與折射率成正比 (簡化模型)
        # 實際上應該考慮 Fresnel 反射、像差等
        intensity_change = refractive_index_change * current_intensity * 100

        return intensity_change

    def _compute_filter_impact(self, pressure_drop: float,
                               current_flow: float) -> float:
        """
        計算過濾器壓降對流量的影響

        Args:
            pressure_drop: 壓降 (Pa)
            current_flow: 當前流量 (L/min)

        Returns:
            流量減少量 (L/min)
        """
        nominal_pressure_drop = 50.0  # 正常壓降

        # 壓降增加 → 阻力增加 → 流量減少
        excess_pressure = max(0, pressure_drop - nominal_pressure_drop)

        # 使用 Darcy-Weisbach 方程簡化版: ΔP ∝ Q^2
        # 反推: ΔQ ∝ sqrt(ΔP)
        flow_reduction = (self.constants.filter_flow_impact *
                         np.sqrt(excess_pressure))

        return flow_reduction

    def _compute_vacuum_leak_effect(self, pressure_drop: float,
                                   current_vacuum: float, dt: float) -> float:
        """
        計算壓降增加導致的真空洩漏

        Args:
            pressure_drop: 過濾器壓降 (Pa)
            current_vacuum: 當前真空度 (Torr)
            dt: 時間間隔 (秒)

        Returns:
            真空壓力增加量 (Torr)
        """
        nominal_pressure_drop = 50.0
        excess_pressure = max(0, pressure_drop - nominal_pressure_drop)

        # 壓降增加可能表示密封問題 → 真空洩漏
        leak_rate = self.constants.vacuum_leak_rate * excess_pressure

        vacuum_increase = leak_rate * dt

        return vacuum_increase

    def _compute_contamination_effect(self, vacuum_pressure: float,
                                     current_intensity: float) -> float:
        """
        計算真空不良導致的污染對光學強度的影響

        Args:
            vacuum_pressure: 真空壓力 (Torr)
            current_intensity: 當前光強 (%)

        Returns:
            光強衰減量 (%)
        """
        nominal_vacuum = 1.0e-6  # 標準真空度

        # 真空越差，污染越嚴重
        vacuum_degradation = max(0, (vacuum_pressure - nominal_vacuum) / nominal_vacuum)

        # 污染導致光學衰減 (非線性關係)
        contamination_loss = 0.5 * vacuum_degradation * np.sqrt(current_intensity)

        return contamination_loss

    def _compute_temperature_gradient(self, temperature: float) -> float:
        """
        計算溫度梯度 (簡化模型)

        Args:
            temperature: 平均溫度 (°C)

        Returns:
            溫度梯度 (°C/mm)
        """
        nominal_temp = 23.0
        delta_T = temperature - nominal_temp

        # 假設溫度偏差 1°C 產生 0.01 °C/mm 的梯度
        gradient = delta_T * 0.01

        return gradient

    def _update_history(self, state: Dict[str, float]):
        """更新參數歷史記錄"""
        for key in ['cooling_flow', 'lens_temp', 'vacuum_pressure', 'filter_pressure_drop']:
            if key in state:
                if key not in self.history:
                    self.history[key] = []
                self.history[key].append(state[key])
                # 保持固定長度
                if len(self.history[key]) > self.history_length:
                    self.history[key].pop(0)

    def get_coupling_diagnostics(self, state: Dict[str, float]) -> Dict[str, str]:
        """
        診斷參數耦合效應，提供可解釋性

        Args:
            state: 當前狀態

        Returns:
            診斷訊息字典
        """
        diagnostics = {}

        # 檢查熱力學耦合鏈
        if state.get('cooling_flow', 5.0) < 4.5:
            temp_rise = (5.0 - state['cooling_flow']) * 0.1
            diagnostics['thermal_chain'] = (
                f"冷卻不足 → 溫度上升 {temp_rise:.2f}°C → "
                f"熱膨脹 → 對準誤差增加 ~{temp_rise * 0.01:.2f}nm"
            )

        # 檢查過濾器影響鏈
        if state.get('filter_pressure_drop', 50.0) > 100:
            diagnostics['filter_chain'] = (
                f"過濾器堵塞 → 壓降 {state['filter_pressure_drop']:.1f}Pa → "
                f"流量減少 → 散熱不良 → 溫度上升"
            )

        # 檢查真空污染鏈
        if state.get('vacuum_pressure', 1.0e-6) > 2.0e-6:
            diagnostics['vacuum_chain'] = (
                f"真空不良 → 粒子污染 → 光學元件污染 → "
                f"光強衰減 ~{(state['vacuum_pressure']/1e-6 - 1) * 0.5:.1f}%"
            )

        return diagnostics

    def predict_fault_propagation(self, initial_fault: str,
                                  current_state: Dict[str, float],
                                  time_horizon: int = 300) -> Dict[str, List[Tuple[int, float]]]:
        """
        預測故障傳播路徑 (用於預測性維護)

        Args:
            initial_fault: 初始故障 ("cooling_failure"/"filter_clog"等)
            current_state: 當前狀態
            time_horizon: 預測時間範圍 (秒)

        Returns:
            各參數的預測軌跡 {param_name: [(time, value), ...]}
        """
        predictions = {
            'lens_temp': [],
            'alignment_error': [],
            'light_intensity': [],
            'vacuum_pressure': []
        }

        # 模擬故障演進
        sim_state = current_state.copy()

        for t in range(0, time_horizon, 10):  # 每 10 秒記錄一次
            # 應用耦合模型
            sim_state = self.update_coupled_parameters(sim_state, dt=10.0)

            # 記錄預測值
            for param in predictions.keys():
                if param in sim_state:
                    predictions[param].append((t, sim_state[param]))

        return predictions


if __name__ == "__main__":
    # 測試物理耦合模型
    print("=" * 70)
    print("物理耦合模型測試")
    print("=" * 70)

    model = PhysicsCouplingModel()

    # 測試場景: 冷卻流量下降
    print("\n[測試場景] 冷卻流量下降至 3.5 L/min")
    print("-" * 70)

    initial_state = {
        'cooling_flow': 3.5,  # 故障: 流量下降
        'lens_temp': 23.0,
        'vacuum_pressure': 1.0e-6,
        'light_intensity': 100.0,
        'filter_pressure_drop': 50.0,
        'alignment_error': 0.0,
        'stage_position_x': 0.0,
        'stage_position_y': 0.0
    }

    print("\n初始狀態:")
    for key, value in initial_state.items():
        print(f"  {key:25s}: {value:.6f}")

    # 模擬 5 分鐘的演進
    current_state = initial_state.copy()
    for i in range(30):  # 30 次，每次 10 秒
        current_state = model.update_coupled_parameters(current_state, dt=10.0)

        if i % 6 == 5:  # 每 1 分鐘輸出一次
            print(f"\n第 {(i+1)*10//60} 分鐘後:")
            print(f"  溫度:     {current_state['lens_temp']:.3f}°C (↑{current_state['lens_temp']-23:.3f}°C)")
            print(f"  對準誤差: {current_state['alignment_error']:.3f}nm")
            print(f"  光強:     {current_state['light_intensity']:.2f}%")
            print(f"  真空:     {current_state['vacuum_pressure']:.2e} Torr")

    # 診斷訊息
    print("\n" + "=" * 70)
    print("耦合效應診斷:")
    print("=" * 70)
    diagnostics = model.get_coupling_diagnostics(current_state)
    for key, msg in diagnostics.items():
        print(f"\n[{key}]")
        print(f"  {msg}")

    print("\n" + "=" * 70)
    print("測試完成!")
    print("=" * 70)
