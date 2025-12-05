"""
學員評分與追蹤系統
自動評估學員表現並追蹤學習進度
"""

import json
from typing import Dict, List
from datetime import datetime
import numpy as np


class ScoringSystem:
    """學員評分系統"""

    def __init__(self):
        """初始化評分系統"""
        self.student_records = {}  # 學員記錄

    def evaluate_session(
        self,
        student_id: str,
        scenario: Dict,
        student_actions: List[Dict],
        diagnosis_result: Dict,
        completion_time: float,  # 分鐘
        safety_violations: List[Dict] = None
    ) -> Dict:
        """
        評估單次訓練會話

        Args:
            student_id: 學員 ID
            scenario: 訓練情境
            student_actions: 學員執行的動作列表
            diagnosis_result: 學員的診斷結果
            completion_time: 完成時間（分鐘）
            safety_violations: 安全違規記錄

        Returns:
            評分結果
        """
        safety_violations = safety_violations or []

        # === 1. 診斷準確性評分 (30%) ===
        diagnostic_score = self._evaluate_diagnostic(
            student_diagnosis=diagnosis_result.get("diagnosis", ""),
            correct_diagnosis=scenario["expected_diagnosis"],
            confidence=diagnosis_result.get("confidence", 0)
        )

        # === 2. 操作正確性評分 (40%) ===
        operation_score = self._evaluate_operations(
            student_actions=student_actions,
            scenario_type=scenario["type"]
        )

        # === 3. 安全合規性評分 (30%) ===
        safety_score = self._evaluate_safety(
            safety_violations=safety_violations,
            required_ppe=diagnosis_result.get("safety", {}).get("required_ppe", [])
        )

        # === 4. 時間效率評分 (加分項) ===
        time_bonus = self._evaluate_time_efficiency(
            completion_time=completion_time,
            time_limit=scenario["time_limit"]
        )

        # === 總分計算 ===
        total_score = (
            diagnostic_score["score"] * 0.3 +
            operation_score["score"] * 0.4 +
            safety_score["score"] * 0.3 +
            time_bonus["bonus"]
        )

        # 限制總分在 0-100 之間
        total_score = max(0, min(100, total_score))

        # 判定等級
        grade = self._calculate_grade(total_score)

        # 記錄評估結果
        evaluation_result = {
            "student_id": student_id,
            "scenario_id": scenario["scenario_id"],
            "scenario_type": scenario["type"],
            "difficulty": scenario["difficulty"],
            "timestamp": datetime.now().isoformat(),
            "scores": {
                "diagnostic": diagnostic_score,
                "operation": operation_score,
                "safety": safety_score,
                "time_efficiency": time_bonus,
                "total": round(total_score, 2)
            },
            "grade": grade,
            "completion_time": completion_time,
            "time_limit": scenario["time_limit"],
            "safety_violations_count": len(safety_violations),
            "feedback": self._generate_feedback(
                diagnostic_score,
                operation_score,
                safety_score,
                time_bonus
            ),
            "improvement_areas": self._identify_improvement_areas(
                diagnostic_score,
                operation_score,
                safety_score
            )
        }

        # 更新學員記錄
        self._update_student_record(student_id, evaluation_result)

        return evaluation_result

    def _evaluate_diagnostic(
        self,
        student_diagnosis: str,
        correct_diagnosis: str,
        confidence: float
    ) -> Dict:
        """評估診斷準確性"""
        # 完全正確
        if student_diagnosis.lower() == correct_diagnosis.lower():
            base_score = 100
            feedback = "診斷完全正確！"

        # 部分正確（簡化版，實際可用語義相似度）
        elif student_diagnosis.lower() in correct_diagnosis.lower() or \
             correct_diagnosis.lower() in student_diagnosis.lower():
            base_score = 70
            feedback = "診斷部分正確，請更精確地識別故障類型"

        # 錯誤
        else:
            base_score = 0
            feedback = f"診斷錯誤。正確答案: {correct_diagnosis}"

        # 信心度調整（如果診斷錯誤但信心很高，扣分）
        if base_score == 0 and confidence > 0.8:
            base_score -= 10  # 過度自信扣分
            feedback += " (提示: 診斷時應保持謹慎)"

        return {
            "score": max(0, base_score),
            "feedback": feedback,
            "correct_diagnosis": correct_diagnosis,
            "student_diagnosis": student_diagnosis
        }

    def _evaluate_operations(
        self,
        student_actions: List[Dict],
        scenario_type: str
    ) -> Dict:
        """評估操作正確性"""
        if not student_actions:
            return {
                "score": 0,
                "feedback": "未執行任何操作",
                "details": {}
            }

        # 統計操作結果
        total_actions = len(student_actions)
        correct_actions = sum(1 for action in student_actions if action.get("is_correct", False))
        skipped_steps = sum(1 for action in student_actions if action.get("skipped", False))

        # 計算基礎分數
        if total_actions > 0:
            correctness_ratio = correct_actions / total_actions
            base_score = correctness_ratio * 100
        else:
            base_score = 0

        # 跳過步驟扣分
        skip_penalty = skipped_steps * 5
        final_score = max(0, base_score - skip_penalty)

        # 生成反饋
        if final_score >= 90:
            feedback = "操作程序執行優秀！"
        elif final_score >= 70:
            feedback = "操作程序基本正確，仍有改進空間"
        elif final_score >= 50:
            feedback = "操作程序存在較多錯誤，需要加強練習"
        else:
            feedback = "操作程序錯誤較多，請重新學習 SOP"

        return {
            "score": round(final_score, 2),
            "feedback": feedback,
            "details": {
                "total_actions": total_actions,
                "correct_actions": correct_actions,
                "skipped_steps": skipped_steps,
                "correctness_ratio": round(correctness_ratio, 2) if total_actions > 0 else 0
            }
        }

    def _evaluate_safety(
        self,
        safety_violations: List[Dict],
        required_ppe: List[str]
    ) -> Dict:
        """評估安全合規性"""
        base_score = 100

        # 安全違規扣分
        critical_violations = sum(1 for v in safety_violations if v.get("risk_level") == "CRITICAL")
        high_violations = sum(1 for v in safety_violations if v.get("risk_level") == "HIGH")
        medium_violations = sum(1 for v in safety_violations if v.get("risk_level") == "MEDIUM")

        # 扣分規則
        base_score -= critical_violations * 30  # 嚴重違規扣 30 分
        base_score -= high_violations * 15      # 高風險違規扣 15 分
        base_score -= medium_violations * 5     # 中風險違規扣 5 分

        final_score = max(0, base_score)

        # 生成反饋
        if final_score == 100:
            feedback = "安全操作完美！"
        elif final_score >= 80:
            feedback = "安全操作良好，注意避免小錯誤"
        elif final_score >= 60:
            feedback = "存在安全風險，請更嚴格遵守安全規範"
        else:
            feedback = "⚠️ 嚴重安全違規！必須重新接受安全訓練"

        return {
            "score": final_score,
            "feedback": feedback,
            "violations": {
                "critical": critical_violations,
                "high": high_violations,
                "medium": medium_violations,
                "total": len(safety_violations)
            }
        }

    def _evaluate_time_efficiency(
        self,
        completion_time: float,
        time_limit: float
    ) -> Dict:
        """評估時間效率（加分項）"""
        if completion_time <= time_limit * 0.7:
            # 70% 時間內完成，加 10 分
            bonus = 10
            feedback = "時間效率優秀！"
        elif completion_time <= time_limit:
            # 時限內完成，加 5 分
            bonus = 5
            feedback = "時間控制良好"
        elif completion_time <= time_limit * 1.2:
            # 略微超時，不加分不扣分
            bonus = 0
            feedback = "時間控制尚可"
        else:
            # 嚴重超時，扣 5 分
            bonus = -5
            feedback = "超時較多，需提高效率"

        return {
            "bonus": bonus,
            "feedback": feedback,
            "completion_time": completion_time,
            "time_limit": time_limit,
            "ratio": round(completion_time / time_limit, 2) if time_limit > 0 else 0
        }

    def _calculate_grade(self, total_score: float) -> str:
        """計算等級"""
        if total_score >= 90:
            return "A"
        elif total_score >= 80:
            return "B"
        elif total_score >= 70:
            return "C"
        elif total_score >= 60:
            return "D"
        else:
            return "F"

    def _generate_feedback(
        self,
        diagnostic: Dict,
        operation: Dict,
        safety: Dict,
        time: Dict
    ) -> str:
        """生成綜合反饋"""
        feedback_parts = [
            f"診斷評價: {diagnostic['feedback']}",
            f"操作評價: {operation['feedback']}",
            f"安全評價: {safety['feedback']}",
            f"時間評價: {time['feedback']}"
        ]

        return "\n".join(feedback_parts)

    def _identify_improvement_areas(
        self,
        diagnostic: Dict,
        operation: Dict,
        safety: Dict
    ) -> List[str]:
        """識別改進領域"""
        areas = []

        if diagnostic["score"] < 70:
            areas.append("故障診斷能力需要加強")

        if operation["score"] < 70:
            areas.append("操作程序熟練度不足")

        if safety["score"] < 80:
            areas.append("安全意識需要提升")

        if not areas:
            areas.append("表現優秀，繼續保持！")

        return areas

    def _update_student_record(self, student_id: str, evaluation: Dict):
        """更新學員記錄"""
        if student_id not in self.student_records:
            self.student_records[student_id] = {
                "student_id": student_id,
                "total_sessions": 0,
                "evaluations": [],
                "statistics": {
                    "average_score": 0,
                    "best_score": 0,
                    "improvement_rate": 0
                }
            }

        record = self.student_records[student_id]
        record["total_sessions"] += 1
        record["evaluations"].append(evaluation)

        # 更新統計
        scores = [e["scores"]["total"] for e in record["evaluations"]]
        record["statistics"]["average_score"] = np.mean(scores)
        record["statistics"]["best_score"] = max(scores)

        # 計算改進率（最近 5 次平均 vs 之前平均）
        if len(scores) >= 10:
            recent_avg = np.mean(scores[-5:])
            previous_avg = np.mean(scores[:-5])
            record["statistics"]["improvement_rate"] = \
                ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0

    def get_student_report(self, student_id: str) -> Dict:
        """取得學員報告"""
        if student_id not in self.student_records:
            return {"error": f"Student {student_id} not found"}

        record = self.student_records[student_id]

        # 統計各難度表現
        difficulty_stats = {}
        for eval in record["evaluations"]:
            diff = eval["difficulty"]
            if diff not in difficulty_stats:
                difficulty_stats[diff] = {"count": 0, "total_score": 0}
            difficulty_stats[diff]["count"] += 1
            difficulty_stats[diff]["total_score"] += eval["scores"]["total"]

        for diff, stats in difficulty_stats.items():
            stats["average_score"] = stats["total_score"] / stats["count"]

        return {
            "student_id": student_id,
            "total_sessions": record["total_sessions"],
            "statistics": record["statistics"],
            "difficulty_performance": difficulty_stats,
            "recent_evaluations": record["evaluations"][-5:],  # 最近 5 次
            "learning_trend": self._calculate_learning_trend(record["evaluations"])
        }

    def _calculate_learning_trend(self, evaluations: List[Dict]) -> str:
        """計算學習趨勢"""
        if len(evaluations) < 3:
            return "數據不足"

        scores = [e["scores"]["total"] for e in evaluations]
        recent = scores[-3:]

        # 簡單趨勢判斷
        if all(recent[i] >= recent[i-1] for i in range(1, len(recent))):
            return "持續進步 ↗"
        elif all(recent[i] <= recent[i-1] for i in range(1, len(recent))):
            return "需要關注 ↘"
        else:
            return "波動 ~"


