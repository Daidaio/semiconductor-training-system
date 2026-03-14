# -*- coding: utf-8 -*-
"""
互動式訓練介面
提供實體操作模擬的遊戲化訓練體驗
"""

import gradio as gr
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.digital_twin import LithographyDigitalTwin
from core.scenario_generator import ScenarioGenerator
from datetime import datetime


class InteractiveTraining:
    """互動式訓練系統"""

    def __init__(self, secom_data_path: str):
        print("[Initializing] Interactive training system...")

        self.digital_twin = LithographyDigitalTwin(secom_data_path)
        self.scenario_generator = ScenarioGenerator(secom_data_path)

        # 訓練狀態
        self.current_scenario = None
        self.current_step = 0
        self.student_actions = []
        self.conversation_history = []
        self.equipment_state = "normal"
        self.start_time = None

        print("[OK] Interactive training system ready!\n")

    def start_scenario(self, difficulty: str) -> Tuple[str, str, str]:
        """開始新情境"""
        # 生成情境
        self.current_scenario = self.scenario_generator.generate_scenario(
            difficulty=difficulty if difficulty != "Random" else None
        )

        # 注入故障
        fault_type = self.current_scenario["type"]
        self.digital_twin.inject_fault(fault_type)

        # 初始化狀態
        self.current_step = 0
        self.student_actions = []
        self.conversation_history = []
        self.start_time = datetime.now()

        # 根據故障類型設定初始狀態
        initial_message = self._get_initial_alert(fault_type)
        self.conversation_history.append(f"[SYSTEM] {initial_message}")

        # 取得設備狀態
        equipment_status = self._get_equipment_status()

        # 可用動作
        available_actions = self._get_available_actions(fault_type)

        return (
            "\n".join(self.conversation_history),
            equipment_status,
            available_actions
        )

    def _get_initial_alert(self, fault_type: str) -> str:
        """取得初始警報訊息"""
        alerts = {
            "vacuum_leak": "WARNING! 真空計讀數異常上升！警報器響起！",
            "temperature_spike": "WARNING! 機台溫度過高！目前 500°C（正常應在 450°C）",
            "alignment_drift": "WARNING! 對準精度超出容差！誤差達到 150nm",
            "optical_intensity_drop": "WARNING! 曝光光源強度不足！只有正常值的 70%",
            "electrical_fluctuation": "WARNING! 電壓波動異常！控制系統出現錯誤訊息"
        }
        return alerts.get(fault_type, "WARNING! 設備異常！")

    def _get_equipment_status(self) -> str:
        """取得設備狀態顯示"""
        summary = self.digital_twin.get_all_sensors_summary()

        status = f"""
### 設備狀態監控

**總感測器數:** {summary['total_sensors']}
- 正常: {summary['normal']} 個 (綠)
- 警告: {summary['warning']} 個 (黃)
- 臨界: {summary['critical']} 個 (紅)

**故障狀態:** {'是' if summary['is_fault'] else '否'}
**當前步驟:** {self.current_step}
"""
        return status

    def _get_available_actions(self, fault_type: str) -> str:
        """取得可用動作列表（根據故障類型和當前步驟）"""
        # 定義每種故障的操作流程
        action_tree = {
            "vacuum_leak": {
                0: ["檢查真空計讀數", "檢查氣體流量", "按下緊急停止"],
                1: ["關閉氣體供應", "檢查密封圈", "執行洩漏測試"],
                2: ["更換密封圈", "清潔密封面", "重新組裝"],
                3: ["執行真空測試", "啟動系統", "記錄維修"]
            },
            "temperature_spike": {
                0: ["檢查溫度顯示", "檢查冷卻水流量", "降低加熱器功率"],
                1: ["檢查過濾網", "檢查冷卻泵", "檢查溫控器"],
                2: ["更換過濾網", "清潔冷卻管路", "校驗溫度感測器"],
                3: ["重啟冷卻系統", "監控溫度變化", "記錄維修"]
            },
            "alignment_drift": {
                0: ["檢查對準誤差", "檢查振動監測器", "啟動校正程序"],
                1: ["使用校正片", "調整 X 軸", "調整 Y 軸"],
                2: ["調整旋轉軸", "執行重複性測試", "清潔光學元件"],
                3: ["確認精度", "記錄校正數據", "完成校正"]
            },
            "optical_intensity_drop": {
                0: ["測量光源功率", "檢查光源使用時數", "檢查光闌開度"],
                1: ["清潔光路鏡片", "檢查光源狀態", "測量曝光劑量"],
                2: ["調整曝光時間", "更換光源（如需要）", "執行測試片曝光"],
                3: ["確認光強度", "驗證曝光品質", "記錄維修"]
            },
            "electrical_fluctuation": {
                0: ["檢查電壓讀數", "檢查電源指示燈", "測量輸入電壓"],
                1: ["檢查接地系統", "檢查電源線連接", "使用頻譜分析儀"],
                2: ["隔離干擾源", "更換電源供應器（如需要）", "檢查EMI濾波器"],
                3: ["執行系統重啟", "監控電壓穩定性", "記錄維修"]
            }
        }

        current_actions = action_tree.get(fault_type, {}).get(self.current_step, ["無可用動作"])

        # 格式化為選項
        return "\n".join([f"{i+1}. {action}" for i, action in enumerate(current_actions)])

    def perform_action(self, action: str) -> Tuple[str, str, str, str]:
        """執行動作並更新狀態"""
        if not self.current_scenario:
            return "請先開始新情境", "", "", ""

        fault_type = self.current_scenario["type"]

        # 記錄動作
        self.student_actions.append({
            "step": self.current_step,
            "action": action,
            "timestamp": datetime.now().isoformat()
        })

        # 根據動作產生系統回應
        response = self._generate_response(fault_type, action)

        # 更新對話歷史
        self.conversation_history.append(f"[YOU] {action}")
        self.conversation_history.append(f"[SYSTEM] {response}")

        # 判斷是否進入下一步
        if self._is_correct_action(fault_type, action):
            self.current_step += 1

        # 檢查是否完成
        completion_status = ""
        if self.current_step >= 4:
            completion_time = (datetime.now() - self.start_time).total_seconds() / 60
            completion_status = f"\n\n=== 訓練完成！===\n完成時間: {completion_time:.1f} 分鐘\n總步驟: {len(self.student_actions)}"

        return (
            "\n".join(self.conversation_history),
            self._get_equipment_status(),
            self._get_available_actions(fault_type),
            completion_status
        )

    def _generate_response(self, fault_type: str, action: str) -> str:
        """根據動作產生系統回應"""
        # 定義動作對應的回應
        responses = {
            "vacuum_leak": {
                "檢查真空計讀數": "真空計顯示: 1.2e-3 Torr（正常應低於 1e-6 Torr）",
                "檢查氣體流量": "氣體流量正常，未發現異常",
                "按下緊急停止": "系統已緊急停機！",
                "關閉氣體供應": "氣體供應已關閉，腔體開始洩壓",
                "檢查密封圈": "發現密封圈老化龜裂！這就是洩漏原因",
                "執行洩漏測試": "氦氣洩漏檢測器在密封面偵測到洩漏信號",
                "更換密封圈": "已更換新的 O-ring，並塗抹真空油脂",
                "清潔密封面": "密封面已清潔乾淨，無異物",
                "重新組裝": "腔體已重新組裝，確認密封",
                "執行真空測試": "真空度恢復正常！達到 5e-7 Torr",
                "啟動系統": "系統重新啟動成功，運作正常",
                "記錄維修": "維修記錄已完成！"
            },
            "temperature_spike": {
                "檢查溫度顯示": "當前溫度 500°C，持續上升中...",
                "檢查冷卻水流量": "冷卻水流量只有 2.5 LPM（正常應為 5 LPM）流量太低！",
                "降低加熱器功率": "加熱器功率已降至 50%，溫度開始下降",
                "檢查過濾網": "過濾網嚴重堵塞！這就是流量降低的原因",
                "檢查冷卻泵": "冷卻泵運作正常",
                "檢查溫控器": "溫控器設定正常",
                "更換過濾網": "已更換新的過濾網，流量恢復至 5.2 LPM",
                "清潔冷卻管路": "冷卻管路已清潔",
                "校驗溫度感測器": "溫度感測器讀數準確",
                "重啟冷卻系統": "冷卻系統已重啟，運作正常",
                "監控溫度變化": "溫度穩定下降中... 目前 450°C，正常！",
                "記錄維修": "維修記錄已完成！"
            },
            "alignment_drift": {
                "檢查對準誤差": "X軸偏移 +120nm, Y軸偏移 -80nm, θ軸偏移 0.05°",
                "檢查振動監測器": "偵測到輕微振動，可能來自空調系統",
                "啟動校正程序": "校正程序已啟動，請放入校正片",
                "使用校正片": "校正片已放置，開始光學對準",
                "調整 X 軸": "X軸已調整，目前偏移 -10nm",
                "調整 Y 軸": "Y軸已調整，目前偏移 +5nm",
                "調整旋轉軸": "旋轉軸已調整，角度偏差 < 0.01°",
                "執行重複性測試": "重複性測試中... 標準差 15nm，合格！",
                "清潔光學元件": "對準鏡頭已清潔",
                "確認精度": "對準精度恢復正常！誤差 < ±20nm",
                "記錄校正數據": "校正數據已記錄",
                "完成校正": "校正完成！系統可重新投入使用"
            },
            "optical_intensity_drop": {
                "測量光源功率": "光源輸出功率 70 mW（正常應為 100 mW）",
                "檢查光源使用時數": "光源已使用 4500 小時（建議更換時數 5000 小時）",
                "檢查光闌開度": "光闌開度正常",
                "清潔光路鏡片": "所有鏡片已清潔，光強度提升至 75 mW",
                "檢查光源狀態": "光源老化中，建議安排更換",
                "測量曝光劑量": "曝光劑量不均勻，中心 70 mJ, 邊緣 65 mJ",
                "調整曝光時間": "曝光時間已增加 30% 以補償光強度不足",
                "更換光源（如需要）": "光源更換耗時較長，暫時調整參數補償",
                "執行測試片曝光": "測試片曝光中... CD 均勻性良好！",
                "確認光強度": "光強度穩定在 75 mW，可繼續使用",
                "驗證曝光品質": "曝光品質合格，CD 控制在規格內",
                "記錄維修": "維修記錄已完成，建議 500 小時後更換光源"
            },
            "electrical_fluctuation": {
                "檢查電壓讀數": "電壓波動範圍 ±15V（正常應 ±2V）",
                "檢查電源指示燈": "電源指示燈正常",
                "測量輸入電壓": "輸入電壓穩定 220V",
                "檢查接地系統": "接地電阻 1.5Ω（正常應 < 1Ω）接地不良！",
                "檢查電源線連接": "發現電源線接觸不良",
                "使用頻譜分析儀": "偵測到 50Hz 和諧波干擾",
                "隔離干擾源": "已關閉附近干擾設備，波動改善",
                "更換電源供應器（如需要）": "電源供應器運作正常",
                "檢查EMI濾波器": "EMI 濾波器效能正常",
                "執行系統重啟": "系統重啟中...",
                "監控電壓穩定性": "電壓穩定！波動降至 ±3V，可接受範圍",
                "記錄維修": "維修記錄已完成！建議加強接地"
            }
        }

        fault_responses = responses.get(fault_type, {})
        return fault_responses.get(action, f"執行: {action}... 完成")

    def _is_correct_action(self, fault_type: str, action: str) -> bool:
        """判斷動作是否正確（簡化版，所有動作都視為正確）"""
        # 實際應用中可以根據動作類型判斷
        return True


