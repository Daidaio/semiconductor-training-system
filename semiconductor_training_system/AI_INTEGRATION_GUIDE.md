# AI/LLM 整合指南

## 概覽

本系統已整合 **AI 學長 BOT**，使用 **Claude 3.5 Sonnet** 提供自然、像學長帶學弟一樣的理論問答體驗。

### 核心特色

1. **反問機制 (Socratic Teaching)**: 每次回答後會主動反問，確認學員理解
2. **自然對話風格**: 使用口語化表達，如「啦」「欸」「嗯」「對啊」等語助詞
3. **上下文記憶**: 維持對話歷史，能夠進行連貫的多輪對話
4. **優雅降級**: 如果沒有 API key，自動退回到 Mock 模式

---

## 系統架構

```
階段 1: 理論學習 (AI 學長 BOT)
    ├── SeniorMentorBot (AI 驅動)
    │   ├── 使用 Claude 3.5 Sonnet API
    │   ├── 反問機制 (確認理解)
    │   ├── 自然對話風格
    │   └── 對話歷史管理
    │
    └── Mock 模式 (Fallback)
        └── 簡單關鍵詞匹配
```

---

## 檔案說明

### 1. `stage1_theory/senior_mentor_bot.py`

**AI 學長 BOT 核心模組** (~230 行)

#### 主要類別

```python
class SeniorMentorBot:
    """
    AI 驅動的學長 BOT
    使用 Claude 3.5 Sonnet 提供自然的理論問答
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 AI BOT

        Args:
            api_key: Anthropic API Key (可選，會從環境變數讀取)
        """

    def ask(self, question: str, maintain_context: bool = True) -> str:
        """
        向學長提問

        Args:
            question: 學員問題
            maintain_context: 是否維持對話歷史 (預設 True)

        Returns:
            學長的回答（包含反問）
        """

    def check_understanding(self, student_answer: str,
                          expected_keywords: List[str]) -> Tuple[bool, str]:
        """
        檢查學員回答是否理解

        Args:
            student_answer: 學員的回答
            expected_keywords: 預期的關鍵詞清單

        Returns:
            (是否理解, 反饋訊息)
        """

    def get_conversation_summary(self) -> str:
        """
        獲取對話摘要

        Returns:
            對話摘要文字
        """

    def reset_conversation(self):
        """
        重置對話歷史
        """
```

#### 系統提示詞設計

BOT 被設定為：
- **身份**: 有 5 年經驗的半導體設備工程師學長
- **個性**: 耐心、友善、喜歡用實際例子教學
- **語言風格**: 台灣口語化中文，自然使用「啦」「欸」「嗯」「對啊」
- **教學方法**: Socratic 反問式教學

**關鍵規則**:
```
1. 一定要反問：每次回答後至少問 1 個問題確認理解
2. 用口語化表達：自然使用語助詞
3. 舉實際例子：用產線實際情況說明
4. 循序漸進：從簡單到複雜
5. 鼓勵思考：引導學員自己推理
```

#### 對話風格範例

✅ **好的回答（學長風格）**:
```
「欸，CVD 其實就是化學氣相沉積啦！簡單說，就是讓氣體在高溫下產生化學反應，
然後在晶圓表面形成一層薄膜。

你可以想像成是在晶圓上『長』一層膜，不是用鍍的喔！

主要有幾種類型：
- PECVD（電漿增強）：用電漿加速反應，溫度可以低一點
- LPCVD（低壓）：在低壓環境下進行，膜質比較均勻
- APCVD（常壓）：就是一般大氣壓力下做

對了，你知道為什麼要控制溫度嗎？或者說，你覺得溫度太高會怎樣？」
```

❌ **不好的回答（太正式）**:
```
「CVD 是 Chemical Vapor Deposition 的縮寫，中文為化學氣相沉積。
其原理為利用化學反應在基材表面沉積薄膜。」
```

---

### 2. `interface/unified_training_interface.py`

**整合 AI BOT 到統一介面**

#### 初始化邏輯

```python
class UnifiedTrainingSystem:
    def __init__(self):
        # ...其他初始化...

        # 階段 1 模組（理論學習）- AI學長BOT
        self.mentor_bot = None
        self.use_ai_bot = os.getenv("ANTHROPIC_API_KEY") is not None

        if self.use_ai_bot:
            try:
                self.mentor_bot = SeniorMentorBot()
                print("[OK] AI學長BOT已啟動（使用Claude API）")
            except Exception as e:
                print(f"[Warning] AI學長BOT啟動失敗: {e}")
                print("[Info] 將使用Mock模式")
                self.use_ai_bot = False
        else:
            print("[Info] 未設置ANTHROPIC_API_KEY，使用Mock模式")
```

#### 問答邏輯

