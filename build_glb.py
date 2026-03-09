# -*- coding: utf-8 -*-
"""
build_glb.py
修改 asml_duv.glb：
  1. 把控制面板（Screen / Keyboard / LED / Logo）移到機台左側面（-X 方向）
  2. 新增 Reticle_Stage + Reticle 節點（光罩載台）
"""
import math, struct, json, copy
import pygltflib
from pathlib import Path

GLB = Path("static/asml_duv.glb")
gltf = pygltflib.GLTF2().load(str(GLB))

# ── 四元數工具 ────────────────────────────────────────────────────────────────
def quat_y(deg):
    """繞 Y 軸旋轉 deg 度的四元數 [x,y,z,w]"""
    r = math.radians(deg) / 2
    return [0.0, round(math.sin(r), 6), 0.0, round(math.cos(r), 6)]

# ── 1. 移動控制面板到機台左側面（-X 朝外）────────────────────────────────────
# Cabinet_Main 中心 x=-2.12；面板原本在 x=-1.72（內側，朝向機台 +x 方向）
# 左側面 x = -2.12 - 0.40 = -2.52，旋轉 180° 讓面朝 -x
CAB_CX = -2.12
PANEL_X = CAB_CX  # 面板 x 居中在機台左側
LEFT_FACE_X = -2.53  # 稍微突出左側面

# 原本面板法線朝 +x，旋轉 180°Y 讓它朝 -x
ROT180Y = quat_y(180)  # [0, 1, 0, 0]

# 各元素在 z 軸上的偏移量（製造立體感）
PANEL_ITEMS = {
    # name:  [x,         y,      z,     rotation]
    'Cabinet_Panel': [LEFT_FACE_X,      1.00,  -0.10, ROT180Y],
    'Screen':        [LEFT_FACE_X-0.01, 1.22,  -0.05, ROT180Y],
    'Keyboard':      [LEFT_FACE_X-0.01, 0.96,  -0.06, ROT180Y],
    'LED_0':         [LEFT_FACE_X-0.02, 1.56,   0.10, ROT180Y],
    'LED_1':         [LEFT_FACE_X-0.02, 1.635,  0.10, ROT180Y],
    'LED_2':         [LEFT_FACE_X-0.02, 1.71,   0.10, ROT180Y],
    'ASML_Logo':     [LEFT_FACE_X-0.01, 1.48,   0.25, ROT180Y],
    'Model_Label':   [LEFT_FACE_X-0.01, 1.33,   0.25, ROT180Y],
}

moved = []
for node in gltf.nodes:
    if node.name in PANEL_ITEMS:
        pos = PANEL_ITEMS[node.name]
        node.translation = [pos[0], pos[1], pos[2]]
        node.rotation    = pos[3]
        moved.append(node.name)

print(f"[移動] {moved}")

# ── 2. 新增 Reticle_Stage + Reticle 節點（純 JSON node，無幾何）────────────────
# 在 Three.js 中用程式建立幾何，GLB 只記錄名稱供參考
# 光罩載台位置：投影鏡組 POB 頂部上方（POB_Top_Cap 在 y=1.97）
# Reticle_Stage ≈ y=2.05，z=-0.1（POB 正上方）

import pygltflib

new_nodes = [
    pygltflib.Node(
        name="Reticle_Stage",
        translation=[0.10, 2.05, -0.10],
        mesh=None,
        children=[]
    ),
    pygltflib.Node(
        name="Reticle",
        translation=[0.10, 2.10, -0.10],
        mesh=None,
        children=[]
    ),
    pygltflib.Node(
        name="Robot_Arm_Base",
        translation=[-1.47, 0.55, 0.52],
        mesh=None,
        children=[]
    ),
    pygltflib.Node(
        name="Robot_Arm_Link",
        translation=[-1.47, 0.82, 0.52],
        mesh=None,
        children=[]
    ),
    pygltflib.Node(
        name="Robot_Wafer",
        translation=[-1.47, 0.85, 0.52],
        mesh=None,
        children=[]
    ),
]

for nn in new_nodes:
    gltf.nodes.append(nn)
    gltf.scenes[0].nodes.append(len(gltf.nodes) - 1)

print(f"[新增節點] {[n.name for n in new_nodes]}")

# ── 儲存 ─────────────────────────────────────────────────────────────────────
gltf.save(str(GLB))
print(f"[OK] Saved to {GLB}")

# 驗證
gltf2 = pygltflib.GLTF2().load(str(GLB))
print(f"[驗證] Nodes: {len(gltf2.nodes)}，Animations: {len(gltf2.animations)}")
for n in gltf2.nodes:
    if n.name in list(PANEL_ITEMS.keys()) + [nn.name for nn in new_nodes]:
        print(f"  {n.name}: t={[round(x,3) for x in n.translation]} r={[round(x,3) for x in (n.rotation or [])]}")
