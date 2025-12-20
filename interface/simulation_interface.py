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
from core.ai_scenario_mentor import AIScenarioMentor
from core.digital_twin import LithographyDigitalTwin
from core.closed_loop_control import ClosedLoopController
from interface.equipment_visualizer_industrial import IndustrialEquipmentVisualizer
import os


class SimulationTrainingSystem:
    """情境模擬訓練系統"""

    def __init__(self, secom_data_path: str, use_ai_mentor: bool = True):
        """初始化系統"""
        print("[Init] Simulation training system...")

        # 核心模組
        self.scenario_engine = ScenarioEngine(secom_data_path)
        self.digital_twin = LithographyDigitalTwin(secom_data_path)
        self.nlu_controller = NaturalLanguageController()
        self.action_executor = ActionExecutor(self.digital_twin)

        # AI 系統：使用新的 AI 情境學長（優先）或舊的 AI 專家顧問
        self.use_ai_mentor = use_ai_mentor
        if use_ai_mentor:
            self.ai_mentor = AIScenarioMentor(use_ai=True)
            self.ai_advisor = None  # 不使用舊版
            print("[OK] 使用 AI 情境學長模式")
        else:
            self.ai_advisor = AIExpertAdvisor()
            self.ai_mentor = None
            print("[OK] 使用傳統專家顧問模式")

        # 設備視覺化器（使用真實照片模式）
        self.equipment_visualizer = IndustrialEquipmentVisualizer()
        print("[OK] 真實照片視覺化器已載入 (ASML 設備大圖 + 故障標示)")

        # 閉環控制系統
        self.closed_loop = ClosedLoopController(
            sensors=self.scenario_engine.sensors,
            process_db=self.scenario_engine.process_db
        )
        print("[OK] 閉環控制系統已載入")

        # 系統狀態
        self.current_scenario = None
        self.session_active = False
        self.action_history = []
        self.last_update_time = None
        self.auto_progression_enabled = True

        # 對話歷史（用於 Chatbot 組件）
        self.conversation_history = []

        # 設備狀態檢查結果（用於顯示實體部件狀態）
        self.equipment_status = {}

        # 當前選中的部件（用於互動式視覺化）
        self.selected_component = None

        print("[OK] System ready!")

    def start_new_scenario(self, difficulty: str = "medium") -> Tuple[str, str, str, list, str]:
        """
        開始新情境

        Returns:
            (equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log)
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

        # 重置對話歷史和設備狀態
        self.conversation_history = []
        self.equipment_status = {}

        # 啟動閉環監控系統
        def alarm_callback(alarm):
            """告警回調 - 記錄到對話歷史"""
            alarm_msg = f"\n[自動告警] {alarm.parameter_name} 異常\n"
            alarm_msg += f"當前值: {alarm.current_value:.4f}\n"
            alarm_msg += f"偏移: {alarm.deviation_percent:.1f}%\n"
            alarm_msg += f"診斷: {alarm.diagnosis}\n"
            alarm_msg += f"建議: {alarm.suggestion}"
            print(alarm_msg)  # 在後台輸出

        def clear_callback(alarm):
            """告警解除回調"""
            clear_msg = f"\n[自動解除] {alarm.parameter_name} 已恢復正常\n"
            clear_msg += f"處置時長: {alarm.handling_duration:.1f} 秒"
            print(clear_msg)  # 在後台輸出

        self.closed_loop.start_monitoring(
            interval=1.0,
            alarm_callback=alarm_callback,
            clear_callback=clear_callback
        )

        # 重置 AI 系統並設定情境上下文
        if self.use_ai_mentor:
            self.ai_mentor.reset()
            self.ai_mentor.set_scenario_context(self.scenario_engine.get_scenario_info())
        else:
            self.ai_advisor.reset()

        # 生成警報訊息
        alarm_message = scenario_info["alarm_message"]

        # 生成初始介面
        equipment_html = self._generate_equipment_diagram(scenario_info["initial_state"])
        dashboard_html = self._generate_dashboard(scenario_info["initial_state"])
        equipment_status_html = self._generate_equipment_status()

        # 初始系統訊息加入對話歷史
        initial_message = f"""{alarm_message}

