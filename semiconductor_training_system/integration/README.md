# 整合模組 (Integration Modules)

本目錄包含整合理論學習和實作訓練的核心模組。

## 模組概覽

### 1. TrainingCoordinator (訓練協調器) ✅

**檔案**: `training_coordinator.py`

**功能**:
- 管理學員在理論學習和實作訓練之間的階段切換
- 判斷階段解鎖條件（理論 ≥70分、實作 ≥80分）
- 追蹤當前訓練狀態
- 資料持久化（JSON 格式）

**主要 API**:
```python
from integration.training_coordinator import TrainingCoordinator, TrainingStage

# 初始化
coordinator = TrainingCoordinator(student_id="S001")

# 檢查是否可進入實作訓練
can_enter, msg = coordinator.can_enter_practice()

# 更新分數
coordinator.update_theory_score(75)
coordinator.update_practice_score(85)

# 切換階段
success, msg = coordinator.enter_stage(TrainingStage.PRACTICE)

# 獲取整體進度
progress = coordinator.get_overall_progress()
```

**解鎖條件**:
- 階段 1 → 階段 2: 理論測驗 ≥ 70 分
- 階段 2 → 完成: 實作訓練 ≥ 80 分

---

### 2. ProgressTracker (進度追蹤器) ✅

**檔案**: `progress_tracker.py`

**功能**:
- 記錄所有學員互動（JSONL 格式）
- 統計學習數據（問題數、操作數、正確率等）
- 計算學習曲線（移動平均）
- 分析知識盲點（正確率 < 60% 且嘗試 ≥ 3 次）
- 生成完整學習報告

**主要 API**:
```python
from integration.progress_tracker import ProgressTracker, InteractionType

# 初始化
tracker = ProgressTracker(student_id="S001")

# 記錄互動
tracker.log_interaction(
    interaction_type=InteractionType.THEORY_QUESTION,
    data={"question": "什麼是CVD?", "answer": "化學氣相沉積", "topic": "CVD"},
    success=True
)

tracker.log_interaction(
    interaction_type=InteractionType.PRACTICE_OPERATION,
    data={"operation": "檢查冷卻水流量", "topic": "冷卻系統"},
    success=False
)

# 獲取學習曲線
learning_curve = tracker.get_learning_curve(window_size=10)

# 獲取知識盲點
knowledge_gaps = tracker.get_knowledge_gaps()

# 生成完整報告
report = tracker.generate_learning_report()

# 匯出 CSV
tracker.export_to_csv()
```

**互動類型**:
- `THEORY_QUESTION`: 理論問答
- `THEORY_TEST`: 理論測驗
- `PRACTICE_OPERATION`: 實作操作
- `EXPERT_CONSULT`: 專家諮詢
- `STAGE_SWITCH`: 階段切換

**資料格式**:

互動記錄 (JSONL):
```json
{
  "timestamp": "2024-01-01T10:15:30",
  "student_id": "S001",
  "type": "theory_question",
  "data": {"question": "...", "answer": "...", "topic": "CVD"},
  "success": true,
  "score": null
}
```

統計資料 (JSON):
```json
{
  "student_id": "S001",
  "total_interactions": 50,
  "theory_questions_asked": 20,
  "theory_questions_correct": 16,
  "practice_operations_count": 15,
  "practice_operations_success": 12,
  "expert_consults": 5
}
```

---

### 3. SmartRecommender (智能推薦器) ✅

**檔案**: `smart_recommender.py`

**功能**:
- 分析實作中的失敗操作
- 識別知識盲點
- 推薦理論複習主題
- 生成個性化學習路徑
- 評估學習優先級

**主要 API**:
```python
from integration.smart_recommender import SmartRecommender

# 初始化
recommender = SmartRecommender()

# 分析失敗操作
failed_ops = [
    {"operation": "檢查冷卻水流量", "topic": "冷卻系統"},
    {"operation": "調整真空壓力", "topic": "真空系統"}
]

failure_analysis = recommender.analyze_failed_operations(failed_ops)

# 分析知識盲點
knowledge_gaps = [
    {"topic": "冷卻系統", "accuracy": 35, "total_attempts": 6}
]

gap_analysis = recommender.analyze_knowledge_gaps(knowledge_gaps)

# 生成推薦
recommendations = recommender.recommend_topics(
    failed_operations=failed_ops,
    knowledge_gaps=knowledge_gaps,
    max_recommendations=5
)

# 生成學習路徑
learning_path = recommender.generate_learning_path(recommendations)

# 檢查是否應該觸發推薦
should_trigger = recommender.should_trigger_recommendation(
    recent_failures=failed_ops,
    failure_threshold=3
)
```

**操作到主題映射**:

