# 半導體微影設備虛擬訓練系統 — 完整系統說明
## 供 AI 輔助撰寫報告/論文使用

> **論文作者**：趙威豪（M1321114）  
> **學校**：長庚大學 碩士班  
> **論文期間**：2024–2026  
> **論文題目**：半導體微影設備虛擬訓練系統（基於數位孿生與自適應 AI 導師）

---

## 一、研究背景與問題

### 1.1 研究動機

半導體微影製程（Lithography）是積體電路製造中技術難度最高、成本最昂貴的核心步驟：

- 微影製程成本佔整體晶圓廠製造成本的 **30–35%**
- ASML DUV 微影機台單台採購成本**逾數千萬美元**
- 設備停機一小時的機會成本可達**數萬至十數萬美元**
- 操作此類設備需具備光學物理、製程控制與故障診斷的深厚知識

### 1.2 傳統訓練的痛點

| 問題 | 具體影響 |
|------|---------|
| 依賴實機機時 | 新進工程師需 2–4 週實機訓練，佔用昂貴設備時間 |
| 資深工程師全程陪同 | 消耗寶貴的資深人力資源 |
| 操作失誤後果嚴重 | 劑量設定錯誤、光罩裝卸失誤→觸發聯鎖停機→批量晶圓報廢 |
| 稀有故障無法練習 | 光罩污染、晶圓台誤差等高危故障極少發生，新人缺乏處理經驗 |

### 1.3 本研究的解決方案

開發一套以「設備數位孿生（Lithography Digital Twin）」為核心的**沉浸式虛擬訓練平台**：
- 第一人稱 3D 互動環境，完全取代初期實機接觸
- UCI SECOM 真實製程資料集驅動感測器模擬
- 本地端 Qwen LLM 多代理 AI 導師系統
- 自主評估設計（學員自行判斷操作順序）
- 自適應四模式教學（依學員表現動態調整）

---

## 二、目標設備：ASML DUV 微影機台

### 2.1 機台概述

本研究以 **ASML TWINSCAN NXT 系列 DUV（深紫外光，248 nm）微影機台**為虛擬訓練對象。

- **雙平台掃描架構**：一個平台進行晶圓量測對準、另一個同步曝光，最大化產能
- **光源**：KrF 準分子雷射（波長 248 nm）
- **投影比例**：4:1 縮小投影至晶圓光阻層

### 2.2 機台 11 個主要子系統（與 3D 訓練模型對應）

| 模組名稱 | 3D 模型 Mesh 群組 | 功能說明 |
|---------|-----------------|---------|
| 雷射光源 | `雷射光源` | KrF 準分子雷射，輸出 248 nm 脈衝雷射 |
| 照明系統 | `照明系統` | 均化雷射光束，設定 σ 相干度 |
| 光罩載台 | `光罩載台` | 承載並精密定位光罩 |
| 投影鏡組 | `投影鏡組` | 4× 縮小投影，關鍵 NA 控制 |
| 晶圓台 | `晶圓台` | 晶圓精密步進定位（nm 等級） |
| 液浸冷卻 | `液浸冷卻` | 冷卻水迴路維持鏡片溫度穩定 |
| 真空系統 | `真空系統` | 光路真空維持，防止空氣折射干擾 |
| 對準量測 | `對準量測` | 晶圓對準感測器，保障套刻精度 |
| 控制系統 | `控制系統` | 整機聯控 PLC/PC 系統 |
| HMI 螢幕 | `HMI 螢幕` | 虛擬人機介面，顯示感測器讀值 |
| 晶圓傳送 | `晶圓傳送` | 機械臂傳送晶圓 |

### 2.3 關鍵技術規格

| 參數 | 數值 |
|------|------|
| 光源波長 | 248 nm（KrF） |
| 數值孔徑 NA | 0.93（乾式）/ 1.35（浸潤式） |
| 解析度 | < 100 nm（乾式） |
| 焦深 DOF | ±150 nm（NA=0.93） |
| 套刻精度 Overlay | < 3 nm |
| CDU（3σ） | < 1.5 nm |
| 晶圓尺寸 | 300 mm |
| 產能（WPH） | ~275 wafers/hour |

---

## 三、DUV 微影製程流程（12 步驟）