你是現場工程師，請用文字輸入你的操作！

範例輸入：
- 「檢查冷卻水流量」或「冷卻水怎麼樣」
- 「詢問學長流量正常嗎」
- 「停機更換過濾網」或「先停一下，換過濾網」

請開始你的操作..."""

        self.conversation_history.append({
            "role": "assistant",
            "content": initial_message
        })

        action_log = "[系統日誌]\n情境已開始，計時器啟動\n"

        return equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

    def process_user_input(self, user_input: str, equipment_html: str,
                          dashboard_html: str, equipment_status_html: str,
                          conversation_history: list,
                          action_log: str) -> Tuple[str, str, str, str, list, str]:
        """
        處理學員輸入

        Returns:
            (user_input_cleared, equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log)
        """
        if not self.session_active:
            return "", equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log

        if not user_input.strip():
            return "", equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log

        # 保存原始輸入
        original_input = user_input

        # 記錄時間
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 1. 先用規則快速檢查（特別是「請問學長」這類明確的句子）
        parsed_input = self.nlu_controller.parse_input(user_input)

        # 2. 如果規則無法理解，再使用 AI 理解
        if parsed_input["intent"] == "unknown" and self.use_ai_mentor:
            # 讓 AI 嘗試理解
            ai_understanding = self.ai_mentor.understand_unclear_input(
                user_input,
                self.scenario_engine.get_scenario_info(),
                self.scenario_engine.get_current_state()
            )

            if ai_understanding:
                # AI 理解成功，轉換成標準指令
                suggested_input = ai_understanding["suggestion"]
                parsed_input = self.nlu_controller.parse_input(suggested_input)

                # 保留原始輸入
                if parsed_input["intent"] != "unknown":
                    parsed_input["raw_input"] = user_input

        # 3. 兩者都無法理解，顯示錯誤
        if parsed_input["intent"] == "unknown":
            error_msg = """抱歉，我不太理解你的意思。

請試試：
- 「檢查冷卻水」「檢查溫度」
- 「學長，該怎麼辦」
- 「停機」「更換過濾網」

或用你自己的話說，我會盡量理解。"""

            self.conversation_history.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": error_msg}
            ])
            return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

        # 記錄動作
        self.action_history.append(parsed_input)

        # 更新日誌
        action_description = self.nlu_controller.generate_action_description(parsed_input)
        action_log += f"\n[{timestamp}] 學員：{action_description}"

        # 2. 檢查是否是詢問專家
        if parsed_input["intent"] == "ask":
            expert_response = self._handle_expert_question(parsed_input)
            # 格式化學長回應（不需要系統回應標題）
            formatted_response = f"[學長回應]\n\n{expert_response}"
            # 加入對話歷史
            self.conversation_history.extend([
                {"role": "user", "content": original_input},
                {"role": "assistant", "content": formatted_response}
            ])
            return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

        # 3. 驗證動作
        current_state = self.scenario_engine.get_current_state()

        # 特殊處理：檢查是否是「確認停機」
        if parsed_input["intent"] == "shutdown" and "確認" in original_input:
            current_state["shutdown_confirmed"] = True

        is_valid, validation_msg = self.nlu_controller.validate_action(parsed_input, current_state)

        if not is_valid:
            if validation_msg == "warning_shutdown":
                # 停機警告
                warning_msg = """[停機確認]

停機會影響生產線的進度和產量。
請確認是否真的需要停機？

