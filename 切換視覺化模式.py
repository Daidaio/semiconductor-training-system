# -*- coding: utf-8 -*-
"""
快速切換設備視覺化模式
"""

import sys
from pathlib import Path

# 視覺化模式說明
MODES = {
    "1": {
        "name": "真實照片模式",
        "class": "PhotoEquipmentVisualizer",
        "import": "from interface.equipment_visualizer_photo import PhotoEquipmentVisualizer",
        "init": 'PhotoEquipmentVisualizer(use_local_image=True, image_path="interface/images/asml_duv.jpg")',
        "description": "使用真實的 ASML DUV 設備照片 + 動態故障標記"
    },
    "2": {
        "name": "超真實 SVG 模式",
        "class": "RealisticEquipmentVisualizer",
        "import": "from interface.equipment_visualizer_realistic import RealisticEquipmentVisualizer",
        "init": "RealisticEquipmentVisualizer()",
        "description": "照片級 SVG 繪製，包含真實材質和光影效果"
    },
    "3": {
        "name": "簡潔 SVG 模式",
        "class": "EquipmentVisualizer",
        "import": "from interface.equipment_visualizer import EquipmentVisualizer",
        "init": "EquipmentVisualizer()",
        "description": "原始版本，簡潔的示意圖"
    },
    "4": {
        "name": "互動式視覺化模式（推薦）",
        "class": "InteractiveEquipmentVisualizer",
        "import": "from interface.equipment_visualizer_interactive import InteractiveEquipmentVisualizer",
        "init": "InteractiveEquipmentVisualizer()",
        "description": "可點擊部件查看近距離特寫，紅燈標示故障位置"
    }
}


def show_menu():
    """顯示選單"""
    print("=" * 60)
    print("設備視覺化模式切換工具")
    print("=" * 60)
    print()
    for key, mode in MODES.items():
        print(f"{key}. {mode['name']}")
        print(f"   {mode['description']}")
        print()
    print("q. 取消")
    print()


def update_interface_file(mode_key: str):
    """更新 simulation_interface.py 文件"""

    interface_file = Path(__file__).parent / "interface" / "simulation_interface.py"

    if not interface_file.exists():
        print(f"[錯誤] 找不到文件: {interface_file}")
        return False

    # 讀取文件
    with open(interface_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 找到並替換 import 行
    import_line_index = None
    for i, line in enumerate(lines):
        if "equipment_visualizer" in line and "import" in line:
            import_line_index = i
            break

    if import_line_index is None:
        print("[錯誤] 找不到視覺化器的 import 語句")
        return False

    mode = MODES[mode_key]
    lines[import_line_index] = f"{mode['import']}\n"

    # 找到並替換初始化行
    init_line_index = None
    for i, line in enumerate(lines):
        if "self.equipment_visualizer = " in line:
            init_line_index = i
            break

    if init_line_index is None:
        print("[錯誤] 找不到視覺化器的初始化語句")
        return False

    lines[init_line_index] = f"        self.equipment_visualizer = {mode['init']}\n"

    # 寫回文件
    with open(interface_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"[成功] 已切換到: {mode['name']}")
    print(f"[提示] 重新啟動 start_simulation.py 即可看到效果")
    return True


def main():
    """主函數"""
    show_menu()

    choice = input("請選擇模式 (1-4): ").strip()

    if choice.lower() == 'q':
        print("已取消")
        return

    if choice not in MODES:
        print("[錯誤] 無效的選擇")
        return

    mode = MODES[choice]

    # 特殊檢查：如果選擇真實照片模式，檢查照片是否存在
    if choice == "1":
        image_path = Path(__file__).parent / "interface" / "images" / "asml_duv.jpg"
        if not image_path.exists():
            image_path_png = Path(__file__).parent / "interface" / "images" / "asml_duv.png"
            if not image_path_png.exists():
                print()
                print("[警告] 找不到設備照片！")
                print(f"請將 ASML DUV 設備照片放到：")
                print(f"  {image_path}")
                print("或")
                print(f"  {image_path_png}")
                print()
                print("詳細說明請看：interface/images/README.md")
                print()
                cont = input("是否仍要切換到照片模式？(y/n): ").strip().lower()
                if cont != 'y':
                    print("已取消")
                    return

    print()
    print(f"正在切換到: {mode['name']}")
    print()

    if update_interface_file(choice):
        print()
        print("✅ 切換完成！")
        print()
        print("現在執行以下命令啟動系統：")
        print("  python start_simulation.py")
        print()
    else:
        print()
        print("❌ 切換失敗，請檢查錯誤訊息")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已取消")
    except Exception as e:
        print(f"\n[錯誤] {e}")
        import traceback
        traceback.print_exc()
