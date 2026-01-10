# Qwen 2.5 LLM 整合指南

## 概述

本系統已整合您原有的 **Qwen 2.5 3B Instruct** 訓練系統，提供本地化的 AI 學長導師功能。

### 優勢

- ✅ **完全本地化**：無需網路連接，資料不外傳
- ✅ **零成本運行**：不需要 API 費用
- ✅ **快速響應**：使用 GPU 加速，響應時間 1-3 秒
- ✅ **情境感知**：針對設備故障處理情境優化
- ✅ **持續學習**：可根據訓練資料微調

---

## 系統架構

```
半導體訓練系統
│
├── AI 學長選項（優先順序）
│   ├── 1. Qwen 2.5 LLM (Transformers) ← 新增
│   ├── 2. Ollama LLM (本地服務)
│   ├── 3. Claude API (雲端服務)
│   └── 4. Mock 模式 (模板回應)
│
├── 核心模組
│   ├── qwen_training_assistant.py ← 新增
│   └── ai_scenario_mentor.py (已更新)
│
└── 整合層
    └── qwen_mentor_bot.py ← 新增
```

---

## 安裝步驟

### 1. 安裝必要套件

```bash
# 進入專案目錄
cd semiconductor_training_system

# 安裝 Qwen 所需套件
pip install transformers>=4.36.0 accelerate>=0.25.0 torch>=2.0.0

# 如果有 GPU，安裝量化支援（節省記憶體）
pip install bitsandbytes>=0.41.0
```

### 2. 系統需求

**最低需求（CPU）：**
- RAM: 16GB+
- 硬碟空間: 10GB+
- 首次啟動時間: 5-10 分鐘（下載模型）

**建議需求（GPU）：**
- GPU: NVIDIA GPU with 8GB+ VRAM
- RAM: 8GB+
- CUDA: 11.7+
- 首次啟動時間: 2-3 分鐘

---

## 啟用 Qwen 模型

### 方法 1: 環境變數（推薦）

#### Windows (PowerShell)
```powershell
$env:USE_QWEN_LLM = "true"
python start_simulation.py
```

#### Linux / macOS
```bash
export USE_QWEN_LLM=true
python start_simulation.py
```

### 方法 2: .env 檔案

創建 `.env` 檔案：
```env
# 啟用 Qwen 2.5 LLM
USE_QWEN_LLM=true

# 可選：指定模型名稱
QWEN_MODEL_NAME=Qwen/Qwen2.5-3B-Instruct
```

---

## 使用方式

### 在訓練系統中

啟動後，系統會自動偵測並載入 Qwen 模型：

```
[Info] 正在載入 Qwen 2.5 模型（這可能需要幾分鐘）...
[Init] Qwen 訓練助手
  - 模型: Qwen/Qwen2.5-3B-Instruct
  - 設備: cuda
  - 量化: 啟用
  - 載入 tokenizer...
  - 載入模型...

[OK] 模型載入成功！用時: 45.2 秒
[Info] GPU 記憶體使用: 3.24 GB
[Init] AI 情境學長模式: qwen
```

### 直接使用 API

```python
from core.qwen_training_assistant import QwenTrainingAssistant

# 初始化助手
assistant = QwenTrainingAssistant(
    model_name="Qwen/Qwen2.5-3B-Instruct",
    use_quantization=True  # 啟用 4-bit 量化
)

# 載入模型
assistant.load_model()

# 生成回答
result = assistant.generate_answer(
    question="什麼是 CVD 製程？",
    max_length=512,
    temperature=0.7
)

print(result['answer'])
print(f"生成時間: {result['generation_time']:.2f} 秒")
print(f"速度: {result['tokens_per_second']:.1f} tokens/秒")
```

### 情境化問答

```python
# 提供情境上下文
context = {
    'scenario_name': '冷卻系統流量異常',
    'equipment_state': '運行中',
    'fault_stage': 1,
    'parameters': '冷卻水流量: 3.5 L/min (偏低)'
}

result = assistant.generate_answer(
    question="學長，冷卻水流量這麼低是什麼原因？",
    context=context
)

print(result['answer'])
```

---

## 測試整合

執行測試腳本：

```bash
python test_qwen_integration.py
```

測試項目：
1. ✓ 環境檢查（PyTorch, CUDA）
2. ✓ 模組導入
3. ✓ 模型載入
4. ✓ 基礎問答
5. ✓ 情境問答
6. ✓ 訓練統計

---

## 功能特色

### 1. 學長式對話風格

Qwen 模型已針對「學長引導」風格優化：

**傳統 AI 回答：**
```
CVD（化學氣相沉積）是一種在半導體製造中常用的薄膜沉積技術。
其原理是將氣態前驅物通過化學反應在基板表面形成固態薄膜...
```

**學長式回答：**
```
嗯，CVD 簡單說就是用氣體在晶圓上「長」一層薄膜。
你看，就像噴漆一樣，但這個是化學反應自己長出來的。
我們機台上常用的就是 PECVD，你之前看過對吧？
```

### 2. 情境感知

系統會根據當前故障情境調整回答：

- **故障初期**：引導觀察、收集資訊
- **故障中期**：幫助分析、提供經驗
- **故障後期**：提醒注意事項、確認步驟

