# Blender 真實 DUV 曝光機 3D 模型 - 完整實作指南

## 🎯 目標

創建一個**照片級真實的 DUV 曝光機 3D 模型**，包含：
- ✅ 真實的零件外觀（螺絲、管線、標籤）
- ✅ 精確的材質（金屬、玻璃、塑料）
- ✅ 異常零件紅燈告警效果
- ✅ 可在網頁中互動旋轉

---

## 🚀 快速方案：購買現成模型（推薦！）

### 為什麼推薦購買？

**時間對比**：
- 自己建模：3-5天 + 學習曲線
- 購買現成：1-2小時找模型 + 1天整合

**成本對比**：
- 自己建模：0元，但花5天時間
- 購買模型：50-200美元，省4天時間

### 推薦購買平台

#### 1. TurboSquid（最推薦）
網址：https://www.turbosquid.com/

**搜尋關鍵字**：
```
• "lithography machine"
• "semiconductor equipment"
• "wafer stepper"
• "ASML scanner"
• "photolithography"
```

**推薦模型範例**（參考）：
- Semiconductor Equipment 3D Model - $79-$199
- Industrial Lithography Machine - $149
- Clean Room Equipment Pack - $299（包含多台設備）

**選購重點**：
- ✅ 支援 `.glb` 或 `.gltf` 格式（Three.js原生支援）
- ✅ 或支援 `.fbx`, `.obj`（可用Blender轉換）
- ✅ 包含材質貼圖（Textures）
- ✅ 多邊形數量 < 100,000（網頁性能考量）
- ✅ 有零件分層（可以單獨控制每個部件）

#### 2. Sketchfab（免費+付費）
網址：https://sketchfab.com/

**優點**：
- 有免費模型（CC授權）
- 可直接下載 `.glb` 格式
- 線上預覽效果

**搜尋範例**：
```
sketchfab.com/search?q=semiconductor+equipment&type=models
```

#### 3. CGTrader
網址：https://www.cgtrader.com/

**優點**：
- 價格較便宜（$50-$150）
- 支援多種格式

### 如何判斷模型品質？

**檢查清單**：
```
✅ 預覽圖是否清晰真實？
✅ 是否有金屬光澤、玻璃透明效果？
✅ 是否有細節（螺絲、管線、標籤）？
✅ 零件是否分層命名（lens, stage, chamber 等）？
✅ 多邊形數量合理嗎？（建議 < 100k）
✅ 是否包含 PBR 材質？（Physically Based Rendering）
✅ 評價和下載次數如何？
```

---

## 🛠️ 方案 A：購買模型並整合（1-2天）

### 第一步：下載並準備模型

```bash
# 購買後下載的檔案通常包含：
model/
├── lithography_machine.fbx      # 主模型檔案
├── textures/                     # 材質貼圖資料夾
│   ├── metal_basecolor.png
│   ├── metal_normal.png
│   ├── metal_roughness.png
│   └── glass_opacity.png
└── readme.txt                    # 使用說明
```

### 第二步：用 Blender 檢查並優化

#### 安裝 Blender（免費）

下載：https://www.blender.org/download/

#### 導入模型到 Blender

1. 開啟 Blender
2. File → Import → FBX / OBJ（根據檔案格式）
3. 選擇下載的模型檔案

#### 檢查零件分層

```
在 Outliner 視窗中查看：
├─ LithographyMachine
   ├─ LensSystem          ← 需要這樣的分層
   ├─ WaferStage
   ├─ LightSource
   ├─ CoolingSystem
   ├─ VacuumChamber
   └─ AlignmentSystem
```

**如果沒有分層**：需要手動分離零件
- 進入 Edit Mode (Tab鍵)
- 選擇特定零件 (L鍵選擇連接的面)
- 按 P → Selection（分離選中部分）
- 重命名零件

#### 重要：為每個零件命名

```python
# 命名規則（與程式碼對應）
lens_system         # 鏡頭系統
light_source        # 光源
wafer_stage         # Wafer 載台
reticle_stage       # Reticle 載台
cooling_system      # 冷卻系統
vacuum_chamber      # 真空腔體
alignment_system    # 對準系統
```

#### 優化模型

```
優化步驟：
1. 減少多邊形數量（如果 > 100k）
   • 選擇物件
   • Modifiers → Decimate
   • Ratio: 0.5（減少一半）

2. 合併相近零件
   • 選擇多個小零件 (Shift+點擊)
   • Ctrl+J（合併）

3. 檢查材質
   • 切換到 Shading 工作區
   • 確認每個材質都有貼圖
```

