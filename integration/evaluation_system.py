# -*- coding: utf-8 -*-
"""
評分系統 (Evaluation System)
綜合評估學員理論學習和實作訓練表現
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path
import math


class EvaluationSystem:
    """
    評分系統

    職責：
    1. 理論測驗評分
    2. 實作操作評分
    3. 綜合評估
    4. 生成改進建議
    5. 計算學習效率指標

    評分公式：
    - 理論分數 = 測驗正確率 × 100
    - 實作分數 = (診斷準確度 × 0.4 + 操作正確性 × 0.4 + 處理速度 × 0.2) × 100
    - 綜合分數 = 理論分數 × 0.3 + 實作分數 × 0.7

    使用範例：
    ```python
    evaluator = EvaluationSystem()

    # 評估理論測驗
    theory_score = evaluator.evaluate_theory_test(test_results)

    # 評估實作訓練
    practice_score = evaluator.evaluate_practice_session(session_data)

    # 綜合評估
    overall = evaluator.evaluate_overall(theory_score, practice_score)
    ```
    """

    # 評分權重
    THEORY_WEIGHT = 0.3
    PRACTICE_WEIGHT = 0.7

    # 實作評分細項權重
    DIAGNOSIS_WEIGHT = 0.4
    OPERATION_WEIGHT = 0.4
    TIME_EFFICIENCY_WEIGHT = 0.2

    # 等級標準
    GRADE_THRESHOLDS = {
        "優秀": 90,
        "良好": 80,
        "及格": 70,
        "待加強": 60,
        "不及格": 0
    }

    def __init__(self, data_dir: str = "data/evaluations"):
        """
        初始化評分系統

        Args:
            data_dir: 評分資料儲存目錄
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_theory_test(self, test_results: List[Dict]) -> Dict:
        """
        評估理論測驗

        Args:
            test_results: 測驗結果列表，每項包含：
                {
                    "question": str,
                    "student_answer": str,
                    "correct_answer": str,
                    "is_correct": bool,
                    "topic": str,
                    "difficulty": str  # easy/medium/hard
                }

        Returns:
            評分結果：
            {
                "score": float,  # 總分 (0-100)
                "correct_count": int,
                "total_count": int,
                "accuracy": float,
                "topic_breakdown": {...},
                "difficulty_breakdown": {...},
                "grade": str
            }
        """
        if not test_results:
            return self._empty_evaluation("theory")

        total_count = len(test_results)
        correct_count = sum(1 for r in test_results if r.get("is_correct", False))

        # 基本準確率
        accuracy = correct_count / total_count if total_count > 0 else 0

        # 按主題分析
        topic_stats = {}
        for result in test_results:
            topic = result.get("topic", "unknown")
            if topic not in topic_stats:
                topic_stats[topic] = {"correct": 0, "total": 0}

            topic_stats[topic]["total"] += 1
            if result.get("is_correct", False):
                topic_stats[topic]["correct"] += 1

        topic_breakdown = {
            topic: {
                "accuracy": stats["correct"] / stats["total"],
                "correct": stats["correct"],
                "total": stats["total"]
            }
            for topic, stats in topic_stats.items()
        }

        # 按難度分析
        difficulty_stats = {"easy": {"correct": 0, "total": 0},
                          "medium": {"correct": 0, "total": 0},
                          "hard": {"correct": 0, "total": 0}}

        for result in test_results:
            difficulty = result.get("difficulty", "medium")
            if difficulty in difficulty_stats:
                difficulty_stats[difficulty]["total"] += 1
                if result.get("is_correct", False):
                    difficulty_stats[difficulty]["correct"] += 1

        difficulty_breakdown = {
            diff: {
                "accuracy": stats["correct"] / stats["total"] if stats["total"] > 0 else 0,
                "correct": stats["correct"],
                "total": stats["total"]
            }
            for diff, stats in difficulty_stats.items()
        }

        # 計算最終分數（考慮難度加權）
        weighted_score = 0
        total_weight = 0

        difficulty_weights = {"easy": 0.8, "medium": 1.0, "hard": 1.3}

        for result in test_results:
            difficulty = result.get("difficulty", "medium")
            weight = difficulty_weights.get(difficulty, 1.0)
            total_weight += weight

            if result.get("is_correct", False):
                weighted_score += weight

        final_score = (weighted_score / total_weight * 100) if total_weight > 0 else 0

        return {
            "score": round(final_score, 1),
            "correct_count": correct_count,
            "total_count": total_count,
            "accuracy": round(accuracy * 100, 1),
            "topic_breakdown": topic_breakdown,
            "difficulty_breakdown": difficulty_breakdown,
            "grade": self._get_grade(final_score),
            "strengths": self._identify_strengths(topic_breakdown),
            "weaknesses": self._identify_weaknesses(topic_breakdown)
        }

    def evaluate_practice_session(self, session_data: Dict) -> Dict:
        """
        評估實作訓練場景

        Args:
            session_data: 訓練場景資料，包含：
                {
                    "scenario_info": {...},
                    "diagnosis": {
                        "student_diagnosis": str,
                        "correct_diagnosis": str,
                        "is_correct": bool
                    },
                    "operations": [
                        {
                            "operation": str,
                            "is_correct": bool,
                            "timestamp": str
                        }
                    ],
                    "start_time": str,
                    "end_time": str,
                    "expert_consults": int
                }

        Returns:
            評分結果：
            {
                "score": float,  # 總分 (0-100)
                "diagnosis_score": float,
                "operation_score": float,
                "time_efficiency_score": float,
                "grade": str,
                "completion_time_minutes": float,
                "operation_accuracy": float
            }
        """
        if not session_data:
            return self._empty_evaluation("practice")

        # 1. 診斷準確度評分
        diagnosis_score = self._evaluate_diagnosis(session_data.get("diagnosis", {}))

        # 2. 操作正確性評分
        operation_score = self._evaluate_operations(session_data.get("operations", []))

        # 3. 處理速度評分
        time_efficiency_score = self._evaluate_time_efficiency(
            session_data.get("start_time"),
            session_data.get("end_time"),
            session_data.get("scenario_info", {}).get("expected_time_minutes", 30)
        )

        # 4. 計算加權總分
        final_score = (
            diagnosis_score * self.DIAGNOSIS_WEIGHT +
            operation_score * self.OPERATION_WEIGHT +
            time_efficiency_score * self.TIME_EFFICIENCY_WEIGHT
        ) * 100

        # 5. 計算完成時間
        completion_time = self._calculate_duration(
            session_data.get("start_time"),
            session_data.get("end_time")
        )

        # 6. 操作準確率
        operations = session_data.get("operations", [])
        correct_ops = sum(1 for op in operations if op.get("is_correct", False))
        operation_accuracy = correct_ops / len(operations) if operations else 0

        return {
            "score": round(final_score, 1),
            "diagnosis_score": round(diagnosis_score * 100, 1),
            "operation_score": round(operation_score * 100, 1),
            "time_efficiency_score": round(time_efficiency_score * 100, 1),
            "grade": self._get_grade(final_score),
            "completion_time_minutes": completion_time,
            "operation_accuracy": round(operation_accuracy * 100, 1),
            "total_operations": len(operations),
            "correct_operations": correct_ops,
            "expert_consults": session_data.get("expert_consults", 0)
        }

    def _evaluate_diagnosis(self, diagnosis: Dict) -> float:
        """
        評估診斷準確度

        Returns:
            分數 (0-1)
        """
        if not diagnosis:
            return 0.0

        is_correct = diagnosis.get("is_correct", False)

        if is_correct:
            return 1.0

        # 部分正確的情況（如果有提供相似度）
        similarity = diagnosis.get("similarity", 0.0)
        if similarity > 0.7:
            return 0.7
        elif similarity > 0.5:
            return 0.5
        elif similarity > 0.3:
            return 0.3

        return 0.0

    def _evaluate_operations(self, operations: List[Dict]) -> float:
        """
        評估操作正確性

        Returns:
            分數 (0-1)
        """
        if not operations:
            return 0.0

        correct_count = sum(1 for op in operations if op.get("is_correct", False))
        total_count = len(operations)

        # 基本準確率
        accuracy = correct_count / total_count

        # 考慮操作順序的正確性（如果有提供）
        sequence_bonus = 0.0
        if all(op.get("is_correct", False) for op in operations[:3]):
            # 前3步都正確，給予獎勵
            sequence_bonus = 0.1

        return min(1.0, accuracy + sequence_bonus)

    def _evaluate_time_efficiency(self,
                                  start_time: Optional[str],
                                  end_time: Optional[str],
                                  expected_time_minutes: float) -> float:
        """
        評估處理速度

        Returns:
            分數 (0-1)
        """
        if not start_time or not end_time:
            return 0.5  # 無時間資料，給予中等分數

        actual_time = self._calculate_duration(start_time, end_time)

        if actual_time <= 0:
            return 0.5

        # 計算時間比率
        time_ratio = actual_time / expected_time_minutes

        # 評分曲線
        if time_ratio <= 0.8:
            # 提前完成，滿分
            return 1.0
        elif time_ratio <= 1.0:
            # 在預期時間內完成
            return 0.9
        elif time_ratio <= 1.2:
            # 略超過預期
            return 0.7
        elif time_ratio <= 1.5:
            # 明顯超過預期
            return 0.5
        else:
            # 超時嚴重
            return max(0.2, 1.0 / time_ratio)

    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """計算時間差（分鐘）"""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            duration = (end - start).total_seconds() / 60
            return round(duration, 1)
        except:
            return 0.0

    def evaluate_overall(self, theory_score: float, practice_score: float) -> Dict:
        """
        綜合評估

        Args:
            theory_score: 理論分數 (0-100)
            practice_score: 實作分數 (0-100)

        Returns:
            綜合評估結果
        """
        # 加權平均
        overall_score = (
            theory_score * self.THEORY_WEIGHT +
            practice_score * self.PRACTICE_WEIGHT
        )

        # 判斷是否平衡
        score_diff = abs(theory_score - practice_score)
        is_balanced = score_diff < 15

        # 生成評語
        comments = []

        if overall_score >= 90:
            comments.append("整體表現優秀！")
        elif overall_score >= 80:
            comments.append("整體表現良好！")
        elif overall_score >= 70:
            comments.append("達到及格標準。")
        else:
            comments.append("需要加強訓練。")

        if not is_balanced:
            if theory_score > practice_score:
                comments.append("理論知識扎實，但實作能力需要提升。")
            else:
                comments.append("實作能力不錯，但理論基礎需要鞏固。")
        else:
            comments.append("理論與實作能力均衡發展。")

        return {
            "overall_score": round(overall_score, 1),
            "theory_score": round(theory_score, 1),
            "practice_score": round(practice_score, 1),
            "theory_weight": self.THEORY_WEIGHT,
            "practice_weight": self.PRACTICE_WEIGHT,
            "grade": self._get_grade(overall_score),
            "is_balanced": is_balanced,
            "score_difference": round(score_diff, 1),
            "comments": comments,
            "ready_for_real_practice": overall_score >= 80 and practice_score >= 80
        }

    def calculate_learning_efficiency(self,
                                      score: float,
                                      study_time_minutes: float,
                                      interaction_count: int) -> Dict:
        """
        計算學習效率指標

        Args:
            score: 分數 (0-100)
            study_time_minutes: 學習時間（分鐘）
            interaction_count: 互動次數

        Returns:
            效率指標
        """
        if study_time_minutes <= 0 or interaction_count <= 0:
            return {
                "efficiency_score": 0,
                "score_per_hour": 0,
                "score_per_interaction": 0,
                "efficiency_rating": "無資料"
            }

        # 每小時得分
        score_per_hour = score / (study_time_minutes / 60)

        # 每次互動得分
        score_per_interaction = score / interaction_count

        # 綜合效率分數 (考慮時間和互動次數)
        efficiency_score = math.sqrt(score_per_hour * score_per_interaction)

        # 效率評級
        if efficiency_score >= 30:
            efficiency_rating = "高效"
        elif efficiency_score >= 20:
            efficiency_rating = "良好"
        elif efficiency_score >= 10:
            efficiency_rating = "普通"
        else:
            efficiency_rating = "需改善"

        return {
            "efficiency_score": round(efficiency_score, 1),
            "score_per_hour": round(score_per_hour, 1),
            "score_per_interaction": round(score_per_interaction, 2),
            "efficiency_rating": efficiency_rating,
            "study_time_hours": round(study_time_minutes / 60, 1)
        }

    def _get_grade(self, score: float) -> str:
        """根據分數獲取等級"""
        for grade, threshold in self.GRADE_THRESHOLDS.items():
            if score >= threshold:
                return grade
        return "不及格"

    def _identify_strengths(self, topic_breakdown: Dict) -> List[str]:
        """識別優勢主題"""
        strengths = []
        for topic, data in topic_breakdown.items():
            if data["accuracy"] >= 0.8 and data["total"] >= 3:
                strengths.append(topic)
        return strengths

    def _identify_weaknesses(self, topic_breakdown: Dict) -> List[str]:
        """識別弱點主題"""
        weaknesses = []
        for topic, data in topic_breakdown.items():
            if data["accuracy"] < 0.6 and data["total"] >= 3:
                weaknesses.append(topic)
        return weaknesses

    def _empty_evaluation(self, eval_type: str) -> Dict:
        """返回空評估結果"""
        return {
            "score": 0,
            "grade": "無資料",
            "type": eval_type,
            "message": "無足夠資料進行評估"
        }

    def generate_improvement_suggestions(self, evaluation: Dict) -> List[str]:
        """
        生成改進建議

        Args:
            evaluation: 評估結果

        Returns:
            改進建議列表
        """
        suggestions = []

        score = evaluation.get("overall_score", evaluation.get("score", 0))

        # 根據總分給建議
        if score < 60:
            suggestions.append("整體表現需要大幅提升，建議系統性地重新學習所有內容。")

        # 理論與實作平衡
        if not evaluation.get("is_balanced", True):
            theory_score = evaluation.get("theory_score", 0)
            practice_score = evaluation.get("practice_score", 0)

            if theory_score < practice_score - 15:
                suggestions.append("理論知識較弱，建議加強理論學習，完善知識體系。")
            elif practice_score < theory_score - 15:
                suggestions.append("實作能力需要提升，建議增加實際操作練習。")

        # 診斷能力
        diagnosis_score = evaluation.get("diagnosis_score", 100)
        if diagnosis_score < 70:
            suggestions.append("故障診斷能力需要加強，建議複習故障分析方法論。")

        # 操作準確性
        operation_score = evaluation.get("operation_score", 100)
        if operation_score < 70:
            suggestions.append("操作準確性不足，建議熟悉標準操作流程（SOP）。")

        # 時間效率
        time_efficiency = evaluation.get("time_efficiency_score", 100)
        if time_efficiency < 60:
            suggestions.append("處理速度較慢，建議通過多次練習提高操作熟練度。")

        # 專家諮詢頻率
        expert_consults = evaluation.get("expert_consults", 0)
        total_operations = evaluation.get("total_operations", 1)
        consult_rate = expert_consults / total_operations if total_operations > 0 else 0

        if consult_rate > 0.5:
            suggestions.append("過度依賴專家協助，建議先嘗試獨立思考再尋求幫助。")
        elif consult_rate < 0.1 and operation_score < 80:
            suggestions.append("遇到困難時建議適時尋求專家指導，避免走彎路。")

        # 弱點主題
        weaknesses = evaluation.get("weaknesses", [])
        if weaknesses:
            suggestions.append(f"需要加強以下主題：{', '.join(weaknesses[:3])}。")

        if not suggestions:
            suggestions.append("表現良好！繼續保持，可以嘗試更高難度的挑戰。")

        return suggestions

    def save_evaluation(self, student_id: str, evaluation: Dict):
        """
        儲存評估結果

        Args:
            student_id: 學員ID
            evaluation: 評估結果
        """
        eval_file = self.data_dir / f"{student_id}_evaluations.jsonl"

        record = {
            "timestamp": datetime.now().isoformat(),
            "student_id": student_id,
            "evaluation": evaluation
        }

        with open(eval_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')


# 使用範例
if __name__ == "__main__":
    print("=== Evaluation System 使用範例 ===\n")

    # 1. 創建評分系統
    evaluator = EvaluationSystem()

    # 2. 模擬理論測驗結果
    theory_test_results = [
        {"question": "CVD是什麼?", "is_correct": True, "topic": "CVD", "difficulty": "easy"},
        {"question": "真空系統原理?", "is_correct": True, "topic": "真空系統", "difficulty": "medium"},
        {"question": "溫控PID參數?", "is_correct": False, "topic": "溫控", "difficulty": "hard"},
        {"question": "對準系統組成?", "is_correct": True, "topic": "對準系統", "difficulty": "medium"},
        {"question": "冷卻系統維護?", "is_correct": True, "topic": "冷卻系統", "difficulty": "easy"},
        {"question": "CVD反應機制?", "is_correct": False, "topic": "CVD", "difficulty": "hard"},
        {"question": "真空洩漏檢測?", "is_correct": True, "topic": "真空系統", "difficulty": "medium"},
        {"question": "溫度控制方法?", "is_correct": True, "topic": "溫控", "difficulty": "medium"},
        {"question": "光學系統維護?", "is_correct": True, "topic": "光學系統", "difficulty": "easy"},
        {"question": "壓力控制原理?", "is_correct": False, "topic": "壓力控制", "difficulty": "hard"}
    ]

    # 3. 評估理論測驗
    print("評估理論測驗...")
    theory_eval = evaluator.evaluate_theory_test(theory_test_results)

    print(f"理論分數: {theory_eval['score']} 分")
    print(f"等級: {theory_eval['grade']}")
    print(f"正確率: {theory_eval['accuracy']}%")
    print(f"優勢主題: {theory_eval['strengths']}")
    print(f"弱點主題: {theory_eval['weaknesses']}")
    print()

    # 4. 模擬實作訓練資料
    practice_session = {
        "scenario_info": {
            "name": "冷卻系統故障",
            "expected_time_minutes": 30
        },
        "diagnosis": {
            "student_diagnosis": "冷卻水流量不足",
            "correct_diagnosis": "冷卻水流量不足",
            "is_correct": True
        },
        "operations": [
            {"operation": "檢查冷卻水流量", "is_correct": True, "timestamp": "2024-01-01T10:00:00"},
            {"operation": "檢查過濾網", "is_correct": True, "timestamp": "2024-01-01T10:05:00"},
            {"operation": "清理過濾網", "is_correct": True, "timestamp": "2024-01-01T10:10:00"},
            {"operation": "重新啟動冷卻系統", "is_correct": True, "timestamp": "2024-01-01T10:15:00"},
            {"operation": "驗證溫度恢復正常", "is_correct": False, "timestamp": "2024-01-01T10:20:00"}
        ],
        "start_time": "2024-01-01T10:00:00",
        "end_time": "2024-01-01T10:25:00",
        "expert_consults": 1
    }

    # 5. 評估實作訓練
    print("評估實作訓練...")
    practice_eval = evaluator.evaluate_practice_session(practice_session)

    print(f"實作分數: {practice_eval['score']} 分")
    print(f"等級: {practice_eval['grade']}")
    print(f"診斷分數: {practice_eval['diagnosis_score']} 分")
    print(f"操作分數: {practice_eval['operation_score']} 分")
    print(f"時間效率: {practice_eval['time_efficiency_score']} 分")
    print(f"完成時間: {practice_eval['completion_time_minutes']} 分鐘")
    print()

    # 6. 綜合評估
    print("綜合評估...")
    overall_eval = evaluator.evaluate_overall(
        theory_score=theory_eval['score'],
        practice_score=practice_eval['score']
    )

    print(f"綜合分數: {overall_eval['overall_score']} 分")
    print(f"等級: {overall_eval['grade']}")
    print(f"是否均衡: {'是' if overall_eval['is_balanced'] else '否'}")
    print(f"可進入真機實習: {'是' if overall_eval['ready_for_real_practice'] else '否'}")
    print()

    print("評語:")
    for comment in overall_eval['comments']:
        print(f"  - {comment}")
    print()

    # 7. 學習效率分析
    print("學習效率分析...")
    efficiency = evaluator.calculate_learning_efficiency(
        score=overall_eval['overall_score'],
        study_time_minutes=120,
        interaction_count=25
    )

    print(f"效率分數: {efficiency['efficiency_score']}")
    print(f"效率評級: {efficiency['efficiency_rating']}")
    print(f"每小時得分: {efficiency['score_per_hour']}")
    print(f"每次互動得分: {efficiency['score_per_interaction']}")
    print()

    # 8. 生成改進建議
    print("改進建議:")
    suggestions = evaluator.generate_improvement_suggestions(overall_eval)
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}")
