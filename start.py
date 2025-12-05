# -*- coding: utf-8 -*-
"""
Simple startup script without emoji (Windows compatible)
"""

import os
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("Semiconductor Equipment Training System")
    print("=" * 60)
    print()

    # Check packages
    print("Checking packages...")
    required = ['pandas', 'numpy', 'gradio']
    missing = []

    for pkg in required:
        try:
            __import__(pkg)
            print(f"  [OK] {pkg}")
        except ImportError:
            print(f"  [FAIL] {pkg}")
            missing.append(pkg)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: pip install pandas numpy gradio")
        sys.exit(1)

    print("[OK] All packages installed\n")

    # Check data
    print("Checking dataset...")
    paths = ["../uci-secom.csv", "../../uci-secom.csv", "uci-secom.csv"]
    secom_path = None

    for path in paths:
        if os.path.exists(path):
            print(f"  [OK] Found: {path}\n")
            secom_path = path
            break

    if not secom_path:
        print("  [FAIL] Cannot find uci-secom.csv")
        print("\nPlease download from Kaggle and place it in project directory")
        sys.exit(1)

    # Start system
    print("Starting training system...\n")

    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from interface.gradio_app import create_interface

        demo = create_interface(secom_path)

        print("=" * 60)
        print("[SUCCESS] System started!")
        print("=" * 60)
        print()
        print("Open browser: http://localhost:7860")
        print("Press Ctrl+C to stop")
        print()

        demo.launch(
            server_name="127.0.0.1",
            server_port=None,  # 自動尋找可用 port
            share=False,
            show_error=True,
            quiet=False
        )

    except Exception as e:
        print(f"\n[ERROR] Failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
