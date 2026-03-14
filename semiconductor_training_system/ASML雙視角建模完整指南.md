# ASML 雙視角建模完整指南

## 📸 你提供的兩張官方圖片

### 圖片 1：NXT:870B（剖面視圖）
- **視角**：側視圖，切開展示內部
- **重點**：內部結構，粉紅色光學系統
- **機型**：NXT:870B KrF scanner

### 圖片 2：NXT:2150i（俯視圖）
- **視角**：俯視圖，從上往下看
- **重點**：整體布局，左右對稱
- **機型**：NXT:2150i（更新型號）

---

## 🎯 圖片 2 的關鍵資訊

### 1. **俯視圖布局**（從上往下看）

```
左側設備：              Wafer               右側設備：
┌──────────┐          ┌────┐            ┌──────────┐
│ New reticle│   ←───  │圓形 │  ───→     │Conditioned│
│ heating   │          │晶圓 │            │ reticle  │
│ control   │          └────┘            │ library  │
├──────────┤                             ├──────────┤
│          │                             │          │
│  ASML    │                             │  ASML    │
│          │                             │          │
│  控制面板 │                             │  儲存櫃  │
└──────────┘                             └──────────┘
```

### 2. **關鍵零件標示**（左側文字）

```
✅ New reticle heating control
   → 光罩加熱控制

✅ Conditioned reticle library
   → 光罩儲存櫃（溫控）

✅ Scanner metrology software
   → 掃描量測軟體

✅ Alignment 12 colors
   → 12色對準系統

✅ Optical sensors
   → 光學感測器

✅ Optical correction elements
   → 光學校正元件

✅ Wafer table
   → Wafer 載台
```

### 3. **右側對比表**

```
機型對比：
┌──────────────┬───────────┬───────────┐
│              │ NXT:2100i │ NXT:2150i │
├──────────────┼───────────┼───────────┤
│ Throughput   │ ≥295 WpH  │ ≥310 WpH  │
│ MMO¹         │ ≤1.3 nm   │ ≤1.0 nm   │
│ EUV-DUV      │ 1.7nm     │ 1.5nm     │
│ On Product   │ ≤1.7 nm   │ ≤1.5 nm   │
└──────────────┴───────────┴───────────┘
```

---

## 🏗️ 整合兩張圖的建模策略

### 關鍵發現

**圖片 1**：
- ✅ 提供側視圖（內部結構）
- ✅ 粉紅色光學系統清楚
- ✅ 高度和深度比例

**圖片 2**：
- ✅ 提供俯視圖（整體布局）
- ✅ 左右對稱結構清楚
- ✅ 寬度和長度比例

**結合使用**：
- ✅ 側視圖 = 垂直結構
- ✅ 俯視圖 = 水平布局
- ✅ 兩者結合 = 完整 3D 模型

---

## 🎨 更新的建模流程

### Day 1：外殼結構（根據俯視圖）

#### 步驟 1：主體結構

```
根據圖片 2 的俯視圖：

1. 中央主體（白色）
   • 從俯視圖看：長方形
   • 從側視圖看：高度約 4-5 單位

2. 左側設備（控制面板區）
   • 俯視圖：突出的方形區域
   • 側視圖：與主體同高
   • 顏色：白色 + ASML 藍色

3. 右側設備（儲存櫃區）
   • 俯視圖：突出的方形區域
   • 側視圖：較矮，約主體 2/3 高
   • 顏色：白色 + ASML 藍色

4. 中央晶圓傳輸口
   • 俯視圖：圓形開口（中間）
   • 側視圖：貫穿整個高度
```

#### Blender 操作

```
1. 創建主體：
   • Add → Cube
   • Scale: X=4, Y=6, Z=4
   • 材質：白色

2. 創建左側設備：
   • Add → Cube
   • Scale: X=1.5, Y=2, Z=4
   • Position: X=-3, Y=-1, Z=0
   • 材質：白色 + 藍色面板

3. 創建右側設備：
   • Add → Cube
   • Scale: X=1.5, Y=2, Z=2.5
   • Position: X=+3, Y=-1, Z=0
   • 材質：白色 + 藍色面板

4. 創建中央開口：
   • Boolean → Difference
   • 在主體中央切出圓形洞
```

### Day 2：內部光學系統（根據側視圖）

```
參考圖片 1 的粉紅色部分：

1. 主光學柱
   • Add → Cylinder
   • Radius: 1.2
   • Height: 3.5
   • Position: 中央，高度 1-4.5

2. 粉紅色發光材質
   • Shader: Emission
   • Color: RGB(1.0, 0.4, 0.6)
   • Strength: 2.5

3. 玻璃鏡頭組
   • 在光學柱內添加多層圓盤
   • 材質：Glass (Transmission: 0.6)
```

