# 本地 LLM 使用指南 (Qwen/Ollama)

## 📌 為什麼使用本地 LLM？

### 優點
✅ **完全免費** - 無需支付 API 費用
✅ **完全離線** - 不需要網路連線
✅ **資料隱私** - 所有對話都在本機，不會外傳
✅ **無使用限制** - 想用多少次就用多少次
✅ **客製化** - 可以自己調整模型參數

### 缺點
⚠️ **需要較好的硬體** - 建議至少 8GB RAM（推薦 16GB）
⚠️ **回應速度較慢** - 取決於電腦效能
⚠️ **中文品質** - 某些模型中文不如 Claude，推薦 Qwen

---

## 🚀 快速開始（3 步驟）

### 步驟 1: 安裝 Ollama

#### Windows
1. 下載安裝包：https://ollama.com/download/windows
2. 執行安裝檔（會自動安裝並啟動服務）
3. 打開命令提示字元，輸入 `ollama` 確認安裝成功

#### Mac
```bash
# 使用 Homebrew
brew install ollama

# 或直接下載安裝包
# https://ollama.com/download/mac
```

#### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 步驟 2: 下載模型

推薦使用 **Qwen 2.5** （阿里巴巴開源，中文超強）

```bash
# 7B 版本（推薦，記憶體需求：~8GB）
ollama pull qwen2.5:7b

# 14B 版本（更強，記憶體需求：~16GB）
ollama pull qwen2.5:14b

# 或其他模型
ollama pull llama3.1:8b    # Meta 的 Llama（英文好，中文普通）
ollama pull mistral:7b     # 速度快（中文較弱）
```

等待下載完成（約 5-10 分鐘，視網速而定）

### 步驟 3: 啟動訓練系統

```bash
cd semiconductor_training_system
python start_unified.py
```

系統會自動偵測本地 LLM 並啟動！

看到這個訊息就成功了：
```
[OK] 本地 LLM 學長BOT已啟動（模型: qwen2.5:7b）
```

---

## 📖 詳細使用說明

### 模型選擇

系統支援多種模型，通過環境變數切換：

```bash
# Windows (PowerShell)
$env:LOCAL_LLM_MODEL="qwen2.5:7b"

# Windows (CMD)
set LOCAL_LLM_MODEL=qwen2.5:7b

# Linux/Mac
export LOCAL_LLM_MODEL="qwen2.5:7b"
```

#### 推薦模型對比

| 模型 | 大小 | 記憶體需求 | 中文品質 | 速度 | 推薦場景 |
|------|------|-----------|---------|------|---------|
| **qwen2.5:7b** ⭐ | 4.7GB | 8GB | ⭐⭐⭐⭐⭐ | 中等 | **最推薦**，中文優秀 |
| qwen2.5:14b | 9.0GB | 16GB | ⭐⭐⭐⭐⭐ | 較慢 | 效能好可用 14B |
| llama3.1:8b | 4.7GB | 8GB | ⭐⭐⭐ | 快 | 英文環境 |
| mistral:7b | 4.1GB | 6GB | ⭐⭐ | 很快 | 硬體較弱時 |

### 檢查模型是否安裝

```bash
ollama list
```

輸出範例：
```
NAME              ID              SIZE     MODIFIED
qwen2.5:7b        8c39a6e4d5b0    4.7 GB   2 days ago
llama3.1:8b       42182419e950    4.7 GB   1 week ago
```

### 測試模型

```bash
# 與模型對話測試
ollama run qwen2.5:7b

# 輸入問題，例如：
# >>> 什麼是 CVD？
# （模型會回答）

# 按 Ctrl+D 或輸入 /bye 退出
```

### 系統自動選擇邏輯

系統啟動時會按以下順序嘗試：

1. **本地 LLM (Ollama)** ← 優先使用
   - 檢查 Ollama 是否運行
   - 檢查指定模型是否已安裝

