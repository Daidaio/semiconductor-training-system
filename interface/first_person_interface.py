# -*- coding: utf-8 -*-
"""
Virtual Fab 第一人稱遊戲介面（完整版）
- PointerLockControls WASD 第一人稱移動
- E 鍵點選部件 → AI 學長即時回應
- 右側常駐 AI 學長對話面板
- 左側 HMI 虛擬螢幕（canvas texture）可互動
- /api/hmi 回傳即時感測器數值 + SECOM 異常指標
"""

import json
import random
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
_captured_state: dict = {}
_hmi_cache: dict = {}

_server_port: int = 0

# ── 快速回應生成（NLU 無法識別時的後備）────────────────────────────────────

def _smart_response(text: str) -> str:
    """當 NLU 解析失敗（target=None）時，從 HMI 快取生成有意義回應"""
    if not _hmi_cache or not _hmi_cache.get("sensors"):
        return ""
    sensors = {s["label"]: s for s in _hmi_cache["sensors"]}
    alarms  = _hmi_cache.get("alarms", [])
    sc_name = _hmi_cache.get("scenario_name", "")

    # 判斷問題類型
    _KW = {
        "控制": "control", "系統狀態": "control", "Cabinet": "control",
        "冷卻": "cooling",  "冷水": "cooling",   "流量": "cooling",
        "水溫": "cooling",  "水流": "cooling",
        "溫度": "temp",     "鏡組": "temp",       "lens": "temp",
        "光源": "light",    "強度": "light",      "曝光": "light",
        "真空": "vacuum",   "壓力": "vacuum",
        "載台": "stage",    "位置": "stage",
        "過濾": "filter",   "濾網": "filter",
        "重啟": "restart",  "診斷": "diag",       "日誌": "diag",
    }
    topic = next((v for k, v in _KW.items() if k in text), "control")

    # 狀態摘要輔助
    def _fmt(s):
        if not s:
            return "（無資料）"
        st = {"normal": "✓ 正常", "warning": "⚠ 警告", "critical": "🔴 異常"}.get(s["status"], "")
        return f"{s['value']} {s['unit']}  {st}（正常值 {s['normal']}）"

    if topic == "control":
        parts = ["[控制系統狀態報告]", f"情境：{sc_name}" if sc_name else ""]
        for s in _hmi_cache["sensors"]:
            icon = {"normal": "🟢", "warning": "🟡", "critical": "🔴"}.get(s["status"], "⚪")
            parts.append(f"  {icon} {s['label']}: {s['value']} {s['unit']}")
        if alarms:
            parts.append(f"\n⚠ 活動警報 {len(alarms)} 項：")
            for a in alarms[:3]:
                parts.append(f"  [{a['code']}] {a['system']} — {a['msg']}")
        else:
            parts.append("\n✅ 目前無警報，各子系統運行正常。")
        return "\n".join(p for p in parts if p)

    if topic == "cooling":
        s = sensors.get("冷卻水流量") or sensors.get("冷卻水溫度")
        t = sensors.get("冷卻水溫度")
        lines = ["[冷卻系統檢查]"]
        if sensors.get("冷卻水流量"):
            lines.append(f"  流量：{_fmt(sensors['冷卻水流量'])}")
        if t:
            lines.append(f"  水溫：{_fmt(t)}")
        if not lines[1:]:
            lines.append("  （感測器資料尚未載入）")
        alm = [a for a in alarms if "冷卻" in a.get("system", "")]
        if alm:
            lines.append(f"⚠ 警報：{alm[0]['msg']}")
        return "\n".join(lines)

    if topic == "temp":
        s = sensors.get("投影鏡組溫度")
        return f"[鏡組溫度] {_fmt(s)}" if s else ""

    if topic == "light":
        s = sensors.get("光源強度")
        return f"[光源系統] 光源強度 {_fmt(s)}" if s else ""

    if topic == "vacuum":
        s = sensors.get("真空壓力")
        return f"[真空系統] 壓力讀數 {_fmt(s)}" if s else ""

    if topic == "stage":
        sx = sensors.get("載台位置X"); sy = sensors.get("載台位置Y")
        parts = ["[晶圓載台]"]
        if sx: parts.append(f"  X: {_fmt(sx)}")
        if sy: parts.append(f"  Y: {_fmt(sy)}")
        return "\n".join(parts) if len(parts) > 1 else ""

    if topic == "restart":
        return "[控制系統] 重啟服務指令已接收。請確認無正在進行的曝光程序後，依序關閉子系統，等待 30 秒後重新啟動。"

    if topic == "diag":
        lines = ["[診斷日誌下載]"]
        if alarms:
            for a in alarms:
                lines.append(f"  {a['code']} | {a['system']} | {a['level'].upper()} | {a['msg']}")
        else:
            lines.append("  無異常記錄。系統運行正常。")
        return "\n".join(lines)

    return ""

# ── SECOM 特徵映射（真實 feature index → sigma 偏差）────────────────────────
_SECOM_FEATURES = {
    "cooling":   [(10, -2.73), (89, -3.12), (156, -2.45), (201, -1.95), (267, -1.62)],
    "lens":      [(50, +3.21), (156, +2.87), (267, +1.73), (301, +2.15), (400, +1.58)],
    "laser":     [(150, -2.45), (267, -3.05), (89, +1.82), (350, -2.10), (178, -1.77)],
    "stage":     [(200, +2.63), (201, +2.41), (350, +1.95), (400, +1.63), (99, +1.44)],
    "alignment": [(300, -1.87), (156, -2.21), (89, -1.55)],
    "handler":   [(250, +2.10), (301, +1.75), (178, +1.38)],
}
_SCENARIO_TO_SECOM = {
    "cooling": "cooling", "lens": "lens", "light_source": "laser",
    "laser":   "laser",   "wafer_stage": "stage", "alignment": "alignment",
    "handler": "handler",
}

# ── HMI 資料建立 ──────────────────────────────────────────────────────────────

def _build_hmi_data(state: dict) -> None:
    """從 state dict 生成結構化 HMI 資料（供 /api/hmi 使用）"""
    global _hmi_cache, _captured_state
    _captured_state = state
    if not state or not _system_instance:
        return

    # 子系統狀態
    try:
        viz = _system_instance.equipment_visualizer
        sys_st = viz._calculate_all_status(state)
    except Exception:
        sys_st = {}

    # ── 警報 ──────────────────────────────────────────────────────────────────
    _ALARM_MAP = {
        "cooling_system":   ("CLG", "冷卻系統"),
        "lens_system":      ("OPT", "投影鏡組"),
        "light_source":     ("LSR", "光源系統"),
        "wafer_stage":      ("STG", "晶圓載台"),
        "alignment_system": ("ALN", "對準系統"),
        "reticle_stage":    ("RTC", "光罩載台"),
        "wafer_handler":    ("HDL", "晶圓傳送"),
        "control_panel":    ("CTL", "控制系統"),
    }
    alarms = []
    for sid, (code, label) in _ALARM_MAP.items():
        s = sys_st.get(sid, {})
        sev = s.get("severity", "normal")
        msg = s.get("message", "正常")
        if sev in ("warning", "critical"):
            alarms.append({"level": sev, "code": f"ALM-{code}",
                           "system": label, "msg": msg})

    # ── 感測器 ────────────────────────────────────────────────────────────────
    # 推算冷卻水溫度（由流量反推：流量越低 → 水溫越高）
    cooling_flow_val = state.get("cooling_flow")
    if cooling_flow_val is not None:
        state = dict(state)  # 不修改原始 dict
        state["cooling_temp"] = round(18.0 + max(0.0, 5.0 - float(cooling_flow_val)) * 2.8, 1)

    # (label, key, unit, normal, warn_thresh, crit_thresh, lower_is_bad)
    SENSORS = [
        ("冷卻水溫度",   "cooling_temp",        "°C",    18.0,20.0,22.0, False),
        ("冷卻水流量",   "cooling_flow",        "L/min",  5.0, 4.5, 4.0,  True),
        ("投影鏡組溫度", "lens_temp",           "°C",    23.0,24.0,26.0, False),
        ("光源強度",    "light_intensity",      "%",    100.0,92.0,85.0,  True),
        ("載台位置X",   "stage_position_x",    "μm",    None,None,None,  None),
        ("載台位置Y",   "stage_position_y",    "μm",    None,None,None,  None),
        ("真空壓力",    "vacuum_pressure",     "Torr",  None,None,None,  None),
        ("過濾器壓差",  "filter_pressure_drop","Pa",    None,None,None,  None),
    ]
    sensors = []
    for label, key, unit, norm, warn, crit, low_bad in SENSORS:
        val = state.get(key)
        if val is None:
            continue
        status = "normal"
        if warn is not None:
            if low_bad:
                status = "critical" if val < crit else "warning" if val < warn else "normal"
            else:
                status = "critical" if val > crit else "warning" if val > warn else "normal"
        dev = ""
        if norm is not None:
            diff = float(val) - norm
            dev = f"{'+' if diff >= 0 else ''}{diff:.2f} {unit}"
        sensors.append({
            "label": label, "value": round(float(val), 3),
            "unit": unit, "status": status,
            "normal": f"{norm} {unit}" if norm else "-",
            "dev": dev,
        })

    # ── SECOM 異常指標 ────────────────────────────────────────────────────────
    scenario_type = state.get("scenario_type", "")
    secom_key = next((v for k, v in _SCENARIO_TO_SECOM.items()
                      if k in scenario_type.lower()), None)
    secom = []
    used_ids = set()
    if secom_key and secom_key in _SECOM_FEATURES:
        for fid, sigma in _SECOM_FEATURES[secom_key]:
            noisy = sigma + random.uniform(-0.12, 0.12)
            sev = "critical" if abs(noisy) > 2.5 else \
                  "warning"  if abs(noisy) > 1.5 else "normal"
            secom.append({"feature": f"Feature_{fid:03d}",
                          "sigma": round(noisy, 2), "severity": sev})
            used_ids.add(fid)
    # 補充正常 feature 作背景參考
    pool = [i for i in range(1, 591) if i not in used_ids]
    for fid in random.sample(pool, min(4, len(pool))):
        secom.append({"feature": f"Feature_{fid:03d}",
                      "sigma": round(random.uniform(-0.7, 0.7), 2),
                      "severity": "normal"})
    secom.sort(key=lambda x: abs(x["sigma"]), reverse=True)
    secom = secom[:8]

    # ── canvas texture 用的顏色陣列 ───────────────────────────────────────────
    SYS_ORDER = ["cooling_system", "light_source", "lens_system", "wafer_stage",
                 "alignment_system", "reticle_stage", "wafer_handler", "control_panel"]
    _COL = {"normal": "#44cc88", "warning": "#ffaa00", "critical": "#ff4444"}
    sys_colors = [_COL.get(sys_st.get(sid, {}).get("severity", "normal"), "#44cc88")
                  for sid in SYS_ORDER]

    _hmi_cache = {
        "scenario_name": state.get("scenario_name", ""),
        "scenario_type": scenario_type,
        "alarms":     alarms,
        "sensors":    sensors,
        "secom":      secom,
        "sys_colors": sys_colors,
    }


