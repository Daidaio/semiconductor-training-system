# -*- coding: utf-8 -*-
"""
情境模擬介面 (Simulation Interface)
全新設計的自由輸入訓練介面
"""

import gradio as gr
from typing import Dict, List, Tuple
from datetime import datetime
import sys
from pathlib import Path

# 添加父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scenario_engine import ScenarioEngine
from core.natural_language_controller import NaturalLanguageController, ActionExecutor
from core.ai_expert_advisor import AIExpertAdvisor
from core.digital_twin import LithographyDigitalTwin


class SimulationTrainingSystem:
    """情境模擬訓練系統"""

    def __init__(self, secom_data_path: str):
        """初始化系統"""
        print("[Init] Simulation training system...")

        # 核心模組
        self.scenario_engine = ScenarioEngine(secom_data_path)
        self.digital_twin = LithographyDigitalTwin(secom_data_path)
        self.nlu_controller = NaturalLanguageController()
        self.action_executor = ActionExecutor(self.digital_twin)
        self.ai_advisor = AIExpertAdvisor()

        # 系統狀態
        self.current_scenario = None
        self.session_active = False
        self.action_history = []
        self.last_update_time = None
        self.auto_progression_enabled = True

        print("[OK] System ready!")

    def start_new_scenario(self, difficulty: str = "medium") -> Tuple[str, str, str, str]:
        """
        開始新情境

        Returns:
            (equipment_html, dashboard_html, system_message, action_log)
        """
        # 初始化新情境
        scenario_info = self.scenario_engine.initialize_scenario(
            scenario_type=None,
            difficulty=difficulty
        )

        self.current_scenario = scenario_info
        self.session_active = True
        self.action_history = []
        self.last_update_time = datetime.now()
        self.ai_advisor.reset()

        # 生成警報訊息
        alarm_message = scenario_info["alarm_message"]

        # 生成初始介面
        equipment_html = self._generate_equipment_diagram(scenario_info["initial_state"])
        dashboard_html = self._generate_dashboard(scenario_info["initial_state"])

        system_message = f"""
{alarm_message}

==========================================

你是現場工程師，請用文字輸入你的操作！

範例輸入：
- 「檢查冷卻水流量」
- 「調整冷卻水流量到 5.5」
- 「詢問專家為什麼溫度上升」
- 「停機更換過濾網」

請開始你的操作...
"""

        action_log = "[系統日誌]\n情境已開始，計時器啟動\n"

        return equipment_html, dashboard_html, system_message, action_log

    def process_user_input(self, user_input: str, equipment_html: str,
                          dashboard_html: str, system_message: str,
                          action_log: str) -> Tuple[str, str, str, str, str]:
        """
        處理學員輸入

        Returns:
            (user_input_cleared, equipment_html, dashboard_html, system_message, action_log)
        """
        if not self.session_active:
            return "", equipment_html, dashboard_html, "請先開始新情境", action_log

        if not user_input.strip():
            return "", equipment_html, dashboard_html, system_message, action_log

        # 記錄時間
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 1. 解析輸入
        parsed_input = self.nlu_controller.parse_input(user_input)

        # 記錄動作
        self.action_history.append(parsed_input)

        # 更新日誌
        action_description = self.nlu_controller.generate_action_description(parsed_input)
        action_log += f"\n[{timestamp}] 學員：{action_description}"

        # 2. 檢查是否是詢問專家
        if parsed_input["intent"] == "ask":
            response = self._handle_expert_question(parsed_input, system_message)
            return "", equipment_html, dashboard_html, response, action_log

        # 3. 驗證動作
        current_state = self.scenario_engine.get_current_state()
        is_valid, validation_msg = self.nlu_controller.validate_action(parsed_input, current_state)

        if not is_valid:
            if validation_msg == "warning_shutdown":
                # 停機警告
                warning_msg = f"""
{system_message}

==========================================
[停機確認]

停機會影響生產線的進度和產量。
請確認是否真的需要停機？

如果確定，請再次輸入：「確認停機」
如果要繼續排查，請輸入其他檢查指令
"""
                current_state["shutdown_confirmed"] = False
                return "", equipment_html, dashboard_html, warning_msg, action_log
            else:
                # 其他驗證失敗
                error_msg = f"{system_message}\n\n==========================================\n[錯誤] {validation_msg}"
                return "", equipment_html, dashboard_html, error_msg, action_log

        # 4. 執行動作
        action_result = self.action_executor.execute(parsed_input, current_state)

        # 5. 應用效果到情境
        update_info = self.scenario_engine.apply_action_effect(action_result)

        # 6. 更新顯示
        new_state = self.scenario_engine.get_current_state()

        equipment_html = self._generate_equipment_diagram(new_state)
        dashboard_html = self._generate_dashboard(new_state)

        # 7. 生成系統回應
        response_message = self._generate_response_message(
            action_result, update_info, new_state
        )

        # 8. 檢查 AI 肯定
        affirmation = self.ai_advisor.provide_affirmation(
            parsed_input,
            self.scenario_engine.scenario_type
        )

        if affirmation:
            response_message += f"\n\n{affirmation}"

        # 9. 檢查是否解決
        if update_info.get("resolved"):
            response_message += self._generate_completion_message()
            self.session_active = False

        # 10. 更新時間
        self.last_update_time = datetime.now()

        return "", equipment_html, dashboard_html, response_message, action_log

    def _handle_expert_question(self, parsed_input: Dict, current_message: str) -> str:
        """處理專家諮詢"""
        question = parsed_input["raw_input"]

        scenario_info = self.scenario_engine.get_scenario_info()
        current_state = self.scenario_engine.get_current_state()

        expert_response = self.ai_advisor.respond_to_question(
            question, scenario_info, current_state, self.action_history
        )

        response = f"{current_message}\n\n==========================================\n{expert_response}"

        return response

    def _generate_response_message(self, action_result: Dict,
                                   update_info: Dict, new_state: Dict) -> str:
        """生成系統回應訊息"""
        message = "[系統回應]\n\n"

        # 動作結果
        message += action_result["message"]

        # 警告
        if action_result.get("warnings"):
            message += "\n\n[警告]\n"
            for warning in action_result["warnings"]:
                message += f"! {warning}\n"

        # 狀態變化
        if action_result.get("state_changes"):
            message += "\n\n[狀態更新]\n"
            for key, value in action_result["state_changes"].items():
                message += f"- {key}: {value}\n"

        return message

    def _generate_completion_message(self) -> str:
        """生成完成訊息"""
        scenario_info = self.scenario_engine.get_scenario_info()
        evaluation = self.scenario_engine.evaluate_actions(self.action_history)

        message = "\n\n=========================================="
        message += "\n[情境完成]"
        message += "\n\n故障已解決！機台可以恢復正常運作。\n\n"

        message += f"處理時間：{self.scenario_engine.time_elapsed} 秒\n"
        message += f"動作次數：{len(self.action_history)} 次\n"
        message += f"準確度：{evaluation['accuracy']*100:.1f}%\n"
        message += f"效率：{evaluation['time_score']*100:.1f}%\n"
        message += f"安全性：{evaluation['safety_score']*100:.1f}%\n"
        message += f"\n總分：{evaluation['overall_score']*100:.1f} 分\n"

        # AI 專家復盤
        final_review = self.ai_advisor.provide_final_review(
            scenario_info, evaluation, self.action_history
        )

        message += f"\n\n{final_review}"

        return message

    def auto_progress(self, equipment_html: str, dashboard_html: str,
                     system_message: str, action_log: str) -> Tuple[str, str, str, str]:
        """
        自動演進故障（定時觸發）

        Returns:
            (equipment_html, dashboard_html, system_message, action_log)
        """
        if not self.session_active:
            return equipment_html, dashboard_html, system_message, action_log

        if self.last_update_time is None:
            return equipment_html, dashboard_html, system_message, action_log

        # 計算經過時間
        now = datetime.now()
        elapsed = (now - self.last_update_time).total_seconds()

        # 更新演進
        progression_info = self.scenario_engine.update_progression(int(elapsed))

        if progression_info.get("progressed"):
            # 故障惡化了
            new_state = progression_info["state"]

            equipment_html = self._generate_equipment_diagram(new_state)
            dashboard_html = self._generate_dashboard(new_state)

            # 添加演進訊息
            progression_msg = progression_info["message"]
            system_message = f"{system_message}\n\n{progression_msg}"

            # 更新日誌
            timestamp = now.strftime("%H:%M:%S")
            action_log += f"\n[{timestamp}] [系統] 故障持續演進..."

        self.last_update_time = now

        return equipment_html, dashboard_html, system_message, action_log

    def _generate_equipment_diagram(self, state: Dict) -> str:
        """生成設備示意圖"""

        # 根據故障類型決定顯示顏色
        lens_color = "#ff4444" if state.get("lens_temp", 23) > 25 else "#44ff44"
        cooling_color = "#ff4444" if state.get("cooling_flow", 5.0) < 4.0 else "#44ff44"
        vacuum_color = "#ff4444" if state.get("vacuum_leak", False) else "#44ff44"
        alignment_color = "#ff4444" if state.get("alignment_error_x", 0) > 0.1 else "#44ff44"

        html = f"""
        <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
            <h3 style="color: white; text-align: center; margin-top: 0;">
                曝光機設備示意圖
            </h3>
            <svg width="100%" height="350" viewBox="0 0 400 350">
                <!-- 鏡頭系統 -->
                <rect x="150" y="20" width="100" height="60" fill="{lens_color}"
                      stroke="#333" stroke-width="2" rx="5">
                    <animate attributeName="opacity" values="1;0.7;1" dur="2s" repeatCount="indefinite"/>
                </rect>
                <text x="200" y="55" text-anchor="middle" fill="white" font-size="14">鏡頭</text>

                <!-- 冷卻系統 -->
                <rect x="20" y="100" width="80" height="50" fill="{cooling_color}"
                      stroke="#333" stroke-width="2" rx="5"/>
                <text x="60" y="130" text-anchor="middle" fill="white" font-size="12">冷卻系統</text>

                <!-- 真空腔體 -->
                <rect x="130" y="120" width="140" height="100" fill="{vacuum_color}"
                      stroke="#333" stroke-width="3" rx="10"/>
                <text x="200" y="175" text-anchor="middle" fill="white" font-size="14">真空腔體</text>

                <!-- 對準系統 -->
                <rect x="300" y="100" width="80" height="50" fill="{alignment_color}"
                      stroke="#333" stroke-width="2" rx="5"/>
                <text x="340" y="125" text-anchor="middle" fill="white" font-size="11">對準</text>
                <text x="340" y="140" text-anchor="middle" fill="white" font-size="11">系統</text>

                <!-- 晶圓平台 -->
                <ellipse cx="200" cy="280" rx="60" ry="20" fill="#888" stroke="#333" stroke-width="2"/>
                <text x="200" y="285" text-anchor="middle" fill="white" font-size="12">晶圓</text>

                <!-- 連接線 -->
                <line x1="60" y1="125" x2="130" y2="160" stroke="white" stroke-width="2"/>
                <line x1="200" y1="80" x2="200" y2="120" stroke="white" stroke-width="2"/>
                <line x1="270" y1="170" x2="300" y2="125" stroke="white" stroke-width="2"/>
                <line x1="200" y1="220" x2="200" y1="260" stroke="white" stroke-width="2"/>
            </svg>

            <div style="text-align: center; color: white; margin-top: 10px; font-size: 12px;">
                <span style="color: #44ff44;">● 正常</span>
                <span style="margin-left: 20px; color: #ff4444;">● 異常</span>
            </div>
        </div>
        """

        return html

    def _generate_dashboard(self, state: Dict) -> str:
        """生成參數儀表板"""

        def get_color(value, min_val, max_val, normal_min, normal_max):
            if normal_min <= value <= normal_max:
                return "#4caf50"
            elif min_val <= value <= max_val:
                return "#ff9800"
            else:
                return "#f44336"

        # 參數定義
        params = [
            {
                "name": "鏡頭溫度",
                "value": state.get("lens_temp", 23.0),
                "unit": "°C",
                "min": 20, "max": 30,
                "normal_min": 22, "normal_max": 24
            },
            {
                "name": "冷卻流量",
                "value": state.get("cooling_flow", 5.0),
                "unit": "L/min",
                "min": 0, "max": 10,
                "normal_min": 4.5, "normal_max": 5.5
            },
            {
                "name": "真空壓力",
                "value": state.get("vacuum_pressure", 1e-6),
                "unit": "Torr",
                "min": 0, "max": 1e-4,
                "normal_min": 5e-7, "normal_max": 2e-6,
                "scientific": True
            },
            {
                "name": "光源強度",
                "value": state.get("light_intensity", 100),
                "unit": "%",
                "min": 0, "max": 120,
                "normal_min": 95, "normal_max": 105
            },
            {
                "name": "X軸誤差",
                "value": state.get("alignment_error_x", 0.0),
                "unit": "μm",
                "min": 0, "max": 0.5,
                "normal_min": 0, "normal_max": 0.05
            },
            {
                "name": "Y軸誤差",
                "value": state.get("alignment_error_y", 0.0),
                "unit": "μm",
                "min": 0, "max": 0.5,
                "normal_min": 0, "normal_max": 0.05
            }
        ]

        html = """
        <div style="background: #f5f5f5; padding: 15px; border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="text-align: center; margin-top: 0; color: #333;">
                即時參數監控
            </h3>
        """

        for param in params:
            value = param["value"]
            color = get_color(value, param["min"], param["max"],
                            param["normal_min"], param["normal_max"])

            # 計算百分比（用於進度條）
            percentage = (value - param["min"]) / (param["max"] - param["min"]) * 100
            percentage = max(0, min(100, percentage))

            # 格式化數值顯示
            if param.get("scientific"):
                value_display = f"{value:.2e}"
            else:
                value_display = f"{value:.2f}"

            html += f"""
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-weight: bold; color: #333;">{param['name']}</span>
                    <span style="color: {color}; font-weight: bold;">
                        {value_display} {param['unit']}
                    </span>
                </div>
                <div style="background: #ddd; height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: {color}; height: 100%; width: {percentage}%;
                               transition: all 0.3s ease;"></div>
                </div>
            </div>
            """

        html += """
        </div>
        """

        return html