```python
def ask_theory_question(self, question: str, chat_history: list):
    """理論問答（AI 學長 BOT）"""

    # 使用 AI 學長 BOT 或 Mock 模式
    if self.use_ai_bot and self.mentor_bot:
        try:
            # 使用 AI BOT 回答（包含反問機制）
            answer = self.mentor_bot.ask(question, maintain_context=True)
            found_answer = True
        except Exception as e:
            # AI 失敗時退回到 Mock 模式
            print(f"[Warning] AI BOT 回答失敗: {e}，使用 Mock 模式")
            answer = self._mock_answer(question)
            found_answer = "cvd" in question.lower() or "真空" in question.lower()
    else:
        # Mock 模式
        answer = self._mock_answer(question)
        found_answer = "cvd" in question.lower() or "真空" in question.lower()

    # 記錄互動
    self.tracker.log_interaction(
        InteractionType.THEORY_QUESTION,
        {"question": question, "answer": answer},
        success=found_answer
    )

    # 更新對話歷史
    chat_history.append({"role": "user", "content": question})
    chat_history.append({"role": "assistant", "content": answer})

    return chat_history, ""
```

---

## 使用方式

### 方法 1: 使用 AI 模式 (需要 API Key)

1. **設置 API Key**:

```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your-api-key-here"

# Windows (CMD)
set ANTHROPIC_API_KEY=your-api-key-here

# Linux/Mac
export ANTHROPIC_API_KEY="your-api-key-here"
```

2. **啟動系統**:

```bash
cd semiconductor_training_system
python start_unified.py
```

3. **看到啟動訊息**:

```
[OK] AI學長BOT已啟動（使用Claude API）
```

4. **開始使用**:
   - 打開瀏覽器訪問 http://127.0.0.1:7860
   - 登入學員帳號
   - 在「階段1：理論學習」標籤頁提問
   - AI 學長會用自然的方式回答，並反問確認理解

### 方法 2: 使用 Mock 模式 (不需要 API Key)

1. **直接啟動** (不設置 API Key):

```bash
python start_unified.py
```

2. **看到啟動訊息**:

```
[Info] 未設置ANTHROPIC_API_KEY，使用Mock模式
```

3. **Mock 模式功能**:
   - 簡單的關鍵詞匹配
   - 固定的回答模板
   - 仍然會顯示反問提示

---

## 對話範例

### 範例 1: CVD 製程

**學員**: 什麼是 CVD？

**AI 學長**:
```
欸，CVD 其實就是化學氣相沉積啦！簡單說，就是讓氣體在高溫下產生化學反應，
然後在晶圓表面形成一層薄膜。

你可以想像成是在晶圓上『長』一層膜，不是用鍍的喔！像我們產線上最常用的
就是 PECVD，用電漿來加速反應，這樣溫度可以低一點，對晶圓比較不傷。

對了，你知道為什麼 CVD 要在真空環境下進行嗎？或者說，你覺得如果有空氣
混進去會怎樣？
```

**學員**: 應該會污染薄膜吧？

**AI 學長**:
```
對啊！你抓到重點了！空氣裡的氧氣、水氣這些東西，都會跟我們的反應氣體
搶著跟晶圓作用，這樣薄膜就不純了。

而且嘛，真空還有另一個好處：可以讓氣體流動更均勻，這樣整片晶圓的薄膜
厚度才會一致。你想想，如果這片厚、那片薄，良率不就掉下來了？

欸對了，你有看過真空幫浦嗎？你知道我們產線上用的是哪一種嗎？
```

### 範例 2: 真空系統故障

**學員**: 真空度不足要怎麼處理？

**AI 學長**:
```
嗯，真空度不足喔，這個在產線上蠻常見的啦！

我教你一個標準的排查順序：

1. 先看 Gauge 讀數對不對 - 有時候是 sensor 壞了
2. 檢查 chamber 門有沒有關緊 - 這個最常發生
3. 看真空管路有沒有漏氣 - 用 leak detector 檢查
4. 確認幫浦運轉正常 - 聽聲音、看轉速
5. 最後才換 O-ring 或維修幫浦

你覺得為什麼要先檢查簡單的？或者說，你遇到這種狀況會從哪裡開始查？
```

---

## API 使用說明

### SeniorMentorBot 完整範例

```python
from stage1_theory.senior_mentor_bot import SeniorMentorBot

# 初始化（自動從環境變數讀取 API Key）
bot = SeniorMentorBot()

# 或者直接傳入 API Key
# bot = SeniorMentorBot(api_key="your-api-key")

# 第一輪對話
question1 = "什麼是 CVD？"
answer1 = bot.ask(question1)
print(f"學員: {question1}")
print(f"學長: {answer1}")

# 第二輪對話（會保持上下文）
question2 = "為什麼要用真空？"
answer2 = bot.ask(question2)
print(f"學員: {question2}")
print(f"學長: {answer2}")

# 檢查學員理解
student_response = "因為要避免污染"
understood, feedback = bot.check_understanding(
    student_response,
    expected_keywords=["污染", "氧化", "純度"]
)
print(f"理解程度: {'✓ 理解' if understood else '✗ 需要再解釋'}")
print(f"反饋: {feedback}")

# 獲取對話摘要
summary = bot.get_conversation_summary()
print(f"\n對話摘要:\n{summary}")

# 重置對話（開始新話題）
bot.reset_conversation()
```