### Day 3：Wafer 載台系統

#### 根據圖片 2 的 "Wafer table"

```
1. 主載台（底部中央）
   • Add → Cylinder
   • Radius: 2.0
   • Height: 0.3
   • Position: Y=0, Z=-1.5

2. Wafer（晶圓）
   • Add → Cylinder
   • Radius: 1.5
   • Height: 0.01
   • 材質：銀灰色，高反射

3. 移動機構
   • 載台下方添加 X-Y 移動軌道
   • 使用小型 Cube 組合
```

### Day 4：Reticle 系統

#### 根據圖片 2 的標示

```
1. Reticle 載台（光學系統上方）
   • Add → Cube
   • Scale: (2, 2, 0.2)
   • Position: Y=0, Z=3.5

2. Reticle heating control（左側）
   • 小型加熱器模組
   • 紅色/橙色 Emission 材質

3. Conditioned reticle library（右側）
   • 儲存櫃結構
   • 多層架子
```

### Day 5：對準與感測系統

#### 根據圖片 2 的 "Alignment 12 colors"

```
1. Optical sensors
   • 12 個小型感測器
   • 環繞光學系統排列
   • 每個不同顏色（12色對準）

2. 感測器光束
   • Add → Curve
   • Emission 材質
   • 12 種顏色：
     紅、橙、黃、綠、青、藍、紫、粉、白、灰...
```

### Day 6：細節與材質

```
1. ASML Logo（兩處）
   • 左側設備
   • 右側設備

2. 控制面板螢幕（左側）
   • 藍色發光螢幕
   • 按鈕細節

3. 通風格柵
   • 上方和側面
   • 使用 Array Modifier 排列

4. 管路連接
   • 左右設備與主體的連接管
   • 藍色/灰色
```

### Day 7：光源與渲染

```
1. 場景光源
   • HDRI 環境光（無塵室照明）
   • 3-Point Lighting

2. 內部發光
   • 粉紅光學系統（最亮）
   • 螢幕（藍光）
   • 感測器（多色）
   • Reticle 加熱器（紅光）

3. 測試渲染
   • Cycles 引擎
   • Samples: 128
   • Denoising: 開啟
```

### Day 8：命名與導出

```
1. 零件命名（對應程式碼）：
   ├─ MainBody
   ├─ LeftModule
   ├─ RightModule
   ├─ LensSystem ← 關鍵（粉紅色）
   ├─ WaferStage ← 關鍵
   ├─ ReticleStage ← 關鍵
   ├─ CoolingSystem ← 關鍵（左側管路）
   ├─ VacuumChamber ← 關鍵（中央）
   ├─ AlignmentSystem ← 關鍵（12色感測器）
   └─ LightSource ← 關鍵（光學系統內）

2. 優化多邊形：
   • Decimate: Ratio 0.7
   • 目標：< 80k polygons

3. 導出：
   • File → Export → glTF 2.0
   • Format: Binary (.glb)
   • Include: All
   • Compression: 開啟
   • 命名：duv_machine_nxt2150i.glb
```

---

## 📐 精確尺寸（基於兩張圖）

### 整體尺寸（Blender 單位）

```
主體：
  X (寬): 4 單位
  Y (長): 6 單位
  Z (高): 4 單位

左側模組：
  X: 1.5 單位
  Y: 2 單位
  Z: 4 單位（與主體同高）

右側模組：
  X: 1.5 單位
  Y: 2 單位
  Z: 2.5 單位（較矮）

總寬度（含左右模組）：
  X: 4 + 1.5 + 1.5 = 7 單位
```

### 內部零件

```
光學系統：
  Radius: 1.2 單位
  Height: 3.5 單位
  Position: 中央，高度 0.5-4

Wafer 載台：
  Radius: 2.0 單位
  Height: 0.3 單位
  Position: 底部，Z=-1.5

Reticle 載台：
  Size: 2×2×0.2 單位
  Position: 頂部，Z=3.5

感測器（12個）：
  Radius: 0.1 單位
  Position: 環繞光學系統，間隔 30°
```

---

## 🎨 完整配色方案

### 外殼配色

```
主體外殼：
  Base Color: RGB(240, 240, 240) 白色
  Metallic: 0.1
  Roughness: 0.4

ASML 藍色區域：
  Base Color: RGB(50, 100, 200) ASML 藍
  Metallic: 0.6
  Roughness: 0.3

ASML Logo：
  Base Color: RGB(255, 255, 255) 白色
  在藍色背景上
```

### 內部零件配色

