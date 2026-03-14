# 整合訓練系統指南

## 系統概覽

本系統整合了**理論知識學習（階段1）**和**虛擬實作訓練（階段2）**，建立完整的三階段訓練體系。

```
階段 1: 理論知識學習 (Theory Bot)
    ↓ (需通過70分測驗)
階段 2: 虛擬實作訓練 (Simulation Training)
    ↓ (需達到80分)
階段 3: 真機實習 (產線實習)
```

## 專案結構

```
semiconductor_training_system/
├── stage1_theory/              # 階段 1：理論 BOT
│   ├── rag_engine.py          # RAG 檢索引擎
│   ├── question_bot.py        # 問答 BOT
│   ├── difficulty_adapter.py  # 難度自適應
│   └── knowledge_test.py      # 知識測驗
│
├── stage2_practice/           # 階段 2：實作訓練（已有）
│   ├── scenario_engine.py     # → core/scenario_engine.py
│   ├── digital_twin.py        # → core/digital_twin.py
│   ├── nlu_controller.py      # → core/natural_language_controller.py
│   └── ai_experts/            # → core/ai_expert_advisor.py
│
├── integration/               # 整合模組 ⭐
│   ├── training_coordinator.py    # 訓練協調器 ✅
│   ├── progress_tracker.py        # 進度追蹤 ✅
│   ├── smart_recommender.py       # 智能推薦
│   └── evaluation_system.py       # 評分系統
│
├── interface/
│   └── unified_gradio_app.py  # 統一介面
│
├── data/
│   ├── sop_documents/         # SOP 文件
│   ├── student_progress/      # 學員進度資料
│   └── secom_processed.csv    # SECOM 資料
│
├── main.py                    # 主程式入口
└── requirements.txt
```

## 已實作模組

### 1. TrainingCoordinator (訓練協調器)

**檔案**: `integration/training_coordinator.py`

**功能**:
- 管理學員訓練階段切換
- 判斷階段解鎖條件（理論70分、實作80分）
- 追蹤當前訓練狀態
- 資料持久化（JSON）

**API**:
```python
coordinator = TrainingCoordinator(student_id="S001")

# 檢查是否可進入實作
can_enter, msg = coordinator.can_enter_practice()

# 更新分數
coordinator.update_theory_score(75)

# 切換階段
coordinator.enter_stage(TrainingStage.PRACTICE)

# 獲取進度
progress = coordinator.get_overall_progress()
```

### 2. ProgressTracker (進度追蹤器)

**檔案**: `integration/progress_tracker.py`

**功能**:
- 記錄所有互動（JSONL 格式）
- 統計學習數據
- 計算學習曲線
- 分析知識盲點
- 生成學習報告

**API**:
```python
tracker = ProgressTracker(student_id="S001")

# 記錄互動
tracker.log_interaction(
    interaction_type=InteractionType.THEORY_QUESTION,
    data={"question": "...", "answer": "..."},
    success=True
)

# 生成報告
report = tracker.generate_learning_report()

# 匯出 CSV
tracker.export_to_csv()
```

## 待實作模組

### 3. SmartRecommender (智能推薦器)

**功能**:
- 分析實作中的錯誤
- 識別知識盲點
- 推薦理論複習主題
- 生成個性化學習路徑

**觸發條件**:
- 連續 3 次操作失敗
- 特定主題錯誤率 > 60%
- 主動請求建議

### 4. EvaluationSystem (評分系統)

**功能**:
- 理論測驗評分
- 實作操作評分
- 綜合評估
- 生成改進建議

**評分公式**:
```
理論分數 = 測驗正確率 × 100

實作分數 = (
    診斷準確度 × 0.4 +
    操作正確性 × 0.4 +
    處理速度 × 0.2
) × 100

綜合分數 = 理論分數 × 0.3 + 實作分數 × 0.7
```

### 5. 階段 1 模組

需要建立:
- `stage1_theory/rag_engine.py` - RAG 檢索引擎
- `stage1_theory/question_bot.py` - 問答機器人
- `stage1_theory/difficulty_adapter.py` - 難度自適應
- `stage1_theory/knowledge_test.py` - 知識測驗

### 6. 統一介面

**檔案**: `interface/unified_gradio_app.py`

**設計**:
```
┌─────────────────────────────────────────┐
│ 學員：S001  |  當前階段：理論學習  |  進度：45% │
├─────────────────────────────────────────┤
│ [階段1：理論學習] [階段2：實作訓練] [學習報告] │
├─────────────────────────────────────────┤
│                                         │
│  Tab 1: 理論學習                         │
│  - 理論 BOT 對話                         │
│  - 知識測驗                              │
│  - [進入實作訓練] 按鈕（需達標）          │
│                                         │
│  Tab 2: 實作訓練                         │
│  - 設備視覺化                            │
│  - 操作輸入                              │
│  - AI 專家諮詢                           │
│                                         │
│  Tab 3: 學習報告                         │
│  - 分數統計                              │
│  - 學習曲線                              │
│  - 知識盲點                              │
│  - 改進建議                              │
│                                         │
└─────────────────────────────────────────┘
```

## 資料流

### 學員資料結構

```json
{
  "student_id": "S001",
  "name": "張三",
  "current_stage": "stage1_theory",
  "theory_score": 75,
  "practice_score": 0,
  "theory_completed": true,
  "practice_completed": false,
  "overall_completion": 22.5,
  "created_at": "2024-01-01T10:00:00",
  "last_updated": "2024-01-01T12:30:00"
}
```

