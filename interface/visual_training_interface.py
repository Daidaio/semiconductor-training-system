# -*- coding: utf-8 -*-
"""
視覺化訓練介面
仿真實控制面板的互動式訓練系統
"""

import gradio as gr
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
import random
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.digital_twin import LithographyDigitalTwin
from core.a2a_coordinator import A2ACoordinator
from core.scenario_generator import ScenarioGenerator
from datetime import datetime


# ===== HTML/CSS 模板 =====

def get_equipment_diagram_html(fault_status: Dict = None) -> str:
    """生成曝光機示意圖 HTML"""

    # 根據故障狀態決定顏色
    lens_color = "#ff4444" if fault_status and fault_status.get("lens_fault") else "#44ff44"
    wafer_color = "#ff4444" if fault_status and fault_status.get("wafer_fault") else "#44ff44"
    stage_color = "#ff4444" if fault_status and fault_status.get("stage_fault") else "#44ff44"
    cooling_color = "#ff4444" if fault_status and fault_status.get("cooling_fault") else "#44ff44"
    vacuum_color = "#ff4444" if fault_status and fault_status.get("vacuum_fault") else "#44ff44"

    html = f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
        <h2 style="color: white; text-align: center; margin-bottom: 20px;">曝光機示意圖</h2>
        <svg width="100%" height="400" viewBox="0 0 400 400" style="background: #2d3748; border-radius: 10px;">

            <!-- 光源系統 -->
            <g id="lens-system">
                <rect x="150" y="20" width="100" height="60" fill="{lens_color}" stroke="white" stroke-width="2" rx="5">
                    <animate attributeName="opacity" values="1;0.7;1" dur="2s" repeatCount="indefinite"/>
                </rect>
                <text x="200" y="55" text-anchor="middle" fill="black" font-size="12" font-weight="bold">光學鏡頭</text>
                <circle cx="200" cy="110" r="15" fill="#ffeb3b" stroke="white" stroke-width="2">
                    <animate attributeName="r" values="15;18;15" dur="1s" repeatCount="indefinite"/>
                </circle>
            </g>

            <!-- 光束 -->
            <line x1="200" y1="125" x2="200" y2="180" stroke="#ffeb3b" stroke-width="3" stroke-dasharray="5,5">
                <animate attributeName="stroke-dashoffset" values="0;10" dur="0.5s" repeatCount="indefinite"/>
            </line>

            <!-- 晶圓 -->
            <g id="wafer">
                <circle cx="200" cy="200" r="50" fill="{wafer_color}" stroke="white" stroke-width="3"/>
                <circle cx="200" cy="200" r="45" fill="none" stroke="white" stroke-width="1" stroke-dasharray="5,5"/>
                <text x="200" y="205" text-anchor="middle" fill="black" font-size="14" font-weight="bold">晶圓</text>
            </g>

            <!-- 平台 -->
            <g id="stage">
                <rect x="100" y="260" width="200" height="40" fill="{stage_color}" stroke="white" stroke-width="2" rx="5"/>
                <text x="200" y="285" text-anchor="middle" fill="black" font-size="12" font-weight="bold">移動平台</text>
            </g>

            <!-- 冷卻系統 -->
            <g id="cooling">
                <rect x="20" y="120" width="60" height="80" fill="{cooling_color}" stroke="white" stroke-width="2" rx="5"/>
                <text x="50" y="145" text-anchor="middle" fill="black" font-size="10" font-weight="bold">冷卻</text>
                <text x="50" y="160" text-anchor="middle" fill="black" font-size="10" font-weight="bold">系統</text>
                <!-- 流動效果 -->
                <circle cx="50" cy="180" r="3" fill="#00bcd4">
                    <animate attributeName="cy" values="180;190;180" dur="1s" repeatCount="indefinite"/>
                </circle>
            </g>

            <!-- 真空系統 -->
            <g id="vacuum">
                <rect x="320" y="120" width="60" height="80" fill="{vacuum_color}" stroke="white" stroke-width="2" rx="5"/>
                <text x="350" y="145" text-anchor="middle" fill="black" font-size="10" font-weight="bold">真空</text>
                <text x="350" y="160" text-anchor="middle" fill="black" font-size="10" font-weight="bold">系統</text>
                <path d="M 340 175 L 345 180 L 340 185" stroke="white" stroke-width="2" fill="none">
                    <animateTransform attributeName="transform" type="translate" values="0,0; 10,0; 0,0" dur="1.5s" repeatCount="indefinite"/>
                </path>
            </g>

            <!-- 連接線 -->
            <line x1="80" y1="160" x2="100" y2="160" stroke="white" stroke-width="2" stroke-dasharray="3,3"/>
            <line x1="300" y1="160" x2="320" y2="160" stroke="white" stroke-width="2" stroke-dasharray="3,3"/>

            <!-- 狀態指示 -->
            <text x="200" y="370" text-anchor="middle" fill="white" font-size="14" font-weight="bold">
                系統狀態: {"異常" if fault_status and any(fault_status.values()) else "正常"}
            </text>

        </svg>
    </div>
    """
    return html


def get_parameter_display_html(params: Dict) -> str:
    """生成參數儀表板 HTML"""

    def get_color(value, normal_min, normal_max):
        if normal_min <= value <= normal_max:
            return "#4caf50"  # 綠色
        elif normal_min * 0.8 <= value <= normal_max * 1.2:
            return "#ff9800"  # 黃色
        else:
            return "#f44336"  # 紅色

    lens_temp = params.get("lens_temp", 450)
    cooling_flow = params.get("cooling_flow", 5.0)
    vacuum_pressure = params.get("vacuum_pressure", 1e-6)
    light_intensity = params.get("light_intensity", 100)
    x_error = params.get("x_error", 0)
    y_error = params.get("y_error", 0)

    html = f"""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
        <h2 style="color: white; text-align: center; margin-bottom: 20px;">即時參數監控</h2>

        <!-- 參數卡片 -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">

            <!-- 鏡頭溫度 -->
            <div style="background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: bold; font-size: 14px;">🌡️ 鏡頭溫度</span>
                    <span style="font-size: 20px; font-weight: bold; color: {get_color(lens_temp, 400, 450)};">{lens_temp}°C</span>
                </div>
                <div style="background: #e0e0e0; height: 10px; border-radius: 5px; overflow: hidden;">
                    <div style="background: {get_color(lens_temp, 400, 450)}; height: 100%; width: {min(lens_temp/5, 100)}%; transition: all 0.3s;"></div>
                </div>
                <div style="font-size: 11px; color: #666; margin-top: 5px;">正常: 400-450°C</div>
            </div>

            <!-- 冷卻水流量 -->
            <div style="background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: bold; font-size: 14px;">💧 冷卻流量</span>
                    <span style="font-size: 20px; font-weight: bold; color: {get_color(cooling_flow, 4.5, 5.5)};">{cooling_flow} L/min</span>
                </div>
                <div style="background: #e0e0e0; height: 10px; border-radius: 5px; overflow: hidden;">
                    <div style="background: {get_color(cooling_flow, 4.5, 5.5)}; height: 100%; width: {cooling_flow*10}%; transition: all 0.3s;"></div>
                </div>
                <div style="font-size: 11px; color: #666; margin-top: 5px;">正常: 4.5-5.5 L/min</div>
            </div>

            <!-- 真空壓力 -->
            <div style="background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: bold; font-size: 14px;">🔘 真空壓力</span>
                    <span style="font-size: 20px; font-weight: bold; color: {get_color(vacuum_pressure*1e6, 0.1, 1)};">{vacuum_pressure:.1e} Torr</span>
                </div>
                <div style="background: #e0e0e0; height: 10px; border-radius: 5px; overflow: hidden;">
                    <div style="background: {get_color(vacuum_pressure*1e6, 0.1, 1)}; height: 100%; width: {min(vacuum_pressure*1e7, 100)}%; transition: all 0.3s;"></div>
                </div>
                <div style="font-size: 11px; color: #666; margin-top: 5px;">正常: < 1e-6 Torr</div>
            </div>

            <!-- 光源強度 -->
            <div style="background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: bold; font-size: 14px;">💡 光源強度</span>
                    <span style="font-size: 20px; font-weight: bold; color: {get_color(light_intensity, 90, 110)};">{light_intensity}%</span>
                </div>
                <div style="background: #e0e0e0; height: 10px; border-radius: 5px; overflow: hidden;">
                    <div style="background: {get_color(light_intensity, 90, 110)}; height: 100%; width: {light_intensity}%; transition: all 0.3s;"></div>
                </div>
                <div style="font-size: 11px; color: #666; margin-top: 5px;">正常: 90-110%</div>
            </div>

            <!-- X軸誤差 -->
            <div style="background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: bold; font-size: 14px;">↔️ X軸誤差</span>
                    <span style="font-size: 20px; font-weight: bold; color: {get_color(abs(x_error), 0, 50)};">{x_error:+d} nm</span>
                </div>
                <div style="background: #e0e0e0; height: 10px; border-radius: 5px; overflow: hidden;">
                    <div style="background: {get_color(abs(x_error), 0, 50)}; height: 100%; width: {min(abs(x_error), 100)}%; transition: all 0.3s;"></div>
                </div>
                <div style="font-size: 11px; color: #666; margin-top: 5px;">正常: ±50 nm</div>
            </div>

            <!-- Y軸誤差 -->
            <div style="background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: bold; font-size: 14px;">↕️ Y軸誤差</span>
                    <span style="font-size: 20px; font-weight: bold; color: {get_color(abs(y_error), 0, 50)};">{y_error:+d} nm</span>
                </div>
                <div style="background: #e0e0e0; height: 10px; border-radius: 5px; overflow: hidden;">
                    <div style="background: {get_color(abs(y_error), 0, 50)}; height: 100%; width: {min(abs(y_error), 100)}%; transition: all 0.3s;"></div>
                </div>
                <div style="font-size: 11px; color: #666; margin-top: 5px;">正常: ±50 nm</div>
            </div>

        </div>
    </div>
    """
    return html


# ===== 訓練邏輯類別 =====

class VisualTrainingSystem:
    """視覺化訓練系統"""

    def __init__(self, secom_data_path: str):
        print("[Init] Visual training system...")

        self.digital_twin = LithographyDigitalTwin(secom_data_path)
        self.coordinator = A2ACoordinator()
        self.scenario_generator = ScenarioGenerator(secom_data_path)

        # 當前狀態
        self.current_scenario = None
        self.parameters = {
            "lens_temp": 450,
            "cooling_flow": 5.0,
            "vacuum_pressure": 1e-6,
            "light_intensity": 100,
            "x_error": 0,
            "y_error": 0
        }
        self.fault_status = {
            "lens_fault": False,
            "wafer_fault": False,
            "stage_fault": False,
            "cooling_fault": False,
            "vacuum_fault": False
        }
        self.messages = []
        self.action_log = []

        print("[OK] System ready!")

    def start_scenario(self, difficulty: str):
        """開始新情境"""
        # 生成情境
        self.current_scenario = self.scenario_generator.generate_scenario(
            difficulty=difficulty if difficulty != "Random" else None
        )

        fault_type = self.current_scenario["type"]

        # 注入故障並更新參數
        self.digital_twin.inject_fault(fault_type)
        self._update_parameters_from_fault(fault_type)

        # 初始警報
        alert = self._get_alert_message(fault_type)
        self.messages = [f"[SYSTEM ALERT] {alert}"]
        self.action_log = []

        return (
            get_equipment_diagram_html(self.fault_status),
            get_parameter_display_html(self.parameters),
            "\n".join(self.messages),
            ""
        )

    def _update_parameters_from_fault(self, fault_type: str):
        """根據故障類型更新參數"""
        if fault_type == "temperature_spike":
            self.parameters["lens_temp"] = 500
            self.parameters["cooling_flow"] = 2.5
            self.fault_status["lens_fault"] = True
            self.fault_status["cooling_fault"] = True

        elif fault_type == "vacuum_leak":
            self.parameters["vacuum_pressure"] = 1e-3
            self.fault_status["vacuum_fault"] = True

        elif fault_type == "alignment_drift":
            self.parameters["x_error"] = 120
            self.parameters["y_error"] = -80
            self.fault_status["stage_fault"] = True

        elif fault_type == "optical_intensity_drop":
            self.parameters["light_intensity"] = 70
            self.fault_status["lens_fault"] = True

        elif fault_type == "electrical_fluctuation":
            self.parameters["light_intensity"] = 85
            self.fault_status["lens_fault"] = True

    def _get_alert_message(self, fault_type: str) -> str:
        """取得警報訊息"""
        alerts = {
            "temperature_spike": "機台溫度過高！目前 500°C（正常 450°C）",
            "vacuum_leak": "真空系統異常！壓力 1e-3 Torr（正常 < 1e-6）",
            "alignment_drift": "對準系統漂移！X軸 +120nm, Y軸 -80nm",
            "optical_intensity_drop": "光源強度不足！目前 70%（正常 100%）",
            "electrical_fluctuation": "電氣系統波動！光源不穩定"
        }
        return alerts.get(fault_type, "設備異常！")

    def perform_action(self, action_name: str):
        """執行動作"""
        if not self.current_scenario:
            return (
                get_equipment_diagram_html(self.fault_status),
                get_parameter_display_html(self.parameters),
                "請先開始新情境！",
                ""
            )

        # 記錄動作
        self.action_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {action_name}")

        # 根據動作更新系統狀態
        response = self._process_action(action_name)
        self.messages.append(f"\n[YOU] {action_name}")
        self.messages.append(f"[SYSTEM] {response}")

        return (
            get_equipment_diagram_html(self.fault_status),
            get_parameter_display_html(self.parameters),
            "\n".join(self.messages),
            "\n".join(self.action_log)
        )

    def _process_action(self, action: str) -> str:
        """處理動作並返回回應"""
        fault_type = self.current_scenario["type"]

        # 溫度相關動作
        if "冷卻水" in action and "檢查" in action:
            if fault_type == "temperature_spike":
                return f"冷卻水流量異常！目前 {self.parameters['cooling_flow']} L/min（正常 5.0）"
            return "冷卻水系統正常"

        elif "冷卻水" in action and "調整" in action:
            if fault_type == "temperature_spike":
                # 發現過濾網堵塞
                return "發現過濾網堵塞！需要更換"
            return "冷卻水流量已調整"

        elif "過濾網" in action or "更換" in action:
            if fault_type == "temperature_spike":
                # 修復
                self.parameters["cooling_flow"] = 5.0
                self.parameters["lens_temp"] = 450
                self.fault_status["cooling_fault"] = False
                self.fault_status["lens_fault"] = False
                return "過濾網已更換！冷卻水流量恢復正常，溫度開始下降"
            return "已更換過濾網"

        # 真空相關動作
        elif "真空" in action:
            if fault_type == "vacuum_leak":
                if "檢查" in action:
                    return f"真空壓力異常！{self.parameters['vacuum_pressure']:.1e} Torr"
                elif "修復" in action or "密封" in action:
                    self.parameters["vacuum_pressure"] = 1e-6
                    self.fault_status["vacuum_fault"] = False
                    return "密封圈已更換！真空恢復正常"
            return "真空系統運作中"

        # 對準相關動作
        elif "對準" in action or "校正" in action:
            if fault_type == "alignment_drift":
                self.parameters["x_error"] = 0
                self.parameters["y_error"] = 0
                self.fault_status["stage_fault"] = False
                return "對準校正完成！誤差已修正"
            return "對準系統正常"

        # 光源相關動作
        elif "光源" in action or "鏡片" in action:
            if fault_type in ["optical_intensity_drop", "electrical_fluctuation"]:
                if "清潔" in action:
                    self.parameters["light_intensity"] = 95
                    return "鏡片已清潔！光強度提升至 95%"
                elif "調整" in action:
                    self.parameters["light_intensity"] = 100
                    self.fault_status["lens_fault"] = False
                    return "光源已調整！強度恢復正常"
            return "光源系統運作中"

        # 診斷專家
        elif "診斷專家" in action or "專家" in action:
            equipment_state = self.digital_twin.export_current_state()
            diagnosis = self.coordinator.start_diagnosis_session(equipment_state, "beginner")

            fault = diagnosis["session_summary"]["fault_type"]
            confidence = diagnosis["session_summary"]["confidence"]
            recommendations = diagnosis["diagnosis"]["recommendations"]

            response = f"[AI 診斷專家]\n故障類型: {fault}\n信心度: {confidence:.0%}\n\n建議:\n"
            for rec in recommendations[:3]:
                response += f"- {rec}\n"
            return response

        # 其他動作
        return f"執行: {action}"

    def get_operation_log(self):
        """取得操作記錄"""
        return "\n".join(self.action_log)


# ===== Gradio 介面 =====

def create_visual_interface(secom_data_path: str):
    """建立視覺化訓練介面"""

    system = VisualTrainingSystem(secom_data_path)

    with gr.Blocks(title="Visual Semiconductor Training") as demo:

        gr.Markdown("""
        # 半導體曝光機訓練系統（視覺化版本）
        ## Interactive Visual Training Interface
        """)

        # 上方區域：機台圖 + 參數儀表板
        with gr.Row():
            with gr.Column(scale=1):
                equipment_diagram = gr.HTML(get_equipment_diagram_html())

            with gr.Column(scale=1):
                parameter_dashboard = gr.HTML(get_parameter_display_html(system.parameters))

        # 中間區域：控制面板
        gr.Markdown("## 控制面板")

        with gr.Row():
            difficulty = gr.Dropdown(
                choices=["Random", "EASY", "MEDIUM", "HARD"],
                value="MEDIUM",
                label="選擇難度"
            )
            start_btn = gr.Button("開始新情境", variant="primary", size="lg")

        gr.Markdown("### 操作按鈕")

        with gr.Row():
            btn1 = gr.Button("🔍 檢查冷卻水系統", elem_classes="control-btn")
            btn2 = gr.Button("⚙️ 調整冷卻水流量", elem_classes="control-btn")
            btn3 = gr.Button("🌡️ 檢查溫度感測器", elem_classes="control-btn")

        with gr.Row():
            btn4 = gr.Button("💨 檢查真空系統", elem_classes="control-btn")
            btn5 = gr.Button("🔧 更換過濾網", elem_classes="control-btn")
            btn6 = gr.Button("📐 執行對準校正", elem_classes="control-btn")

        with gr.Row():
            btn7 = gr.Button("💡 清潔光學鏡片", elem_classes="control-btn")
            btn8 = gr.Button("📞 詢問診斷專家", elem_classes="control-btn", variant="secondary")

        with gr.Row():
            btn9 = gr.Button("🛑 緊急停機", elem_classes="control-btn", variant="stop")
            btn10 = gr.Button("🔄 重新開機", elem_classes="control-btn")

        # 下方區域：訊息與記錄
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 系統訊息")
                system_messages = gr.Textbox(
                    lines=15,
                    label="",
                    interactive=False
                )

            with gr.Column(scale=1):
                gr.Markdown("### 操作記錄")
                action_log = gr.Textbox(
                    lines=15,
                    label="",
                    interactive=False
                )

        # === 事件綁定 ===

        # 開始情境
        start_btn.click(
            fn=system.start_scenario,
            inputs=[difficulty],
            outputs=[equipment_diagram, parameter_dashboard, system_messages, action_log]
        )

        # 操作按鈕
        buttons = [
            (btn1, "檢查冷卻水系統"),
            (btn2, "調整冷卻水流量"),
            (btn3, "檢查溫度感測器"),
            (btn4, "檢查真空系統"),
            (btn5, "更換過濾網"),
            (btn6, "執行對準校正"),
            (btn7, "清潔光學鏡片"),
            (btn8, "詢問診斷專家"),
            (btn9, "緊急停機"),
            (btn10, "重新開機")
        ]

        for btn, action_name in buttons:
            btn.click(
                fn=lambda a=action_name: system.perform_action(a),
                outputs=[equipment_diagram, parameter_dashboard, system_messages, action_log]
            )

    return demo


if __name__ == "__main__":
    secom_path = "../../uci-secom.csv"

    if os.path.exists(secom_path):
        demo = create_visual_interface(secom_path)
        demo.launch(server_name="127.0.0.1", server_port=None)
    else:
        print(f"[ERROR] Cannot find {secom_path}")