### 第三步：導出為 .glb 格式

```
導出步驟：
1. File → Export → glTF 2.0 (.glb/.gltf)

2. 導出設定：
   ✅ Format: glTF Binary (.glb)          ← 選這個
   ✅ Include: Selected Objects (或 All)
   ✅ Transform: +Y Up
   ✅ Compression: 開啟（減少檔案大小）

3. 檔案命名：duv_machine.glb

4. 儲存位置：
   semiconductor_training_system/assets/models/duv_machine.glb
```

### 第四步：創建 Three.js 載入器

創建檔案：`interface/equipment_visualizer_3d_realistic.py`

```python
# -*- coding: utf-8 -*-
"""
3D真實設備視覺化器 (使用真實 Blender 模型)
"""

from typing import Dict, List
import json
from pathlib import Path

class RealisticEquipmentVisualizer:
    """真實 3D 模型視覺化器（使用 GLTFLoader）"""

    def __init__(self, model_path: str = "assets/models/duv_machine.glb"):
        """初始化視覺化器"""
        self.model_path = model_path

        # 零件名稱映射（Blender 模型中的名稱）
        self.component_names = {
            'lens_system': 'LensSystem',
            'light_source': 'LightSource',
            'wafer_stage': 'WaferStage',
            'reticle_stage': 'ReticleStage',
            'cooling_system': 'CoolingSystem',
            'vacuum_chamber': 'VacuumChamber',
            'alignment_system': 'AlignmentSystem',
        }

    def generate_3d_view(self, state: Dict, faults: List[str] = None) -> str:
        """生成真實 3D 設備視圖"""

        # 分析零件狀態
        component_status = self._analyze_component_status(state, faults)

        # 生成配置 JSON
        config_json = json.dumps({
            'model_path': self.model_path,
            'components': component_status,
            'component_names': self.component_names
        })

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0;
            overflow: hidden;
            font-family: 'Microsoft YaHei', 'Arial', sans-serif;
            background: #0a0e1a;
        }}
        #canvas-container {{
            width: 100%;
            height: 700px;
            position: relative;
        }}

        /* 載入畫面 */
        #loading-screen {{
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(10, 14, 26, 0.95);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            transition: opacity 0.5s;
        }}
        #loading-screen.hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        .loading-spinner {{
            width: 60px;
            height: 60px;
            border: 4px solid rgba(100, 181, 246, 0.3);
            border-top-color: #64B5F6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        /* 資訊面板 */
        #info-panel {{
            position: absolute;
            top: 15px;
            left: 15px;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(10px);
            color: white;
            padding: 20px;
            border-radius: 12px;
            font-size: 13px;
            max-width: 280px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(100, 181, 246, 0.3);
        }}
        .panel-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #64B5F6;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .status-item {{
            margin: 10px 0;
            padding: 8px 10px;
            border-left: 3px solid #4CAF50;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
            transition: all 0.3s;
        }}
        .status-item:hover {{
            background: rgba(255, 255, 255, 0.1);
            transform: translateX(5px);
        }}
        .status-item.warning {{
            border-color: #FF9800;
            background: rgba(255, 152, 0, 0.1);
        }}
        .status-item.critical {{
            border-color: #f44336;
            background: rgba(244, 67, 54, 0.1);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
        .status-label {{
            font-weight: bold;
            font-size: 13px;
        }}
        .status-value {{
            color: #aaa;
            font-size: 12px;
            margin-top: 3px;
        }}

        /* 控制說明 */
        #controls {{
            position: absolute;
            bottom: 15px;
            right: 15px;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(10px);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            font-size: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(100, 181, 246, 0.3);
        }}
        .control-title {{
            font-weight: bold;
            margin-bottom: 8px;
            color: #64B5F6;
        }}
        .control-item {{
            margin: 5px 0;
            opacity: 0.8;
        }}

        /* 零件詳情彈窗 */
        #component-detail {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(0.8);
            background: rgba(0, 0, 0, 0.95);
            backdrop-filter: blur(15px);
            color: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
            border: 2px solid rgba(100, 181, 246, 0.5);
            min-width: 300px;
            opacity: 0;
            pointer-events: none;
            transition: all 0.3s;
            z-index: 100;
        }}
        #component-detail.show {{
            opacity: 1;
            pointer-events: auto;
            transform: translate(-50%, -50%) scale(1);
        }}
        .detail-close {{
            position: absolute;
            top: 10px;
            right: 15px;
            font-size: 24px;
            cursor: pointer;
            color: #aaa;
            transition: color 0.3s;
        }}
        .detail-close:hover {{
            color: #fff;
        }}
    </style>
</head>
<body>
    <div id="canvas-container">
        <!-- 載入畫面 -->
        <div id="loading-screen">
            <div class="loading-spinner"></div>
            <div style="color: #64B5F6; margin-top: 20px; font-size: 16px;">
                載入 3D 模型中...
            </div>
            <div style="color: #aaa; margin-top: 10px; font-size: 12px;">
                Loading DUV Lithography Machine
            </div>
        </div>

        <!-- 資訊面板 -->
        <div id="info-panel">
            <div class="panel-title">
                🔬 DUV 曝光機監控
            </div>
            <div id="status-list"></div>
        </div>

        <!-- 控制說明 -->
        <div id="controls">
            <div class="control-title">🎮 互動控制</div>
            <div class="control-item">• 滑鼠左鍵拖曳：旋轉視角</div>
            <div class="control-item">• 滑鼠滾輪：縮放</div>
            <div class="control-item">• 滑鼠右鍵拖曳：平移</div>
            <div class="control-item">• 點擊零件：查看詳細資訊</div>
        </div>

        <!-- 零件詳情彈窗 -->
        <div id="component-detail">
            <span class="detail-close" onclick="hideDetail()">×</span>
            <div id="detail-content"></div>
        </div>
    </div>

    <!-- Three.js Libraries -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>

    <script>
        // 配置
        const config = {config_json};

        // 全局變數
        let scene, camera, renderer, controls;
        let loadedModel;
        let componentMeshes = {{}};
        let raycaster = new THREE.Raycaster();
        let mouse = new THREE.Vector2();

        // 初始化
        function init() {{
            console.log('Initializing 3D viewer...');

            // 創建場景
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0e1a);
            scene.fog = new THREE.Fog(0x0a0e1a, 40, 120);

            // 創建相機
            const container = document.getElementById('canvas-container');
            camera = new THREE.PerspectiveCamera(
                50,
                container.clientWidth / container.clientHeight,
                0.1,
                1000
            );
            camera.position.set(25, 20, 25);

            // 創建渲染器
            renderer = new THREE.WebGLRenderer({{
                antialias: true,
                alpha: true
            }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            renderer.outputEncoding = THREE.sRGBEncoding;
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.2;
            container.appendChild(renderer.domElement);

            // 軌道控制器
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.minDistance = 10;
            controls.maxDistance = 80;
            controls.maxPolarAngle = Math.PI / 2;

            // 添加光源
            addLights();

            // 載入 3D 模型
            loadModel();

            // 創建地板
            createFloor();

            // 更新狀態面板
            updateStatusPanel();

            // 滑鼠事件
            renderer.domElement.addEventListener('click', onMouseClick, false);

            // 開始動畫
            animate();
        }}

        function addLights() {{
            // 環境光
            const ambientLight = new THREE.AmbientLight(0x404040, 2);
            scene.add(ambientLight);

            // 主光源
            const mainLight = new THREE.DirectionalLight(0xffffff, 1.2);
            mainLight.position.set(20, 30, 20);
            mainLight.castShadow = true;
            mainLight.shadow.mapSize.width = 2048;
            mainLight.shadow.mapSize.height = 2048;
            mainLight.shadow.camera.near = 0.5;
            mainLight.shadow.camera.far = 100;
            scene.add(mainLight);

            // 補光
            const fillLight1 = new THREE.DirectionalLight(0x6699ff, 0.6);
            fillLight1.position.set(-15, 15, -15);
            scene.add(fillLight1);

            const fillLight2 = new THREE.DirectionalLight(0xff9966, 0.4);
            fillLight2.position.set(15, 5, -15);
            scene.add(fillLight2);

            // 頂部光
            const topLight = new THREE.PointLight(0xffffff, 0.8, 100);
            topLight.position.set(0, 25, 0);
            scene.add(topLight);
        }}

        function loadModel() {{
            const loader = new THREE.GLTFLoader();

            console.log('Loading model from:', config.model_path);

            loader.load(
                config.model_path,
                // onLoad
                function(gltf) {{
                    console.log('Model loaded successfully!');
                    loadedModel = gltf.scene;

                    // 設定模型
                    loadedModel.traverse((child) => {{
                        if (child.isMesh) {{
                            child.castShadow = true;
                            child.receiveShadow = true;

                            // 儲存零件參考
                            const componentKey = findComponentKey(child.name);
                            if (componentKey) {{
                                componentMeshes[componentKey] = child;
                                child.userData.componentKey = componentKey;
                                console.log('Found component:', componentKey, '->', child.name);
                            }}
                        }}
                    }});

                    // 調整模型大小和位置
                    const box = new THREE.Box3().setFromObject(loadedModel);
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());

                    const maxDim = Math.max(size.x, size.y, size.z);
                    const scale = 15 / maxDim; // 縮放到適當大小
                    loadedModel.scale.multiplyScalar(scale);

                    loadedModel.position.sub(center.multiplyScalar(scale));
                    loadedModel.position.y = 0;

                    scene.add(loadedModel);

                    // 添加告警效果
                    updateComponentAlarms();

                    // 隱藏載入畫面
                    document.getElementById('loading-screen').classList.add('hidden');
                }},
                // onProgress
                function(xhr) {{
                    const percent = (xhr.loaded / xhr.total * 100).toFixed(0);
                    console.log('Loading: ' + percent + '%');
                }},
                // onError
                function(error) {{
                    console.error('Error loading model:', error);
                    document.getElementById('loading-screen').innerHTML = `
                        <div style="color: #f44336; font-size: 18px;">載入失敗</div>
                        <div style="color: #aaa; margin-top: 10px; font-size: 13px;">
                            請確認模型檔案路徑正確：<br>
                            ${{config.model_path}}
                        </div>
                    `;
                }}
            );
        }}

        function findComponentKey(meshName) {{
            // 根據 mesh 名稱找到對應的 component key
            meshName = meshName.toLowerCase();
            for (const [key, name] of Object.entries(config.component_names)) {{
                if (meshName.includes(name.toLowerCase())) {{
                    return key;
                }}
            }}
            return null;
        }}

        function updateComponentAlarms() {{
            Object.entries(config.components).forEach(([key, info]) => {{
                const mesh = componentMeshes[key];
                if (!mesh) return;

                // 移除舊的告警光暈
                if (mesh.userData.alarmGlow) {{
                    mesh.parent.remove(mesh.userData.alarmGlow);
                }}

                // 如果是異常狀態，添加光暈
                if (info.status === 'critical' || info.status === 'warning') {{
                    const alarmColor = info.status === 'critical' ? 0xff0000 : 0xff9800;

                    // 計算 mesh 的包圍盒
                    const box = new THREE.Box3().setFromObject(mesh);
                    const size = box.getSize(new THREE.Vector3());
                    const maxSize = Math.max(size.x, size.y, size.z);

                    // 創建光暈
                    const glowGeometry = new THREE.SphereGeometry(maxSize * 0.8, 32, 32);
                    const glowMaterial = new THREE.MeshBasicMaterial({{
                        color: alarmColor,
                        transparent: true,
                        opacity: 0.3,
                        side: THREE.BackSide
                    }});
                    const glow = new THREE.Mesh(glowGeometry, glowMaterial);

                    const center = box.getCenter(new THREE.Vector3());
                    glow.position.copy(center);

                    mesh.parent.add(glow);
                    mesh.userData.alarmGlow = glow;
                    mesh.userData.alarmAnimation = true;
                }}
            }});
        }}

        function createFloor() {{
            const gridHelper = new THREE.GridHelper(50, 50, 0x2c3e50, 0x1a1a2e);
            gridHelper.position.y = -0.5;
            scene.add(gridHelper);
        }}

        function updateStatusPanel() {{
            const statusList = document.getElementById('status-list');
            let html = '';

            Object.entries(config.components).forEach(([key, info]) => {{
                const statusClass = info.status || 'normal';
                const emoji = statusClass === 'critical' ? '🔴' :
                             statusClass === 'warning' ? '🟡' : '🟢';

                html += `
                    <div class="status-item ${{statusClass}}">
                        <div class="status-label">${{emoji}} ${{info.label}}</div>
                        <div class="status-value">${{info.value}}</div>
                    </div>
                `;
            }});

            statusList.innerHTML = html;
        }}

        function onMouseClick(event) {{
            // 計算滑鼠位置
            const rect = renderer.domElement.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

            // 射線檢測
            raycaster.setFromCamera(mouse, camera);

            if (!loadedModel) return;

            const intersects = raycaster.intersectObject(loadedModel, true);

            if (intersects.length > 0) {{
                const clickedMesh = intersects[0].object;
                const componentKey = clickedMesh.userData.componentKey;

                if (componentKey) {{
                    showComponentDetail(componentKey);
                }}
            }}
        }}

        function showComponentDetail(componentKey) {{
            const info = config.components[componentKey];
            if (!info) return;

            const statusClass = info.status || 'normal';
            const emoji = statusClass === 'critical' ? '🔴' :
                         statusClass === 'warning' ? '🟡' : '🟢';
            const statusText = statusClass === 'critical' ? '異常' :
                              statusClass === 'warning' ? '警告' : '正常';

            const detailContent = `
                <div style="font-size: 20px; font-weight: bold; margin-bottom: 15px; color: #64B5F6;">
                    ${{info.label}}
                </div>
                <div style="margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <div style="color: #aaa; font-size: 12px;">狀態</div>
                    <div style="font-size: 16px; margin-top: 5px;">${{emoji}} ${{statusText}}</div>
                </div>
                <div style="margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <div style="color: #aaa; font-size: 12px;">數值</div>
                    <div style="font-size: 16px; margin-top: 5px;">${{info.value}}</div>
                </div>
            `;

            document.getElementById('detail-content').innerHTML = detailContent;
            document.getElementById('component-detail').classList.add('show');
        }}

        function hideDetail() {{
            document.getElementById('component-detail').classList.remove('show');
        }}

        function animate() {{
            requestAnimationFrame(animate);

            // 更新控制器
            controls.update();

            // 告警閃爍動畫
            Object.values(componentMeshes).forEach(mesh => {{
                if (mesh.userData.alarmAnimation && mesh.userData.alarmGlow) {{
                    mesh.userData.alarmGlow.material.opacity =
                        0.2 + Math.sin(Date.now() * 0.003) * 0.15;
                }}
            }});

            // 渲染
            renderer.render(scene, camera);
        }}

        // 響應式調整
        window.addEventListener('resize', () => {{
            const container = document.getElementById('canvas-container');
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }});

        // 點擊空白處關閉詳情
        document.addEventListener('click', (e) => {{
            if (e.target.id === 'canvas-container') {{
                hideDetail();
            }}
        }});

        // 啟動
        init();
    </script>
</body>
</html>
        """

        return html

    def _analyze_component_status(self, state: Dict, faults: List[str] = None) -> Dict:
        """分析各零件狀態"""
        components = {{}}

        # 冷卻系統
        cooling_flow = state.get('cooling_flow', 5.0)
        cooling_status = self._get_status(abs(cooling_flow - 5.0) / 5.0, 0.05, 0.15)
        components['cooling_system'] = {{
            'label': '冷卻系統',
            'value': f'{{cooling_flow:.2f}} L/min',
            'status': cooling_status
        }}

        # 鏡頭系統
        lens_temp = state.get('lens_temp', 23.0)
        temp_status = self._get_status(abs(lens_temp - 23.0), 0.2, 0.5)
        components['lens_system'] = {{
            'label': '投影鏡頭',
            'value': f'{{lens_temp:.1f}} °C',
            'status': temp_status
        }}

        # 真空腔體
        vacuum = state.get('vacuum_pressure', 1.0e-6)
        vacuum_status = self._get_status((vacuum - 1.0e-6) / 1.0e-6, 0.5, 1.0)
        components['vacuum_chamber'] = {{
            'label': '真空腔體',
            'value': f'{{vacuum:.2e}} Torr',
            'status': vacuum_status
        }}

        # 光源系統
        light = state.get('light_intensity', 100.0)
        light_status = self._get_status(abs(light - 100.0) / 100.0, 0.05, 0.10)
        components['light_source'] = {{
            'label': '光源系統',
            'value': f'{{light:.1f}} %',
            'status': light_status
        }}

        # Wafer 載台
        alignment_error = state.get('alignment_error', 0.0)
        align_status = self._get_status(alignment_error, 2.0, 5.0)
        components['wafer_stage'] = {{
            'label': 'Wafer 載台',
            'value': f'誤差 {{alignment_error:.1f}} nm',
            'status': align_status
        }}

        # Reticle 載台
        components['reticle_stage'] = {{
            'label': 'Reticle 載台',
            'value': '正常運作',
            'status': 'normal'
        }}

        # 對準系統
        components['alignment_system'] = {{
            'label': '對準系統',
            'value': f'{{alignment_error:.1f}} nm',
            'status': align_status
        }}

        return components

    def _get_status(self, deviation: float, warning_threshold: float, critical_threshold: float) -> str:
        """根據偏差量判斷狀態"""
        if deviation >= critical_threshold:
            return 'critical'
        elif deviation >= warning_threshold:
            return 'warning'
        else:
            return 'normal'
```