### 不保存上下文的使用

```python
# 每次都是獨立問答
answer = bot.ask("CVD 是什麼？", maintain_context=False)
# 下一個問題不會記得之前的對話
```

---

## 進階配置

### 自定義系統提示詞

如需調整 BOT 的個性或教學風格，編輯 [`senior_mentor_bot.py`](stage1_theory/senior_mentor_bot.py):

```python
self.system_prompt = """你是一位...（自定義設定）"""
```

### 調整模型參數

```python
response = self.client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,  # 調整回答長度
    temperature=0.7,  # 調整創意程度 (0-1)
    system=self.system_prompt,
    messages=self.conversation_history
)
```

---

## 故障排除

### 1. 啟動時提示 `ModuleNotFoundError: No module named 'anthropic'`

**解決方法**:
```bash
pip install anthropic>=0.18.0
```

### 2. 啟動時提示 `未設置ANTHROPIC_API_KEY`

**原因**: 沒有設置環境變數

**解決方法**:
```bash
# 設置環境變數
export ANTHROPIC_API_KEY="your-api-key"

# 或直接在程式中傳入
bot = SeniorMentorBot(api_key="your-api-key")
```

### 3. AI BOT 啟動失敗，自動退回 Mock 模式

**可能原因**:
- API Key 無效
- 網路連線問題
- Anthropic API 服務中斷

**檢查方式**:
```python
# 測試 API Key 是否有效
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello"}]
)
print(message.content[0].text)
```

### 4. 回答太短或太長

**調整 `max_tokens`**:
```python
# 在 senior_mentor_bot.py 中
response = self.client.messages.create(
    max_tokens=2048,  # 增加到 2048（預設 1024）
    ...
)
```

### 5. 對話失去上下文

**原因**: `maintain_context=False` 或對話被重置

**解決方法**:
```python
# 確保使用 maintain_context=True
answer = bot.ask(question, maintain_context=True)

# 檢查是否意外呼叫了 reset_conversation()
```

---

## 成本估算

### Claude 3.5 Sonnet 定價 (2024)

- **Input**: $3 / 1M tokens
- **Output**: $15 / 1M tokens

### 典型使用量估算

一次對話（一問一答）:
- 輸入: ~200 tokens（問題 + 系統提示 + 歷史）
- 輸出: ~300 tokens（回答 + 反問）

**單次對話成本**:
```
(200 × $3 + 300 × $15) / 1,000,000 = $0.0051 ≈ NT$0.15
```

**每位學員完整訓練（假設 100 次對話）**:
```
100 × $0.0051 = $0.51 ≈ NT$15
```

**建議**:
- 初期測試使用 Mock 模式（免費）
- 正式訓練時才啟用 AI 模式
- 為學員設定每日對話次數上限

---

## 與 Mock 模式對比

| 特性 | AI 模式 | Mock 模式 |
|------|---------|-----------|
| **回答品質** | 自然、詳細、個性化 | 簡單、制式化 |
| **反問機制** | ✅ 智能反問 | ⚠️ 固定提示 |
| **上下文記憶** | ✅ 完整保存 | ❌ 無 |
| **成本** | ~NT$0.15/次 | 免費 |
| **網路需求** | 需要 | 不需要 |
| **適用場景** | 正式訓練 | 開發測試 |

---

## 未來擴展

### 可能的改進方向

1. **RAG 整合**: 從 SOP 文件檢索相關資訊
2. **多輪對話管理**: 更複雜的對話狀態追蹤
3. **學習路徑規劃**: 根據學員表現推薦學習內容
4. **語音輸入輸出**: 整合 TTS/STT
5. **多模態輸入**: 支援圖片問答（如設備照片）

---

## 總結

✅ **已完成**:
- SeniorMentorBot 核心實作
- 整合到統一訓練介面
- 反問機制實現
- 自然對話風格
- 優雅降級到 Mock 模式

📝 **使用建議**:
1. 開發/測試階段使用 Mock 模式
2. 正式訓練時啟用 AI 模式
3. 監控 API 使用量與成本
4. 收集學員反饋持續優化提示詞

🔗 **相關文件**:
- [整合指南](INTEGRATION_GUIDE.md)
- [整合完成報告](INTEGRATION_COMPLETED.md)
- [模組說明](integration/README.md)

---

**系統目標**: 提供像學長帶學弟一樣自然的理論學習體驗，通過反問機制確保學員真正理解，而不只是背答案。
