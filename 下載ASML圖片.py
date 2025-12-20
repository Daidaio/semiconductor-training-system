# -*- coding: utf-8 -*-
"""
自動下載 ASML DUV 設備圖片
"""

import requests
from pathlib import Path


def download_asml_image():
    """下載 ASML TWINSCAN NXT:1980Di 官方圖片"""

    # ASML 官方圖片 URL
    image_url = "https://edge.sitecorecloud.io/asmlnetherlaaea-asmlcom-prd-5369/media/project/asmlcom/asmlcom/asml/images/products/duv-lithography-systems/twinscan-nxt1980di.png?h=1080&iar=0&w=1920"

    # 目標路徑
    output_dir = Path(__file__).parent / "interface" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "asml_duv.png"

    print("=" * 60)
    print("下載 ASML DUV 設備圖片")
    print("=" * 60)
    print()
    print(f"來源：ASML 官方網站")
    print(f"設備：TWINSCAN NXT:1980Di")
    print(f"解析度：1920x1080 px")
    print()
    print(f"下載中...")

    try:
        # 下載圖片
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # 儲存圖片
        with open(output_path, 'wb') as f:
            f.write(response.content)

        print()
        print("[OK] 下載成功！")
        print()
        print(f"圖片已儲存至：{output_path}")
        print()
        print("下一步：")
        print("1. 執行切換工具：python 切換視覺化模式.py")
        print("2. 選擇模式 1（真實照片模式）")
        print("3. 啟動系統：python start_simulation.py")
        print()

        return True

    except requests.exceptions.RequestException as e:
        print()
        print(f"[Error] 下載失敗：{e}")
        print()
        print("替代方案：")
        print("1. 手動訪問 ASML 官網：")
        print("   https://www.asml.com/en/products/duv-lithography-systems/twinscan-nxt1980di")
        print("2. 右鍵點擊設備圖片 → 另存圖片")
        print(f"3. 儲存至：{output_path}")
        print()

        return False

    except Exception as e:
        print()
        print(f"[Error] 發生錯誤：{e}")
        print()
        return False


if __name__ == "__main__":
    try:
        download_asml_image()
    except KeyboardInterrupt:
        print("\n已取消下載")
    except Exception as e:
        print(f"\n錯誤：{e}")
        import traceback
        traceback.print_exc()
