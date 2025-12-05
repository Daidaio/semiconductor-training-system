# -*- coding: utf-8 -*-
"""
統一訓練介面 (Unified Training Interface)
整合理論學習和實作訓練的完整訓練系統
"""

import gradio as gr
import sys
from pathlib import Path
from typing import Tuple, Optional

# 添加父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from integration.training_coordinator import TrainingCoordinator, TrainingStage
from integration.progress_tracker import ProgressTracker, InteractionType
from integration.smart_recommender import SmartRecommender
from integration.evaluation_system import EvaluationSystem
from core.scenario_engine import ScenarioEngine
from core.natural_language_controller import NaturalLanguageController, ActionExecutor
from core.digital_twin import LithographyDigitalTwin


class UnifiedTrainingSystem:
    """統一訓練系統 - 整合階段1和階段2"""

    def __init__(self, secom_data_path: str):
        """
        初始化統一訓練系統

        Args:
            secom_data_path: SECOM 資料集路徑
        """
        print("[Init] Unified Training System...")

        # SECOM 資料路徑
        self.secom_data_path = secom_data_path

        # 當前學員
        self.current_student_id = None
        self.coordinator = None
        self.tracker = None

        # 新增整合模組
        self.recommender = SmartRecommender()
        self.evaluator = EvaluationSystem()

        # 階段 2 模組（實作訓練）
        self.scenario_engine = None
        self.digital_twin = None
        self.nlu_controller = None
        self.action_executor = None

        # 階段 2 狀態
        self.stage2_active = False
        self.current_scenario_data = None  # 當前場景資料（用於評分）

        print("[OK] System ready!")

    def login_student(self, student_id: str, student_name: str) -> Tuple[str, str, str]:
        """
        學員登入

        Returns:
            (welcome_message, progress_html, stage_status)
        """
        if not student_id.strip():
            return "請輸入學員 ID", "", ""

        self.current_student_id = student_id

        # 初始化協調器和追蹤器
        self.coordinator = TrainingCoordinator(student_id)
        self.tracker = ProgressTracker(student_id)

        # 生成歡迎訊息
        progress = self.coordinator.get_overall_progress()

        welcome = f"""
# 歡迎，{student_name or student_id}！

你好！歡迎來到半導體設備故障處理訓練系統。

## 當前訓練狀態

- **當前階段**: {self._get_stage_name(progress['current_stage'])}
- **整體完成度**: {progress['overall_completion']}%
- **下一步**: {progress['next_step']}

## 訓練路徑

```
階段 1: 理論知識學習 → {'✅ 已完成' if progress['theory_completed'] else f"⏳ 進行中 ({progress['theory_score']}分)"}
    ↓
階段 2: 虛擬實作訓練 → {'✅ 已完成' if progress['practice_completed'] else ('🔒 未解鎖' if not progress['can_enter_practice'] else f"⏳ 進行中 ({progress['practice_score']}分)")}
    ↓
階段 3: 真機實習 → {'✅ 可進入' if progress['practice_completed'] else '🔒 未解鎖'}
```

請選擇對應的 Tab 開始訓練！
"""

        # 生成進度 HTML
        progress_html = self._generate_progress_html(progress)

        # 生成階段狀態
        stage_status = self._generate_stage_status_html(progress)

        return welcome, progress_html, stage_status

    def _get_stage_name(self, stage: str) -> str:
        """獲取階段名稱"""
        names = {
            TrainingStage.THEORY: "階段 1：理論知識學習",
            TrainingStage.PRACTICE: "階段 2：虛擬實作訓練",
            TrainingStage.COMPLETED: "已完成所有訓練"
        }
        return names.get(stage, stage)

    def _generate_progress_html(self, progress: dict) -> str:
        """生成進度條 HTML"""
        completion = progress['overall_completion']

        html = f"""
        <div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 10px; color: white;">
            <h3 style="margin-top: 0;">整體訓練進度</h3>
            <div style="background: rgba(255,255,255,0.3); height: 30px; border-radius: 15px;
                       margin: 10px 0; overflow: hidden;">
                <div style="background: #4caf50; height: 100%; width: {completion}%;
                           transition: width 0.5s ease; display: flex; align-items: center;
                           justify-content: center; font-weight: bold;">
                    {completion}%
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                <span>理論: {progress['theory_score']}分</span>
                <span>實作: {progress['practice_score']}分</span>
                <span>{'✅ 可進入真機實習' if progress['practice_completed'] else '繼續訓練...'}</span>
            </div>
        </div>
        """
        return html

    def _generate_stage_status_html(self, progress: dict) -> str:
        """生成階段狀態 HTML"""
        theory_status = self.coordinator.get_stage_status(TrainingStage.THEORY)
        practice_status = self.coordinator.get_stage_status(TrainingStage.PRACTICE)

        html = f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
            <!-- 階段 1 -->
            <div style="padding: 15px; background: {'#e8f5e9' if theory_status['completed'] else '#fff3e0'};
                       border-radius: 10px; border-left: 4px solid {'#4caf50' if theory_status['completed'] else '#ff9800'};">
                <h4 style="margin-top: 0;">📚 {theory_status['name']}</h4>
                <p><strong>狀態:</strong> {theory_status['status']}</p>
                <p><strong>分數:</strong> {theory_status['score']} / {theory_status['pass_score']}</p>
                <p><strong>進度:</strong> {'✅ 已完成' if theory_status['completed'] else '⏳ 進行中'}</p>
            </div>

            <!-- 階段 2 -->
            <div style="padding: 15px; background: {'#e8f5e9' if practice_status['completed'] else ('#ffebee' if practice_status['locked'] else '#e3f2fd')};
                       border-radius: 10px; border-left: 4px solid {'#4caf50' if practice_status['completed'] else ('#f44336' if practice_status['locked'] else '#2196f3')};">
                <h4 style="margin-top: 0;">🛠️ {practice_status['name']}</h4>
                <p><strong>狀態:</strong> {practice_status['status']}</p>
                <p><strong>分數:</strong> {practice_status['score']} / {practice_status['pass_score']}</p>
                <p><strong>進度:</strong> {'✅ 已完成' if practice_status['completed'] else ('🔒 已鎖定' if practice_status['locked'] else '⏳ 進行中')}</p>
                {f"<p style='color: #f44336;'><strong>解鎖條件:</strong> {practice_status['lock_reason']}</p>" if practice_status['locked'] else ""}
            </div>
        </div>
        """
        return html

    # ===== 階段 1：理論學習 (Mock 實作) =====

    def ask_theory_question(self, question: str, chat_history: list) -> Tuple[list, str]:
        """
        理論問答（簡化版）

        Args:
            question: 學員問題
            chat_history: 對話歷史

        Returns:
            (updated_chat_history, input_cleared)
        """
        if not question.strip():
            return chat_history, ""

        if not self.current_student_id:
            # Gradio Chatbot 格式：[{"role": "user"/"assistant", "content": "..."}]
            if chat_history is None:
                chat_history = []
            chat_history.append({"role": "assistant", "content": "請先登入"})
            return chat_history, ""

        # Mock 回答（未來接入真實 RAG）
        mock_answers = {
            "cvd": "CVD（Chemical Vapor Deposition，化學氣相沉積）是一種重要的薄膜沉積技術，通過化學反應在晶圓表面形成薄膜。\n\n主要類型包括：\n- PECVD（電漿增強CVD）\n- LPCVD（低壓CVD）\n- APCVD（常壓CVD）",
            "真空": "真空系統是半導體製程的關鍵設備，主要功能包括：\n\n1. 提供無污染的製程環境\n2. 控制反應氣體的流動\n3. 確保薄膜品質\n\n真空度通常需要達到 10⁻⁶ Torr 以下。",
            "溫度": "溫度控制對製程品質至關重要，影響因素包括：\n\n1. 反應速率\n2. 薄膜品質\n3. 設備壽命\n\n通常需要精確控制在 ±0.5°C 以內。",
        }

        # 簡單匹配
        answer = "這是一個好問題！\n\n"
        found_answer = False

        for keyword, mock_answer in mock_answers.items():
            if keyword in question.lower():
                answer += mock_answer
                found_answer = True
                break

        if not found_answer:
            answer += "關於這個問題，我建議你查閱相關的製程手冊和 SOP 文件。\n\n你也可以詢問更具體的問題，例如：\n- CVD 是什麼？\n- 真空系統如何運作？\n- 溫度控制的重要性？"

        # 記錄互動
        if self.tracker:
            self.tracker.log_interaction(
                InteractionType.THEORY_QUESTION,
                {"question": question, "answer": answer},
                success=found_answer
            )

        # 更新對話（Gradio Chatbot 格式）
        if chat_history is None:
            chat_history = []

        chat_history.append({"role": "user", "content": question})
        chat_history.append({"role": "assistant", "content": answer + "\n\n💡 你理解了嗎？還有什麼想問的？"})

        return chat_history, ""

    def take_theory_test(self) -> Tuple[str, str, str]:
        """
        參加理論測驗（使用 EvaluationSystem）

        Returns:
            (result_message, progress_html, stage_status)
        """
        if not self.current_student_id:
            return "請先登入", "", ""

        # Mock 測驗題目（未來接入真實題庫）
        import random

        mock_test_results = []
        topics = ["CVD", "真空系統", "冷卻系統", "對準系統", "溫度控制", "壓力控制", "光學系統", "化學反應", "安全規範", "SOP"]
        difficulties = ["easy", "medium", "hard"]

        for i in range(10):
            # 隨機正確率約 70-80%
            is_correct = random.random() > 0.25
            mock_test_results.append({
                "question": f"問題 {i+1}",
                "is_correct": is_correct,
                "topic": random.choice(topics),
                "difficulty": random.choice(difficulties)
            })

        # 使用 EvaluationSystem 評分
        theory_eval = self.evaluator.evaluate_theory_test(mock_test_results)
        score = theory_eval['score']

        # 更新分數
        result_message = self.coordinator.update_theory_score(score)

        # 記錄測驗
        self.tracker.log_interaction(
            InteractionType.THEORY_TEST,
            {
                "test_type": "理論測驗",
                "questions": 10,
                "correct": theory_eval['correct_count'],
                "evaluation": theory_eval
            },
            success=score >= 70,
            score=score
        )

        # 生成詳細結果
        result_details = f"""## 📊 測驗結果