```
粉紅光學系統：⭐ 最重要
  Base Color: RGB(255, 100, 150)
  Emission Color: RGB(255, 100, 150)
  Emission Strength: 2.5
  Metallic: 0.8
  Roughness: 0.2

Wafer 載台：
  Base Color: RGB(50, 50, 50) 深灰
  Metallic: 0.9
  Roughness: 0.3

晶圓（Wafer）：
  Base Color: RGB(180, 180, 200) 銀灰
  Metallic: 1.0
  Roughness: 0.1

Reticle 載台：
  Base Color: RGB(80, 80, 80) 灰色
  Metallic: 0.8
  Roughness: 0.4
```

### 發光零件

```
螢幕（藍光）：
  Emission: RGB(100, 150, 255)
  Strength: 1.5

Reticle 加熱器（紅光）：
  Emission: RGB(255, 100, 50)
  Strength: 2.0

12色感測器：
  顏色1: RGB(255, 0, 0) 紅
  顏色2: RGB(255, 127, 0) 橙
  顏色3: RGB(255, 255, 0) 黃
  顏色4: RGB(0, 255, 0) 綠
  顏色5: RGB(0, 255, 255) 青
  顏色6: RGB(0, 0, 255) 藍
  顏色7: RGB(127, 0, 255) 紫
  顏色8: RGB(255, 0, 255) 品紅
  ... (依序 12 種顏色)
  Emission Strength: 1.0
```

---

## 🎬 Blender 詳細操作（Day 1 範例）

### 第一步：設定參考圖

```
1. 開啟 Blender
2. Delete 預設的 Cube
3. Add → Image → Reference
   • 載入圖片 1（側視圖）
   • Rotation: X=90° (轉成側視角)
   • Position: X=10 (移到右側參考)

4. Add → Image → Reference
   • 載入圖片 2（俯視圖）
   • Rotation: X=0° (保持俯視角)
   • Position: Z=10 (移到上方參考)

5. 切換視角對照：
   • Numpad 3 → 右視圖（看圖片1）
   • Numpad 7 → 頂視圖（看圖片2）
```

### 第二步：創建主體外殼

```
1. Add → Mesh → Cube
2. Scale:
   • S → 2 (整體放大2倍)
   • S, X, 2 (X軸再放大2倍)
   • S, Y, 3 (Y軸放大3倍)
   • S, Z, 2 (Z軸放大2倍)
   • 結果：4×6×4 單位

3. 位置：
   • G, Z, 2 (往上移2單位，底部在地面)

4. 材質：
   • Material Properties → New
   • Base Color: 設為白色 (0.95, 0.95, 0.95)
   • Metallic: 0.1
   • Roughness: 0.4
   • 命名：WhiteShell
```

### 第三步：創建 ASML 藍色區域

```
1. 選擇主體 Cube
2. Tab (進入 Edit Mode)
3. Face Select (3鍵)
4. 選擇正面左側的面
5. I (Inset) → 0.1 (內縮)
6. E (Extrude) → 0.1 (擠出)
7. 選擇這個擠出的面
8. 指定新材質：
   • Material Properties → + → New
   • Base Color: ASML 藍 (0.2, 0.4, 0.8)
   • Metallic: 0.6
   • Roughness: 0.3
   • 命名：ASMLBlue
9. Assign (指定材質)
10. Tab (回到 Object Mode)
```

### 第四步：創建左側控制模組

```
1. Add → Mesh → Cube
2. Scale:
   • S, X, 0.75 (X軸縮小)
   • S, Y, 1 (Y軸保持)
   • S, Z, 2 (Z軸放大)
   • 結果：1.5×2×4 單位

3. 位置：
   • G, X, -3 (往左移3單位)
   • G, Y, -1 (往前移1單位)
   • G, Z, 2 (往上移2單位)

4. 材質：
   • 複製主體的 WhiteShell 材質
   • 前面添加 ASMLBlue 區域（同上方法）
```

### 第五步：創建右側儲存模組

```
1. 複製左側模組：
   • 選擇左側模組
   • Shift + D (Duplicate)
   • X, 6 (往右移6單位)
   • 確認 (Enter)

2. 調整高度（右側較矮）：
   • S, Z, 0.625 (Z軸縮小到2.5單位)
   • G, Z, -0.75 (往下調整對齊地面)
```

### 第六步：創建中央圓形開口

```
1. 選擇主體 Cube
2. Tab (Edit Mode)
3. Face Select
4. 選擇頂面
5. I (Inset) → 調整大小到適當圓形區域
6. E (Extrude) → -4 (往下擠出穿透底部)
7. X → Faces (刪除面)
8. A (全選) → Alt+M → At Center (合併重疊頂點)
9. Tab (Object Mode)
```

