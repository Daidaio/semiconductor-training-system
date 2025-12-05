# -*- coding: utf-8 -*-
"""
進度追蹤器 (Progress Tracker)
記錄學員所有互動、評估表現、生成學習報告
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path
import pandas as pd


class InteractionType:
    """互動類型"""
    THEORY_QUESTION = "theory_question"  # 理論問答
    THEORY_TEST = "theory_test"  # 理論測驗
    PRACTICE_OPERATION = "practice_operation"  # 實作操作
    EXPERT_CONSULT = "expert_consult"  # 專家諮詢
    STAGE_SWITCH = "stage_switch"  # 階段切換


class ProgressTracker:
    """
    進度追蹤器

    職責：
    1. 記錄所有學員互動
    2. 統計學習數據
    3. 分析學習模式
    4. 生成學習報告

    使用範例：
    ```python
    tracker = ProgressTracker(student_id="S001")

    # 記錄互動
    tracker.log_interaction(
        interaction_type=InteractionType.THEORY_QUESTION,
        data={"question": "什麼是CVD?", "answer": "..."}
    )

    # 生成報告
    report = tracker.generate_learning_report()
    ```
    """

    def __init__(self, student_id: str, data_dir: str = "data/student_progress"):
        """
        初始化進度追蹤器

        Args:
            student_id: 學員 ID
            data_dir: 資料儲存目錄
        """
        self.student_id = student_id
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 互動記錄檔案
        self.interaction_file = self.data_dir / f"{student_id}_interactions.jsonl"

        # 統計資料
        self.stats = self._load_statistics()

    def _load_statistics(self) -> Dict:
        """載入統計資料"""
        stats_file = self.data_dir / f"{self.student_id}_stats.json"

        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "student_id": self.student_id,
                "total_interactions": 0,
                "theory_questions_asked": 0,
                "theory_questions_correct": 0,
                "theory_tests_taken": 0,
                "practice_operations_count": 0,
                "practice_operations_success": 0,
                "expert_consults": 0,
                "total_study_time_minutes": 0,
                "created_at": datetime.now().isoformat()
            }

    def _save_statistics(self):
        """儲存統計資料"""
        stats_file = self.data_dir / f"{self.student_id}_stats.json"

        self.stats["last_updated"] = datetime.now().isoformat()

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

    def log_interaction(self, interaction_type: str, data: Dict,
                       success: Optional[bool] = None, score: Optional[float] = None):
        """
        記錄互動

        Args:
            interaction_type: 互動類型 (使用 InteractionType 常數)
            data: 互動資料
            success: 是否成功 (可選)
            score: 分數 (可選)
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "student_id": self.student_id,
            "type": interaction_type,
            "data": data,
            "success": success,
            "score": score
        }

        # 寫入 JSONL 檔案（每行一個 JSON）
        with open(self.interaction_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(interaction, ensure_ascii=False) + '\n')

        # 更新統計
        self._update_statistics(interaction_type, success, score)

    def _update_statistics(self, interaction_type: str,
                          success: Optional[bool], score: Optional[float]):
        """更新統計資料"""
        self.stats["total_interactions"] += 1

        if interaction_type == InteractionType.THEORY_QUESTION:
            self.stats["theory_questions_asked"] += 1
            if success:
                self.stats["theory_questions_correct"] += 1

        elif interaction_type == InteractionType.THEORY_TEST:
            self.stats["theory_tests_taken"] += 1

        elif interaction_type == InteractionType.PRACTICE_OPERATION:
            self.stats["practice_operations_count"] += 1
            if success:
                self.stats["practice_operations_success"] += 1

        elif interaction_type == InteractionType.EXPERT_CONSULT:
            self.stats["expert_consults"] += 1

        self._save_statistics()

    def get_all_interactions(self) -> List[Dict]:
        """
        獲取所有互動記錄

        Returns:
            互動記錄列表
        """
        if not self.interaction_file.exists():
            return []

        interactions = []
        with open(self.interaction_file, 'r', encoding='utf-8') as f:
            for line in f:
                interactions.append(json.loads(line))

        return interactions

    def get_interactions_by_type(self, interaction_type: str) -> List[Dict]:
        """
        根據類型獲取互動記錄

        Args:
            interaction_type: 互動類型

        Returns:
            該類型的互動記錄
        """
        all_interactions = self.get_all_interactions()
        return [i for i in all_interactions if i['type'] == interaction_type]

    def get_learning_curve(self, window_size: int = 10) -> Dict:
        """
        計算學習曲線

        Args:
            window_size: 移動平均窗口大小

        Returns:
            {
                "theory_accuracy": [...],  # 理論正確率趨勢
                "practice_success_rate": [...]  # 實作成功率趨勢
            }
        """
        interactions = self.get_all_interactions()

        # 理論問題正確率
        theory_questions = [i for i in interactions
                           if i['type'] == InteractionType.THEORY_QUESTION]

        theory_curve = []
        for i in range(len(theory_questions)):
            start = max(0, i - window_size + 1)
            window = theory_questions[start:i + 1]
            correct = sum(1 for q in window if q.get('success'))
            accuracy = correct / len(window) if window else 0
            theory_curve.append(round(accuracy * 100, 1))

        # 實作操作成功率
        practice_ops = [i for i in interactions
                       if i['type'] == InteractionType.PRACTICE_OPERATION]

        practice_curve = []
        for i in range(len(practice_ops)):
            start = max(0, i - window_size + 1)
            window = practice_ops[start:i + 1]
            success = sum(1 for op in window if op.get('success'))
            success_rate = success / len(window) if window else 0
            practice_curve.append(round(success_rate * 100, 1))

        return {
            "theory_accuracy": theory_curve,
            "practice_success_rate": practice_curve
        }

    def get_knowledge_gaps(self) -> List[Dict]:
        """
        分析知識盲點

        Returns:
            知識盲點列表，每項包含：
            {
                "topic": str,  # 主題
                "error_count": int,  # 錯誤次數
                "total_attempts": int,  # 總嘗試次數
                "accuracy": float  # 正確率
            }
        """
        interactions = self.get_all_interactions()

        # 統計各主題的表現
        topic_stats = {}

        for interaction in interactions:
            if interaction['type'] in [InteractionType.THEORY_QUESTION,
                                      InteractionType.PRACTICE_OPERATION]:
                # 從 data 中提取主題
                topic = interaction.get('data', {}).get('topic', 'unknown')

                if topic not in topic_stats:
                    topic_stats[topic] = {"correct": 0, "total": 0}

                topic_stats[topic]["total"] += 1
                if interaction.get('success'):
                    topic_stats[topic]["correct"] += 1

        # 找出表現較差的主題
        knowledge_gaps = []
        for topic, stats in topic_stats.items():
            accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0

            if accuracy < 0.6 and stats["total"] >= 3:  # 正確率低於 60% 且嘗試次數 >= 3
                knowledge_gaps.append({
                    "topic": topic,
                    "error_count": stats["total"] - stats["correct"],
                    "total_attempts": stats["total"],
                    "accuracy": round(accuracy * 100, 1)
                })

        # 按錯誤次數排序
        knowledge_gaps.sort(key=lambda x: x["error_count"], reverse=True)

        return knowledge_gaps

    def calculate_study_time(self) -> float:
        """
        計算總學習時間（分鐘）

        Returns:
            學習時間（分鐘）
        """
        interactions = self.get_all_interactions()

        if len(interactions) < 2:
            return 0

        # 從第一個到最後一個互動的時間差
        first_time = datetime.fromisoformat(interactions[0]["timestamp"])
        last_time = datetime.fromisoformat(interactions[-1]["timestamp"])

        duration_minutes = (last_time - first_time).total_seconds() / 60

        return round(duration_minutes, 1)

    def generate_learning_report(self) -> Dict:
        """
        生成完整學習報告

        Returns:
            {
                "student_id": str,
                "report_date": str,
                "study_time_minutes": float,
                "statistics": {...},
                "performance": {...},
                "learning_curve": {...},
                "knowledge_gaps": [...],
                "recommendations": [...]
            }
        """
        # 基本統計
        statistics = self.stats.copy()
        statistics["study_time_minutes"] = self.calculate_study_time()

        # 表現指標
        theory_accuracy = (
            statistics["theory_questions_correct"] / statistics["theory_questions_asked"]
            if statistics["theory_questions_asked"] > 0 else 0
        )

        practice_success_rate = (
            statistics["practice_operations_success"] / statistics["practice_operations_count"]
            if statistics["practice_operations_count"] > 0 else 0
        )

        performance = {
            "theory_accuracy": round(theory_accuracy * 100, 1),
            "practice_success_rate": round(practice_success_rate * 100, 1),
            "expert_consult_frequency": (
                statistics["expert_consults"] / statistics["total_interactions"]
                if statistics["total_interactions"] > 0 else 0
            )
        }

        # 學習曲線
        learning_curve = self.get_learning_curve()

        # 知識盲點
        knowledge_gaps = self.get_knowledge_gaps()

        # 改進建議
        recommendations = self._generate_recommendations(
            performance, knowledge_gaps, statistics
        )

        return {
            "student_id": self.student_id,
            "report_date": datetime.now().isoformat(),
            "study_time_minutes": statistics["study_time_minutes"],
            "statistics": statistics,
            "performance": performance,
            "learning_curve": learning_curve,
            "knowledge_gaps": knowledge_gaps,
            "recommendations": recommendations
        }

    def _generate_recommendations(self, performance: Dict,
                                 knowledge_gaps: List[Dict],
                                 statistics: Dict) -> List[str]:
        """生成改進建議"""
        recommendations = []

        # 理論正確率建議
        if performance["theory_accuracy"] < 60:
            recommendations.append(
                "建議加強理論學習，當前理論正確率較低。"
                "可以多花時間在基礎概念的理解上。"
            )
        elif performance["theory_accuracy"] < 80:
            recommendations.append(
                "理論基礎不錯，但仍有進步空間。"
                "建議針對錯誤的問題進行深入復習。"
            )

        # 實作成功率建議
        if performance["practice_success_rate"] < 60:
            recommendations.append(
                "實作操作需要加強，建議多練習常見故障排除流程。"
            )

        # 知識盲點建議
        if knowledge_gaps:
            top_gaps = [gap["topic"] for gap in knowledge_gaps[:3]]
            recommendations.append(
                f"發現以下知識盲點：{', '.join(top_gaps)}。"
                "建議優先複習這些主題。"
            )

        # 專家諮詢建議
        consult_rate = performance["expert_consult_frequency"]
        if consult_rate < 0.1:
            recommendations.append(
                "建議適時尋求 AI 專家的協助，不要獨自摸索太久。"
            )
        elif consult_rate > 0.5:
            recommendations.append(
                "可以嘗試先獨立思考再尋求專家建議，培養獨立解決問題的能力。"
            )

        # 學習時間建議
        if statistics["study_time_minutes"] < 30:
            recommendations.append(
                "投入的學習時間較少，建議增加練習時間以鞏固知識。"
            )

        if not recommendations:
            recommendations.append(
                "表現優秀！繼續保持良好的學習態度和習慣。"
            )

        return recommendations

    def export_to_csv(self, output_file: Optional[str] = None) -> str:
        """
        匯出互動記錄為 CSV

        Args:
            output_file: 輸出檔案路徑（可選）

        Returns:
            輸出檔案路徑
        """
        if output_file is None:
            output_file = str(self.data_dir / f"{self.student_id}_interactions.csv")

        interactions = self.get_all_interactions()

        if not interactions:
            return output_file

        # 轉換為 DataFrame
        df = pd.DataFrame(interactions)

        # 展開 data 欄位
        data_df = pd.json_normalize(df['data'])
        df = df.drop('data', axis=1)
        df = pd.concat([df, data_df], axis=1)

        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        return output_file


