# -*- coding: utf-8 -*-
"""
真實照片式設備視覺化器（Photo-based Equipment Visualizer）
使用真實的 ASML DUV 光刻機照片，疊加動態故障標記
"""

from typing import Dict
import base64
from pathlib import Path


class PhotoEquipmentVisualizer:
    """真實照片式設備視覺化生成器"""

    def __init__(self, use_local_image: bool = False, image_path: str = None):
        """
        初始化視覺化器

        Args:
            use_local_image: 是否使用本地圖片
            image_path: 本地圖片路徑（如果 use_local_image=True）
        """
        self.use_local_image = use_local_image
        self.image_path = image_path
        self.image_base64 = None

        # 如果使用本地圖片，預先載入並轉換為 base64
        if self.use_local_image and self.image_path:
            self._load_image_as_base64()

    def generate_equipment_svg(self, state: Dict) -> str:
        """
        生成基於真實照片的設備視覺化

        Args:
            state: 設備狀態字典

        Returns:
            HTML字串（包含圖片和疊加層）
        """

        # 計算各部件狀態
        cooling_status = self._get_cooling_status(state)
        vacuum_status = self._get_vacuum_status(state)
        temp_status = self._get_temp_status(state)
        filter_status = self._get_filter_status(state)
        light_status = self._get_light_status(state)

        # 設備圖片來源
        if self.use_local_image and self.image_base64:
            # 使用 base64 編碼的圖片（嵌入 HTML）
            image_src = self.image_base64
        else:
            # 使用佔位圖片（深色背景 + 設備輪廓）
            image_src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 600'%3E%3Crect width='1000' height='600' fill='%231e293b'/%3E%3Ctext x='500' y='280' text-anchor='middle' font-size='24' fill='%2394a3b8' font-family='Arial'%3E請放置 ASML DUV 設備照片%3C/text%3E%3Ctext x='500' y='320' text-anchor='middle' font-size='16' fill='%2364748b' font-family='Arial'%3E圖片路徑：interface/images/asml_duv.jpg%3C/text%3E%3C/svg%3E"

        # 生成 HTML
        html = f"""
        <div style="position: relative; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    padding: 15px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                    width: 100%; max-width: 1000px; margin: 0 auto;">

            <!-- 設備標題 -->
            <div style="text-align: center; margin-bottom: 10px;">
                <h2 style="color: #f1f5f9; margin: 0; font-size: 24px; text-shadow: 2px 2px 4px rgba(0,0,0,0.7);">
                    光刻曝光機 (Lithography Scanner)
                </h2>
                <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 13px;">
                    ASML TWINSCAN NXT:1980Di - 193nm ArF 浸潤式微影系統
                </p>
            </div>

            <!-- 設備圖片容器 -->
            <div style="position: relative; width: 100%; height: 500px; background: #0f172a;
                        border-radius: 10px; overflow: hidden; box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);">

                <!-- 背景設備圖片 -->
                <img src="{image_src}"
                     style="width: 100%; height: 100%; object-fit: contain; opacity: 0.9;"
                     alt="ASML DUV Lithography Scanner"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">

                <!-- 圖片載入失敗時的備用內容 -->
                <div style="display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                            align-items: center; justify-content: center; flex-direction: column;
                            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);">
                    <svg width="200" height="200" viewBox="0 0 200 200" style="opacity: 0.3;">
                        <rect x="40" y="40" width="120" height="120" rx="10" fill="none" stroke="#64748b" stroke-width="2"/>
                        <circle cx="100" cy="100" r="30" fill="none" stroke="#64748b" stroke-width="2"/>
                        <path d="M 70,70 L 130,130 M 130,70 L 70,130" stroke="#64748b" stroke-width="2"/>
                    </svg>
                    <p style="color: #64748b; margin-top: 20px; font-size: 16px;">設備照片未載入</p>
                    <p style="color: #475569; font-size: 12px;">請將設備照片放置於：interface/images/asml_duv.jpg</p>
                </div>

                <!-- ========================= 動態標記疊加層 ========================= -->

                <!-- 光源模組標記（頂部中央）-->
                {self._generate_marker(
                    x=450, y=80, width=140, height=40,
                    label=f"曝光光源 {state.get('light_intensity', 100):.0f}%",
                    status=light_status,
                    description="193nm ArF 準分子雷射"
                )}

                <!-- 投影鏡頭標記（上層中央）-->
                {self._generate_marker(
                    x=420, y=150, width=160, height=40,
                    label="投影鏡頭組",
                    status={"color": "#22c55e", "severity": "normal"},
                    description="4倍縮小投影系統"
                )}

                <!-- 真空腔體標記（中層）-->
                {self._generate_marker(
                    x=350, y=240, width=300, height=50,
                    label=f"真空腔體 {state.get('vacuum_pressure', 1e-6):.2e} Torr",
                    status=vacuum_status,
                    description="晶圓曝光區域"
                )}

                <!-- 晶圓載台標記（底部中央）-->
                {self._generate_marker(
                    x=380, y=380, width=240, height=40,
                    label="晶圓載台",
                    status={"color": "#22c55e", "severity": "normal"},
                    description="高精度 6 軸定位系統"
                )}

                <!-- 冷卻系統標記（右側）-->
                {self._generate_marker(
                    x=720, y=200, width=160, height=60,
                    label=f"冷卻系統 {state.get('cooling_flow', 5.0):.1f} L/min",
                    status=cooling_status,
                    description=f"鏡頭溫度 {state.get('lens_temp', 23.0):.1f}°C"
                )}

                <!-- 對準系統標記（左側）-->
                {self._generate_marker(
                    x=120, y=220, width=140, height=50,
                    label="對準系統",
                    status={"color": "#10b981", "severity": "normal"},
                    description="TTL 對準相機"
                )}

                <!-- 過濾網標記（左下）-->
                {self._generate_marker(
                    x=140, y=400, width=140, height=40,
                    label="空氣過濾",
                    status=filter_status,
                    description="HEPA H14 級過濾"
                )}

                <!-- ========================= 故障警示浮動標籤 ========================= -->
                {self._generate_fault_alerts(state, cooling_status, vacuum_status, temp_status, filter_status)}

                <!-- ========================= 狀態圖例 ========================= -->
                <div style="position: absolute; bottom: 15px; right: 15px;
                            background: rgba(15, 23, 42, 0.95); padding: 12px 15px;
                            border-radius: 8px; border: 1px solid #334155;">
                    <div style="color: #cbd5e1; font-size: 12px; font-weight: bold; margin-bottom: 8px;">
                        狀態圖例
                    </div>
                    <div style="display: flex; align-items: center; margin: 5px 0;">
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: #22c55e; margin-right: 8px;"></div>
                        <span style="color: #cbd5e1; font-size: 11px;">正常</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 5px 0;">
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: #f59e0b; margin-right: 8px;"></div>
                        <span style="color: #cbd5e1; font-size: 11px;">警告</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 5px 0;">
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: #ef4444; margin-right: 8px;"></div>
                        <span style="color: #cbd5e1; font-size: 11px;">異常</span>
                    </div>
                </div>

            </div>

            <!-- CSS 動畫 -->
            <style>
                @keyframes pulse-warning {{
                    0%, 100% {{
                        opacity: 1;
                        box-shadow: 0 0 15px var(--warning-color);
                    }}
                    50% {{
                        opacity: 0.7;
                        box-shadow: 0 0 25px var(--warning-color);
                    }}
                }}

                @keyframes pulse-danger {{
                    0%, 100% {{
                        opacity: 1;
                        box-shadow: 0 0 20px #ef4444;
                    }}
                    50% {{
                        opacity: 0.6;
                        box-shadow: 0 0 35px #ef4444;
                    }}
                }}

                @keyframes float-alert {{
                    0%, 100% {{
                        transform: translateY(0px);
                    }}
                    50% {{
                        transform: translateY(-5px);
                    }}
                }}

                .equipment-marker {{
                    transition: all 0.3s ease;
                }}

                .equipment-marker:hover {{
                    transform: scale(1.05);
                    z-index: 100;
                }}

                .fault-alert {{
                    animation: float-alert 2s ease-in-out infinite, pulse-danger 1.5s infinite;
                }}
            </style>
        </div>
        """

        return html

    def _generate_marker(self, x: int, y: int, width: int, height: int,
                        label: str, status: Dict, description: str = "") -> str:
        """生成設備標記"""
        color = status.get("color", "#22c55e")
        severity = status.get("severity", "normal")

        # 根據嚴重程度選擇樣式
        if severity == "danger":
            animation = "animation: pulse-danger 1.5s infinite;"
            border_width = "3px"
        elif severity == "warning":
            animation = f"animation: pulse-warning 2s infinite; --warning-color: {color};"
            border_width = "2px"
        else:
            animation = ""
            border_width = "2px"

        return f"""
        <div class="equipment-marker" style="position: absolute; left: {x}px; top: {y}px;
                    width: {width}px; height: {height}px;
                    background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px);
                    border: {border_width} solid {color}; border-radius: 8px;
                    padding: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                    {animation}">
            <div style="color: {color}; font-size: 12px; font-weight: bold; margin-bottom: 3px;">
                {label}
            </div>
            {f'<div style="color: #94a3b8; font-size: 10px;">{description}</div>' if description else ''}
        </div>
        """

    def _generate_fault_alerts(self, state: Dict, cooling_status: Dict,
                               vacuum_status: Dict, temp_status: Dict,
                               filter_status: Dict) -> str:
        """生成故障警示標籤"""
        alerts = []

        # 冷卻流量過低
        if cooling_status.get("severity") in ["warning", "danger"]:
            flow = state.get("cooling_flow", 5.0)
            alerts.append(f"""
            <div class="fault-alert" style="position: absolute; left: 720px; top: 270px;
                        background: rgba(239, 68, 68, 0.95); color: white;
                        padding: 10px 15px; border-radius: 8px; font-size: 13px;
                        font-weight: bold; border: 2px solid #fca5a5;
                        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.6);">
                ⚠️ 冷卻流量過低<br>
                <span style="font-size: 11px; font-weight: normal;">當前: {flow:.1f} L/min</span>
            </div>
            """)

        # 溫度過高
        if temp_status.get("severity") in ["warning", "danger"]:
            temp = state.get("lens_temp", 23.0)
            color = "#ef4444" if temp > 26 else "#f59e0b"
            alerts.append(f"""
            <div class="fault-alert" style="position: absolute; left: 720px; top: 335px;
                        background: rgba(239, 68, 68, 0.95); color: white;
                        padding: 10px 15px; border-radius: 8px; font-size: 13px;
                        font-weight: bold; border: 2px solid #fca5a5;
                        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.6);">
                🔥 溫度過高<br>
                <span style="font-size: 11px; font-weight: normal;">當前: {temp:.1f}°C</span>
            </div>
            """)

        # 真空洩漏
        if vacuum_status.get("severity") == "danger":
            pressure = state.get("vacuum_pressure", 1e-6)
            alerts.append(f"""
            <div class="fault-alert" style="position: absolute; left: 480px; top: 295px;
                        background: rgba(239, 68, 68, 0.95); color: white;
                        padding: 10px 15px; border-radius: 8px; font-size: 13px;
                        font-weight: bold; border: 2px solid #fca5a5;
                        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.6);">
                ⚡ 真空洩漏<br>
                <span style="font-size: 11px; font-weight: normal;">壓力: {pressure:.2e} Torr</span>
            </div>
            """)

        # 過濾網堵塞
        if filter_status.get("severity") == "warning":
            alerts.append(f"""
            <div style="position: absolute; left: 150px; top: 445px;
                        background: rgba(245, 158, 11, 0.95); color: white;
                        padding: 8px 12px; border-radius: 6px; font-size: 12px;
                        font-weight: bold; border: 2px solid #fcd34d;
                        animation: pulse-warning 2s infinite; --warning-color: #f59e0b;">
                ⛔ 過濾網堵塞
            </div>
            """)

        return "\n".join(alerts)

    def _get_cooling_status(self, state: Dict) -> Dict:
        """獲取冷卻系統狀態"""
        flow_rate = state.get("cooling_flow", 5.0)

        if flow_rate < 4.0:
            return {"color": "#ef4444", "severity": "danger"}
        elif flow_rate < 4.5:
            return {"color": "#f59e0b", "severity": "warning"}
        else:
            return {"color": "#22c55e", "severity": "normal"}

    def _get_vacuum_status(self, state: Dict) -> Dict:
        """獲取真空系統狀態"""
        vacuum_leak = state.get("vacuum_leak", False)
        pressure = state.get("vacuum_pressure", 1e-6)

        if vacuum_leak or pressure > 1e-5:
            return {"color": "#ef4444", "severity": "danger"}
        else:
            return {"color": "#22c55e", "severity": "normal"}

    def _get_temp_status(self, state: Dict) -> Dict:
        """獲取溫度狀態"""
        temp = state.get("lens_temp", 23.0)

        if temp > 26:
            return {"color": "#ef4444", "severity": "danger"}
        elif temp > 25:
            return {"color": "#f59e0b", "severity": "warning"}
        else:
            return {"color": "#22c55e", "severity": "normal"}

    def _get_filter_status(self, state: Dict) -> Dict:
        """獲取過濾網狀態"""
        clogged = state.get("filter_clogged", False)

        if clogged:
            return {"color": "#f59e0b", "severity": "warning"}
        else:
            return {"color": "#64748b", "severity": "normal"}

    def _get_light_status(self, state: Dict) -> Dict:
        """獲取光源狀態"""
        intensity = state.get("light_intensity", 100)

        if intensity < 90:
            return {"color": "#f59e0b", "severity": "warning"}
        else:
            return {"color": "#8b5cf6", "severity": "normal"}

    def _load_image_as_base64(self):
        """載入圖片並轉換為 base64 編碼"""
        try:
            # 構建完整路徑
            if Path(self.image_path).is_absolute():
                image_file = Path(self.image_path)
            else:
                # 相對於專案根目錄
                base_dir = Path(__file__).parent.parent
                image_file = base_dir / self.image_path

            if not image_file.exists():
                print(f"[Warning] 找不到圖片：{image_file}")
                return

            # 讀取圖片並轉換為 base64
            with open(image_file, 'rb') as f:
                image_data = f.read()
                image_base64_str = base64.b64encode(image_data).decode('utf-8')

                # 判斷圖片格式
                if image_file.suffix.lower() in ['.png']:
                    mime_type = 'image/png'
                elif image_file.suffix.lower() in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                else:
                    mime_type = 'image/png'  # 預設

                # 構建 data URI
                self.image_base64 = f"data:{mime_type};base64,{image_base64_str}"
                print(f"[OK] 圖片已載入並轉換為 base64：{image_file.name} ({len(image_data)} bytes)")

        except Exception as e:
            print(f"[Error] 載入圖片失敗：{e}")
            self.image_base64 = None
