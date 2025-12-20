# -*- coding: utf-8 -*-
"""
預覽新的設備視覺化效果
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from interface.equipment_visualizer import EquipmentVisualizer
import gradio as gr

# 創建視覺化器
visualizer = EquipmentVisualizer()

def preview_normal():
    """預覽正常狀態"""
    state = {
        "cooling_flow": 5.0,
        "vacuum_pressure": 1e-6,
        "vacuum_leak": False,
        "lens_temp": 23.5,
        "filter_clogged": False,
        "light_intensity": 100,
        "is_running": True
    }
    return visualizer.generate_equipment_svg(state)

def preview_cooling_warning():
    """預覽冷卻警告"""
    state = {
        "cooling_flow": 4.2,  # 警告
        "vacuum_pressure": 1e-6,
        "vacuum_leak": False,
        "lens_temp": 25.5,  # 稍高
        "filter_clogged": False,
        "light_intensity": 100,
        "is_running": True
    }
    return visualizer.generate_equipment_svg(state)

def preview_multiple_faults():
    """預覽多重故障"""
    state = {
        "cooling_flow": 3.5,  # 危險
        "vacuum_pressure": 5e-5,  # 洩漏
        "vacuum_leak": True,
        "lens_temp": 26.5,  # 過高
        "filter_clogged": True,  # 堵塞
        "light_intensity": 95,
        "is_running": True
    }
    return visualizer.generate_equipment_svg(state)

# 創建 Gradio 介面
with gr.Blocks(title="設備視覺化預覽") as demo:
    gr.Markdown("# 🔬 設備視覺化效果預覽")
    gr.Markdown("**查看不同故障狀態下的設備視覺化效果**")

    with gr.Tab("正常狀態"):
        gr.Markdown("### ✅ 所有系統正常運作")
        btn1 = gr.Button("顯示正常狀態", variant="primary")
        output1 = gr.HTML()
        btn1.click(fn=preview_normal, outputs=output1)

    with gr.Tab("冷卻警告"):
        gr.Markdown("### ⚠️ 冷卻流量偏低 + 溫度上升")
        btn2 = gr.Button("顯示警告狀態", variant="primary")
        output2 = gr.HTML()
        btn2.click(fn=preview_cooling_warning, outputs=output2)

    with gr.Tab("多重故障"):
        gr.Markdown("### 🔥 冷卻異常 + 真空洩漏 + 過濾網堵塞 + 溫度過高")
        btn3 = gr.Button("顯示多重故障", variant="primary")
        output3 = gr.HTML()
        btn3.click(fn=preview_multiple_faults, outputs=output3)

    gr.Markdown("""
    ---
    ### 視覺化特點：
    - ✅ **動態脈動效果**：異常部位會發光/脈動
    - ✅ **顏色區分**：綠色(正常) / 橙色(警告) / 紅色(危險)
    - ✅ **流動動畫**：冷卻水管路有流動效果
    - ✅ **故障標記**：浮動標籤清楚標示問題位置
    - ✅ **即時更新**：狀態改變立即反映在圖上
    """)

if __name__ == "__main__":
    demo.launch(share=False)
