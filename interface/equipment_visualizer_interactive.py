# -*- coding: utf-8 -*-
"""
互動式設備視覺化器（Interactive Equipment Visualizer）
- 總覽圖顯示整台設備，故障部位亮紅燈
- 點擊部件可切換到近距離特寫
- 顯示該部件的實際位置和長相
"""

from typing import Dict
import base64
from pathlib import Path


class InteractiveEquipmentVisualizer:
    """互動式設備視覺化生成器"""

    def __init__(self):
        """初始化視覺化器"""
        self.current_view = "overview"  # overview 或 部件名稱
        self.component_images = {}  # 儲存各部件的近距離照片

        # 載入設備總覽圖
        self.overview_image = self._load_image_as_base64("interface/images/asml_duv.png")

        # 載入各部件近距離照片（如果有的話）
        self._load_component_images()

    def generate_equipment_view(self, state: Dict, selected_component: str = None) -> str:
        """
        生成設備視覺化（總覽或特寫）

        Args:
            state: 設備狀態字典
            selected_component: 選中的部件（None = 總覽圖）

        Returns:
            HTML字串
        """

        # 計算各部件狀態
        component_status = {
            "light_source": self._get_light_status(state),
            "projection_lens": {"color": "#22c55e", "severity": "normal"},
            "vacuum_chamber": self._get_vacuum_status(state),
            "wafer_stage": {"color": "#22c55e", "severity": "normal"},
            "cooling_system": self._get_cooling_status(state),
            "alignment_system": {"color": "#10b981", "severity": "normal"},
            "air_filter": self._get_filter_status(state),
        }

        if selected_component and selected_component != "overview":
            # 顯示部件特寫
            return self._generate_component_detail(selected_component, state, component_status)
        else:
            # 顯示設備總覽
            return self._generate_overview(state, component_status)

    def _generate_overview(self, state: Dict, component_status: Dict) -> str:
        """生成設備總覽圖"""

        image_src = self.overview_image if self.overview_image else "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 600'%3E%3Crect width='1000' height='600' fill='%231e293b'/%3E%3C/svg%3E"

        html = f"""
        <div style="position: relative; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    padding: 15px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">

            <!-- 標題 -->
            <div style="text-align: center; margin-bottom: 10px;">
                <h2 style="color: #f1f5f9; margin: 0; font-size: 24px;">
                    光刻曝光機 - 設備總覽
                </h2>
                <p style="color: #94a3b8; margin: 5px 0; font-size: 13px;">
                    點擊部件查看近距離特寫 | ASML TWINSCAN NXT:1980Di
                </p>
            </div>

            <!-- 設備總覽圖 -->
            <div style="position: relative; width: 100%; height: 500px; background: #0f172a;
                        border-radius: 10px; overflow: hidden;">

                <!-- 背景設備圖 -->
                <img src="{image_src}"
                     style="width: 100%; height: 100%; object-fit: contain; opacity: 0.85;"
                     alt="ASML DUV Equipment">

                <!-- ==================== 可點擊的部件熱區 ==================== -->

                {self._generate_clickable_hotspot(
                    component="light_source",
                    x=420, y=70, width=160, height=50,
                    label="曝光光源",
                    value=f"{state.get('light_intensity', 100):.0f}%",
                    status=component_status["light_source"]
                )}

                {self._generate_clickable_hotspot(
                    component="projection_lens",
                    x=400, y=140, width=200, height=50,
                    label="投影鏡頭組",
                    value="4x 縮小系統",
                    status=component_status["projection_lens"]
                )}

                {self._generate_clickable_hotspot(
                    component="vacuum_chamber",
                    x=340, y=240, width=320, height=60,
                    label="真空腔體",
                    value=f"{state.get('vacuum_pressure', 1e-6):.2e} Torr",
                    status=component_status["vacuum_chamber"]
                )}

                {self._generate_clickable_hotspot(
                    component="wafer_stage",
                    x=380, y=360, width=240, height=50,
                    label="晶圓載台",
                    value="6 軸精密定位",
                    status=component_status["wafer_stage"]
                )}

                {self._generate_clickable_hotspot(
                    component="cooling_system",
                    x=720, y=200, width=160, height=80,
                    label="冷卻系統",
                    value=f"{state.get('cooling_flow', 5.0):.1f} L/min | {state.get('lens_temp', 23.0):.1f}°C",
                    status=component_status["cooling_system"]
                )}

                {self._generate_clickable_hotspot(
                    component="alignment_system",
                    x=120, y=220, width=140, height=60,
                    label="對準系統",
                    value="TTL 對準相機",
                    status=component_status["alignment_system"]
                )}

                {self._generate_clickable_hotspot(
                    component="air_filter",
                    x=140, y=390, width=140, height=50,
                    label="空氣過濾",
                    value="HEPA H14",
                    status=component_status["air_filter"]
                )}

                <!-- ==================== 故障警示標籤 ==================== -->
                {self._generate_fault_alerts(state, component_status)}

                <!-- 操作提示 -->
                <div style="position: absolute; bottom: 10px; left: 10px;
                            background: rgba(15, 23, 42, 0.9); padding: 8px 12px;
                            border-radius: 6px; font-size: 11px; color: #94a3b8;">
                    💡 點擊任一部件查看近距離特寫
                </div>

            </div>

            <!-- CSS 樣式 -->
            <style>
                .component-hotspot {{
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                .component-hotspot:hover {{
                    transform: scale(1.05);
                    z-index: 100;
                }}
                @keyframes pulse-danger {{
                    0%, 100% {{ opacity: 1; box-shadow: 0 0 20px var(--alert-color); }}
                    50% {{ opacity: 0.6; box-shadow: 0 0 35px var(--alert-color); }}
                }}
                .fault-blink {{
                    animation: pulse-danger 1.5s infinite;
                }}
            </style>
        </div>
        """

        return html

    def _generate_component_detail(self, component: str, state: Dict, component_status: Dict) -> str:
        """生成部件近距離特寫"""

        # 部件資訊
        component_info = {
            "light_source": {
                "name": "曝光光源系統",
                "full_name": "193nm ArF 準分子雷射光源",
                "description": "提供 193nm 波長的深紫外光，用於晶圓曝光",
                "key_params": [
                    f"光源強度：{state.get('light_intensity', 100):.1f}%",
                    "波長：193nm (ArF)",
                    "脈衝頻率：6 kHz",
                    "能量穩定度：±0.5%"
                ],
                "common_issues": [
                    "光源強度衰減（燈管老化）",
                    "能量不穩定（電源問題）",
                    "光學元件污染"
                ]
            },
            "projection_lens": {
                "name": "投影鏡頭組",
                "full_name": "4倍縮小投影光學系統",
                "description": "將光罩圖案以 1:4 比例投影到晶圓上",
                "key_params": [
                    "縮小倍率：4x",
                    "數值孔徑 (NA)：1.35",
                    "鏡片數量：40+ 片",
                    "材質：石英玻璃"
                ],
                "common_issues": [
                    "鏡片污染（影響成像品質）",
                    "光學偏移（對準精度下降）",
                    "溫度漂移"
                ]
            },
            "vacuum_chamber": {
                "name": "真空腔體",
                "full_name": "晶圓曝光真空環境控制系統",
                "description": "提供高真空環境，防止雜質污染晶圓",
                "key_params": [
                    f"真空度：{state.get('vacuum_pressure', 1e-6):.2e} Torr",
                    "目標真空度：< 1e-6 Torr",
                    "抽氣速率：2000 L/s",
                    "洩漏率：< 1e-8 Torr·L/s"
                ],
                "common_issues": [
                    "真空洩漏（O環老化）",
                    "真空泵效能下降",
                    "密封圈磨損"
                ]
            },
            "wafer_stage": {
                "name": "晶圓載台",
                "full_name": "高精度 6 軸晶圓定位系統",
                "description": "精確控制晶圓位置，實現奈米級對準",
                "key_params": [
                    "定位精度：< 2 nm",
                    "移動範圍：X/Y ±150 mm",
                    "旋轉精度：< 0.1 µrad",
                    "加速度：20 m/s²"
                ],
                "common_issues": [
                    "軸承磨損（定位精度下降）",
                    "馬達過熱",
                    "感測器漂移"
                ]
            },
            "cooling_system": {
                "name": "冷卻水系統",
                "full_name": "精密溫控冷卻循環系統",
                "description": "維持光學元件溫度穩定，確保成像品質",
                "key_params": [
                    f"流量：{state.get('cooling_flow', 5.0):.1f} L/min",
                    f"鏡頭溫度：{state.get('lens_temp', 23.0):.1f}°C",
                    "目標溫度：23.0 ± 0.1°C",
                    "冷卻能力：15 kW"
                ],
                "common_issues": [
                    "流量不足（過濾網堵塞）",
                    "溫度過高（冷卻能力下降）",
                    "管路洩漏"
                ]
            },
            "alignment_system": {
                "name": "對準系統",
                "full_name": "TTL 穿透式對準相機系統",
                "description": "偵測對準標記，確保層間對準精度",
                "key_params": [
                    "對準精度：< 2 nm (3σ)",
                    "對準速度：< 0.5 秒/點",
                    "相機數量：4 組",
                    "波長：633 nm (He-Ne)"
                ],
                "common_issues": [
                    "相機污染（對準失敗）",
                    "雷射功率衰減",
                    "光學偏移"
                ]
            },
            "air_filter": {
                "name": "空氣過濾系統",
                "full_name": "HEPA H14 級潔淨空氣過濾",
                "description": "提供 Class 1 潔淨度，防止粒子污染",
                "key_params": [
                    "過濾等級：HEPA H14",
                    "過濾效率：> 99.995%",
                    "風速：0.45 m/s",
                    "更換週期：6 個月"
                ],
                "common_issues": [
                    "過濾網堵塞（風量下降）",
                    "過濾效率下降",
                    "壓差過高"
                ]
            }
        }

        info = component_info.get(component, {})
        status = component_status.get(component, {"color": "#22c55e", "severity": "normal"})

        # 嘗試載入部件特寫照片
        detail_image = self.component_images.get(component)
        if not detail_image:
            # 如果沒有特寫照片，生成示意圖
            detail_image = self._generate_component_diagram(component, status)

        html = f"""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    padding: 15px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">

            <!-- 返回按鈕 -->
            <div style="margin-bottom: 10px;">
                <button onclick="window.top.postMessage({{type: 'component_click', component: 'overview'}}, '*');"
                        style="background: #475569; color: #f1f5f9; border: 2px solid #64748b;
                               padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px;
                               font-weight: bold; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"
                        onmouseover="this.style.background='#5b6d83'; this.style.transform='scale(1.05)';"
                        onmouseout="this.style.background='#475569'; this.style.transform='scale(1)';">
                    ← 返回設備總覽
                </button>
            </div>

            <!-- 部件標題 -->
            <div style="text-align: center; margin-bottom: 15px;">
                <h2 style="color: #f1f5f9; margin: 0; font-size: 24px;">
                    {info.get('name', component)}
                </h2>
                <p style="color: #94a3b8; margin: 5px 0; font-size: 14px;">
                    {info.get('full_name', '')}
                </p>
            </div>

            <!-- 部件特寫照片區域 -->
            <div style="position: relative; width: 100%; height: 400px; background: #0f172a;
                        border-radius: 10px; overflow: hidden; margin-bottom: 15px;
                        border: 3px solid {status['color']};">

                <img src="{detail_image}"
                     style="width: 100%; height: 100%; object-fit: contain; opacity: 0.9;"
                     alt="{info.get('name', '')}">

                <!-- 狀態指示燈 -->
                <div style="position: absolute; top: 15px; right: 15px;
                            background: rgba(15, 23, 42, 0.9); padding: 10px 15px;
                            border-radius: 8px; border: 2px solid {status['color']};">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 20px; height: 20px; border-radius: 50%;
                                    background: {status['color']};
                                    box-shadow: 0 0 15px {status['color']};
                                    {'animation: pulse-danger 1.5s infinite;' if status['severity'] != 'normal' else ''}">
                        </div>
                        <span style="color: {status['color']}; font-weight: bold; font-size: 14px;">
                            {'正常' if status['severity'] == 'normal' else ('警告' if status['severity'] == 'warning' else '異常')}
                        </span>
                    </div>
                </div>
            </div>

            <!-- 部件詳細資訊 -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">

                <!-- 左欄：功能說明和參數 -->
                <div>
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                        <h3 style="color: #f1f5f9; margin: 0 0 10px 0; font-size: 16px;">功能說明</h3>
                        <p style="color: #cbd5e1; margin: 0; font-size: 13px; line-height: 1.6;">
                            {info.get('description', '')}
                        </p>
                    </div>

                    <div style="background: rgba(30, 41, 59, 0.7); padding: 15px; border-radius: 8px;">
                        <h3 style="color: #f1f5f9; margin: 0 0 10px 0; font-size: 16px;">關鍵參數</h3>
                        <ul style="color: #cbd5e1; margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.8;">
                            {''.join([f'<li>{param}</li>' for param in info.get('key_params', [])])}
                        </ul>
                    </div>
                </div>

                <!-- 右欄：常見問題 -->
                <div>
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 15px; border-radius: 8px;">
                        <h3 style="color: #f1f5f9; margin: 0 0 10px 0; font-size: 16px;">常見問題</h3>
                        <ul style="color: #fbbf24; margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.8;">
                            {''.join([f'<li>{issue}</li>' for issue in info.get('common_issues', [])])}
                        </ul>
                    </div>

                    <!-- 當前狀態詳情 -->
                    {self._generate_component_status_detail(component, state, status)}
                </div>

            </div>

            <style>
                @keyframes pulse-danger {{
                    0%, 100% {{ opacity: 1; box-shadow: 0 0 15px {status['color']}; }}
                    50% {{ opacity: 0.6; box-shadow: 0 0 30px {status['color']}; }}
                }}
            </style>
        </div>
        """

        return html

    def _generate_clickable_hotspot(self, component: str, x: int, y: int,
                                    width: int, height: int, label: str,
                                    value: str, status: Dict) -> str:
        """生成可點擊的部件熱區"""

        color = status["color"]
        severity = status["severity"]

        # 異常部件會閃爍
        blink_class = "fault-blink" if severity != "normal" else ""

        return f"""
        <div class="component-hotspot {blink_class}"
             onclick="window.top.postMessage({{type: 'component_click', component: '{component}'}}, '*');"
             style="position: absolute; left: {x}px; top: {y}px; width: {width}px; height: {height}px;
                    background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(10px);
                    border: 3px solid {color}; border-radius: 12px; padding: 10px;
                    box-shadow: 0 6px 20px rgba(0,0,0,0.5); --alert-color: {color}; cursor: pointer;
                    transition: all 0.3s ease; z-index: 10;"
             onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 8px 30px rgba(0,0,0,0.7)';"
             onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 6px 20px rgba(0,0,0,0.5)';">
            <div style="color: {color}; font-size: 12px; font-weight: bold; margin-bottom: 4px; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">
                {label}
            </div>
            <div style="color: #cbd5e1; font-size: 11px; line-height: 1.4;">
                {value}
            </div>
            <div style="color: #94a3b8; font-size: 10px; margin-top: 4px;">
                ▶ 點擊查看詳情
            </div>
        </div>
        """

    def _generate_component_diagram(self, component: str, status: Dict) -> str:
        """生成部件示意圖（當沒有實際照片時）"""

        color = status["color"]

        # 簡單的 SVG 示意圖
        diagrams = {
            "light_source": f"""data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'%3E%3Crect width='400' height='300' fill='%231e293b'/%3E%3Crect x='100' y='80' width='200' height='80' fill='%232c2c2c' stroke='{color.replace('#', '%23')}' stroke-width='3' rx='10'/%3E%3Crect x='120' y='100' width='160' height='40' fill='{color.replace('#', '%23')}' opacity='0.7' rx='5'/%3E%3Ctext x='200' y='190' text-anchor='middle' font-size='16' fill='%23cbd5e1'%3E193nm ArF 光源%3C/text%3E%3Ctext x='200' y='220' text-anchor='middle' font-size='12' fill='%2394a3b8'%3E準分子雷射系統%3C/text%3E%3C/svg%3E""",

            "projection_lens": f"""data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'%3E%3Crect width='400' height='300' fill='%231e293b'/%3E%3Cellipse cx='200' cy='150' rx='80' ry='40' fill='%234a5568' stroke='{color.replace('#', '%23')}' stroke-width='3'/%3E%3Cellipse cx='200' cy='145' rx='65' ry='32' fill='%23667eea' opacity='0.3'/%3E%3Ctext x='200' y='220' text-anchor='middle' font-size='16' fill='%23cbd5e1'%3E投影鏡頭組%3C/text%3E%3Ctext x='200' y='245' text-anchor='middle' font-size='12' fill='%2394a3b8'%3E40+ 片石英鏡片%3C/text%3E%3C/svg%3E""",

            "vacuum_chamber": f"""data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'%3E%3Crect width='400' height='300' fill='%231e293b'/%3E%3Crect x='80' y='80' width='240' height='140' fill='%23334155' stroke='{color.replace('#', '%23')}' stroke-width='3' rx='15'/%3E%3Crect x='100' y='100' width='200' height='100' fill='%230ea5e9' opacity='0.3' rx='10'/%3E%3Ctext x='200' y='250' text-anchor='middle' font-size='16' fill='%23cbd5e1'%3E真空腔體%3C/text%3E%3Ctext x='200' y='275' text-anchor='middle' font-size='12' fill='%2394a3b8'%3E高真空環境控制%3C/text%3E%3C/svg%3E""",

            "cooling_system": f"""data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'%3E%3Crect width='400' height='300' fill='%231e293b'/%3E%3Crect x='120' y='70' width='160' height='160' fill='%232c2c2c' stroke='{color.replace('#', '%23')}' stroke-width='3' rx='10'/%3E%3Cpath d='M 150,120 L 250,120' stroke='%230ea5e9' stroke-width='12' opacity='0.7'/%3E%3Cpath d='M 150,150 L 250,150' stroke='%230ea5e9' stroke-width='12' opacity='0.7'/%3E%3Cpath d='M 150,180 L 250,180' stroke='%230ea5e9' stroke-width='12' opacity='0.7'/%3E%3Ctext x='200' y='255' text-anchor='middle' font-size='16' fill='%23cbd5e1'%3E冷卻水系統%3C/text%3E%3Ctext x='200' y='280' text-anchor='middle' font-size='12' fill='%2394a3b8'%3E精密溫控循環%3C/text%3E%3C/svg%3E""",
        }

        return diagrams.get(component, diagrams["light_source"])

    def _generate_component_status_detail(self, component: str, state: Dict, status: Dict) -> str:
        """生成部件當前狀態詳情"""

        if status["severity"] == "normal":
            return f"""
            <div style="background: rgba(34, 197, 94, 0.1); padding: 15px; border-radius: 8px; margin-top: 15px;
                        border: 1px solid #22c55e;">
                <h3 style="color: #22c55e; margin: 0 0 10px 0; font-size: 16px;">✓ 當前狀態：正常</h3>
                <p style="color: #cbd5e1; margin: 0; font-size: 13px;">
                    所有參數在正常範圍內，設備運作良好。
                </p>
            </div>
            """
        else:
            # 根據不同部件生成具體的異常資訊
            alerts = {
                "cooling_system": f"""
                <div style="background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px; margin-top: 15px;
                            border: 1px solid #ef4444;">
                    <h3 style="color: #ef4444; margin: 0 0 10px 0; font-size: 16px;">⚠ 當前狀態：異常</h3>
                    <ul style="color: #fca5a5; margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.8;">
                        <li>冷卻流量：{state.get('cooling_flow', 5.0):.1f} L/min（過低）</li>
                        <li>鏡頭溫度：{state.get('lens_temp', 23.0):.1f}°C（過高）</li>
                        <li>建議動作：檢查過濾網、管路接頭</li>
                    </ul>
                </div>
                """,
                "vacuum_chamber": f"""
                <div style="background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px; margin-top: 15px;
                            border: 1px solid #ef4444;">
                    <h3 style="color: #ef4444; margin: 0 0 10px 0; font-size: 16px;">⚠ 當前狀態：異常</h3>
                    <ul style="color: #fca5a5; margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.8;">
                        <li>真空度：{state.get('vacuum_pressure', 1e-6):.2e} Torr（洩漏）</li>
                        <li>洩漏位置：可能為 O 環密封處</li>
                        <li>建議動作：更換密封圈、檢查管路</li>
                    </ul>
                </div>
                """
            }

            return alerts.get(component, f"""
            <div style="background: rgba(245, 158, 11, 0.1); padding: 15px; border-radius: 8px; margin-top: 15px;
                        border: 1px solid #f59e0b;">
                <h3 style="color: #f59e0b; margin: 0 0 10px 0; font-size: 16px;">⚠ 當前狀態：警告</h3>
                <p style="color: #fde68a; margin: 0; font-size: 13px;">
                    部分參數偏離正常值，建議進行檢查。
                </p>
            </div>
            """)

    def _generate_fault_alerts(self, state: Dict, component_status: Dict) -> str:
        """生成故障警示標籤"""
        alerts = []

        # 只在總覽圖顯示最嚴重的警示
        for component, status in component_status.items():
            if status["severity"] == "danger":
                if component == "cooling_system":
                    alerts.append(f"""
                    <div style="position: absolute; left: 720px; top: 290px;
                                background: rgba(239, 68, 68, 0.95); color: white;
                                padding: 8px 12px; border-radius: 6px; font-size: 12px;
                                font-weight: bold; border: 2px solid #fca5a5;
                                box-shadow: 0 4px 15px rgba(239, 68, 68, 0.6);
                                animation: pulse-danger 1.5s infinite;">
                        🔥 冷卻異常
                    </div>
                    """)
                elif component == "vacuum_chamber":
                    alerts.append(f"""
                    <div style="position: absolute; left: 480px; top: 305px;
                                background: rgba(239, 68, 68, 0.95); color: white;
                                padding: 8px 12px; border-radius: 6px; font-size: 12px;
                                font-weight: bold; border: 2px solid #fca5a5;
                                box-shadow: 0 4px 15px rgba(239, 68, 68, 0.6);
                                animation: pulse-danger 1.5s infinite;">
                        ⚡ 真空洩漏
                    </div>
                    """)

        return "\n".join(alerts)

    # ==================== 狀態判斷方法 ====================

    def _get_cooling_status(self, state: Dict) -> Dict:
        flow_rate = state.get("cooling_flow", 5.0)
        if flow_rate < 4.0:
            return {"color": "#ef4444", "severity": "danger"}
        elif flow_rate < 4.5:
            return {"color": "#f59e0b", "severity": "warning"}
        else:
            return {"color": "#22c55e", "severity": "normal"}

    def _get_vacuum_status(self, state: Dict) -> Dict:
        vacuum_leak = state.get("vacuum_leak", False)
        pressure = state.get("vacuum_pressure", 1e-6)
        if vacuum_leak or pressure > 1e-5:
            return {"color": "#ef4444", "severity": "danger"}
        else:
            return {"color": "#22c55e", "severity": "normal"}

    def _get_temp_status(self, state: Dict) -> Dict:
        temp = state.get("lens_temp", 23.0)
        if temp > 26:
            return {"color": "#ef4444", "severity": "danger"}
        elif temp > 25:
            return {"color": "#f59e0b", "severity": "warning"}
        else:
            return {"color": "#22c55e", "severity": "normal"}

    def _get_filter_status(self, state: Dict) -> Dict:
        clogged = state.get("filter_clogged", False)
        if clogged:
            return {"color": "#f59e0b", "severity": "warning"}
        else:
            return {"color": "#64748b", "severity": "normal"}

    def _get_light_status(self, state: Dict) -> Dict:
        intensity = state.get("light_intensity", 100)
        if intensity < 90:
            return {"color": "#f59e0b", "severity": "warning"}
        else:
            return {"color": "#8b5cf6", "severity": "normal"}

    def _load_image_as_base64(self, image_path: str) -> str:
        """載入圖片並轉換為 base64"""
        try:
            if Path(image_path).is_absolute():
                image_file = Path(image_path)
            else:
                base_dir = Path(__file__).parent.parent
                image_file = base_dir / image_path

            if not image_file.exists():
                return None

            with open(image_file, 'rb') as f:
                image_data = f.read()
                image_base64_str = base64.b64encode(image_data).decode('utf-8')

                if image_file.suffix.lower() == '.png':
                    mime_type = 'image/png'
                elif image_file.suffix.lower() in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                else:
                    mime_type = 'image/png'

                return f"data:{mime_type};base64,{image_base64_str}"
        except Exception as e:
            print(f"[Error] 載入圖片失敗：{e}")
            return None

    def _load_component_images(self):
        """載入各部件的近距離特寫照片（如果有的話）"""
        base_dir = Path(__file__).parent.parent / "interface" / "images" / "components"

        if not base_dir.exists():
            return

        components = ["light_source", "projection_lens", "vacuum_chamber",
                     "wafer_stage", "cooling_system", "alignment_system", "air_filter"]

        for component in components:
            for ext in ['.png', '.jpg', '.jpeg']:
                image_file = base_dir / f"{component}{ext}"
                if image_file.exists():
                    self.component_images[component] = self._load_image_as_base64(str(image_file))
                    print(f"[OK] 載入部件照片：{component}{ext}")
                    break
