# 🎓 半導體設備故障處理訓練系統

> Interactive Semiconductor Equipment Fault Handling Training System
> 基於真實 SECOM 資料 + A2A 多專家 AI 協作的沉浸式訓練平台

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Gradio](https://img.shields.io/badge/Gradio-UI-orange.svg)](https://gradio.app/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 目錄

- [專案概述](#專案概述)
- [系統架構](#系統架構)
- [功能特色](#功能特色)
- [安裝指南](#安裝指南)
- [使用說明](#使用說明)
- [專案結構](#專案結構)
- [技術文件](#技術文件)
- [論文貢獻](#論文貢獻)

---

## 📖 專案概述

### 研究背景

半導體製造業新人訓練面臨的挑戰：
- ❌ 真機操作風險高（設備價值數億）
- ❌ 訓練時間長（3-6 個月）
- ❌ 產品報廢成本高（良率損失）

### 解決方案

本系統提供：
- ✅ **安全的虛擬訓練環境**（數位孿生技術）
- ✅ **AI 專家即時指導**（A2A 多專家協作）
- ✅ **真實故障情境**（基於 SECOM 1500+ 筆資料）
- ✅ **自動化評分追蹤**（學習進度可視化）

### 預期效益

| 指標 | 改善幅度 |
|------|---------|
| 避免真機損壞 | ⬇️ 70% |
| 訓練時間縮短 | ⬇️ 50% |
| 產品報廢減少 | ⬇️ 60% |

---

## 🏗️ 系統架構

```
┌─────────────────────────────────────────────────────────┐
│                    Gradio 訓練介面                        │
│  (學員互動、情境顯示、操作輸入、評分報告)                    │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│              A2A 多專家協調系統                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 診斷專家  │  │ 操作專家  │  │ 安全專家  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│           曝光機數位孿生模擬器 (590 感測器)                 │
│        ┌──────────┐        ┌──────────┐                │
│        │ 正常狀態  │   ⟷   │ 故障狀態  │                │
│        └──────────┘        └──────────┘                │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│    SECOM 真實資料集 (1567 筆 × 590 感測器參數)             │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ 功能特色

### 1. 曝光機數位孿生 (Digital Twin)

- 🔬 **高擬真模擬**：590 個感測器參數
- 📊 **真實資料驅動**：基於 SECOM 資料集
- 🎯 **故障注入**：支援 5 種主要故障類型
  - 真空洩漏 (Vacuum Leak)
  - 溫度異常 (Temperature Spike)
  - 對準漂移 (Alignment Drift)
  - 光強度下降 (Optical Intensity Drop)
  - 電氣波動 (Electrical Fluctuation)

### 2. A2A 多專家系統 (Agent-to-Agent)

#### 診斷專家 (Diagnostic Agent)
- 分析設備異常徵兆
- 推斷故障根本原因
- 評估嚴重程度
- 提供診斷信心度

#### 操作專家 (Operation Agent)
- 提供詳細操作步驟
- 根據學員程度調整指引
- 設置操作檢查點
- 提供步驟提示

#### 安全專家 (Safety Agent)
- 監控操作安全性
- 識別禁止操作
- 要求必要防護裝備
- 提供緊急應變程序

### 3. 訓練情境生成器

- 📚 **情境庫**：5 種典型故障情境
- 🎲 **隨機生成**：支援難度分級（EASY/MEDIUM/HARD）
- ⏱️ **時間限制**：模擬真實時間壓力
- 📖 **學習目標**：每個情境附學習目標

### 4. 自動評分系統

評分維度（權重）：
- 📋 **診斷準確性** (30%)
- 🔧 **操作正確性** (40%)
- 🛡️ **安全合規性** (30%)
- ⏱️ **時間效率** (加分項)

等級評定：
- A: 90-100 分（優秀）
- B: 80-89 分（良好）
- C: 70-79 分（及格）
- D: 60-69 分（待加強）
- F: 0-59 分（不及格）

---

## 🚀 安裝指南

### 環境需求

- Python 3.8+
- 8GB+ RAM
- Pandas, NumPy, Gradio

### 本地安裝

```bash
# 1. Clone 專案
git clone <your-repo-url>
cd semiconductor_training_system

# 2. 安裝套件
pip install -r requirements.txt

# 3. 準備資料
# 下載 SECOM 資料集並放置到專案根目錄
# 檔案名稱: uci-secom.csv

# 4. 執行測試
python core/digital_twin.py
python core/a2a_coordinator.py
python core/scenario_generator.py

# 5. 啟動 Gradio 介面
cd interface
python gradio_app.py
```

### Google Colab 快速啟動

1. 開啟 [notebooks/Training_System_Colab.ipynb](notebooks/Training_System_Colab.ipynb)
2. 點擊「Open in Colab」
3. 依照筆記本指示執行

---

## 📘 使用說明

### 訓練流程

#### 步驟 1: 開始訓練
1. 輸入學員 ID（例如：STU001）
2. 選擇難度等級（EASY/MEDIUM/HARD）
3. 選擇學員程度（beginner/intermediate/advanced）
4. 點擊「🚀 開始新情境」

#### 步驟 2: 查看情境
- 閱讀情境描述
- 查看設備狀態摘要
- 檢查感測器資料表格

#### 步驟 3: 請求專家診斷
1. 切換到「🤖 AI 專家診斷」分頁
2. 點擊「🩺 請求專家診斷」
3. 查看三位專家的建議：
   - 診斷專家的故障分析
   - 操作專家的步驟指引
   - 安全專家的安全評估

#### 步驟 4: 執行操作
1. 切換到「🔧 執行操作」分頁
2. 依照專家建議輸入操作步驟
3. 點擊「✅ 執行步驟」
4. 查看操作記錄

#### 步驟 5: 提交診斷
1. 切換到「📝 提交診斷」分頁
2. 輸入您的診斷結果（例如：vacuum_leak）
3. 選擇診斷信心度
4. 點擊「📤 提交診斷」
5. 查看詳細評分報告

---

## 📁 專案結構

```
semiconductor_training_system/
├── README.md                      # 本文件
├── requirements.txt               # Python 套件需求
│
├── data/                          # 資料目錄
│   └── (存放 uci-secom.csv)
│
├── core/                          # 核心系統
│   ├── digital_twin.py            # 數位孿生模擬器
│   ├── a2a_coordinator.py         # A2A 協調器
│   ├── scenario_generator.py     # 情境生成器
│   │
│   └── agents/                    # AI 專家模組
│       ├── base_agent.py          # 基礎 Agent 類別
│       ├── diagnostic_agent.py    # 診斷專家
│       ├── operation_agent.py     # 操作專家
│       └── safety_agent.py        # 安全專家
│
├── evaluation/                    # 評估系統
│   └── scoring_system.py          # 評分系統
│
├── interface/                     # 使用者介面
│   └── gradio_app.py              # Gradio 網頁介面
│
└── notebooks/                     # Jupyter Notebooks
    └── Training_System_Colab.ipynb # Colab 整合版本
```

---

## 📚 技術文件

### API 文件

#### LithographyDigitalTwin

```python
from core.digital_twin import LithographyDigitalTwin

# 初始化
twin = LithographyDigitalTwin('uci-secom.csv')

# 注入故障
twin.inject_fault('vacuum_leak')

# 取得感測器狀態
status = twin.get_sensor_status('0')

# 取得所有感測器摘要
summary = twin.get_all_sensors_summary()

# 執行操作
result = twin.perform_action('reset_system')
```

#### A2ACoordinator

```python
from core.a2a_coordinator import A2ACoordinator

# 初始化
coordinator = A2ACoordinator()

# 啟動診斷會話
equipment_state = twin.export_current_state()
diagnosis = coordinator.start_diagnosis_session(
    equipment_state=equipment_state,
    student_level='beginner'
)

# 驗證學員操作
validation = coordinator.validate_student_action(
    action='檢查真空計',
    expected_step='檢查真空計讀數',
    fault_type='vacuum_leak'
)
```

#### ScenarioGenerator

```python
from core.scenario_generator import ScenarioGenerator

# 初始化
generator = ScenarioGenerator('uci-secom.csv')

# 生成單一情境
scenario = generator.generate_scenario(
    difficulty='MEDIUM',
    student_level='beginner'
)

# 生成訓練集
training_set = generator.generate_training_set(
    n_scenarios=10,
    difficulty_distribution={'EASY': 0.3, 'MEDIUM': 0.5, 'HARD': 0.2}
)
```

#### ScoringSystem

```python
from evaluation.scoring_system import ScoringSystem

# 初始化
scorer = ScoringSystem()

# 評估會話
evaluation = scorer.evaluate_session(
    student_id='STU001',
    scenario=scenario,
    student_actions=actions,
    diagnosis_result=diagnosis,
    completion_time=25.0
)

# 取得學員報告
report = scorer.get_student_report('STU001')
```

---

## 🎓 論文貢獻

### 研究創新點

1. **真實資料驅動的數位孿生**
   - 首次將 SECOM 工業資料集應用於訓練系統
   - 高擬真模擬（590 個感測器參數）

2. **A2A 多專家協作架構**
   - 診斷、操作、安全三專家協同
   - Agent-to-Agent 訊息傳遞機制

3. **完整的評估體系**
   - 多維度自動評分
   - 學習進度追蹤
   - 改進建議生成

### 實驗設計

建議進行以下實驗：

1. **對照組實驗**
   - 控制組：傳統課堂 + 真機訓練
   - 實驗組：本系統 + 真機驗證
   - 比較：訓練時間、測試成績、設備損壞率

2. **學習曲線分析**
   - 追蹤 30-50 名學員
   - 記錄每次訓練評分
   - 分析進步趨勢

3. **難度梯度實驗**
   - EASY → MEDIUM → HARD
   - 評估適應性學習效果

### 論文結構建議

```
第一章 緒論
  1.1 研究背景與動機
  1.2 研究目的
  1.3 論文架構

第二章 文獻探討
  2.1 半導體製造訓練
  2.2 數位孿生技術
  2.3 多專家系統
  2.4 機器學習評估

第三章 系統設計與實作
  3.1 系統架構
  3.2 數位孿生模擬器
  3.3 A2A 多專家系統
  3.4 訓練介面設計

第四章 實驗結果與分析
  4.1 實驗設計
  4.2 效益分析
  4.3 學習成效評估

第五章 結論與未來展望
  5.1 研究貢獻
  5.2 限制與挑戰
  5.3 未來研究方向
```

---

## 📊 資料集說明

### SECOM 資料集

- **來源**: UCI Machine Learning Repository / Kaggle
- **記錄數**: 1567 筆
- **欄位數**: 592 個（590 感測器 + 時間 + Pass/Fail）
- **時間範圍**: 2008/01/08 - 2008/12/10
- **異常比例**: 6.6% (104 筆異常)

### 感測器類別（本系統分類）

1. **Chamber Pressure** (0-99): 腔體壓力
2. **Temperature** (100-199): 溫度
3. **Flow Rate** (200-299): 氣體流量
4. **Electrical** (300-399): 電氣參數
5. **Optical Intensity** (400-499): 光學強度
6. **Alignment Accuracy** (500-589): 對準精度

---

## 🤝 貢獻指南

歡迎貢獻改進！

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

---

## 📝 授權

本專案僅供學術研究使用。

---

## 📧 聯絡方式

- 作者：碩士生
- 學校：長庚大學
- Email：[your-email]
- 論文指導教授：[advisor-name]

---

## 🙏 致謝

- 感謝指導教授的指導
- 感謝半導體業界專家提供實務建議
- 感謝 UCI / Kaggle 提供 SECOM 資料集

---

**⭐ 如果這個專案對您的研究有幫助，請給個 Star！**
