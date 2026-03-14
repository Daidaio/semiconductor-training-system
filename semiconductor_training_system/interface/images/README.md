# 設備照片使用說明

## 📸 放置真實設備照片

### 步驟 1：找到 ASML DUV 設備照片

推薦來源：
1. **ASML 官方網站**：https://www.asml.com/en/products/duv-lithography-systems
2. **Google 圖片搜尋**：搜尋 "ASML TWINSCAN NXT DUV lithography"
3. **公司內部資料**：如果你們公司有實際設備照片（需確認可否使用）

### 步驟 2：下載圖片

建議規格：
- **解析度**：至少 1920x1080 px
- **格式**：JPG 或 PNG
- **角度**：正面或側面視角最佳
- **清晰度**：可清楚看到各部件

### 步驟 3：放置圖片

將下載的照片重新命名並放到這個資料夾：

```
interface/images/asml_duv.jpg
```

或

```
interface/images/asml_duv.png
```

### 步驟 4：更新系統設定

編輯 `interface/simulation_interface.py`，找到視覺化器初始化的部分：

```python
# 修改前
self.equipment_visualizer = RealisticEquipmentVisualizer()

# 修改後
self.equipment_visualizer = PhotoEquipmentVisualizer(
    use_local_image=True,
    image_path="interface/images/asml_duv.jpg"
)
```

---

## 🎯 推薦的設備照片範例

### ASML TWINSCAN NXT:1980Di

**特點**：
- 193nm ArF 浸潤式微影系統
- 可清楚看到設備各部件
- 正面視角，適合標記

**可能的照片來源**：
1. ASML 官方產品目錄
2. 半導體廠商網站（如台積電、三星）
3. 學術論文中的設備照片
4. YouTube 技術影片截圖

---

## 🔧 使用網路圖片（無需下載）

如果找到網路上的圖片，也可以直接使用 URL：

```python
self.equipment_visualizer = PhotoEquipmentVisualizer(
    use_local_image=False,
    image_path="https://example.com/path/to/asml_image.jpg"
)
```

**但要注意**：
- ⚠️ 確保圖片 URL 穩定可訪問
- ⚠️ 注意版權問題
- ⚠️ 網路載入可能較慢

---

## 📋 版權注意事項

### ✅ 可以使用：
1. ASML 官方提供的產品照片（教育用途）
2. 公開發表的學術論文中的設備圖
3. 公司內部照片（需獲得授權）
4. Creative Commons 授權的照片

### ❌ 避免使用：
1. 未經授權的商業攝影
2. 他人享有版權的照片
3. 標示「禁止轉載」的圖片

### 💡 建議：
- 論文使用：註明「圖片來源：ASML 官網」
- 內部訓練：可使用公司設備實拍照片
- Demo 展示：使用官方公開資料最保險

---

## 🎨 如果沒有照片怎麼辦？

系統已經內建**超真實 SVG 視覺化**（不需要照片），包含：
- 照片級材質和光影
- 工業設備細節
- 動態故障標記

如果暫時沒有真實照片，可以繼續使用 SVG 版本：

```python
# 使用超真實 SVG 版本
self.equipment_visualizer = RealisticEquipmentVisualizer()
```

---

## 📞 需要協助？

如果你：
- 找到了照片但不知道如何放置
- 想調整標記位置
- 需要支援其他圖片格式

隨時告訴我，我會幫你調整！
