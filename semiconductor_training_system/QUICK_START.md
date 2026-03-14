# 🚀 快速開始指南

## 📦 安裝步驟（5 分鐘）

### 步驟 1: 確認 Python 版本

```bash
python --version
# 需要 Python 3.8 或更高版本
```

### 步驟 2: 安裝套件

```bash
cd semiconductor_training_system
pip install pandas numpy gradio matplotlib
```

或者使用 requirements.txt：

```bash
pip install -r requirements.txt
```

**如果遇到編碼錯誤**，請使用：
```bash
pip install pandas numpy gradio matplotlib seaborn python-dateutil
```

### 步驟 3: 下載資料集

1. 前往 Kaggle: https://www.kaggle.com/datasets/paresh2047/uci-secom
2. 下載 `uci-secom.csv`
3. 放到專案**上一層目錄**：

```
論文/
├── uci-secom.csv           ← 放這裡
└── semiconductor_training_system/
    ├── core/
    ├── interface/
    └── ...
```

### 步驟 4: 測試系統

```bash
python simple_test.py
```

應該看到：
```
============================================================
System Test - Semiconductor Training System
============================================================

Test 1: Digital Twin...[OK]
Test 2: A2A Coordinator...[OK]
Test 3: Scenario Generator...[OK]
Test 4: Scoring System...[OK]
```

### 步驟 5: 啟動系統

```bash
python run_training_system.py
```

然後開啟瀏覽器訪問：
```
http://localhost:7860
```

---

## 🎮 第一次使用

### 1. 開始訓練
- 輸入學員 ID：`STU001`
- 選擇難度：`MEDIUM`
- 選擇程度：`beginner`
- 點擊「🚀 開始新情境」

### 2. 查看情境
你會看到類似這樣的情境：
> 「製程進行到一半，你發現晶圓溫度顯示異常，比設定值高出 50°C...」

### 3. 請求 AI 診斷
- 切換到「🤖 AI 專家診斷」分頁
- 點擊「🩺 請求專家診斷」
- 查看三位專家的建議

### 4. 執行操作
- 切換到「🔧 執行操作」分頁
- 輸入操作，例如：「降低加熱器功率至 50%」
- 點擊「✅ 執行步驟」

### 5. 提交診斷
- 切換到「📝 提交診斷」分頁
- 輸入診斷結果，例如：`temperature_spike`
- 選擇信心度：`比較確定`
- 點擊「📤 提交診斷」
- 查看評分報告

---

## ❓ 常見問題

### Q1: 找不到 uci-secom.csv

**錯誤訊息：**
```
FileNotFoundError: uci-secom.csv not found
```

**解決方法：**
1. 確認檔案位置：應該在專案**上一層目錄**
2. 或修改程式碼路徑為：`./uci-secom.csv` 或完整路徑

### Q2: pip install 編碼錯誤

**錯誤訊息：**
```
UnicodeDecodeError: 'cp950' codec can't decode...
```

**解決方法：**
直接安裝套件，不使用 requirements.txt：
```bash
pip install pandas numpy gradio matplotlib seaborn python-dateutil
```

### Q3: Gradio 無法開啟

**錯誤訊息：**
```
Address already in use
```

**解決方法：**
Port 7860 被佔用，修改 `run_training_system.py` 或 `gradio_app.py` 中的 port：
```python
demo.launch(server_port=7861)  # 改成其他 port
```

### Q4: 記憶體不足

**解決方法：**
- 關閉其他程式
- SECOM 資料集很小（~10MB），通常不會有問題

### Q5: import 錯誤

**錯誤訊息：**
```
ModuleNotFoundError: No module named 'core'
```

**解決方法：**
確認在正確目錄執行：
```bash
cd semiconductor_training_system
python run_training_system.py
```

---

## 🧪 驗證安裝

執行以下命令驗證每個組件：

```bash
# 測試 1: 數位孿生
python -c "from core.digital_twin import LithographyDigitalTwin; print('OK')"

# 測試 2: A2A 系統
python -c "from core.a2a_coordinator import A2ACoordinator; print('OK')"

# 測試 3: 情境生成
python -c "from core.scenario_generator import ScenarioGenerator; print('OK')"

# 測試 4: 評分系統
python -c "from evaluation.scoring_system import ScoringSystem; print('OK')"
```

全部顯示 `OK` 表示安裝成功！

---

## 📞 需要協助？

1. **查看完整文件**：[README.md](README.md)
2. **查看專案總覽**：[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
3. **查看交付文件**：[SYSTEM_DELIVERED.md](../SYSTEM_DELIVERED.md)

---

## ✅ 檢查清單

安裝前確認：
- [ ] Python 3.8+ 已安裝
- [ ] pip 可以正常使用
- [ ] 有穩定的網路（下載套件）

安裝後確認：
- [ ] `simple_test.py` 所有測試通過
- [ ] `run_training_system.py` 可以啟動
- [ ] 瀏覽器可以開啟 http://localhost:7860
- [ ] 可以看到 Gradio 介面

---

## 🎉 成功！

當你看到這個介面，就成功了：

```
🎓 半導體設備故障處理訓練系統
Interactive Semiconductor Equipment Fault Handling Training System

基於真實 SECOM 資料 + A2A 多專家 AI 協作的沉浸式訓練平台
```

**開始你的訓練吧！** 🚀