if __name__ == "__main__":
    # 測試評分系統
    scorer = ScoringSystem()

    print("=== 評分系統測試 ===\n")

    # 模擬情境
    test_scenario = {
        "scenario_id": "TEST_001",
        "type": "vacuum_leak",
        "difficulty": "HARD",
        "expected_diagnosis": "vacuum_leak",
        "time_limit": 30
    }

    # 模擬學員動作
    test_actions = [
        {"action": "檢查真空計", "is_correct": True},
        {"action": "關閉氣體供應", "is_correct": True},
        {"action": "執行洩漏檢測", "is_correct": True},
        {"action": "更換密封圈", "is_correct": True}
    ]

    # 模擬診斷結果
    test_diagnosis = {
        "diagnosis": "vacuum_leak",
        "confidence": 0.85,
        "safety": {"required_ppe": ["防護手套", "安全眼鏡"]}
    }

    # 評估
    result = scorer.evaluate_session(
        student_id="STU001",
        scenario=test_scenario,
        student_actions=test_actions,
        diagnosis_result=test_diagnosis,
        completion_time=25.0,
        safety_violations=[]
    )

    print(f"學員 ID: {result['student_id']}")
    print(f"總分: {result['scores']['total']}")
    print(f"等級: {result['grade']}")
    print(f"\n各項分數:")
    print(f"  診斷: {result['scores']['diagnostic']['score']}")
    print(f"  操作: {result['scores']['operation']['score']}")
    print(f"  安全: {result['scores']['safety']['score']}")
    print(f"  時間加分: {result['scores']['time_efficiency']['bonus']}")
    print(f"\n改進建議:")
    for area in result['improvement_areas']:
        print(f"  • {area}")
