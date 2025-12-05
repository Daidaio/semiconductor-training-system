"""
快速啟動腳本
一鍵啟動訓練系統
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """檢查必要套件"""
    print("🔍 檢查系統需求...")

    required_packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'gradio': 'gradio'
    }

    missing = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} (未安裝)")
            missing.append(package_name)

    if missing:
        print(f"\n⚠️  缺少套件: {', '.join(missing)}")
        print("請執行: pip install -r requirements.txt")
        return False

    print("✅ 所有套件已安裝\n")
    return True

def check_data():
    """檢查資料集"""
    print("📂 檢查資料集...")

    # 尋找 SECOM 資料
    possible_paths = [
        "../uci-secom.csv",
        "../../uci-secom.csv",
        "data/uci-secom.csv",
        "uci-secom.csv"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"  ✅ 找到資料集: {path}\n")
            return path

    print("  ❌ 找不到 uci-secom.csv")
    print("\n請下載 SECOM 資料集並放置到以下位置之一:")
    for path in possible_paths:
        print(f"  - {path}")
    return None

def main():
    """主程式"""
    print("=" * 60)
    print("🎓 半導體設備故障處理訓練系統")
    print("   Semiconductor Equipment Fault Handling Training System")
    print("=" * 60)
    print()

    # 檢查需求
    if not check_requirements():
        sys.exit(1)

    # 檢查資料
    secom_path = check_data()
    if not secom_path:
        sys.exit(1)

    # 啟動系統
    print("🚀 啟動訓練系統...\n")

    try:
        # 添加路徑
        sys.path.insert(0, str(Path(__file__).parent))

        from interface.gradio_app import create_interface

        # 建立介面
        demo = create_interface(secom_path)

        print("=" * 60)
        print("✅ 系統啟動成功！")
        print("=" * 60)
        print()
        print("📱 開啟瀏覽器訪問: http://localhost:7860")
        print("⌨️  按 Ctrl+C 停止系統")
        print()

        # 啟動 Gradio
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True
        )

    except Exception as e:
        print(f"\n❌ 系統啟動失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