系統內建 10 大類別映射：
- **冷卻系統**: 冷卻系統原理、熱管理基礎、過濾網維護
- **真空系統**: 真空系統原理、真空泵操作、洩漏檢測
- **對準系統**: 對準系統原理、機械穩定性、振動控制
- **光學系統**: 光學系統原理、鏡片清潔維護、光源管理
- **溫度控制**: 溫控系統原理、熱平衡原理、溫度感測器
- **壓力控制**: 壓力控制原理、氣體供應系統、壓力感測器
- **化學**: CVD 原理、化學反應、氣體化學
- **電氣**: 電氣系統原理、電源管理、電氣故障排除
- **機械**: 機械結構、傳動系統、機械故障診斷
- **安全**: 安全規範、緊急停機程序、SOP 標準

**優先級分類**:
- `critical`: 嚴重盲點（正確率 < 40% 且嘗試 ≥ 5）
- `high`: 高優先級（正確率 < 60% 且嘗試 ≥ 3，或高風險主題）
- `medium`: 中等優先級
- `low`: 低優先級

**觸發條件**:
- 連續失敗 ≥ 3 次
- 特定主題錯誤率 > 60%
- 學員主動請求

---

### 4. EvaluationSystem (評分系統) ✅

**檔案**: `evaluation_system.py`

**功能**:
- 理論測驗評分（考慮難度加權）
- 實作訓練評分（診斷、操作、時間效率）
- 綜合評估（理論 30% + 實作 70%）
- 學習效率計算
- 生成改進建議

**主要 API**:
```python
from integration.evaluation_system import EvaluationSystem

# 初始化
evaluator = EvaluationSystem()

# 評估理論測驗
theory_test_results = [
    {
        "question": "CVD是什麼?",
        "is_correct": True,
        "topic": "CVD",
        "difficulty": "easy"
    },
    # ...
]

theory_eval = evaluator.evaluate_theory_test(theory_test_results)

# 評估實作訓練
practice_session = {
    "scenario_info": {"name": "冷卻系統故障", "expected_time_minutes": 30},
    "diagnosis": {
        "student_diagnosis": "冷卻水流量不足",
        "correct_diagnosis": "冷卻水流量不足",
        "is_correct": True
    },
    "operations": [
        {"operation": "檢查冷卻水流量", "is_correct": True},
        # ...
    ],
    "start_time": "2024-01-01T10:00:00",
    "end_time": "2024-01-01T10:25:00",
    "expert_consults": 1
}

practice_eval = evaluator.evaluate_practice_session(practice_session)

# 綜合評估
overall_eval = evaluator.evaluate_overall(
    theory_score=theory_eval['score'],
    practice_score=practice_eval['score']
)

# 學習效率分析
efficiency = evaluator.calculate_learning_efficiency(
    score=overall_eval['overall_score'],
    study_time_minutes=120,
    interaction_count=25
)

# 生成改進建議
suggestions = evaluator.generate_improvement_suggestions(overall_eval)

# 儲存評估結果
evaluator.save_evaluation(student_id="S001", evaluation=overall_eval)
```

**評分公式**:

**理論分數**:
```
基本分數 = 正確題數 / 總題數 × 100

難度加權分數 = Σ(正確題 × 難度權重) / Σ(所有題 × 難度權重) × 100

難度權重:
- easy: 0.8
- medium: 1.0
- hard: 1.3
```

**實作分數**:
```
實作分數 = (
    診斷準確度 × 0.4 +
    操作正確性 × 0.4 +
    處理速度 × 0.2
) × 100

診斷準確度:
- 完全正確: 1.0
- 相似度 > 0.7: 0.7
- 相似度 > 0.5: 0.5
- 相似度 > 0.3: 0.3
- 否則: 0.0

操作正確性:
- 基本準確率 + 順序獎勵（前3步全對 +0.1）

處理速度:
- 時間比率 ≤ 0.8: 1.0 (提前完成)
- 時間比率 ≤ 1.0: 0.9 (按時完成)
- 時間比率 ≤ 1.2: 0.7 (略超時)
- 時間比率 ≤ 1.5: 0.5 (明顯超時)
- 時間比率 > 1.5: max(0.2, 1.0/比率)
```

**綜合分數**:
```
綜合分數 = 理論分數 × 0.3 + 實作分數 × 0.7
```

**等級標準**:
- 優秀: ≥ 90
- 良好: ≥ 80
- 及格: ≥ 70
- 待加強: ≥ 60
- 不及格: < 60

**學習效率**:
```
效率分數 = √(每小時得分 × 每次互動得分)

效率評級:
- 高效: ≥ 30
- 良好: ≥ 20
- 普通: ≥ 10
- 需改善: < 10
```

---

## 資料流架構

