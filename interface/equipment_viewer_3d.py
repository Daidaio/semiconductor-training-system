"""
ASML TWINSCAN NXT:870 互動式 3D 設備展示
整合 Gradio Model3D 元件
"""

import gradio as gr
from pathlib import Path

# GLB 檔案路徑
GLB_PATH = str(Path(__file__).parent.parent / "static" / "asml_duv.glb")

# 各元件說明資訊
COMPONENT_INFO = {
    "Projection Optics (POB)": {
        "zh": "投影物鏡組",
        "desc": "包含多層精密透鏡，將光罩圖案縮小投影至晶圓表面。縮小倍率通常為 4:1。透鏡材質為超純石英玻璃（熔融二氧化矽），對 193nm 深紫外光具高穿透率。",
        "params": "數值孔徑（NA）: 1.35（浸潤式）\n解析度: < 38nm",
        "icon": "🔬"
    },
    "Illumination System": {
        "zh": "照明系統",
        "desc": "將 ArF 準分子雷射光束整形並均勻化，提供穩定的光強度分布。支援多種照明模式（環形、偶極、四極）以優化解析度與景深。",
        "params": "波長: 193nm\n照明模式: 傳統/環形/偶極/四極",
        "icon": "💡"
    },
    "Wafer Stage": {
        "zh": "晶圓台",
        "desc": "高精度六軸定位平台，在曝光過程中精確移動晶圓。採用磁浮技術（無摩擦），定位精度達奈米等級。掃描速度可達 750mm/s。",
        "params": "定位精度: < 2nm\n掃描速度: 750mm/s\n晶圓尺寸: 300mm",
        "icon": "🎯"
    },
    "Immersion Hood": {
        "zh": "浸潤式水頭",
        "desc": "NXT 系列的核心技術。在投影物鏡底端與晶圓之間充填超純水（n=1.44），提高有效數值孔徑，突破空氣介質的解析度極限。",
        "params": "介質: 超純水（n=1.44）\n有效 NA: 最高 1.35",
        "icon": "💧"
    },
    "193nm ArF DUV Laser": {
        "zh": "193nm ArF 準分子雷射",
        "desc": "深紫外光（DUV）光源，波長 193nm。氬氟化物（ArF）準分子雷射提供高功率、高重複率的脈衝紫外光。光束經光纖或反射鏡傳導至照明系統。",
        "params": "波長: 193nm\n能量穩定性: < 0.1%\n重複率: 6000Hz",
        "icon": "⚡"
    },
    "ArF Excimer Laser": {
        "zh": "ArF 準分子雷射光源箱",
        "desc": "雷射光源主機，通常與曝光主機分離放置以隔絕振動。內部包含放電腔、光學諧振腔與波長選擇元件，輸出高純度 193nm 雷射光束。",
        "params": "輸出功率: > 90W\n光束品質: M² < 1.3",
        "icon": "🔴"
    },
    "FOUP Port": {
        "zh": "前開式晶圓傳送盒接口",
        "desc": "Front Opening Unified Pod（FOUP）是半導體製程中的標準晶圓載具。透過自動化機械手臂（EFEM）將晶圓從 FOUP 取出並傳送至曝光腔體。",
        "params": "容量: 25片晶圓/FOUP\n傳送方式: EFEM 機械手臂",
        "icon": "📦"
    },
}

def create_3d_viewer_tab():
    """建立 3D 設備展示頁籤"""

    with gr.Tab("🏭 3D 設備展示"):
        gr.Markdown("""
        ## ASML TWINSCAN NXT:870 互動式 3D 模型
        **操作說明：** 滑鼠左鍵旋轉 | 滾輪縮放 | 右鍵平移
        點選下方元件按鈕查看詳細說明。
        """)

        with gr.Row():
            # 左側：3D 模型
            with gr.Column(scale=3):
                model_viewer = gr.Model3D(
                    value=GLB_PATH if Path(GLB_PATH).exists() else None,
                    label="ASML TWINSCAN NXT:870",
                    camera_position=(45, 60, 5),
                    height=520,
                )
                if not Path(GLB_PATH).exists():
                    gr.Markdown(
                        "⚠️ **GLB 檔案未找到**，請先從 Blender 匯出 `asml_duv.glb` 到 `static/` 資料夾。",
                    )

            # 右側：元件資訊面板
            with gr.Column(scale=2):
                gr.Markdown("### 元件說明")
                component_title = gr.Markdown("← 點選左側按鈕查看元件資訊")
                component_detail = gr.Markdown("")

        # 元件選擇按鈕
        gr.Markdown("### 點選元件查看說明")
        with gr.Row():
            buttons = []
            for name, info in COMPONENT_INFO.items():
                btn = gr.Button(
                    f"{info['icon']} {info['zh']}",
                    size="sm",
                    variant="secondary"
                )
                buttons.append((btn, name))

        def show_component(name):
            info = COMPONENT_INFO[name]
            title = f"## {info['icon']} {info['zh']}\n**{name}**"
            detail = f"""
**功能說明：**
{info['desc']}

---
**關鍵規格：**
```
{info['params']}
```
"""
            return title, detail

        # 綁定按鈕事件
        for btn, name in buttons:
            btn.click(
                fn=lambda n=name: show_component(n),
                outputs=[component_title, component_detail]
            )

    return model_viewer


def launch_standalone():
    """獨立啟動 3D 展示介面"""
    with gr.Blocks(title="ASML 設備 3D 展示") as demo:
        gr.Markdown("""
        # 🏭 ASML TWINSCAN NXT:870 互動式 3D 展示
        半導體微影製程設備教學展示系統
        """)
        create_3d_viewer_tab()

    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        inbrowser=True
    )


if __name__ == "__main__":
    launch_standalone()