2. **Claude API** ← 次選
   - 檢查 `ANTHROPIC_API_KEY` 環境變數

3. **Mock 模式** ← 最後退回
   - 簡單的關鍵詞匹配

---

## ⚙️ 進階配置

### 調整模型參數

編輯 [`local_mentor_bot.py`](stage1_theory/local_mentor_bot.py)，找到 `ask()` 方法：

```python
"options": {
    "temperature": 0.7,  # 創意程度 (0-1)，越高越有創意
    "top_p": 0.9,        # 核心採樣 (0-1)
    "top_k": 40,         # 限制候選詞數量
}
```

**參數說明**：
- `temperature`:
  - `0.3` - 保守、一致（適合技術問答）
  - `0.7` - 平衡（**推薦**）
  - `1.0` - 創意、多樣

- `top_p`: 控制隨機性，通常 0.9 即可

- `top_k`: 限制每次選擇的候選詞數量

### 自定義 Ollama 地址

如果 Ollama 運行在其他機器或端口：

```python
from stage1_theory.local_mentor_bot import LocalMentorBot

bot = LocalMentorBot(
    model_name="qwen2.5:7b",
    ollama_url="http://192.168.1.100:11434"  # 自定義地址
)
```

### 查看模型詳細資訊

```bash
ollama show qwen2.5:7b
```

---

## 🔧 故障排除

### 問題 1: 啟動時提示 "無法連接到 Ollama"

**原因**: Ollama 服務未啟動

**解決**:
```bash
# Windows: Ollama 通常會自動啟動，檢查系統托盤圖標

# Mac/Linux: 手動啟動
ollama serve
```

### 問題 2: 提示 "模型未安裝"

**原因**: 指定的模型尚未下載

**解決**:
```bash
ollama pull qwen2.5:7b
```

### 問題 3: 回答太慢

**可能原因與解決方法**:

1. **電腦效能不足**
   - 改用較小的模型：`ollama pull qwen2.5:3b` （未來版本）
   - 或用 `mistral:7b` （較快但中文弱）

2. **同時運行太多程式**
   - 關閉不必要的程式釋放記憶體

3. **模型參數設定**
   - 降低 `max_tokens`（限制回答長度）

### 問題 4: 回答品質不佳

**解決方法**:

1. **換更好的模型**:
   ```bash
   ollama pull qwen2.5:14b
   ```
   然後設定環境變數：
   ```bash
   export LOCAL_LLM_MODEL="qwen2.5:14b"
   ```

2. **調整 system prompt** （進階）:
   - 編輯 [`local_mentor_bot.py`](stage1_theory/local_mentor_bot.py)
   - 修改 `self.system_prompt` 中的指示

3. **降低 temperature**:
   - 改為 `0.5` 或 `0.3` 讓回答更穩定

### 問題 5: 記憶體不足

**症狀**: 系統變慢、Ollama crash

**解決**:
```bash
# 使用更小的模型
ollama pull qwen2.5:7b  # 取代 14b

# 或使用量化版本（如果有）
ollama pull qwen2.5:7b-q4  # 4-bit 量化，更省記憶體
```

---

## 📊 效能對比

### 測試環境
- CPU: Intel i7-12700
- RAM: 16GB
- 無獨立顯卡（僅 CPU 運算）

### 回應時間對比

| 問題 | qwen2.5:7b | Claude API | Mock |
|------|-----------|------------|------|
| "什麼是CVD？" | ~5 秒 | ~2 秒 | 即時 |
| 複雜問題 | ~8 秒 | ~3 秒 | 即時 |

### 記憶體使用

| 模型 | 載入後記憶體 | 對話中記憶體 |
|------|-------------|-------------|
| qwen2.5:7b | ~5GB | ~6GB |
| qwen2.5:14b | ~10GB | ~12GB |
| mistral:7b | ~4GB | ~5GB |

---

## 💡 使用建議

### 開發/測試階段
→ 使用 **Mock 模式**（快速）

