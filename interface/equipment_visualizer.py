# -*- coding: utf-8 -*-
"""
設備視覺化模組 - 生成高質感的設備狀態圖
"""

from typing import Dict


class EquipmentVisualizer:
    """設備視覺化生成器"""

    def __init__(self):
        """初始化視覺化器"""
        pass

    def generate_equipment_svg(self, state: Dict) -> str:
        """
        生成 SVG 格式的設備圖，包含動態標註

        Args:
            state: 當前設備狀態

        Returns:
            SVG HTML 字串
        """
        # 取得各部件狀態
        cooling_status = self._get_cooling_status(state)
        vacuum_status = self._get_vacuum_status(state)
        temp_status = self._get_temp_status(state)
        filter_status = self._get_filter_status(state)
        light_status = self._get_light_status(state)

        # 生成故障標記
        fault_markers = self._generate_fault_markers(state)

        svg_html = f"""
        <div style="position: relative; width: 100%; height: 100%;
                    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
                    border-radius: 12px; padding: 20px; box-sizing: border-box;">

            <!-- CSS 動畫定義 -->
            <style>
                @keyframes pulse-red {{
                    0%, 100% {{ opacity: 1; transform: scale(1); }}
                    50% {{ opacity: 0.6; transform: scale(1.15); }}
                }}
                @keyframes pulse-orange {{
                    0%, 100% {{ opacity: 1; transform: scale(1); }}
                    50% {{ opacity: 0.7; transform: scale(1.1); }}
                }}
                @keyframes flow-animate {{
                    0% {{ stroke-dashoffset: 0; }}
                    100% {{ stroke-dashoffset: 40; }}
                }}
                @keyframes flow-slow {{
                    0% {{ stroke-dashoffset: 0; }}
                    100% {{ stroke-dashoffset: -30; }}
                }}
                @keyframes glow-green {{
                    0%, 100% {{ filter: drop-shadow(0 0 5px #44ff44); }}
                    50% {{ filter: drop-shadow(0 0 15px #44ff44); }}
                }}
                @keyframes glow-red {{
                    0%, 100% {{ filter: drop-shadow(0 0 8px #ff4444); }}
                    50% {{ filter: drop-shadow(0 0 20px #ff4444); }}
                }}
                .marker-pulse-red {{
                    animation: pulse-red 1.5s infinite;
                }}
                .marker-pulse-orange {{
                    animation: pulse-orange 2s infinite;
                }}
            </style>

            <svg width="100%" height="100%" viewBox="0 0 900 500" xmlns="http://www.w3.org/2000/svg">

                <!-- 定義漸層 -->
                <defs>
                    <linearGradient id="metalGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#e8e8e8;stop-opacity:1" />
                        <stop offset="50%" style="stop-color:#c0c0c0;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#a0a0a0;stop-opacity:1" />
                    </linearGradient>

                    <linearGradient id="glassGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#b3d9ff;stop-opacity:0.8" />
                        <stop offset="100%" style="stop-color:#0066cc;stop-opacity:0.4" />
                    </linearGradient>

                    <filter id="shadow">
                        <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.5"/>
                    </filter>
                </defs>

                <!-- 背景標題 -->
                <text x="450" y="30" text-anchor="middle"
                      font-size="24" font-weight="bold" fill="#ffffff"
                      style="text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
                    光刻曝光機 (Lithography Scanner)
                </text>

                <!-- 主設備外殼 -->
                <rect x="150" y="80" width="600" height="350" rx="20" ry="20"
                      fill="url(#metalGradient)"
                      stroke="#666" stroke-width="3"
                      filter="url(#shadow)"/>

                <!-- 設備內部區域 -->
                <rect x="170" y="100" width="560" height="310" rx="15" ry="15"
                      fill="#2c3e50" stroke="#444" stroke-width="2"/>

                <!-- ==================== 真空腔室（中央） ==================== -->
                <g id="vacuum-chamber">
                    <!-- 真空腔體 -->
                    <circle cx="450" cy="250" r="100"
                            fill="url(#glassGradient)"
                            stroke="{vacuum_status['color']}"
                            stroke-width="5"
                            style="{vacuum_status['animation']}"
                            filter="url(#shadow)"/>

                    <!-- 真空腔內部 -->
                    <circle cx="450" cy="250" r="80"
                            fill="none"
                            stroke="{vacuum_status['color']}"
                            stroke-width="2"
                            stroke-dasharray="5,5"
                            opacity="0.6"/>

                    <!-- 真空標籤 -->
                    <text x="450" y="255" text-anchor="middle"
                          font-size="16" font-weight="bold" fill="#ffffff">
                        真空腔
                    </text>
                    <text x="450" y="275" text-anchor="middle"
                          font-size="12" fill="{vacuum_status['color']}">
                        {state.get('vacuum_pressure', 1e-6):.2e} Torr
                    </text>
                </g>

                <!-- ==================== 冷卻水系統（頂部） ==================== -->
                <g id="cooling-system">
                    <!-- 冷卻水入口管 -->
                    <path d="M 200,120 L 350,120"
                          stroke="{cooling_status['color']}"
                          stroke-width="12"
                          stroke-linecap="round"
                          stroke-dasharray="20,20"
                          style="{cooling_status['animation']}"
                          fill="none"/>

                    <!-- 冷卻水出口管 -->
                    <path d="M 550,120 L 700,120"
                          stroke="{cooling_status['color']}"
                          stroke-width="12"
                          stroke-linecap="round"
                          stroke-dasharray="20,20"
                          style="{cooling_status['animation']}"
                          fill="none"/>

                    <!-- 熱交換器 -->
                    <rect x="350" y="105" width="200" height="30" rx="5"
                          fill="#34495e" stroke="{cooling_status['color']}"
                          stroke-width="2"/>

                    <!-- 冷卻水標籤 -->
                    <text x="450" y="95" text-anchor="middle"
                          font-size="14" font-weight="bold"
                          fill="{cooling_status['color']}">
                        冷卻水系統
                    </text>
                    <text x="450" y="125" text-anchor="middle"
                          font-size="11" fill="#ffffff">
                        {state.get('cooling_flow', 5.0):.1f} L/min
                    </text>
                </g>

                <!-- ==================== 過濾網（左下） ==================== -->
                <g id="filter-system">
                    <rect x="200" y="370" width="100" height="50" rx="5"
                          fill="{filter_status['color']}"
                          stroke="#333" stroke-width="2"
                          style="{filter_status['animation']}"/>

                    <!-- 過濾網紋理 -->
                    <line x1="210" y1="380" x2="290" y2="410" stroke="#666" stroke-width="1"/>
                    <line x1="210" y1="390" x2="290" y2="420" stroke="#666" stroke-width="1"/>
                    <line x1="210" y1="400" x2="290" y2="410" stroke="#666" stroke-width="1"/>

                    <text x="250" y="400" text-anchor="middle"
                          font-size="12" font-weight="bold" fill="#ffffff">
                        過濾網
                    </text>
                </g>

                <!-- ==================== 溫度感測器（右側） ==================== -->
                <g id="temperature-sensor">
                    <!-- 感測器外殼 -->
                    <circle cx="680" cy="250" r="25"
                            fill="{temp_status['color']}"
                            stroke="#333" stroke-width="2"
                            style="{temp_status['animation']}"/>

                    <!-- 溫度計圖示 -->
                    <rect x="677" y="235" width="6" height="20" rx="3"
                          fill="#ffffff"/>
                    <circle cx="680" cy="258" r="5" fill="#ffffff"/>

                    <!-- 溫度數值 -->
                    <text x="680" y="290" text-anchor="middle"
                          font-size="14" font-weight="bold"
                          fill="{temp_status['color']}">
                        {state.get('lens_temp', 23.0):.1f}°C
                    </text>
                </g>

                <!-- ==================== 光源系統（頂部 - 曝光光源） ==================== -->
                <g id="light-system">
                    <!-- 光源模組外殼 -->
                    <rect x="380" y="50" width="140" height="35" rx="8"
                          fill="#2c2c2c" stroke="{light_status['color']}"
                          stroke-width="3"
                          style="{light_status['animation']}"/>

                    <!-- 光源發光效果 -->
                    <rect x="390" y="58" width="120" height="20" rx="4"
                          fill="{light_status['color']}"
                          opacity="0.7"
                          style="{light_status['animation']}"/>

                    <!-- 光束向下投射 -->
                    <path d="M 420,85 L 410,120" stroke="{light_status['color']}"
                          stroke-width="4" opacity="0.4"/>
                    <path d="M 450,85 L 450,120" stroke="{light_status['color']}"
                          stroke-width="5" opacity="0.5"/>
                    <path d="M 480,85 L 490,120" stroke="{light_status['color']}"
                          stroke-width="4" opacity="0.4"/>

                    <text x="450" y="73" text-anchor="middle"
                          font-size="11" font-weight="bold" fill="#ffffff">
                        曝光光源 {state.get('light_intensity', 100):.0f}%
                    </text>
                </g>

                <!-- ==================== 投影鏡頭（上方） ==================== -->
                <g id="projection-lens">
                    <!-- 鏡頭組 -->
                    <ellipse cx="450" cy="140" rx="60" ry="25"
                             fill="#4a5568" stroke="#2d3748"
                             stroke-width="2"/>
                    <ellipse cx="450" cy="138" rx="50" ry="20"
                             fill="#667eea" opacity="0.3"/>

                    <text x="450" y="143" text-anchor="middle"
                          font-size="11" font-weight="bold" fill="#ffffff">
                        投影鏡頭
                    </text>
                </g>

                <!-- ==================== 對準系統（側邊） ==================== -->
                <g id="alignment-system">
                    <!-- 對準感測器 -->
                    <rect x="600" y="220" width="80" height="60" rx="5"
                          fill="#34495e" stroke="#44ff44"
                          stroke-width="2"/>

                    <!-- 對準光束 -->
                    <line x1="600" y1="250" x2="550" y2="250"
                          stroke="#44ff44" stroke-width="2"
                          stroke-dasharray="5,5" opacity="0.6"/>

                    <text x="640" y="245" text-anchor="middle"
                          font-size="11" font-weight="bold" fill="#ffffff">
                        對準
                    </text>
                    <text x="640" y="260" text-anchor="middle"
                          font-size="11" font-weight="bold" fill="#ffffff">
                        系統
                    </text>
                </g>

                <!-- ==================== 晶圓平台（底部） ==================== -->
                <g id="wafer-stage">
                    <!-- 平台基座 -->
                    <rect x="350" y="340" width="200" height="50" rx="5"
                          fill="#5a6c7d" stroke="#333" stroke-width="2"/>

                    <!-- 晶圓 -->
                    <ellipse cx="450" cy="355" rx="70" ry="15"
                             fill="#9ca3af" stroke="#4b5563" stroke-width="2"/>
                    <ellipse cx="450" cy="353" rx="60" ry="12"
                             fill="#d1d5db" opacity="0.6"/>

                    <text x="450" y="380" text-anchor="middle"
                          font-size="11" fill="#ffffff">
                        晶圓載台
                    </text>
                </g>

                <!-- ==================== 電源指示（右下） ==================== -->
                <g id="power-indicator">
                    <circle cx="680" cy="395" r="15"
                            fill="#44ff44"
                            style="animation: glow-green 2s infinite;"/>
                    <text x="680" y="420" text-anchor="middle"
                          font-size="11" fill="#44ff44">
                        運行中
                    </text>
                </g>

                <!-- ==================== 連接管路 ==================== -->
                <!-- 真空泵浦連接 -->
                <path d="M 350,250 L 200,250"
                      stroke="#888" stroke-width="6"
                      stroke-dasharray="10,5"
                      fill="none" opacity="0.6"/>

                <!-- 排氣管 -->
                <path d="M 550,250 L 700,250"
                      stroke="#888" stroke-width="6"
                      stroke-dasharray="10,5"
                      fill="none" opacity="0.6"/>

            </svg>

            <!-- 動態故障標記覆蓋層 -->
            {fault_markers}

            <!-- 狀態圖例 -->
            <div style="position: absolute; bottom: 10px; right: 10px;
                        background: rgba(0,0,0,0.8); padding: 10px;
                        border-radius: 8px; font-size: 11px; color: white;">
                <div style="margin-bottom: 5px;">
                    <span style="display: inline-block; width: 12px; height: 12px;
                                 background: #44ff44; border-radius: 50%; margin-right: 8px;"></span>
                    正常
                </div>
                <div style="margin-bottom: 5px;">
                    <span style="display: inline-block; width: 12px; height: 12px;
                                 background: #ff9800; border-radius: 50%; margin-right: 8px;"></span>
                    警告
                </div>
                <div>
                    <span style="display: inline-block; width: 12px; height: 12px;
                                 background: #ff4444; border-radius: 50%; margin-right: 8px;"></span>
                    異常
                </div>
            </div>
        </div>
        """

        return svg_html

    def _get_cooling_status(self, state: Dict) -> Dict:
        """取得冷卻系統狀態"""
        flow = state.get("cooling_flow", 5.0)
        if flow < 4.0:
            return {
                "color": "#ff4444",
                "animation": "animation: flow-slow 2s linear infinite, glow-red 2s infinite;"
            }
        elif flow < 4.5:
            return {
                "color": "#ff9800",
                "animation": "animation: flow-slow 2.5s linear infinite;"
            }
        else:
            return {
                "color": "#44aaff",
                "animation": "animation: flow-animate 2s linear infinite;"
            }

    def _get_vacuum_status(self, state: Dict) -> Dict:
        """取得真空系統狀態"""
        vacuum_leak = state.get("vacuum_leak", False)
        pressure = state.get("vacuum_pressure", 1e-6)

        if vacuum_leak or pressure > 1e-4:
            return {
                "color": "#ff4444",
                "animation": "animation: glow-red 1.5s infinite;"
            }
        elif pressure > 5e-6:
            return {
                "color": "#ff9800",
                "animation": ""
            }
        else:
            return {
                "color": "#44ff44",
                "animation": "animation: glow-green 3s infinite;"
            }

    def _get_temp_status(self, state: Dict) -> Dict:
        """取得溫度狀態"""
        temp = state.get("lens_temp", 23.0)
        if temp > 26:
            return {
                "color": "#ff4444",
                "animation": "animation: pulse-red 1.5s infinite;"
            }
        elif temp > 25:
            return {
                "color": "#ff9800",
                "animation": "animation: pulse-orange 2s infinite;"
            }
        else:
            return {
                "color": "#44ff44",
                "animation": ""
            }

    def _get_filter_status(self, state: Dict) -> Dict:
        """取得過濾網狀態"""
        clogged = state.get("filter_clogged", False)
        if clogged:
            return {
                "color": "#996600",
                "animation": "animation: pulse-orange 2s infinite;"
            }
        else:
            return {
                "color": "#cccccc",
                "animation": ""
            }

    def _get_light_status(self, state: Dict) -> Dict:
        """取得光源狀態"""
        intensity = state.get("light_intensity", 100)
        if intensity < 90:
            return {
                "color": "#ff9800",
                "animation": ""
            }
        else:
            return {
                "color": "#ffeb3b",
                "animation": "animation: glow-green 2s infinite;"
            }

    def _generate_fault_markers(self, state: Dict) -> str:
        """生成故障標記浮動層"""
        markers = []

        # 冷卻系統異常標記
        flow = state.get("cooling_flow", 5.0)
        if flow < 4.5:
            severity = "danger" if flow < 4.0 else "warning"
            markers.append(f"""
            <div style="position: absolute; top: 18%; left: 45%; transform: translate(-50%, -50%);">
                <div class="marker-pulse-{'red' if severity == 'danger' else 'orange'}"
                     style="width: 35px; height: 35px; background: {'#ff4444' if severity == 'danger' else '#ff9800'};
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;
                            color: white; font-weight: bold; font-size: 20px; cursor: pointer;
                            box-shadow: 0 0 20px {'rgba(255,68,68,0.8)' if severity == 'danger' else 'rgba(255,152,0,0.8)'};">
                    ⚠
                </div>
                <div style="position: absolute; top: 45px; left: 50%; transform: translateX(-50%);
                            background: rgba(0,0,0,0.9); color: white; padding: 6px 10px;
                            border-radius: 6px; white-space: nowrap; font-size: 12px; font-weight: bold;
                            border-left: 3px solid {'#ff4444' if severity == 'danger' else '#ff9800'};">
                    冷卻流量過低
                </div>
            </div>
            """)

        # 溫度過高標記
        temp = state.get("lens_temp", 23.0)
        if temp > 25:
            severity = "danger" if temp > 26 else "warning"
            markers.append(f"""
            <div style="position: absolute; top: 48%; right: 18%; transform: translate(50%, -50%);">
                <div class="marker-pulse-{'red' if severity == 'danger' else 'orange'}"
                     style="width: 35px; height: 35px; background: {'#ff4444' if severity == 'danger' else '#ff9800'};
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;
                            color: white; font-weight: bold; font-size: 20px; cursor: pointer;
                            box-shadow: 0 0 20px {'rgba(255,68,68,0.8)' if severity == 'danger' else 'rgba(255,152,0,0.8)'};">
                    🔥
                </div>
                <div style="position: absolute; top: 45px; left: 50%; transform: translateX(-50%);
                            background: rgba(0,0,0,0.9); color: white; padding: 6px 10px;
                            border-radius: 6px; white-space: nowrap; font-size: 12px; font-weight: bold;
                            border-left: 3px solid {'#ff4444' if severity == 'danger' else '#ff9800'};">
                    溫度過高
                </div>
            </div>
            """)

        # 真空洩漏標記
        if state.get("vacuum_leak", False):
            markers.append(f"""
            <div style="position: absolute; top: 48%; left: 50%; transform: translate(-50%, -50%);">
                <div class="marker-pulse-red"
                     style="width: 40px; height: 40px; background: #ff4444;
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;
                            color: white; font-weight: bold; font-size: 22px; cursor: pointer;
                            box-shadow: 0 0 25px rgba(255,68,68,0.9);">
                    ⚡
                </div>
                <div style="position: absolute; top: 50px; left: 50%; transform: translateX(-50%);
                            background: rgba(0,0,0,0.9); color: white; padding: 6px 10px;
                            border-radius: 6px; white-space: nowrap; font-size: 12px; font-weight: bold;
                            border-left: 3px solid #ff4444;">
                    真空洩漏
                </div>
            </div>
            """)

        # 過濾網堵塞標記
        if state.get("filter_clogged", False):
            markers.append(f"""
            <div style="position: absolute; bottom: 20%; left: 25%; transform: translateX(-50%);">
                <div class="marker-pulse-orange"
                     style="width: 30px; height: 30px; background: #ff9800;
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;
                            color: white; font-weight: bold; font-size: 18px; cursor: pointer;
                            box-shadow: 0 0 15px rgba(255,152,0,0.8);">
                    ⛔
                </div>
                <div style="position: absolute; top: 40px; left: 50%; transform: translateX(-50%);
                            background: rgba(0,0,0,0.9); color: white; padding: 6px 10px;
                            border-radius: 6px; white-space: nowrap; font-size: 12px; font-weight: bold;
                            border-left: 3px solid #ff9800;">
                    過濾網堵塞
                </div>
            </div>
            """)

        return "\n".join(markers)