1. **基板清洗（Wafer Clean）**：去除顆粒與有機污染
2. **底層薄膜沉積**：Hard Mask 或 ARC 沉積
3. **光阻塗佈（PR Coating）**：BARC + CAR 旋塗
4. **軟烘烤（Soft Bake / PAB）**：驅除殘留溶劑
5. **曝光（DUV 248nm Exposure）**：核心步驟，參數最複雜
6. **曝後烘烤（PEB）**：活化酸催化反應
7. **顯影（Develop）**：溶解曝光區域光阻
8. **檢測（Inspection / OCD）**：CD-SEM 或 OCD 量測
9. ⋯（後段 CMP、蝕刻等）

**曝光站核心物理方程式（系統使用）**：

```
Rayleigh 解析度：R = k₁ × λ / NA
焦深：DOF = k₂ × λ / NA²
Bossung Curve：CD = f(focus_offset, dose) — 二次曲線模型
鏡片熱方程式：T(t) = T₀ + ΔT × (1 - e^(-t/τ₁)) + ΔT₂ × (1 - e^(-t/τ₂))
```

---

## 四、系統整體架構（六層式垂直架構）

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1：資料來源層                                       │
│   UCI SECOM 資料集 (1,567 晶圓 × 590 感測器特徵)          │
│   + 設備數位孿生（Lithography Digital Twin）              │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2：AI 導師系統層                                    │
│   Qwen LLM（本地端）                                      │
│   ├─ AIScenarioMentor（蘇格拉底式對話）                    │
│   ├─ Diagnostic Agent（故障根因分析）                      │
│   ├─ Operation Agent（SOP 操作引導）                       │
│   └─ Adaptive Teaching / Competency Assessment           │
│      自適應四模式：挑戰/標準/鷹架/補救                     │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3：後端服務層（Python http.server，Port 8765）       │
│   REST API：8 個端點（4 GET + 4 POST）                    │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 4：使用者介面層                                     │
│   Three.js WebGL 第一人稱 3D 環境                         │
│   + HTML5 Canvas 虛擬 HMI 面板                           │
│   + AI 對話面板（[C] 鍵開啟）                             │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 5：訓練流程層                                       │
│   整合式設計（理論問答 + 3D 實機操作同步進行）              │
│   5 種故障情境 × 自主評估設計                             │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 6：評分系統層                                       │
│   三維度加權評分 → A-F 五級制能力認證                     │
└─────────────────────────────────────────────────────────┘
```

---

## 五、資料來源：UCI SECOM 資料集

### 5.1 資料集概述

- **來源**：UCI Machine Learning Repository（2008年）
- **全稱**：Semiconductor Equipment COMputer Monitoring
- **規模**：1,567 筆晶圓量測記錄 × 590 個感測器特徵
- **標記**：通過（1,463 筆，Pass/Fail = -1）/ 失敗（104 筆，Pass/Fail = 1）
- **特徵**：溫度、壓力、流量、電氣、光學等製程感測器讀值

### 5.2 本系統的使用方式

SECOM 資料集在本系統中的角色**不是**預測 CD 或良率，而是：

1. **建立製程雜訊模型**（SecomNoiseModel）：
   - 對 590 個特徵執行 PCA，萃取前 20 個主成分
   - 以 Pass 樣本的殘差分布建立「正常製程雜訊」統計模型
   - 以 Fail 樣本特徵識別「異常製程狀態」

2. **計算設備健康分數**（health_score，0~1）：
   - 依據 PCA 投影座標計算
   - 直接調變 CD 預測雜訊標準差：
     - 正常狀態：σ = 1.5 nm
     - 故障狀態：σ = 3.0~4.8 nm（依健康分數線性插值）

3. **驅動虛擬 HMI 面板**：
   - 590 個感測器即時讀值符合真實統計分布
   - CDU Map 空間分布圖
   - CD 趨勢圖（含 3σ 控制線）

### 5.3 資料前處理流程

```
原始 SECOM CSV（1,567 × 590）
    ↓ 填補 NaN（各欄中位數）
    ↓ PCA 降維（590 → 20 主成分）
    ↓ 分離 Pass / Fail 樣本
    ↓ 計算各特徵 mean, std, skewness
    ↓ 建立正常雜訊分布模型（正偏態，skewness=0.12）
    ↓ 供即時模擬使用
