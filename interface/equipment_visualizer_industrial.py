# -*- coding: utf-8 -*-
"""
工業產線視覺化器 (Industrial Production Line Visualizer)
參考論文 "Digital twin driven intelligent manufacturing" 的視覺化風格
- 多設備監控視圖
- 即時狀態資訊彈窗
- 故障告警閃爍
- 工業控制室風格
"""

from typing import Dict
import base64
from pathlib import Path


class IndustrialEquipmentVisualizer:
    """工業產線視覺化生成器 (類似 Paper 圖片 2 風格)"""

    def __init__(self):
        """初始化視覺化器"""
        # 載入真實設備照片
        self.equipment_image = self._load_image_as_base64("interface/images/asml_duv.png")

    def generate_equipment_view(self, state: Dict, selected_component: str = None) -> str:
        """
        生成設備視覺化 (工業產線風格)

        Args:
            state: 設備狀態字典
            selected_component: 選中的部件

        Returns:
            HTML字串
        """

        # 計算各部件狀態
        cooling_status = self._get_component_status("cooling", state)
        vacuum_status = self._get_component_status("vacuum", state)
        lens_status = self._get_component_status("lens", state)
        light_status = self._get_component_status("light", state)

        # 設備圖片來源
        if self.equipment_image:
            image_src = self.equipment_image
        else:
            image_src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 600'%3E%3Crect width='1000' height='600' fill='%231e293b'/%3E%3C/svg%3E"

        # 生成狀態彈窗 (類似 Paper 圖片 2 的資訊框)
        info_cards = self._generate_info_cards(state, cooling_status, vacuum_status, lens_status, light_status)

        # 生成故障告警 (類似 Paper 左側的 Fault Alarm)
        fault_alarms = self._generate_fault_alarms(state, cooling_status, vacuum_status, lens_status)

        html = f"""
        <div style="position: relative; background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%);
                    padding: 15px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.7);">

            <!-- 頂部標題列 -->
            <div style="background: linear-gradient(90deg, #1e3a5f 0%, #2d5a8c 100%);
                        padding: 12px 20px; border-radius: 8px; margin-bottom: 15px;
                        border: 1px solid #3a5f8c; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="color: #e0f2ff; margin: 0; font-size: 22px; font-weight: bold;
                                   text-shadow: 0 2px 8px rgba(0,0,0,0.6);">
                            ASML TWINSCAN NXT:1980Di 光刻曝光機
                        </h2>
                        <p style="color: #94c5e8; margin: 5px 0 0 0; font-size: 12px;">
                            193nm ArF 浸潤式微影系統 | 即時設備狀態監控
                        </p>
                    </div>
                    <div style="background: rgba(0,0,0,0.3); padding: 8px 16px; border-radius: 6px;
                               border: 1px solid #3a5f8c;">
                        <span style="color: #94c5e8; font-size: 11px;">設備 ID:</span>
                        <span style="color: #e0f2ff; font-size: 13px; font-weight: bold; margin-left: 8px;">ET01</span>
                    </div>
                </div>
            </div>

            <!-- 主要內容區 -->
            <div style="display: grid; grid-template-columns: 250px 1fr 320px; gap: 15px;">

                <!-- 左側: 故障告警面板 -->
                <div style="background: rgba(15, 23, 42, 0.9); border-radius: 10px;
                           border: 1px solid #2d4a6e; padding: 15px;
                           box-shadow: inset 0 0 20px rgba(0,0,0,0.5);">
                    <div style="color: #e0f2ff; font-size: 14px; font-weight: bold;
                               margin-bottom: 12px; padding-bottom: 8px;
                               border-bottom: 2px solid #3a5f8c;">
                        <span style="color: #ff6b6b; margin-right: 8px;">⚠</span>
                        故障告警
                    </div>
                    {fault_alarms}
                </div>

                <!-- 中間: 設備 3D 視圖 + 資訊卡片 -->
                <div style="position: relative; background: #0f172a; border-radius: 10px;
                           overflow: hidden; border: 1px solid #2d4a6e;
                           box-shadow: inset 0 0 30px rgba(0,0,0,0.7);">

                    <!-- 設備照片/3D 模型 -->
                    <img src="{image_src}"
                         style="width: 100%; height: 100%; object-fit: contain; opacity: 0.95;"
                         alt="ASML Equipment">

                    <!-- 資訊卡片疊加 (類似 Paper 圖片 2 的彈窗) -->
                    {info_cards}

                    <!-- 連接線 (視覺化數據流) -->
                    <svg style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;">
                        <!-- 冷卻系統連接線 -->
                        <line x1="80%" y1="40%" x2="95%" y2="20%"
                              stroke="#00d4ff" stroke-width="2" stroke-dasharray="5,5"
                              opacity="0.6">
                            <animate attributeName="stroke-dashoffset" from="0" to="10"
                                     dur="1s" repeatCount="indefinite"/>
                        </line>
                        <!-- 真空系統連接線 -->
                        <line x1="50%" y1="45%" x2="95%" y2="35%"
                              stroke="#00d4ff" stroke-width="2" stroke-dasharray="5,5"
                              opacity="0.6">
                            <animate attributeName="stroke-dashoffset" from="0" to="10"
                                     dur="1s" repeatCount="indefinite"/>
                        </line>
                        <!-- 光源系統連接線 -->
                        <line x1="45%" y1="15%" x2="95%" y2="50%"
                              stroke="#00d4ff" stroke-width="2" stroke-dasharray="5,5"
                              opacity="0.6">
                            <animate attributeName="stroke-dashoffset" from="0" to="10"
                                     dur="1s" repeatCount="indefinite"/>
                        </line>
                        <!-- 鏡頭系統連接線 -->
                        <line x1="50%" y1="25%" x2="95%" y2="65%"
                              stroke="#00d4ff" stroke-width="2" stroke-dasharray="5,5"
                              opacity="0.6">
                            <animate attributeName="stroke-dashoffset" from="0" to="10"
                                     dur="1s" repeatCount="indefinite"/>
                        </line>
                    </svg>
                </div>

                <!-- 右側: 即時狀態資訊面板 -->
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    {self._generate_status_card("冷卻系統", cooling_status, state)}
                    {self._generate_status_card("真空系統", vacuum_status, state)}
                    {self._generate_status_card("光源系統", light_status, state)}
                    {self._generate_status_card("鏡頭系統", lens_status, state)}
                </div>
            </div>

            <!-- 底部狀態列 -->
            <div style="margin-top: 15px; padding: 10px 15px;
                       background: rgba(15, 23, 42, 0.6); border-radius: 8px;
                       border: 1px solid #2d4a6e; display: flex; justify-content: space-between;">
                <div style="display: flex; gap: 25px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 12px; height: 12px; background: #22c55e; border-radius: 50%;
                                   box-shadow: 0 0 10px #22c55e;"></div>
                        <span style="color: #cbd5e1; font-size: 12px;">正常</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 12px; height: 12px; background: #f59e0b; border-radius: 50%;
                                   box-shadow: 0 0 10px #f59e0b;"></div>
                        <span style="color: #cbd5e1; font-size: 12px;">警告</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 12px; height: 12px; background: #ef4444; border-radius: 50%;
                                   box-shadow: 0 0 10px #ef4444; animation: pulse 1.5s infinite;"></div>
                        <span style="color: #cbd5e1; font-size: 12px;">異常</span>
                    </div>
                </div>
                <div style="color: #94a3b8; font-size: 11px;">
                    Real-time Status Information
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
                @keyframes blink {{
                    0%, 49% {{ opacity: 1; }}
                    50%, 100% {{ opacity: 0.3; }}
                }}
            </style>
        </div>
        """

        return html

    def _generate_info_cards(self, state: Dict, cooling_status: Dict,
                            vacuum_status: Dict, lens_status: Dict, light_status: Dict) -> str:
        """生成資訊卡片 (類似 Paper 圖片 2 的彈窗)"""
        cards = []

        # 冷卻系統資訊卡 (右上)
        if cooling_status["severity"] != "normal":
            cards.append(f"""
            <div style="position: absolute; right: 5%; top: 15%;
                       background: linear-gradient(135deg, rgba(220, 38, 38, 0.95) 0%, rgba(185, 28, 28, 0.95) 100%);
                       color: white; padding: 12px 16px; border-radius: 10px;
                       box-shadow: 0 8px 32px rgba(220, 38, 38, 0.6);
                       border: 2px solid #fca5a5; animation: blink 2s infinite;
                       max-width: 200px; z-index: 100;">
                <div style="font-size: 11px; font-weight: bold; margin-bottom: 6px; opacity: 0.9;">
                    設備信息 ✕
                </div>
                <div style="font-size: 13px; font-weight: bold; margin-bottom: 8px;">
                    ID編號: ET01
                </div>
                <div style="font-size: 11px; line-height: 1.6;">
                    <div>設備名稱: <span style="color: #00d4ff;">冷卻水循環</span></div>
                    <div>對應工藝: <span style="color: #fecaca;">溫控</span></div>
                    <div>故障率: <span style="color: #fff;">{int((5.0 - state.get('cooling_flow', 5.0)) / 5.0 * 100)}%</span></div>
                    <div>噴淋壓力: <span style="color: #fff;">0.15Mpa</span></div>
                    <div>轉水補水: <span style="color: #fecaca;">{state.get('cooling_flow', 5.0):.1f}L/min</span></div>
                    <div>溫度: <span style="color: #fecaca;">{state.get('lens_temp', 23.0):.0f}°C</span></div>
                </div>
            </div>
            """)
        else:
            cards.append(f"""
            <div style="position: absolute; right: 5%; top: 15%;
                       background: linear-gradient(135deg, rgba(34, 197, 94, 0.95) 0%, rgba(22, 163, 74, 0.95) 100%);
                       color: white; padding: 12px 16px; border-radius: 10px;
                       box-shadow: 0 8px 32px rgba(34, 197, 94, 0.4);
                       border: 2px solid #86efac;
                       max-width: 200px; z-index: 100;">
                <div style="font-size: 11px; font-weight: bold; margin-bottom: 6px; opacity: 0.9;">
                    設備信息 ✕
                </div>
                <div style="font-size: 13px; font-weight: bold; margin-bottom: 8px;">
                    ID編號: ET01
                </div>
                <div style="font-size: 11px; line-height: 1.6;">
                    <div>設備名稱: <span style="color: #e0f2ff;">冷卻水循環</span></div>
                    <div>對應工藝: <span style="color: #e0f2ff;">溫控</span></div>
                    <div>故障率: <span style="color: #fff;">1%</span></div>
                    <div>噴淋壓力: <span style="color: #fff;">0.15Mpa</span></div>
                    <div>轉水補水: <span style="color: #e0f2ff;">{state.get('cooling_flow', 5.0):.1f}L/min</span></div>
                    <div>溫度: <span style="color: #e0f2ff;">{state.get('lens_temp', 23.0):.0f}°C</span></div>
                </div>
            </div>
            """)

        # 真空系統資訊卡 (中間)
        vacuum_color = "#dc2626" if vacuum_status["severity"] != "normal" else "#16a34a"
        vacuum_bg = f"linear-gradient(135deg, rgba(220, 38, 38, 0.95) 0%, rgba(185, 28, 28, 0.95) 100%)" if vacuum_status["severity"] != "normal" else f"linear-gradient(135deg, rgba(34, 197, 94, 0.95) 0%, rgba(22, 163, 74, 0.95) 100%)"

        cards.append(f"""
        <div style="position: absolute; left: 50%; top: 40%; transform: translateX(-50%);
                   background: {vacuum_bg};
                   color: white; padding: 12px 16px; border-radius: 10px;
                   box-shadow: 0 8px 32px rgba(34, 197, 94, 0.4);
                   border: 2px solid #86efac;
                   max-width: 200px; z-index: 100;
                   {'animation: blink 2s infinite;' if vacuum_status['severity'] != 'normal' else ''}">
            <div style="font-size: 11px; font-weight: bold; margin-bottom: 6px; opacity: 0.9;">
                設備信息 ✕
            </div>
            <div style="font-size: 13px; font-weight: bold; margin-bottom: 8px;">
                ID編號: ET01
            </div>
            <div style="font-size: 11px; line-height: 1.6;">
                <div>設備名稱: <span style="color: #e0f2ff;">真空系統</span></div>
                <div>對應工藝: <span style="color: #e0f2ff;">微影曝光</span></div>
                <div>故障率: <span style="color: #fff;">1%</span></div>
                <div>噴淋壓力: <span style="color: #fff;">0.15Mpa</span></div>
                <div>真空度: <span style="color: #e0f2ff;">{state.get('vacuum_pressure', 1e-6):.2e}Torr</span></div>
            </div>
        </div>
        """)

        return "\n".join(cards)

    def _generate_fault_alarms(self, state: Dict, cooling_status: Dict,
                              vacuum_status: Dict, lens_status: Dict) -> str:
        """生成故障告警列表 (類似 Paper 左側面板)"""
        alarms = []

        if cooling_status["severity"] == "critical":
            alarms.append(f"""
            <div style="background: rgba(220, 38, 38, 0.2); border-left: 4px solid #ef4444;
                       padding: 10px; margin-bottom: 10px; border-radius: 6px;
                       animation: blink 2s infinite;">
                <div style="color: #fca5a5; font-size: 12px; font-weight: bold; margin-bottom: 4px;">
                    🔴 冷卻系統故障
                </div>
                <div style="color: #cbd5e1; font-size: 10px; line-height: 1.5;">
                    流量: {state.get('cooling_flow', 5.0):.1f}L/min (過低)<br>
                    溫度: {state.get('lens_temp', 23.0):.1f}°C (過高)<br>
                    建議: 檢查過濾網和管路
                </div>
            </div>
            """)

        if vacuum_status["severity"] == "critical":
            alarms.append(f"""
            <div style="background: rgba(220, 38, 38, 0.2); border-left: 4px solid #ef4444;
                       padding: 10px; margin-bottom: 10px; border-radius: 6px;
                       animation: blink 2s infinite;">
                <div style="color: #fca5a5; font-size: 12px; font-weight: bold; margin-bottom: 4px;">
                    🔴 真空系統洩漏
                </div>
                <div style="color: #cbd5e1; font-size: 10px; line-height: 1.5;">
                    壓力: {state.get('vacuum_pressure', 1e-6):.2e} Torr<br>
                    建議: 檢查密封圈
                </div>
            </div>
            """)

        if lens_status["severity"] == "warning":
            alarms.append(f"""
            <div style="background: rgba(245, 158, 11, 0.2); border-left: 4px solid #f59e0b;
                       padding: 10px; margin-bottom: 10px; border-radius: 6px;">
                <div style="color: #fbbf24; font-size: 12px; font-weight: bold; margin-bottom: 4px;">
                    🟠 鏡頭溫度警告
                </div>
                <div style="color: #cbd5e1; font-size: 10px; line-height: 1.5;">
                    溫度: {state.get('lens_temp', 23.0):.1f}°C<br>
                    建議: 增加冷卻
                </div>
            </div>
            """)

        if not alarms:
            alarms.append("""
            <div style="text-align: center; padding: 20px; color: #64748b;">
                <div style="font-size: 40px; margin-bottom: 10px;">✓</div>
                <div style="font-size: 12px;">系統運行正常</div>
            </div>
            """)

        return "\n".join(alarms)

    def _generate_status_card(self, title: str, status: Dict, state: Dict) -> str:
        """生成右側狀態卡片"""
        color = {
            "normal": "#22c55e",
            "warning": "#f59e0b",
            "critical": "#ef4444"
        }.get(status["severity"], "#64748b")

        # 取得參數值
        param_values = {
            "冷卻系統": f"{state.get('cooling_flow', 5.0):.1f} L/min | {state.get('lens_temp', 23.0):.1f}°C",
            "真空系統": f"{state.get('vacuum_pressure', 1e-6):.2e} Torr",
            "光源系統": f"{state.get('light_intensity', 100):.0f}%",
            "鏡頭系統": f"4x 縮小 | {state.get('lens_temp', 23.0):.1f}°C"
        }.get(title, "N/A")

        animation = "animation: glow 2s infinite;" if status["severity"] == "critical" else ""

        return f"""
        <div style="background: rgba(15, 23, 42, 0.9); border-radius: 10px;
                   border: 2px solid {color}; padding: 12px;
                   box-shadow: 0 8px 32px rgba(0,0,0,0.5); --glow-color: {color}; {animation}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #e0f2ff; font-size: 13px; font-weight: bold;">{title}</span>
                <div style="width: 14px; height: 14px; background: {color}; border-radius: 50%;
                           box-shadow: 0 0 12px {color};
                           {'animation: pulse 1.5s infinite;' if status['severity'] == 'critical' else ''}"></div>
            </div>
            <div style="color: #94a3b8; font-size: 11px; line-height: 1.6;">
                {param_values}
            </div>
            <div style="color: {color}; font-size: 10px; margin-top: 6px; font-weight: 500;">
                {status.get("message", "正常運行")}
            </div>
        </div>
        """

    def _get_component_status(self, component: str, state: Dict) -> Dict:
        """取得部件狀態"""
        if component == "cooling":
            flow = state.get("cooling_flow", 5.0)
            temp = state.get("lens_temp", 23.0)
            if flow < 4.5 or temp > 25:
                return {"severity": "critical", "color": "#ef4444", "message": "流量過低/溫度過高"}
            elif flow < 4.8 or temp > 24:
                return {"severity": "warning", "color": "#f59e0b", "message": "需注意"}
            else:
                return {"severity": "normal", "color": "#22c55e", "message": "正常"}

        elif component == "vacuum":
            leak = state.get("vacuum_leak", False)
            pressure = state.get("vacuum_pressure", 1.0e-6)
            if leak or pressure > 1.5e-6:
                return {"severity": "critical", "color": "#ef4444", "message": "真空洩漏"}
            else:
                return {"severity": "normal", "color": "#22c55e", "message": "正常"}

        elif component == "lens":
            temp = state.get("lens_temp", 23.0)
            if temp > 25:
                return {"severity": "critical", "color": "#ef4444", "message": "溫度過高"}
            elif temp > 24:
                return {"severity": "warning", "color": "#f59e0b", "message": "溫度偏高"}
            else:
                return {"severity": "normal", "color": "#22c55e", "message": "正常"}

        elif component == "light":
            intensity = state.get("light_intensity", 100)
            if intensity < 90:
                return {"severity": "warning", "color": "#f59e0b", "message": "光源衰減"}
            else:
                return {"severity": "normal", "color": "#22c55e", "message": "正常"}

        return {"severity": "normal", "color": "#64748b", "message": "未知"}

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
                print(f"[OK] 工業產線視覺化圖片已載入：{image_file.name}")
                return data_uri

        except Exception as e:
            print(f"[Error] 載入圖片失敗：{e}")
            return None