{result_message}

### 詳細分析
- **總分**: {theory_eval['score']} 分
- **等級**: {theory_eval['grade']}
- **正確率**: {theory_eval['accuracy']}%
- **答對題數**: {theory_eval['correct_count']} / {theory_eval['total_count']}

### 表現分析
"""

        # 優勢主題
        if theory_eval['strengths']:
            result_details += f"\n**✅ 優勢主題**: {', '.join(theory_eval['strengths'])}"

        # 弱點主題
        if theory_eval['weaknesses']:
            result_details += f"\n**⚠️ 需加強**: {', '.join(theory_eval['weaknesses'])}"

        result_details += f"\n\n{self._get_test_feedback(score)}"

        # 更新進度
        progress = self.coordinator.get_overall_progress()
        progress_html = self._generate_progress_html(progress)
        stage_status = self._generate_stage_status_html(progress)

        return result_details, progress_html, stage_status

    def _get_test_feedback(self, score: float) -> str:
        """生成測驗反饋"""
        if score >= 90:
            return "🎉 優秀！你對理論知識掌握得非常好！"
        elif score >= 80:
            return "👍 很好！理論基礎紮實。"
        elif score >= 70:
            return "✅ 通過！可以進入實作訓練了。建議先複習一下錯誤的部分。"
        else:
            return "❌ 未通過。建議多花時間學習理論知識，然後再次測驗。"

    # ===== 階段 2：實作訓練 =====

    def start_practice_scenario(self, difficulty: str) -> Tuple[str, str, str, str, str]:
        """
        開始實作訓練情境

        Returns:
            (equipment_html, dashboard_html, system_message, action_log, practice_status)
        """
        if not self.current_student_id:
            return "", "", "請先登入", "", ""

        # 檢查是否可以進入
        can_enter, message = self.coordinator.can_enter_practice()

        if not can_enter:
            return "", "", f"🔒 {message}", "", "locked"

        # 初始化階段 2 模組（如果尚未初始化）
        if not self.stage2_active:
            self.scenario_engine = ScenarioEngine(self.secom_data_path)
            self.digital_twin = LithographyDigitalTwin(self.secom_data_path)
            self.nlu_controller = NaturalLanguageController()
            self.action_executor = ActionExecutor(self.digital_twin)
            self.stage2_active = True

        # 初始化情境
        scenario_info = self.scenario_engine.initialize_scenario(difficulty=difficulty)

        # 生成設備圖和儀表板
        equipment_html = self._generate_equipment_diagram(scenario_info["initial_state"])
        dashboard_html = self._generate_dashboard(scenario_info["initial_state"])

        # 生成警報訊息
        system_message = f"""
{scenario_info['alarm_message']}