```

---

## 六、物理模型（PhysicsCouplingModel）

系統整合以下物理方程式，提供比純隨機雜訊更真實的製程退化模擬：

### 6.1 Bossung Curve（焦距–劑量–CD 關係）

```
CD(focus, dose) = CD₀ + α×(focus)² + β×(dose-dose₀) + γ×focus×dose
```
- 用於模擬焦距偏移與劑量漂移對線寬的影響
- 訓練中學員可在 HMI 觀察 CDU Map 的退化趨勢

### 6.2 鏡片熱模型（雙指數）

```
ΔT(t) = ΔT₁×(1-e^(-t/τ₁)) + ΔT₂×(1-e^(-t/τ₂))
```
- τ₁（快速熱時間常數）≈ 200s：鏡片本體
- τ₂（慢速熱時間常數）≈ 800s：鏡框結構
- 鏡片過熱→折射率變化→Overlay 誤差增加

### 6.3 Overlay 誤差模型

```
Overlay = Stage_Error + Lens_Aberration(Zernike Z7/Z8) + Thermal_Expansion
```

---

## 七、五種故障情境與 SOP 步驟定義

本系統提供五種製程故障情境，每種含 5 個有序 SOP 步驟：

### 7.1 鏡片熱點（lens_hotspot）

| 步驟 | 操作零件 | 動作關鍵詞 | 工程原因 |
|------|---------|-----------|---------|
| 1 | 投影鏡組 | 溫度/溫升/查看 | 確認鏡片溫升量，判斷嚴重程度 |
| 2 | 控制系統/雷射光源/HMI | dose/降低/減少 | 降低 dose 減少熱輸入，阻止溫升惡化 |
| 3 | 投影鏡組/控制系統 | 停止/等待/冷卻 | 停止曝光讓鏡片自然冷卻 |
| 4 | 液浸冷卻 | 冷卻水/流量/水溫 | 確認冷卻水迴路正常 |
| 5 | 控制系統/HMI | 恢復/監控/CDU | 恢復曝光並驗證 CDU 回到規格內 |

### 7.2 光罩污染（contamination）

| 步驟 | 操作零件 | 動作關鍵詞 | 工程原因 |
|------|---------|-----------|---------|
| 1 | 光罩載台/控制系統 | 光源/強度/確認/污染 | 光罩污染→光源強度下降，先確認異常位置 |
| 2 | 光罩載台/控制系統 | 卸載/停機/取出 | 處理光罩前必須先停機 |
| 3 | 光罩載台 | 目視/檢查/表面 | 找出污染位置與類型 |
| 4 | 光罩載台 | 清潔/更換 | 輕微可清潔，嚴重需更換 |
| 5 | 光罩載台/控制系統 | 裝回/對準/驗證 | 確認對準精度符合規格 |

### 7.3 晶圓台位置誤差（stage_error）

5 個步驟：確認 Overlay → 停機 → 診斷台位移 → 校正 → 驗證 Overlay

### 7.4 劑量漂移（dose_drift）

5 個步驟：確認 dose 讀值異常 → 停機 → 檢查雷射能量監測器 → 調整 dose 設定 → 驗證 CDU

### 7.5 焦距漂移（focus_drift）

5 個步驟：確認 Focus Map 異常 → 停機 → 檢查 AF 感測器 → 重新對焦校正 → 驗證 CDU/Overlay

### SOP 判斷邏輯

```
正確條件：零件比對（精確匹配）AND 動作比對（模糊關鍵詞包含）
答對：不扣分，給予正向回饋
答錯：-10 分，給予糾正提示
求助學長：-5 分，給出方向性提示（hint_component + hint_action）
```

---

## 八、自適應教學系統

### 8.1 四種教學模式

| 模式 | 觸發條件 | 回饋風格 |
|------|---------|---------|
| **挑戰模式（Challenge）** | 連續答對 ≥ 3 次 | 簡潔回饋，無額外提示，提升難度 |
| **標準模式（Standard）** | 預設模式 | 適量提示，平衡回饋 |
| **鷹架模式（Scaffolding）** | 連續答錯 ≥ 3 次 | 頻繁提示，詳細分解步驟 |
| **補救模式（Remedial）** | 連續答錯 ≥ 5 次 | 提供 reason 工程原因，超詳細引導，回到基礎概念 |

### 8.2 AI 評分驅動機制

除了 SOP 操作外，AI 對話問答也有評分（0–10 分）：

- ≥ 8.5 分（UnderstandingLevel.EXCELLENT）→ 挑戰模式
- ≥ 6.5 分（UnderstandingLevel.GOOD）→ 標準模式
- ≥ 4.0 分（UnderstandingLevel.FAIR）→ 鷹架模式
- < 4.0 分（UnderstandingLevel.POOR/VERY_POOR）→ 補救模式

### 8.3 知識點追蹤（KnowledgeTracker）

系統分 6 個主題追蹤學員知識掌握度：

| 主題分類 | 關鍵詞 |
|---------|--------|
| thermal | 熱膨脹、溫度、冷卻、散熱 |
| vacuum | 真空、壓力、泵浦、洩漏 |
| optical | 光學、對準、曝光、光強 |
| mechanical | 機械、定位、振動、磨損 |
| chemical | CVD、蝕刻、沉積、清洗 |
| electrical | 電源、電壓、電流、接地 |

---

## 九、使用者介面（Frontend）

### 9.1 技術棧

- **3D 引擎**：Three.js（WebGL）
- **3D 模型**：asml_duv.glb（GLB 格式，GLTF 二進位）
- **相機控制**：PointerLock API（第一人稱視角）
- **HMI 渲染**：HTML5 Canvas 2D API
- **通訊**：fetch API → REST API（localhost:8765）

### 9.2 鍵盤操作

| 按鍵 | 功能 |
|------|------|
| W/A/S/D | 移動 |
| 滑鼠移動 | 視角旋轉 |
| E | 與近距零件互動（開啟零件操作面板） |
| C | 開啟/關閉 AI 對話面板 |
| ESC | 釋放滑鼠 |

### 9.3 零件互動流程

```
受訓者靠近零件 → 準心對準（Raycaster 偵測）→ 按 [E]
    ↓
