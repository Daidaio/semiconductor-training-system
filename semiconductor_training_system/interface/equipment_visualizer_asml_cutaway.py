# -*- coding: utf-8 -*-
"""
ASML 官方剖面圖設備視覺化器
- 使用 ASML TWINSCAN NXT:870 官方剖面圖
- 採用資訊面板 + 箭頭指向設備的設計
- 異常時該區域面板亮紅燈閃爍
"""

from typing import Dict
import base64
from pathlib import Path


class ASMLCutawayVisualizer:
    """ASML 剖面圖視覺化生成器"""

    def __init__(self):
        """初始化視覺化器"""
        # 載入 ASML 官方剖面圖
        self.equipment_image = self._load_image_as_base64("interface/images/asml_cutaway.png")

        # 定義各元件的資訊面板位置和指向的設備位置
        # panel_x, panel_y: 資訊面板的位置（百分比）
        # target_x, target_y: 箭頭指向的設備位置（百分比）
        # 根據 ASML TWINSCAN NXT:870 剖面圖重新標示
        self.component_regions = {
            # 控制系統（光罩載台左邊的螢幕）
            "control_panel": {
                "name": "控制系統",
                "name_en": "Control Panel",
                "panel_x": 2,
                "panel_y": 5,
                "target_x": 12,     # 指向光罩載台左邊的螢幕
                "target_y": 48,     # 往下一點
                "description": "TWINSCAN 控制台",
            },

            # 對準系統（中間粉紅柱中間位置）
            "alignment_system": {
                "name": "對準系統",
                "name_en": "Alignment",
                "panel_x": 2,
                "panel_y": 30,
                "target_x": 50,     # 指向中間粉紅柱中間
                "target_y": 48,
                "description": "ATHENA 對位感測器",
            },

            # 晶圓傳送（左下角 - 銅色圓形機械手臂）
            "wafer_handler": {
                "name": "晶圓傳送",
                "name_en": "Wafer Handler",
                "panel_x": 2,
                "panel_y": 85,      # 框框往下移，不擋到本體
                "target_x": 18,     # 箭頭往左一點
                "target_y": 78,
                "description": "傳送機械手臂",
            },

            # 光罩載台（左上方紅色結構 - 控制螢幕右邊）
            "reticle_stage": {
                "name": "光罩載台",
                "name_en": "Reticle Stage",
                "panel_x": 30,
                "panel_y": 2,
                "target_x": 28,     # 指向控制螢幕右邊的紅色結構
                "target_y": 48,
                "description": "光罩定位系統",
            },

            # 曝光光源（中間粉紅柱中間偏上）
            "light_source": {
                "name": "曝光光源",
                "name_en": "Light Source",
                "panel_x": 55,      # 移到上方中間
                "panel_y": 2,
                "target_x": 50,
                "target_y": 38,
                "description": "248nm KrF 雷射",
            },

            # 投影光學系統（中間粉紅柱中間）
            "lens_system": {
                "name": "投影光學系統",
                "name_en": "Projection Optics",
                "panel_x": 78,      # 往右上移，避免重疊
                "panel_y": 5,
                "target_x": 50,
                "target_y": 50,
                "description": "ZEISS 4x 縮小鏡組",
            },

            # 冷卻系統（右側 - 粉紅色管路）
            "cooling_system": {
                "name": "冷卻系統",
                "name_en": "Cooling System",
                "panel_x": 70,      # 右側中間
                "panel_y": 38,
                "target_x": 75,
                "target_y": 45,
                "description": "溫度控制迴路",
            },

            # 晶圓載台（中間粉紅柱最下面）
            "wafer_stage": {
                "name": "晶圓載台",
                "name_en": "Wafer Stage",
                "panel_x": 70,      # 右側下方
                "panel_y": 62,
                "target_x": 50,
                "target_y": 72,
                "description": "雙載台系統",
            },
        }

    def generate_equipment_view(self, state: Dict, selected_component: str = None) -> str:
        """生成設備視覺化"""

        # 計算各部件狀態
        component_status = self._calculate_all_status(state)

        # 設備圖片來源
        if self.equipment_image:
            image_src = self.equipment_image
        else:
            image_src = self._generate_placeholder_svg()

        # 生成資訊面板和箭頭
        info_panels = self._generate_info_panels(component_status, state)

        # 生成右側狀態總覽
        status_panel = self._generate_status_panel(component_status, state)

        html = f"""
        <div style="position: relative; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    padding: 20px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.6);">

            <!-- 標題 -->
            <div style="text-align: center; margin-bottom: 15px;">
                <h2 style="color: #f1f5f9; margin: 0; font-size: 24px; font-weight: bold;">
                    ASML TWINSCAN NXT:870 DUV 光刻曝光機
                </h2>
                <p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 13px;">
                    KrF 深紫外光微影系統 | 即時設備狀態監控
                </p>
            </div>

            <!-- 主要內容區 -->
            <div style="display: flex; gap: 20px;">

                <!-- 設備圖 + 資訊面板區域 -->
                <div style="position: relative; flex: 1; min-height: 550px; background: #0a0f1a;
                            border-radius: 12px; overflow: hidden;">

                    <!-- 設備圖片 -->
                    <img src="{image_src}"
                         style="width: 100%; height: 100%; object-fit: contain; display: block;"
                         alt="ASML DUV Equipment">

                    <!-- 資訊面板覆蓋層 -->
                    {info_panels}

                </div>

                <!-- 右側狀態面板 -->
                {status_panel}

            </div>

            <!-- 圖例 -->
            <div style="margin-top: 15px; padding: 12px; background: rgba(15, 23, 42, 0.6);
                        border-radius: 8px; display: flex; justify-content: center; gap: 30px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 16px; height: 16px; background: #22c55e; border-radius: 50%;
                                box-shadow: 0 0 10px #22c55e;"></div>
                    <span style="color: #cbd5e1; font-size: 13px;">正常運作</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 16px; height: 16px; background: #f59e0b; border-radius: 50%;
                                box-shadow: 0 0 10px #f59e0b;"></div>
                    <span style="color: #cbd5e1; font-size: 13px;">警告</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 16px; height: 16px; background: #ef4444; border-radius: 50%;
                                box-shadow: 0 0 10px #ef4444; animation: pulse 1.5s infinite;"></div>
                    <span style="color: #cbd5e1; font-size: 13px;">異常（閃爍）</span>
                </div>
            </div>

            <style>
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; transform: scale(1); }}
                    50% {{ opacity: 0.5; transform: scale(1.1); }}
                }}
                @keyframes glow-red {{
                    0%, 100% {{ box-shadow: 0 0 10px #ef4444, 0 0 20px #ef4444; }}
                    50% {{ box-shadow: 0 0 20px #ef4444, 0 0 40px #ef4444; }}
                }}
                @keyframes glow-yellow {{
                    0%, 100% {{ box-shadow: 0 0 8px #f59e0b; }}
                    50% {{ box-shadow: 0 0 15px #f59e0b; }}
                }}
            </style>
        </div>
        """

        return html

    def _generate_info_panels(self, component_status: Dict, state: Dict) -> str:
        """生成資訊面板和連接線"""

        panels = []

        for comp_id, region in self.component_regions.items():
            status = component_status.get(comp_id, {"severity": "normal", "message": "正常"})
            severity = status["severity"]

            # 決定顏色和動畫
            if severity == "critical":
                border_color = "#ef4444"
                bg_color = "rgba(239, 68, 68, 0.15)"
                text_color = "#ef4444"
                animation = "animation: glow-red 1.5s infinite;"
                status_icon = "🔴"
            elif severity == "warning":
                border_color = "#f59e0b"
                bg_color = "rgba(245, 158, 11, 0.15)"
                text_color = "#f59e0b"
                animation = "animation: glow-yellow 2s infinite;"
                status_icon = "🟡"
            else:
                border_color = "#22c55e"
                bg_color = "rgba(34, 197, 94, 0.1)"
                text_color = "#22c55e"
                animation = ""
                status_icon = "🟢"

            # 取得即時數值
            value_display = self._get_component_value(comp_id, state, status)

            # 資訊面板
            panel = f"""
            <!-- {region['name']} 資訊面板 -->
            <div style="position: absolute; left: {region['panel_x']}%; top: {region['panel_y']}%;
                        background: rgba(10, 15, 30, 0.95); backdrop-filter: blur(10px);
                        border: 2px solid {border_color}; border-radius: 8px;
                        padding: 8px 12px; min-width: 120px; z-index: 10;
                        {animation}">

                <!-- 標題列 -->
                <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
                    <span style="font-size: 10px;">{status_icon}</span>
                    <span style="color: #f1f5f9; font-size: 11px; font-weight: bold;">{region['name']}</span>
                </div>

                <!-- 數值顯示 -->
                <div style="color: {text_color}; font-size: 13px; font-weight: bold;">
                    {value_display}
                </div>

                <!-- 狀態訊息 -->
                <div style="color: #94a3b8; font-size: 9px; margin-top: 2px;">
                    {status.get('message', '正常')}
                </div>
            </div>

            <!-- 連接點（在設備上的標記點）-->
            <div style="position: absolute; left: {region['target_x']}%; top: {region['target_y']}%;
                        width: 12px; height: 12px; background: {border_color};
                        border-radius: 50%; border: 2px solid white;
                        transform: translate(-50%, -50%); z-index: 5;
                        box-shadow: 0 0 10px {border_color};
                        {'animation: pulse 1s infinite;' if severity != 'normal' else ''}">
            </div>

            <!-- SVG 連接線 -->
            <svg style="position: absolute; left: 0; top: 0; width: 100%; height: 100%;
                        pointer-events: none; z-index: 3;">
                <defs>
                    <marker id="arrowhead-{comp_id}" markerWidth="10" markerHeight="7"
                            refX="9" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="{border_color}" />
                    </marker>
                </defs>
                <line x1="{region['panel_x'] + 5}%" y1="{region['panel_y'] + 4}%"
                      x2="{region['target_x']}%" y2="{region['target_y']}%"
                      stroke="{border_color}" stroke-width="2" stroke-dasharray="5,3"
                      marker-end="url(#arrowhead-{comp_id})" opacity="0.8"/>
            </svg>
            """
            panels.append(panel)

        return "\n".join(panels)

    def _get_component_value(self, comp_id: str, state: Dict, status: Dict) -> str:
        """取得元件的即時數值顯示"""

        if comp_id == "lens_system":
            temp = state.get("lens_temp", 23.0)
            return f"{temp:.1f}°C"
        elif comp_id == "cooling_system":
            flow = state.get("cooling_flow", 5.0)
            return f"{flow:.1f} L/min"
        elif comp_id == "light_source":
            intensity = state.get("light_intensity", 100)
            return f"{intensity:.0f}%"
        elif comp_id == "wafer_stage":
            return "6軸定位"
        elif comp_id == "reticle_stage":
            return "光罩就位"
        elif comp_id == "alignment_system":
            return "12色模式"
        elif comp_id == "control_panel":
            return "運作中"
        elif comp_id == "wafer_handler":
            return "待機中"
        else:
            return status.get('message', '正常')

    def _generate_status_panel(self, component_status: Dict, state: Dict) -> str:
        """生成右側狀態面板"""

        # 計算異常數量
        critical_count = sum(1 for s in component_status.values() if s["severity"] == "critical")
        warning_count = sum(1 for s in component_status.values() if s["severity"] == "warning")

        # 整體狀態
        if critical_count > 0:
            overall_status = "異常"
            overall_color = "#ef4444"
            overall_bg = "rgba(239, 68, 68, 0.15)"
        elif warning_count > 0:
            overall_status = "警告"
            overall_color = "#f59e0b"
            overall_bg = "rgba(245, 158, 11, 0.15)"
        else:
            overall_status = "正常"
            overall_color = "#22c55e"
            overall_bg = "rgba(34, 197, 94, 0.15)"

        # 生成元件狀態列表
        status_items = []
        for comp_id, region in self.component_regions.items():
            status = component_status.get(comp_id, {"severity": "normal"})
            severity = status["severity"]

            if severity == "critical":
                color = "#ef4444"
                icon = "🔴"
                bg = "rgba(239, 68, 68, 0.1)"
            elif severity == "warning":
                color = "#f59e0b"
                icon = "🟡"
                bg = "rgba(245, 158, 11, 0.1)"
            else:
                color = "#22c55e"
                icon = "🟢"
                bg = "transparent"

            status_items.append(f"""
            <div style="display: flex; align-items: center; gap: 10px; padding: 8px 12px;
                        background: {bg}; border-radius: 6px; margin-bottom: 6px;">
                <span style="font-size: 12px;">{icon}</span>
                <div style="flex: 1;">
                    <div style="color: #f1f5f9; font-size: 12px; font-weight: 500;">{region['name']}</div>
                    <div style="color: #94a3b8; font-size: 10px;">{region['name_en']}</div>
                </div>
                <div style="color: {color}; font-size: 11px; font-weight: bold;">
                    {status.get('message', '正常')}
                </div>
            </div>
            """)

        panel = f"""
        <div style="width: 260px; background: rgba(15, 23, 42, 0.8); border-radius: 12px;
                    padding: 15px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1);">

            <!-- 整體狀態 -->
            <div style="text-align: center; padding: 15px; background: {overall_bg};
                        border-radius: 10px; margin-bottom: 15px; border: 2px solid {overall_color};">
                <div style="color: #94a3b8; font-size: 12px; margin-bottom: 5px;">設備狀態</div>
                <div style="color: {overall_color}; font-size: 28px; font-weight: bold;">{overall_status}</div>
                <div style="color: #64748b; font-size: 11px; margin-top: 5px;">
                    {f"🔴 {critical_count} 個異常" if critical_count > 0 else ""}
                    {f"🟡 {warning_count} 個警告" if warning_count > 0 else ""}
                    {"✓ 所有系統正常" if critical_count == 0 and warning_count == 0 else ""}
                </div>
            </div>

            <!-- 元件狀態列表 -->
            <div style="color: #94a3b8; font-size: 11px; margin-bottom: 10px; padding-left: 5px;">
                元件狀態監控
            </div>
            <div style="max-height: 280px; overflow-y: auto;">
                {''.join(status_items)}
            </div>

            <!-- 即時數據 -->
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #94a3b8; font-size: 11px; margin-bottom: 10px;">即時監控數據</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                        <div style="color: #64748b; font-size: 9px;">冷卻流量</div>
                        <div style="color: #f1f5f9; font-size: 14px; font-weight: bold;">
                            {state.get('cooling_flow', 5.0):.1f} <span style="font-size: 10px; color: #94a3b8;">L/min</span>
                        </div>
                    </div>
                    <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                        <div style="color: #64748b; font-size: 9px;">鏡組溫度</div>
                        <div style="color: #f1f5f9; font-size: 14px; font-weight: bold;">
                            {state.get('lens_temp', 23.0):.1f} <span style="font-size: 10px; color: #94a3b8;">°C</span>
                        </div>
                    </div>
                    <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                        <div style="color: #64748b; font-size: 9px;">真空壓力</div>
                        <div style="color: #f1f5f9; font-size: 14px; font-weight: bold;">
                            {state.get('vacuum_pressure', 1e-6):.0e} <span style="font-size: 10px; color: #94a3b8;">Torr</span>
                        </div>
                    </div>
                    <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                        <div style="color: #64748b; font-size: 9px;">光源強度</div>
                        <div style="color: #f1f5f9; font-size: 14px; font-weight: bold;">
                            {state.get('light_intensity', 100):.0f} <span style="font-size: 10px; color: #94a3b8;">%</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

        return panel

    def _calculate_all_status(self, state: Dict) -> Dict:
        """計算所有元件的狀態"""

        status = {}

        # 投影光學系統 - 受溫度影響
        lens_temp = state.get("lens_temp", 23.0)
        if lens_temp > 26:
            status["lens_system"] = {"severity": "critical", "message": f"溫度過高 {lens_temp:.1f}°C"}
        elif lens_temp > 24:
            status["lens_system"] = {"severity": "warning", "message": f"溫度偏高 {lens_temp:.1f}°C"}
        else:
            status["lens_system"] = {"severity": "normal", "message": "正常"}

        # 晶圓載台
        if state.get("stage_error", False):
            status["wafer_stage"] = {"severity": "critical", "message": "定位異常"}
        else:
            status["wafer_stage"] = {"severity": "normal", "message": "正常"}

        # 光罩載台
        if state.get("reticle_error", False):
            status["reticle_stage"] = {"severity": "warning", "message": "對位偏移"}
        else:
            status["reticle_stage"] = {"severity": "normal", "message": "正常"}

        # 冷卻系統
        cooling_flow = state.get("cooling_flow", 5.0)
        if cooling_flow < 4.0:
            status["cooling_system"] = {"severity": "critical", "message": f"流量過低 {cooling_flow:.1f}L/min"}
        elif cooling_flow < 4.5:
            status["cooling_system"] = {"severity": "warning", "message": f"流量偏低 {cooling_flow:.1f}L/min"}
        else:
            status["cooling_system"] = {"severity": "normal", "message": "正常"}

        # 對準系統
        if state.get("alignment_error", False):
            status["alignment_system"] = {"severity": "warning", "message": "校準需要"}
        else:
            status["alignment_system"] = {"severity": "normal", "message": "正常"}

        # 曝光光源
        light_intensity = state.get("light_intensity", 100)
        if light_intensity < 85:
            status["light_source"] = {"severity": "critical", "message": f"強度不足 {light_intensity:.0f}%"}
        elif light_intensity < 92:
            status["light_source"] = {"severity": "warning", "message": f"強度偏低 {light_intensity:.0f}%"}
        else:
            status["light_source"] = {"severity": "normal", "message": "正常"}

        # 控制面板
        status["control_panel"] = {"severity": "normal", "message": "正常"}

        # 晶圓傳送
        if state.get("handler_error", False):
            status["wafer_handler"] = {"severity": "critical", "message": "傳送異常"}
        else:
            status["wafer_handler"] = {"severity": "normal", "message": "正常"}

        return status

    def _generate_placeholder_svg(self) -> str:
        """生成佔位圖"""
        return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 600'%3E%3Crect width='800' height='600' fill='%231e293b'/%3E%3Ctext x='400' y='280' text-anchor='middle' font-size='20' fill='%2394a3b8' font-family='Arial'%3E請放置 ASML 剖面圖%3C/text%3E%3Ctext x='400' y='320' text-anchor='middle' font-size='14' fill='%2364748b' font-family='Arial'%3Einterface/images/asml_cutaway.png%3C/text%3E%3C/svg%3E"

    def _load_image_as_base64(self, image_path: str) -> str:
        """載入圖片並轉換為 base64 編碼"""
        try:
            if Path(image_path).is_absolute():
                image_file = Path(image_path)
            else:
                base_dir = Path(__file__).parent.parent
                image_file = base_dir / image_path

            if not image_file.exists():
                print(f"[Warning] 找不到圖片：{image_file}")
                return None

            with open(image_file, 'rb') as f:
                image_data = f.read()
                image_base64_str = base64.b64encode(image_data).decode('utf-8')

                suffix = image_file.suffix.lower()
                if suffix == '.png':
                    mime_type = 'image/png'
                elif suffix in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                else:
                    mime_type = 'image/png'

                data_uri = f"data:{mime_type};base64,{image_base64_str}"
                print(f"[OK] ASML 剖面圖已載入：{image_file.name} ({len(image_data)} bytes)")
                return data_uri

        except Exception as e:
            print(f"[Error] 載入圖片失敗：{e}")
            return None