==========================================

你現在在虛擬環境中，請用自然語言輸入你的操作！

範例：
- 「檢查冷卻水流量」
- 「調整溫度到 23 度」
- 「詢問專家為什麼溫度上升」
- 「停機更換過濾網」

開始你的操作...
"""

        action_log = f"[{scenario_info['scenario_name']}] 情境已開始\n"

        # 記錄階段切換
        self.tracker.log_interaction(
            InteractionType.STAGE_SWITCH,
            {"from": TrainingStage.THEORY, "to": TrainingStage.PRACTICE}
        )

        return equipment_html, dashboard_html, system_message, action_log, "active"

    def process_practice_input(self, user_input: str, equipment_html: str, dashboard_html: str,
                               system_message: str, action_log: str) -> Tuple[str, str, str, str, str]:
        """
        處理實作訓練的輸入

        Returns:
            (cleared_input, equipment_html, dashboard_html, system_message, action_log)
        """
        if not user_input.strip() or not self.stage2_active:
            return "", equipment_html, dashboard_html, system_message, action_log

        # 解析輸入
        parsed_input = self.nlu_controller.parse_input(user_input)

        # 執行動作
        current_state = self.scenario_engine.get_current_state()

        # 驗證
        is_valid, validation_msg = self.nlu_controller.validate_action(parsed_input, current_state)

        if not is_valid:
            system_message += f"\n\n[錯誤] {validation_msg}"
            return "", equipment_html, dashboard_html, system_message, action_log

        # 執行
        action_result = self.action_executor.execute(parsed_input, current_state)

        # 更新狀態
        self.scenario_engine.apply_action_effect(action_result)

        # 更新顯示
        new_state = self.scenario_engine.get_current_state()
        equipment_html = self._generate_equipment_diagram(new_state)
        dashboard_html = self._generate_dashboard(new_state)

        # 更新訊息
        system_message += f"\n\n{action_result['message']}"

        # 更新日誌
        action_log += f"\n[操作] {user_input}"

        # 記錄互動
        self.tracker.log_interaction(
            InteractionType.PRACTICE_OPERATION,
            {"operation": user_input, "result": action_result, "topic": parsed_input.get("category", "unknown")},
            success=action_result["success"]
        )

        # 智能推薦：檢查是否需要推薦
        recent_ops = self.tracker.get_interactions_by_type(InteractionType.PRACTICE_OPERATION)
        recent_failures = [op for op in recent_ops[-5:] if not op.get("success", False)]

        if self.recommender.should_trigger_recommendation(recent_failures, failure_threshold=3):
            # 獲取知識盲點
            knowledge_gaps = self.tracker.get_knowledge_gaps()

            # 生成推薦
            recommendations = self.recommender.recommend_topics(
                failed_operations=[{"operation": op["data"]["operation"], "topic": op["data"].get("topic", "unknown")} for op in recent_failures],
                knowledge_gaps=knowledge_gaps,
                max_recommendations=3
            )

            if recommendations:
                system_message += "\n\n" + "="*50 + "\n"
                system_message += "💡 **智能推薦系統**\n\n"
                system_message += "偵測到你在某些操作上遇到困難，建議複習以下主題：\n\n"

                for i, rec in enumerate(recommendations, 1):
                    system_message += f"{i}. {rec['recommendation']}\n"

                system_message += "\n你可以返回「理論學習」頁面複習這些主題。\n"
                system_message += "="*50

        return "", equipment_html, dashboard_html, system_message, action_log

    def _generate_equipment_diagram(self, state: dict) -> str:
        """生成設備示意圖（簡化版）"""
        lens_color = "#ff4444" if state.get("lens_temp", 23) > 25 else "#44ff44"
        cooling_color = "#ff4444" if state.get("cooling_flow", 5.0) < 4.0 else "#44ff44"

        html = f"""
        <div style="background: #1e3c72; padding: 20px; border-radius: 10px;">
            <h3 style="color: white; text-align: center;">曝光機設備狀態</h3>
            <svg width="100%" height="300" viewBox="0 0 400 300">
                <!-- 鏡頭 -->
                <rect x="150" y="20" width="100" height="60" fill="{lens_color}" stroke="#333" stroke-width="2" rx="5"/>
                <text x="200" y="55" text-anchor="middle" fill="white" font-size="14">鏡頭</text>

                <!-- 冷卻系統 -->
                <rect x="20" y="100" width="80" height="50" fill="{cooling_color}" stroke="#333" stroke-width="2" rx="5"/>
                <text x="60" y="130" text-anchor="middle" fill="white" font-size="12">冷卻</text>

                <!-- 腔體 -->
                <rect x="130" y="120" width="140" height="100" fill="#888" stroke="#333" stroke-width="3" rx="10"/>
                <text x="200" y="175" text-anchor="middle" fill="white" font-size="14">真空腔體</text>

                <!-- 晶圓 -->
                <ellipse cx="200" cy="250" rx="40" ry="15" fill="#666" stroke="#333" stroke-width="2"/>
                <text x="200" y="255" text-anchor="middle" fill="white" font-size="11">晶圓</text>
            </svg>
            <div style="text-align: center; color: white; margin-top: 10px;">
                <span style="color: #44ff44;">● 正常</span>
                <span style="margin-left: 20px; color: #ff4444;">● 異常</span>
            </div>
        </div>
        """
        return html

    def _generate_dashboard(self, state: dict) -> str:
        """生成參數儀表板（簡化版）"""
        def get_color(value, min_val, max_val, normal_min, normal_max):
            if normal_min <= value <= normal_max:
                return "#4caf50"
            elif min_val <= value <= max_val:
                return "#ff9800"
            else:
                return "#f44336"

        params = [
            {"name": "鏡頭溫度", "value": state.get("lens_temp", 23.0), "unit": "°C",
             "min": 20, "max": 30, "normal_min": 22, "normal_max": 24},
            {"name": "冷卻流量", "value": state.get("cooling_flow", 5.0), "unit": "L/min",
             "min": 0, "max": 10, "normal_min": 4.5, "normal_max": 5.5},
            {"name": "真空壓力", "value": state.get("vacuum_pressure", 1e-6), "unit": "Torr",
             "min": 0, "max": 1e-4, "normal_min": 5e-7, "normal_max": 2e-6, "scientific": True},
        ]

        html = """
        <div style="background: #f5f5f5; padding: 15px; border-radius: 10px;">
            <h3 style="text-align: center; margin-top: 0;">即時參數監控</h3>
        """

        for param in params:
            value = param["value"]
            color = get_color(value, param["min"], param["max"], param["normal_min"], param["normal_max"])
            percentage = (value - param["min"]) / (param["max"] - param["min"]) * 100 if not param.get("scientific") else 50

            value_display = f"{value:.2e}" if param.get("scientific") else f"{value:.2f}"

            html += f"""
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-weight: bold;">{param['name']}</span>
                    <span style="color: {color}; font-weight: bold;">{value_display} {param['unit']}</span>
                </div>
                <div style="background: #ddd; height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: {color}; height: 100%; width: {percentage}%;"></div>
                </div>
            </div>
            """

        html += "</div>"
        return html

    # ===== 學習報告 =====

    def generate_report(self) -> str:
        """生成增強版學習報告（整合評分系統）"""
        if not self.current_student_id:
            return "請先登入"

        # 獲取基本報告
        report = self.tracker.generate_learning_report()

        # 獲取訓練進度
        progress = self.coordinator.get_overall_progress()

        # 使用評分系統進行綜合評估
        overall_eval = self.evaluator.evaluate_overall(
            theory_score=progress['theory_score'],
            practice_score=progress['practice_score']
        )

        # 計算學習效率
        efficiency = self.evaluator.calculate_learning_efficiency(
            score=overall_eval['overall_score'],
            study_time_minutes=report['study_time_minutes'],
            interaction_count=report['statistics']['total_interactions']
        )

        # 生成改進建議
        suggestions = self.evaluator.generate_improvement_suggestions(overall_eval)

        # 構建增強版報告
        report_md = f"""