---

## 📊 時間規劃（更新）

| 天數 | 任務 | 時間 | 難度 |
|------|------|------|------|
| Day 1 | 外殼結構（左中右三部分） | 4h | ⭐⭐ |
| Day 2 | 粉紅光學系統 | 3h | ⭐⭐⭐ |
| Day 3 | Wafer 載台系統 | 2h | ⭐⭐ |
| Day 4 | Reticle 系統 | 2h | ⭐⭐ |
| Day 5 | 12色對準感測器 | 3h | ⭐⭐⭐ |
| Day 6 | 細節與管路 | 2h | ⭐⭐ |
| Day 7 | 材質與光源 | 2h | ⭐⭐⭐ |
| Day 8 | 命名與導出 | 1h | ⭐ |
| **總計** | | **19h** | |

**實際工作天數**：3-4 天（集中工作）

---

## 🎯 關鍵視覺元素（必做！）

### 1. 粉紅色光學系統（圖片1）⭐⭐⭐⭐⭐
```
這是最吸引眼球的特徵
必須有強烈的發光效果
Emission Strength: 2.5-3.0
```

### 2. 12色對準感測器（圖片2）⭐⭐⭐⭐
```
環繞光學系統的彩色光點
12種不同顏色
展現技術複雜度
```

### 3. 左右對稱布局（圖片2）⭐⭐⭐⭐
```
左側：控制模組（藍色面板）
中間：主體設備（白色）
右側：儲存模組（較矮）
展現專業工業設計
```

### 4. ASML Logo（兩張圖都有）⭐⭐⭐⭐
```
藍色區域上的白色 Logo
清楚可見
品牌識別
```

---

## 📚 論文引用

**參考文獻**：
```
[1] ASML. (2024). NXT:870B KrF Scanner Technical Overview.
    ASML Official Presentation, November 14, 2024, Page 21.

[2] ASML. (2024). NXT:2150i DUV Lithography System.
    ASML Official Presentation, November 14, 2024, Page 22.
```

**模型說明**：
> "本研究基於 ASML 官方技術文件（NXT:870B 與 NXT:2150i），整合側視剖面圖與俯視布局圖，使用 Blender 3D 建模軟體精確還原設備外觀、內部光學系統、雙載台結構、12色對準感測器及晶圓傳輸系統。"

---

## ✅ 完成檢查清單

### 外觀檢查
```
□ 左中右三部分結構清楚
□ 白色外殼 + 藍色 ASML 區域
□ ASML Logo 清楚可見
□ 比例符合官方圖片
□ 中央圓形開口正確
```

### 內部檢查
```
□ 粉紅色光學系統發光 ⭐
□ Wafer 載台在底部
□ Reticle 載台在上方
□ 12色感測器環繞
□ 各零件正確命名
```

### 材質檢查
```
□ 金屬材質有反射
□ 玻璃材質有透明
□ 發光材質有光暈
□ 顏色符合官方配色
```

### 技術檢查
```
□ 多邊形數 < 100k
□ 檔案大小 < 20MB
□ .glb 格式正確
□ 在 Three.js 中可載入
```

---

## 🎉 預期最終效果

**視覺品質**：
```
外觀：⭐⭐⭐⭐⭐（官方還原）
內部：⭐⭐⭐⭐⭐（結構完整）
配色：⭐⭐⭐⭐⭐（官方配色）
發光：⭐⭐⭐⭐⭐（粉紅光學 + 12色感測）
專業度：⭐⭐⭐⭐⭐（可用於論文）
```

**論文價值**：
```
引用依據：✅ 官方文件
視覺效果：✅ 專業級
技術深度：✅ 內外結構完整
創新性：✅ 12色對準視覺化
完整性：✅ 左中右完整布局
```

---

## 🚀 立即開始

**今天（1 小時）**：
```
□ 下載 Blender
□ 儲存兩張 ASML 圖片
□ 開啟 Blender，載入參考圖
□ 熟悉基本操作
```

**明天起（3-4 天）**：
```
□ Day 1: 外殼（4h）
□ Day 2: 光學（3h）⭐ 粉紅發光
□ Day 3: 載台（2h）
□ Day 4: Reticle（2h）
□ Day 5: 感測器（3h）⭐ 12色
□ Day 6: 細節（2h）
□ Day 7: 材質（2h）
□ Day 8: 導出（1h）
```

---

**有了這兩張官方圖，你可以建立一個完整、準確、專業的 ASML DUV 曝光機 3D 模型！** 🎉

**需要我提供 Day 1 的詳細逐步操作教學嗎？** 🚀
