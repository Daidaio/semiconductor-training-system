# -*- coding: utf-8 -*-
"""
工業產線視覺化器 (Industrial Production Line Visualizer)
完全仿照 Paper Figure 2 風格：
- 橫向產線佈局（多台設備排成一列）
- 設備上方浮動資訊卡片
- 左側故障告警面板
- 藍色數據流連接線
- 工業監控室風格
"""

from typing import Dict, List
import base64
from pathlib import Path


class IndustrialEquipmentVisualizer:
    """工業產線視覺化生成器 (完全仿造 Paper 圖片 2 風格)"""

    def __init__(self):
        """初始化視覺化器"""
        pass

    def generate_equipment_view(self, state: Dict, selected_component: str = None) -> str:
        """
        生成產線視覺化 (Paper Figure 2 風格)

        Args:
            state: 設備狀態字典
            selected_component: 選中的部件

        Returns:
            HTML字串
        """

        # 獲取即時感測器數據
        cooling_flow = state.get('cooling_flow', 5.0)
        lens_temp = state.get('lens_temp', 23.0)
        vacuum_pressure = state.get('vacuum_pressure', 1.0e-6)
        light_intensity = state.get('light_intensity', 100.0)
        filter_pressure = state.get('filter_pressure_drop', 50.0)
        alignment_error = state.get('alignment_error', 0.0)

        # 判斷各系統狀態
        cooling_status = "critical" if abs(cooling_flow - 5.0) / 5.0 > 0.15 else ("warning" if abs(cooling_flow - 5.0) / 5.0 > 0.05 else "normal")
        temp_status = "critical" if abs(lens_temp - 23.0) > 0.5 else ("warning" if abs(lens_temp - 23.0) > 0.2 else "normal")
        vacuum_status = "critical" if vacuum_pressure > 2.0e-6 else ("warning" if vacuum_pressure > 1.5e-6 else "normal")
        light_status = "critical" if abs(light_intensity - 100.0) > 10 else ("warning" if abs(light_intensity - 100.0) > 5 else "normal")
        filter_status = "critical" if filter_pressure > 150 else ("warning" if filter_pressure > 100 else "normal")

        # 生成故障告警列表
        fault_alarms_html = self._generate_fault_alarms(
            cooling_flow, lens_temp, vacuum_pressure, light_intensity, filter_pressure,
            cooling_status, temp_status, vacuum_status, light_status, filter_status
        )

        # 生成多設備產線視圖
        production_line_html = self._generate_production_line(
            cooling_flow, lens_temp, vacuum_pressure, light_intensity, filter_pressure,
            cooling_status, temp_status, vacuum_status, light_status, filter_status
        )

        html = f"""
        <div style="position: relative; background: linear-gradient(135deg, #0d1117 0%, #1a1f2e 100%);
                    padding: 20px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.9);
                    font-family: 'Microsoft YaHei', sans-serif;">

            <!-- 頂部標題列 -->
            <div style="background: linear-gradient(90deg, #1e3a5f 0%, #2d5a8c 100%);
                        padding: 15px 25px; border-radius: 8px; margin-bottom: 20px;
                        border: 1px solid #3a5f8c; box-shadow: 0 4px 12px rgba(0,0,0,0.6);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="color: #e0f2ff; margin: 0; font-size: 24px; font-weight: bold;">
                            半導體製造產線監控系統
                        </h2>
                        <p style="color: #94c5e8; margin: 5px 0 0 0; font-size: 13px;">
                            Semiconductor Manufacturing Production Line Monitoring System
                        </p>
                    </div>
                    <div style="background: rgba(0,0,0,0.3); padding: 10px 20px; border-radius: 6px;
                               border: 1px solid #3a5f8c;">
                        <span style="color: #94c5e8; font-size: 12px;">產線 ID:</span>
                        <span style="color: #e0f2ff; font-size: 15px; font-weight: bold; margin-left: 10px;">LINE-A01</span>
                    </div>
                </div>
            </div>

            <!-- 主要內容區：左側告警 + 右側產線 -->
            <div style="display: grid; grid-template-columns: 280px 1fr; gap: 20px;">

                <!-- 左側: 故障告警面板 (Fault Alarm Panel) -->
                <div style="background: rgba(15, 23, 42, 0.95); border-radius: 10px;
                           border: 2px solid #2d4a6e; padding: 18px;
                           box-shadow: inset 0 0 25px rgba(0,0,0,0.6);">
                    <div style="color: #e0f2ff; font-size: 16px; font-weight: bold;
                               margin-bottom: 15px; padding-bottom: 10px;
                               border-bottom: 2px solid #ff6b6b; text-align: center;">
                        ⚠ Fault Alarm
                    </div>
                    {fault_alarms_html}
                </div>

                <!-- 右側: 產線設備視圖 (Production Line View) -->
                {production_line_html}

            </div>

            <!-- 底部狀態圖例 -->
            <div style="margin-top: 20px; padding: 12px 20px; background: rgba(15, 23, 42, 0.6);
                       border-radius: 8px; border: 1px solid #2d4a6e; display: flex; gap: 30px; justify-content: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 12px; height: 12px; background: #4ade80; border-radius: 50%;"></div>
                    <span style="color: #94c5e8; font-size: 12px;">正常 Normal</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 12px; height: 12px; background: #fbbf24; border-radius: 50%;"></div>
                    <span style="color: #94c5e8; font-size: 12px;">警告 Warning</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 12px; height: 12px; background: #ef4444; border-radius: 50%; animation: blink 1s infinite;"></div>
                    <span style="color: #94c5e8; font-size: 12px;">嚴重 Critical</span>
                </div>
            </div>

            <style>
                @keyframes blink {{
                    0%, 100% {{ opacity: 1; box-shadow: 0 0 10px #ef4444; }}
                    50% {{ opacity: 0.3; box-shadow: 0 0 20px #ef4444; }}
                }}
                @keyframes pulse {{
                    0%, 100% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.05); }}
                }}
                @keyframes flowLine {{
                    0% {{ stroke-dashoffset: 20; }}
                    100% {{ stroke-dashoffset: 0; }}
                }}
            </style>
        </div>
        """

        return html

    def _generate_fault_alarms(self, cooling_flow, lens_temp, vacuum_pressure,
                               light_intensity, filter_pressure,
                               cooling_status, temp_status, vacuum_status,
                               light_status, filter_status) -> str:
        """生成故障告警列表（類似 Paper 左側面板）"""

        alarms = []

        # 檢查冷卻系統
        if cooling_status in ["warning", "critical"]:
            severity = "CRITICAL" if cooling_status == "critical" else "WARNING"
            color = "#ef4444" if cooling_status == "critical" else "#fbbf24"
            animation = "animation: pulse 1s infinite;" if cooling_status == "critical" else ""
            alarms.append(f"""
                <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid {color};
                           padding: 12px; margin-bottom: 10px; border-radius: 6px; {animation}">
                    <div style="color: {color}; font-size: 11px; font-weight: bold; margin-bottom: 4px;">
                        [{severity}] ALARM-001
                    </div>
                    <div style="color: #e0f2ff; font-size: 13px; font-weight: bold; margin-bottom: 6px;">
                        冷卻流量異常
                    </div>
                    <div style="color: #94c5e8; font-size: 11px;">
                        當前: {cooling_flow:.2f} L/min<br>
                        標準: 5.0 L/min
                    </div>
                </div>
            """)

        # 檢查溫度
        if temp_status in ["warning", "critical"]:
            severity = "CRITICAL" if temp_status == "critical" else "WARNING"
            color = "#ef4444" if temp_status == "critical" else "#fbbf24"
            animation = "animation: pulse 1s infinite;" if temp_status == "critical" else ""
            alarms.append(f"""
                <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid {color};
                           padding: 12px; margin-bottom: 10px; border-radius: 6px; {animation}">
                    <div style="color: {color}; font-size: 11px; font-weight: bold; margin-bottom: 4px;">
                        [{severity}] ALARM-002
                    </div>
                    <div style="color: #e0f2ff; font-size: 13px; font-weight: bold; margin-bottom: 6px;">
                        鏡頭溫度異常
                    </div>
                    <div style="color: #94c5e8; font-size: 11px;">
                        當前: {lens_temp:.2f}°C<br>
                        標準: 23.0°C
                    </div>
                </div>
            """)

        # 檢查真空
        if vacuum_status in ["warning", "critical"]:
            severity = "CRITICAL" if vacuum_status == "critical" else "WARNING"
            color = "#ef4444" if vacuum_status == "critical" else "#fbbf24"
            animation = "animation: pulse 1s infinite;" if vacuum_status == "critical" else ""
            alarms.append(f"""
                <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid {color};
                           padding: 12px; margin-bottom: 10px; border-radius: 6px; {animation}">
                    <div style="color: {color}; font-size: 11px; font-weight: bold; margin-bottom: 4px;">
                        [{severity}] ALARM-003
                    </div>
                    <div style="color: #e0f2ff; font-size: 13px; font-weight: bold; margin-bottom: 6px;">
                        真空壓力異常
                    </div>
                    <div style="color: #94c5e8; font-size: 11px;">
                        當前: {vacuum_pressure:.2e} Torr<br>
                        標準: 1.0e-6 Torr
                    </div>
                </div>
            """)

        if not alarms:
            alarms.append("""
                <div style="text-align: center; padding: 30px 10px; color: #4ade80;">
                    <div style="font-size: 40px; margin-bottom: 10px;">✓</div>
                    <div style="font-size: 13px; font-weight: bold;">系統運行正常</div>
                    <div style="font-size: 11px; color: #94c5e8; margin-top: 5px;">All Systems Normal</div>
                </div>
            """)

        return "".join(alarms)

    def _generate_production_line(self, cooling_flow, lens_temp, vacuum_pressure,
                                  light_intensity, filter_pressure,
                                  cooling_status, temp_status, vacuum_status,
                                  light_status, filter_status) -> str:
        """生成產線設備視圖（橫向排列，類似 Paper Figure 2）"""

        # 定義 5 個設備模組
        equipment_modules = [
            {
                "id": "ET01",
                "name": "清洗模組",
                "process": "Wafer Cleaning",
                "temp": "30°C",
                "pressure": "0.15 MPa",
                "flow": f"{cooling_flow:.1f} L/min",
                "status": cooling_status,
                "x": 50,
                "info_top": -120
            },
            {
                "id": "ET02",
                "name": "塗佈模組",
                "process": "Resist Coating",
                "temp": f"{lens_temp:.1f}°C",
                "pressure": "0.15 MPa",
                "thickness": "2 μm",
                "status": temp_status,
                "x": 250,
                "info_top": 320
            },
            {
                "id": "ET03",
                "name": "曝光模組",
                "process": "Lithography",
                "vacuum": f"{vacuum_pressure:.2e} Torr",
                "power": f"{light_intensity:.0f}%",
                "status": vacuum_status,
                "x": 450,
                "info_top": -120
            },
            {
                "id": "ET04",
                "name": "顯影模組",
                "process": "Development",
                "temp": "40°C",
                "flow": "150 L/min",
                "status": light_status,
                "x": 650,
                "info_top": 320
            },
            {
                "id": "ET05",
                "name": "蝕刻模組",
                "process": "Etching",
                "pressure": f"{filter_pressure:.0f} Pa",
                "temp": "70°C",
                "rate": "4.0 nm/min",
                "status": filter_status,
                "x": 850,
                "info_top": -120
            }
        ]

        # 生成設備模組 HTML
        equipment_html = []
        info_cards_html = []

        for eq in equipment_modules:
            # 狀態顏色
            if eq["status"] == "critical":
                status_color = "#ef4444"
                glow = "0 0 20px #ef4444"
            elif eq["status"] == "warning":
                status_color = "#fbbf24"
                glow = "0 0 15px #fbbf24"
            else:
                status_color = "#4ade80"
                glow = "0 0 10px #4ade80"

            # 設備圖示（3D 立方體）
            equipment_html.append(f"""
                <g transform="translate({eq['x']}, 140)">
                    <!-- 設備 3D 立方體 -->
                    <rect x="0" y="20" width="120" height="140" fill="url(#equipmentGrad)"
                          stroke="{status_color}" stroke-width="3" rx="8"
                          filter="drop-shadow(0 10px 20px rgba(0,0,0,0.5))"
                          style="filter: drop-shadow({glow});"/>
                    <polygon points="0,20 20,0 140,0 120,20" fill="url(#topGrad)"
                             stroke="{status_color}" stroke-width="2"/>
                    <polygon points="120,20 140,0 140,140 120,160" fill="url(#sideGrad)"
                             stroke="{status_color}" stroke-width="2"/>

                    <!-- 狀態指示燈 -->
                    <circle cx="60" cy="50" r="8" fill="{status_color}"
                            style="animation: blink 1.5s infinite;">
                        <animate attributeName="opacity" values="1;0.3;1" dur="1.5s" repeatCount="indefinite"/>
                    </circle>

                    <!-- 設備 ID -->
                    <text x="60" y="100" text-anchor="middle"
                          style="fill: #e0f2ff; font-size: 18px; font-weight: bold; font-family: 'Courier New';">
                        {eq['id']}
                    </text>

                    <!-- 設備名稱 -->
                    <text x="60" y="180" text-anchor="middle"
                          style="fill: #94c5e8; font-size: 13px; font-weight: bold;">
                        {eq['name']}
                    </text>
                </g>
            """)

            # 資訊卡片（浮在設備上方或下方）
            params_html = []
            for key, value in eq.items():
                if key not in ["id", "name", "process", "status", "x", "info_top"]:
                    params_html.append(f"<div style='font-size: 11px; color: #94c5e8; margin-top: 3px;'>{key}: {value}</div>")

            info_cards_html.append(f"""
                <div style="position: absolute; left: {eq['x'] + 10}px; top: {eq['info_top']}px;
                           width: 150px; background: rgba(15, 30, 50, 0.95);
                           border: 2px solid {status_color}; border-radius: 8px;
                           padding: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.7),
                           {glow}; z-index: 10;">
                    <div style="color: #e0f2ff; font-size: 12px; font-weight: bold; margin-bottom: 3px;">
                        {eq['id']} - {eq['name']}
                    </div>
                    <div style="color: #60a5fa; font-size: 10px; margin-bottom: 8px;
                               padding-bottom: 6px; border-bottom: 1px solid #3a5f8c;">
                        {eq['process']}
                    </div>
                    {''.join(params_html)}
                </div>
            """)

        # 生成連接線（藍色數據流）
        connections_html = []
        for i in range(len(equipment_modules) - 1):
            x1 = equipment_modules[i]['x'] + 120
            x2 = equipment_modules[i + 1]['x']
            connections_html.append(f"""
                <line x1="{x1 + 30}" y1="230" x2="{x2 + 30}" y2="230"
                      stroke="#60a5fa" stroke-width="3" stroke-dasharray="8,4"
                      style="animation: flowLine 1s linear infinite;">
                    <animate attributeName="stroke-dashoffset" from="12" to="0" dur="1s" repeatCount="indefinite"/>
                </line>
                <polygon points="{x2 + 20},230 {x2 + 35},225 {x2 + 35},235" fill="#60a5fa"/>
            """)

        html = f"""
        <div style="background: rgba(15, 23, 42, 0.95); border-radius: 10px;
                   border: 2px solid #2d4a6e; padding: 20px; position: relative;
                   box-shadow: inset 0 0 30px rgba(0,0,0,0.7);">

            <!-- SVG 產線視圖 -->
            <svg width="100%" height="420" viewBox="0 0 1050 420" style="background: #0a0f1a; border-radius: 8px;">
                <defs>
                    <linearGradient id="equipmentGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#2d5a8c;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#1e3a5f;stop-opacity:1" />
                    </linearGradient>
                    <linearGradient id="topGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" style="stop-color:#3a6ba5;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#2d5a8c;stop-opacity:1" />
                    </linearGradient>
                    <linearGradient id="sideGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" style="stop-color:#1e3a5f;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#0f1f3a;stop-opacity:1" />
                    </linearGradient>
                </defs>

                <!-- 設備模組 -->
                {''.join(equipment_html)}

                <!-- 連接線（數據流） -->
                {''.join(connections_html)}
            </svg>

            <!-- 資訊卡片（浮在 SVG 上方） -->
            {''.join(info_cards_html)}
        </div>
        """

        return html