---

## 🎨 方案 B：自己用 Blender 建模（3-5天）

如果你想完全客製化，或找不到合適的模型，可以自己建模。

### Blender 建模完整流程

#### 第一天：基礎結構

**參考資料準備**：
1. Google 搜尋：`"ASML DUV" OR "lithography machine" site:asml.com`
2. 下載官方圖片作為參考
3. 收集至少 3-5 張不同角度的照片

**建模步驟**：
```
1. 創建真空腔體（主體）
   • Add → Mesh → Cylinder
   • Radius: 5, Depth: 8
   • 調整為半透明材質

2. 創建 Wafer 載台
   • Add → Mesh → Cylinder
   • Radius: 2.5, Depth: 0.5
   • 位置：Y = -2

3. 創建 Reticle 載台
   • Add → Mesh → Cube
   • Scale: (3, 0.3, 3)
   • 位置：Y = 5

4. 創建鏡頭系統
   • Add → Mesh → Cylinder
   • Radius: 1.5, Depth: 4
   • 位置：Y = 8
   • 添加玻璃透明材質

5. 創建光源系統
   • Add → Mesh → Cube
   • Scale: (3, 2, 3)
   • 位置：Y = 12
```

#### 第二天：添加細節

```
1. 冷卻系統管路
   • Add → Mesh → Cylinder
   • 使用 Array Modifier 複製
   • 使用 Curve Modifier 彎曲

2. 支撐結構
   • 添加支柱、支架
   • 使用 Mirror Modifier 對稱

3. 螺絲和固定件
   • Add → Mesh → Cylinder (小型)
   • 使用 Array 排列

4. 控制面板
   • Add → Mesh → Cube
   • 添加按鈕、螢幕貼圖
```

