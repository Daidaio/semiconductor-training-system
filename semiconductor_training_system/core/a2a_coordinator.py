"""
A2A (Agent-to-Agent) 協調器
協調診斷、操作、安全三個專家 Agent 的協作
"""

from typing import Dict, List
from .agents.diagnostic_agent import DiagnosticAgent
from .agents.operation_agent import OperationAgent
from .agents.safety_agent import SafetyAgent
from .agents.base_agent import AgentMessage
from datetime import datetime


class A2ACoordinator:
    """A2A 多專家協調系統"""

    def __init__(self, api_key: str = None):
        """
        初始化協調器

        Args:
            api_key: OpenAI/Claude API 金鑰（選填）
        """
        # 初始化三個專家
        self.diagnostic_agent = DiagnosticAgent(api_key=api_key)
        self.operation_agent = OperationAgent()
        self.safety_agent = SafetyAgent()

        # 協調記錄
        self.session_log = []
        self.current_session = None

    def start_diagnosis_session(
        self,
        equipment_state: Dict,
        student_level: str = "beginner"
    ) -> Dict:
        """
        啟動診斷會話

        Args:
            equipment_state: 設備狀態（從 digital_twin 取得）
            student_level: 學員程度 (beginner/intermediate/advanced)

        Returns:
            完整的診斷與操作建議
        """
        session_id = f"SESSION_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.current_session = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "student_level": student_level,
            "equipment_state": equipment_state
        }

        print(f"\n{'='*60}")
        print(f"🤖 A2A 多專家會診系統啟動")
        print(f"會話 ID: {session_id}")
        print(f"{'='*60}\n")

        # === 階段 1: 診斷專家分析 ===
        print("📋 階段 1: 診斷專家分析中...")
        diagnostic_result = self.diagnostic_agent.analyze({
            "sensors": equipment_state.get("sensors", {}),
            "summary": equipment_state.get("summary", {})
        })

        diagnostic_decision = self.diagnostic_agent.make_decision(diagnostic_result)

        print(f"   ✓ 診斷完成")
        print(f"   - 診斷結果: {diagnostic_decision.get('diagnosis', 'N/A')}")
        print(f"   - 信心度: {diagnostic_decision.get('confidence', 0):.2%}")
        print(f"   - 嚴重程度: {diagnostic_decision.get('severity', 'N/A')}\n")

        # === 階段 2: 操作專家提供指引 ===
        print("🔧 階段 2: 操作專家規劃程序...")

        # 診斷專家 → 操作專家
        msg_to_operation = self.diagnostic_agent.send_message(
            receiver="OperationAgent",
            message_type="query",
            content={
                "fault_type": diagnostic_decision.get("diagnosis", "unknown"),
                "severity": diagnostic_decision.get("severity", "MEDIUM"),
                "student_level": student_level
            },
            priority=3
        )

        operation_result = self.operation_agent.receive_message(msg_to_operation)
        operation_decision = self.operation_agent.make_decision(operation_result)

        print(f"   ✓ 操作規劃完成")
        print(f"   - 操作難度: {operation_result.get('difficulty_level', 'N/A')}")
        print(f"   - 預估時間: {operation_result.get('estimated_time', 'N/A')}")
        print(f"   - 步驟數量: {len(operation_result.get('procedure_steps', []))}\n")

        # === 階段 3: 安全專家評估 ===
        print("🛡️  階段 3: 安全專家評估風險...")

        # 操作專家 → 安全專家
        msg_to_safety = self.operation_agent.send_message(
            receiver="SafetyAgent",
            message_type="safety_check",
            content={
                "proposed_action": operation_result.get("procedure_steps", [""])[0] if operation_result.get("procedure_steps") else "",
                "current_state": equipment_state,
                "fault_type": diagnostic_decision.get("diagnosis", "unknown"),
                "severity": diagnostic_decision.get("severity", "MEDIUM")
            },
            priority=5  # 安全最高優先
        )

        safety_result = self.safety_agent.receive_message(msg_to_safety)
        safety_decision = self.safety_agent.make_decision(safety_result)

        print(f"   ✓ 安全評估完成")
        print(f"   - 安全性: {'✓ 可執行' if safety_result.get('is_safe', False) else '✗ 有風險'}")
        print(f"   - 風險等級: {safety_result.get('risk_level', 'N/A')}")
        print(f"   - 決策: {safety_decision.get('decision', 'N/A')}\n")

        # === 整合建議 ===
        print("📊 階段 4: 整合專家建議...\n")

        integrated_recommendation = self._integrate_recommendations(
            diagnostic_decision,
            operation_result,
            safety_decision
        )

        # 記錄會話
        self.session_log.append({
            "session_id": session_id,
            "diagnostic": diagnostic_decision,
            "operation": operation_result,
            "safety": safety_decision,
            "integrated": integrated_recommendation,
            "timestamp": datetime.now().isoformat()
        })

        print(f"{'='*60}")
        print("✅ A2A 多專家會診完成")
        print(f"{'='*60}\n")

        return integrated_recommendation

    def _integrate_recommendations(
        self,
        diagnostic: Dict,
        operation: Dict,
        safety: Dict
    ) -> Dict:
        """整合三個專家的建議"""

        # 檢查安全性
        if safety.get("decision") == "REJECT":
            return {
                "status": "REJECTED",
                "reason": "安全風險過高，不建議執行",
                "diagnostic": diagnostic,
                "safety_concerns": safety,
                "alternative_actions": [
                    "聯繫資深工程師",
                    "執行緊急停機",
                    "啟動安全協議"
                ]
            }

        # 整合操作步驟與安全要求
        procedure_steps = operation.get("procedure_steps", [])

        # 添加安全檢查點
        enhanced_steps = []
        required_ppe = safety.get("required_ppe", [])

        # 第一步前加入安全準備
        enhanced_steps.append({
            "step_number": 0,
            "type": "safety_preparation",
            "description": "安全準備",
            "actions": [
                f"穿戴防護裝備: {', '.join(required_ppe)}",
                "確認緊急停止按鈕位置",
                "通知主管開始操作"
            ],
            "is_mandatory": True
        })

        # 添加原始步驟
        for idx, step in enumerate(procedure_steps, 1):
            enhanced_steps.append({
                "step_number": idx,
                "type": "operation",
                "description": step,
                "actions": [step],
                "is_mandatory": True,
                "safety_notes": []
            })

        # 添加檢查點
        checkpoints = operation.get("checkpoints", [])

        return {
            "status": "APPROVED" if safety.get("decision") in ["APPROVE", "APPROVE_WITH_CONDITIONS"] else "CONDITIONAL",
            "session_summary": {
                "fault_type": diagnostic.get("diagnosis"),
                "confidence": diagnostic.get("confidence"),
                "severity": diagnostic.get("severity"),
                "difficulty": operation.get("difficulty_level"),
                "risk_level": safety.get("risk_level"),
                "estimated_time": operation.get("estimated_time")
            },
            "diagnosis": {
                "result": diagnostic.get("diagnosis"),
                "root_causes": diagnostic.get("root_causes", []),
                "confidence": diagnostic.get("confidence"),
                "recommendations": diagnostic.get("recommendations", [])
            },
            "procedure": {
                "steps": enhanced_steps,
                "checkpoints": checkpoints,
                "tools_required": operation.get("tools_required", []),
                "difficulty_level": operation.get("difficulty_level")
            },
            "safety": {
                "decision": safety.get("decision"),
                "risk_level": safety.get("risk_level"),
                "required_ppe": required_ppe,
                "safety_recommendations": safety.get("safety_recommendations", []),
                "emergency_procedure": safety.get("emergency_procedure", {})
            },
            "learning_objectives": self._generate_learning_objectives(diagnostic, operation),
            "assessment_criteria": self._generate_assessment_criteria(operation, safety)
        }

    def _generate_learning_objectives(self, diagnostic: Dict, operation: Dict) -> List[str]:
        """生成學習目標"""
        objectives = [
            f"理解 {diagnostic.get('diagnosis', 'N/A')} 故障的成因與徵兆",
            "能夠正確診斷設備異常狀態",
            "熟悉標準操作程序 (SOP)",
            "理解安全規範的重要性"
        ]

        difficulty = operation.get("difficulty_level", "MEDIUM")
        if difficulty == "HARD":
            objectives.append("能夠處理高難度故障情境")

        return objectives

    def _generate_assessment_criteria(self, operation: Dict, safety: Dict) -> Dict:
        """生成評估標準"""
        return {
            "diagnostic_accuracy": {
                "weight": 0.3,
                "description": "診斷準確性",
                "criteria": [
                    "正確識別故障類型",
                    "準確判斷嚴重程度",
                    "合理推斷根本原因"
                ]
            },
            "procedure_correctness": {
                "weight": 0.4,
                "description": "操作正確性",
                "criteria": [
                    "按照正確順序執行步驟",
                    "使用正確的工具和參數",
                    "完成所有必要檢查點"
                ]
            },
            "safety_compliance": {
                "weight": 0.3,
                "description": "安全合規性",
                "criteria": [
                    "正確穿戴防護裝備",
                    "遵守安全操作規範",
                    "識別並規避風險"
                ]
            }
        }

    def provide_step_guidance(
        self,
        step_number: int,
        fault_type: str,
        need_hint: bool = False
    ) -> Dict:
        """
        為特定步驟提供指引

        Args:
            step_number: 步驟編號
            fault_type: 故障類型
            need_hint: 是否需要提示

        Returns:
            步驟指引
        """
        guidance = {
            "step_number": step_number,
            "fault_type": fault_type
        }

        if need_hint:
            hint = self.operation_agent.provide_hint(step_number, fault_type)
            guidance["hint"] = hint

        return guidance

    def validate_student_action(
        self,
        action: str,
        expected_step: str,
        fault_type: str
    ) -> Dict:
        """
        驗證學員操作

        Args:
            action: 學員執行的動作
            expected_step: 預期步驟
            fault_type: 故障類型

        Returns:
            驗證結果
        """
        # 操作驗證
        operation_validation = self.operation_agent.validate_action(
            action,
            {"expected_step": expected_step, "fault_type": fault_type}
        )

        # 安全檢查
        safety_check = self.safety_agent.analyze({
            "proposed_action": action,
            "current_state": {},
            "fault_type": fault_type,
            "severity": "MEDIUM"
        })

        return {
            "is_correct": operation_validation["is_correct"],
            "is_safe": safety_check["is_safe"],
            "feedback": operation_validation["feedback"],
            "safety_warnings": safety_check.get("safety_recommendations", []),
            "allow_proceed": operation_validation["is_correct"] and safety_check["is_safe"]
        }

    def get_session_history(self, last_n: int = 5) -> List[Dict]:
        """取得會話歷史"""
        return self.session_log[-last_n:]


if __name__ == "__main__":
    # 測試 A2A 協調器
    coordinator = A2ACoordinator()

    # 模擬設備狀態
    test_equipment_state = {
        "sensors": {},
        "summary": {
            "total_sensors": 558,
            "normal": 500,
            "warning": 30,
            "critical": 28,
            "is_fault": True,
            "fault_type": "vacuum_leak"
        },
        "timestamp": "2024-01-01T00:00:00"
    }

    # 啟動會診
    result = coordinator.start_diagnosis_session(
        equipment_state=test_equipment_state,
        student_level="beginner"
    )

    # 顯示結果
    print("\n=== 整合建議 ===")
    print(f"狀態: {result['status']}")
    print(f"\n診斷: {result['session_summary']['fault_type']}")
    print(f"信心度: {result['session_summary']['confidence']:.2%}")
    print(f"嚴重程度: {result['session_summary']['severity']}")
    print(f"風險等級: {result['session_summary']['risk_level']}")

    print(f"\n操作步驟數: {len(result['procedure']['steps'])}")
    print(f"所需工具: {', '.join(result['procedure']['tools_required'])}")

    print(f"\n安全決策: {result['safety']['decision']}")
    print(f"必要防護: {', '.join(result['safety']['required_ppe'])}")
