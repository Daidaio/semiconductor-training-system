# -*- coding: utf-8 -*-
"""
Virtual Fab 第一人稱遊戲介面（完整版）
- PointerLockControls WASD 第一人稱移動
- E 鍵點選部件 → AI 學長即時回應
- 右側常駐 AI 學長對話面板
- 純 Python REST API（不需要 Gradio）
"""

import json
import threading
import functools
import http.server
import types
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from interface.simulation_interface import SimulationTrainingSystem

# ── 路徑 ─────────────────────────────────────────────────────────────────────
_STATIC = Path(__file__).parent.parent / "static"
_GLB_PATH = _STATIC / "asml_duv.glb"

# ── 全局遊戲狀態（REST API 共用）────────────────────────────────────────────
_system_instance: SimulationTrainingSystem = None
_session_lock = threading.Lock()
_session = {
    "started": False,
    "eq": "", "dash": "", "eq_st": "", "msgs": [], "log": "",
}

_server_port: int = 0

# ── REST API + 靜態檔案 HTTP Handler ─────────────────────────────────────────

class _GameHandler(http.server.SimpleHTTPRequestHandler):
    """靜態檔案 + REST API 合一"""

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/status":
            self._api_status()
        elif self.path == "/api/tick":
            self._api_tick()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/start":
            self._api_start()
        elif self.path == "/api/chat":
            self._api_chat()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a):
        pass  # 靜音 access log

    # ── helpers ──────────────────────────────────────────────────────────────

    def _read_json(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n).decode("utf-8")) if n else {}

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _msgs_to_list(self, msgs):
        """Gradio Chatbot [[user,ai],...] → [{role,content},...] 列表"""
        out = []
        for m in (msgs or []):
            if isinstance(m, (list, tuple)) and len(m) >= 2:
                if m[0]: out.append({"role": "user",      "content": str(m[0])})
                if m[1]: out.append({"role": "assistant",  "content": str(m[1])})
            elif isinstance(m, dict):
                out.append(m)
        return out

    def _latest_ai(self, msgs):
        for m in reversed(msgs or []):
            if isinstance(m, (list, tuple)) and len(m) > 1 and m[1]:
                return str(m[1])
            if isinstance(m, dict) and m.get("role") == "assistant":
                return m.get("content", "")
        return ""

    # ── API endpoints ─────────────────────────────────────────────────────────

    def _api_status(self):
        with _session_lock:
            self._json({
                "started": _session["started"],
                "msgs": self._msgs_to_list(_session["msgs"]),
            })

    def _api_tick(self):
        with _session_lock:
            if not _session["started"]:
                self._json({"ok": False, "ai_msg": ""})
                return
            snap = dict(_session)

        eq, dash, eq_st, msgs, log = _system_instance.auto_progress(
            snap["eq"], snap["dash"], snap["eq_st"], snap["msgs"], snap["log"])

        with _session_lock:
            _session.update(eq=eq, dash=dash, eq_st=eq_st, msgs=msgs, log=log)

        ai_msg = self._latest_ai(msgs)
        self._json({"ok": True, "ai_msg": ai_msg,
                    "msgs": self._msgs_to_list(msgs)})

    def _api_start(self):
        data = self._read_json()
        difficulty = data.get("difficulty", "medium")
        eq, dash, eq_st, msgs, log = _system_instance.start_new_scenario(difficulty)

        with _session_lock:
            _session.update(started=True, eq=eq, dash=dash,
                            eq_st=eq_st, msgs=msgs, log=log)

        ai_msg = self._latest_ai(msgs) or "情境已開始，請開始檢查設備。"
        self._json({"ok": True, "ai_msg": ai_msg,
                    "msgs": self._msgs_to_list(msgs)})

    def _api_chat(self):
        data = self._read_json()
        text = data.get("text", "").strip()
        if not text:
            self._json({"ok": False, "ai_msg": ""}); return

        with _session_lock:
            snap = dict(_session)

        _, eq, dash, eq_st, msgs, log = _system_instance.process_user_input(
            text, snap["eq"], snap["dash"], snap["eq_st"],
            snap["msgs"], snap["log"])

        with _session_lock:
            _session.update(eq=eq, dash=dash, eq_st=eq_st, msgs=msgs, log=log)

        ai_msg = self._latest_ai(msgs)
        self._json({"ok": True, "ai_msg": ai_msg,
                    "msgs": self._msgs_to_list(msgs)})


# ── 啟動伺服器 ────────────────────────────────────────────────────────────────

def _start_server(directory: str, port: int = 8765) -> int:
    global _server_port
    if _server_port:
        return _server_port
    handler = functools.partial(_GameHandler, directory=directory)
    for p in range(port, port + 20):
        try:
            srv = http.server.HTTPServer(("127.0.0.1", p), handler)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            _server_port = p
            print(f"[OK] Game server: http://127.0.0.1:{p}/")
            return p
        except OSError:
            continue
    raise RuntimeError("No available port")