#### 第三天：材質和貼圖

```
1. 金屬材質
   • Shader Editor
   • Principled BSDF
   • Metallic: 0.9
   • Roughness: 0.3

2. 玻璃材質（鏡頭）
   • Transmission: 1.0
   • IOR: 1.5
   • Roughness: 0.05

3. 塑料材質
   • Metallic: 0
   • Roughness: 0.4

4. 添加 Logo 和標籤
   • 使用 Image Texture
   • ASML logo、警告標示等
```

#### 第四天：光源和渲染

```
1. 設定場景光源
   • HDRI 環境貼圖
   • 點光源、聚光燈

2. 測試渲染
   • Render → Render Image
   • 調整材質和光源

3. 優化反射和陰影
```

#### 第五天：優化和導出

```
1. 減少多邊形
   • Modifiers → Decimate

2. 合併小零件
   • 選擇 → Ctrl+J

3. 檢查零件命名
   • 確保符合程式碼規範

4. 導出 .glb
   • File → Export → glTF 2.0
```

---

## 📋 檢查清單

### 模型品質檢查
```
✅ 所有零件都正確命名了嗎？
✅ 多邊形數量 < 100,000？
✅ 材質都正確設定了嗎？
✅ .glb 檔案大小 < 20MB？
✅ 在 Blender 中預覽正常嗎？
```

### 程式整合檢查
```
✅ 模型檔案放在 assets/models/ 了嗎？
✅ 零件名稱與程式碼對應嗎？
✅ 在瀏覽器中能正常載入嗎？
✅ 異常告警效果正常嗎？
✅ 點擊互動功能正常嗎？
```

---

## 🚀 立即開始

**推薦流程**：
1. 先到 TurboSquid 或 Sketchfab 搜尋現成模型
2. 如果找到合適的，購買並整合（1-2天完成）
3. 如果找不到，再考慮自己建模（3-5天完成）

**需要我幫你**：
1. ✅ 建立完整的 Python 視覺化器程式碼
2. ✅ 整合到 Gradio 介面
3. ✅ 提供測試腳本
4. ✅ 提供 Blender 建模詳細教學影片連結

**準備好開始了嗎？**