如果確定，請再次輸入：「確認停機」
如果要繼續排查，請輸入其他檢查指令"""

                current_state["shutdown_confirmed"] = False
                # 加入對話歷史
                self.conversation_history.extend([
                    {"role": "user", "content": original_input},
                    {"role": "assistant", "content": warning_msg}
                ])
                return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log
            else:
                # 其他驗證失敗
                error_msg = f"[錯誤] {validation_msg}"
                # 加入對話歷史
                self.conversation_history.extend([
                    {"role": "user", "content": original_input},
                    {"role": "assistant", "content": error_msg}
                ])
                return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

        # 4. 執行動作
        action_result = self.action_executor.execute(parsed_input, current_state)

        # 5. 應用效果到情境
        update_info = self.scenario_engine.apply_action_effect(action_result)

        # 6. 更新顯示
        new_state = self.scenario_engine.get_current_state()

        equipment_html = self._generate_equipment_diagram(new_state)
        dashboard_html = self._generate_dashboard(new_state)

        # 7. 特殊處理：如果是檢查動作，顯示檢查結果
        if parsed_input["intent"] == "check":
            # 更新設備狀態檢查結果
            self._update_equipment_status(parsed_input, action_result, new_state)

            # 生成設備狀態 HTML
            equipment_status_html = self._generate_equipment_status()

            # 生成檢查結果訊息（顯示在對話中）
            check_response = self._generate_check_response(parsed_input, action_result, new_state)

            # 加入對話歷史
            self.conversation_history.extend([
                {"role": "user", "content": original_input},
                {"role": "assistant", "content": check_response}
            ])

            self.last_update_time = datetime.now()
            return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

        # 8. 其他動作：生成系統回應
        new_response = self._generate_response_message(
            action_result, update_info, new_state
        )

        # 9. 檢查 AI 動作回饋（非檢查動作才給回饋）
        if self.use_ai_mentor:
            # 使用 AI 學長的動作回饋
            feedback = self.ai_mentor.provide_action_feedback(
                parsed_input, action_result,
                self.scenario_engine.get_scenario_info(), new_state
            )
            if feedback:
                new_response += f"\n\n{feedback}"
        else:
            # 使用傳統專家的肯定訊息
            affirmation = self.ai_advisor.provide_affirmation(
                parsed_input,
                self.scenario_engine.scenario_type
            )
            if affirmation:
                new_response += f"\n\n{affirmation}"

        # 10. 檢查是否解決
        if update_info.get("resolved"):
            new_response += "\n\n" + self._generate_completion_message()
            self.session_active = False

        # 11. 加入對話歷史
        self.conversation_history.extend([
            {"role": "user", "content": original_input},
            {"role": "assistant", "content": new_response}
        ])

        # 12. 更新時間
        self.last_update_time = datetime.now()

        # 生成設備狀態 HTML（非檢查動作不更新設備狀態）
        equipment_status_html = self._generate_equipment_status()

        return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

    def _handle_expert_question(self, parsed_input: Dict) -> str:
        """處理專家諮詢"""
        question = parsed_input["raw_input"]

        scenario_info = self.scenario_engine.get_scenario_info()
        current_state = self.scenario_engine.get_current_state()

        # 使用 AI 學長或傳統專家
        if self.use_ai_mentor:
            expert_response = self.ai_mentor.respond_to_question(
                question, scenario_info, current_state, self.action_history
            )
        else:
            expert_response = self.ai_advisor.respond_to_question(
                question, scenario_info, current_state, self.action_history
            )

        return expert_response

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

        # AI 復盤
        if self.use_ai_mentor:
            final_review = self.ai_mentor.provide_final_review(
                scenario_info, evaluation, self.action_history
            )
        else:
            final_review = self.ai_advisor.provide_final_review(
                scenario_info, evaluation, self.action_history
            )

        message += f"\n\n{final_review}"

        return message

    def auto_progress(self, equipment_html: str, dashboard_html: str,
                     equipment_status_html: str, conversation_history: list,
                     action_log: str) -> Tuple[str, str, str, list, str]:
        """
        自動演進故障（定時觸發）

        Returns:
            (equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log)
        """
        if not self.session_active:
            return equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log

        if self.last_update_time is None:
            return equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log

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

            # AI 學長階段轉換評論
            if self.use_ai_mentor:
                mentor_comment = self.ai_mentor.provide_stage_transition_comment(
                    self.scenario_engine.get_scenario_info(),
                    progression_info.get("new_stage", 0),
                    progression_info.get("symptoms", [])
                )
                progression_msg += "\n\n" + mentor_comment

            # 系統訊息加入對話歷史
            self.conversation_history.append({
                "role": "assistant",
                "content": progression_msg
            })

            # 更新日誌
            timestamp = now.strftime("%H:%M:%S")
            action_log += f"\n[{timestamp}] [系統] 故障持續演進..."

        self.last_update_time = now

        return equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

    def _generate_equipment_diagram(self, state: Dict) -> str:
        """生成設備視覺化圖（使用互動式視覺化器）"""
        return self.equipment_visualizer.generate_equipment_view(state, self.selected_component)

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

    def _update_equipment_status(self, parsed_input: Dict, action_result: Dict, current_state: Dict):
        """更新設備狀態檢查結果"""

        target = parsed_input.get("target")
        if not target:
            return

        # 根據檢查目標生成詳細的設備狀態資訊
        component_name = ""
        status = "normal"
        message = ""

        if target == "cooling":
            component_name = "冷卻水系統"
            flow_rate = current_state.get("cooling_flow", 5.0)
            filter_clogged = current_state.get("filter_clogged", False)

            if flow_rate < 4.5:
                status = "warning"
                message = f"流量：{flow_rate:.2f} L/min（偏低）\n"
                if filter_clogged:
                    message += "過濾網：堵塞（發現大量雜質）\n"
                    message += "管路：O環可能老化\n"
                    message += "建議：停機更換過濾網"
                else:
                    message += "管路壓力：偏低\n"
                    message += "建議：檢查管路連接"
            else:
                message = f"流量：{flow_rate:.2f} L/min（正常）\n過濾網：正常\n管路：密封良好"

        elif target == "vacuum":
            component_name = "真空系統"
            vacuum_pressure = current_state.get("vacuum_pressure", 1e-6)
            vacuum_leak = current_state.get("vacuum_leak", False)

            if vacuum_leak:
                status = "warning"
                message = f"壓力：{vacuum_pressure:.2e} Torr（異常）\n"
                message += "真空管：發現微小裂痕（O環老化）\n"
                message += "閥門：密封圈磨損\n"
                message += "建議：更換真空管O環密封圈"
            else:
                message = f"壓力：{vacuum_pressure:.2e} Torr（正常）\n真空泵：運作正常\n管路：密封良好"

        elif target == "temperature":
            component_name = "溫控系統"
            temp = current_state.get("lens_temp", 23.0)

            if temp > 25:
                status = "warning"
                message = f"鏡頭溫度：{temp:.1f}°C（偏高）\n"
                message += "散熱風扇：轉速正常\n"
                message += "可能原因：冷卻水流量不足\n"
                message += "建議：檢查冷卻水系統"
            else:
                message = f"鏡頭溫度：{temp:.1f}°C（正常）\n散熱系統：運作正常"

        elif target == "filter":
            component_name = "過濾網"
            filter_clogged = current_state.get("filter_clogged", False)

            if filter_clogged:
                status = "warning"
                message = "狀態：堵塞\n積累雜質：嚴重\n流通性：受阻\n建議：立即更換"
            else:
                message = "狀態：正常\n積累雜質：輕微\n流通性：良好"

        elif target == "light":
            component_name = "光源系統"
            light_intensity = current_state.get("light_intensity", 100)

            if light_intensity < 95:
                status = "warning"
                message = f"強度：{light_intensity:.1f}%（偏低）\n"
                message += "光學鏡片：可能有污染\n"
                message += "建議：清潔光學元件"
            else:
                message = f"強度：{light_intensity:.1f}%（正常）\n光學元件：清潔"

        elif target == "power":
            component_name = "電源系統"
            message = "供電：正常\n電壓：穩定\n插頭：連接良好"

        else:
            component_name = f"{target}"
            message = "已檢查，狀態正常"

        # 更新設備狀態字典
        self.equipment_status[component_name] = {
            "status": status,
            "message": message
        }

    def _generate_check_response(self, parsed_input: Dict, action_result: Dict, current_state: Dict) -> str:
        """生成檢查動作的對話回應"""
        target = parsed_input.get("target", "未知")

        # 獲取檢查結果
        target_name_map = {
            "cooling": "冷卻水系統",
            "vacuum": "真空系統",
            "temperature": "溫控系統",
            "filter": "過濾網",
            "light": "光源系統",
            "power": "電源系統"
        }

        component_name = target_name_map.get(target, target)

        # 從 equipment_status 獲取詳細資訊
        if component_name in self.equipment_status:
            status_info = self.equipment_status[component_name]
            message = status_info["message"]
            status = status_info["status"]

            if status == "warning":
                response = f"[檢查結果]\n\n你檢查了{component_name}，發現以下狀況：\n\n{message}"
            else:
                response = f"[檢查結果]\n\n你檢查了{component_name}：\n\n{message}"
        else:
            response = f"[檢查結果]\n\n你檢查了{component_name}，一切正常。"

        return response

    def _generate_equipment_status(self) -> str:
        """生成設備狀態檢視"""

        html = """
        <div style="background: #f0f4f8; padding: 15px; border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 15px;">
            <h3 style="text-align: center; margin-top: 0; color: #333;">
                設備狀態檢視
            </h3>
        """

        if not self.equipment_status:
            html += """
            <div style="text-align: center; color: #666; padding: 20px;">
                <p>尚未檢查任何設備</p>
                <p style="font-size: 0.9em;">輸入「檢查XX」來查看設備狀態</p>
            </div>
            """
        else:
            for component, status in self.equipment_status.items():
                icon = "✓" if status["status"] == "normal" else "⚠"
                color = "#44aa44" if status["status"] == "normal" else "#ff8800"

                html += f"""
                <div style="margin-bottom: 12px; padding: 10px; background: white;
                           border-left: 4px solid {color}; border-radius: 4px;">
                    <div style="display: flex; align-items: center; margin-bottom: 5px;">
                        <span style="font-size: 1.2em; margin-right: 8px;">{icon}</span>
                        <span style="font-weight: bold; color: #333;">{component}</span>
                    </div>
                    <div style="color: #666; font-size: 0.9em; margin-left: 28px;">
                        {status["message"]}
                    </div>
                </div>
                """

        html += """
        </div>
        """

        return html

    def select_component(self, component: str, equipment_html: str,
                        dashboard_html: str, equipment_status_html: str,
                        conversation_history: list, action_log: str) -> Tuple[str, str, str, list, str]:
        """
        處理部件選擇（用於互動式視覺化）

        Returns:
            (equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log)
        """
        if not self.session_active:
            return equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log

        # 更新選中的部件
        self.selected_component = component if component != "overview" else None

        # 重新生成設備視覺化
        current_state = self.scenario_engine.get_current_state()
        equipment_html = self._generate_equipment_diagram(current_state)

        return equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log


def create_simulation_interface(secom_data_path: str, use_ai_mentor: bool = True):
    """建立情境模擬介面"""

    system = SimulationTrainingSystem(secom_data_path, use_ai_mentor=use_ai_mentor)

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

        # 上半部：設備圖 + 參數儀表 + 設備狀態
        with gr.Row():
            with gr.Column(scale=1):
                equipment_display = gr.HTML(label="設備狀態", elem_id="equipment_display")

            with gr.Column(scale=1):
                dashboard_display = gr.HTML(label="參數監控")
                equipment_status_display = gr.HTML(label="設備檢查")

        # 系統訊息區（使用 Chatbot 以更好顯示對話歷史）
        system_messages = gr.Chatbot(
            label="對話歷史",
            height=400,
            show_label=True
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
            eq, dash, eq_status, msg, log = system.start_new_scenario(difficulty)
            return eq, dash, eq_status, msg, log, gr.Timer(active=True)

        start_btn.click(
            fn=start_scenario,
            inputs=[difficulty_dropdown],
            outputs=[equipment_display, dashboard_display, equipment_status_display, system_messages, action_log, timer]
        )

        submit_btn.click(
            fn=system.process_user_input,
            inputs=[user_input, equipment_display, dashboard_display, equipment_status_display, system_messages, action_log],
            outputs=[user_input, equipment_display, dashboard_display, equipment_status_display, system_messages, action_log]
        )

        user_input.submit(
            fn=system.process_user_input,
            inputs=[user_input, equipment_display, dashboard_display, equipment_status_display, system_messages, action_log],
            outputs=[user_input, equipment_display, dashboard_display, equipment_status_display, system_messages, action_log]
        )

        # 定時自動演進
        timer.tick(
            fn=system.auto_progress,
            inputs=[equipment_display, dashboard_display, equipment_status_display, system_messages, action_log],
            outputs=[equipment_display, dashboard_display, equipment_status_display, system_messages, action_log]
        )


    return demo