# ── REST API + 靜態檔案 HTTP Handler ─────────────────────────────────────────

class _GameHandler(http.server.SimpleHTTPRequestHandler):

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200); self.end_headers()

    def do_GET(self):
        if   self.path == "/api/status": self._api_status()
        elif self.path == "/api/tick":   self._api_tick()
        elif self.path == "/api/hmi":    self._api_hmi()
        else: super().do_GET()

    def do_POST(self):
        if   self.path == "/api/start": self._api_start()
        elif self.path == "/api/chat":  self._api_chat()
        else: self.send_response(404); self.end_headers()

    def log_message(self, *a): pass

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
            self._json({"started": _session["started"],
                        "msgs": self._msgs_to_list(_session["msgs"])})

    def _api_tick(self):
        with _session_lock:
            if not _session["started"]:
                self._json({"ok": False, "ai_msg": ""}); return
            snap = dict(_session)
        eq, dash, eq_st, msgs, log = _system_instance.auto_progress(
            snap["eq"], snap["dash"], snap["eq_st"], snap["msgs"], snap["log"])
        with _session_lock:
            _session.update(eq=eq, dash=dash, eq_st=eq_st, msgs=msgs, log=log)
        self._json({"ok": True, "ai_msg": self._latest_ai(msgs),
                    "msgs": self._msgs_to_list(msgs)})

    def _api_hmi(self):
        if not _hmi_cache:
            self._json({"started": False, "alarms": [], "sensors": [],
                        "secom": [], "sys_colors": []})
        else:
            self._json(_hmi_cache)

    def _api_start(self):
        data = self._read_json()
        difficulty = data.get("difficulty", "medium")
        eq, dash, eq_st, msgs, log = _system_instance.start_new_scenario(difficulty)
        with _session_lock:
            _session.update(started=True, eq=eq, dash=dash,
                            eq_st=eq_st, msgs=msgs, log=log)
        self._json({"ok": True,
                    "ai_msg": self._latest_ai(msgs) or "情境已開始，請開始檢查設備。",
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
        ai_reply = self._latest_ai(msgs)
        # NLU 無法識別 target 時（"你檢查了None"），改用 HMI 快取生成有意義回應
        if not ai_reply or "你檢查了None" in ai_reply or "你檢查了未知" in ai_reply:
            smart = _smart_response(text)
            if smart:
                ai_reply = smart
        self._json({"ok": True, "ai_msg": ai_reply,
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


# ══════════════════════════════════════════════════════════════════════════════
# viewer.html — 完整第一人稱遊戲
# ══════════════════════════════════════════════════════════════════════════════

_VIEWER_HTML = """\
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>ASML Virtual Fab</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:100%;height:100%;overflow:hidden;background:#050d1a;
  font-family:Consolas,"Courier New",monospace;color:#cde;}
canvas{position:fixed;top:0;left:0;display:block;}

/* ── Loading ── */
#loading-screen{position:fixed;inset:0;background:#050d1a;z-index:900;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;}
#load-pct{font-size:32px;color:#ffa500;}
.bar-wrap{width:280px;height:6px;background:#0a1828;border-radius:3px;}
#load-bar{height:6px;background:linear-gradient(90deg,#4af,#ffa500);
  border-radius:3px;width:0;transition:width .25s;}

/* ── Start Screen ── */
#start-screen{position:fixed;top:0;left:0;z-index:800;display:none;
  flex-direction:column;align-items:center;justify-content:center;gap:22px;
  background:rgba(5,13,26,.94);}
#start-screen h1{font-size:20px;letter-spacing:3px;color:#4af;text-align:center;}
#start-screen h2{font-size:11px;color:#6ab;letter-spacing:2px;text-align:center;}
.hint{font-size:11px;color:#5a8a9a;text-align:center;line-height:2.1;max-width:440px;}
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
.hud-box{background:rgba(0,6,18,.84);border:1px solid #1a3a5c;border-radius:8px;padding:7px 13px;}
.sys-row{display:flex;flex-wrap:wrap;gap:8px;}
.si{display:flex;align-items:center;gap:4px;font-size:10px;color:#8ab;}
.dot{width:7px;height:7px;border-radius:50%;}
.g{background:#44cc88;box-shadow:0 0 4px #44cc88;}
.y{background:#ffaa00;box-shadow:0 0 4px #ffaa00;}
.r{background:#ff4444;box-shadow:0 0 6px #ff4444;animation:blink 1s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}

/* ── Crosshair ── */
#xhair{position:fixed;display:none;pointer-events:none;z-index:200;width:24px;height:24px;}
#xhair::before,#xhair::after{content:'';position:absolute;background:rgba(255,165,0,.75);}
#xhair::before{width:2px;height:22px;left:50%;transform:translateX(-50%);}
#xhair::after{width:22px;height:2px;top:50%;transform:translateY(-50%);}
#xhair.hit::before,#xhair.hit::after{background:#ffa500;box-shadow:0 0 7px #ffa500;}

/* ── Interaction Prompt ── */
#prompt{position:fixed;bottom:110px;display:none;transform:translateX(-50%);z-index:200;
  background:rgba(0,6,18,.9);border:1px solid #ffa50088;border-radius:8px;
  padding:8px 22px;color:#ffa500;font-size:13px;letter-spacing:1px;white-space:nowrap;
  animation:pb 2s infinite;}
@keyframes pb{0%,100%{border-color:#ffa50044}50%{border-color:#ffa500cc}}

/* ── Inspect Panel ── */
#inspect-panel{position:fixed;top:50%;left:0;transform:translateY(-50%);
  width:270px;display:none;flex-direction:column;z-index:300;
  background:rgba(5,13,26,.97);border:1px solid #1a4a7c;border-left:none;
  border-radius:0 12px 12px 0;padding:16px;}
#inspect-title{color:#ffa500;font-size:13px;font-weight:bold;margin-bottom:8px;letter-spacing:1px;}
#inspect-desc{color:#8ab;font-size:11px;line-height:1.7;margin-bottom:12px;}
.qbtn{background:rgba(10,24,40,.9);border:1px solid #2a5a9c;color:#4af;
  padding:7px 12px;border-radius:6px;font:11px Consolas,monospace;
  cursor:pointer;width:100%;margin-bottom:6px;text-align:left;transition:.2s;}
.qbtn:hover{border-color:#4af;background:rgba(20,44,70,.9);}
#inspect-close{color:#5a8a9a;font-size:10px;margin-top:6px;cursor:pointer;text-align:center;}
#inspect-close:hover{color:#4af;}

/* ── Controls Bar ── */
#ctrl-bar{position:fixed;bottom:8px;display:none;transform:translateX(-50%);
  background:rgba(0,6,18,.75);border:1px solid #1a3a5c;border-radius:6px;
  padding:5px 18px;color:#4a7a9a;font-size:10px;letter-spacing:.5px;z-index:200;}

/* ── Pause ── */
#pause{position:fixed;top:0;left:0;z-index:700;display:none;flex-direction:column;
  align-items:center;justify-content:center;gap:18px;background:rgba(0,0,0,.65);}
#pause h2{font-size:18px;letter-spacing:3px;color:#4af;}
.pbtn{background:rgba(10,24,40,.9);border:1px solid #2a5a9c;color:#4af;
  padding:10px 32px;border-radius:6px;font:13px Consolas,monospace;
  cursor:pointer;letter-spacing:1px;transition:.2s;}
.pbtn:hover{border-color:#4af;color:#fff;}

/* ── Chat Panel ── */
#chat-panel{position:fixed;top:0;right:0;width:300px;height:100vh;
  background:linear-gradient(180deg,#060e1c,#050d1a);
  border-left:1px solid #1a3a5c;display:flex;flex-direction:column;z-index:250;}
#chat-hdr{background:linear-gradient(135deg,#0d1b2a,#0a1528);
  border-bottom:1px solid #1a4a7c;padding:12px 14px;color:#4af;
  font-size:12px;font-weight:bold;letter-spacing:1.5px;
  display:flex;align-items:center;gap:8px;flex-shrink:0;}
.alive{width:8px;height:8px;border-radius:50%;background:#4f4;
  box-shadow:0 0 6px #4f4;animation:pg 2s infinite;}
@keyframes pg{0%,100%{opacity:1}50%{opacity:.4}}
#chat-msgs{flex:1;overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:8px;}
#chat-msgs::-webkit-scrollbar{width:4px;}
#chat-msgs::-webkit-scrollbar-thumb{background:#1a3a5c;border-radius:2px;}
.msg{border-radius:8px;padding:8px 10px;font-size:11px;line-height:1.65;}
.mu{background:linear-gradient(135deg,#0d2a4a,#152a45);color:#a0c8ff;
  border:1px solid #1a4a7c;margin-left:20px;}
.ma{background:linear-gradient(135deg,#1a0d2a,#120a1e);color:#c0a8ff;
  border:1px solid #3a1a5c;}
.ms{background:rgba(255,165,0,.07);color:#ffa500;
  border:1px solid rgba(255,165,0,.2);font-size:10px;text-align:center;}
#chat-input-row{border-top:1px solid #1a3a5c;padding:10px;display:flex;gap:8px;flex-shrink:0;}
#ci{flex:1;background:#0a1220;border:1px solid #2a4a6b;color:#a0d0ff;
  padding:8px 10px;border-radius:6px;font:11px Consolas,monospace;outline:none;}
#ci:focus{border-color:#4af;}
#cs{background:linear-gradient(135deg,#0d2a4a,#1a4a7c);border:1px solid #4af;color:#4af;
  padding:8px 14px;border-radius:6px;font:11px Consolas,monospace;
  cursor:pointer;flex-shrink:0;transition:.2s;}
#cs:hover{color:#fff;background:#1a3a5c;}
#chat-hint{padding:5px 10px;font-size:10px;color:#3a5a7c;
  text-align:center;flex-shrink:0;border-top:1px solid #0d1b2a;}

/* ── HMI Overlay ── */
#hmi-overlay{position:fixed;top:0;left:0;z-index:600;display:none;
  align-items:center;justify-content:center;background:rgba(0,0,0,.75);}
#hmi-modal{background:linear-gradient(180deg,#070f1e,#050d1a);
  border:1px solid #1a4a7c;border-radius:12px;width:680px;max-height:85vh;
  display:flex;flex-direction:column;overflow:hidden;
  box-shadow:0 0 40px rgba(64,170,255,.15);}
#hmi-modal-hdr{background:linear-gradient(135deg,#0d1b2a,#0a1528);
  border-bottom:2px solid #1a4a7c;padding:14px 18px;
  display:flex;justify-content:space-between;align-items:center;flex-shrink:0;}
#hmi-modal-hdr span{color:#4af;font-size:13px;font-weight:bold;letter-spacing:1.5px;}
#hmi-close{background:rgba(255,68,68,.15);border:1px solid #ff4444;color:#ff4444;
  padding:5px 14px;border-radius:6px;font:11px Consolas,monospace;cursor:pointer;}
#hmi-close:hover{background:rgba(255,68,68,.3);}
#hmi-content{overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px;}
#hmi-content::-webkit-scrollbar{width:5px;}
#hmi-content::-webkit-scrollbar-thumb{background:#1a3a5c;border-radius:3px;}
.hmi-section{background:rgba(10,24,40,.6);border:1px solid #1a3a5c;
  border-radius:8px;padding:12px 14px;}
.hmi-section-title{font-size:11px;letter-spacing:1.5px;font-weight:bold;
  color:#6ab;margin-bottom:8px;text-transform:uppercase;}
.hmi-alarm{display:flex;align-items:center;gap:10px;padding:7px 10px;
  border-radius:6px;border:1px solid transparent;margin-bottom:5px;}
.alarm-code{font-size:10px;font-weight:bold;min-width:65px;letter-spacing:.5px;}
.alarm-sys{font-size:11px;color:#8ab;min-width:60px;}
.alarm-msg{font-size:11px;color:#cde;flex:1;}
.hmi-sensor{display:grid;grid-template-columns:120px 100px 110px 1fr;
  align-items:center;gap:8px;padding:5px 0;
  border-bottom:1px solid #0d1b2a;font-size:11px;}
.hmi-sensor:last-child{border-bottom:none;}
.sensor-val{font-weight:bold;font-family:Consolas,monospace;}
.sensor-norm{color:#3a5a7c;font-size:10px;}
.sensor-dev{font-size:10px;font-weight:bold;}
.secom-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;}
.secom-feat{background:rgba(10,18,32,.8);border:1px solid transparent;
  border-radius:6px;padding:8px 10px;text-align:center;}
.hmi-info-row{display:flex;justify-content:space-between;font-size:11px;
  padding:4px 0;border-bottom:1px solid #0d1b2a;}
</style>
</head><body>

<!-- Chat Panel -->
<div id="chat-panel">
  <div id="chat-hdr"><div class="alive"></div>AI 學長 — 即時輔導</div>
  <div id="chat-msgs"><div class="msg ms">⏳ 等待訓練開始…</div></div>
  <div id="chat-input-row">
    <input id="ci" placeholder="問學長… (C 鍵)" />
    <button id="cs">送出</button>
  </div>
  <div id="chat-hint">C:對話 | Enter:送出 | ESC:返回操作</div>
</div>

<!-- Loading -->
<div id="loading-screen">
  <div style="font-size:16px;letter-spacing:3px;color:#4af;">ASML TWINSCAN NXT:870</div>
  <div id="load-pct">0%</div>
  <div class="bar-wrap"><div id="load-bar"></div></div>
  <div style="font-size:11px;color:#5a8a9a;">載入 3D 設備模型…</div>
</div>

<!-- Start Screen -->
<div id="start-screen">
  <div style="font-size:48px;color:#4af;opacity:.25;">⚙</div>
  <h1>ASML TWINSCAN NXT:870<br>操作員故障排除訓練</h1>
  <h2>Virtual Fab — 第一人稱沉浸式訓練</h2>
  <div class="hint">
    <b>WASD</b> 移動 &nbsp;|&nbsp; <b>滑鼠</b> 旋轉視角（點擊畫面鎖定）&nbsp;|&nbsp; <b>E</b> 檢查部件<br>
    <b>靠近左側 HMI 螢幕按 E</b> 查看即時感測器數值 &amp; SECOM 異常指標<br>
    <b>C</b> 與 AI 學長對話 &nbsp;|&nbsp; <b>ESC</b> 暫停
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
<!-- Prompt -->
<div id="prompt"></div>
<!-- Inspect Panel -->
<div id="inspect-panel">
  <div id="inspect-title"></div>
  <div id="inspect-desc"></div>
  <div id="inspect-actions"></div>
  <div id="inspect-close" onclick="closeInspect()">✕ 關閉</div>
</div>
<!-- Controls Bar -->
<div id="ctrl-bar">WASD: 移動 | E: 檢查部件 / HMI螢幕 | C: 學長對話 | ESC: 暫停</div>
<!-- Pause -->
<div id="pause">
  <h2>⏸ 訓練暫停</h2>
  <div style="font-size:11px;color:#6ab;">點擊 3D 畫面或按 R 繼續</div>
  <button class="pbtn" id="resume-btn">▶ 繼續訓練</button>
  <button class="pbtn" onclick="location.reload()">↺ 重新開始</button>
</div>

<!-- HMI Overlay -->
<div id="hmi-overlay">
  <div id="hmi-modal">
    <div id="hmi-modal-hdr">
      <span>⚙ ASML TWINSCAN NXT:870 — HMI 控制面板</span>
      <button id="hmi-close" onclick="closeHMI()">✕ 關閉 [ESC]</button>
    </div>
    <div id="hmi-content">
      <div style="color:#5a8a9a;text-align:center;padding:24px;">載入感測器資料…</div>
    </div>
  </div>
</div>

<script src="./three.min.js"></script>
<script src="./GLTFLoader.js"></script>
<script src="./PointerLockControls.js"></script>
<script>
'use strict';
// Catch any JS error and display on screen
window.onerror=function(msg,src,line,col,err){
  var s=document.getElementById('loading-screen');
  if(s)s.innerHTML='<div style="color:#f44;font-size:13px;max-width:80%;text-align:center;padding:20px;">'
    +'<b>❌ JavaScript 錯誤</b><br><br>'
    +'<span style="color:#aaa">'+msg+'</span><br>'
    +'<span style="color:#666;font-size:11px;">Line '+line+'</span><br><br>'
    +'<button onclick="location.reload()" style="background:#0d2a4a;border:1px solid #4af;color:#4af;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:12px;">重新整理</button>'
    +'</div>';
  return false;
};

// ── Mesh action / label maps ──────────────────────────────────────────────────
var MA={
  Reticle_Stage_Mesh:'查看光罩載台狀態',Reticle_Mesh:'查看光罩載台狀態',
  Robot_Arm_Link_Mesh:'查看晶圓傳送機械手臂',
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
  Duct_Top:'檢查真空系統壓力',Duct_Vent1:'檢查真空系統壓力',Duct_Vent2:'檢查真空系統壓力',
  Cabinet_Main:'查看控制系統狀態',Cabinet_Panel:'查看控制系統狀態',
  Screen:'查看控制系統狀態',Keyboard:'查看控制系統狀態',
  FOUP_Port:'確認晶圓傳送狀態',FOUP_Door:'確認晶圓傳送狀態',Label_FOUP:'確認晶圓傳送狀態',
  HMI_Screen:'HMI'
};
var ML={
  Reticle_Stage_Mesh:'光罩載台',Reticle_Mesh:'光罩載台',
  Robot_Arm_Link_Mesh:'晶圓傳送手臂',
  Stage_Base:'晶圓載台','Rail_-0.6':'晶圓載台','Rail_0.0':'晶圓載台',
  'Rail_0.6':'晶圓載台',Wafer_Chuck:'晶圓載台',Wafer:'晶圓載台',Label_Stage:'晶圓載台',
  POB_Barrel:'投影鏡組',POB_Top_Cap:'投影鏡組',POB_Bottom:'投影鏡組',Label_POB:'投影鏡組',
  Illum_Barrel:'照明系統',Label_Illum:'照明系統',
  Laser_Box:'雷射光源',Laser_Vent:'雷射光源',Laser_Out:'雷射光源',Label_Laser:'雷射光源',
  Beam_H1:'DUV光束',Beam_V1:'DUV光束',Beam_H2:'DUV光束',Beam_V2:'DUV光束',Beam_Spot:'DUV光束',
  Mirror1:'反射鏡',Mirror2:'反射鏡',Mirror3:'反射鏡',
  Immersion_Hood:'液浸冷卻',Immersion_Supply:'液浸冷卻',
  Immersion_Return:'液浸冷卻',Label_Immersion:'液浸冷卻',
  Duct_Top:'通風排氣',Duct_Vent1:'通風排氣',Duct_Vent2:'通風排氣',
  Cabinet_Main:'控制系統',Cabinet_Panel:'控制系統',Screen:'控制系統',Keyboard:'控制系統',
  FOUP_Port:'晶圓傳送',FOUP_Door:'晶圓傳送',Label_FOUP:'晶圓傳送',
  HMI_Screen:'HMI 控制面板'
};
var DESC={
  '光罩載台':'精密光罩（Reticle）定位台，承載石英光罩在掃描曝光時做同步往復移動。光罩移動精度決定圖案縮放比例與CD 均一性。',
  '晶圓傳送手臂':'SCARA 機械手臂，負責從 FOUP 取出晶圓後精確放置到晶圓載台。終端效應器（End Effector）採用伯努利原理無接觸夾持。',
  '晶圓載台':'精密定位平台，負責承載並精確移動晶圓。位置精度須達奈米等級，任何震動或溫度變化都會影響對準精度。',
  '投影鏡組':'核心光學系統，將光罩圖案縮小投影至晶圓。鏡組溫度變化 0.01°C 即可能造成對焦偏移。',
  '雷射光源':'KrF 準分子雷射（248nm），提供曝光所需深紫外線。能量穩定性直接影響線寬均一性。',
  '照明系統':'將雷射光整形均勻化，確保光罩面均勻照射。包含多組光學元件和快門。',
  '液浸冷卻':'液浸水冷系統，維持鏡組底部與晶圓間的超純水層。水溫需控制在 ±0.001°C。',
  '通風排氣':'維持機台內部氣體潔淨度，排除熱氣和化學氣體。',
  '控制系統':'即時監控和控制所有子系統的主控電腦，處理數千個感測器數據。',
  '晶圓傳送':'FOUP 介面和機械手臂，負責晶圓的自動裝卸，維持潔淨度和定位精度。',
  'DUV光束':'深紫外線（248nm）光束傳輸路徑，需在氮氣環境中傳輸以避免能量衰減。',
  '反射鏡':'高精度反射鏡，用於光束折轉和準直，鍍膜反射率 >99%。',
  'HMI 控制面板':'設備主控制面板，顯示所有感測器即時數值、警報狀態及 SECOM 製程異常指標。'
};
var QUICK_ACTIONS={
  '投影鏡組':['檢查投影鏡組溫度','調整投影鏡組溫度補償','記錄鏡組溫度數據'],
  '晶圓載台':['查看晶圓載台位置誤差','重新校準晶圓載台','檢查載台馬達電流'],
  '雷射光源':['查看光源強度和穩定性','重設雷射能量校準','檢查雷射氣體壓力'],
  '液浸冷卻':['檢查冷卻水流量和溫度','清洗液浸水頭','更換過濾器'],
  '照明系統':['查看光源強度和穩定性','調整照明均勻性','檢查快門功能'],
  '控制系統':['查看控制系統狀態','重啟控制系統服務','下載診斷日誌'],
  '晶圓傳送':['確認晶圓傳送狀態','重新對準傳送手臂','檢查 FOUP 鎖定'],
  '通風排氣':['檢查真空系統壓力','清潔排氣過濾器','查看氣流量'],
  'DUV光束':['查看光源強度和穩定性','對準光束路徑','檢查光束擋板'],
  '反射鏡':['查看光源強度和穩定性','清潔反射鏡面','檢查反射率'],
  '光罩載台':['查看光罩載台狀態','檢查光罩對準精度','更換光罩','查看光罩掃描速度'],
  '晶圓傳送手臂':['確認晶圓傳送狀態','重新對準傳送手臂','查看手臂馬達電流','檢查 End Effector']
};
(function(){
  for(var i=0;i<10;i++){MA['Lens_'+i]='檢查投影鏡組溫度';ML['Lens_'+i]='投影鏡組';}
  for(var i=0;i<6;i++){MA['IllumLens_'+i]='查看光源強度和穩定性';ML['IllumLens_'+i]='照明系統';}
})();

// ── Three.js Setup ────────────────────────────────────────────────────────────
var CW=window.innerWidth-300, CH=window.innerHeight;
var scene=new THREE.Scene();
scene.background=new THREE.Color(0x050d1a);
scene.fog=new THREE.FogExp2(0x050d1a,0.016);
var renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
renderer.setSize(CW,CH); renderer.shadowMap.enabled=true;
renderer.shadowMap.type=THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);
renderer.domElement.style.width=CW+'px';renderer.domElement.style.height=CH+'px';
var camera=new THREE.PerspectiveCamera(72,CW/CH,0.05,100);
camera.position.set(0,1.6,4);
// Lights
scene.add(new THREE.AmbientLight(0xffffff,0.65));
var sun=new THREE.DirectionalLight(0xffffff,1.3);
sun.position.set(6,10,6);sun.castShadow=true;scene.add(sun);
var fill=new THREE.DirectionalLight(0x4488ff,.3);fill.position.set(-6,3,-6);scene.add(fill);
var rim=new THREE.DirectionalLight(0xffeedd,.15);rim.position.set(0,-3,-8);scene.add(rim);
// Floor
var floorMesh=new THREE.Mesh(new THREE.PlaneGeometry(40,40),
  new THREE.MeshStandardMaterial({color:0x080e18,roughness:.95,metalness:.05}));
floorMesh.rotation.x=-Math.PI/2;floorMesh.receiveShadow=true;scene.add(floorMesh);

// ── PointerLockControls ───────────────────────────────────────────────────────
var controls=new THREE.PointerLockControls(camera,document.body);
scene.add(controls.getObject());
var moveF=false,moveB=false,moveL=false,moveR=false;
var velocity=new THREE.Vector3();
var clock=new THREE.Clock();
var gameStarted=false,chatFocus=false,inspecting=false,hmiOpen=false;

// ── Raycasting & Model ────────────────────────────────────────────────────────
var allMeshes=[],hoveredObj=null,origMats=new Map();
var hlMat=new THREE.MeshStandardMaterial({color:0xffa500,emissive:0x220800,metalness:.3,roughness:.5});
var raycaster=new THREE.Raycaster();raycaster.far=9;
var mixer=null; // GLB AnimationMixer
function getInfo(obj){var o=obj;while(o){if(MA[o.name])return{label:ML[o.name]||o.name,action:MA[o.name]};o=o.parent;}return null;}

// ── HMI Screen (canvas texture) ───────────────────────────────────────────────
var hmiCanvas=null,hmiCtx=null,hmiTex=null,hmiMesh=null;

function createHMIScreen(modelBox){
  var size=modelBox.getSize(new THREE.Vector3());
  // Canvas
  hmiCanvas=document.createElement('canvas');
  hmiCanvas.width=512;hmiCanvas.height=320;
  hmiCtx=hmiCanvas.getContext('2d');
  drawHMIScreen(null);
  hmiTex=new THREE.CanvasTexture(hmiCanvas);
  // Plane on left face: x = -size.x/2, facing -X direction (rotate Y = -PI/2)
  var sw=Math.min(size.z*0.38, 1.2), sh=Math.min(size.y*0.22, 0.75);
  hmiMesh=new THREE.Mesh(
    new THREE.PlaneGeometry(sw,sh),
    new THREE.MeshBasicMaterial({map:hmiTex,side:THREE.FrontSide})
  );
  hmiMesh.name='HMI_Screen';
  hmiMesh.position.set(-size.x/2-0.015, size.y*0.62, 0);
  hmiMesh.rotation.y=-Math.PI/2;
  scene.add(hmiMesh);
  allMeshes.push(hmiMesh);
}

function drawHMIScreen(data){
  if(!hmiCtx) return;
  var W=512,H=320,ctx=hmiCtx;
  ctx.fillStyle='#030810';ctx.fillRect(0,0,W,H);
  ctx.strokeStyle='#1a4a7c';ctx.lineWidth=3;ctx.strokeRect(2,2,W-4,H-4);
  // Header
  ctx.fillStyle='#0a1828';ctx.fillRect(0,0,W,46);
  ctx.strokeStyle='#1a4a7c';ctx.lineWidth=1;
  ctx.beginPath();ctx.moveTo(0,46);ctx.lineTo(W,46);ctx.stroke();
  ctx.fillStyle='#4af';ctx.font='bold 17px Consolas';ctx.fillText('ASML HMI',14,30);
  ctx.fillStyle='#5a8a9a';ctx.font='12px Consolas';ctx.fillText('NXT:870  DUV 248nm',140,30);
  // Status lights
  var labels=['冷卻','光源','鏡組','載台','對準','光罩','傳送','控制'];
  var colors=data&&data.sys_colors?data.sys_colors:Array(8).fill('#44cc88');
  for(var i=0;i<8;i++){
    var col=i<colors.length?colors[i]:'#44cc88';
    var x=14+(i%4)*124, y=62+Math.floor(i/4)*60;
    ctx.fillStyle=col;ctx.shadowColor=col;ctx.shadowBlur=8;
    ctx.beginPath();ctx.arc(x+10,y+10,9,0,Math.PI*2);ctx.fill();
    ctx.shadowBlur=0;
    ctx.fillStyle='#8ab';ctx.font='13px Consolas';ctx.fillText(labels[i],x+26,y+15);
  }
  // Alarm footer
  var hasAlarm=data&&data.alarms&&data.alarms.length>0;
  if(hasAlarm){
    ctx.fillStyle='rgba(255,68,0,.12)';ctx.fillRect(0,H-54,W,54);
    ctx.strokeStyle='#ff440040';ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(0,H-54);ctx.lineTo(W,H-54);ctx.stroke();
    ctx.fillStyle='#ff6644';ctx.font='bold 13px Consolas';
    var txt='⚠  '+data.alarms[0].msg;
    if(txt.length>44)txt=txt.substring(0,44)+'…';
    ctx.fillText(txt,14,H-32);
    ctx.fillStyle='#ffa500';ctx.font='11px Consolas';
    ctx.fillText('按 E 查看詳細資料',14,H-12);
  } else if(data){
    ctx.fillStyle='rgba(68,204,136,.08)';ctx.fillRect(0,H-44,W,44);
    ctx.fillStyle='#44cc88';ctx.font='13px Consolas';ctx.fillText('✓  系統運行正常',14,H-16);
    ctx.fillStyle='#5a8a9a';ctx.font='11px Consolas';ctx.fillText('按 E 查看詳細資料',14,H-4);
  } else {
    ctx.fillStyle='#2a4a6a';ctx.font='12px Consolas';ctx.fillText('⏳ 等待情境開始…',14,H-18);
  }
  if(hmiTex)hmiTex.needsUpdate=true;
}

// ── Load GLB ──────────────────────────────────────────────────────────────────
var loader=new THREE.GLTFLoader();
loader.load('./asml_duv.glb',
  function(gltf){
    try{
      document.getElementById('loading-screen').style.display='none';
      var ss=document.getElementById('start-screen');
      ss.style.display='flex';ss.style.width=CW+'px';ss.style.height=CH+'px';
      var model=gltf.scene;
      model.traverse(function(o){if(o.isMesh){o.castShadow=true;o.receiveShadow=true;allMeshes.push(o);}});
      scene.add(model);
      var box=new THREE.Box3().setFromObject(model);
      var c=box.getCenter(new THREE.Vector3()),s=box.getSize(new THREE.Vector3());
      model.position.set(-c.x,-box.min.y,-c.z);
      var worldBox=new THREE.Box3().setFromObject(model);
      createHMIScreen(worldBox);
      var r=Math.max(s.x,s.z)*0.85;
      camera.position.set(r,1.6,r);
      camera.lookAt(new THREE.Vector3(0,s.y*0.4,0));
      // ── 播放 GLB 動畫 ──────────────────────────────────────────
      if(gltf.animations&&gltf.animations.length>0){
        mixer=new THREE.AnimationMixer(model);
        gltf.animations.forEach(function(clip){
          var action=mixer.clipAction(clip);
          action.setLoop(THREE.LoopRepeat,Infinity);
          action.play();
        });
        console.log('[OK] Playing',gltf.animations.length,'animations:',
          gltf.animations.map(function(a){return a.name;}).join(', '));
      }
      // 建立程序化幾何（光罩載台、機械手臂等）
      createProcObjects(model);
    }catch(e){
      var el=document.getElementById('loading-screen');
      if(el)el.innerHTML='<div style="color:#f44;text-align:center;padding:20px;">❌ 模型處理錯誤<br><small style="color:#888">'+e.message+'</small></div>';
      console.error('onLoad error:',e);
    }
  },
  function(xhr){
    var pEl=document.getElementById('load-pct');
    var bEl=document.getElementById('load-bar');
    if(!pEl)return;
    if(xhr.total&&xhr.total>0){
      var p=Math.round(xhr.loaded/xhr.total*100);
      pEl.textContent=p+'%'; if(bEl)bEl.style.width=p+'%';
    } else if(xhr.loaded>0){
      var kb=Math.round(xhr.loaded/1024);
      pEl.textContent=kb+' KB';
      // Fake progress (model ~1.5MB)
      if(bEl)bEl.style.width=Math.min(90,Math.round(xhr.loaded/15000))+'%';
    }
  },
  function(err){
    var el=document.getElementById('loading-screen');
    if(el)el.innerHTML='<div style="color:#f44;text-align:center;padding:20px;">❌ 模型載入失敗<br><small style="color:#888">'+err+'</small><br><br><button onclick="location.reload()" style="background:#0d2a4a;border:1px solid #4af;color:#4af;padding:8px 20px;border-radius:6px;cursor:pointer;">重新整理</button></div>';
    console.error('GLB error:',err);
  }
);

// ── DOM refs ──────────────────────────────────────────────────────────────────
var $hud=document.getElementById('hud');
var $xhair=document.getElementById('xhair');
var $prompt=document.getElementById('prompt');
var $ctrl=document.getElementById('ctrl-bar');
var $pause=document.getElementById('pause');
var $ip=document.getElementById('inspect-panel');
var $msgs=document.getElementById('chat-msgs');
var $ci=document.getElementById('ci');
var $cs=document.getElementById('cs');
var $hmiOverlay=document.getElementById('hmi-overlay');
var $hmiContent=document.getElementById('hmi-content');

// ── Chat ──────────────────────────────────────────────────────────────────────
function addMsg(role,text){
  var w=$msgs.querySelector('.ms');if(w&&w.textContent.includes('等待'))w.remove();
  var d=document.createElement('div');
  d.className='msg '+(role==='user'?'mu':role==='sys'?'ms':'ma');
  d.textContent=role==='user'?'你: '+text:role==='sys'?text:'學長: '+text;
  $msgs.appendChild(d);$msgs.scrollTop=$msgs.scrollHeight;
}
function sendChat(txt){
  txt=txt.trim();if(!txt||!gameStarted)return;
  addMsg('user',txt);$ci.value='';$cs.disabled=true;
  fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text:txt})})
  .then(function(r){return r.json();})
  .then(function(d){if(d.ai_msg)addMsg('ai',d.ai_msg);})
  .catch(function(e){addMsg('sys','⚠ 連線錯誤');})
  .finally(function(){$cs.disabled=false;});
}
$cs.onclick=function(){sendChat($ci.value);};
$ci.addEventListener('keydown',function(e){
  if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendChat($ci.value);}
  if(e.key==='Escape'){$ci.blur();chatFocus=false;}
});
$ci.addEventListener('focus',function(){chatFocus=true;controls.unlock();});
$ci.addEventListener('blur',function(){chatFocus=false;});

// ── Inspect Panel ─────────────────────────────────────────────────────────────
function openInspect(label,action){
  inspecting=true;controls.unlock();
  $ip.style.display='flex';
  document.getElementById('inspect-title').textContent='🔍 '+label;
  document.getElementById('inspect-desc').textContent=DESC[label]||'請進一步檢查此子系統的運作狀態。';
  var $ia=document.getElementById('inspect-actions');$ia.innerHTML='';
  var acts=QUICK_ACTIONS[label]||[action];
  acts.forEach(function(a){
    var btn=document.createElement('button');btn.className='qbtn';btn.textContent='▶ '+a;
    btn.onclick=function(){sendChat(a);closeInspect();};$ia.appendChild(btn);
  });
  var ask=document.createElement('button');ask.className='qbtn';
  ask.textContent='💬 學長，這個部件狀態如何？';
  ask.onclick=function(){sendChat('學長，'+label+'目前狀態如何？');closeInspect();};
  $ia.appendChild(ask);
}
function closeInspect(){
  inspecting=false;$ip.style.display='none';
  if(gameStarted&&!hmiOpen)controls.lock();
}

// ── HMI Overlay ───────────────────────────────────────────────────────────────
function showHMIOverlay(){
  hmiOpen=true;controls.unlock();
  $hmiOverlay.style.display='flex';
  $hmiOverlay.style.width=CW+'px';$hmiOverlay.style.height='100vh';
  $hmiContent.innerHTML='<div style="color:#5a8a9a;text-align:center;padding:24px;">載入感測器資料…</div>';
  fetch('/api/hmi').then(function(r){return r.json();}).then(function(d){renderHMI(d);})
  .catch(function(){$hmiContent.innerHTML='<div style="color:#f44;padding:20px;">無法取得 HMI 資料</div>';});
}
function closeHMI(){
  hmiOpen=false;$hmiOverlay.style.display='none';
  if(gameStarted)controls.lock();
}
window.closeHMI=closeHMI;

function renderHMI(d){
  if(!d||!d.sensors){$hmiContent.innerHTML='<div style="color:#5a8a9a;padding:20px">尚未開始情境</div>';return;}
  var html='';
  // Scenario info
  html+='<div class="hmi-section">';
  html+='<div class="hmi-section-title">📋 情境資訊</div>';
  html+='<div class="hmi-info-row"><span style="color:#6ab">情境名稱</span><span style="color:#ffa500">'+(d.scenario_name||'N/A')+'</span></div>';
  html+='<div class="hmi-info-row"><span style="color:#6ab">故障類型</span><span style="color:#cde">'+(d.scenario_type||'N/A')+'</span></div>';
  html+='</div>';
  // Alarms
  var aColor=d.alarms&&d.alarms.length?'#ff6644':'#44cc88';
  var aTitle=d.alarms&&d.alarms.length?'⚠ 活動警報 ('+d.alarms.length+')':'✅ 無活動警報';
  html+='<div class="hmi-section"><div class="hmi-section-title" style="color:'+aColor+'">'+aTitle+'</div>';
  if(d.alarms&&d.alarms.length){
    d.alarms.forEach(function(a){
      var col=a.level==='critical'?'#ff4444':'#ffaa00';
      html+='<div class="hmi-alarm" style="border-color:'+col+'44;background:'+col+'0e">';
      html+='<span class="alarm-code" style="color:'+col+'">'+a.code+'</span>';
      html+='<span class="alarm-sys">'+a.system+'</span>';
      html+='<span class="alarm-msg">'+a.msg+'</span></div>';
    });
  } else {
    html+='<div style="color:#44cc88;font-size:11px;padding:4px 0;">所有子系統運行正常</div>';
  }
  html+='</div>';
  // Sensors
  html+='<div class="hmi-section"><div class="hmi-section-title">📊 即時感測器數值</div>';
  (d.sensors||[]).forEach(function(s){
    var col=s.status==='critical'?'#ff4444':s.status==='warning'?'#ffaa00':'#44cc88';
    var icon=s.status==='critical'?'🔴':s.status==='warning'?'🟡':'🟢';
    html+='<div class="hmi-sensor">';
    html+='<span>'+icon+' '+s.label+'</span>';
    html+='<span class="sensor-val" style="color:'+col+'">'+s.value+' '+s.unit+'</span>';
    html+='<span class="sensor-norm">正常: '+s.normal+'</span>';
    html+='<span class="sensor-dev" style="color:'+col+'">'+(s.dev||'')+'</span>';
    html+='</div>';
  });
  html+='</div>';
  // SECOM
  if(d.secom&&d.secom.length){
    html+='<div class="hmi-section"><div class="hmi-section-title">🔬 SECOM 製程參數異常指標</div>';
    html+='<div class="secom-grid">';
    d.secom.forEach(function(f){
      var col=f.severity==='critical'?'#ff4444':f.severity==='warning'?'#ffaa00':'#44cc88';
      var sig=(f.sigma>=0?'+':'')+f.sigma+'σ';
      html+='<div class="secom-feat" style="border-color:'+col+'33">';
      html+='<div style="color:#5a8a9a;font-size:10px;">'+f.feature+'</div>';
      html+='<div style="color:'+col+';font-size:14px;font-weight:bold;margin-top:3px;">'+sig+'</div>';
      html+='</div>';
    });
    html+='</div></div>';
  }
  // ERROR Log
  html+='<div class="hmi-section">';
  html+='<div class="hmi-section-title" style="color:'+(d.alarms&&d.alarms.length?'#ff6644':'#5a8a9a')+'">📋 系統錯誤日誌 (ERROR Log)</div>';
  if(d.alarms&&d.alarms.length){
    var now=new Date();
    d.alarms.forEach(function(a,i){
      var t=new Date(now.getTime()-i*197000);
      function z(n){return n.toString().padStart(2,'0');}
      var ts=z(t.getHours())+':'+z(t.getMinutes())+':'+z(t.getSeconds());
      var col=a.level==='critical'?'#ff4444':'#ffaa00';
      html+='<div style="display:flex;gap:10px;padding:5px 8px;border-bottom:1px solid #0d1b2a;font-family:Consolas,monospace;font-size:11px;">';
      html+='<span style="color:#3a5a7c;min-width:55px;">'+ts+'</span>';
      html+='<span style="color:'+col+';min-width:65px;font-weight:bold;">['+a.level.toUpperCase()+']</span>';
      html+='<span style="color:#7ab;min-width:70px;">'+a.code+'</span>';
      html+='<span style="color:#cde;">'+a.system+'：'+a.msg+'</span>';
      html+='</div>';
    });
    // 新增正常運行紀錄
    var ok=new Date(now.getTime()-d.alarms.length*210000);
    function z2(n){return n.toString().padStart(2,'0');}
    html+='<div style="display:flex;gap:10px;padding:5px 8px;font-family:Consolas,monospace;font-size:11px;">';
    html+='<span style="color:#3a5a7c;min-width:55px;">'+z2(ok.getHours())+':'+z2(ok.getMinutes())+':'+z2(ok.getSeconds())+'</span>';
    html+='<span style="color:#44cc88;min-width:65px;font-weight:bold;">[INFO]</span>';
    html+='<span style="color:#7ab;min-width:70px;">SYS-INIT</span>';
    html+='<span style="color:#5a8a9a;">系統啟動完成，開始監控。</span>';
    html+='</div>';
  } else {
    html+='<div style="font-family:Consolas,monospace;font-size:11px;padding:8px;">';
    html+='<span style="color:#3a5a7c;">'+new Date().toLocaleTimeString()+'</span>';
    html+=' <span style="color:#44cc88;">[INFO]</span>';
    html+=' <span style="color:#5a8a9a;">SYS-OK — 所有子系統運行正常，無錯誤記錄。</span>';
    html+='</div>';
  }
  html+='</div>';
  $hmiContent.innerHTML=html;
  // Update canvas texture
  drawHMIScreen(d);
}

// ── Pointer Lock events ───────────────────────────────────────────────────────
controls.addEventListener('lock',function(){
  document.getElementById('start-screen').style.display='none';
  $pause.style.display='none';
  $xhair.style.display='block';
  $xhair.style.left=(CW/2-12)+'px';$xhair.style.top='calc(50% - 12px)';
});
controls.addEventListener('unlock',function(){
  if(gameStarted&&!chatFocus&&!inspecting&&!hmiOpen){
    $pause.style.display='flex';$pause.style.width=CW+'px';$pause.style.height='100vh';
    $xhair.style.display='none';
  }
});

// ── Start button ──────────────────────────────────────────────────────────────
document.getElementById('start-btn').addEventListener('click',function(){
  var diff=document.getElementById('difficulty').value;
  document.getElementById('start-btn').textContent='⏳ 載入中…';
  fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({difficulty:diff})})
  .then(function(r){return r.json();})
  .then(function(d){
    gameStarted=true;
    if(d.ai_msg)addMsg('ai',d.ai_msg);
    addMsg('sys','訓練開始！靠近左側 HMI 螢幕按 E 查看感測器數值');
    $hud.style.display='flex';$ctrl.style.display='block';
    updateHUD();startTick();controls.lock();
  })
  .catch(function(e){
    document.getElementById('start-btn').textContent='▶ 開始訓練 — 點此進入';
    addMsg('sys','⚠ 無法連線: '+e);
  });
});
document.getElementById('resume-btn').addEventListener('click',function(){controls.lock();});

// ── Keyboard ──────────────────────────────────────────────────────────────────
document.addEventListener('keydown',function(e){
  if(chatFocus)return;
  if(hmiOpen&&e.key==='Escape'){closeHMI();return;}
  switch(e.code){
    case 'KeyW':case 'ArrowUp':    moveF=true;break;
    case 'KeyS':case 'ArrowDown':  moveB=true;break;
    case 'KeyA':case 'ArrowLeft':  moveL=true;break;
    case 'KeyD':case 'ArrowRight': moveR=true;break;
    case 'KeyE':
      if(hmiOpen){closeHMI();break;}
      if(inspecting){closeInspect();break;}
      if(hoveredObj){
        if(hoveredObj.name==='HMI_Screen'){showHMIOverlay();break;}
        var inf=getInfo(hoveredObj);
        if(inf){
          // 控制系統面板 → 直接開啟 HMI 覆蓋畫面
          if(inf.label==='控制系統'||inf.label==='HMI 控制面板'){showHMIOverlay();}
          else{openInspect(inf.label,inf.action);}
        }
      }
      break;
    case 'KeyC':$ci.focus();break;
    case 'KeyR':if(gameStarted&&!controls.isLocked)controls.lock();break;
  }
});
document.addEventListener('keyup',function(e){
  switch(e.code){
    case 'KeyW':case 'ArrowUp':    moveF=false;break;
    case 'KeyS':case 'ArrowDown':  moveB=false;break;
    case 'KeyA':case 'ArrowLeft':  moveL=false;break;
    case 'KeyD':case 'ArrowRight': moveR=false;break;
  }
});

// ── HUD subsystem lights ──────────────────────────────────────────────────────
var SYS=[['❄️','冷卻'],['💡','光源'],['🔭','鏡組'],['💿','載台'],
         ['🎯','對準'],['📐','光罩'],['🦾','傳送'],['🖥','控制']];
function updateHUD(colors){
  colors=colors||Array(8).fill('#44cc88');
  var html='';
  SYS.forEach(function(s,i){
    var c=colors[i]||'#44cc88';
    var cls=c==='#44cc88'?'g':c==='#ffaa00'?'y':'r';
    html+='<div class="si"><div class="dot '+cls+'"></div>'+s[0]+' '+s[1]+'</div>';
  });
  document.getElementById('sys-lights').innerHTML=html;
}

// ── Auto-tick ─────────────────────────────────────────────────────────────────
var tickTimer=null;
function startTick(){
  if(tickTimer)return;
  tickTimer=setInterval(function(){
    if(!gameStarted)return;
    fetch('/api/tick').then(function(r){return r.json();})
    .then(function(d){
      if(d.ok&&d.ai_msg)addMsg('ai',d.ai_msg);
      // Refresh HMI canvas in background
      fetch('/api/hmi').then(function(r){return r.json();})
      .then(function(h){if(h.sys_colors){updateHUD(h.sys_colors);drawHMIScreen(h);}})
      .catch(function(){});
    }).catch(function(){});
  },8000);
}

// ── Procedural 3D Objects（光罩載台 + 機械手臂）─────────────────────────────
var procObjs={};
var sceneMeshMap={};
var beamPtLight=null;
var procElapsed=0;

function createProcObjects(model){
  model.traverse(function(o){if(o.name)sceneMeshMap[o.name]=o;});

  // ── 材質 ──────────────────────────────────────────────────────────────────
  var metalMat=new THREE.MeshStandardMaterial({color:0x8899aa,metalness:.75,roughness:.25});
  var darkMetal=new THREE.MeshStandardMaterial({color:0x334455,metalness:.8,roughness:.2});
  var silicaMat=new THREE.MeshStandardMaterial({color:0x4466cc,metalness:.4,roughness:.1,transparent:true,opacity:.85});
  var maskMat=new THREE.MeshStandardMaterial({color:0x110022,metalness:.1,roughness:.2,transparent:true,opacity:.9});
  var markMat=new THREE.MeshStandardMaterial({color:0xcc88ff,emissive:0x440066});
  var uvMat=new THREE.MeshStandardMaterial({color:0x8800ff,emissive:0x5500cc,transparent:true,opacity:.55});
  var glowMat=new THREE.MeshStandardMaterial({color:0xaa44ff,emissive:0x7700ff,transparent:true,opacity:.7});

  // ── 取得關鍵 GLB 節點的「世界座標」────────────────────────────────────────
  // GLB 節點是 model 的子物件，.position 是局部座標；
  // 必須用 getWorldPosition() 才能取得正確世界座標
  var pobTop  = sceneMeshMap['POB_Top_Cap'];
  var pobBot  = sceneMeshMap['POB_Bottom'];
  var wChuck  = sceneMeshMap['Wafer_Chuck'];
  var foupPort= sceneMeshMap['FOUP_Port'];

  var pobTopW =new THREE.Vector3(); var pobBotW=new THREE.Vector3();
  var chuckW  =new THREE.Vector3(); var foupW  =new THREE.Vector3();
  if(pobTop) pobTop.getWorldPosition(pobTopW);   else pobTopW.set(0.64,2.19,0.12);
  if(pobBot) pobBot.getWorldPosition(pobBotW);   else pobBotW.set(0.64,0.71,0.12);
  if(wChuck) wChuck.getWorldPosition(chuckW);    else chuckW.set(0.24,0.62,0.12);
  if(foupPort)foupPort.getWorldPosition(foupW);  else foupW.set(-0.93,1.04,0.64);

  // 儲存動畫用基準位置
  procObjs.chuckW  = chuckW.clone();   // 晶圓夾頭世界座標（靜止時）
  procObjs.pobBotW = pobBotW.clone();  // 鏡組底部（光束起點）

  console.log('[DBG] chuckW:',chuckW.x.toFixed(2),chuckW.y.toFixed(2),chuckW.z.toFixed(2),
              '  pobTopW:',pobTopW.x.toFixed(2),pobTopW.y.toFixed(2),pobTopW.z.toFixed(2));

  // ── 光罩載台（Reticle Stage）──────────────────────────────────────────────
  // 放在 POB_Top_Cap 正上方 0.18m
  var rsCX=pobTopW.x, rsCZ=pobTopW.z, rsY=pobTopW.y+0.18;

  var rs=new THREE.Mesh(new THREE.BoxGeometry(.52,.06,.52),metalMat.clone());
  rs.name='Reticle_Stage_Mesh';rs.position.set(rsCX,rsY,rsCZ);rs.castShadow=true;
  scene.add(rs);procObjs.rs=rs;allMeshes.push(rs);

  var rsEdge=new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(.52,.06,.52)),
    new THREE.LineBasicMaterial({color:0x4488cc}));
  rsEdge.position.copy(rs.position);scene.add(rsEdge);

  // 光罩（薄方形石英板）
  var rmBaseY=rsY+0.038;
  var rm=new THREE.Mesh(new THREE.BoxGeometry(.28,.006,.28),maskMat);
  rm.name='Reticle_Mesh';rm.position.set(rsCX,rmBaseY,rsCZ);
  scene.add(rm);procObjs.rm=rm;procObjs.rmBaseY=rmBaseY;allMeshes.push(rm);

  // 光罩圖案標記（十字線）
  var rm1=new THREE.Mesh(new THREE.BoxGeometry(.26,.007,.015),markMat);
  rm1.position.set(rsCX,rmBaseY+0.003,rsCZ);scene.add(rm1);
  var rm2=new THREE.Mesh(new THREE.BoxGeometry(.015,.007,.26),markMat);
  rm2.position.set(rsCX,rmBaseY+0.003,rsCZ);scene.add(rm2);
  procObjs.rmMarks=[rm1,rm2];procObjs.rmMarkBaseY=rmBaseY+0.003;

  // 光罩載台支撐柱（4角）
  [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(function(d){
    var col=new THREE.Mesh(new THREE.CylinderGeometry(.018,.018,.16,8),darkMetal.clone());
    col.position.set(rsCX+d[0]*.20,rsY-0.05,rsCZ+d[1]*.20);scene.add(col);
  });
  var rail=new THREE.Mesh(new THREE.BoxGeometry(.02,.02,.58),darkMetal.clone());
  rail.position.set(rsCX,rsY+0.01,rsCZ);scene.add(rail);

  // ── 機械手臂（Robot Arm）──────────────────────────────────────────────────
  // 底座靠近 FOUP，高度與晶圓夾頭相符
  var armBX=foupW.x+0.28, armBZ=foupW.z-0.18, armBY=chuckW.y-0.30;
  // End Effector 移動起點（FOUP 側）→ 終點（Chuck 正上方）
  procObjs.efStart=new THREE.Vector3(armBX+0.18, chuckW.y+0.05, armBZ+0.05);
  procObjs.efEnd  =new THREE.Vector3(chuckW.x,   chuckW.y+0.04, chuckW.z);

  var rbBase=new THREE.Mesh(new THREE.CylinderGeometry(.065,.085,.36,12),metalMat.clone());
  rbBase.position.set(armBX,armBY,armBZ);rbBase.castShadow=true;
  scene.add(rbBase);procObjs.rbBase=rbBase;

  var rbTurret=new THREE.Mesh(new THREE.CylinderGeometry(.07,.07,.06,12),darkMetal.clone());
  rbTurret.position.set(armBX,chuckW.y+0.02,armBZ);
  scene.add(rbTurret);procObjs.rbTurret=rbTurret;

  var rbLink=new THREE.Mesh(new THREE.BoxGeometry(.55,.05,.06),metalMat.clone());
  rbLink.name='Robot_Arm_Link_Mesh';
  rbLink.position.set(armBX,chuckW.y+0.04,armBZ);rbLink.castShadow=true;
  scene.add(rbLink);procObjs.rbLink=rbLink;allMeshes.push(rbLink);

  var rbLink2=new THREE.Mesh(new THREE.BoxGeometry(.35,.04,.06),darkMetal.clone());
  rbLink2.position.set(armBX+0.35,chuckW.y+0.04,armBZ);
  scene.add(rbLink2);procObjs.rbLink2=rbLink2;

  var ef1=new THREE.Mesh(new THREE.BoxGeometry(.30,.01,.02),metalMat.clone());
  ef1.position.set(procObjs.efStart.x,procObjs.efStart.y,procObjs.efStart.z+0.03);
  scene.add(ef1);procObjs.ef1=ef1;
  var ef2=new THREE.Mesh(new THREE.BoxGeometry(.30,.01,.02),metalMat.clone());
  ef2.position.set(procObjs.efStart.x,procObjs.efStart.y,procObjs.efStart.z-0.03);
  scene.add(ef2);procObjs.ef2=ef2;

  var rbWafer=new THREE.Mesh(new THREE.CylinderGeometry(.148,.148,.008,32),silicaMat.clone());
  rbWafer.name='Robot_Wafer_Mesh';
  rbWafer.position.copy(procObjs.efStart);rbWafer.visible=false;
  scene.add(rbWafer);procObjs.rbWafer=rbWafer;

  // ── UV 光束視覺化 ──────────────────────────────────────────────────────────
  // 正確光路（DUV scanner）：
  //   ArF Laser（右） → 水平 hBeam → 照明系統頂部
  //   → 垂直向下貫穿照明系統 → 穿過光罩（rmBaseY）→ 穿過投影鏡組 → 晶圓

  // 垂直光束起點：光罩上方 0.30m（避免使用 Illum_Barrel 節點，該節點 Y 偏低）
  var beamTop = rsY + 0.30;   // 照明系統底部（光罩稍上方）
  var beamBot = chuckW.y;
  var beamH   = beamTop - beamBot;
  var beamMidY= (beamTop + beamBot) / 2;

  // 主光束柱：寬頂窄底（照明出口寬 → 4:1 縮小投影 → 晶圓窄）
  var beamCyl=new THREE.Mesh(new THREE.CylinderGeometry(.055,.008,beamH,12),uvMat.clone());
  beamCyl.position.set(rsCX,beamMidY,rsCZ);beamCyl.visible=false;
  scene.add(beamCyl);procObjs.beamCyl=beamCyl;
  procObjs.beamMidY=beamMidY;procObjs.beamTop=beamTop;

  // 光罩處的光暈（表示光通過光罩）
  var reticlGlow=new THREE.Mesh(new THREE.CircleGeometry(.14,32),glowMat.clone());
  reticlGlow.rotation.x=-Math.PI/2;
  reticlGlow.position.set(rsCX,rmBaseY-0.002,rsCZ);reticlGlow.visible=false;
  scene.add(reticlGlow);procObjs.reticleGlow=reticlGlow;

  // 晶圓上的曝光光暈（小圓，4:1 縮小投影）
  var beamSpot=new THREE.Mesh(new THREE.CircleGeometry(.04,32),glowMat.clone());
  beamSpot.rotation.x=-Math.PI/2;
  beamSpot.position.set(rsCX,chuckW.y+0.002,rsCZ);beamSpot.visible=false;
  scene.add(beamSpot);procObjs.beamSpotGlow=beamSpot;

  // 水平入射光：ArF Laser（右側）→ 照明系統
  // 高度固定在 beamTop+0.05（照明系統出口，光在這裡轉為垂直向下）
  var hBSrcX = rsCX + 0.52;   // 右側（ArF 雷射方向）
  var hBLen  = 0.52;
  var hBMidX = rsCX + hBLen * 0.5;
  var hBY    = beamTop + 0.05; // 照明系統出口高度（垂直光束起點上方）
  var hBeam=new THREE.Mesh(new THREE.CylinderGeometry(.007,.007,hBLen,8),uvMat.clone());
  hBeam.rotation.z=Math.PI/2;
  hBeam.position.set(hBMidX,hBY,rsCZ);hBeam.visible=false;
  scene.add(hBeam);procObjs.hBeam=hBeam;

  beamPtLight=new THREE.PointLight(0x9900ff,0,1.4);
  beamPtLight.position.set(rsCX,chuckW.y+0.06,rsCZ);scene.add(beamPtLight);

  // GLB Wafer_Chuck / Wafer 動畫與製程動畫衝突，停止 GLB 動畫交由製程動畫統一管理
  if(mixer){mixer.stopAllAction();mixer=null;}

  console.log('[OK] Proc objects built. efStart:',
    procObjs.efStart.x.toFixed(2),procObjs.efStart.z.toFixed(2),
    '→ efEnd:',procObjs.efEnd.x.toFixed(2),procObjs.efEnd.z.toFixed(2));
}

// ── 製程順序動畫（32s 循環）──────────────────────────────────────────────────
// 時序：FOUP開→手臂取片→傳到載台→對準曝光→手臂取片→FOUP關
var PROC_T=32;

function _eio(t){return t<.5?2*t*t:(4-2*t)*t-1;}  // ease-in-out
function _c01(t){return Math.max(0,Math.min(1,t));}
function _ph(t,s,e){return _eio(_c01((t-s)/(e-s)));}  // phase 0→1 with ease

function updateProcessAnim(dt){
  if(!procObjs.rs||!gameStarted)return;
  procElapsed=(procElapsed+dt)%PROC_T;
  var t=procElapsed;

  var foupDoor=sceneMeshMap['FOUP_Door'];
  var wChuck  =sceneMeshMap['Wafer_Chuck'];
  var wWafer  =sceneMeshMap['Wafer'];
  var eS=procObjs.efStart, eE=procObjs.efEnd;

  // ── 0~2s / 25~27s: FOUP 門開關（GLB 局部 Y 座標）────────────────────────
  if(foupDoor){
    var fp=_ph(t,0,2)-_ph(t,25,27);
    foupDoor.position.y=0.82+fp*0.35;
  }

  // ── 機械手臂（世界座標插值）────────────────────────────────────────────
  var extP=_ph(t,2,5.5), retP=_ph(t,19.5,23);
  var netExt=_c01(extP-retP);
  // End Effector 從 efStart 插值到 efEnd（均為世界座標）
  var efX=eS.x+netExt*(eE.x-eS.x);
  var efY=eE.y;
  var efZ=eS.z+netExt*(eE.z-eS.z);

  if(procObjs.rbLink){
    procObjs.rbLink.position.x=eS.x-0.08+netExt*(eE.x-eS.x+0.08);
    procObjs.rbLink.position.z=eS.z+netExt*(eE.z-eS.z)*0.4;
    procObjs.rbLink.scale.x=1+netExt*0.9;
  }
  if(procObjs.rbLink2){
    procObjs.rbLink2.position.x=eS.x+0.18+netExt*(eE.x-eS.x-0.05);
    procObjs.rbLink2.position.z=eS.z+netExt*(eE.z-eS.z)*0.7;
    procObjs.rbLink2.scale.x=1+netExt*0.7;
  }
  if(procObjs.rbTurret){
    procObjs.rbTurret.position.x=eS.x+netExt*(eE.x-eS.x)*0.25;
    procObjs.rbTurret.position.z=eS.z+netExt*(eE.z-eS.z)*0.25;
  }
  if(procObjs.ef1)procObjs.ef1.position.set(efX,efY,efZ+0.03);
  if(procObjs.ef2)procObjs.ef2.position.set(efX,efY,efZ-0.03);

  // ── 手臂上的晶圓（3.5~8.5s 傳送中；19.5~23.5s 取回）──────────────────
  var rwShow=(t>=3.5&&t<8.5)||(t>=19.5&&t<23.5);
  if(procObjs.rbWafer){
    procObjs.rbWafer.visible=rwShow;
    if(rwShow)procObjs.rbWafer.position.set(efX,efY+0.005,efZ);
  }

  // ── 晶圓載台移動（GLB 局部座標）──────────────────────────────────────────
  // 鏡組（POB_Bottom）局部座標約 [0.10, *, -0.10]
  // 裝載位置 [-0.30, 0.00]；掃描中心應在鏡組正下方 [0.10, -0.10]
  var LENS_LX=0.10, LENS_LZ=-0.10; // 鏡組正下方局部座標
  var LOAD_LX=-0.30,LOAD_LZ=0.00;  // 裝載/卸載位置局部座標

  // 8.5~9.5s: 晶圓從裝載位置移到鏡組下方（定位）
  var posP=_ph(t,8.5,9.5);
  // 9.5~19s: 在鏡組下方做步進掃描
  var scanning=(t>=9.5&&t<19);
  // 19~20s: 掃描結束，移回裝載位置（給機械手臂取片）
  var retLoadP=_ph(t,19,20);

  if(wChuck&&wWafer){
    var lx,lz;
    if(t>=8.5&&t<9.5){
      // 定位：從裝載位置平滑移到鏡組下方
      lx=LOAD_LX+posP*(LENS_LX-LOAD_LX);
      lz=LOAD_LZ+posP*(LENS_LZ-LOAD_LZ);
    } else if(scanning){
      // 步進掃描：以鏡組為中心做 XZ 蛇行掃描
      var sp=_c01((t-9.5)/9.5);
      lx=LENS_LX+0.09*Math.sin(sp*Math.PI*7)*Math.cos(sp*Math.PI*0.5);
      lz=LENS_LZ+0.07*Math.cos(sp*Math.PI*5)*Math.sin(sp*Math.PI*0.7);
    } else if(t>=19&&t<20){
      // 回到裝載位置
      lx=LENS_LX+retLoadP*(LOAD_LX-LENS_LX);
      lz=LENS_LZ+retLoadP*(LOAD_LZ-LENS_LZ);
    } else {
      lx=LOAD_LX; lz=LOAD_LZ;
    }
    wChuck.position.x=lx; wWafer.position.x=lx;
    wChuck.position.z=lz; wWafer.position.z=lz;
  }

  // ── 10~19s: UV 曝光光束（追蹤 Chuck 世界座標）───────────────────────────
  var exposing=(t>=10&&t<19);
  if(procObjs.beamCyl)procObjs.beamCyl.visible=exposing;
  if(procObjs.beamSpotGlow)procObjs.beamSpotGlow.visible=exposing;
  if(procObjs.reticleGlow)procObjs.reticleGlow.visible=exposing;
  if(procObjs.hBeam)procObjs.hBeam.visible=exposing;
  if(beamPtLight){
    if(exposing&&wChuck){
      // 用 getWorldPosition 取 Chuck 當前世界座標（含掃描偏移）
      var cwp=new THREE.Vector3();
      wChuck.getWorldPosition(cwp);
      var pulse=0.5+0.5*Math.sin(t*Math.PI*12);
      beamPtLight.intensity=pulse*2.0;
      if(procObjs.beamCyl){
        procObjs.beamCyl.material.opacity=0.25+pulse*0.45;
        // 垂直光束只追蹤 X/Z（chuck 掃描位移），Y 保持固定（從光罩頂到晶圓）
        procObjs.beamCyl.position.x=cwp.x;
        procObjs.beamCyl.position.z=cwp.z;
      }
      if(procObjs.reticleGlow){
        // 光罩光暈：固定在光罩平面，但 X/Z 隨 chuck 微幅跟隨（模擬掃描窗口）
        procObjs.reticleGlow.material.opacity=0.3+pulse*0.4;
        procObjs.reticleGlow.position.x=cwp.x;
        procObjs.reticleGlow.position.z=cwp.z;
      }
      if(procObjs.hBeam){
        // 水平入射光束：強度隨脈衝閃爍
        procObjs.hBeam.material.opacity=0.2+pulse*0.35;
      }
      if(procObjs.beamSpotGlow){
        procObjs.beamSpotGlow.material.opacity=0.4+pulse*0.5;
        procObjs.beamSpotGlow.position.x=cwp.x;
        procObjs.beamSpotGlow.position.z=cwp.z;
      }
      beamPtLight.position.x=cwp.x;beamPtLight.position.z=cwp.z;
    } else {beamPtLight.intensity=0;}
  }

  // ── 10~19s: 光罩掃描（世界座標 Y 軸小幅往復）────────────────────────────
  if(procObjs.rm&&procObjs.rmMarks){
    var rmY=exposing?
      procObjs.rmBaseY+0.012*Math.sin(t*Math.PI*3.5):procObjs.rmBaseY;
    procObjs.rm.position.y=rmY;
    procObjs.rmMarks.forEach(function(m){m.position.y=rmY+0.003;});
  }
}

// ── Render loop ───────────────────────────────────────────────────────────────
function animate(){
  requestAnimationFrame(animate);
  var dt=clock.getDelta();
  if(mixer)mixer.update(dt); // GLB animations
  updateProcessAnim(dt);     // 製程順序動畫
  // Movement
  if(controls.isLocked&&gameStarted){
    velocity.x-=velocity.x*9*dt;velocity.z-=velocity.z*9*dt;
    var sp=5.5;
    if(moveF)velocity.z-=sp*dt;if(moveB)velocity.z+=sp*dt;
    if(moveL)velocity.x-=sp*dt;if(moveR)velocity.x+=sp*dt;
    controls.moveRight(velocity.x*dt);controls.moveForward(-velocity.z*dt);
    camera.position.y=1.6;
  }
  // Raycasting
  if(gameStarted){
    raycaster.setFromCamera(new THREE.Vector2(0,0),camera);
    var hits=raycaster.intersectObjects(allMeshes);
    if(hoveredObj){
      if(origMats.has(hoveredObj))hoveredObj.material=origMats.get(hoveredObj);
      hoveredObj=null;
      if(!inspecting&&!hmiOpen){$prompt.style.display='none';$xhair.classList.remove('hit');}
    }
    if(hits.length>0){
      var obj=hits[0].object;
      var inf=getInfo(obj);
      if(inf){
        if(!origMats.has(obj))origMats.set(obj,obj.material);
        obj.material=hlMat;hoveredObj=obj;
        if(!inspecting&&!hmiOpen){
          var isHMITrigger=(obj.name==='HMI_Screen'||inf.label==='控制系統'||inf.label==='HMI 控制面板');
          $prompt.textContent=(isHMITrigger?'[E] 開啟 HMI 控制面板（感測器 & ERROR Log）':'[E] 檢查: '+inf.label);
          $prompt.style.left=(CW/2)+'px';$prompt.style.display='block';
          $xhair.classList.add('hit');
        }
      }
    }
  }
  renderer.render(scene,camera);
}
animate();

// ── Resize ────────────────────────────────────────────────────────────────────
window.addEventListener('resize',function(){
  CW=window.innerWidth-300;CH=window.innerHeight;
  camera.aspect=CW/CH;camera.updateProjectionMatrix();
  renderer.setSize(CW,CH);
  renderer.domElement.style.width=CW+'px';renderer.domElement.style.height=CH+'px';
  var ss=document.getElementById('start-screen');
  if(ss.style.display!=='none'){ss.style.width=CW+'px';ss.style.height=CH+'px';}
  if($pause.style.display!=='none'){$pause.style.width=CW+'px';}
  if($hmiOverlay.style.display!=='none'){$hmiOverlay.style.width=CW+'px';}
  $xhair.style.left=(CW/2-12)+'px';$prompt.style.left=(CW/2)+'px';
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
    global _system_instance
    print("[OK] Loading training system…")
    _system_instance = SimulationTrainingSystem(secom_data_path,
                                                use_ai_mentor=use_ai_mentor)

    # Monkey-patch _generate_equipment_diagram to capture state for HMI
    _orig_gen = _system_instance._generate_equipment_diagram.__func__

    def _patched_gen(self, state):
        _build_hmi_data(state)
        return _orig_gen(self, state)

    _system_instance._generate_equipment_diagram = types.MethodType(
        _patched_gen, _system_instance)
    print("[OK] Training system ready.")

    p = _start_server(str(_STATIC), port)
    _write_viewer_html(_STATIC)
    url = f"http://127.0.0.1:{p}/viewer.html"
    print(f"[OK] Game URL: {url}")
    return url


def create_firstperson_interface(secom_data_path: str,
                                  use_ai_mentor: bool = True):
    url = start_game(secom_data_path, use_ai_mentor)

    class _FakeDemo:
        def launch(self, **kwargs):
            import webbrowser
            print(f"\n[GAME] Opening: {url}")
            webbrowser.open(url)
            print("Press Ctrl+C to stop.\n")
            try:
                threading.Event().wait()
            except KeyboardInterrupt:
                pass

    return _FakeDemo()