# 📋 學習報告

**學員 ID**: {report['student_id']}
**報告日期**: {report['report_date'][:10]}
**學習時間**: {report['study_time_minutes']} 分鐘 ({efficiency['study_time_hours']} 小時)

---

## 🎯 綜合評估

### 整體表現
- **綜合分數**: **{overall_eval['overall_score']}** 分
- **等級**: **{overall_eval['grade']}**
- **理論分數**: {overall_eval['theory_score']} 分 (權重 {int(overall_eval['theory_weight']*100)}%)
- **實作分數**: {overall_eval['practice_score']} 分 (權重 {int(overall_eval['practice_weight']*100)}%)
- **發展平衡性**: {'✅ 均衡發展' if overall_eval['is_balanced'] else '⚠️ 需平衡發展'}
- **可進入真機實習**: {'✅ 是' if overall_eval['ready_for_real_practice'] else '❌ 否'}

### 評語
"""
        for comment in overall_eval['comments']:
            report_md += f"- {comment}\n"

        report_md += f"""
---

## 📚 學習效率分析

- **效率評級**: **{efficiency['efficiency_rating']}**
- **效率分數**: {efficiency['efficiency_score']}
- **每小時得分**: {efficiency['score_per_hour']:.1f}
- **每次互動得分**: {efficiency['score_per_interaction']:.2f}

