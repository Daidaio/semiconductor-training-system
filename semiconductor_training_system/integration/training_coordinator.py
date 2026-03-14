# -*- coding: utf-8 -*-
"""
訓練協調器 (Training Coordinator)
管理學員在理論學習和實作訓練之間的流程控制
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path


class TrainingStage:
    """訓練階段定義"""
    THEORY = "stage1_theory"
    PRACTICE = "stage2_practice"
    COMPLETED = "completed"


class TrainingCoordinator:
    """
    訓練協調器

    職責：
    1. 管理學員訓練階段切換
    2. 判斷階段解鎖條件
    3. 追蹤當前訓練狀態
    4. 處理階段間的資料傳遞

    使用範例：
    ```python
    coordinator = TrainingCoordinator(student_id="S001")

    # 檢查是否可以進入實作訓練
    can_practice, message = coordinator.can_enter_practice()

    if can_practice:
        coordinator.enter_stage(TrainingStage.PRACTICE)
    ```
    """

    # 階段解鎖條件
    THEORY_PASS_SCORE = 70  # 理論測驗及格分數
    PRACTICE_PASS_SCORE = 80  # 實作訓練及格分數

    def __init__(self, student_id: str, data_dir: str = "data/student_progress"):
        """
        初始化訓練協調器

        Args:
            student_id: 學員 ID
            data_dir: 學員進度資料儲存目錄
        """
        self.student_id = student_id
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 學員狀態
        self.student_state = self._load_student_state()

        # 當前階段
        self.current_stage = self.student_state.get("current_stage", TrainingStage.THEORY)

        # 階段分數
        self.theory_score = self.student_state.get("theory_score", 0)
        self.practice_score = self.student_state.get("practice_score", 0)

        # 階段完成狀態
        self.theory_completed = self.student_state.get("theory_completed", False)
        self.practice_completed = self.student_state.get("practice_completed", False)

    def _load_student_state(self) -> Dict:
        """載入學員狀態"""
        state_file = self.data_dir / f"{self.student_id}_state.json"

        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 初始狀態
            return {
                "student_id": self.student_id,
                "current_stage": TrainingStage.THEORY,
                "theory_score": 0,
                "practice_score": 0,
                "theory_completed": False,
                "practice_completed": False,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }

    def _save_student_state(self):
        """儲存學員狀態"""
        state_file = self.data_dir / f"{self.student_id}_state.json"

        self.student_state.update({
            "current_stage": self.current_stage,
            "theory_score": self.theory_score,
            "practice_score": self.practice_score,
            "theory_completed": self.theory_completed,
            "practice_completed": self.practice_completed,
            "last_updated": datetime.now().isoformat()
        })

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(self.student_state, f, ensure_ascii=False, indent=2)

    def can_enter_practice(self) -> Tuple[bool, str]:
        """
        檢查是否可以進入實作訓練

        Returns:
            (can_enter, message):
                - can_enter: 是否可以進入
                - message: 說明訊息
        """
        if self.theory_completed:
            return True, "已通過理論測驗，可以進入實作訓練"

        if self.theory_score >= self.THEORY_PASS_SCORE:
            return True, f"理論測驗分數 {self.theory_score} 分，已達標準 (>= {self.THEORY_PASS_SCORE} 分)"

        return False, f"理論測驗分數 {self.theory_score} 分，尚未達標 (需 >= {self.THEORY_PASS_SCORE} 分)"

    def enter_stage(self, stage: str) -> Tuple[bool, str]:
        """
        進入指定訓練階段

        Args:
            stage: 訓練階段 (TrainingStage.THEORY 或 TrainingStage.PRACTICE)

        Returns:
            (success, message):
                - success: 是否成功進入
                - message: 說明訊息
        """
        if stage == TrainingStage.THEORY:
            # 可以隨時回到理論學習
            self.current_stage = TrainingStage.THEORY
            self._save_student_state()
            return True, "進入階段 1：理論學習"

        elif stage == TrainingStage.PRACTICE:
            # 檢查是否可以進入實作訓練
            can_enter, message = self.can_enter_practice()

            if can_enter:
                self.current_stage = TrainingStage.PRACTICE
                self._save_student_state()
                return True, "進入階段 2：實作訓練"
            else:
                return False, f"無法進入實作訓練：{message}"

        else:
            return False, f"未知的訓練階段：{stage}"

    def update_theory_score(self, score: float) -> str:
        """
        更新理論測驗分數

        Args:
            score: 測驗分數 (0-100)

        Returns:
            結果訊息
        """
        self.theory_score = score

        # 檢查是否通過
        if score >= self.THEORY_PASS_SCORE:
            self.theory_completed = True
            message = f"理論測驗通過！分數：{score} 分。可以進入實作訓練了。"
        else:
            message = f"理論測驗分數：{score} 分。需要 {self.THEORY_PASS_SCORE} 分以上才能進入實作訓練。"

        self._save_student_state()
        return message

    def update_practice_score(self, score: float) -> str:
        """
        更新實作訓練分數

        Args:
            score: 訓練分數 (0-100)

        Returns:
            結果訊息
        """
        self.practice_score = score

        # 檢查是否通過
        if score >= self.PRACTICE_PASS_SCORE:
            self.practice_completed = True
            self.current_stage = TrainingStage.COMPLETED
            message = f"實作訓練通過！分數：{score} 分。已完成系統訓練，可進入真機實習。"
        else:
            message = f"實作訓練分數：{score} 分。需要 {self.PRACTICE_PASS_SCORE} 分以上才算完成訓練。"

        self._save_student_state()
        return message

    def get_overall_progress(self) -> Dict:
        """
        獲取整體訓練進度

        Returns:
            {
                "current_stage": str,
                "theory_score": float,
                "practice_score": float,
                "theory_completed": bool,
                "practice_completed": bool,
                "overall_completion": float,  # 整體完成度 (0-100)
                "can_enter_practice": bool,
                "next_step": str  # 下一步建議
            }
        """
        can_practice, _ = self.can_enter_practice()

        # 計算整體完成度
        theory_weight = 0.3
        practice_weight = 0.7

        overall_completion = (
            (self.theory_score / 100) * theory_weight * 100 +
            (self.practice_score / 100) * practice_weight * 100
        )

        # 決定下一步
        if self.practice_completed:
            next_step = "已完成所有訓練，可進入真機實習"
        elif self.current_stage == TrainingStage.PRACTICE:
            next_step = "繼續完成實作訓練"
        elif self.theory_completed:
            next_step = "進入階段 2：實作訓練"
        else:
            next_step = "完成理論測驗（需 >= 70 分）"

        return {
            "current_stage": self.current_stage,
            "theory_score": self.theory_score,
            "practice_score": self.practice_score,
            "theory_completed": self.theory_completed,
            "practice_completed": self.practice_completed,
            "overall_completion": round(overall_completion, 1),
            "can_enter_practice": can_practice,
            "next_step": next_step
        }

    def get_stage_status(self, stage: str) -> Dict:
        """
        獲取指定階段的狀態

        Args:
            stage: 訓練階段

        Returns:
            階段狀態資訊
        """
        if stage == TrainingStage.THEORY:
            return {
                "stage": TrainingStage.THEORY,
                "name": "階段 1：理論學習",
                "score": self.theory_score,
                "pass_score": self.THEORY_PASS_SCORE,
                "completed": self.theory_completed,
                "locked": False,  # 理論階段永遠不鎖定
                "status": "已完成" if self.theory_completed else "進行中"
            }

        elif stage == TrainingStage.PRACTICE:
            can_enter, message = self.can_enter_practice()

            return {
                "stage": TrainingStage.PRACTICE,
                "name": "階段 2：實作訓練",
                "score": self.practice_score,
                "pass_score": self.PRACTICE_PASS_SCORE,
                "completed": self.practice_completed,
                "locked": not can_enter,
                "lock_reason": message if not can_enter else None,
                "status": "已完成" if self.practice_completed else ("進行中" if can_enter else "未解鎖")
            }

        else:
            return {"error": f"Unknown stage: {stage}"}

    def recommend_review_topics(self, failed_operations: list) -> list:
        """
        根據實作失敗操作推薦理論複習主題

        Args:
            failed_operations: 失敗的操作列表

        Returns:
            推薦的理論主題列表
        """
        # 操作到理論主題的映射
        operation_topic_mapping = {
            "冷卻": ["冷卻系統原理", "熱管理", "過濾網維護"],
            "真空": ["真空系統", "真空泵原理", "洩漏檢測"],
            "對準": ["對準系統", "機械穩定性", "振動控制"],
            "光學": ["光學系統", "鏡片清潔", "光源維護"],
            "溫度": ["溫控系統", "熱平衡", "溫度感測器"],
            "壓力": ["壓力控制", "氣體供應", "壓力感測器"],
            "停機": ["緊急停機程序", "安全規範", "SOP"],
        }

        recommended_topics = set()

        for operation in failed_operations:
            # 找出操作相關的關鍵字
            for keyword, topics in operation_topic_mapping.items():
                if keyword in operation:
                    recommended_topics.update(topics)

        return list(recommended_topics)

    def reset_progress(self):
        """重置學員進度（用於測試或重新開始）"""
        self.current_stage = TrainingStage.THEORY
        self.theory_score = 0
        self.practice_score = 0
        self.theory_completed = False
        self.practice_completed = False
        self._save_student_state()


# 使用範例
if __name__ == "__main__":
    print("=== Training Coordinator 使用範例 ===\n")

    # 1. 創建協調器
    coordinator = TrainingCoordinator(student_id="S001")

    # 2. 查看初始狀態
    progress = coordinator.get_overall_progress()
    print(f"當前階段：{progress['current_stage']}")
    print(f"下一步：{progress['next_step']}\n")

    # 3. 嘗試進入實作訓練（應該失敗）
    success, message = coordinator.enter_stage(TrainingStage.PRACTICE)
    print(f"嘗試進入實作訓練：{message}\n")

    # 4. 完成理論測驗
    result = coordinator.update_theory_score(75)
    print(f"理論測驗結果：{result}\n")

    # 5. 現在可以進入實作訓練了
    success, message = coordinator.enter_stage(TrainingStage.PRACTICE)
    print(f"進入實作訓練：{message}\n")

    # 6. 完成實作訓練
    result = coordinator.update_practice_score(85)
    print(f"實作訓練結果：{result}\n")

    # 7. 查看最終進度
    final_progress = coordinator.get_overall_progress()
    print(f"整體完成度：{final_progress['overall_completion']}%")
    print(f"狀態：{final_progress['next_step']}")