### 正式訓練
→ 使用 **本地 LLM**（免費、隱私）

### 追求最佳品質
→ 使用 **Claude API**（品質最好，但要付費）

### 硬體建議

| 你的硬體 | 推薦模型 |
|---------|---------|
| RAM < 8GB | Mock 模式或雲端 API |
| RAM 8-16GB | qwen2.5:7b ⭐ |
| RAM > 16GB | qwen2.5:14b |
| 有 NVIDIA GPU (8GB+) | 可考慮 vLLM (未來支援) |

---

## 🔄 切換模式

### 方法 1: 環境變數（推薦）

```bash
# 使用本地 LLM
export LOCAL_LLM_MODEL="qwen2.5:7b"
python start_unified.py

# 使用 Claude API
export ANTHROPIC_API_KEY="sk-ant-..."
python start_unified.py

# 使用 Mock（不設任何環境變數）
python start_unified.py
```

### 方法 2: 程式內切換

系統會**自動檢測**並選擇可用的模式，優先順序：
```
本地 LLM > Claude API > Mock
```

---

## 📚 相關資源

### Ollama 官方資源
- 官網: https://ollama.com
- 模型庫: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama
- 文檔: https://github.com/ollama/ollama/blob/main/docs/api.md

### Qwen 模型
- Qwen 2.5 介紹: https://ollama.com/library/qwen2.5
- 官方網站: https://qwenlm.github.io
- 技術報告: https://arxiv.org/abs/2407.10671

### 其他推薦模型
- Llama 3.1: https://ollama.com/library/llama3.1
- Mistral: https://ollama.com/library/mistral
- Gemma: https://ollama.com/library/gemma

---

## 🆚 與 Claude API 對比

| 特性 | 本地 LLM (Qwen 2.5) | Claude API |
|------|-------------------|------------|
| **中文品質** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **反問機制** | ✅ 支援 | ✅ 支援 |
| **回應速度** | 5-8 秒 | 2-3 秒 |
| **成本** | 免費 | ~NT$0.15/次 |
| **網路需求** | 不需要 | 需要 |
| **隱私性** | 100% 本地 | 資料傳雲端 |
| **使用限制** | 無 | 按使用量計費 |
| **硬體需求** | 8GB+ RAM | 無 |

---

## 📝 使用範例

### Python 腳本範例

```python
from stage1_theory.local_mentor_bot import LocalMentorBot

# 創建本地學長 BOT
bot = LocalMentorBot(model_name="qwen2.5:7b")

# 第一輪對話
q1 = "什麼是 CVD？"
a1 = bot.ask(q1)
print(f"Q: {q1}")
print(f"A: {a1}\n")

# 第二輪對話（會記得前面的對話）
q2 = "為什麼要用真空？"
a2 = bot.ask(q2)
print(f"Q: {q2}")
print(f"A: {a2}\n")

# 檢查學員理解
student_answer = "因為要避免污染"
understood, feedback = bot.check_understanding(
    student_answer,
    expected_keywords=["污染", "氧化", "純度"]
)
print(f"理解程度: {'✓' if understood else '✗'}")
print(f"反饋: {feedback}\n")

# 獲取對話摘要
summary = bot.get_conversation_summary()
print(f"對話摘要:\n{summary}")

# 重置對話
bot.reset_conversation()
```

### 測試運行

```bash
cd semiconductor_training_system/stage1_theory
python local_mentor_bot.py
```

---

## 🎯 總結

### 推薦方案

1. **學生自學** → 本地 Qwen 2.5:7b (免費、隱私)
2. **企業訓練** → Claude API (品質最佳)
3. **快速測試** → Mock 模式 (即時回應)

### 安裝清單

- [x] 安裝 Ollama
- [x] 下載 Qwen 2.5 模型
- [x] 測試模型運行
- [x] 啟動訓練系統

一切就緒，開始使用本地 LLM 進行訓練吧！ 🚀