# ── viewer.html（嵌入式遊戲）────────────────────────────────────────────────

_VIEWER_HTML = """\
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>ASML Virtual Fab — Operator Training</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:100%;height:100%;overflow:hidden;background:#050d1a;
  font-family:Consolas,"Courier New",monospace;color:#cde;}
/* Three.js canvas — full viewport minus chat panel */
canvas{position:fixed;top:0;left:0;display:block;}

/* ── Loading ── */
#loading-screen{position:fixed;inset:0;background:#050d1a;z-index:900;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;}
#load-title{font-size:16px;letter-spacing:3px;color:#4af;}
#load-pct{font-size:32px;color:#ffa500;}
.bar-wrap{width:280px;height:6px;background:#0a1828;border-radius:3px;}
#load-bar{height:6px;background:linear-gradient(90deg,#4af,#ffa500);
  border-radius:3px;width:0;transition:width .3s;}
#load-sub{font-size:11px;color:#5a8a9a;}

/* ── Start Screen ── */
#start-screen{position:fixed;top:0;left:0;z-index:800;display:none;
  flex-direction:column;align-items:center;justify-content:center;
  gap:22px;background:rgba(5,13,26,.94);}
#start-screen h1{font-size:21px;letter-spacing:3px;color:#4af;text-align:center;}
#start-screen h2{font-size:12px;color:#6ab;letter-spacing:2px;text-align:center;}
.hint{font-size:11px;color:#5a8a9a;text-align:center;line-height:2;max-width:420px;}
.hint b{color:#ffa500;}
#diff-row{display:flex;align-items:center;gap:12px;}
#difficulty{background:#0a1828;border:1px solid #2a5a9c;color:#4af;
  padding:8px 18px;border-radius:6px;font:13px Consolas,monospace;}
#start-btn{background:linear-gradient(135deg,#0d2a4a,#1a4a7c);
  border:2px solid #4af;color:#4af;padding:14px 44px;border-radius:8px;
  font:15px Consolas,monospace;cursor:pointer;letter-spacing:2px;transition:.2s;}
#start-btn:hover{box-shadow:0 0 24px rgba(64,170,255,.4);color:#fff;}

/* ── HUD ── */
#hud{position:fixed;top:10px;left:10px;display:none;flex-direction:column;gap:6px;z-index:200;}
.hud-box{background:rgba(0,6,18,.84);border:1px solid #1a3a5c;
  border-radius:8px;padding:7px 13px;}
.sys-row{display:flex;flex-wrap:wrap;gap:8px;}
.si{display:flex;align-items:center;gap:4px;font-size:10px;color:#8ab;}
.dot{width:7px;height:7px;border-radius:50%;}
.g{background:#44cc88;box-shadow:0 0 4px #44cc88;}
.y{background:#ffaa00;box-shadow:0 0 4px #ffaa00;}
.r{background:#ff4444;box-shadow:0 0 6px #ff4444;animation:blink 1s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}

/* ── Crosshair ── */
#xhair{position:fixed;display:none;pointer-events:none;z-index:200;}
#xhair::before,#xhair::after{content:'';position:absolute;background:rgba(255,165,0,.75);}
#xhair::before{width:2px;height:22px;left:50%;transform:translateX(-50%);}
#xhair::after{width:22px;height:2px;top:50%;transform:translateY(-50%);}
#xhair.hit::before,#xhair.hit::after{background:#ffa500;box-shadow:0 0 7px #ffa500;}

/* ── Inspect Prompt ── */
#prompt{position:fixed;bottom:100px;display:none;
  transform:translateX(-50%);z-index:200;
  background:rgba(0,6,18,.88);border:1px solid #ffa50088;
  border-radius:8px;padding:8px 22px;color:#ffa500;
  font-size:13px;letter-spacing:1px;white-space:nowrap;
  animation:pb 2s infinite;}
@keyframes pb{0%,100%{border-color:#ffa50044}50%{border-color:#ffa500cc}}

/* ── Inspect Panel (slides in from left on E) ── */
#inspect-panel{position:fixed;top:50%;left:0;transform:translateY(-50%);
  width:260px;display:none;flex-direction:column;z-index:300;
  background:rgba(5,13,26,.96);border:1px solid #1a4a7c;border-left:none;
  border-radius:0 12px 12px 0;padding:16px;}
#inspect-title{color:#ffa500;font-size:13px;font-weight:bold;margin-bottom:8px;
  letter-spacing:1px;}
#inspect-desc{color:#8ab;font-size:11px;line-height:1.7;margin-bottom:12px;}
.qbtn{background:rgba(10,24,40,.9);border:1px solid #2a5a9c;color:#4af;
  padding:7px 12px;border-radius:6px;font:11px Consolas,monospace;
  cursor:pointer;width:100%;margin-bottom:6px;text-align:left;transition:.2s;}
.qbtn:hover{border-color:#4af;background:rgba(20,44,70,.9);}
#inspect-close{color:#5a8a9a;font-size:10px;margin-top:6px;cursor:pointer;text-align:center;}
#inspect-close:hover{color:#4af;}

/* ── Controls bar ── */
#ctrl-bar{position:fixed;bottom:8px;display:none;transform:translateX(-50%);
  background:rgba(0,6,18,.75);border:1px solid #1a3a5c;border-radius:6px;
  padding:5px 18px;color:#4a7a9a;font-size:10px;letter-spacing:.5px;z-index:200;}

/* ── Pause screen ── */
#pause{position:fixed;top:0;left:0;z-index:700;display:none;
  flex-direction:column;align-items:center;justify-content:center;
  gap:18px;background:rgba(0,0,0,.65);}
#pause h2{font-size:18px;letter-spacing:3px;color:#4af;}
.pbtn{background:rgba(10,24,40,.9);border:1px solid #2a5a9c;color:#4af;
  padding:10px 32px;border-radius:6px;font:13px Consolas,monospace;
  cursor:pointer;letter-spacing:1px;transition:.2s;}
.pbtn:hover{border-color:#4af;color:#fff;}

/* ── Chat Panel (right sidebar — always visible) ── */
#chat-panel{position:fixed;top:0;right:0;width:300px;height:100vh;
  background:linear-gradient(180deg,#060e1c,#050d1a);
  border-left:1px solid #1a3a5c;display:flex;flex-direction:column;z-index:250;}
#chat-hdr{background:linear-gradient(135deg,#0d1b2a,#0a1528);
  border-bottom:1px solid #1a4a7c;padding:12px 14px;
  color:#4af;font-size:12px;font-weight:bold;letter-spacing:1.5px;
  display:flex;align-items:center;gap:8px;flex-shrink:0;}
.alive{width:8px;height:8px;border-radius:50%;background:#4f4;
  box-shadow:0 0 6px #4f4;animation:pg 2s infinite;}
@keyframes pg{0%,100%{opacity:1}50%{opacity:.4}}
#chat-msgs{flex:1;overflow-y:auto;padding:10px;
  display:flex;flex-direction:column;gap:8px;}
#chat-msgs::-webkit-scrollbar{width:4px;}
#chat-msgs::-webkit-scrollbar-thumb{background:#1a3a5c;border-radius:2px;}
.msg{border-radius:8px;padding:8px 10px;font-size:11px;line-height:1.65;}
.mu{background:linear-gradient(135deg,#0d2a4a,#152a45);color:#a0c8ff;
  border:1px solid #1a4a7c;margin-left:20px;}
.ma{background:linear-gradient(135deg,#1a0d2a,#120a1e);color:#c0a8ff;
  border:1px solid #3a1a5c;}
.ms{background:rgba(255,165,0,.07);color:#ffa500;
  border:1px solid rgba(255,165,0,.2);font-size:10px;text-align:center;}
#chat-input-row{border-top:1px solid #1a3a5c;padding:10px;
  display:flex;gap:8px;flex-shrink:0;}
#ci{flex:1;background:#0a1220;border:1px solid #2a4a6b;color:#a0d0ff;
  padding:8px 10px;border-radius:6px;font:11px Consolas,monospace;outline:none;}
#ci:focus{border-color:#4af;}
#cs{background:linear-gradient(135deg,#0d2a4a,#1a4a7c);
  border:1px solid #4af;color:#4af;padding:8px 14px;border-radius:6px;
  font:11px Consolas,monospace;cursor:pointer;flex-shrink:0;transition:.2s;}
#cs:hover{color:#fff;background:#1a3a5c;}
#chat-hint{padding:5px 10px;font-size:10px;color:#3a5a7c;
  text-align:center;flex-shrink:0;border-top:1px solid #0d1b2a;}
</style>
</head><body>

<!-- Chat Panel -->
<div id="chat-panel">
  <div id="chat-hdr"><div class="alive"></div>AI 學長 — 即時輔導</div>
  <div id="chat-msgs"><div class="msg ms">⏳ 等待訓練開始…</div></div>
  <div id="chat-input-row">
    <input id="ci" placeholder="問學長… (C 鍵或直接點此)" />
    <button id="cs">送出</button>
  </div>
  <div id="chat-hint">C:對話 | Enter:送出 | ESC:返回操作</div>
</div>

<!-- Loading -->
<div id="loading-screen">
  <div id="load-title">ASML TWINSCAN NXT:870</div>
  <div id="load-pct">0%</div>
  <div class="bar-wrap"><div id="load-bar"></div></div>
  <div id="load-sub">載入 3D 設備模型…</div>
</div>

<!-- Start Screen -->
<div id="start-screen">
  <div style="font-size:48px;color:#4af;opacity:.3;">⚙</div>
  <h1>ASML TWINSCAN NXT:870<br>操作員故障排除訓練</h1>
  <h2>Virtual Fab — 第一人稱沉浸式訓練</h2>
  <div class="hint">
    <b>WASD</b> 移動 &nbsp;|&nbsp; <b>滑鼠</b> 旋轉視角 &nbsp;|&nbsp;
    <b>E</b> 檢查部件 &nbsp;|&nbsp; <b>C</b> 與學長對話<br>
    <b>ESC</b> 暫停 &nbsp;|&nbsp; 右側面板隨時可輸入問題
  </div>
  <div id="diff-row">
    <label style="color:#6ab;font-size:12px;">訓練難度：</label>
    <select id="difficulty">
      <option value="easy">簡單</option>
      <option value="medium" selected>中等</option>
      <option value="hard">困難</option>
    </select>
  </div>
  <button id="start-btn">▶ 開始訓練 — 點此進入</button>
</div>

<!-- HUD -->
<div id="hud">
  <div class="hud-box">
    <div style="color:#4af;font-size:9px;letter-spacing:2px;margin-bottom:5px;">⚡ 子系統狀態</div>
    <div class="sys-row" id="sys-lights"></div>
  </div>
</div>

<!-- Crosshair -->
<div id="xhair"></div>

<!-- Interaction Prompt -->
<div id="prompt"></div>

<!-- Inspect Panel -->
<div id="inspect-panel">
  <div id="inspect-title"></div>
  <div id="inspect-desc"></div>
  <div id="inspect-actions"></div>
  <div id="inspect-close" onclick="closeInspect()">✕ 關閉</div>
</div>

<!-- Controls Bar -->
<div id="ctrl-bar">WASD: 移動 | E: 檢查部件 | C: 與學長對話 | ESC: 暫停</div>

<!-- Pause -->
<div id="pause">
  <h2>⏸ 訓練暫停</h2>
  <div style="font-size:11px;color:#6ab;">點擊 3D 畫面或按 R 繼續</div>
  <button class="pbtn" id="resume-btn">▶ 繼續訓練</button>
  <button class="pbtn" onclick="location.reload()">↺ 重新開始</button>
</div>

<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/PointerLockControls.js"></script>
<script>
'use strict';

// ── Mesh → action/label maps ─────────────────────────────────────────────────
var MA = {
  Stage_Base:'查看晶圓載台位置誤差','Rail_-0.6':'查看晶圓載台位置誤差',
  'Rail_0.0':'查看晶圓載台位置誤差','Rail_0.6':'查看晶圓載台位置誤差',
  Wafer_Chuck:'查看晶圓載台位置誤差',Wafer:'查看晶圓載台位置誤差',
  Label_Stage:'查看晶圓載台位置誤差',
  POB_Barrel:'檢查投影鏡組溫度',POB_Top_Cap:'檢查投影鏡組溫度',
  POB_Bottom:'檢查投影鏡組溫度',Label_POB:'檢查投影鏡組溫度',
  Illum_Barrel:'查看光源強度和穩定性',Label_Illum:'查看光源強度和穩定性',
  Laser_Box:'查看光源強度和穩定性',Laser_Vent:'查看光源強度和穩定性',
  Laser_Out:'查看光源強度和穩定性',Label_Laser:'查看光源強度和穩定性',
  Beam_H1:'查看光源強度和穩定性',Beam_V1:'查看光源強度和穩定性',
  Beam_H2:'查看光源強度和穩定性',Beam_V2:'查看光源強度和穩定性',
  Beam_Spot:'查看光源強度和穩定性',Mirror1:'查看光源強度和穩定性',
  Mirror2:'查看光源強度和穩定性',Mirror3:'查看光源強度和穩定性',
  Immersion_Hood:'檢查冷卻水流量和溫度',Immersion_Supply:'檢查冷卻水流量和溫度',
  Immersion_Return:'檢查冷卻水流量和溫度',Label_Immersion:'檢查冷卻水流量和溫度',
  Duct_Top:'檢查真空系統壓力',Duct_Vent1:'檢查真空系統壓力',
  Duct_Vent2:'檢查真空系統壓力',
  Cabinet_Main:'查看控制系統狀態',Cabinet_Panel:'查看控制系統狀態',
  Screen:'查看控制系統狀態',Keyboard:'查看控制系統狀態',
  FOUP_Port:'確認晶圓傳送狀態',FOUP_Door:'確認晶圓傳送狀態',
  Label_FOUP:'確認晶圓傳送狀態'
};
var ML = {
  Stage_Base:'晶圓載台','Rail_-0.6':'晶圓載台','Rail_0.0':'晶圓載台',
  'Rail_0.6':'晶圓載台',Wafer_Chuck:'晶圓載台',Wafer:'晶圓載台',
  Label_Stage:'晶圓載台',
  POB_Barrel:'投影鏡組',POB_Top_Cap:'投影鏡組',
  POB_Bottom:'投影鏡組',Label_POB:'投影鏡組',
  Illum_Barrel:'照明系統',Label_Illum:'照明系統',
  Laser_Box:'雷射光源',Laser_Vent:'雷射光源',Laser_Out:'雷射光源',
  Label_Laser:'雷射光源',
  Beam_H1:'DUV光束',Beam_V1:'DUV光束',Beam_H2:'DUV光束',
  Beam_V2:'DUV光束',Beam_Spot:'DUV光束',
  Mirror1:'反射鏡',Mirror2:'反射鏡',Mirror3:'反射鏡',
  Immersion_Hood:'液浸冷卻',Immersion_Supply:'液浸冷卻',
  Immersion_Return:'液浸冷卻',Label_Immersion:'液浸冷卻',
  Duct_Top:'通風排氣',Duct_Vent1:'通風排氣',Duct_Vent2:'通風排氣',
  Cabinet_Main:'控制系統',Cabinet_Panel:'控制系統',
  Screen:'控制系統',Keyboard:'控制系統',
  FOUP_Port:'晶圓傳送',FOUP_Door:'晶圓傳送',Label_FOUP:'晶圓傳送'
};
// Extended mappings
(function(){
  for(var i=0;i<10;i++){MA['Lens_'+i]='檢查投影鏡組溫度';ML['Lens_'+i]='投影鏡組';}
  for(var i=0;i<6;i++){MA['IllumLens_'+i]='查看光源強度和穩定性';ML['IllumLens_'+i]='照明系統';}
})();

// Part descriptions for inspect panel
var DESC = {
  '晶圓載台': '精密定位平台，負責承載並精確移動晶圓。位置精度須達奈米等級，任何震動或溫度變化都會影響對準精度。',
  '投影鏡組': '核心光學系統，將光罩圖案縮小投影至晶圓。鏡組溫度變化 0.01°C 即可能造成對焦偏移。',
  '雷射光源': 'KrF 準分子雷射（248nm），提供曝光所需的深紫外線。能量穩定性直接影響線寬均一性。',
  '照明系統': '將雷射光整形並均勻化，確保光罩面均勻照射。包含多組光學元件和快門。',
  '液浸冷卻': '液浸水冷系統，維持鏡組底部與晶圓間的超純水層。水溫需控制在 ±0.001°C。',
  '通風排氣': '維持機台內部氣體潔淨度，排除熱氣和化學氣體。',
  '控制系統': '即時監控和控制所有子系統的主控電腦，處理數千個感測器數據。',
  '晶圓傳送': 'FOUP 介面和機械手臂，負責晶圓的自動裝卸，維持潔淨度和定位精度。',
  'DUV光束': '深紫外線（248nm）光束傳輸路徑，需在氮氣環境中傳輸以避免能量衰減。',
  '反射鏡': '高精度反射鏡，用於光束折轉和準直，鍍膜反射率 >99%。'
};

// Quick actions for inspect panel (part label → list of actions)
var QUICK_ACTIONS = {
  '投影鏡組': ['檢查投影鏡組溫度','調整投影鏡組溫度補償','記錄鏡組溫度數據'],
  '晶圓載台': ['查看晶圓載台位置誤差','重新校準晶圓載台','檢查載台馬達電流'],
  '雷射光源': ['查看光源強度和穩定性','重設雷射能量校準','檢查雷射氣體壓力'],
  '液浸冷卻': ['檢查冷卻水流量和溫度','清洗液浸水頭','更換過濾器'],
  '照明系統': ['查看光源強度和穩定性','調整照明均勻性','檢查快門功能'],
  '控制系統': ['查看控制系統狀態','重啟控制系統服務','下載診斷日誌'],
  '晶圓傳送': ['確認晶圓傳送狀態','重新對準傳送手臂','檢查 FOUP 鎖定'],
  '通風排氣': ['檢查真空系統壓力','清潔排氣過濾器','查看氣流量'],
  'DUV光束': ['查看光源強度和穩定性','對準光束路徑','檢查光束擋板'],
  '反射鏡': ['查看光源強度和穩定性','清潔反射鏡面','檢查反射率']
};

// ── Three.js Setup ────────────────────────────────────────────────────────────
var CW = window.innerWidth - 300;  // canvas width (minus chat)
var CH = window.innerHeight;

var scene = new THREE.Scene();
scene.background = new THREE.Color(0x050d1a);
scene.fog = new THREE.FogExp2(0x050d1a, 0.018);

var renderer = new THREE.WebGLRenderer({antialias: true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(CW, CH);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);
renderer.domElement.style.width = CW + 'px';
renderer.domElement.style.height = CH + 'px';

var camera = new THREE.PerspectiveCamera(72, CW/CH, 0.05, 100);
camera.position.set(0, 1.6, 4);

// Lights
scene.add(new THREE.AmbientLight(0xffffff, 0.65));
var sun = new THREE.DirectionalLight(0xffffff, 1.3);
sun.position.set(6, 10, 6); sun.castShadow = true; scene.add(sun);
var fill = new THREE.DirectionalLight(0x4488ff, 0.3);
fill.position.set(-6, 3, -6); scene.add(fill);
var rim = new THREE.DirectionalLight(0xffeedd, 0.15);
rim.position.set(0, -3, -8); scene.add(rim);

// Floor grid
var floorGeo = new THREE.PlaneGeometry(30, 30);
var floorMat = new THREE.MeshStandardMaterial({color:0x080e18,roughness:.95,metalness:.05});
var floor = new THREE.Mesh(floorGeo, floorMat);
floor.rotation.x = -Math.PI/2; floor.receiveShadow = true; scene.add(floor);

// ── PointerLockControls ───────────────────────────────────────────────────────
var controls = new THREE.PointerLockControls(camera, document.body);
scene.add(controls.getObject());

var moveF=false, moveB=false, moveL=false, moveR=false;
var velocity = new THREE.Vector3();
var clock = new THREE.Clock();
var gameStarted = false;
var chatFocus = false;
var inspecting = false;

// ── Raycasting & Model ───────────────────────────────────────────────────────
var allMeshes = [];
var hoveredObj = null;
var origMats = new Map();
var hlMat = new THREE.MeshStandardMaterial(
  {color:0xffa500,emissive:0x220800,metalness:.3,roughness:.5});
var raycaster = new THREE.Raycaster();
raycaster.far = 8;

function getInfo(obj) {
  var o = obj;
  while (o) { if (MA[o.name]) return {label:ML[o.name]||o.name, action:MA[o.name]}; o=o.parent; }
  return null;
}

// ── Load GLB ──────────────────────────────────────────────────────────────────
var loader = new THREE.GLTFLoader();
loader.load('./asml_duv.glb',
  function(gltf){
    document.getElementById('loading-screen').style.display='none';
    var ss=document.getElementById('start-screen');
    ss.style.display='flex'; ss.style.width=CW+'px'; ss.style.height=CH+'px';

    var model = gltf.scene;
    model.traverse(function(o){
      if(o.isMesh){o.castShadow=true;o.receiveShadow=true;allMeshes.push(o);}
    });
    scene.add(model);
    // Auto-fit: center on floor
    var box = new THREE.Box3().setFromObject(model);
    var c = box.getCenter(new THREE.Vector3());
    var s = box.getSize(new THREE.Vector3());
    model.position.set(-c.x, -box.min.y, -c.z);
    var r = Math.max(s.x, s.z) * 0.8;
    camera.position.set(r, 1.6, r);
    var look = new THREE.Vector3(0, s.y*0.4, 0);
    camera.lookAt(look);
  },
  function(xhr){
    if(xhr.total>0){
      var p=Math.round(xhr.loaded/xhr.total*100);
      document.getElementById('load-pct').textContent=p+'%';
      document.getElementById('load-bar').style.width=p+'%';
    }
  },
  function(err){
    document.getElementById('loading-screen').innerHTML=
      '<span style="color:#f44">❌ 模型載入失敗</span><br><small style="color:#888">'+err+'</small>';
    console.error('GLB:',err);
  }
);

// ── DOM refs ─────────────────────────────────────────────────────────────────
var $ss    = document.getElementById('start-screen');
var $hud   = document.getElementById('hud');
var $xhair = document.getElementById('xhair');
var $prompt= document.getElementById('prompt');
var $ctrl  = document.getElementById('ctrl-bar');
var $pause = document.getElementById('pause');
var $ip    = document.getElementById('inspect-panel');
var $iT    = document.getElementById('inspect-title');
var $iD    = document.getElementById('inspect-desc');
var $iA    = document.getElementById('inspect-actions');
var $msgs  = document.getElementById('chat-msgs');
var $ci    = document.getElementById('ci');
var $cs    = document.getElementById('cs');

// ── Chat ─────────────────────────────────────────────────────────────────────
function addMsg(role, text){
  // Remove initial "waiting" message
  var w=$msgs.querySelector('.ms');
  if(w && w.textContent.includes('等待')) w.remove();
  var d=document.createElement('div');
  d.className='msg '+(role==='user'?'mu':role==='sys'?'ms':'ma');
  d.textContent = role==='user'?'你: '+text : role==='sys'?text : '學長: '+text;
  $msgs.appendChild(d);
  $msgs.scrollTop=$msgs.scrollHeight;
}

function sendChat(txt){
  txt = txt.trim();
  if(!txt || !gameStarted) return;
  addMsg('user', txt);
  $ci.value='';
  $cs.disabled=true;
  fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text:txt})})
  .then(function(r){return r.json();})
  .then(function(d){if(d.ai_msg) addMsg('ai',d.ai_msg);})
  .catch(function(e){addMsg('sys','⚠ 連線錯誤: '+e);})
  .finally(function(){$cs.disabled=false;});
}

$cs.addEventListener('click', function(){sendChat($ci.value);});
$ci.addEventListener('keydown', function(e){
  if(e.key==='Enter' && !e.shiftKey){e.preventDefault();sendChat($ci.value);}
  if(e.key==='Escape'){$ci.blur();exitChatFocus();}
});
$ci.addEventListener('focus', function(){chatFocus=true; controls.unlock();});
$ci.addEventListener('blur',  function(){chatFocus=false;});

function exitChatFocus(){chatFocus=false;}

// ── Inspect Panel ─────────────────────────────────────────────────────────────
function openInspect(label, action){
  inspecting = true;
  controls.unlock();
  $ip.style.display='flex';
  $iT.textContent = '🔍 ' + label;
  $iD.textContent = DESC[label] || '請進一步檢查此子系統的運作狀態。';
  $iA.innerHTML = '';
  var actions = QUICK_ACTIONS[label] || [action];
  actions.forEach(function(a){
    var btn=document.createElement('button');
    btn.className='qbtn'; btn.textContent='▶ '+a;
    btn.onclick=function(){sendChat(a); closeInspect();};
    $iA.appendChild(btn);
  });
  // Also show a "ask mentor" button
  var ask=document.createElement('button');
  ask.className='qbtn';
  ask.textContent='💬 詢問學長：這個部件的狀態如何？';
  ask.onclick=function(){sendChat('學長，'+label+'目前狀態如何？');closeInspect();};
  $iA.appendChild(ask);
}

function closeInspect(){
  inspecting=false;
  $ip.style.display='none';
  if(gameStarted) controls.lock();
}

// ── PointerLock events ────────────────────────────────────────────────────────
controls.addEventListener('lock', function(){
  $ss.style.display='none';
  $pause.style.display='none';
  $xhair.style.display='block';
  // Position xhair at center of 3D area (not chat panel)
  $xhair.style.left = (CW/2)+'px'; $xhair.style.top='50%';
});
controls.addEventListener('unlock', function(){
  if(gameStarted && !chatFocus && !inspecting){
    $pause.style.display='flex';
    $pause.style.width=CW+'px'; $pause.style.height='100vh';
    $xhair.style.display='none';
  }
});

document.getElementById('start-btn').addEventListener('click', function(){
  var diff=document.getElementById('difficulty').value;
  document.getElementById('start-btn').textContent='⏳ 載入中…';
  fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({difficulty:diff})})
  .then(function(r){return r.json();})
  .then(function(d){
    gameStarted=true;
    if(d.ai_msg) addMsg('ai',d.ai_msg);
    addMsg('sys','訓練開始！WASD移動，靠近部件按 E 檢查，C 鍵對話');
    $hud.style.display='flex'; $ctrl.style.display='block';
    updateHUD();
    startTick();
    controls.lock();
  })
  .catch(function(e){
    document.getElementById('start-btn').textContent='▶ 開始訓練 — 點此進入';
    addMsg('sys','⚠ 無法連線到訓練系統: '+e);
  });
});

document.getElementById('resume-btn').addEventListener('click', function(){controls.lock();});

// ── Keyboard ─────────────────────────────────────────────────────────────────
document.addEventListener('keydown', function(e){
  if(chatFocus) return;
  switch(e.code){
    case 'KeyW': case 'ArrowUp':    moveF=true;  break;
    case 'KeyS': case 'ArrowDown':  moveB=true;  break;
    case 'KeyA': case 'ArrowLeft':  moveL=true;  break;
    case 'KeyD': case 'ArrowRight': moveR=true;  break;
    case 'KeyE':
      if(hoveredObj && !inspecting){
        var inf=getInfo(hoveredObj);
        if(inf) openInspect(inf.label, inf.action);
      } else if(inspecting){
        closeInspect();
      }
      break;
    case 'KeyC':
      if(!chatFocus){ $ci.focus(); }
      break;
    case 'KeyR':
      if(gameStarted && !controls.isLocked) controls.lock();
      break;
  }
});
document.addEventListener('keyup', function(e){
  switch(e.code){
    case 'KeyW':case 'ArrowUp':    moveF=false; break;
    case 'KeyS':case 'ArrowDown':  moveB=false; break;
    case 'KeyA':case 'ArrowLeft':  moveL=false; break;
    case 'KeyD':case 'ArrowRight': moveR=false; break;
  }
});

// ── HUD ──────────────────────────────────────────────────────────────────────
var SYS = [
  ['❄️','冷卻'],['💡','光源'],['🔭','鏡組'],['💿','載台'],
  ['🎯','對準'],['📐','光罩'],['🦾','傳送'],['🖥','控制']
];
function updateHUD(){
  var html='';
  SYS.forEach(function(s){
    html+='<div class="si"><div class="dot g"></div>'+s[0]+' '+s[1]+'</div>';
  });
  document.getElementById('sys-lights').innerHTML=html;
}

// ── Auto-tick ─────────────────────────────────────────────────────────────────
var tickTimer=null;
function startTick(){
  if(tickTimer) return;
  tickTimer=setInterval(function(){
    if(!gameStarted) return;
    fetch('/api/tick')
    .then(function(r){return r.json();})
    .then(function(d){if(d.ok && d.ai_msg) addMsg('ai',d.ai_msg);})
    .catch(function(){});
  }, 8000);
}

// ── Render loop ───────────────────────────────────────────────────────────────
function animate(){
  requestAnimationFrame(animate);
  var dt=clock.getDelta();

  // Movement
  if(controls.isLocked && gameStarted){
    velocity.x -= velocity.x * 9 * dt;
    velocity.z -= velocity.z * 9 * dt;
    var sp=5.5;
    if(moveF) velocity.z -= sp*dt;
    if(moveB) velocity.z += sp*dt;
    if(moveL) velocity.x -= sp*dt;
    if(moveR) velocity.x += sp*dt;
    controls.moveRight( velocity.x * dt);
    controls.moveForward(-velocity.z * dt);
    camera.position.y = 1.6; // lock to eye height
  }

  // Raycast from camera center (FPS style)
  if(gameStarted){
    raycaster.setFromCamera(new THREE.Vector2(0,0), camera);
    var hits=raycaster.intersectObjects(allMeshes);

    // Restore previous highlight
    if(hoveredObj){
      if(origMats.has(hoveredObj)) hoveredObj.material=origMats.get(hoveredObj);
      hoveredObj=null;
      if(!inspecting){ $prompt.style.display='none'; $xhair.classList.remove('hit'); }
    }

    if(hits.length>0){
      var obj=hits[0].object;
      var inf=getInfo(obj);
      if(inf){
        if(!origMats.has(obj)) origMats.set(obj,obj.material);
        obj.material=hlMat; hoveredObj=obj;
        if(!inspecting){
          $prompt.textContent='[E] 檢查: '+inf.label;
          $prompt.style.left=(CW/2)+'px';
          $prompt.style.display='block';
          $xhair.classList.add('hit');
        }
      }
    }
  }

  renderer.render(scene, camera);
}
animate();

// ── Resize ────────────────────────────────────────────────────────────────────
window.addEventListener('resize', function(){
  CW=window.innerWidth-300; CH=window.innerHeight;
  camera.aspect=CW/CH; camera.updateProjectionMatrix();
  renderer.setSize(CW,CH);
  renderer.domElement.style.width=CW+'px';
  renderer.domElement.style.height=CH+'px';
  if($ss.style.display!=='none'){$ss.style.width=CW+'px';$ss.style.height=CH+'px';}
  $xhair.style.left=(CW/2)+'px';
  $prompt.style.left=(CW/2)+'px';
});
</script>
</body></html>
"""


