# -*- coding: utf-8 -*-
"""
測試 ASML 剖面圖視覺化器
"""

import gradio as gr
from interface.equipment_visualizer_asml_cutaway import ASMLCutawayVisualizer


def create_test_interface():
    """建立測試介面"""

    visualizer = ASMLCutawayVisualizer()

    def update_visualization(cooling_flow, lens_temp, vacuum_leak, light_intensity):
        """更新視覺化"""
        state = {
            "cooling_flow": cooling_flow,
            "lens_temp": lens_temp,
            "vacuum_leak": vacuum_leak,
            "vacuum_pressure": 1e-3 if vacuum_leak else 1e-6,
            "light_intensity": light_intensity,
        }
        return visualizer.generate_equipment_view(state)

    # 建立 Gradio 介面
    with gr.Blocks(title="ASML 剖面圖測試") as demo:

        gr.Markdown("""
        # 🔬 ASML DUV 設備剖面圖測試

        調整下方參數來模擬各種異常狀態，觀察設備圖上的紅燈閃爍效果。

        **圖片需求**：請將 ASML 剖面圖存放到 `interface/images/asml_cutaway.png`
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ 模擬參數")

                cooling_flow = gr.Slider(
                    minimum=2.0, maximum=6.0, value=5.0, step=0.1,
                    label="冷卻流量 (L/min)",
                    info="< 4.0 = 異常, < 4.5 = 警告"
                )

                lens_temp = gr.Slider(
                    minimum=20.0, maximum=30.0, value=23.0, step=0.5,
                    label="鏡組溫度 (°C)",
                    info="> 26 = 異常, > 24 = 警告"
                )

                vacuum_leak = gr.Checkbox(
                    label="真空洩漏",
                    value=False,
                    info="勾選模擬真空系統洩漏"
                )

                light_intensity = gr.Slider(
                    minimum=70, maximum=100, value=100, step=1,
                    label="光源強度 (%)",
                    info="< 85 = 異常, < 92 = 警告"
                )

                gr.Markdown("""
                ---
                ### 📋 快速預設

                點擊按鈕快速切換狀態：
                """)

                with gr.Row():
                    normal_btn = gr.Button("✅ 全部正常", variant="secondary", size="sm")
                    fault_btn = gr.Button("🔴 模擬故障", variant="stop", size="sm")

            with gr.Column(scale=3):
                equipment_view = gr.HTML(
                    label="設備視覺化",
                    value=visualizer.generate_equipment_view({
                        "cooling_flow": 5.0,
                        "lens_temp": 23.0,
                        "vacuum_leak": False,
                        "vacuum_pressure": 1e-6,
                        "light_intensity": 100,
                    })
                )

        # 綁定事件
        inputs = [cooling_flow, lens_temp, vacuum_leak, light_intensity]

        for inp in inputs:
            inp.change(
                fn=update_visualization,
                inputs=inputs,
                outputs=equipment_view
            )

        # 預設按鈕
        def set_normal():
            return 5.0, 23.0, False, 100

        def set_fault():
            return 3.5, 27.0, True, 80

        normal_btn.click(
            fn=set_normal,
            outputs=[cooling_flow, lens_temp, vacuum_leak, light_intensity]
        ).then(
            fn=update_visualization,
            inputs=inputs,
            outputs=equipment_view
        )

        fault_btn.click(
            fn=set_fault,
            outputs=[cooling_flow, lens_temp, vacuum_leak, light_intensity]
        ).then(
            fn=update_visualization,
            inputs=inputs,
            outputs=equipment_view
        )

    return demo


if __name__ == "__main__":
    print("=" * 60)
    print("ASML 剖面圖視覺化測試")
    print("=" * 60)
    print()
    print("請確保已將 ASML 剖面圖放到：")
    print("  interface/images/asml_cutaway.png")
    print()
    print("啟動中...")
    print()

    demo = create_test_interface()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7862,
        share=False
    )