# 使用範例
if __name__ == "__main__":
    print("=== Progress Tracker 使用範例 ===\n")

    # 1. 創建追蹤器
    tracker = ProgressTracker(student_id="S001")

    # 2. 記錄一些互動
    print("記錄互動...")

    # 理論問答
    tracker.log_interaction(
        interaction_type=InteractionType.THEORY_QUESTION,
        data={"topic": "CVD", "question": "什麼是CVD?", "answer": "化學氣相沉積"},
        success=True
    )

    # 實作操作
    tracker.log_interaction(
        interaction_type=InteractionType.PRACTICE_OPERATION,
        data={"topic": "冷卻系統", "operation": "檢查冷卻水流量"},
        success=True
    )

    tracker.log_interaction(
        interaction_type=InteractionType.PRACTICE_OPERATION,
        data={"topic": "真空系統", "operation": "檢查真空壓力"},
        success=False
    )

    # 3. 查看統計
    print("\n統計資料：")
    print(f"總互動次數：{tracker.stats['total_interactions']}")
    print(f"理論問題數：{tracker.stats['theory_questions_asked']}")
    print(f"實作操作數：{tracker.stats['practice_operations_count']}")

    # 4. 生成報告
    print("\n生成學習報告...")
    report = tracker.generate_learning_report()

    print(f"\n學習時間：{report['study_time_minutes']} 分鐘")
    print(f"理論正確率：{report['performance']['theory_accuracy']}%")
    print(f"實作成功率：{report['performance']['practice_success_rate']}%")

    print("\n改進建議：")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")
