"""
Gradio 訓練介面
提供完整的互動式訓練體驗
"""

import gradio as gr
import sys
import os
from pathlib import Path
from typing import Dict, List

# 添加父目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent.parent))

from core.digital_twin import LithographyDigitalTwin
from core.a2a_coordinator import A2ACoordinator
from core.scenario_generator import ScenarioGenerator
from evaluation.scoring_system import ScoringSystem
from datetime import datetime
import pandas as pd
import json


class TrainingInterface:
    """訓練介面主類別"""

    def __init__(self, secom_data_path: str):
        """
        初始化訓練介面

        Args:
            secom_data_path: SECOM 資料集路徑
        """
        print("[Initializing] Training system...")

        # 初始化核心組件
        self.digital_twin = LithographyDigitalTwin(secom_data_path)
        self.a2a_coordinator = A2ACoordinator()
        self.scenario_generator = ScenarioGenerator(secom_data_path)
        self.scoring_system = ScoringSystem()

        # 訓練狀態
        self.current_scenario = None
        self.current_student_id = None
        self.session_start_time = None
        self.student_actions = []
        self.current_step = 0

        print("[OK] Training system initialized!\n")

    def start_new_scenario(
        self,
        student_id: str,
        difficulty: str,
        student_level: str
    ):
        """開始新情境"""
        if not student_id:
            return "❌ 請輸入學員 ID", "", "", ""

        self.current_student_id = student_id
        self.student_actions = []
        self.current_step = 0
        self.session_start_time = datetime.now()

        # 生成情境
        self.current_scenario = self.scenario_generator.generate_scenario(
            difficulty=difficulty if difficulty != "隨機" else None,
            student_level=student_level
        )

        # 注入故障到數位孿生
        self.digital_twin.inject_fault(self.current_scenario["type"])

        # 準備顯示資訊
        scenario_info = f"""
## 📋 訓練情境資訊

**情境 ID:** {self.current_scenario['scenario_id']}
**情境名稱:** {self.current_scenario['template']['name']}
**難度等級:** {self.current_scenario['difficulty']}
**時間限制:** {self.current_scenario['time_limit']} 分鐘

### 情境描述
{self.current_scenario['template']['story']}

### 學習目標
"""
        for obj in self.current_scenario['template']['learning_objectives']:
            scenario_info += f"- {obj}\n"

        # 設備狀態摘要
        summary = self.digital_twin.get_all_sensors_summary()
        equipment_status = f"""
## 🔧 設備狀態

- **總感測器數:** {summary['total_sensors']}
- **正常:** {summary['normal']} 個
- **警告:** {summary['warning']} 個
- **臨界:** {summary['critical']} 個
- **故障狀態:** {'是' if summary['is_fault'] else '否'}

⚠️ **請開始診斷！**
"""

        return (
            scenario_info,
            equipment_status,
            "✅ 情境已載入，請開始診斷",
            self._get_sensor_data_df()
        )

    def request_diagnosis(self):
        """請求 A2A 專家診斷"""
        if self.current_scenario is None:
            return "❌ 請先開始新情境", ""

        # 取得設備狀態
        equipment_state = self.digital_twin.export_current_state()

        # 啟動 A2A 會診
        diagnosis_result = self.a2a_coordinator.start_diagnosis_session(
            equipment_state=equipment_state,
            student_level=self.current_scenario.get("student_level", "beginner")
        )

        # 格式化診斷報告
        report = self._format_diagnosis_report(diagnosis_result)

        # 格式化操作步驟
        steps = self._format_procedure_steps(diagnosis_result["procedure"]["steps"])

        return report, steps

    def _format_diagnosis_report(self, diagnosis: Dict) -> str:
        """格式化診斷報告"""
        summary = diagnosis["session_summary"]
        diag = diagnosis["diagnosis"]
        safety = diagnosis["safety"]

        report = f"""
# 🤖 A2A 多專家診斷報告

## 會話摘要
- **故障類型:** {summary['fault_type']}
- **診斷信心度:** {summary['confidence']:.2%}
- **嚴重程度:** {summary['severity']}
- **風險等級:** {summary['risk_level']}
- **難度等級:** {summary['difficulty']}
- **預估時間:** {summary['estimated_time']}

---

## 📋 診斷專家意見
**診斷結果:** {diag['result']}
**信心度:** {diag['confidence']:.2%}

**可能根因:**
"""
        for rc in diag.get('root_causes', []):
            report += f"- {rc}\n"

        report += "\n**專家建議:**\n"
        for rec in diag.get('recommendations', []):
            report += f"{rec}\n"

        report += f"""
---

## 🛡️ 安全專家意見
**安全決策:** {safety['decision']}
**風險等級:** {safety['risk_level']}

**必要防護裝備:**
"""
        for ppe in safety['required_ppe']:
            report += f"- {ppe}\n"

        report += "\n**安全建議:**\n"
        for rec in safety['safety_recommendations']:
            report += f"{rec}\n"

        return report

    def _format_procedure_steps(self, steps: List[Dict]) -> str:
        """格式化操作步驟"""
        procedure = "# 🔧 操作專家建議步驟\n\n"

        for step in steps:
            step_num = step['step_number']
            step_type = step['type']

            if step_type == "safety_preparation":
                procedure += f"## ⚠️ 步驟 {step_num}: {step['description']}\n"
            else:
                procedure += f"## 步驟 {step_num}: {step['description']}\n"

            for action in step['actions']:
                procedure += f"- {action}\n"

            procedure += "\n"

        return procedure

    def execute_step(self, step_description: str):
        """執行操作步驟"""
        if not step_description:
            return "❌ 請輸入操作步驟", ""

        # 記錄學員動作
        action_record = {
            "step_number": self.current_step,
            "action": step_description,
            "timestamp": datetime.now().isoformat(),
            "is_correct": True  # 簡化版，實際應驗證
        }
        self.student_actions.append(action_record)
        self.current_step += 1

        feedback = f"✅ 已記錄步驟 {self.current_step}: {step_description}"

        # 更新操作記錄
        action_log = self._get_action_log()

        return feedback, action_log

    def submit_diagnosis(self, student_diagnosis: str, confidence: str):
        """提交診斷結果"""
        if not student_diagnosis:
            return "❌ 請輸入診斷結果"

        if self.current_scenario is None:
            return "❌ 請先開始新情境"

        # 計算完成時間
        completion_time = (datetime.now() - self.session_start_time).total_seconds() / 60

        # 轉換信心度
        confidence_map = {
            "非常確定": 0.95,
            "比較確定": 0.75,
            "不太確定": 0.50,
            "完全不確定": 0.25
        }
        conf_value = confidence_map.get(confidence, 0.5)

        # 評分
        evaluation = self.scoring_system.evaluate_session(
            student_id=self.current_student_id,
            scenario=self.current_scenario,
            student_actions=self.student_actions,
            diagnosis_result={
                "diagnosis": student_diagnosis,
                "confidence": conf_value,
                "safety": {"required_ppe": []}
            },
            completion_time=completion_time,
            safety_violations=[]
        )

        # 格式化評分報告
        report = self._format_evaluation_report(evaluation)

        return report

    def _format_evaluation_report(self, evaluation: Dict) -> str:
        """格式化評分報告"""
        scores = evaluation["scores"]

        report = f"""
# 📊 訓練評估報告

## 學員資訊
- **學員 ID:** {evaluation['student_id']}
- **情境類型:** {evaluation['scenario_type']}
- **難度等級:** {evaluation['difficulty']}
- **完成時間:** {evaluation['completion_time']:.1f} / {evaluation['time_limit']} 分鐘

---

## 得分詳情

### 總分: {scores['total']} / 100 (等級: {evaluation['grade']})

#### 📋 診斷準確性 (30%)
- **得分:** {scores['diagnostic']['score']:.1f} / 100
- **反饋:** {scores['diagnostic']['feedback']}

#### 🔧 操作正確性 (40%)
- **得分:** {scores['operation']['score']:.1f} / 100
- **反饋:** {scores['operation']['feedback']}
- **正確動作:** {scores['operation']['details']['correct_actions']} / {scores['operation']['details']['total_actions']}

#### 🛡️ 安全合規性 (30%)
- **得分:** {scores['safety']['score']:.1f} / 100
- **反饋:** {scores['safety']['feedback']}
- **違規次數:** {scores['safety']['violations']['total']}

#### ⏱️ 時間效率 (加分)
- **加分:** {scores['time_efficiency']['bonus']}
- **反饋:** {scores['time_efficiency']['feedback']}

---

## 💡 改進建議
"""
        for area in evaluation['improvement_areas']:
            report += f"- {area}\n"

        report += f"\n---\n\n**綜合評語:**\n{evaluation['feedback']}"

        return report

    def _get_sensor_data_df(self) -> pd.DataFrame:
        """取得感測器資料表格"""
        # 隨機選擇 20 個感測器顯示
        import random
        sample_sensors = random.sample(list(self.digital_twin.sensor_specs.keys()),
                                      min(20, len(self.digital_twin.sensor_specs)))

        data = []
        for sensor_id in sample_sensors:
            status = self.digital_twin.get_sensor_status(sensor_id)
            data.append({
                "感測器 ID": sensor_id,
                "類別": status["category"],
                "當前值": f"{status['current_value']:.2f}",
                "單位": status["unit"],
                "狀態": status["status"],
                "偏差%": f"{status['deviation']:.1f}%"
            })

        return pd.DataFrame(data)

    def _get_action_log(self) -> str:
        """取得操作記錄"""
        if not self.student_actions:
            return "尚未執行任何操作"

        log = "## 操作記錄\n\n"
        for action in self.student_actions:
            log += f"- **步驟 {action['step_number']}:** {action['action']}\n"

        return log


