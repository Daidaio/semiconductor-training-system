# -*- coding: utf-8 -*-
"""
測試設備狀態顯示功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from interface.simulation_interface import SimulationTrainingSystem

# 找資料集
secom_path = None
for path in ["../uci-secom.csv", "../../uci-secom.csv", "uci-secom.csv"]:
    if Path(path).exists():
        secom_path = path
        break

if not secom_path:
    print("[ERROR] 找不到 uci-secom.csv")
    sys.exit(1)

print("=" * 60)
print("測試設備狀態顯示功能")
print("=" * 60)

system = SimulationTrainingSystem(secom_path, use_ai_mentor=True)

# 開始新情境
print("\n[測試 1] 開始新情境...")
eq, dash, eq_status, conv_history, log = system.start_new_scenario("medium")

print(f"  [OK] 設備圖: {len(eq)} 字元")
print(f"  [OK] 儀表板: {len(dash)} 字元")
print(f"  [OK] 設備狀態: {len(eq_status)} 字元")
print(f"  [OK] 對話歷史: {len(conv_history)} 條訊息")

# 檢查設備狀態初始內容
if "尚未檢查任何設備" in eq_status:
    print("  [OK] 設備狀態初始訊息正確")
else:
    print("  [FAIL] 設備狀態初始訊息錯誤")
    print(f"    內容: {eq_status[:200]}")

# 執行檢查動作
print("\n[測試 2] 執行檢查動作：檢查冷卻水...")
user_input, eq, dash, eq_status, conv_history, log = system.process_user_input(
    "檢查冷卻水", eq, dash, eq_status, conv_history, log
)

print(f"  [OK] 設備狀態更新: {len(eq_status)} 字元")

# 檢查是否包含冷卻系統資訊
if "冷卻系統" in eq_status:
    print("  [OK] 設備狀態包含冷卻系統資訊")
    # 提取關鍵資訊
    if "流量" in eq_status:
        print("  [OK] 包含流量資訊")
    if "溫度" in eq_status:
        print("  [OK] 包含溫度資訊")
else:
    print("  [FAIL] 設備狀態缺少冷卻系統資訊")
    print(f"    內容: {eq_status[:300]}")

# 檢查對話歷史是否保持乾淨（檢查動作不應加入對話）
print(f"\n[測試 3] 檢查對話歷史（檢查動作應該靜默）...")
print(f"  對話歷史長度: {len(conv_history)}")
if len(conv_history) == 1:  # 應該只有初始訊息
    print("  [OK] 檢查動作沒有加入對話歷史（正確）")
else:
    print(f"  [FAIL] 對話歷史意外增加（預期 1 條，實際 {len(conv_history)} 條）")

# 執行詢問動作
print("\n[測試 4] 執行詢問動作：流量正常嗎...")
user_input, eq, dash, eq_status, conv_history, log = system.process_user_input(
    "流量正常嗎", eq, dash, eq_status, conv_history, log
)

# 檢查對話歷史是否增加（詢問動作應該加入對話）
print(f"  對話歷史長度: {len(conv_history)}")
if len(conv_history) > 1:
    print("  [OK] 詢問動作加入對話歷史（正確）")
    # 檢查最後一條是否是學長回應
    last_msg = conv_history[-1]
    if "學長" in last_msg.get("content", ""):
        print("  [OK] 包含學長回應")
    else:
        print(f"  [?] 最後一條訊息: {last_msg.get('content', '')[:100]}")
else:
    print("  [FAIL] 詢問動作沒有加入對話歷史（錯誤）")

# 再次檢查設備
print("\n[測試 5] 檢查真空系統...")
user_input, eq, dash, eq_status, conv_history, log = system.process_user_input(
    "檢查真空", eq, dash, eq_status, conv_history, log
)

# 檢查是否包含真空系統資訊
if "真空系統" in eq_status:
    print("  [OK] 設備狀態包含真空系統資訊")
    if "壓力" in eq_status:
        print("  [OK] 包含壓力資訊")
else:
    print("  [FAIL] 設備狀態缺少真空系統資訊")

# 檢查設備狀態是否累積多個檢查結果
if "冷卻系統" in eq_status and "真空系統" in eq_status:
    print("  [OK] 設備狀態正確累積多個檢查結果")
else:
    print("  [FAIL] 設備狀態沒有累積檢查結果")
    print(f"    內容: {eq_status[:500]}")

print("\n" + "=" * 60)
print("測試完成")
print("=" * 60)
