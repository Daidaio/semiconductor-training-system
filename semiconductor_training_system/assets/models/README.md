# 3D 模型資料夾

## 📁 用途

此資料夾用於存放 DUV 曝光機的 3D 模型檔案。

---

## 📥 如何放置模型

### 步驟 1：取得 3D 模型

#### 方式 A：購買現成模型（推薦，最快）

**TurboSquid**（最專業）
```
https://www.turbosquid.com/Search/3D-Models?keywords=lithography+machine
```
- 價格：$79-$299
- 品質：高
- 格式：支援 .glb / .fbx / .obj

**Sketchfab**（有免費選項）
```
https://sketchfab.com/search?q=semiconductor&type=models
```
- 價格：免費-$150
- 品質：中到高
- 格式：直接下載 .glb

**CGTrader**（價格實惠）
```
https://www.cgtrader.com/3d-models?keywords=semiconductor
```
- 價格：$30-$150
- 品質：中
- 格式：多種格式

#### 方式 B：自己用 Blender 建模

參考文件：`Blender真實模型完整指南.md`

預計時間：3-5天

#### 方式 C：使用免費模型

**Free3D**
```
https://free3d.com/3d-models/industrial
```

**Blend Swap**（Blender 社群）
```
https://blendswap.com/blends/search?term=industrial
```

---

### 步驟 2：放置模型檔案

將下載的模型檔案重命名為：

```
duv_machine.glb
```

並放置在此資料夾中：

```
semiconductor_training_system/
└── assets/
    └── models/
        └── duv_machine.glb  ← 放這裡
```

---

## ✅ 模型要求

### 必須條件

- ✅ **格式**：`.glb` 或 `.gltf`（推薦 .glb）
- ✅ **檔案名稱**：`duv_machine.glb`
- ✅ **大小**：< 20 MB（建議 5-15 MB）
- ✅ **多邊形數**：< 100,000（網頁性能考量）

### 建議條件

- ✅ **零件分層**：主要零件分別命名
  - Lens / LensSystem
  - Wafer / WaferStage
  - Light / LightSource
  - Cooling / CoolingSystem
  - Vacuum / VacuumChamber
  - Alignment / AlignmentSystem

- ✅ **材質貼圖**：包含 PBR 材質
  - Base Color
  - Normal Map
  - Roughness
  - Metallic

- ✅ **UV 展開**：正確的 UV 映射

---

## 🔧 模型轉換（如果格式不對）

### 如果你下載的是 .fbx, .obj, .dae 等格式

#### 使用 Blender 轉換（免費）

1. **下載並安裝 Blender**
   ```
   https://www.blender.org/download/
   ```

2. **導入模型**
   - 開啟 Blender
   - File → Import → FBX / OBJ / Collada
   - 選擇你的模型檔案

3. **導出為 .glb**
   - File → Export → glTF 2.0 (.glb/.gltf)
   - 設定：
     - Format: **glTF Binary (.glb)** ✅
     - Include: Selected Objects 或 All
     - Compression: **開啟** ✅
   - 檔名：`duv_machine.glb`
   - 儲存位置：此資料夾

4. **完成！**

---

## 🧪 測試模型

### 快速測試

執行測試腳本：

```bash
python test_3d_model.py
```

開啟瀏覽器：`http://127.0.0.1:7860`

### 測試檢查項目

```
□ 模型能正常載入（2-10秒）
□ 可以用滑鼠旋轉
□ 可以用滾輪縮放
□ 零件細節清晰可見
□ 材質和顏色正確
□ 無黑色或缺失的零件
□ 異常零件顯示紅色光暈
□ 點擊零件顯示詳情
```

---

## ❓ 疑難排解

### 問題 1：模型載入失敗

```
❌ 錯誤訊息：「模型載入失敗」
```

**原因**：
- 檔案路徑錯誤
- 檔案格式不支援
- 檔案損壞

**解決**：
1. 確認檔案確實在 `assets/models/duv_machine.glb`
2. 確認檔案大小 > 1 MB
3. 用 Blender 重新導出

### 問題 2：模型太大，載入很慢

```
⏳ 載入超過 30 秒
```

**原因**：
- 檔案太大（> 50 MB）
- 多邊形數太多（> 500k）

**解決**：
1. 開啟 Blender
2. 選擇所有物件 (A 鍵)
3. Modifiers → Decimate → Ratio: 0.5
4. Apply
5. 重新導出

### 問題 3：模型是黑色的

```
🖤 模型顯示全黑
```

**原因**：
- 缺少材質
- 缺少光源資訊

**解決**：
1. 開啟 Blender
2. 切換到 Shading 工作區
3. 選擇物件
4. 添加 Principled BSDF 材質
5. 設定 Base Color
6. 重新導出

### 問題 4：找不到零件（無法添加告警）

```
⚠️ 主控台顯示：「找不到零件: lens_system」
```

**原因**：
- 模型中的零件名稱與程式碼不匹配

**解決**：

1. 用 Blender 查看零件名稱
   - 開啟模型
   - 查看 Outliner（右上角）
   - 記錄每個零件的名稱

2. 修改 `equipment_visualizer_3d_realistic.py`
   ```python
   self.component_names = {
       'lens_system': ['你實際的鏡頭名稱', 'Lens', ...],
       'wafer_stage': ['你實際的載台名稱', 'Stage', ...],
       # ...
   }
   ```

---

## 📚 相關文件

- **完整實作指南**：`Blender真實模型完整指南.md`
- **購買資源與測試**：`3D模型資源與測試.md`
- **方案詳細比較**：`3D方案詳細比較.md`
- **整體方案概覽**：`3D視覺化方案.md`

---

## 🎯 快速開始流程

```
1. 到 TurboSquid 搜尋「lithography machine」
2. 購買並下載模型（選擇 .glb 或 .fbx 格式）
3. 將檔案重命名為 duv_machine.glb
4. 放置在此資料夾
5. 執行 python test_3d_model.py
6. 開啟瀏覽器查看效果
```

**預計完成時間**：1-2 小時（不含模型建立時間）

---

## 💡 臨時方案

如果暫時沒有模型，可以先用方案1（Three.js 簡化幾何模型）：

參考文件：`3D視覺化方案.md` 中的方案1

這個方案可以在 1-2 天內完成，視覺效果也足夠應付論文需求。

---

**需要幫助？**
- 查看：`3D模型資源與測試.md` 的完整疑難排解章節
- 或詢問你的指導教授/同學
