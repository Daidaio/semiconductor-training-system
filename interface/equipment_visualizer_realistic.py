# -*- coding: utf-8 -*-
"""
超真實光刻曝光機設備視覺化器（Photorealistic Lithography Scanner Visualizer）
使用高品質 SVG 和真實材質效果，接近實際設備照片的風格
"""

from typing import Dict


class RealisticEquipmentVisualizer:
    """超真實設備視覺化生成器"""

    def generate_equipment_svg(self, state: Dict) -> str:
        """
        生成超真實 SVG 格式的設備圖

        Args:
            state: 設備狀態字典

        Returns:
            HTML字串（包含 SVG 和動畫）
        """

        # 計算各部件狀態
        cooling_status = self._get_cooling_status(state)
        vacuum_status = self._get_vacuum_status(state)
        temp_status = self._get_temp_status(state)
        filter_status = self._get_filter_status(state)
        light_status = self._get_light_status(state)

        # 生成 HTML + SVG
        html = f"""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
                    padding: 20px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">

            <svg width="100%" height="100%" viewBox="0 0 1000 600" xmlns="http://www.w3.org/2000/svg">

                <!-- ========================= 材質定義 ========================= -->
                <defs>
                    <!-- 鋁合金外殼材質 -->
                    <linearGradient id="aluminumBody" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#e0e7ee;stop-opacity:1" />
                        <stop offset="15%" style="stop-color:#f8fafc;stop-opacity:1" />
                        <stop offset="40%" style="stop-color:#cbd5e1;stop-opacity:1" />
                        <stop offset="70%" style="stop-color:#94a3b8;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#64748b;stop-opacity:1" />
                    </linearGradient>

                    <!-- 深色機殼 -->
                    <linearGradient id="darkCasing" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#475569;stop-opacity:1" />
                        <stop offset="50%" style="stop-color:#334155;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#1e293b;stop-opacity:1" />
                    </linearGradient>

                    <!-- 玻璃視窗 -->
                    <radialGradient id="glassWindow" cx="40%" cy="40%">
                        <stop offset="0%" style="stop-color:#e0f2fe;stop-opacity:0.5" />
                        <stop offset="50%" style="stop-color:#bae6fd;stop-opacity:0.4" />
                        <stop offset="100%" style="stop-color:#0ea5e9;stop-opacity:0.6" />
                    </radialGradient>

                    <!-- 金屬光澤反光 -->
                    <radialGradient id="metalShine" cx="30%" cy="30%">
                        <stop offset="0%" style="stop-color:#ffffff;stop-opacity:0.8" />
                        <stop offset="50%" style="stop-color:#ffffff;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#ffffff;stop-opacity:0" />
                    </radialGradient>

                    <!-- 管路金屬 -->
                    <linearGradient id="pipeMetal" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" style="stop-color:#94a3b8;stop-opacity:1" />
                        <stop offset="50%" style="stop-color:#cbd5e1;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#94a3b8;stop-opacity:1" />
                    </linearGradient>

                    <!-- 立體陰影 -->
                    <filter id="deepShadow">
                        <feGaussianBlur in="SourceAlpha" stdDeviation="5"/>
                        <feOffset dx="4" dy="4" result="offsetblur"/>
                        <feComponentTransfer>
                            <feFuncA type="linear" slope="0.5"/>
                        </feComponentTransfer>
                        <feMerge>
                            <feMergeNode/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>

                    <!-- 內陰影（凹陷） -->
                    <filter id="innerDepth">
                        <feGaussianBlur in="SourceAlpha" stdDeviation="3"/>
                        <feOffset dx="2" dy="2"/>
                        <feComposite operator="arithmetic" k2="-1" k3="1"/>
                        <feColorMatrix type="matrix" values="0 0 0 0 0, 0 0 0 0 0, 0 0 0 0 0, 0 0 0 0.4 0"/>
                        <feBlend in2="SourceGraphic" mode="normal"/>
                    </filter>

                    <!-- 玻璃反射 -->
                    <filter id="glassReflect">
                        <feGaussianBlur stdDeviation="1.5"/>
                        <feColorMatrix type="matrix"
                            values="1 0 0 0 0.2, 0 1 0 0 0.3, 0 0 1 0 0.5, 0 0 0 0.6 0"/>
                    </filter>

                    <!-- 發光效果（用於警示）-->
                    <filter id="warningGlow">
                        <feGaussianBlur stdDeviation="8" result="coloredBlur"/>
                        <feMerge>
                            <feMergeNode in="coloredBlur"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                </defs>

                <!-- ========================= 背景和標題 ========================= -->
                <rect width="1000" height="600" fill="url(#darkCasing)"/>

                <text x="500" y="35" text-anchor="middle"
                      font-family="Arial, sans-serif" font-size="28" font-weight="bold"
                      fill="#f1f5f9" style="text-shadow: 3px 3px 6px rgba(0,0,0,0.7);">
                    光刻曝光機 (Lithography Scanner)
                </text>

                <text x="500" y="58" text-anchor="middle"
                      font-family="Arial, sans-serif" font-size="13" fill="#94a3b8">
                    ASML PAS 5500 系列 - 193nm ArF 準分子雷射系統
                </text>

                <!-- ========================= 主機箱體 ========================= -->
                <!-- 機箱背板 -->
                <rect x="150" y="90" width="700" height="450" rx="25" ry="25"
                      fill="url(#aluminumBody)" stroke="#475569" stroke-width="3"
                      filter="url(#deepShadow)"/>

                <!-- 機箱金屬反光 -->
                <ellipse cx="300" cy="180" rx="120" ry="80"
                         fill="url(#metalShine)" opacity="0.4"/>

                <!-- 通風格柵（頂部）-->
                <g id="ventilation-grille">
                    <rect x="380" y="105" width="240" height="15" rx="3"
                          fill="#1e293b" stroke="#0f172a" stroke-width="1"
                          filter="url(#innerDepth)"/>
                    <!-- 格柵條紋 -->
                    <line x1="400" y1="108" x2="400" y2="117" stroke="#475569" stroke-width="1.5"/>
                    <line x1="420" y1="108" x2="420" y2="117" stroke="#475569" stroke-width="1.5"/>
                    <line x1="440" y1="108" x2="440" y2="117" stroke="#475569" stroke-width="1.5"/>
                    <line x1="460" y1="108" x2="460" y2="117" stroke="#475569" stroke-width="1.5"/>
                    <line x1="480" y1="108" x2="480" y2="117" stroke="#475569" stroke-width="1.5"/>
                    <line x1="500" y1="108" x2="500" y2="117" stroke="#475569" stroke-width="1.5"/>
                    <line x1="520" y1="108" x2="520" y2="117" stroke="#475569" stroke-width="1.5"/>
                    <line x1="540" y1="108" x2="540" y2="117" stroke="#475569" stroke-width="1.5"/>
                    <line x1="560" y1="108" x2="560" y2="117" stroke="#475569" stroke-width="1.5"/>
                    <line x1="580" y1="108" x2="580" y2="117" stroke="#475569" stroke-width="1.5"/>
                    <line x1="600" y1="108" x2="600" y2="117" stroke="#475569" stroke-width="1.5"/>
                </g>

                <!-- 螺絲細節（左上角）-->
                <circle cx="175" cy="110" r="4" fill="#334155" stroke="#1e293b" stroke-width="1"/>
                <line x1="172" y1="110" x2="178" y2="110" stroke="#64748b" stroke-width="0.8"/>
                <circle cx="825" cy="110" r="4" fill="#334155" stroke="#1e293b" stroke-width="1"/>
                <line x1="822" y1="110" x2="828" y2="110" stroke="#64748b" stroke-width="0.8"/>
                <circle cx="175" cy="515" r="4" fill="#334155" stroke="#1e293b" stroke-width="1"/>
                <line x1="172" y1="515" x2="178" y2="515" stroke="#64748b" stroke-width="0.8"/>
                <circle cx="825" cy="515" r="4" fill="#334155" stroke="#1e293b" stroke-width="1"/>
                <line x1="822" y1="515" x2="828" y2="515" stroke="#64748b" stroke-width="0.8"/>

                <!-- ========================= 光源模組（頂部）========================= -->
                <g id="light-source">
                    <!-- 光源外殼 -->
                    <rect x="400" y="130" width="200" height="50" rx="8"
                          fill="url(#darkCasing)" stroke="#0f172a" stroke-width="2"
                          filter="url(#deepShadow)"/>

                    <!-- 光源發光部分 -->
                    <rect x="415" y="142" width="170" height="26" rx="5"
                          fill="{light_status['color']}" opacity="0.8"
                          style="{light_status['animation']}"
                          filter="url(#warningGlow)"/>

                    <!-- 光源標籤 -->
                    <rect x="408" y="135" width="75" height="14" rx="3" fill="#1e293b"/>
                    <text x="445" y="145" text-anchor="middle" font-size="10"
                          font-weight="bold" fill="#94a3b8">193nm ArF</text>

                    <!-- 光束投射（向下）-->
                    <path d="M 430,180 L 420,210" stroke="{light_status['color']}"
                          stroke-width="6" opacity="0.4" stroke-linecap="round"/>
                    <path d="M 460,180 L 455,210" stroke="{light_status['color']}"
                          stroke-width="8" opacity="0.5" stroke-linecap="round"/>
                    <path d="M 490,180 L 485,210" stroke="{light_status['color']}"
                          stroke-width="8" opacity="0.5" stroke-linecap="round"/>
                    <path d="M 520,180 L 515,210" stroke="{light_status['color']}"
                          stroke-width="8" opacity="0.5" stroke-linecap="round"/>
                    <path d="M 550,180 L 545,210" stroke="{light_status['color']}"
                          stroke-width="8" opacity="0.5" stroke-linecap="round"/>
                    <path d="M 570,180 L 580,210" stroke="{light_status['color']}"
                          stroke-width="6" opacity="0.4" stroke-linecap="round"/>

                    <!-- 狀態指示燈 -->
                    <circle cx="570" cy="148" r="4" fill="{light_status['color']}"
                            style="animation: glow-pulse 1.5s infinite;"/>
                </g>

                <!-- ========================= 投影鏡頭組（上層）========================= -->
                <g id="projection-lens">
                    <!-- 鏡頭外殼 -->
                    <rect x="380" y="215" width="240" height="80" rx="12"
                          fill="url(#darkCasing)" stroke="#0f172a" stroke-width="2"
                          filter="url(#deepShadow)"/>

                    <!-- 鏡頭組件 -->
                    <ellipse cx="500" cy="255" rx="90" ry="35"
                             fill="url(#pipeMetal)" stroke="#475569" stroke-width="2"/>
                    <ellipse cx="500" cy="253" rx="75" ry="28"
                             fill="url(#glassWindow)" filter="url(#glassReflect)"/>

                    <!-- 鏡頭反光 -->
                    <ellipse cx="480" cy="245" rx="40" ry="15"
                             fill="#ffffff" opacity="0.3"/>

                    <!-- 標籤 -->
                    <rect x="385" y="220" width="100" height="16" rx="3" fill="#1e293b"/>
                    <text x="435" y="231" text-anchor="middle" font-size="11"
                          font-weight="bold" fill="#cbd5e1">投影鏡頭組</text>
                </g>

                <!-- ========================= 真空腔體（中層）========================= -->
                <g id="vacuum-chamber">
                    <!-- 腔體外框 -->
                    <rect x="300" y="305" width="400" height="120" rx="15"
                          fill="url(#aluminumBody)" stroke="#475569" stroke-width="3"
                          filter="url(#deepShadow)"/>

                    <!-- 玻璃視窗 -->
                    <rect x="330" y="325" width="340" height="80" rx="10"
                          fill="url(#glassWindow)" stroke="#0ea5e9" stroke-width="2"
                          style="{vacuum_status['animation']}"
                          filter="url(#glassReflect)"/>

                    <!-- 真空狀態指示 -->
                    <circle cx="655" cy="315" r="6" fill="{vacuum_status['color']}"
                            style="{vacuum_status['animation']}"/>

                    <!-- 標籤和壓力值 -->
                    <rect x="305" y="310" width="90" height="18" rx="4" fill="#1e293b" opacity="0.9"/>
                    <text x="350" y="322" text-anchor="middle" font-size="11"
                          font-weight="bold" fill="#cbd5e1">真空腔體</text>

                    <rect x="560" y="430" width="130" height="22" rx="4" fill="#0f172a" opacity="0.95"/>
                    <text x="625" y="445" text-anchor="middle" font-size="12"
                          font-weight="bold" fill="{vacuum_status['color']}">
                        {state.get('vacuum_pressure', 1e-6):.2e} Torr
                    </text>
                </g>

                <!-- ========================= 晶圓載台（底部）========================= -->
                <g id="wafer-stage">
                    <!-- 載台基座 -->
                    <rect x="350" y="435" width="300" height="60" rx="8"
                          fill="url(#darkCasing)" stroke="#1e293b" stroke-width="2"
                          filter="url(#deepShadow)"/>

                    <!-- 精密移動軸（X/Y軸標示）-->
                    <rect x="360" y="445" width="10" height="40" fill="#475569"/>
                    <rect x="630" y="445" width="10" height="40" fill="#475569"/>

                    <!-- 晶圓片 -->
                    <ellipse cx="500" cy="455" rx="100" ry="20"
                             fill="#94a3b8" stroke="#64748b" stroke-width="2"/>
                    <ellipse cx="500" cy="453" rx="85" ry="16"
                             fill="#cbd5e1" opacity="0.6"/>

                    <!-- 晶圓反光 -->
                    <ellipse cx="480" cy="450" rx="40" ry="8"
                             fill="#ffffff" opacity="0.4"/>

                    <!-- 標籤 -->
                    <rect x="355" y="440" width="80" height="16" rx="3" fill="#0f172a" opacity="0.9"/>
                    <text x="395" y="451" text-anchor="middle" font-size="10"
                          font-weight="bold" fill="#cbd5e1">晶圓載台</text>
                </g>

                <!-- ========================= 冷卻水系統（右側）========================= -->
                <g id="cooling-system">
                    <!-- 冷卻水泵 -->
                    <rect x="720" y="250" width="100" height="80" rx="10"
                          fill="url(#darkCasing)" stroke="#0f172a" stroke-width="2"
                          filter="url(#deepShadow)"/>

                    <!-- 管路連接 -->
                    <path d="M 720,270 L 700,270" stroke="url(#pipeMetal)"
                          stroke-width="12" stroke-linecap="round"/>
                    <path d="M 720,310 L 700,310" stroke="url(#pipeMetal)"
                          stroke-width="12" stroke-linecap="round"/>

                    <!-- 水流動畫 -->
                    <path d="M 700,270 L 720,270" stroke="{cooling_status['color']}"
                          stroke-width="8" opacity="0.7" stroke-linecap="round"
                          style="{cooling_status['animation']}">
                        <animate attributeName="stroke-dasharray" from="0,20" to="20,0"
                                 dur="1.5s" repeatCount="indefinite"/>
                    </path>

                    <!-- 流量顯示 -->
                    <rect x="725" y="255" width="90" height="20" rx="4" fill="#0f172a" opacity="0.95"/>
                    <text x="770" y="268" text-anchor="middle" font-size="11"
                          font-weight="bold" fill="{cooling_status['color']}">
                        {state.get('cooling_flow', 5.0):.1f} L/min
                    </text>

                    <!-- 溫度感測器 -->
                    <circle cx="770" cy="300" r="15" fill="#1e293b" stroke="{temp_status['color']}"
                            stroke-width="3" style="{temp_status['animation']}"/>
                    <text x="770" y="305" text-anchor="middle" font-size="11"
                          font-weight="bold" fill="{temp_status['color']}">
                        {state.get('lens_temp', 23.0):.1f}°
                    </text>
                </g>

                <!-- ========================= 對準系統（左側）========================= -->
                <g id="alignment-system">
                    <!-- 對準相機模組 -->
                    <rect x="180" y="260" width="90" height="70" rx="8"
                          fill="url(#darkCasing)" stroke="#0f172a" stroke-width="2"
                          filter="url(#deepShadow)"/>

                    <!-- 鏡頭 -->
                    <circle cx="225" cy="295" r="22" fill="#1e293b" stroke="#475569" stroke-width="2"/>
                    <circle cx="225" cy="295" r="16" fill="#0f172a"/>
                    <circle cx="225" cy="295" r="10" fill="url(#glassWindow)"/>

                    <!-- 對準光束 -->
                    <line x1="270" y1="295" x2="330" y2="360" stroke="#10b981"
                          stroke-width="3" stroke-dasharray="6,4" opacity="0.6">
                        <animate attributeName="opacity" values="0.6;0.3;0.6"
                                 dur="2s" repeatCount="indefinite"/>
                    </line>

                    <!-- 標籤 -->
                    <rect x="185" y="265" width="75" height="14" rx="3" fill="#0f172a" opacity="0.9"/>
                    <text x="222" y="275" text-anchor="middle" font-size="10"
                          font-weight="bold" fill="#10b981">對準系統</text>
                </g>

                <!-- ========================= 控制面板（底部右側）========================= -->
                <g id="control-panel">
                    <!-- 面板 -->
                    <rect x="720" y="420" width="100" height="100" rx="10"
                          fill="url(#darkCasing)" stroke="#0f172a" stroke-width="2"
                          filter="url(#innerDepth)"/>

                    <!-- 顯示螢幕 -->
                    <rect x="730" y="430" width="80" height="45" rx="4"
                          fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
                    <text x="770" y="450" text-anchor="middle" font-size="10"
                          fill="#10b981">READY</text>
                    <text x="770" y="465" text-anchor="middle" font-size="8"
                          fill="#64748b">系統正常</text>

                    <!-- 按鈕 -->
                    <circle cx="745" cy="495" r="8" fill="#22c55e" opacity="0.8">
                        <animate attributeName="opacity" values="0.8;0.4;0.8"
                                 dur="2s" repeatCount="indefinite"/>
                    </circle>
                    <circle cx="770" cy="495" r="8" fill="#eab308"/>
                    <circle cx="795" cy="495" r="8" fill="#6b7280"/>
                </g>

                <!-- ========================= 過濾網（底部左側）========================= -->
                <g id="filter-unit">
                    <rect x="180" y="420" width="90" height="100" rx="10"
                          fill="url(#aluminumBody)" stroke="#475569" stroke-width="2"
                          filter="url(#deepShadow)"/>

                    <!-- 過濾網格 -->
                    <rect x="190" y="435" width="70" height="70" rx="4"
                          fill="#334155" stroke="{filter_status['color']}" stroke-width="2"
                          style="{filter_status['animation']}"
                          filter="url(#innerDepth)"/>

                    <!-- 網格紋理 -->
                    <g opacity="0.5">
                        <line x1="195" y1="440" x2="195" y2="500" stroke="#64748b" stroke-width="1"/>
                        <line x1="205" y1="440" x2="205" y2="500" stroke="#64748b" stroke-width="1"/>
                        <line x1="215" y1="440" x2="215" y2="500" stroke="#64748b" stroke-width="1"/>
                        <line x1="225" y1="440" x2="225" y2="500" stroke="#64748b" stroke-width="1"/>
                        <line x1="235" y1="440" x2="235" y2="500" stroke="#64748b" stroke-width="1"/>
                        <line x1="245" y1="440" x2="245" y2="500" stroke="#64748b" stroke-width="1"/>
                        <line x1="255" y1="440" x2="255" y2="500" stroke="#64748b" stroke-width="1"/>
                        <line x1="190" y1="445" x2="260" y2="445" stroke="#64748b" stroke-width="1"/>
                        <line x1="190" y1="455" x2="260" y2="455" stroke="#64748b" stroke-width="1"/>
                        <line x1="190" y1="465" x2="260" y2="465" stroke="#64748b" stroke-width="1"/>
                        <line x1="190" y1="475" x2="260" y2="475" stroke="#64748b" stroke-width="1"/>
                        <line x1="190" y1="485" x2="260" y2="485" stroke="#64748b" stroke-width="1"/>
                        <line x1="190" y1="495" x2="260" y2="495" stroke="#64748b" stroke-width="1"/>
                    </g>

                    <!-- 標籤 -->
                    <rect x="185" y="425" width="65" height="14" rx="3" fill="#0f172a" opacity="0.9"/>
                    <text x="217" y="435" text-anchor="middle" font-size="10"
                          font-weight="bold" fill="#cbd5e1">空氣過濾</text>
                </g>

                <!-- ========================= 故障標記浮動層 ========================= -->
                {self._generate_fault_markers(state)}

                <!-- ========================= 狀態圖例（右下角）========================= -->
                <g id="status-legend">
                    <rect x="850" y="510" width="130" height="75" rx="8"
                          fill="#0f172a" fill-opacity="0.9" stroke="#334155" stroke-width="1"/>

                    <text x="915" y="527" text-anchor="middle" font-size="11"
                          font-weight="bold" fill="#cbd5e1">狀態圖例</text>

                    <circle cx="865" cy="545" r="5" fill="#22c55e"/>
                    <text x="875" y="549" font-size="10" fill="#cbd5e1">正常</text>

                    <circle cx="865" cy="560" r="5" fill="#f59e0b"/>
                    <text x="875" y="564" font-size="10" fill="#cbd5e1">警告</text>

                    <circle cx="865" cy="575" r="5" fill="#ef4444"/>
                    <text x="875" y="579" font-size="10" fill="#cbd5e1">異常</text>
                </g>

                <!-- ========================= 品牌標誌 ========================= -->
                <text x="500" y="575" text-anchor="middle" font-family="Arial"
                      font-size="10" font-weight="bold" fill="#475569" opacity="0.6">
                    ASML • TAIWAN FACILITY • 193nm DUV LITHOGRAPHY
                </text>

            </svg>

            <!-- CSS 動畫定義 -->
            <style>
                @keyframes flow-normal {{
                    0% {{ stroke-dashoffset: 0; }}
                    100% {{ stroke-dashoffset: 40; }}
                }}

                @keyframes flow-slow {{
                    0% {{ stroke-dashoffset: 0; }}
                    100% {{ stroke-dashoffset: -40; }}
                }}

                @keyframes pulse-warning {{
                    0%, 100% {{
                        opacity: 1;
                        filter: drop-shadow(0 0 8px {cooling_status['color']});
                    }}
                    50% {{
                        opacity: 0.6;
                        filter: drop-shadow(0 0 15px {cooling_status['color']});
                    }}
                }}

                @keyframes pulse-danger {{
                    0%, 100% {{
                        opacity: 1;
                        filter: drop-shadow(0 0 12px #ef4444);
                    }}
                    50% {{
                        opacity: 0.5;
                        filter: drop-shadow(0 0 20px #ef4444);
                    }}
                }}

                @keyframes glow-pulse {{
                    0%, 100% {{
                        opacity: 1;
                        filter: drop-shadow(0 0 4px currentColor);
                    }}
                    50% {{
                        opacity: 0.4;
                        filter: drop-shadow(0 0 8px currentColor);
                    }}
                }}
            </style>
        </div>
        """

        return html

    def _get_cooling_status(self, state: Dict) -> Dict:
        """獲取冷卻系統狀態"""
        flow_rate = state.get("cooling_flow", 5.0)

        if flow_rate < 4.0:
            return {
                "color": "#ef4444",  # 紅色
                "animation": "animation: pulse-danger 1s infinite;"
            }
        elif flow_rate < 4.5:
            return {
                "color": "#f59e0b",  # 橙色
                "animation": "animation: pulse-warning 2s infinite;"
            }
        else:
            return {
                "color": "#0ea5e9",  # 藍色（正常）
                "animation": "animation: flow-normal 2s linear infinite;"
            }

    def _get_vacuum_status(self, state: Dict) -> Dict:
        """獲取真空系統狀態"""
        vacuum_leak = state.get("vacuum_leak", False)
        pressure = state.get("vacuum_pressure", 1e-6)

        if vacuum_leak or pressure > 1e-5:
            return {
                "color": "#ef4444",
                "animation": "animation: pulse-danger 1.5s infinite;"
            }
        else:
            return {
                "color": "#22c55e",
                "animation": ""
            }

    def _get_temp_status(self, state: Dict) -> Dict:
        """獲取溫度狀態"""
        temp = state.get("lens_temp", 23.0)

        if temp > 26:
            return {
                "color": "#ef4444",
                "animation": "animation: pulse-danger 1s infinite;"
            }
        elif temp > 25:
            return {
                "color": "#f59e0b",
                "animation": "animation: pulse-warning 2s infinite;"
            }
        else:
            return {
                "color": "#22c55e",
                "animation": ""
            }

    def _get_filter_status(self, state: Dict) -> Dict:
        """獲取過濾網狀態"""
        clogged = state.get("filter_clogged", False)

        if clogged:
            return {
                "color": "#f59e0b",
                "animation": "animation: pulse-warning 2s infinite;"
            }
        else:
            return {
                "color": "#64748b",
                "animation": ""
            }

    def _get_light_status(self, state: Dict) -> Dict:
        """獲取光源狀態"""
        intensity = state.get("light_intensity", 100)

        if intensity < 90:
            return {
                "color": "#f59e0b",
                "animation": "animation: pulse-warning 2s infinite;"
            }
        else:
            return {
                "color": "#8b5cf6",  # 紫色（正常光源）
                "animation": ""
            }

    def _generate_fault_markers(self, state: Dict) -> str:
        """生成故障標記浮動標籤"""
        markers = []

        # 冷卻流量
        flow_rate = state.get("cooling_flow", 5.0)
        if flow_rate < 4.5:
            severity = "danger" if flow_rate < 4.0 else "warning"
            color = "#ef4444" if severity == "danger" else "#f59e0b"
            markers.append(f"""
                <g id="cooling-fault-marker">
                    <rect x="725" y="280" width="95" height="28" rx="5"
                          fill="#0f172a" fill-opacity="0.95" stroke="{color}" stroke-width="2"/>
                    <text x="772" y="298" text-anchor="middle" font-size="11"
                          font-weight="bold" fill="{color}">
                        ⚠ 流量過低
                    </text>
                </g>
            """)

        # 真空洩漏
        if state.get("vacuum_leak", False):
            markers.append(f"""
                <g id="vacuum-fault-marker">
                    <rect x="545" y="460" width="110" height="28" rx="5"
                          fill="#0f172a" fill-opacity="0.95" stroke="#ef4444" stroke-width="2"/>
                    <text x="600" y="478" text-anchor="middle" font-size="11"
                          font-weight="bold" fill="#ef4444">
                        ⚡ 真空洩漏
                    </text>
                </g>
            """)

        # 溫度過高
        temp = state.get("lens_temp", 23.0)
        if temp > 25:
            severity = "danger" if temp > 26 else "warning"
            color = "#ef4444" if severity == "danger" else "#f59e0b"
            markers.append(f"""
                <g id="temp-fault-marker">
                    <rect x="715" y="330" width="110" height="28" rx="5"
                          fill="#0f172a" fill-opacity="0.95" stroke="{color}" stroke-width="2"/>
                    <text x="770" y="348" text-anchor="middle" font-size="11"
                          font-weight="bold" fill="{color}">
                        🔥 溫度過高
                    </text>
                </g>
            """)

        # 過濾網堵塞
        if state.get("filter_clogged", False):
            markers.append(f"""
                <g id="filter-fault-marker">
                    <rect x="175" y="510" width="100" height="28" rx="5"
                          fill="#0f172a" fill-opacity="0.95" stroke="#f59e0b" stroke-width="2"/>
                    <text x="225" y="528" text-anchor="middle" font-size="11"
                          font-weight="bold" fill="#f59e0b">
                        ⛔ 過濾堵塞
                    </text>
                </g>
            """)

        return "\n".join(markers)