def _write_viewer_html(static_dir: Path) -> None:
    out = static_dir / "viewer.html"
    safe = _VIEWER_HTML.encode("utf-16-le", "surrogatepass").decode("utf-16-le")
    out.write_text(safe, encoding="utf-8")
    print(f"[OK] viewer.html → {out}")


# ── 公開 API ──────────────────────────────────────────────────────────────────

def start_game(secom_data_path: str, use_ai_mentor: bool = True,
               port: int = 8765) -> str:
    """啟動遊戲伺服器，回傳遊戲 URL。"""
    global _system_instance
    print("[OK] Loading training system…")
    _system_instance = SimulationTrainingSystem(secom_data_path,
                                                use_ai_mentor=use_ai_mentor)
    print("[OK] Training system ready.")
    p = _start_server(str(_STATIC), port)
    _write_viewer_html(_STATIC)
    url = f"http://127.0.0.1:{p}/viewer.html"
    print(f"[OK] Game URL: {url}")
    return url


def create_firstperson_interface(secom_data_path: str,
                                  use_ai_mentor: bool = True):
    """向下相容的包裝器，回傳可呼叫 .launch() 的物件。"""
    url = start_game(secom_data_path, use_ai_mentor)

    class _FakeDemo:
        def launch(self, **kwargs):
            import webbrowser, time
            print(f"\n[GAME] Opening: {url}")
            webbrowser.open(url)
            print("Press Ctrl+C to stop.\n")
            try:
                threading.Event().wait()
            except KeyboardInterrupt:
                pass

    return _FakeDemo()