def create_simulation_interface(secom_data_path: str):
    """建立情境模擬介面"""

    system = SimulationTrainingSystem(secom_data_path)

    with gr.Blocks(title="Simulation Training System") as demo:

        gr.Markdown("""
        # 半導體設備故障處理模擬訓練系統
        ## Free-Form Natural Language Simulation

        這是真實情境模擬，不是選擇題！
        - 用自然語言輸入你的操作
        - 系統會模擬真實反應
        - 故障會隨時間演進
        - AI 專家只在你詢問時出現
        """)

        # 控制區
        with gr.Row():
            difficulty_dropdown = gr.Dropdown(
                choices=["easy", "medium", "hard"],
                value="medium",
                label="難度"
            )
            start_btn = gr.Button("開始新情境", variant="primary", size="lg")

        # 上半部：設備圖 + 參數儀表
        with gr.Row():
            with gr.Column(scale=1):
                equipment_display = gr.HTML(label="設備狀態")

            with gr.Column(scale=1):
                dashboard_display = gr.HTML(label="參數監控")

        # 系統訊息區
        system_messages = gr.Textbox(
            label="系統訊息",
            lines=15,
            max_lines=20,
            interactive=False
        )

        # 輸入區（大文字框）
        with gr.Row():
            user_input = gr.Textbox(
                label="",
                placeholder="在此輸入你的操作... (例如：檢查冷卻水流量)",
                lines=2,
                max_lines=3,
                scale=4
            )
            submit_btn = gr.Button("執行", variant="primary", scale=1)

        # 動作日誌
        action_log = gr.Textbox(
            label="操作日誌",
            lines=10,
            interactive=False
        )

        # 定時器（用於自動演進）
        timer = gr.Timer(value=10, active=False)  # 每10秒觸發一次

        # 事件綁定
        def start_scenario(difficulty):
            eq, dash, msg, log = system.start_new_scenario(difficulty)
            return eq, dash, msg, log, gr.Timer(active=True)

        start_btn.click(
            fn=start_scenario,
            inputs=[difficulty_dropdown],
            outputs=[equipment_display, dashboard_display, system_messages, action_log, timer]
        )

        submit_btn.click(
            fn=system.process_user_input,
            inputs=[user_input, equipment_display, dashboard_display, system_messages, action_log],
            outputs=[user_input, equipment_display, dashboard_display, system_messages, action_log]
        )

        user_input.submit(
            fn=system.process_user_input,
            inputs=[user_input, equipment_display, dashboard_display, system_messages, action_log],
            outputs=[user_input, equipment_display, dashboard_display, system_messages, action_log]
        )

        # 定時自動演進
        timer.tick(
            fn=system.auto_progress,
            inputs=[equipment_display, dashboard_display, system_messages, action_log],
            outputs=[equipment_display, dashboard_display, system_messages, action_log]
        )

    return demo
