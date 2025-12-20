# -*- coding: utf-8 -*-
"""
真實照片設備視覺化器（Real Photo Equipment Visualizer）
- 使用真實 ASML DUV 設備照片
- 在照片上直接標示故障部位（紅色標記）
- 大圖一次展示所有部件狀態
"""

from typing import Dict
import base64
from pathlib import Path


class RealPhotoEquipmentVisualizer:
    """真實照片設備視覺化生成器"""

    def __init__(self):
        """初始化視覺化器"""
        # 載入真實設備照片
        self.equipment_image = self._load_image_as_base64("interface/images/asml_duv.png")

    def generate_equipment_view(self, state: Dict, selected_component: str = None) -> str:
        """
        生成設備視覺化（使用真實照片 + 故障標示）

        Args:
            state: 設備狀態字典
            selected_component: 忽略（保持介面相容性）

        Returns:
            HTML字串
        """

        # 計算各部件狀態
        light_status = self._get_light_status(state)
        vacuum_status = self._get_vacuum_status(state)
        cooling_status = self._get_cooling_status(state)
        filter_status = self._get_filter_status(state)

        # 設備圖片來源
        if self.equipment_image:
            image_src = self.equipment_image
        else:
            image_src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 600'%3E%3Crect width='1000' height='600' fill='%231e293b'/%3E%3Ctext x='500' y='280' text-anchor='middle' font-size='24' fill='%2394a3b8' font-family='Arial'%3E請放置 ASML DUV 設備照片%3C/text%3E%3Ctext x='500' y='320' text-anchor='middle' font-size='16' fill='%2364748b' font-family='Arial'%3E圖片路徑：interface/images/asml_duv.png%3C/text%3E%3C/svg%3E"

        html = f"""
        <div style="position: relative; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    padding: 20px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.6);">

            <!-- 標題 -->
            <div style="text-align: center; margin-bottom: 15px;">
                <h2 style="color: #f1f5f9; margin: 0; font-size: 26px; font-weight: bold; text-shadow: 0 2px 8px rgba(0,0,0,0.5);">
                    ASML TWINSCAN NXT:1980Di 光刻曝光機
                </h2>
                <p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 14px;">
                    193nm ArF 浸潤式微影系統 | 即時設備狀態監控
                </p>
            </div>

            <!-- 設備大圖（真實照片）-->
            <div style="position: relative; width: 100%; min-height: 600px; background: #0f172a;
                        border-radius: 12px; overflow: hidden; box-shadow: inset 0 0 30px rgba(0,0,0,0.8);">

                <!-- 背景設備照片 -->
                <img src="{image_src}"
                     style="width: 100%; height: 100%; object-fit: contain;"
                     alt="ASML DUV Equipment">

                <!-- ==================== 設備部件標示（疊加在照片上）==================== -->

                <!-- 曝光光源（頂部）-->
                <div style="position: absolute; left: 45%; top: 8%; transform: translateX(-50%);">
                    {self._generate_status_marker(
                        label="曝光光源",
                        value=f"{state.get('light_intensity', 100):.0f}%",
                        status=light_status,
                        size="medium"
                    )}
                </div>

                <!-- 投影鏡頭組（上方中央）-->
                <div style="position: absolute; left: 50%; top: 22%; transform: translateX(-50%);">
                    {self._generate_status_marker(
                        label="投影鏡頭組",
                        value="4x 縮小系統",
                        status={"color": "#22c55e", "severity": "normal"},
                        size="large"
                    )}
                </div>

                <!-- 真空腔體（中央）-->
                <div style="position: absolute; left: 50%; top: 42%; transform: translateX(-50%);">
                    {self._generate_status_marker(
                        label="真空腔體",
                        value=f"{state.get('vacuum_pressure', 1e-6):.2e} Torr",
                        status=vacuum_status,
                        size="large"
                    )}
                </div>

                <!-- 晶圓載台（下方）-->
                <div style="position: absolute; left: 50%; top: 68%; transform: translateX(-50%);">
                    {self._generate_status_marker(
                        label="晶圓載台",
                        value="6 軸定位",
                        status={"color": "#22c55e", "severity": "normal"},
                        size="medium"
                    )}
                </div>

                <!-- 冷卻系統（右側）-->
                <div style="position: absolute; right: 5%; top: 35%;">
                    {self._generate_status_marker(
                        label="冷卻系統",
                        value=f"{state.get('cooling_flow', 5.0):.1f} L/min<br>{state.get('lens_temp', 23.0):.1f}°C",
                        status=cooling_status,
                        size="large",
                        highlight=True  # 故障時特別標示
                    )}
                </div>

                <!-- 對準系統（左側）-->
                <div style="position: absolute; left: 8%; top: 40%;">
                    {self._generate_status_marker(
                        label="對準系統",
                        value="TTL 相機",
                        status={"color": "#10b981", "severity": "normal"},
                        size="medium"
                    )}
                </div>

                <!-- 空氣過濾（左下）-->
                <div style="position: absolute; left: 12%; top: 75%;">
                    {self._generate_status_marker(
                        label="空氣過濾",
                        value="HEPA H14",
                        status=filter_status,
                        size="small"
                    )}
                </div>

                <!-- ==================== 故障警示（浮動標籤）==================== -->
                {self._generate_fault_alerts(state, cooling_status, vacuum_status, filter_status)}

            </div>

            <!-- 圖例說明 -->
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
                    <span style="color: #cbd5e1; font-size: 13px;">異常</span>
                </div>
            </div>

            <!-- CSS 動畫 -->
            <style>
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; transform: scale(1); }}
                    50% {{ opacity: 0.6; transform: scale(1.2); }}
                }}
                @keyframes glow {{
                    0%, 100% {{ box-shadow: 0 0 20px var(--glow-color), 0 0 40px var(--glow-color); }}
                    50% {{ box-shadow: 0 0 30px var(--glow-color), 0 0 60px var(--glow-color); }}
                }}
            </style>
        </div>
        """

        return html

    def _generate_status_marker(self, label: str, value: str, status: Dict,
                                size: str = "medium", highlight: bool = False) -> str:
        """生成狀態標記（疊加在照片上）"""

        color = status["color"]
        severity = status["severity"]

        # 尺寸設定
        sizes = {
            "small": {"width": "140px", "font_label": "11px", "font_value": "10px", "padding": "8px"},
            "medium": {"width": "180px", "font_label": "12px", "font_value": "11px", "padding": "10px"},
            "large": {"width": "220px", "font_label": "13px", "font_value": "12px", "padding": "12px"}
        }

        size_config = sizes.get(size, sizes["medium"])

        # 異常時的動畫
        animation = "animation: glow 2s infinite;" if severity != "normal" and highlight else ""

        # 背景透明度（異常時更明顯）
        bg_opacity = "0.95" if severity != "normal" else "0.85"

        return f"""
        <div style="background: rgba(15, 23, 42, {bg_opacity}); backdrop-filter: blur(12px);
                    border: 3px solid {color}; border-radius: 10px;
                    padding: {size_config['padding']}; width: {size_config['width']};
                    box-shadow: 0 8px 32px rgba(0,0,0,0.6), inset 0 0 20px rgba(0,0,0,0.3);
                    --glow-color: {color}; {animation}">
            <!-- 狀態指示燈 -->
            <div style="position: absolute; top: -8px; right: -8px;
                        width: 20px; height: 20px; background: {color}; border-radius: 50%;
                        box-shadow: 0 0 15px {color}; border: 2px solid #0f172a;
                        {'animation: pulse 1.5s infinite;' if severity != 'normal' else ''}"></div>

            <!-- 部件名稱 -->
            <div style="color: {color}; font-size: {size_config['font_label']};
                        font-weight: bold; margin-bottom: 5px; text-shadow: 0 2px 8px rgba(0,0,0,0.8);">
                {label}
            </div>

            <!-- 狀態數值 -->
            <div style="color: #e2e8f0; font-size: {size_config['font_value']};
                        line-height: 1.5; font-weight: 500;">
                {value}
            </div>
        </div>
        """

    def _generate_fault_alerts(self, state: Dict, cooling_status: Dict,
                               vacuum_status: Dict, filter_status: Dict) -> str:
        """生成故障警示浮動標籤"""

        alerts = []

        # 冷卻系統異常
        if cooling_status["severity"] != "normal":
            alerts.append(f"""
            <div style="position: absolute; right: 2%; top: 28%;
                        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                        color: white; padding: 15px 20px; border-radius: 12px;
                        box-shadow: 0 8px 32px rgba(220, 38, 38, 0.6);
                        border: 2px solid #fca5a5; animation: glow 2s infinite;
                        --glow-color: #ef4444; max-width: 280px;">
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
                    🔥 冷卻系統異常
                </div>
                <div style="font-size: 12px; line-height: 1.6; color: #fecaca;">
                    • 流量：{state.get('cooling_flow', 5.0):.1f} L/min（過低）<br>
                    • 溫度：{state.get('lens_temp', 23.0):.1f}°C（過高）<br>
                    • 建議：檢查過濾網和管路
                </div>
            </div>
            """)

        # 真空洩漏
        if vacuum_status["severity"] != "normal":
            alerts.append(f"""
            <div style="position: absolute; left: 3%; top: 50%;
                        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                        color: white; padding: 15px 20px; border-radius: 12px;
                        box-shadow: 0 8px 32px rgba(220, 38, 38, 0.6);
                        border: 2px solid #fca5a5; animation: glow 2s infinite;
                        --glow-color: #ef4444; max-width: 260px;">
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">
                    ⚡ 真空系統洩漏
                </div>
                <div style="font-size: 12px; line-height: 1.6; color: #fecaca;">
                    • 壓力：{state.get('vacuum_pressure', 1e-6):.2e} Torr<br>
                    • 建議：檢查密封圈
                </div>
            </div>
            """)

        return "\n".join(alerts)

    # ==================== 狀態計算方法 ====================

    def _get_light_status(self, state: Dict) -> Dict:
        """獲取光源狀態"""
        intensity = state.get("light_intensity", 100)
        if intensity < 90:
            return {"color": "#f59e0b", "severity": "warning"}
        else:
            return {"color": "#8b5cf6", "severity": "normal"}

    def _get_vacuum_status(self, state: Dict) -> Dict:
        """獲取真空狀態"""
        leak = state.get("vacuum_leak", False)
        if leak:
            return {"color": "#ef4444", "severity": "critical"}
        else:
            return {"color": "#22c55e", "severity": "normal"}

    def _get_cooling_status(self, state: Dict) -> Dict:
        """獲取冷卻狀態"""
        flow = state.get("cooling_flow", 5.0)
        temp = state.get("lens_temp", 23.0)

        if flow < 4.5 or temp > 25:
            return {"color": "#ef4444", "severity": "critical"}
        elif flow < 4.8 or temp > 24:
            return {"color": "#f59e0b", "severity": "warning"}
        else:
            return {"color": "#22c55e", "severity": "normal"}

    def _get_filter_status(self, state: Dict) -> Dict:
        """獲取過濾網狀態"""
        clogged = state.get("filter_clogged", False)
        if clogged:
            return {"color": "#f59e0b", "severity": "warning"}
        else:
            return {"color": "#22c55e", "severity": "normal"}

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

                if image_file.suffix.lower() in ['.png']:
                    mime_type = 'image/png'
                elif image_file.suffix.lower() in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                else:
                    mime_type = 'image/png'

                data_uri = f"data:{mime_type};base64,{image_base64_str}"
                print(f"[OK] 真實設備照片已載入：{image_file.name} ({len(image_data)} bytes)")
                return data_uri

        except Exception as e:
            print(f"[Error] 載入圖片失敗：{e}")
            return None
