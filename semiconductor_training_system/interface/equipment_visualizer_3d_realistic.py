# -*- coding: utf-8 -*-
"""
3D真實設備視覺化器 (使用真實 Blender 模型)
使用 Three.js GLTFLoader 載入真實 3D 模型
"""

from typing import Dict, List
import json
from pathlib import Path

class RealisticEquipmentVisualizer:
    """真實 3D 模型視覺化器（使用 GLTFLoader）"""

    def __init__(self, model_path: str = "assets/models/duv_machine.glb"):
        """
        初始化視覺化器

        Args:
            model_path: 3D 模型檔案路徑（.glb 格式）
        """
        self.model_path = model_path

        # 零件名稱映射（Blender 模型中的名稱 → 系統中的 key）
        # 根據你的 Blender 模型實際命名調整
        self.component_names = {
            'lens_system': ['lens', 'LensSystem', 'Lens', 'ProjectionLens'],
            'light_source': ['light', 'LightSource', 'Light', 'Source'],
            'wafer_stage': ['wafer', 'WaferStage', 'Wafer', 'Stage'],
            'reticle_stage': ['reticle', 'ReticleStage', 'Reticle', 'Mask'],
            'cooling_system': ['cooling', 'CoolingSystem', 'Cooling', 'Chiller'],
            'vacuum_chamber': ['vacuum', 'VacuumChamber', 'Vacuum', 'Chamber'],
            'alignment_system': ['alignment', 'AlignmentSystem', 'Alignment', 'Align'],
        }

    def generate_3d_view(self, state: Dict, faults: List[str] = None) -> str:
        """
        生成真實 3D 設備視圖

        Args:
            state: 設備狀態字典
            faults: 故障零件列表

        Returns:
            完整的 HTML + Three.js 視覺化
        """

        # 分析零件狀態
        component_status = self._analyze_component_status(state, faults)

        # 轉換為 JSON 配置
        config_json = json.dumps({
            'model_path': self.model_path,
            'components': component_status,
            'component_names': self.component_names
        }, ensure_ascii=False)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>DUV 曝光機 3D 監控</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            overflow: hidden;
            background: #0a0e1a;
            color: #fff;
        }}

        #canvas-container {{
            width: 100%;
            height: 700px;
            position: relative;
            background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%);
        }}

        /* 載入畫面 */
        #loading-screen {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(10, 14, 26, 0.98);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 2000;
            transition: opacity 0.5s ease-out;
        }}
        #loading-screen.hidden {{
            opacity: 0;
            pointer-events: none;
        }}

        .loading-spinner {{
            width: 60px;
            height: 60px;
            border: 4px solid rgba(100, 181, 246, 0.2);
            border-top-color: #64B5F6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        .loading-text {{
            margin-top: 20px;
            font-size: 18px;
            color: #64B5F6;
            font-weight: 500;
        }}
        .loading-subtext {{
            margin-top: 10px;
            font-size: 13px;
            color: #7a8a9a;
        }}
        .loading-progress {{
            margin-top: 15px;
            width: 200px;
            height: 4px;
            background: rgba(100, 181, 246, 0.2);
            border-radius: 2px;
            overflow: hidden;
        }}
        .loading-progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #64B5F6, #42A5F5);
            width: 0%;
            transition: width 0.3s;
        }}

        /* 資訊面板 */
        #info-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(15, 23, 42, 0.92);
            backdrop-filter: blur(12px);
            padding: 20px;
            border-radius: 12px;
            max-width: 300px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(100, 181, 246, 0.2);
            z-index: 100;
        }}

        .panel-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #64B5F6;
            display: flex;
            align-items: center;
            gap: 10px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(100, 181, 246, 0.3);
        }}

        .status-item {{
            margin: 10px 0;
            padding: 10px 12px;
            border-left: 3px solid #4CAF50;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 6px;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .status-item:hover {{
            background: rgba(255, 255, 255, 0.08);
            transform: translateX(5px);
        }}
        .status-item.warning {{
            border-color: #FF9800;
            background: rgba(255, 152, 0, 0.08);
        }}
        .status-item.critical {{
            border-color: #f44336;
            background: rgba(244, 67, 54, 0.12);
            animation: pulse-warning 2s infinite;
        }}
        @keyframes pulse-warning {{
            0%, 100% {{ opacity: 1; box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.4); }}
            50% {{ opacity: 0.9; box-shadow: 0 0 0 8px rgba(244, 67, 54, 0); }}
        }}

        .status-label {{
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 4px;
        }}
        .status-value {{
            color: #94a3b8;
            font-size: 12px;
        }}

        /* 控制說明 */
        #controls {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(15, 23, 42, 0.92);
            backdrop-filter: blur(12px);
            padding: 15px 20px;
            border-radius: 10px;
            font-size: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(100, 181, 246, 0.2);
            z-index: 100;
        }}

        .control-title {{
            font-weight: 600;
            margin-bottom: 10px;
            color: #64B5F6;
            font-size: 13px;
        }}
        .control-item {{
            margin: 6px 0;
            opacity: 0.85;
            line-height: 1.5;
        }}

        /* 零件詳情彈窗 */
        #component-detail {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(0.9);
            background: rgba(15, 23, 42, 0.98);
            backdrop-filter: blur(20px);
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 25px 70px rgba(0, 0, 0, 0.9);
            border: 2px solid rgba(100, 181, 246, 0.3);
            min-width: 350px;
            max-width: 500px;
            opacity: 0;
            pointer-events: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 200;
        }}
        #component-detail.show {{
            opacity: 1;
            pointer-events: auto;
            transform: translate(-50%, -50%) scale(1);
        }}

        .detail-close {{
            position: absolute;
            top: 15px;
            right: 20px;
            font-size: 28px;
            cursor: pointer;
            color: #94a3b8;
            transition: all 0.3s;
            line-height: 1;
        }}
        .detail-close:hover {{
            color: #fff;
            transform: rotate(90deg);
        }}

        .detail-title {{
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #64B5F6;
            padding-bottom: 12px;
            border-bottom: 2px solid rgba(100, 181, 246, 0.3);
        }}

        .detail-section {{
            margin: 15px 0;
            padding: 15px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            border-left: 3px solid #64B5F6;
        }}
        .detail-section-title {{
            color: #94a3b8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        .detail-section-value {{
            font-size: 18px;
            font-weight: 500;
        }}

        /* 錯誤訊息 */
        .error-message {{
            color: #f44336;
            font-size: 16px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div id="canvas-container">
        <!-- 載入畫面 -->
        <div id="loading-screen">
            <div class="loading-spinner"></div>
            <div class="loading-text">載入 3D 模型中...</div>
            <div class="loading-subtext">Loading DUV Lithography Machine</div>
            <div class="loading-progress">
                <div class="loading-progress-bar" id="progress-bar"></div>
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
            <div class="control-item">• 滑鼠右鍵拖曳：平移視角</div>
            <div class="control-item">• 點擊零件：查看詳細資訊</div>
        </div>

        <!-- 零件詳情彈窗 -->
        <div id="component-detail">
            <span class="detail-close" onclick="hideDetail()">×</span>
            <div id="detail-content"></div>
        </div>
    </div>

    <!-- Three.js 核心庫 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>

    <script>
        // 配置數據
        const config = {config_json};

        // 全局變數
        let scene, camera, renderer, controls;
        let loadedModel;
        let componentMeshes = {{}};
        let raycaster = new THREE.Raycaster();
        let mouse = new THREE.Vector2();
        let isModelLoaded = false;

        // 初始化
        function init() {{
            console.log('🚀 初始化 3D 視覺化系統...');

            // 創建場景
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0e1a);
            scene.fog = new THREE.Fog(0x0a0e1a, 50, 150);

            // 創建相機
            const container = document.getElementById('canvas-container');
            camera = new THREE.PerspectiveCamera(
                45,
                container.clientWidth / container.clientHeight,
                0.1,
                1000
            );
            camera.position.set(30, 25, 30);
            camera.lookAt(0, 0, 0);

            // 創建渲染器
            renderer = new THREE.WebGLRenderer({{
                antialias: true,
                alpha: false
            }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
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
            controls.minDistance = 15;
            controls.maxDistance = 100;
            controls.maxPolarAngle = Math.PI / 2 + 0.2;
            controls.target.set(0, 5, 0);

            // 添加光源
            addLights();

            // 載入 3D 模型
            loadGLTFModel();

            // 創建地板
            createFloor();

            // 更新狀態面板
            updateStatusPanel();

            // 事件監聽
            renderer.domElement.addEventListener('click', onMouseClick, false);
            window.addEventListener('resize', onWindowResize, false);

            // 開始動畫循環
            animate();
        }}

        function addLights() {{
            // 環境光（整體照明）
            const ambientLight = new THREE.AmbientLight(0x404565, 1.8);
            scene.add(ambientLight);

            // 主光源（模擬太陽光）
            const mainLight = new THREE.DirectionalLight(0xffffff, 1.5);
            mainLight.position.set(25, 35, 25);
            mainLight.castShadow = true;
            mainLight.shadow.camera.left = -30;
            mainLight.shadow.camera.right = 30;
            mainLight.shadow.camera.top = 30;
            mainLight.shadow.camera.bottom = -30;
            mainLight.shadow.camera.near = 0.5;
            mainLight.shadow.camera.far = 100;
            mainLight.shadow.mapSize.width = 2048;
            mainLight.shadow.mapSize.height = 2048;
            mainLight.shadow.bias = -0.0001;
            scene.add(mainLight);

            // 補光1（側面藍光）
            const fillLight1 = new THREE.DirectionalLight(0x4466ff, 0.6);
            fillLight1.position.set(-20, 15, -20);
            scene.add(fillLight1);

            // 補光2（側面暖光）
            const fillLight2 = new THREE.DirectionalLight(0xff9955, 0.5);
            fillLight2.position.set(20, 10, -20);
            scene.add(fillLight2);

            // 頂部點光源（強調照明）
            const topLight = new THREE.PointLight(0xffffff, 1.0, 100);
            topLight.position.set(0, 30, 0);
            scene.add(topLight);

            // 底部環境光（減少陰影過深）
            const bottomLight = new THREE.HemisphereLight(0x64B5F6, 0x1a1f2e, 0.5);
            scene.add(bottomLight);
        }}

        function loadGLTFModel() {{
            const loader = new THREE.GLTFLoader();
            const progressBar = document.getElementById('progress-bar');

            console.log('📦 載入模型:', config.model_path);

            loader.load(
                config.model_path,

                // onLoad - 成功載入
                function(gltf) {{
                    console.log('✅ 模型載入成功!');
                    loadedModel = gltf.scene;
                    isModelLoaded = true;

                    // 遍歷所有 mesh
                    let meshCount = 0;
                    loadedModel.traverse((child) => {{
                        if (child.isMesh) {{
                            meshCount++;

                            // 啟用陰影
                            child.castShadow = true;
                            child.receiveShadow = true;

                            // 尋找零件對應關係
                            const componentKey = findComponentKey(child.name);
                            if (componentKey) {{
                                if (!componentMeshes[componentKey]) {{
                                    componentMeshes[componentKey] = [];
                                }}
                                componentMeshes[componentKey].push(child);
                                child.userData.componentKey = componentKey;
                                console.log('🔗 綁定零件:', componentKey, '←', child.name);
                            }}

                            // 優化材質
                            if (child.material) {{
                                child.material.needsUpdate = true;
                            }}
                        }}
                    }});

                    console.log('📊 總共找到', meshCount, '個 mesh');
                    console.log('🎯 識別到', Object.keys(componentMeshes).length, '個系統零件');

                    // 調整模型大小和位置
                    const box = new THREE.Box3().setFromObject(loadedModel);
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());

                    console.log('📏 模型尺寸:', size);

                    // 計算縮放比例（使模型高度約為 20 單位）
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const targetSize = 20;
                    const scale = targetSize / maxDim;

                    loadedModel.scale.multiplyScalar(scale);
                    console.log('🔍 縮放比例:', scale);

                    // 中心化
                    const scaledCenter = center.multiplyScalar(scale);
                    loadedModel.position.sub(scaledCenter);
                    loadedModel.position.y = 0; // 放在地面上

                    scene.add(loadedModel);

                    // 添加告警效果
                    updateComponentAlarms();

                    // 隱藏載入畫面
                    setTimeout(() => {{
                        document.getElementById('loading-screen').classList.add('hidden');
                    }}, 500);
                }},

                // onProgress - 載入進度
                function(xhr) {{
                    if (xhr.lengthComputable) {{
                        const percentComplete = (xhr.loaded / xhr.total) * 100;
                        progressBar.style.width = percentComplete + '%';
                        console.log('⏳ 載入進度:', Math.round(percentComplete) + '%');
                    }}
                }},

                // onError - 載入失敗
                function(error) {{
                    console.error('❌ 模型載入失敗:', error);
                    document.getElementById('loading-screen').innerHTML = `
                        <div class="error-message">
                            <div style="font-size: 48px; margin-bottom: 20px;">⚠️</div>
                            <div style="font-size: 20px; margin-bottom: 10px;">模型載入失敗</div>
                            <div style="font-size: 14px; color: #94a3b8; margin-top: 15px;">
                                請確認模型檔案路徑正確：<br>
                                <code style="background: rgba(255,255,255,0.1); padding: 5px 10px; border-radius: 4px; margin-top: 10px; display: inline-block;">
                                    ${{config.model_path}}
                                </code>
                            </div>
                            <div style="font-size: 13px; color: #7a8a9a; margin-top: 20px;">
                                請將 .glb 模型檔案放置在 assets/models/ 資料夾中
                            </div>
                        </div>
                    `;
                }}
            );
        }}

        function findComponentKey(meshName) {{
            // 根據 mesh 名稱找到對應的 component key
            const meshNameLower = meshName.toLowerCase();

            for (const [key, possibleNames] of Object.entries(config.component_names)) {{
                for (const name of possibleNames) {{
                    if (meshNameLower.includes(name.toLowerCase())) {{
                        return key;
                    }}
                }}
            }}

            return null;
        }}

        function updateComponentAlarms() {{
            console.log('🚨 更新告警效果...');

            Object.entries(config.components).forEach(([key, info]) => {{
                const meshes = componentMeshes[key];
                if (!meshes || meshes.length === 0) {{
                    console.warn('⚠️ 找不到零件:', key);
                    return;
                }}

                meshes.forEach(mesh => {{
                    // 移除舊的告警光暈
                    if (mesh.userData.alarmGlow) {{
                        scene.remove(mesh.userData.alarmGlow);
                        mesh.userData.alarmGlow = null;
                    }}

                    // 如果是異常狀態，添加光暈
                    if (info.status === 'critical' || info.status === 'warning') {{
                        const alarmColor = info.status === 'critical' ? 0xff0000 : 0xff9800;
                        const intensity = info.status === 'critical' ? 0.4 : 0.3;

                        // 計算包圍盒
                        const box = new THREE.Box3().setFromObject(mesh);
                        const size = box.getSize(new THREE.Vector3());
                        const center = box.getCenter(new THREE.Vector3());
                        const maxSize = Math.max(size.x, size.y, size.z);

                        // 創建光暈
                        const glowGeometry = new THREE.SphereGeometry(maxSize * 1.2, 32, 32);
                        const glowMaterial = new THREE.MeshBasicMaterial({{
                            color: alarmColor,
                            transparent: true,
                            opacity: intensity,
                            side: THREE.BackSide,
                            depthWrite: false
                        }});
                        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
                        glow.position.copy(center);

                        scene.add(glow);
                        mesh.userData.alarmGlow = glow;
                        mesh.userData.alarmAnimation = true;

                        console.log('🔴 添加告警:', key, info.status);
                    }}
                }});
            }});
        }}

        function createFloor() {{
            // 格線地板
            const gridHelper = new THREE.GridHelper(60, 60, 0x2c3e50, 0x1a1f2e);
            gridHelper.position.y = -0.1;
            scene.add(gridHelper);

            // 圓形平台
            const platformGeometry = new THREE.CylinderGeometry(12, 12, 0.5, 64);
            const platformMaterial = new THREE.MeshStandardMaterial({{
                color: 0x1e293b,
                metalness: 0.6,
                roughness: 0.4
            }});
            const platform = new THREE.Mesh(platformGeometry, platformMaterial);
            platform.position.y = -0.3;
            platform.receiveShadow = true;
            scene.add(platform);
        }}

        function updateStatusPanel() {{
            const statusList = document.getElementById('status-list');
            let html = '';

            Object.entries(config.components).forEach(([key, info]) => {{
                const statusClass = info.status || 'normal';
                const emoji = statusClass === 'critical' ? '🔴' :
                             statusClass === 'warning' ? '🟡' : '🟢';

                html += `
                    <div class="status-item ${{statusClass}}" onclick="focusOnComponent('${{key}}')">
                        <div class="status-label">${{emoji}} ${{info.label}}</div>
                        <div class="status-value">${{info.value}}</div>
                    </div>
                `;
            }});

            statusList.innerHTML = html;
        }}

        function focusOnComponent(componentKey) {{
            const meshes = componentMeshes[componentKey];
            if (!meshes || meshes.length === 0) return;

            // 計算零件的中心位置
            const box = new THREE.Box3();
            meshes.forEach(mesh => {{
                box.expandByObject(mesh);
            }});

            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);

            // 相機移動到適當位置
            const distance = maxDim * 3;
            const targetPos = new THREE.Vector3(
                center.x + distance * 0.7,
                center.y + distance * 0.5,
                center.z + distance * 0.7
            );

            // 平滑動畫
            animateCameraTo(targetPos, center);
        }}

        function animateCameraTo(targetPos, lookAtPos) {{
            const duration = 1000; // 1秒
            const startPos = camera.position.clone();
            const startLookAt = controls.target.clone();
            const startTime = Date.now();

            function update() {{
                const elapsed = Date.now() - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const eased = easeInOutCubic(progress);

                camera.position.lerpVectors(startPos, targetPos, eased);
                controls.target.lerpVectors(startLookAt, lookAtPos, eased);
                controls.update();

                if (progress < 1) {{
                    requestAnimationFrame(update);
                }}
            }}

            update();
        }}

        function easeInOutCubic(t) {{
            return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
        }}

        function onMouseClick(event) {{
            if (!isModelLoaded) return;

            // 計算滑鼠位置
            const rect = renderer.domElement.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

            // 射線檢測
            raycaster.setFromCamera(mouse, camera);
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
            const statusColor = statusClass === 'critical' ? '#f44336' :
                               statusClass === 'warning' ? '#FF9800' : '#4CAF50';

            const detailContent = `
                <div class="detail-title">${{info.label}}</div>

                <div class="detail-section" style="border-color: ${{statusColor}}">
                    <div class="detail-section-title">運行狀態</div>
                    <div class="detail-section-value">${{emoji}} ${{statusText}}</div>
                </div>

                <div class="detail-section">
                    <div class="detail-section-title">當前數值</div>
                    <div class="detail-section-value">${{info.value}}</div>
                </div>

                <div class="detail-section">
                    <div class="detail-section-title">零件代碼</div>
                    <div class="detail-section-value" style="font-size: 14px; font-family: monospace;">
                        ${{componentKey.toUpperCase()}}
                    </div>
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
            if (isModelLoaded) {{
                Object.values(componentMeshes).forEach(meshes => {{
                    if (!meshes) return;
                    meshes.forEach(mesh => {{
                        if (mesh.userData.alarmAnimation && mesh.userData.alarmGlow) {{
                            const time = Date.now() * 0.002;
                            mesh.userData.alarmGlow.material.opacity =
                                0.25 + Math.sin(time) * 0.15;
                        }}
                    }});
                }});
            }}

            // 渲染
            renderer.render(scene, camera);
        }}

        function onWindowResize() {{
            const container = document.getElementById('canvas-container');
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }}

        // 點擊空白處關閉詳情
        document.addEventListener('click', (e) => {{
            if (e.target === document.getElementById('canvas-container')) {{
                hideDetail();
            }}
        }});

        // ESC 鍵關閉詳情
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                hideDetail();
            }}
        }});

        // 啟動系統
        console.log('🎬 啟動 3D 視覺化系統');
        init();
    </script>
</body>
</html>
        """

        return html

    def _analyze_component_status(self, state: Dict, faults: List[str] = None) -> Dict:
        """分析各零件狀態"""
        components = {}

        # 冷卻系統
        cooling_flow = state.get('cooling_flow', 5.0)
        cooling_status = self._get_status(abs(cooling_flow - 5.0) / 5.0, 0.05, 0.15)
        components['cooling_system'] = {
            'label': '冷卻系統',
            'value': f'{cooling_flow:.2f} L/min',
            'status': cooling_status
        }

        # 鏡頭系統
        lens_temp = state.get('lens_temp', 23.0)
        temp_status = self._get_status(abs(lens_temp - 23.0), 0.2, 0.5)
        components['lens_system'] = {
            'label': '投影鏡頭',
            'value': f'{lens_temp:.1f} °C',
            'status': temp_status
        }

        # 真空腔體
        vacuum = state.get('vacuum_pressure', 1.0e-6)
        vacuum_status = self._get_status((vacuum - 1.0e-6) / 1.0e-6, 0.5, 1.0)
        components['vacuum_chamber'] = {
            'label': '真空腔體',
            'value': f'{vacuum:.2e} Torr',
            'status': vacuum_status
        }

        # 光源系統
        light = state.get('light_intensity', 100.0)
        light_status = self._get_status(abs(light - 100.0) / 100.0, 0.05, 0.10)
        components['light_source'] = {
            'label': '光源系統',
            'value': f'{light:.1f} %',
            'status': light_status
        }

        # Wafer 載台
        alignment_error = state.get('alignment_error', 0.0)
        align_status = self._get_status(alignment_error, 2.0, 5.0)
        components['wafer_stage'] = {
            'label': 'Wafer 載台',
            'value': f'誤差 {alignment_error:.1f} nm',
            'status': align_status
        }

        # Reticle 載台
        components['reticle_stage'] = {
            'label': 'Reticle 載台',
            'value': '正常運作',
            'status': 'normal'
        }

        # 對準系統
        components['alignment_system'] = {
            'label': '對準系統',
            'value': f'{alignment_error:.1f} nm',
            'status': align_status
        }

        return components

    def _get_status(self, deviation: float, warning_threshold: float, critical_threshold: float) -> str:
        """根據偏差量判斷狀態"""
        if deviation >= critical_threshold:
            return 'critical'
        elif deviation >= warning_threshold:
            return 'warning'
        else:
            return 'normal'