### 3. 反問引導

```python
# 生成反問問題
follow_up = assistant.generate_follow_up(
    question="為什麼溫度會上升？",
    answer="可能是冷卻系統的問題..."
)

# 輸出：「那你覺得應該先檢查哪個部分？」
```

### 4. 學習評估

```python
# 評估學員回答
evaluation = assistant.evaluate_response(
    follow_up_q="應該先檢查哪個部分？",
    trainee_answer="我覺得先看冷卻水流量"
)

print(evaluation['score'])      # 7.5
print(evaluation['feedback'])   # "對，這是正確的思路..."
```

---

## 性能優化

### GPU 記憶體優化

```python
# 使用 4-bit 量化（推薦）
assistant = QwenTrainingAssistant(
    use_quantization=True  # 記憶體使用: ~3GB
)

# 不使用量化
assistant = QwenTrainingAssistant(
    use_quantization=False  # 記憶體使用: ~12GB
)
```

### 響應速度優化

```python
# 調整生成長度（較短 = 較快）
result = assistant.generate_answer(
    question="...",
    max_length=256,        # 較短回答
    temperature=0.5        # 較確定的回答
)
```

### 批次處理

```python
# 如需處理多個問題
questions = ["問題1", "問題2", "問題3"]

for q in questions:
    result = assistant.generate_answer(q)
    print(result['answer'])
```

---

## 常見問題 (FAQ)

### Q1: 模型下載失敗怎麼辦？

**A:** 可能是網路問題。可以手動下載模型：

```bash
# 使用 huggingface-cli
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2.5-3B-Instruct
```

### Q2: GPU 記憶體不足

**A:** 啟用量化或使用 CPU：

```python
# 方法 1: 啟用量化
assistant = QwenTrainingAssistant(use_quantization=True)

# 方法 2: 強制使用 CPU
import torch
torch.cuda.is_available = lambda: False
```

### Q3: 載入速度太慢

**A:** 首次載入需要下載模型（約 6GB），之後會使用快取：

- 首次: 5-10 分鐘
- 之後: 30-60 秒

### Q4: 回答品質不如預期

**A:** 可以調整提示詞或溫度：

```python
result = assistant.generate_answer(
    question="...",
    temperature=0.7,  # 0.1-1.0，較高=較有創意
    max_length=512    # 較長=較詳細
)
```

---

## 進階功能

### 對話歷史管理

```python
# 檢視對話歷史
print(assistant.conversation_history)

# 清除對話歷史
assistant.clear_history()
```

### 統計資訊

```python
stats = assistant.get_stats()
print(stats)
# {
#     'session_duration': '15 分鐘',
#     'questions_asked': 3,
#     'answers_given': 12,
#     'total_tokens': 2048,
#     'avg_response_time': '1.25 秒'
# }
```

### 自訂模型

```python
# 使用其他 Qwen 模型
assistant = QwenTrainingAssistant(
    model_name="Qwen/Qwen2.5-7B-Instruct",  # 更大的模型
    use_quantization=True
)
```

---

## 與其他 LLM 的比較

| 特性 | Qwen 2.5 | Ollama | Claude API |
|------|----------|--------|------------|
| 本地運行 | ✅ | ✅ | ❌ |
| 零成本 | ✅ | ✅ | ❌ |
| 繁體中文 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 技術領域 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 啟動速度 | 中 (30-60s) | 快 (<5s) | 即時 |
| 記憶體需求 | 3-12 GB | 4-8 GB | 0 GB |
| 客製化 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |

---

## 系統監控

### GPU 使用監控

```bash
# 即時監控 GPU
nvidia-smi -l 1

# 或使用 Python
import torch
print(f"已分配: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
print(f"快取: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")
```

### 性能分析

```python
result = assistant.generate_answer("test")
print(f"生成時間: {result['generation_time']:.2f} 秒")
print(f"Tokens 數: {result['tokens_generated']}")
print(f"速度: {result['tokens_per_second']:.1f} tokens/秒")
```

---

## 故障排除

### 模組導入錯誤

```bash
# 確認模組路徑
python -c "import sys; print(sys.path)"

# 重新安裝
pip uninstall transformers accelerate torch
pip install transformers accelerate torch
```

### CUDA 錯誤

```bash
# 檢查 CUDA 版本
nvidia-smi

# 重新安裝對應版本的 PyTorch
# 訪問: https://pytorch.org/get-started/locally/
```

---

## 未來優化方向

1. **模型微調**：使用半導體領域資料微調
2. **多輪對話**：改進上下文記憶
3. **知識庫整合**：連接設備手冊、SOP
4. **多模態**：支援圖片輸入（設備照片）
5. **量化優化**：探索 INT8/INT4 量化

---

## 貢獻者

- 原始 Qwen 訓練系統：您的實作
- 系統整合：Claude Code
- Qwen 2.5 模型：阿里雲

---

## 授權

本整合遵循 Qwen 2.5 的授權條款。

詳情請見：https://github.com/QwenLM/Qwen2.5

---

## 聯絡支援

如有問題或建議，請：

1. 查看本文檔的 FAQ 部分
2. 執行 `python test_qwen_integration.py` 進行診斷
3. 檢查系統日誌中的錯誤訊息

---

**最後更新：2026-01-10**
