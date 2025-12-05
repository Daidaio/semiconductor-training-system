# 開始使用訓練系統

## 快速啟動（3 個指令）

```bash
# 1. 進入專案目錄
cd semiconductor_training_system

# 2. 安裝套件（如果還沒裝）
pip install pandas numpy gradio

# 3. 啟動系統
python start.py
```

然後開啟瀏覽器訪問：**http://localhost:7860**

---

## 常見問題解決

### 問題 1: 找不到 uci-secom.csv

**解決方法：**
1. 下載 SECOM 資料集
   - Kaggle: https://www.kaggle.com/datasets/paresh2047/uci-secom
2. 放到專案**上一層**目錄（與 semiconductor_training_system 同一層）

目錄結構應該是：
```
論文/
├── uci-secom.csv           ← 放這裡
└── semiconductor_training_system/
    └── start.py
```

### 問題 2: 套件錯誤

```bash
pip install pandas numpy gradio matplotlib
```

### 問題 3: Port 被佔用

修改 `start.py` 第 56 行：
```python
server_port=7861,  # 改成其他 port
```

---

## 第一次訓練步驟

### 1. 開始訓練
- 學員 ID: `STU001`
- 難度: `MEDIUM`
- 程度: `beginner`
- 點「開始新情境」

### 2. 請求 AI 診斷
- 切換到「AI 專家診斷」分頁
- 點「請求專家診斷」
- 查看三位專家建議

### 3. 執行操作
- 切換到「執行操作」分頁
- 輸入操作步驟
- 點「執行步驟」

### 4. 提交診斷
- 切換到「提交診斷」分頁
- 輸入診斷結果（例如：`temperature_spike`）
- 選擇信心度
- 點「提交診斷」

### 5. 查看評分
- 看到總分、等級、改進建議

---

## 測試系統

```bash
python simple_test.py
```

應該看到所有測試 [OK]

---

## 需要協助？

1. 查看完整說明：[README.md](README.md)
2. 快速指南：[QUICK_START.md](QUICK_START.md)
3. 專案總覽：[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)

---

## 成功標誌

當你看到：
```
============================================================
[SUCCESS] System started!
============================================================

Open browser: http://localhost:7860
Press Ctrl+C to stop
```

就成功了！🎉
