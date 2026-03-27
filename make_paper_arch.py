"""
論文用系統架構圖 — 白底黑字，簡潔學術風格
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

plt.rcParams['font.family'] = ['Microsoft JhengHei','Microsoft YaHei','DFKai-SB','DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(14, 22))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')
ax.set_xlim(0, 14)
ax.set_ylim(0, 22)
ax.axis('off')

# ── helpers ──────────────────────────────────────────────────────────────────
def rbox(x, y, w, h, title, items=None, dark=False):
    """白底黑字方框（dark=True → 深灰底白字，用於標題行）"""
    fc = '#2C2C2C' if dark else 'white'
    tc = 'white'   if dark else '#1A1A1A'
    ec = '#2C2C2C'
    r = FancyBboxPatch((x,y), w, h,
                       boxstyle='square,pad=0', lw=1.2,
                       edgecolor=ec, facecolor=fc, zorder=2)
    ax.add_patch(r)
    title_lines = str(title).split('\n')
    if items:
        # 標題可能多行：從頂部往下排
        for li, tl in enumerate(title_lines):
            ax.text(x+w/2, y+h-0.2-li*0.28, tl,
                    ha='center', va='top', fontsize=9.5,
                    fontweight='bold', color=tc, zorder=3)
        top_used = 0.2 + len(title_lines)*0.28
        for i, it in enumerate(items):
            ax.text(x+w/2, y+h-top_used-0.1-i*0.28, it,
                    ha='center', va='top', fontsize=8.0,
                    color='#1A1A1A', zorder=3)
    else:
        # 無 sub-items：標題置中，多行用 \n 自然換行
        ax.text(x+w/2, y+h/2, '\n'.join(title_lines),
                ha='center', va='center', fontsize=9.5,
                fontweight='bold', color=tc, zorder=3,
                multialignment='center', linespacing=1.5)

def hdr(x, y, w, h, text):
    """區塊標題欄（灰底）"""
    r = FancyBboxPatch((x,y), w, h,
                       boxstyle='square,pad=0', lw=0,
                       edgecolor='none', facecolor='#ECECEC', zorder=2)
    ax.add_patch(r)
    ax.text(x+w/2, y+h/2, text,
            ha='center', va='center', fontsize=9,
            fontweight='bold', color='#1A1A1A', zorder=3,
            style='italic')

def grp(x, y, w, h, label=''):
    """群組外框"""
    r = FancyBboxPatch((x,y), w, h,
                       boxstyle='square,pad=0', lw=1.5,
                       edgecolor='#444444', facecolor='none', zorder=1)
    ax.add_patch(r)
    if label:
        ax.text(x+0.12, y+h+0.04, label,
                ha='left', va='bottom', fontsize=9,
                fontweight='bold', color='#1A1A1A')

def arr(x1, y1, x2, y2, label='', double=False):
    style = '<->' if double else '->'
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle=style, color='#333333',
                                lw=1.5, mutation_scale=14),
                zorder=0)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx+0.1, my, label, fontsize=8,
                color='#444444', va='center', style='italic')

def arr_curved(x1,y1,x2,y2,rad=0.3,label=''):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle='->', color='#555555', lw=1.2,
                                connectionstyle=f'arc3,rad={rad}'))
    if label:
        mx,my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx+0.1, my, label, fontsize=7.5, color='#555', style='italic')

# ════════════════════════════════════════════════════════════════════════════
# 標題
# ════════════════════════════════════════════════════════════════════════════
ax.text(7, 21.7, '圖 X　系統整體架構圖',
        ha='center', va='center', fontsize=14,
        fontweight='bold', color='#1A1A1A')
ax.plot([1.0, 13.0], [21.45, 21.45], color='#1A1A1A', lw=1.2)

# ════════════════════════════════════════════════════════════════════════════
# ① 資料來源  y=19.3~21.25
# ════════════════════════════════════════════════════════════════════════════
grp(0.8, 19.3, 12.4, 1.95, '① 資料來源')
hdr(0.8, 20.87, 12.4, 0.38, '資料來源  Data Source')

rbox(1.0, 19.4, 5.5, 1.5, 'UCI SECOM 製程資料集',
     ['1,567 wafer samples  ·  590 sensor features',
      'Pass 1,463  /  Fail 104  ·  UCI ML Repository, 2008'])

rbox(7.5, 19.4, 5.5, 1.5, '設備數位孿生\nLithography Digital Twin',
     ['590 感測器模擬',
      '製程狀態即時追蹤'])

# ════════════════════════════════════════════════════════════════════════════
# ② AI 導師系統  y=16.2~18.7   (① bottom 19.3 → ② top 18.7, gap=0.6)
# ════════════════════════════════════════════════════════════════════════════
arr(7.0, 19.3, 7.0, 18.7)

grp(0.8, 16.2, 12.4, 2.5, '② AI 導師系統')
hdr(0.8, 18.32, 12.4, 0.38, 'AI 導師系統  AI Mentor System  (Qwen LLM)')

rbox(1.0, 16.3, 3.3, 1.85, 'AIScenarioMentor',
     ['Qwen 大型語言模型（本地端）',
      '蘇格拉底式對話引導',
      '場景脈絡感知回應'])

rbox(5.0, 16.3, 3.5, 1.85, 'Diagnostic Agent\nOperation Agent',
     ['故障根本原因分析',
      '逐步操作指引',
      '維修 SOP 管理'])

rbox(9.1, 16.3, 3.9, 1.85, 'Adaptive Teaching\nCompetency Assessment',
     ['挑戰≥8.5 ／ 標準≥6.5',
      '鷹架≥4.0 ／ 補救<4.0',
      '學習歷程紀錄'])

arr(4.3, 17.225, 5.0, 17.225)
arr(8.5, 17.225, 9.1, 17.225)

# ════════════════════════════════════════════════════════════════════════════
# ③ 後端服務層  y=14.1~15.5   (② bottom 16.2 → ③ top 15.5, gap=0.7)
# ════════════════════════════════════════════════════════════════════════════
arr(7.0, 16.2, 7.0, 15.5)

grp(0.8, 14.1, 12.4, 1.3, '③ 後端服務層')
hdr(0.8, 15.02, 12.4, 0.38, '後端服務層  Backend Service  (Python http.server · Port 8765)')

rbox(1.0, 14.2, 12.0, 0.7,
     'REST API：/api/start  ·  /api/chat  ·  /api/hmi  ·  /api/fault')

# ════════════════════════════════════════════════════════════════════════════
# ④ 使用者介面層  y=10.7~13.3   (③ bottom 14.1 → ④ top 13.3, gap=0.8)
# ════════════════════════════════════════════════════════════════════════════
arr(7.0, 14.1, 7.0, 13.3, double=True)

grp(0.8, 10.7, 12.4, 2.6, '④ 使用者介面層')
hdr(0.8, 12.92, 12.4, 0.38, '使用者介面層  User Interface  (Three.js WebGL · viewer.html)')

rbox(1.0, 10.8, 3.7, 1.85, '3D 互動環境',
     ['ASML DUV 3D 模型（GLB）',
      'PointerLock 第一人稱視角',
      'WASD 移動  ·  [E] 互動'])

rbox(5.3, 10.8, 3.5, 1.85, 'HMI 虛擬控制面板',
     ['感測器讀值即時顯示',
      'CDU Map  ·  CD 趨勢圖',
      '警報與系統狀態'])

rbox(9.4, 10.8, 3.7, 1.85, 'AI 對話  &  SOP 面板',
     ['Chat 對話框 [C]',
      '維修 SOP 步驟引導',
      '警報通知  ·  操作回饋'])

arr(4.7, 11.725, 5.3, 11.725)
arr(8.8, 11.725, 9.4, 11.725)

# ════════════════════════════════════════════════════════════════════════════
# ⑤ 訓練流程  y=7.5~10.0   (④ bottom 10.7 → ⑤ top 10.0, gap=0.7)
# ════════════════════════════════════════════════════════════════════════════
arr(7.0, 10.7, 7.0, 10.0)

grp(0.8, 7.5, 12.4, 2.4, '⑤ 訓練流程')
hdr(0.8, 9.52, 12.4, 0.38, '訓練流程  Training Workflow')

rbox(1.0, 7.6, 5.5, 1.75, '階段一：理論學習',
     ['DUV 微影原理  ·  製程參數',
      'AI 蘇格拉底問答',
      '通過門檻：理論測驗 ≥ 70 分'])

rbox(7.3, 7.6, 5.7, 1.75, '階段二：實機操作',
     ['3D 環境探索與零件互動',
      '故障診斷（7 種）·  維修 SOP',
      '通過門檻：實作評量 ≥ 80 分'])

arr(6.5, 8.475, 7.3, 8.475)

# ════════════════════════════════════════════════════════════════════════════
# ⑥ 評分系統  y=4.0~7.0   (⑤ bottom 7.5 → ⑥ top 7.0, gap=0.5)
# ════════════════════════════════════════════════════════════════════════════
arr(7.0, 7.5, 7.0, 7.0)

grp(0.8, 4.0, 12.4, 2.9, '⑥ 評分系統')
hdr(0.8, 6.52, 12.4, 0.38, '評分系統  Scoring System  (ScoringSystem)')

rbox(1.0, 4.1, 3.5, 2.1, '診斷準確性\nDiagnostic Accuracy',
     ['配分：30%',
      '故障類型正確判斷',
      '信心度加權計算'])

rbox(5.1, 4.1, 3.5, 2.1, '操作正確性\nOperation Correctness',
     ['配分：40%',
      'SOP 步驟符合度',
      '操作順序評估'])

rbox(9.4, 4.1, 3.7, 2.1, '安全合規  +  效率\nSafety & Efficiency',
     ['安全合規：30%',
      '時間效率：加分項',
      '等級評定 A / B / C / D / F'])

arr(4.5, 5.15, 5.1, 5.15)
arr(8.6, 5.15, 9.4, 5.15)

# ════════════════════════════════════════════════════════════════════════════
# 右側資料流標籤
# ════════════════════════════════════════════════════════════════════════════
for (y, lbl) in [(17.45, 'AI 回應 / SOP'),
                 (14.8,  'JSON API 通訊'),
                 (12.0,  '渲染 / 顯示'),
                 (9.1,   '訓練事件'),
                 (5.5,   '評分輸入')]:
    ax.text(13.4, y, lbl, fontsize=8, color='#555555',
            style='italic', ha='left', va='center',
            bbox=dict(fc='none', ec='#AAAAAA', lw=0.7,
                      boxstyle='round,pad=0.2'))
    ax.plot([13.1, 13.4], [y, y], color='#AAAAAA', lw=0.8, ls='--')

# ════════════════════════════════════════════════════════════════════════════
# 儲存
# ════════════════════════════════════════════════════════════════════════════
fig.savefig(
    r"c:\Users\user\Desktop\在職碩\OneDrive - 長庚大學\長庚碩班\論文\系統架構圖_論文用.png",
    dpi=200, bbox_inches='tight', facecolor='white'
)
print("Saved.")
plt.close(fig)
