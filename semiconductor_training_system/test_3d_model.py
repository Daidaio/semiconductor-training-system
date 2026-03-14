# -*- coding: utf-8 -*-
"""
測試 3D 真實模型載入
快速驗證 3D 視覺化功能
"""

import gradio as gr
from interface.equipment_visualizer_3d_realistic import RealisticEquipmentVisualizer

def test_3d_visualization():
    """測試 3D 視覺化"""

    print("=" * 70)
    print("3D 真實模型視覺化測試")
    print("=" * 70)
    print()

    # 初始化視覺化器
    print("📦 初始化 3D 視覺化器...")
    visualizer = RealisticEquipmentVisualizer(
        model_path="assets/models/duv_machine.glb"
    )
    print("✅ 視覺化器初始化完成")
    print()

    # 模擬設備狀態（包含異常）
    print("🔧 設定測試狀態...")
    test_state = {
        'cooling_flow': 3.5,        # 異常（正常 5.0 L/min）
        'lens_temp': 25.2,          # 異常（正常 23.0°C）
        'vacuum_pressure': 2.1e-6,  # 警告（正常 1.0e-6 Torr）
        'light_intensity': 98.0,    # 正常
        'alignment_error': 8.5      # 異常（正常 < 2.0 nm）
    }

    print("  冷卻流量: 3.5 L/min (異常 🔴)")
    print("  鏡頭溫度: 25.2°C (異常 🔴)")
    print("  真空壓力: 2.1e-6 Torr (警告 🟡)")
    print("  光源強度: 98.0% (正常 🟢)")
    print("  對準誤差: 8.5 nm (異常 🔴)")
    print()

    # 生成 3D 視圖
    print("🎨 生成 3D 視覺化...")
    html_output = visualizer.generate_3d_view(
        state=test_state,
        faults=['cooling_system', 'lens_system', 'alignment_system']
    )
    print("✅ HTML 視覺化已生成")
    print()

    # 創建 Gradio 介面
    print("🌐 創建 Web 介面...")
    with gr.Blocks(
        title="3D 曝光機測試",
        theme=gr.themes.Soft(primary_hue="blue")
    ) as demo:

        gr.Markdown("""
        # 🔬 DUV 曝光機 3D 真實模型測試

        測試 Three.js + GLTFLoader 載入真實 Blender 模型
        """)

        # 3D 視覺化
        html_component = gr.HTML(html_output, label="3D 設備監控")

        # 說明文字
        with gr.Row():
            with gr.Column():
                gr.Markdown("""
                ## 🎮 互動控制

                - **滑鼠左鍵拖曳**：旋轉視角
                - **滑鼠滾輪**：縮放模型
                - **滑鼠右鍵拖曳**：平移視角
                - **點擊零件**：查看詳細資訊
                - **點擊狀態面板**：聚焦到該零件
                """)

            with gr.Column():
                gr.Markdown("""
                ## 🔴 當前異常狀態

                - **冷卻系統**：流量 3.5 L/min（應為 5.0）
                - **投影鏡頭**：溫度 25.2°C（應為 23.0°C）
                - **對準系統**：誤差 8.5 nm（應 < 2.0）
                - **真空腔體**：壓力 2.1e-6 Torr（警告）

                **異常零件會顯示紅色閃爍光暈 🔴**
                """)

        gr.Markdown("""
        ---

        ## 📋 測試檢查項目

        - [ ] 模型能正常載入（無錯誤訊息）
        - [ ] 可以用滑鼠旋轉模型
        - [ ] 可以用滾輪縮放模型
        - [ ] 異常零件顯示紅色光暈
        - [ ] 光暈有閃爍動畫效果
        - [ ] 點擊零件顯示詳情彈窗
        - [ ] 點擊狀態面板能聚焦零件
        - [ ] 左側狀態面板顯示正確

        ## 🔧 如果模型載入失敗

        1. 確認模型檔案在：`assets/models/duv_machine.glb`
        2. 檢查檔案大小是否 > 1MB
        3. 嘗試用 Blender 重新導出為 .glb 格式
        4. 參考：`3D模型資源與測試.md` 疑難排解章節

        ## 📚 相關文件

        - **完整指南**：`Blender真實模型完整指南.md`
        - **購買資源**：`3D模型資源與測試.md`
        - **方案比較**：`3D方案詳細比較.md`
        """)

    print("✅ Web 介面創建完成")
    print()

    return demo


if __name__ == "__main__":
    print()
    print("🚀 啟動測試伺服器...")
    print()
    print("=" * 70)
    print("📱 請開啟瀏覽器，訪問：http://127.0.0.1:7860")
    print("=" * 70)
    print()
    print("💡 提示：")
    print("   - 如果模型載入失敗，請確認 assets/models/duv_machine.glb 存在")
    print("   - 可以先到 TurboSquid 或 Sketchfab 下載測試模型")
    print("   - 按 Ctrl+C 停止伺服器")
    print()
    print("=" * 70)
    print()

    try:
        demo = test_3d_visualization()
        demo.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            show_error=True
        )
    except Exception as e:
        print()
        print("❌ 啟動失敗:", str(e))
        print()
        print("常見原因：")
        print("  1. Port 7860 已被佔用 → 關閉其他 Gradio 應用")
        print("  2. gradio 未安裝 → 執行: pip install gradio")
        print("  3. 模組匯入錯誤 → 檢查 interface 資料夾結構")
        print()
