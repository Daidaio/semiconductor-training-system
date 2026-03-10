# -*- coding: utf-8 -*-
"""
reposition_beams.py
把 GLB 裡靜態光束節點移到正確的高度：
  現況：Beam_H2 在 y=1.2（鏡組中段）
  目標：水平段 Beam_H2 移到 y=2.35（照明系統頂部出口），
        再垂直往下 Beam_V2 貫穿光罩 + 鏡組到晶圓

光路（修正後）：
  Laser_Box → Beam_H1(y=1.8) → Mirror1[0.85,1.8]
    → Beam_V1(UP 0.85 : y=1.8→2.35) → Mirror2[0.85,2.35]
    → Beam_H2(LEFT y=2.35 : x=0.85→0.1) → Mirror3[0.1,2.35]
    → Beam_V2(DOWN 0.1 : y=2.35→0.44) → Beam_Spot[0.1,0.44]
"""
import pygltflib
from pathlib import Path

GLB = Path("static/asml_duv.glb")
gltf = pygltflib.GLTF2().load(str(GLB))

# ── 原始尺寸（由原始節點位置推算）────────────────────────────────────────────
# V1 原本：Mirror1(y=1.8) → Mirror2(y=1.2)，長度 0.60，center y=1.50，scale=[1,1,1]
# V2 原本：Mirror3(y=1.2) → Beam_Spot(y=0.44)，長度 0.76，center y=0.82，scale=[1,1,1]
V1_ORIG_LEN = 0.60   # 模型自然長度
V2_ORIG_LEN = 0.76   # 模型自然長度

# ── 新的關鍵座標 ──────────────────────────────────────────────────────────────
TOP_Y  = 2.35   # 照明系統頂部出口 / 水平束高度
BOT_Y  = 0.44   # Beam_Spot（晶圓層），不動
M1_Y   = 1.80   # Mirror1，不動

# V1 新路徑：從 Mirror1(y=1.8) 往上到 Mirror2(y=2.35)
v1_new_len    = TOP_Y - M1_Y           # 0.55
v1_center_y   = (TOP_Y + M1_Y) / 2    # 2.075
v1_scale_y    = v1_new_len / V1_ORIG_LEN  # 0.917

# V2 新路徑：從 Mirror3(y=2.35) 往下到 Beam_Spot(y=0.44)
v2_new_len    = TOP_Y - BOT_Y          # 1.91
v2_center_y   = (TOP_Y + BOT_Y) / 2   # 1.395
v2_scale_y    = v2_new_len / V2_ORIG_LEN  # 2.513

print(f"V1: len={v1_new_len:.3f}  center_y={v1_center_y:.3f}  scale_y={v1_scale_y:.4f}")
print(f"V2: len={v2_new_len:.3f}  center_y={v2_center_y:.3f}  scale_y={v2_scale_y:.4f}")

# ── 節點更新表 ────────────────────────────────────────────────────────────────
UPDATES = {
    # V1：往上延伸到 TOP_Y，中心上移
    'Beam_V1': {
        'translation': [0.85, v1_center_y, -0.1],
        'scale':       [1.0, round(v1_scale_y, 4), 1.0],
    },
    # Mirror2：移到照明系統頂部出口
    'Mirror2': {
        'translation': [0.85, TOP_Y, -0.1],
    },
    # H2：高度升到 TOP_Y，X 路徑不變（0.85→0.1，center=0.475）
    'Beam_H2': {
        'translation': [0.475, TOP_Y, -0.1],
    },
    # Mirror3：移到光學主軸頂部
    'Mirror3': {
        'translation': [0.1, TOP_Y, -0.1],
    },
    # V2：從 TOP_Y 往下貫穿整個光學柱到晶圓，拉長
    'Beam_V2': {
        'translation': [0.1, v2_center_y, -0.1],
        'scale':       [1.0, round(v2_scale_y, 4), 1.0],
    },
    # Illum_Barrel：跟著移到 V1 中段位置（視覺上包覆 V1 束）
    'Illum_Barrel': {
        'translation': [0.85, v1_center_y, -0.1],
    },
}

changed = []
for node in gltf.nodes:
    if node.name in UPDATES:
        upd = UPDATES[node.name]
        if 'translation' in upd:
            node.translation = upd['translation']
        if 'scale' in upd:
            node.scale = upd['scale']
        changed.append(node.name)

print(f"[更新] {changed}")

gltf.save(str(GLB))
print(f"[OK] Saved → {GLB}")

# 驗證
gltf2 = pygltflib.GLTF2().load(str(GLB))
print("\n[驗證] 光束節點位置：")
for n in gltf2.nodes:
    if n.name in UPDATES or n.name in ('Mirror1', 'Beam_H1', 'Beam_Spot', 'POB_Top_Cap'):
        t = [round(x, 3) for x in (n.translation or [0,0,0])]
        s = [round(x, 3) for x in (n.scale or [1,1,1])]
        print(f"  {n.name:20s} t={t}  s={s}")