def create_interactive_interface(secom_data_path: str):
    """建立互動式 Gradio 介面"""

    trainer = InteractiveTraining(secom_data_path)

    with gr.Blocks(title="Interactive Semiconductor Training") as demo:

        gr.Markdown("""
        # 半導體設備故障處理訓練系統（互動版）
        ## 點擊按鈕進行實體操作模擬
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 開始訓練")
                difficulty = gr.Dropdown(
                    choices=["Random", "EASY", "MEDIUM", "HARD"],
                    value="MEDIUM",
                    label="選擇難度"
                )
                start_btn = gr.Button("開始新情境", variant="primary", size="lg")

                gr.Markdown("### 設備狀態")
                equipment_status = gr.Markdown()

                gr.Markdown("### 可用動作")
                available_actions = gr.Markdown()

            with gr.Column(scale=2):
                gr.Markdown("### 訓練對話記錄")
                conversation = gr.Textbox(
                    lines=20,
                    label="",
                    interactive=False
                )

                gr.Markdown("### 執行動作")
                action_input = gr.Textbox(
                    label="輸入動作（或從上方選擇）",
                    placeholder="例如: 檢查冷卻水流量"
                )

                with gr.Row():
                    action_btn = gr.Button("執行動作", variant="primary")
                    clear_btn = gr.Button("清除輸入")

                completion_status = gr.Textbox(
                    label="完成狀態",
                    interactive=False
                )

        # 快捷按鈕（動態生成常用動作）
        with gr.Row():
            gr.Markdown("### 快捷操作按鈕")

        quick_btns = []
        with gr.Row():
            for i in range(6):
                btn = gr.Button(f"動作 {i+1}", size="sm")
                quick_btns.append(btn)

        # === 事件綁定 ===

        def start_training(diff):
            conv, equip, actions = trainer.start_scenario(diff)
            return conv, equip, actions, ""

        def execute_action(action):
            if not action:
                return trainer.conversation_history, "", "", "請輸入動作"
            return trainer.perform_action(action)

        start_btn.click(
            fn=start_training,
            inputs=[difficulty],
            outputs=[conversation, equipment_status, available_actions, completion_status]
        )

        action_btn.click(
            fn=execute_action,
            inputs=[action_input],
            outputs=[conversation, equipment_status, available_actions, completion_status]
        )

        clear_btn.click(
            fn=lambda: "",
            outputs=[action_input]
        )

        # 快捷按鈕綁定
        for btn in quick_btns:
            btn.click(
                fn=lambda: None,  # 佔位符
                outputs=[]
            )

    return demo


if __name__ == "__main__":
    secom_path = "../../uci-secom.csv"

    if os.path.exists(secom_path):
        demo = create_interactive_interface(secom_path)
        demo.launch(server_name="127.0.0.1", server_port=None)
    else:
        print(f"Cannot find {secom_path}")