### 互動記錄格式

```json
{
  "timestamp": "2024-01-01T10:15:30",
  "student_id": "S001",
  "type": "theory_question",
  "data": {
    "topic": "CVD",
    "question": "什麼是CVD?",
    "answer": "化學氣相沉積",
    "bot_response": "..."
  },
  "success": true,
  "score": null
}
```

## 階段解鎖機制

```python
# 階段 2 初始為鎖定狀態
stage2_tab.interactive = False

# 監聽理論分數更新
def on_theory_score_update(score):
    if score >= 70:
        # 解鎖階段 2
        stage2_tab.interactive = True
        return "恭喜通過理論測驗！可以進入實作訓練了。"
```

## 智能推薦觸發

```python
# 在階段 2 實作訓練中
failed_operations = tracker.get_recent_failures(count=3)

if len(failed_operations) >= 3:
    # 分析失敗原因
    gaps = tracker.get_knowledge_gaps()

    # 推薦複習
    recommender = SmartRecommender()
    topics = recommender.recommend_topics(gaps)

    # 提示學員
    return f"建議複習：{', '.join(topics)}"
```

## 使用流程

### 1. 系統啟動

```bash
python main.py
```

### 2. 學員登入

- 輸入學員 ID
- 系統載入進度
- 顯示當前階段

### 3. 階段 1：理論學習

- 與 Theory Bot 對話
- 參加知識測驗
- 達到 70 分解鎖階段 2

### 4. 階段 2：實作訓練

- 面對故障情境
- 自由輸入操作
- AI 專家引導
- 達到 80 分完成訓練

### 5. 生成報告

- 查看學習統計
- 分析學習曲線
- 檢視知識盲點
- 獲取改進建議

## API 整合範例

```python
from integration.training_coordinator import TrainingCoordinator, TrainingStage
from integration.progress_tracker import ProgressTracker, InteractionType
from integration.smart_recommender import SmartRecommender
from integration.evaluation_system import EvaluationSystem

# 初始化
student_id = "S001"
coordinator = TrainingCoordinator(student_id)
tracker = ProgressTracker(student_id)
recommender = SmartRecommender()
evaluator = EvaluationSystem()

# 階段 1：理論學習
while not coordinator.theory_completed:
    # 學員提問
    question = input("你的問題：")

    # BOT 回答
    answer, is_correct = theory_bot.answer(question)

    # 記錄互動
    tracker.log_interaction(
        InteractionType.THEORY_QUESTION,
        {"question": question, "answer": answer},
        success=is_correct
    )

    # 定期測驗
    if tracker.stats["theory_questions_asked"] % 10 == 0:
        score = conduct_test()
        coordinator.update_theory_score(score)

# 階段 2：實作訓練
if coordinator.can_enter_practice()[0]:
    coordinator.enter_stage(TrainingStage.PRACTICE)

    while not coordinator.practice_completed:
        # 學員操作
        operation = input("你的操作：")

        # 執行操作
        result = simulation_system.execute(operation)

        # 記錄互動
        tracker.log_interaction(
            InteractionType.PRACTICE_OPERATION,
            {"operation": operation, "result": result},
            success=result["success"]
        )

        # 檢查是否需要推薦
        if should_recommend(tracker):
            topics = recommender.recommend_topics(tracker.get_knowledge_gaps())
            print(f"建議複習：{topics}")

        # 評分
        score = evaluator.evaluate_practice(tracker)
        coordinator.update_practice_score(score)

# 生成最終報告
report = tracker.generate_learning_report()
print(report)
```

## 評分演算法

### 理論分數

```python
def calculate_theory_score(test_results):
    correct = sum(1 for r in test_results if r["correct"])
    total = len(test_results)
    return (correct / total) * 100 if total > 0 else 0
```

### 實作分數

```python
def calculate_practice_score(session_data):
    # 診斷準確度
    diagnosis_accuracy = evaluate_diagnosis(session_data)

    # 操作正確性
    operation_correctness = evaluate_operations(session_data)

    # 處理速度（時間獎勵）
    time_efficiency = evaluate_time_efficiency(session_data)

    # 加權平均
    practice_score = (
        diagnosis_accuracy * 0.4 +
        operation_correctness * 0.4 +
        time_efficiency * 0.2
    ) * 100

    return practice_score
```

### 綜合分數

```python
def calculate_overall_score(theory_score, practice_score):
    return theory_score * 0.3 + practice_score * 0.7
```

## 下一步

1. ✅ 實作 `SmartRecommender` 智能推薦器
2. ✅ 實作 `EvaluationSystem` 評分系統
3. ✅ 建立統一 Gradio 介面原型
4. ✅ 整合 SmartRecommender 到統一介面
5. ✅ 整合 EvaluationSystem 到統一介面
6. ✅ 整合測試完成
7. ⬜ 建立階段 1 理論模組 (RAG, 問答 BOT, 難度自適應, 知識測驗)
8. ⬜ AI/LLM 整合 (後續)

## 注意事項

1. **資料持久化**: 所有學員資料都儲存在 `data/student_progress/`
2. **階段鎖定**: 必須通過階段 1 才能進入階段 2
3. **即時儲存**: 每次互動都即時儲存，避免資料遺失
4. **智能推薦**: 系統會主動發現學習盲點並推薦複習
5. **報告生成**: 可隨時生成當前學習報告

---

**系統目標**: 提供完整的從理論到實作的訓練路徑，確保新人全面掌握半導體設備故障處理能力。