出現「🔍 檢查」與「⚙ 操作」兩類按鈕
    ↓
受訓者自行選擇操作
    ↓
POST /api/action → SOP 比對評估
    ↓
AI 即時回饋文字（答對/答錯）+ 分數更新
    ↓
依連續答對/錯次數切換自適應教學模式
```

### 9.4 故障視覺化

- 故障發生時：對應 Mesh 群組**橘色發光提示**
- HMI 面板：相關感測器讀值進入警報範圍（紅色）
- CDU Map：空間分布異常（顏色梯度變化）
- AI 對話框：顯示故障警報通知

---

## 十、後端 API 端點規格

### REST API（Python http.server，Port 8765）

| 方法 | 端點 | 功能 |
|------|------|------|
| GET | `/api/hmi` | 取得 590 個感測器即時讀值 + CDU Map |
| GET | `/api/tick` | 系統時間步進，更新感測器狀態 |
| GET | `/api/summary` | 取得當前訓練會話摘要與評分 |
| GET | `/api/wafer_map` | 取得晶圓 Overlay 向量場資料 |
| POST | `/api/chat` | AI 導師對話（蘇格拉底式問答） |
| POST | `/api/action` | 提交零件操作，取得 SOP 評估結果 |
| POST | `/api/fault` | 注入/清除故障情境 |
| POST | `/api/start` | 開始新訓練會話（指定情境） |

---

## 十一、評分系統（ScoringSystem）

### 11.1 三維度加權評分（滿分 100 分）

| 維度 | 權重 | 評估內容 |
|------|------|---------|
| 診斷準確性（Diagnostic Accuracy） | 30% | 故障類型判斷正確性 + 信心度加權 |
| 操作正確性（Operation Correctness） | 40% | SOP 步驟符合度 + 操作順序 |
| 安全合規性（Safety Compliance） | 30% | PPE 穿戴 + 安全規範遵守 |
| 時間效率（Time Efficiency） | 加分 | 實際完成時間 vs 標準時限比率 |

### 11.2 A–F 五級制能力認證

| 等級 | 分數範圍 | 說明 |
|------|---------|------|
| A | ≥ 90 分 | 優秀，系統推薦進階訓練 |
| B | ≥ 80 分 | **合格，取得能力認證** |
| C | ≥ 70 分 | 尚可，建議再練習 |
| D | ≥ 60 分 | 不足，需加強 |
| F | < 60 分 | 未達標，建議重新訓練 |

---

## 十二、技術架構關鍵檔案

### 12.1 後端核心檔案

```
semiconductor_training_system/
├── core/
│   ├── digital_twin.py          — 數位孿生主系統（LithographyDigitalTwin 類別）
│   ├── secom_noise_model.py     — SECOM 資料驅動雜訊模型（SecomNoiseModel 類別）
│   ├── physics_coupling_model.py — Bossung Curve + 鏡片熱方程式
│   ├── lens_heating_model.py    — 雙指數鏡片熱模型
│   ├── sop_definitions.py       — 五種故障 SOP 步驟定義 + 評估引擎
│   ├── adaptive_teaching_strategy.py — 自適應四模式教學策略
│   ├── competency_assessment.py — 能力評估與學習歷程記錄
│   ├── a2a_coordinator.py       — 多代理協調器（A2A 架構）
│   ├── ai_scenario_mentor.py    — AI 導師（蘇格拉底式引導）
│   ├── scenario_engine.py       — 故障情境引擎
│   └── agents/
│       ├── diagnostic_agent.py  — 故障診斷代理
│       ├── operation_agent.py   — 操作引導代理
│       └── safety_agent.py      — 安全合規代理
├── static/
│   ├── viewer.html              — 主前端（Three.js 3D 環境 + AI 對話介面）
│   ├── asml_duv.glb             — ASML DUV 3D 模型（GLB 格式）
│   ├── three.min.js             — Three.js 函式庫
│   ├── GLTFLoader.js            — GLB 載入器
│   └── PointerLockControls.js   — 第一人稱相機控制器
├── evaluation/
│   └── scoring_system.py        — 三維度評分系統
└── run_training_system.py        — 一鍵啟動腳本
```

### 12.2 前端關鍵技術實作

```javascript
// 第一人稱相機控制
const controls = new PointerLockControls(camera, renderer.domElement);