def create_interface(secom_data_path: str):
    """建立 Gradio 介面"""

    # 初始化訓練介面
    training_interface = TrainingInterface(secom_data_path)

    # === 建立 Gradio 介面 ===
    with gr.Blocks(title="半導體設備故障處理訓練系統") as demo:

        gr.Markdown("""
        # 🎓 半導體設備故障處理訓練系統
        ## Interactive Semiconductor Equipment Fault Handling Training System

        基於真實 SECOM 資料 + A2A 多專家 AI 協作的沉浸式訓練平台
        """)

        with gr.Tab("🎯 開始訓練"):
            gr.Markdown("### 設定訓練參數")

            with gr.Row():
                student_id_input = gr.Textbox(
                    label="學員 ID",
                    placeholder="請輸入您的學員編號，例如: STU001"
                )
                difficulty_dropdown = gr.Dropdown(
                    choices=["隨機", "EASY", "MEDIUM", "HARD"],
                    value="MEDIUM",
                    label="難度等級"
                )
                level_dropdown = gr.Dropdown(
                    choices=["beginner", "intermediate", "advanced"],
                    value="beginner",
                    label="學員程度"
                )

            start_btn = gr.Button("🚀 開始新情境", variant="primary", size="lg")

            scenario_output = gr.Markdown(label="情境資訊")
            equipment_output = gr.Markdown(label="設備狀態")
            status_output = gr.Textbox(label="系統訊息")

            gr.Markdown("### 感測器資料")
            sensor_table = gr.Dataframe(label="感測器讀數")

        with gr.Tab("🤖 AI 專家診斷"):
            gr.Markdown("### 請求 A2A 多專家會診")

            diagnose_btn = gr.Button("🩺 請求專家診斷", variant="primary", size="lg")

            diagnosis_report = gr.Markdown(label="診斷報告")
            procedure_steps = gr.Markdown(label="操作步驟")

        with gr.Tab("🔧 執行操作"):
            gr.Markdown("### 執行操作步驟")

            step_input = gr.Textbox(
                label="輸入您要執行的操作",
                placeholder="例如: 檢查真空計讀數",
                lines=2
            )
            execute_btn = gr.Button("✅ 執行步驟", variant="primary")

            execute_feedback = gr.Textbox(label="執行反饋")
            action_log = gr.Markdown(label="操作記錄")

        with gr.Tab("📝 提交診斷"):
            gr.Markdown("### 提交您的診斷結果")

            diagnosis_input = gr.Textbox(
                label="您的診斷結果",
                placeholder="例如: vacuum_leak",
                lines=2
            )
            confidence_dropdown = gr.Dropdown(
                choices=["非常確定", "比較確定", "不太確定", "完全不確定"],
                value="比較確定",
                label="診斷信心度"
            )

            submit_btn = gr.Button("📤 提交診斷", variant="primary", size="lg")

            evaluation_report = gr.Markdown(label="評估報告")

        # === 綁定事件 ===
        start_btn.click(
            fn=training_interface.start_new_scenario,
            inputs=[student_id_input, difficulty_dropdown, level_dropdown],
            outputs=[scenario_output, equipment_output, status_output, sensor_table]
        )

        diagnose_btn.click(
            fn=training_interface.request_diagnosis,
            outputs=[diagnosis_report, procedure_steps]
        )

        execute_btn.click(
            fn=training_interface.execute_step,
            inputs=[step_input],
            outputs=[execute_feedback, action_log]
        )

        submit_btn.click(
            fn=training_interface.submit_diagnosis,
            inputs=[diagnosis_input, confidence_dropdown],
            outputs=[evaluation_report]
        )

    return demo


if __name__ == "__main__":
    # 設定 SECOM 資料路徑
    secom_path = "../../uci-secom.csv"

    # 檢查檔案是否存在
    if not os.path.exists(secom_path):
        print(f"❌ 找不到 SECOM 資料集: {secom_path}")
        print("請確認檔案路徑是否正確")
    else:
        # 建立並啟動介面
        demo = create_interface(secom_path)
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False
        )