```
學員登入
    ↓
TrainingCoordinator 載入狀態
    ↓
ProgressTracker 開始記錄
    ↓
┌─────────────────────────────────────┐
│ 階段 1: 理論學習                      │
│  - 理論問答 (記錄到 ProgressTracker)  │
│  - 知識測驗                          │
│  - EvaluationSystem 評分             │
│  - 達到 70 分                        │
└─────────────────────────────────────┘
    ↓ (TrainingCoordinator 解鎖)
┌─────────────────────────────────────┐
│ 階段 2: 實作訓練                      │
│  - 故障診斷                          │
│  - 操作執行 (記錄到 ProgressTracker)  │
│  - 失敗 → SmartRecommender 推薦      │
│  - EvaluationSystem 評分             │
│  - 達到 80 分                        │
└─────────────────────────────────────┘
    ↓
TrainingCoordinator 標記完成
    ↓
ProgressTracker 生成報告
```

## 整合使用範例

```python
from integration.training_coordinator import TrainingCoordinator, TrainingStage
from integration.progress_tracker import ProgressTracker, InteractionType
from integration.smart_recommender import SmartRecommender
from integration.evaluation_system import EvaluationSystem

# 初始化所有模組
student_id = "S001"
coordinator = TrainingCoordinator(student_id)
tracker = ProgressTracker(student_id)
recommender = SmartRecommender()
evaluator = EvaluationSystem()

# === 階段 1: 理論學習 ===
while not coordinator.theory_completed:
    # 學員提問
    question = "什麼是CVD?"
    answer = "化學氣相沉積..."

    # 記錄互動
    tracker.log_interaction(
        InteractionType.THEORY_QUESTION,
        {"question": question, "answer": answer, "topic": "CVD"},
        success=True
    )

    # 定期測驗
    if tracker.stats["theory_questions_asked"] % 10 == 0:
        # 進行測驗
        test_results = [...]
        theory_eval = evaluator.evaluate_theory_test(test_results)

        # 更新分數
        msg = coordinator.update_theory_score(theory_eval['score'])
        print(msg)

# === 階段 2: 實作訓練 ===
can_enter, msg = coordinator.can_enter_practice()
if can_enter:
    coordinator.enter_stage(TrainingStage.PRACTICE)

    while not coordinator.practice_completed:
        # 學員操作
        operation = "檢查冷卻水流量"
        result = {"success": False}

        # 記錄互動
        tracker.log_interaction(
            InteractionType.PRACTICE_OPERATION,
            {"operation": operation, "topic": "冷卻系統"},
            success=result["success"]
        )

        # 檢查是否需要推薦
        recent_failures = tracker.get_interactions_by_type(
            InteractionType.PRACTICE_OPERATION
        )[-3:]

        if recommender.should_trigger_recommendation(recent_failures):
            # 推薦複習主題
            recommendations = recommender.recommend_topics(
                failed_operations=recent_failures,
                knowledge_gaps=tracker.get_knowledge_gaps()
            )

            print("建議複習:")
            for rec in recommendations:
                print(f"  - {rec['recommendation']}")

        # 場景完成後評分
        if scenario_completed:
            practice_eval = evaluator.evaluate_practice_session(session_data)
            msg = coordinator.update_practice_score(practice_eval['score'])
            print(msg)

# === 生成最終報告 ===
# 學習報告
learning_report = tracker.generate_learning_report()

# 綜合評估
overall_eval = evaluator.evaluate_overall(
    theory_score=coordinator.theory_score,
    practice_score=coordinator.practice_score
)

# 學習效率
efficiency = evaluator.calculate_learning_efficiency(
    score=overall_eval['overall_score'],
    study_time_minutes=learning_report['study_time_minutes'],
    interaction_count=tracker.stats['total_interactions']
)

# 改進建議
suggestions = evaluator.generate_improvement_suggestions(overall_eval)

print(f"綜合分數: {overall_eval['overall_score']} 分")
print(f"等級: {overall_eval['grade']}")
print(f"學習效率: {efficiency['efficiency_rating']}")
print(f"可進入真機實習: {overall_eval['ready_for_real_practice']}")
```

## 測試方法

每個模組都包含 `if __name__ == "__main__"` 測試代碼，可單獨執行：

```bash
# 測試訓練協調器
python integration/training_coordinator.py

# 測試進度追蹤器
python integration/progress_tracker.py

# 測試智能推薦器
python integration/smart_recommender.py

# 測試評分系統
python integration/evaluation_system.py
```

## 資料儲存位置

```
data/
├── student_progress/
│   ├── S001_state.json              # 訓練狀態 (TrainingCoordinator)
│   ├── S001_stats.json              # 統計資料 (ProgressTracker)
│   ├── S001_interactions.jsonl      # 互動記錄 (ProgressTracker)
│   └── S001_interactions.csv        # 匯出的 CSV (ProgressTracker)
│
└── evaluations/
    └── S001_evaluations.jsonl       # 評估記錄 (EvaluationSystem)
```

## 後續整合任務

1. ✅ 完成核心整合模組
2. ⬜ 整合到統一 Gradio 介面
3. ⬜ 建立階段 1 理論 BOT (RAG)
4. ⬜ AI/LLM 整合
5. ⬜ 完整系統測試

---

**開發日期**: 2024-2025
**狀態**: 核心模組已完成 ✅