// 零件互動（Raycaster）
const raycaster = new THREE.Raycaster();
// 靠近零件 + 按 E → 觸發互動面板

// SOP 動作評估
fetch('/api/action', {method:'POST', body: JSON.stringify({
    component: selectedComponent,  // 前端 label 精確比對
    action: selectedAction,         // 模糊關鍵詞比對
    scenario: currentScenario
})})

// AI 對話
fetch('/api/chat', {method:'POST', body: JSON.stringify({
    message: userInput,
    scenario: currentScenario
})})
```

---

## 十三、多代理 AI 架構

### 13.1 代理分工

```
A2ACoordinator（總協調器）
    ├─ AIScenarioMentor     ← 蘇格拉底式對話，依情境生成差異化問題
    ├─ Diagnostic Agent     ← 故障根本原因分析（RCA）
    ├─ Operation Agent      ← 逐步操作引導、SOP 管理
    ├─ Safety Agent         ← PPE/安全規範提醒
    └─ Adaptive Teaching    ← 評分驅動模式切換、學習歷程記錄
```

### 13.2 LLM 選型：本地端 Qwen

- **選擇理由**：晶圓廠資安要求嚴格，不可連網外部 API
- **部署方式**：Ollama 或 llama.cpp 後端，完全本地端推理
- **模型**：Qwen（通義千問，阿里巴巴開發）
- **優點**：中文能力強、技術領域理解佳、可本地端部署

---

## 十四、訓練流程設計特點

### 14.1 整合式設計（無分離測驗）

與傳統「先通過理論測驗、再做實機操作」不同，本系統採**整合式設計**：
- 受訓者進入 3D 環境後，理論學習與實機操作同時展開
- AI 導師根據輸入內容**動態切換**理論引導或實作指引
- 無需先通過任何獨立的理論測驗門檻

### 14.2 自主評估設計（非逐步指引）

與傳統 SOP 訓練系統「按步驟指引操作」不同：
- 受訓者**自行判斷**應對哪個零件執行何種操作
- 系統評估操作是否符合當前 SOP 步驟
- 訓練「解讀設備狀態、自主決策」的工程師核心能力

### 14.3 求助學長機制

- 按「求助學長」按鈕：**扣 5 分**（而非直接告知答案）
- 獲得方向性提示：「你應該去看 [hint_component] 的 [hint_action]」
- 在提供安全網的同時，保留主動思考的激勵誘因

---

## 十五、預期研究成果

### 15.1 訓練效益

| 指標 | 傳統訓練 | 本系統（預期） |
|------|---------|-------------|
| 達到上機資格所需時間 | 2–4 週 | 縮短 50% 以上 |
| 實機操作失誤率 | 高（初學者） | 顯著降低 |
| 晶圓報廢風險 | 存在 | 零（虛擬環境） |
| 機台停機風險 | 存在 | 零（虛擬環境） |
| 資深工程師陪同需求 | 全程需要 | 不需要（AI 導師） |
| 時間/地點限制 | 機台有空才能訓練 | 任意時間/地點瀏覽器開啟 |

### 15.2 學術貢獻

1. **方法論貢獻**：以公開資料集（UCI SECOM）驅動設備數位孿生感測器的完整技術路徑
2. **系統驗證**：本地端 LLM（Qwen + Ollama）結合製程領域知識庫的 AI 導師可行性
3. **工程實作**：Three.js WebGL 設備 3D 互動建模工作流程，供半導體教育領域參考
4. **後續基礎**：多設備擴充（ALD、PVD、CMP）、多人協同訓練、計量量測整合

---

## 十六、名詞解釋

| 術語 | 解釋 |
|------|------|
| DUV | Deep Ultraviolet，深紫外光，波長 100–300 nm |
| KrF | 氪氟準分子雷射，波長 248 nm |
| CD | Critical Dimension，臨界尺寸，最小特徵線寬（nm） |
| CDU | CD Uniformity，線寬均勻性，以 3σ 表示 |
| Overlay | 疊對誤差，不同微影層間圖案對準偏差（nm） |
| NA | Numerical Aperture，數值孔徑，描述光學系統收光能力 |
| DOF | Depth of Focus，焦深 |
| SECOM | Semiconductor Equipment COMputer Monitoring |
| PCA | Principal Component Analysis，主成分分析 |
| HMI | Human-Machine Interface，人機介面 |
| APC | Advanced Process Control，先進製程控制 |
| SOP | Standard Operating Procedure，標準作業程序 |
| GLB | GL Transmission Format Binary，3D 模型格式 |
| PointerLock | 瀏覽器 API，鎖定滑鼠游標用於第一人稱視角控制 |
| Raycaster | 射線投射，用於偵測 3D 場景中物件交點 |
| Qwen | 通義千問，阿里巴巴開發的大型語言模型 |
| A2A | Agent-to-Agent，多代理系統架構 |
| Bossung Curve | 焦距-劑量-CD 三維關係曲線 |
| Zernike | 用於描述光學像差的正交多項式 |

---

## 十七、參考文獻

1. ASML. (2023). *TWINSCAN NXT:2050i Product Specifications*. ASML Technical Documentation.
2. McCord, M.A. & Rooks, M.J. (2000). *Handbook of Microlithography, Micromachining, and Microfabrication*. SPIE Press.
3. Mack, C. (2007). *Fundamental Principles of Optical Lithography*. Wiley-Interscience.
4. Smith, B.W. (2007). *Microlithography: Science and Technology, 2nd ed*. CRC Press.
5. UCI Machine Learning Repository. (2008). *SECOM Dataset*. UC Irvine.
6. Zernike, F. (1934). Diffraction theory of the knife-edge test. *Monthly Notices RAS*, 94, 377–384.
7. Bossung, J.W. (1977). Projection printing characterization. *SPIE*, 100, 80–84.
8. Three.js Documentation. (2024). https://threejs.org/docs/
9. 張，等. (2023). *半導體製程技術概論*. 全華圖書.

---

*本文件由 Claude Code 根據系統完整程式碼與架構文件自動生成，版本日期：2026-04-20*
