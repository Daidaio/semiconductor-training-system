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
from core.qa_assistant import TrainingAssistant
from core.proactive_mentor import ProactiveMentor
from core.adaptive_teaching_strategy import AdaptiveTeachingStrategy
from interface.equipment_visualizer_asml_cutaway import ASMLCutawayVisualizer
import os

# 3D 設備展示模組（選擇性載入）
try:
    from interface.equipment_viewer_3d import create_3d_viewer_tab
    HAS_3D_VIEWER = True
except Exception:
    HAS_3D_VIEWER = False


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

            # 理論知識問答助手（整合到 AI 學長）
            # 使用 AI 學長的 ai_bot 作為 LLM handler
            if self.ai_mentor.ai_bot:
                self.qa_assistant = TrainingAssistant(self.ai_mentor.ai_bot)
                self.proactive_mentor = ProactiveMentor(self.ai_mentor.ai_bot)
                self.adaptive_strategy = AdaptiveTeachingStrategy(self.ai_mentor.ai_bot)
                print("[OK] 理論問答助手已整合（蘇格拉底式引導）")
                print("[OK] 主動提示學長已整合（異常偵測後主動說明）")
                print("[OK] 自適應教學策略已載入（動態調整難度）")
            else:
                self.qa_assistant = None
                self.proactive_mentor = None
                self.adaptive_strategy = None
                print("[WARN] AI 不可用，理論問答助手未啟用")
        else:
            self.ai_advisor = AIExpertAdvisor()
            self.ai_mentor = None
            self.qa_assistant = None
            self.proactive_mentor = None
            self.adaptive_strategy = None
            print("[OK] 使用傳統專家顧問模式")

        # 設備視覺化器（使用 ASML 官方剖面圖）
        self.equipment_visualizer = ASMLCutawayVisualizer()
        print("[OK] ASML 剖面圖視覺化器已載入 (官方剖面圖 + 異常區域亮紅燈)")

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

        # 訓練模式狀態（新增）
        self.training_mode = "diagnostic"  # "diagnostic" / "learning" / "reflection"
        self.pending_follow_up = None  # 待回答的反問問題
        self.pending_theory_context = None  # 待反問的理論上下文（延遲生成反問）
        self.scenario_completed = False  # 場景是否完成

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

        # 重置 ProactiveMentor 本次學習狀態（避免上次難度/分數殘留）
        if self.proactive_mentor:
            self.proactive_mentor.reset_session()

        # 生成警報訊息（使用主動提示學長）
        # 從 scenario_type 推導 root_cause（兩個 key 都對應起來）
        _SCENARIO_TO_ROOT = {
            "alignment_drift":       ("對準系統漂移", "alignment"),
            "optical_contamination": ("光學污染", "lens_contamination"),
            "power_fluctuation":     ("電源電壓波動", "alignment"),
            "cooling_failure":       ("冷卻流量不足", "cooling_flow"),
            "vacuum_leak":           ("真空洩漏", "vacuum_leak"),
            "filter_clogged":        ("濾網堵塞", "cooling_flow"),
        }
        stype = scenario_info.get('scenario_type', '')
        _ft, _rc = _SCENARIO_TO_ROOT.get(stype, ('設備異常', 'unknown'))

        if self.proactive_mentor:
            proactive_alert = self.proactive_mentor.generate_fault_alert(
                fault_info={
                    'fault_type': _ft,
                    'root_cause': _rc,
                    'severity': 'medium',
                    'scenario_name': scenario_info.get('scenario_name', '')
                },
                current_state=scenario_info["initial_state"]
            )
            alarm_message = proactive_alert
        else:
            alarm_message = scenario_info["alarm_message"]

        # 生成初始介面
        equipment_html = self._generate_equipment_diagram(scenario_info["initial_state"])
        dashboard_html = self._generate_dashboard(scenario_info["initial_state"])
        equipment_status_html = self._generate_equipment_status()

        # 初始系統訊息加入對話歷史
        initial_message = f"""{alarm_message}

━━━━━━━━━━━━━━━━━━━━
💬 【問答模式】請先回答上面學長的問題
🔧 【操作模式】回答完後，在 3D 環境靠近部件按 E 進行實際操作
━━━━━━━━━━━━━━━━━━━━"""

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
        處理學員輸入（智能模式切換）

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

        # ===== 優先攔截：待回答的反問（最高優先，不被 NLU / theory 搶走）=====
        if self.pending_follow_up:
            # closing_reflection 型別：用 ProactiveMentor 評分邏輯處理
            if isinstance(self.pending_follow_up, dict) and \
                    self.pending_follow_up.get('type') == 'closing_reflection':
                return self._handle_closing_reflection(
                    user_input, timestamp, equipment_html, dashboard_html,
                    equipment_status_html, conversation_history, action_log
                )
            return self._handle_follow_up_answer(
                user_input, timestamp, equipment_html, dashboard_html,
                equipment_status_html, conversation_history, action_log
            )

        if self.proactive_mentor and self.proactive_mentor.pending_followup:
            return self._handle_proactive_followup_answer(
                user_input, timestamp, equipment_html, dashboard_html,
                equipment_status_html, conversation_history, action_log
            )

        # ===== 智能模式切換：檢測理論問題（反問都處理完才走這裡）=====
        if self.qa_assistant and self.qa_assistant.is_theory_question(user_input):
            return self._handle_theory_question(
                user_input, timestamp, equipment_html, dashboard_html,
                equipment_status_html, conversation_history, action_log
            )

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


    def _handle_theory_question(self, user_input: str, timestamp: str,
                                equipment_html: str, dashboard_html: str,
                                equipment_status_html: str,
                                conversation_history: list,
                                action_log: str) -> Tuple[str, str, str, str, list, str]:
        """
        處理理論問題（學習模式）

        Returns:
            (user_input_cleared, equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log)
        """
        # 切換模式
        self.training_mode = "learning"

        # ===== 優先檢查：是否在問主動告警中提到的專業術語 =====
        if self.proactive_mentor:
            is_term_question, term_answer = self.proactive_mentor.answer_followup_question(user_input)
            if is_term_question and term_answer:
                # 這是專業術語追問，不直接給答案，先反問學員
                # 從問題中提取術語名稱
                term_name = self._extract_term_from_question(user_input)

                # 儲存正確答案供後續評估使用
                self.pending_term_answer = term_answer
                self.pending_term_name = term_name

                # 反問學員，引導思考
                response = f"""[學長反問]

🤔 你問的是「{term_name}」對吧？

在我告訴你之前，我想先聽聽你的想法：
**你覺得「{term_name}」是什麼意思？它在半導體製程中扮演什麼角色？**

💡 提示：試著從字面上理解，或回想一下相關的物理現象。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 請先回答你的理解，我會根據你的回答給予回饋！"""

                # 加入對話歷史
                self.conversation_history.extend([
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": response}
                ])

                # 更新日誌
                action_log += f"\n[{timestamp}] [術語反問] {term_name} - 等待學員回答"

                # 不更新設備狀態，直接返回
                return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

        # ===== 檢查：是否是對術語反問的回答 =====
        if hasattr(self, 'pending_term_answer') and self.pending_term_answer:
            # 學員正在回答術語問題，進行評估
            term_answer = self.pending_term_answer
            term_name = getattr(self, 'pending_term_name', '該術語')

            # 評估學員的回答
            evaluation = self._evaluate_term_understanding(user_input, term_name, term_answer)

            # 清除暫存
            self.pending_term_answer = None
            self.pending_term_name = None

            # 根據評估結果給予回饋（自適應模式）
            teaching_mode = evaluation.get('teaching_mode', 'standard')
            mode_label = {
                'challenge': '🎯 挑戰模式',
                'scaffolding': '🪜 鷹架引導',
                'remedial': '📖 基礎鞏固',
                'standard': '📚 標準模式'
            }.get(teaching_mode, '📚 標準模式')

            response = f"""[學長回饋] {mode_label}

{evaluation['feedback']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 **完整解釋：**

{term_answer}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 評分：{evaluation['score']}/10 | 教學模式：{mode_label}
💡 理解這個術語後，繼續處理故障吧！"""

            # 加入對話歷史
            self.conversation_history.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": response}
            ])

            # 更新日誌（包含自適應教學模式）
            action_log += f"\n[{timestamp}] [術語評估] {term_name} - 得分: {evaluation['score']}/10 ({teaching_mode})"

            return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

        # ===== 一般理論問題：需要消耗時間 =====
        # 獲取問答前的狀態
        scenario_info = self.scenario_engine.get_scenario_info()
        old_state = self.scenario_engine.get_current_state()
        context = f"{scenario_info.get('fault_type', '')}故障場景"

        # 生成回答（期間時間會流逝，故障會惡化）
        result = self.qa_assistant.generate_answer(user_input, context)

        # 更新場景狀態（模擬問答期間時間經過，約 20-30 秒）
        update_info = self.scenario_engine.update_state(time_delta=25)

        # 立即生成反問（用戶要求一次看到完整內容）
        follow_up = self.qa_assistant.generate_follow_up(
            user_input,
            result['answer'],
            context
        )

        # 再次更新場景狀態（反問生成期間又過了 20-30 秒）
        update_info2 = self.scenario_engine.update_state(time_delta=25)

        # 合併更新資訊
        new_state = self.scenario_engine.get_current_state()

        # 保存反問供後續評估使用
        self.pending_follow_up = follow_up
        self.pending_theory_context = None  # 清除延遲反問的暫存

        # 更新視覺化（反映故障惡化）
        equipment_html = self.equipment_visualizer.render(new_state)
        dashboard_html = self.dashboard_generator.generate(
            new_state, scenario_info, self.scenario_engine.time_elapsed
        )
        equipment_status_html = self.equipment_visualizer.render_status_indicators(new_state)

        # 格式化回應（一次顯示回答 + 反問 + 故障警告）
        response = f"""[學習模式 - 理論問答]

{result['answer']}

---
[反問檢驗理解]
{follow_up}

（請回答以上問題，我會評估你的理解程度）"""

        # 加入故障惡化提醒
        if update_info.get('new_alarms') or update_info2.get('new_alarms'):
            total_new_alarms = len(update_info.get('new_alarms', [])) + len(update_info2.get('new_alarms', []))
            response += f"""

⚠️ 注意：問答期間故障持續惡化，新增 {total_new_alarms} 個警報！"""

        # 加入對話歷史
        self.conversation_history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response}
        ])

        # 更新日誌
        action_log += f"\n[{timestamp}] [學習模式] 詢問理論: {user_input[:30]}... (期間經過約 50 秒，故障持續惡化)"

        return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

    def _extract_term_from_question(self, question: str) -> str:
        """
        從問題中提取術語名稱

        Args:
            question: 學員的問題

        Returns:
            術語名稱
        """
        # 常見的術語列表
        terms = [
            '熱膨脹', 'thermal expansion',
            '疊對', 'overlay', 'overlay shift',
            'CD', 'CD uniformity', '關鍵尺寸',
            '曝光劑量', 'dose',
            '對準', 'alignment',
            '真空', 'vacuum',
            '冷卻', 'cooling',
            '光阻', 'photoresist',
            '蝕刻', 'etching',
            '薄膜', 'film'
        ]

        question_lower = question.lower()
        for term in terms:
            if term.lower() in question_lower:
                return term

        # 如果沒找到，嘗試提取引號中的內容
        import re
        quoted = re.findall(r'[「」『』\"\'](.*?)[「」『』\"\']', question)
        if quoted:
            return quoted[0]

        # 預設返回問題的主要部分
        return question.replace('是什麼', '').replace('是甚麼', '').replace('什麼是', '').strip()

    def _evaluate_term_understanding(self, student_answer: str, term_name: str, correct_answer: str) -> Dict:
        """
        評估學員對術語的理解（使用自適應教學策略）

        Args:
            student_answer: 學員的回答
            term_name: 術語名稱
            correct_answer: 正確答案

        Returns:
            評估結果 {'score': int, 'feedback': str, 'teaching_mode': str, ...}
        """
        student_answer_lower = student_answer.lower().strip()

        # ===== 基礎關鍵概念檢查 =====
        key_concepts = {
            '熱膨脹': ['溫度', '體積', '膨脹', '熱', '尺寸', '變大', '增加', '金屬', '材料'],
            'thermal expansion': ['temperature', 'volume', 'expand', 'heat', 'size', 'increase'],
            '疊對': ['對準', '精度', '層', '偏移', '對齊', '重疊'],
            'overlay': ['align', 'layer', 'accuracy', 'shift', 'precision'],
            'CD': ['線寬', '尺寸', '寬度', 'critical', 'dimension', '關鍵'],
            '曝光劑量': ['能量', '光', '劑量', '曝光', 'energy', '強度'],
            '真空': ['壓力', '抽氣', '泵浦', '密封', '洩漏'],
            '冷卻': ['溫度', '散熱', '流量', '循環', '控溫'],
        }

        # 獲取該術語的關鍵概念
        concepts = []
        for key, values in key_concepts.items():
            if key.lower() in term_name.lower():
                concepts = values
                break

        if not concepts:
            concepts = ['原理', '影響', '應用', '現象', '作用']

        # 計算匹配概念數
        matched_concepts = sum(1 for concept in concepts if concept.lower() in student_answer_lower)
        total_concepts = len(concepts)

        # 計算基礎得分（0-10）
        base_score = min(10, int((matched_concepts / total_concepts) * 8))

        # 回答長度品質調整
        if len(student_answer) < 10:
            base_score = max(0, base_score - 3)
        elif len(student_answer) < 30:
            base_score = max(0, base_score - 1)
        elif len(student_answer) > 100:
            base_score = min(10, base_score + 1)  # 詳細回答加分

        # 誠實回答加分
        if '不確定' in student_answer or '不知道' in student_answer or '不太清楚' in student_answer:
            base_score = max(base_score, 2)

        # ===== 使用自適應教學策略（如果可用）=====
        teaching_mode = 'standard'
        suggested_actions = []
        weak_topics = []

        if self.adaptive_strategy:
            # 決定理解程度
            if base_score >= 8:
                understanding_level = 'excellent'
            elif base_score >= 6:
                understanding_level = 'good'
            elif base_score >= 4:
                understanding_level = 'fair'
            else:
                understanding_level = 'poor'

            # 呼叫自適應策略進行評估
            adaptive_result = self.adaptive_strategy.evaluate_and_adapt(
                question=f"什麼是{term_name}？",
                system_answer=correct_answer,
                trainee_answer=student_answer,
                score=float(base_score),
                understanding_level=understanding_level
            )

            teaching_mode = adaptive_result.get('teaching_mode', 'standard')
            suggested_actions = adaptive_result.get('suggested_actions', [])
            weak_topics = adaptive_result.get('weak_topics', [])

        # ===== 根據教學模式生成自適應回饋 =====
        if teaching_mode == 'challenge':
            if base_score >= 8:
                feedback = f"✅ 優秀！你對「{term_name}」的理解非常深入！\n"
                feedback += f"作為進階挑戰，你能舉例說明這在實際製程中如何影響良率嗎？"
            else:
                feedback = f"👍 不錯的嘗試！讓我補充一些進階概念。"

        elif teaching_mode == 'scaffolding':
            feedback = f"📝 [鷹架引導]\n\n"
            if base_score >= 5:
                feedback += f"你對「{term_name}」有基本認識，讓我們一步步深入：\n"
            else:
                feedback += f"讓我們分解「{term_name}」這個概念：\n"
            feedback += f"1️⃣ 首先理解基本定義\n"
            feedback += f"2️⃣ 然後思考在半導體製程的影響\n"
            feedback += f"3️⃣ 最後連結到故障診斷的應用"

        elif teaching_mode == 'remedial':
            feedback = f"💡 [基礎鞏固] 沒關係，這個概念需要時間理解。\n\n"
            feedback += f"「{term_name}」是半導體製程的重要基礎，讓我用簡單的方式說明。"

        else:  # standard
            if base_score >= 8:
                feedback = f"✅ 非常好！你對「{term_name}」的理解相當正確！\n"
                feedback += f"你提到了關鍵概念，這是新人少見的理解深度。"
            elif base_score >= 5:
                feedback = f"👍 不錯！你對「{term_name}」有基本的認識。\n"
                feedback += f"讓我補充一些你可能遺漏的部分。"
            elif base_score >= 3:
                feedback = f"🤔 你的理解方向大致正確，但還有些關鍵點沒抓到。\n"
                feedback += f"讓我來詳細解釋「{term_name}」。"
            else:
                feedback = f"💡 看來你對「{term_name}」還不太熟悉，沒關係！\n"
                feedback += f"這是一個重要的概念，讓我來詳細說明。"

        # 添加建議行動（如果有）
        if suggested_actions and len(suggested_actions) > 0:
            feedback += f"\n\n📌 學習建議：{suggested_actions[0]}"

        return {
            'score': base_score,
            'feedback': feedback,
            'matched_concepts': matched_concepts,
            'total_concepts': total_concepts,
            'teaching_mode': teaching_mode,
            'weak_topics': weak_topics
        }

    def _generate_follow_up_question(self, user_input: str, timestamp: str,
                                     equipment_html: str, dashboard_html: str,
                                     equipment_status_html: str,
                                     conversation_history: list,
                                     action_log: str) -> Tuple[str, str, str, str, list, str]:
        """
        用戶確認理解後，生成反問問題

        Returns:
            (user_input_cleared, equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log)
        """
        # 使用暫存的上下文生成反問
        ctx = self.pending_theory_context
        follow_up = self.qa_assistant.generate_follow_up(
            ctx['question'],
            ctx['answer'],
            ctx['scenario_context']
        )

        # 保存反問問題
        self.pending_follow_up = follow_up
        self.pending_theory_context = None  # 清除暫存

        # 格式化回應
        response = f"""[反問檢驗理解]

{follow_up}

（請回答以上問題，我會評估你的理解程度）"""

        # 加入對話歷史
        self.conversation_history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response}
        ])

        return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

    def _handle_closing_reflection(self, user_input: str, timestamp: str,
                                    equipment_html: str, dashboard_html: str,
                                    equipment_status_html: str,
                                    conversation_history: list,
                                    action_log: str) -> Tuple[str, str, str, str, list, str]:
        """
        處理故障結束後的反思問題回答，用 ProactiveMentor 評分後給最終結語。
        """
        followup_info = self.pending_follow_up
        self.pending_follow_up = None  # 清掉，不再攔截

        fault_type = followup_info.get('fault_type', '')
        question   = followup_info.get('question', '')

        _CLOSING_KEYWORDS = {
            # SOP_DEFINITIONS keys
            'stage_error':   ['overlay', '疊對', '良率', '短路', '斷路', '偏移', '精度', '對準', '製程'],
            'contamination': ['劑量', '曝光', '光阻', 'CD', '線寬', '圖案', '穿透率', '污染', '預防'],
            'lens_hotspot':  ['熱膨脹', '折射率', '溫度', '焦點', '解析度', '曝光', '品質'],
            'dose_drift':    ['劑量', '光阻', '曝光量', '閾值', '線寬', 'CD', '良率'],
            'focus_drift':   ['焦距', '解析度', '製程視窗', '焦點', 'DOF', '對焦', '景深'],
        }
        _CLOSING_EXPL = {
            'stage_error':   'Overlay 是核心影響：上下層對不準→金屬層短路或 via 斷路→良率下降。DUV 要求 <3~5nm。',
            'contamination': '光強不足→劑量不夠→光阻反應不完全→CD偏大→圖案不清晰→良率受損。預防：定期清潔保養。',
            'lens_hotspot':  '溫升→熱膨脹+折射率改變→焦點漂移+對準偏移→解析度下降→製程良率受損。',
            'dose_drift':    '劑量偏高→光阻過度曝光→線寬縮小；劑量偏低→圖案不清晰→CD超規→良率下降。',
            'focus_drift':   '焦距漂移超出景深(DOF)→解析度下降→製程視窗縮窄→圖案邊緣模糊→良率受損。',
        }
        keywords = _CLOSING_KEYWORDS.get(fault_type, ['原因', '影響', '系統', '處理'])
        explanation = _CLOSING_EXPL.get(fault_type, '系統性排查：症狀→根因→處置。')
        score = self._quick_score(user_input, keywords)

        # 用 ProactiveMentor LLM 生成個人化回饋
        if self.proactive_mentor:
            tmp_followup = {
                'question': question,
                'term_name': fault_type,
                'answer_keywords': keywords,
                'correct_explanation': explanation,
                'socratic_followup': {}
            }
            feedback = self.proactive_mentor._generate_followup_feedback(
                score=score,
                followup=tmp_followup,
                user_answer=user_input
            )
        else:
            if score >= 7:
                feedback = "分析得很好！這次訓練到此結束，你對這個故障的理解相當紮實。"
            elif score >= 4:
                feedback = f"方向對了。補充一下：{explanation}\n\n記住核心影響鏈，下次更順手。"
            else:
                feedback = f"沒關係，這次先把流程走過一遍。核心概念：{explanation}\n\n繼續努力！"

        action_log += f"\n[{timestamp}] [反思評估] 情境結束"
        self.session_active = False  # 正式結束情境，不再接受操作輸入
        self.conversation_history.extend([
            {"role": "user",      "content": user_input},
            {"role": "assistant", "content": feedback},
            {"role": "sys_status", "content": "✅ 本次訓練情境結束。"},
        ])
        return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

    def _quick_score(self, answer: str, keywords: list) -> int:
        """快速關鍵字評分（0-10）"""
        answer_lower = answer.lower()
        matched = sum(1 for kw in keywords if kw.lower() in answer_lower)
        if matched == 0:
            return 1 if len(answer) > 5 else 0
        return min(10, 4 + int((matched / len(keywords)) * 7)) if keywords else 5

    def _handle_proactive_followup_answer(self, user_input: str, timestamp: str,
                                          equipment_html: str, dashboard_html: str,
                                          equipment_status_html: str,
                                          conversation_history: list,
                                          action_log: str) -> Tuple[str, str, str, str, list, str]:
        """
        處理主動告警反問的回答，使用 proactive_mentor 評估並自適應難度。
        """
        try:
            result = self.proactive_mentor.evaluate_followup_answer(user_input)
        except Exception as e:
            print(f"[Error] evaluate_followup_answer 失敗: {e}")
            conversation_history.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": "好，我們繼續處理故障吧。"}
            ])
            return "", equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log
        if not result:
            conversation_history.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": "好，繼續處理故障吧。"}
            ])
            return "", equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log

        score = result['score']
        feedback = result['feedback']
        difficulty = result['difficulty']

        # 將難度同步給 AI 學長的 LLM prompt
        mode_map = {'challenge': 'challenge', 'standard': 'standard', 'easy': 'scaffolding'}
        if self.use_ai_mentor and self.ai_mentor:
            self.ai_mentor.set_teaching_mode(mode_map.get(difficulty, 'standard'))

        # 難度標示（口語化）
        difficulty_hint = {
            'challenge': '（你理解得不錯，下次會問得更深一點）',
            'standard': '',
            'easy': '（沒關係，下次問簡單一點的）'
        }.get(difficulty, '')

        full_response = feedback
        if difficulty_hint:
            full_response += f"\n\n{difficulty_hint}"

        action_log += f"\n[{timestamp}] [反問評估] 得分: {score}/10 | 難度調整為: {difficulty}"

        conversation_history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": full_response}
        ])
        return "", equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log

    def _handle_follow_up_answer(self, user_input: str, timestamp: str,
                                 equipment_html: str, dashboard_html: str,
                                 equipment_status_html: str,
                                 conversation_history: list,
                                 action_log: str) -> Tuple[str, str, str, str, list, str]:
        """
        處理反問問題的回答

        Returns:
            (user_input_cleared, equipment_html, dashboard_html, equipment_status_html, conversation_history, action_log)
        """
        # 評估回答
        evaluation = self.qa_assistant.evaluate_response(
            self.pending_follow_up,
            user_input
        )

        # 格式化評估結果
        feedback_emoji = {
            'excellent': '🌟',
            'good': '👍',
            'fair': '💪',
            'poor': '📚'
        }

        emoji = feedback_emoji.get(evaluation['understanding_level'], '')

        response = f"""[評估結果] {emoji}

分數：{evaluation['score']:.1f}/10
{evaluation['feedback']}"""

        # 加入建議回答（如果有的話）
        if 'suggested_answer' in evaluation and evaluation['suggested_answer']:
            response += f"""

---
[建議回答參考]
{evaluation['suggested_answer']}"""

        response += """

---
你現在可以：
1. 繼續詢問理論問題
2. 返回故障診斷

（直接輸入診斷指令即可返回診斷模式）"""

        # 根據評估結果同步自適應模式給 AI 學長
        ul = evaluation.get('understanding_level', 'fair')
        ul_to_mode = {
            'excellent': 'challenge',
            'good':      'challenge',
            'fair':      'standard',
            'poor':      'scaffolding',
            'very_poor': 'remedial'
        }
        if self.use_ai_mentor and self.ai_mentor:
            self.ai_mentor.set_teaching_mode(ul_to_mode.get(ul, 'standard'))

        # 清除待回答問題
        self.pending_follow_up = None
        self.training_mode = "diagnostic"

        # 加入對話歷史
        self.conversation_history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response}
        ])

        # 更新日誌
        action_log += f"\n[{timestamp}] [學習] 理解評分: {evaluation['score']:.1f}/10"

        return "", equipment_html, dashboard_html, equipment_status_html, self.conversation_history, action_log

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
        """生成完成訊息（含反思問題）"""
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

        # ===== 新增：場景後反思問題 =====
        if self.qa_assistant:
            scenario_summary = {
                'fault_type': scenario_info.get('fault_type', '未知'),
                'actions_taken': f"{len(self.action_history)} 個動作",
                'time_taken': self.scenario_engine.time_elapsed,
                'mistakes': len([a for a in self.action_history if not a.get('success', True)])
            }

            reflection_q = self.qa_assistant.generate_scenario_reflection(scenario_summary)

            message += "\n\n" + "="*40
            message += "\n[反思時間]"
            message += f"\n\n{reflection_q}"
            message += "\n\n（請回答以上反思問題，鞏固所學知識）"

            # 保存反思問題
            self.pending_follow_up = reflection_q
            self.training_mode = "reflection"
            self.scenario_completed = True

            # 獲取理論知識分數
            qa_stats = self.qa_assistant.get_stats()
            if qa_stats['theory_questions'] > 0:
                message += f"\n\n[學習統計]"
                message += f"\n理論問題：{qa_stats['theory_questions']} 個"
                message += f"\n知識評分：{qa_stats['knowledge_score']:.1f}/10"

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

            # 添加演進訊息（系統狀態 / AI 評論分開儲存）
            progression_msg = progression_info["message"]

            # 系統狀態單獨儲存（前端顯示在狀態視窗）
            self.conversation_history.append({
                "role": "sys_status",
                "content": progression_msg
            })

            # AI 學長階段轉換評論單獨儲存（前端顯示在對話視窗）
            if self.use_ai_mentor:
                mentor_comment = self.ai_mentor.provide_stage_transition_comment(
                    self.scenario_engine.get_scenario_info(),
                    progression_info.get("new_stage", 0),
                    progression_info.get("symptoms", [])
                )
                if mentor_comment:
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": mentor_comment
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

    # GLB 3D 模型（base64 嵌入，無需 file serving，無 CORS 問題）
    import base64, html as _html
    static_dir = Path(__file__).parent.parent / "static"
    glb_src = static_dir / "asml_duv.glb"
    glb_exists = glb_src.exists()

    viewer_html = None
    if glb_exists:
        with open(str(glb_src), "rb") as _f:
            _glb_b64 = base64.b64encode(_f.read()).decode("ascii")
        print(f"[OK] GLB 已讀取並編碼 ({len(_glb_b64)//1024} KB base64)")
        _srcdoc = (
            "<!DOCTYPE html><html><head>"
            "<meta charset=\"utf-8\">"
            "<script type=\"module\" src=\"https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js\"></script>"
            "<style>body{margin:0;background:#1a1a2e;overflow:hidden;}"
            "model-viewer{width:100%;height:460px;--progress-bar-color:#4a9eff;}</style>"
            "</head><body>"
            f"<model-viewer src=\"data:model/gltf-binary;base64,{_glb_b64}\""
            " alt=\"ASML TWINSCAN NXT:870\" auto-rotate camera-controls"
            " shadow-intensity=\"1\" environment-image=\"neutral\" exposure=\"0.8\">"
            "</model-viewer></body></html>"
        )
        viewer_html = (
            f'<iframe srcdoc="{_html.escape(_srcdoc)}"'
            ' style="width:100%;height:460px;border:none;border-radius:8px;"'
            ' sandbox="allow-scripts"></iframe>'
        )
    else:
        print("[WARN] asml_duv.glb 未找到")

    with gr.Blocks(title="Simulation Training System") as demo:

        gr.Markdown("""
        # 半導體設備故障處理模擬訓練系統
        ## Free-Form Natural Language Simulation

        這是真實情境模擬，不是選擇題！用自然語言輸入操作，AI 學長引導思考。
        """)

        # 控制區
        with gr.Row():
            difficulty_dropdown = gr.Dropdown(
                choices=["easy", "medium", "hard"],
                value="medium",
                label="難度"
            )
            start_btn = gr.Button("開始新情境", variant="primary", size="lg")

        # 上半部：3D 模型（左）+ 參數儀表 + 設備狀態（右）
        with gr.Row():
            with gr.Column(scale=3):
                if viewer_html:
                    gr.HTML(value=viewer_html, label="ASML TWINSCAN NXT:870")
                else:
                    gr.Markdown("⚠️ **3D 模型未找到**，請確認 `static/asml_duv.glb` 存在。")

            with gr.Column(scale=2):
                dashboard_display = gr.HTML(label="參數監控")
                equipment_status_display = gr.HTML(label="設備檢查")

        # 內部用的設備圖（隱藏，供狀態機使用）
        equipment_display = gr.HTML(visible=False)

        # 系統訊息區
        system_messages = gr.Chatbot(
            label="對話歷史",
            height=400,
            show_label=True
        )

        # 輸入區
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
        timer = gr.Timer(value=1, active=False)  # 每1秒觸發一次（逐秒更新）

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