---

## 📊 詳細統計

### 理論學習
- **問題總數**: {report['statistics']['theory_questions_asked']}
- **答對題數**: {report['statistics']['theory_questions_correct']}
- **正確率**: {report['performance']['theory_accuracy']}%
- **測驗次數**: {report['statistics']['theory_tests_taken']}

### 實作訓練
- **操作總數**: {report['statistics']['practice_operations_count']}
- **成功操作**: {report['statistics']['practice_operations_success']}
- **成功率**: {report['performance']['practice_success_rate']}%
- **專家諮詢**: {report['statistics']['expert_consults']} 次

### 整體數據
- **總互動次數**: {report['statistics']['total_interactions']}
- **訓練完成度**: {progress['overall_completion']}%

---

## 💡 個性化改進建議

"""
        for i, suggestion in enumerate(suggestions, 1):
            report_md += f"{i}. {suggestion}\n"

        # 知識盲點分析
        if report['knowledge_gaps']:
            report_md += "\n---\n\n## ⚠️ 知識盲點分析\n\n"
            report_md += "以下主題需要特別加強：\n\n"

            for gap in report['knowledge_gaps'][:5]:  # 最多顯示5個
                report_md += f"- **{gap['topic']}**\n"
                report_md += f"  - 錯誤次數: {gap['error_count']} 次\n"
                report_md += f"  - 嘗試次數: {gap['total_attempts']} 次\n"
                report_md += f"  - 正確率: {gap['accuracy']}%\n\n"

            # 使用智能推薦器生成學習路徑
            recommendations = self.recommender.recommend_topics(
                knowledge_gaps=report['knowledge_gaps'],
                max_recommendations=5
            )

            if recommendations:
                report_md += "\n### 📌 建議複習順序\n\n"
                learning_path = self.recommender.generate_learning_path(recommendations)

                for i, step in enumerate(learning_path, 1):
                    time_est = step.get('estimated_time_minutes', 30)
                    report_md += f"{i}. **{step['topic']}** (預估 {time_est} 分鐘)\n"

                total_time = sum(step.get('estimated_time_minutes', 0) for step in learning_path)
                report_md += f"\n*預估總複習時間: {total_time} 分鐘 ({total_time/60:.1f} 小時)*\n"

        # 學習曲線
        if report['learning_curve']['theory_accuracy'] or report['learning_curve']['practice_success_rate']:
            report_md += "\n---\n\n## 📈 學習曲線趨勢\n\n"

            if report['learning_curve']['theory_accuracy']:
                latest_theory = report['learning_curve']['theory_accuracy'][-1] if report['learning_curve']['theory_accuracy'] else 0
                report_md += f"- **理論學習**: 最新正確率 {latest_theory}%\n"

            if report['learning_curve']['practice_success_rate']:
                latest_practice = report['learning_curve']['practice_success_rate'][-1] if report['learning_curve']['practice_success_rate'] else 0
                report_md += f"- **實作訓練**: 最新成功率 {latest_practice}%\n"

        report_md += "\n---\n\n*報告由系統自動生成*\n"

        return report_md


def create_unified_interface(secom_data_path: str):
    """建立統一訓練介面"""

    system = UnifiedTrainingSystem(secom_data_path)

    with gr.Blocks(title="Integrated Training System") as demo:

        gr.Markdown("""
        # 半導體設備故障處理訓練系統
        ## 理論 + 實作整合訓練平台

        本系統提供完整的三階段訓練路徑，從理論學習到實作演練，全方位培養故障處理能力。
        """)

        # ===== 學員登入區 =====
        with gr.Row():
            student_id_input = gr.Textbox(label="學員 ID", placeholder="請輸入學員 ID (例如：S001)")
            student_name_input = gr.Textbox(label="姓名（選填）", placeholder="張三")
            login_btn = gr.Button("登入", variant="primary")

        # ===== 進度顯示區 =====
        welcome_msg = gr.Markdown("請先登入以開始訓練")
        progress_display = gr.HTML()
        stage_status_display = gr.HTML()

        # ===== 主要訓練區（Tabs）=====
        with gr.Tabs() as tabs:

            # Tab 1: 階段 1 - 理論學習
            with gr.Tab("📚 階段 1：理論知識學習") as theory_tab:
                gr.Markdown("""
                ## 理論知識學習

                在這個階段，你將：
                - 與理論 BOT 對話，學習製程知識
                - 參加知識測驗
                - 達到 70 分以上才能進入實作訓練

                **提示**: 可以詢問任何關於半導體製程、設備、SOP 的問題！
                """)

                theory_chatbot = gr.Chatbot(label="理論 BOT", height=400)

                with gr.Row():
                    theory_input = gr.Textbox(
                        label="",
                        placeholder="輸入你的問題... (例如：什麼是CVD？)",
                        scale=4
                    )
                    theory_send_btn = gr.Button("發送", scale=1)

                theory_test_btn = gr.Button("🎯 參加理論測驗", variant="primary", size="lg")
                theory_result = gr.Markdown()

            # Tab 2: 階段 2 - 實作訓練
            with gr.Tab("🛠️ 階段 2：虛擬實作訓練") as practice_tab:
                gr.Markdown("""
                ## 虛擬實作訓練

                在這個階段，你將：
                - 面對真實的設備故障情境
                - 用自然語言輸入操作指令
                - AI 專家會引導你思考（不直接給答案）
                - 達到 80 分以上完成訓練

                **注意**: 需要先通過階段 1 的理論測驗才能解鎖！
                """)

                practice_status = gr.State("locked")

                with gr.Row():
                    difficulty_choice = gr.Dropdown(
                        choices=["easy", "medium", "hard"],
                        value="medium",
                        label="難度"
                    )
                    start_practice_btn = gr.Button("開始新情境", variant="primary")

                with gr.Row():
                    equipment_display = gr.HTML(label="設備狀態")
                    dashboard_display = gr.HTML(label="參數監控")

                system_messages = gr.Textbox(label="系統訊息", lines=10, interactive=False)

                with gr.Row():
                    practice_input = gr.Textbox(
                        label="",
                        placeholder="輸入你的操作... (例如：檢查冷卻水流量)",
                        scale=4
                    )
                    practice_send_btn = gr.Button("執行", variant="primary", scale=1)

                action_log = gr.Textbox(label="操作日誌", lines=5, interactive=False)

            # Tab 3: 學習報告
            with gr.Tab("📈 學習報告") as report_tab:
                gr.Markdown("""
                ## 學習報告

                查看你的學習進度、表現分析和改進建議。
                """)

                generate_report_btn = gr.Button("生成最新報告", variant="primary")
                report_display = gr.Markdown()

        # ===== 事件綁定 =====

        # 登入
        login_btn.click(
            fn=system.login_student,
            inputs=[student_id_input, student_name_input],
            outputs=[welcome_msg, progress_display, stage_status_display]
        )

        # 理論問答
        theory_send_btn.click(
            fn=system.ask_theory_question,
            inputs=[theory_input, theory_chatbot],
            outputs=[theory_chatbot, theory_input]
        )

        theory_input.submit(
            fn=system.ask_theory_question,
            inputs=[theory_input, theory_chatbot],
            outputs=[theory_chatbot, theory_input]
        )

        # 理論測驗
        theory_test_btn.click(
            fn=system.take_theory_test,
            inputs=[],
            outputs=[theory_result, progress_display, stage_status_display]
        )

        # 開始實作訓練
        start_practice_btn.click(
            fn=system.start_practice_scenario,
            inputs=[difficulty_choice],
            outputs=[equipment_display, dashboard_display, system_messages, action_log, practice_status]
        )

        # 實作操作
        practice_send_btn.click(
            fn=system.process_practice_input,
            inputs=[practice_input, equipment_display, dashboard_display, system_messages, action_log],
            outputs=[practice_input, equipment_display, dashboard_display, system_messages, action_log]
        )

        practice_input.submit(
            fn=system.process_practice_input,
            inputs=[practice_input, equipment_display, dashboard_display, system_messages, action_log],
            outputs=[practice_input, equipment_display, dashboard_display, system_messages, action_log]
        )

        # 生成報告
        generate_report_btn.click(
            fn=system.generate_report,
            inputs=[],
            outputs=[report_display]
        )

    return demo
