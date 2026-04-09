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

# ── 物理模型 + SECOM 噪聲模型 ─────────────────────────────────────────────
try:
    from core.lens_heating_model import get_engine as _get_physics_engine
    from core.secom_noise_model  import get_noise_model as _get_noise_model
    _physics_engine = _get_physics_engine()
    _noise_model    = _get_noise_model()
    _PHYSICS_OK = True
    print("[OK] Physics engine + SECOM noise model loaded.")
except Exception as _e:
    _PHYSICS_OK = False
    _physics_engine = None
    _noise_model    = None
    print(f"[WARN] Physics engine not loaded: {_e}")

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

# ── 動作評估 Session ──────────────────────────────────────────────────────────
try:
    from core.sop_definitions import ActionSession, SOP_DEFINITIONS
    _SOP_OK = True
except Exception:
    _SOP_OK = False

_action_session: "ActionSession | None" = None
_action_session_lock = threading.Lock()

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
        parts = []
        if sc_name:
            parts.append(f"現在跑的是「{sc_name}」這個情境，我幫你看一下各系統狀態：")
        else:
            parts.append("幫你快速確認一下各系統狀態：")
        for s in _hmi_cache["sensors"]:
            icon = {"normal": "🟢", "warning": "🟡", "critical": "🔴"}.get(s["status"], "⚪")
            parts.append(f"  {icon} {s['label']}: {s['value']} {s['unit']}")
        if alarms:
            parts.append(f"\n目前有 {len(alarms)} 個警報要注意：")
            for a in alarms[:3]:
                parts.append(f"  {a['system']} — {a['msg']}")
        else:
            parts.append("\n目前沒有警報，各子系統都正常。")
        return "\n".join(p for p in parts if p)

    if topic == "cooling":
        s = sensors.get("冷卻水流量") or sensors.get("冷卻水溫度")
        t = sensors.get("冷卻水溫度")
        lines = ["幫你看一下冷卻系統："]
        if sensors.get("冷卻水流量"):
            lines.append(f"  流量：{_fmt(sensors['冷卻水流量'])}")
        if t:
            lines.append(f"  水溫：{_fmt(t)}")
        if not lines[1:]:
            lines.append("  感測器資料還沒載入，稍等一下。")
        alm = [a for a in alarms if "冷卻" in a.get("system", "")]
        if alm:
            lines.append(f"有警報：{alm[0]['msg']}")
        return "\n".join(lines)

    if topic == "temp":
        s = sensors.get("投影鏡組溫度")
        return f"鏡組溫度現在是 {_fmt(s)}" if s else ""

    if topic == "light":
        s = sensors.get("光源強度")
        return f"光源強度 {_fmt(s)}" if s else ""

    if topic == "vacuum":
        s = sensors.get("真空壓力")
        return f"真空壓力現在是 {_fmt(s)}" if s else ""

    if topic == "stage":
        sx = sensors.get("載台位置X"); sy = sensors.get("載台位置Y")
        parts = ["載台位置："]
        if sx: parts.append(f"  X: {_fmt(sx)}")
        if sy: parts.append(f"  Y: {_fmt(sy)}")
        return "\n".join(parts) if len(parts) > 1 else ""

    if topic == "restart":
        return "重啟的話，先確認沒有在跑曝光程序，然後依序把子系統關掉，等個 30 秒再重新啟動，不要直接硬關。"

    if topic == "diag":
        lines = ["診斷日誌幫你拉一下："]
        if alarms:
            for a in alarms:
                lines.append(f"  {a['code']} | {a['system']} | {a['level'].upper()} | {a['msg']}")
        else:
            lines.append("  目前沒有異常記錄，系統運行正常。")
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
        if norm is not None and warn is not None:
            if low_bad:
                range_str = f"{norm} {unit}（警告 < {warn}）"
            else:
                range_str = f"{norm} {unit}（警告 > {warn}）"
        else:
            range_str = f"{norm} {unit}" if norm else "-"
        sensors.append({
            "label": label, "value": round(float(val), 3),
            "unit": unit, "status": status,
            "normal": range_str,
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
        try:
            if   self.path == "/api/status":       self._api_status()
            elif self.path == "/api/tick":          self._api_tick()
            elif self.path == "/api/hmi":           self._api_hmi()
            elif self.path == "/api/qa_pending":    self._api_qa_pending()
            elif self.path == "/api/wafer_map":     self._api_wafer_map()
            elif self.path == "/api/process_window": self._api_process_window()
            elif self.path == "/api/secom_summary":  self._api_secom_summary()
            else: super().do_GET()
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        try:
            if   self.path == "/api/start":    self._api_start()
            elif self.path == "/api/chat":     self._api_chat()
            elif self.path == "/api/exposure": self._api_exposure()
            elif self.path == "/api/fault":    self._api_fault()
            elif self.path == "/api/action":   self._api_action()
            elif self.path == "/api/hint":     self._api_hint()
            else: self.send_response(404); self.end_headers()
        except Exception as e:
            print(f"[POST {self.path}] 未捕捉例外: {e}")
            try:
                self._json({"ok": False, "error": str(e), "ai_msg": "⚠ 伺服器內部錯誤，請稍後重試。"})
            except Exception:
                pass

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

    def _latest_sys(self, msgs):
        """取最新一條系統狀態訊息（role=sys_status）"""
        for m in reversed(msgs or []):
            if isinstance(m, dict) and m.get("role") == "sys_status":
                return m.get("content", "")
        return ""

    # ── API endpoints ─────────────────────────────────────────────────────────
    def _api_status(self):
        with _session_lock:
            self._json({"started": _session["started"],
                        "msgs": self._msgs_to_list(_session["msgs"])})

    def _api_qa_pending(self):
        """GET /api/qa_pending — 前端進入內部時查詢是否有待答問題
        - pending_follow_up（closing_reflection/理論問題）：一律遮擋
        - proactive_mentor.pending_followup（主動提問）：
            尚未開始操作時（無 action_session）遮擋；操作中不遮擋
        """
        if not _system_instance:
            self._json({"qa_pending": False}); return
        if _system_instance.pending_follow_up:
            self._json({"qa_pending": True}); return
        pm = _system_instance.proactive_mentor
        pf = pm.pending_followup if pm else None
        # is_followup_round=True 是操作引導追問，不遮擋
        proactive_q = bool(pf and not pf.get('is_followup_round', False))
        self._json({"qa_pending": proactive_q})

    def _api_tick(self):
        with _session_lock:
            if not _session["started"]:
                self._json({"ok": False, "ai_msg": ""}); return
            snap = dict(_session)
        eq, dash, eq_st, msgs, log = _system_instance.auto_progress(
            snap["eq"], snap["dash"], snap["eq_st"], snap["msgs"], snap["log"])
        with _session_lock:
            _session.update(eq=eq, dash=dash, eq_st=eq_st, msgs=msgs, log=log)
        self._json({"ok": True,
                    "ai_msg": self._latest_ai(msgs),
                    "sys_msg": self._latest_sys(msgs),
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
        # 將 scenario_type 轉成 SOP fault_type，讓前端能正確初始化 _activeFaults
        _SCENARIO_TO_SOP = {
            'alignment_drift':       'stage_error',
            'optical_contamination': 'contamination',
            'power_fluctuation':     'dose_drift',
            'cooling_failure':       'lens_hotspot',
            'vacuum_leak':           'focus_drift',
            'filter_clogged':        'lens_hotspot',
        }
        stype = ''
        if _system_instance.current_scenario:
            stype = _system_instance.current_scenario.get('scenario_type', '')
        sop_fault_type = _SCENARIO_TO_SOP.get(stype, '')
        # 若有 pending followup（proactive mentor 初始問題），告訴前端需遮罩
        qa_pending = bool(
            _system_instance.pending_follow_up or
            (_system_instance.proactive_mentor and
             _system_instance.proactive_mentor.pending_followup)
        )
        self._json({"ok": True,
                    "ai_msg": self._latest_ai(msgs) or "情境已開始，請開始檢查設備。",
                    "sop_fault_type": sop_fault_type,
                    "qa_pending": qa_pending,
                    "msgs": self._msgs_to_list(msgs)})

    def _api_chat(self):
        data = self._read_json()
        text = data.get("text", "").strip()
        if not text:
            self._json({"ok": False, "ai_msg": ""}); return
        with _session_lock:
            snap = dict(_session)
        try:
            _, eq, dash, eq_st, msgs, log = _system_instance.process_user_input(
                text, snap["eq"], snap["dash"], snap["eq_st"],
                snap["msgs"], snap["log"])
        except Exception as e:
            import traceback
            print(f"[_api_chat] process_user_input 例外: {e}")
            traceback.print_exc()
            self._json({"ok": False, "ai_msg": f"學長暫時無法回應，請稍後再試。（{type(e).__name__}）"})
            return
        with _session_lock:
            _session.update(eq=eq, dash=dash, eq_st=eq_st, msgs=msgs, log=log)
        ai_reply = self._latest_ai(msgs)
        # NLU 無法識別 target 時（"你檢查了None"），改用 HMI 快取生成有意義回應
        if not ai_reply or "你檢查了None" in ai_reply or "你檢查了未知" in ai_reply:
            smart = _smart_response(text)
            if smart:
                ai_reply = smart
        # pending_follow_up 一律遮擋
        # pending_follow_up（closing_reflection）一律遮擋
        # proactive pending_followup：第一輪知識問題遮擋，第二輪（is_followup_round）不遮擋
        if _system_instance.pending_follow_up:
            qa_pending = True
        else:
            pm = _system_instance.proactive_mentor
            pf = pm.pending_followup if pm else None
            # is_followup_round=True 表示是操作引導性追問，不遮擋，讓使用者邊操作邊回答
            qa_pending = bool(pf and not pf.get('is_followup_round', False))
        # 情境結束旗標
        session_ended = not bool(_system_instance.session_active)
        sys_msg = self._latest_sys(msgs)
        self._json({"ok": True, "ai_msg": ai_reply, "qa_pending": qa_pending,
                    "session_ended": session_ended, "sys_msg": sys_msg,
                    "msgs": self._msgs_to_list(msgs)})

    # ── Physics API ──────────────────────────────────────────────────────────
    def _api_exposure(self):
        """POST /api/exposure  { dose, focus, na, sigma, fault }"""
        if not _PHYSICS_OK:
            self._json({"ok": False, "error": "Physics engine not available"}); return
        data = self._read_json()
        dose  = float(data.get("dose",  30.0))
        focus = float(data.get("focus",  0.0))
        na    = float(data.get("na",    0.75))
        sigma = float(data.get("sigma", 0.75))
        fault = data.get("fault", None)

        if fault:
            _noise_model.inject_fault(fault)
        else:
            _noise_model.clear_fault()

        noise_sigma = _noise_model.get_noise_sigma()
        result = _physics_engine.expose_wafer(
            dose=dose, focus=focus, na=na, sigma=sigma,
            noise_sigma=noise_sigma)
        result["secom"] = _noise_model.get_feature_summary()
        self._json({"ok": True, "result": result})

    def _api_wafer_map(self):
        """GET /api/wafer_map — 回傳最新一筆 CDU + overlay 歷史"""
        if not _PHYSICS_OK:
            self._json({"ok": False, "history": []}); return
        history = _physics_engine.get_history()
        lens_state = _physics_engine.get_lens_state()
        self._json({"ok": True,
                    "history": history[-30:],    # 最近 30 片
                    "lens_state": lens_state,
                    "secom": _noise_model.get_feature_summary()})

    def _api_process_window(self):
        """GET /api/process_window"""
        if not _PHYSICS_OK:
            self._json({"ok": False}); return
        pw = _physics_engine.get_process_window()
        self._json({"ok": True, "process_window": pw})

    def _api_secom_summary(self):
        """GET /api/secom_summary"""
        if not _PHYSICS_OK:
            self._json({"ok": False}); return
        self._json({"ok": True,
                    "secom": _noise_model.get_feature_summary(),
                    "stats": _noise_model.get_pass_fail_stats()})

    def _api_fault(self):
        """POST /api/fault  { type: 'lens_hotspot' | null }"""
        if not _PHYSICS_OK:
            self._json({"ok": False}); return
        data = self._read_json()
        ft = data.get("type", None)
        if ft:
            _noise_model.inject_fault(ft)
        else:
            _noise_model.clear_fault()
        self._json({"ok": True, "fault": _noise_model.get_fault_info(),
                    "health": _noise_model.get_health_score()})

    def _api_action(self):
        """POST /api/action  { component, action, fault_type }
        操作者互動一個零件並選擇動作 → AI 評估對錯 → 回傳回饋與進度
        """
        global _action_session
        if not _SOP_OK:
            self._json({"ok": False, "feedback": "SOP 模組未載入"}); return

        data = self._read_json()
        component  = data.get("component", "")
        action     = data.get("action", "")
        fault_type = data.get("fault_type", None)

        with _action_session_lock:
            # 若故障類型改變或尚無 session，初始化新 session
            if fault_type and fault_type in SOP_DEFINITIONS:
                if _action_session is None or _action_session.fault_type != fault_type:
                    _action_session = ActionSession(fault_type)

            if _action_session is None:
                # 沒有活躍故障，直接送給 AI 學長聊天
                self._json({"ok": True, "feedback": "目前沒有活躍故障，可以自由探索環境。",
                            "no_fault": True}); return

            result = _action_session.evaluate(component, action)
            adaptive_mode = result.get("adaptive_mode", "standard")

            # ── 1. 同步 AI 學長教學風格（teaching_mode）──────────────────────
            if _system_instance and _system_instance.ai_mentor:
                mode_map = {
                    'challenge':   'challenge',
                    'standard':    'standard',
                    'scaffolding': 'scaffolding',
                    'remedial':    'remedial',
                }
                _system_instance.ai_mentor.set_teaching_mode(
                    mode_map.get(adaptive_mode, 'standard'))

            # ── 2. 同步 ProactiveMentor.difficulty（讓 Socratic 追問一致）──
            if _system_instance and hasattr(_system_instance, 'proactive_mentor') \
                    and _system_instance.proactive_mentor:
                difficulty_map = {
                    'challenge':   'challenge',
                    'standard':    'standard',
                    'scaffolding': 'easy',
                    'remedial':    'easy',
                }
                _system_instance.proactive_mentor.difficulty = \
                    difficulty_map.get(adaptive_mode, 'standard')

            # ── 3. 操作錯誤時用 LLM 生成自然回饋（替換靜態模板）────────────
            if not result.get("correct") and _system_instance \
                    and _system_instance.ai_mentor:
                sop = SOP_DEFINITIONS.get(_action_session.fault_type if _action_session else "", {})
                fault_system = sop.get("fault_system", "")
                try:
                    from concurrent.futures import ThreadPoolExecutor
                    def _get_fb():
                        return _system_instance.ai_mentor.provide_sop_wrong_feedback(
                            component=component,
                            action=action,
                            fault_system=fault_system,
                            mistake_level=result.get("mistake_level", "full_wrong"),
                            template_hint=result.get("feedback", ""),
                        )
                    with ThreadPoolExecutor(max_workers=1) as ex:
                        ai_fb = ex.submit(_get_fb).result(timeout=15)
                except Exception:
                    ai_fb = None
                if ai_fb:
                    result["feedback"] = ai_fb   # LLM 回饋取代模板

            # ── 4. 故障排除完成，產生反思問題並重置 session ────────────────
            if result.get("all_done"):
                if _PHYSICS_OK:
                    _noise_model.clear_fault()
                ft = _action_session.fault_type if _action_session else ""
                current_score = result.get("score", 70)
                # 用 AI 學長生成反思收尾問題（一定要有 fallback）
                _CLOSING_FALLBACKS = {
                    'contamination':  '故障排除完成！最後問你：光學污染通常是怎麼發生的？你會怎麼預防它？',
                    'stage_error':    '故障排除完成！最後問你：對準誤差超規，最直接影響的是哪個製程指標？為什麼？',
                    'lens_hotspot':   '故障排除完成！最後問你：鏡片過熱對曝光品質的最直接影響是什麼？',
                    'dose_drift':     '故障排除完成！最後問你：劑量漂移超規，會對光阻製程造成什麼影響？',
                    'focus_drift':    '故障排除完成！最後問你：焦距漂移超規，對解析度和製程視窗有什麼影響？',
                }
                closing_q = _CLOSING_FALLBACKS.get(ft,
                    '故障排除完成！最後問你：這次故障的根本原因是什麼？你從處理過程中學到了什麼？')
                if _system_instance and _system_instance.ai_mentor:
                    try:
                        from concurrent.futures import ThreadPoolExecutor
                        def _gen_closing():
                            return _system_instance.ai_mentor.generate_closing_question(ft, current_score)
                        with ThreadPoolExecutor(max_workers=1) as ex:
                            llm_q = ex.submit(_gen_closing).result(timeout=15)
                        if llm_q and llm_q.strip():
                            closing_q = llm_q.strip()
                    except Exception as e:
                        print(f"[closing_q] LLM 生成失敗，用 fallback: {e}")
                # 存入 pending_follow_up
                if _system_instance:
                    _system_instance.pending_follow_up = {
                        'question': closing_q,
                        'type': 'closing_reflection',
                        'fault_type': ft,
                    }
                result["closing_question"] = closing_q
                _action_session = None

        # proactive_mentor Socratic 追問屬對話式，不遮擋操作
        qa_pending = bool(_system_instance.pending_follow_up)
        self._json({"ok": True, "qa_pending": qa_pending, **result})

    def _api_hint(self):
        """POST /api/hint  { fault_type }
        操作者求助學長 → 扣 5 分 → 依自適應模式給提示
        """
        global _action_session
        if not _SOP_OK:
            self._json({"ok": False, "hint": "SOP 模組未載入"}); return

        data = self._read_json()
        fault_type = data.get("fault_type", None)

        with _action_session_lock:
            if fault_type and fault_type in SOP_DEFINITIONS:
                if _action_session is None or _action_session.fault_type != fault_type:
                    _action_session = ActionSession(fault_type)

            if _action_session is None:
                self._json({"ok": True, "hint": "目前沒有活躍故障。", "score": 100}); return

            result = _action_session.get_hint()

        self._json({"ok": True, **result})


# ── 啟動伺服器 ────────────────────────────────────────────────────────────────

def _start_server(directory: str, port: int = 8765) -> int:
    import os
    global _server_port
    if _server_port:
        return _server_port
    # Render / 雲端部署時使用 PORT 環境變數，本機則用傳入的 port
    port = int(os.environ.get("PORT", port))
    # 0.0.0.0 允許外部連線（雲端部署必要）；本機測試仍可正常使用
    bind_host = "0.0.0.0"
    handler = functools.partial(_GameHandler, directory=directory)
    for p in range(port, port + 20):
        try:
            srv = http.server.HTTPServer((bind_host, p), handler)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            _server_port = p
            print(f"[OK] Game server: http://{bind_host}:{p}/")
            return p
        except OSError:
            continue
    raise RuntimeError("No available port")


# ══════════════════════════════════════════════════════════════════════════════
# viewer.html — 完整第一人稱遊戲
# ══════════════════════════════════════════════════════════════════════════════

_VIEWER_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>ASML Virtual Fab</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:100%;height:100%;overflow:hidden;background:#050d1a;
  font-family:Consolas,"Courier New",monospace;color:#cde;}
canvas{position:fixed;top:0;left:0;display:block;}
/* ── 3D 零件名稱標籤（DOM 疊層，論文用）── */
#label-layer{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:10;}
.eq-label{
  position:absolute;
  transform:translate(-50%,-50%);
  background:rgba(8,18,50,0.88);
  border:2px solid rgba(100,180,255,0.90);
  border-radius:8px;
  padding:5px 16px;
  color:#ffffff;
  font-family:"Arial Black","Arial",sans-serif;
  font-weight:900;
  font-size:15px;
  letter-spacing:0.5px;
  white-space:nowrap;
  text-shadow:0 0 8px rgba(80,160,255,0.8);
  display:none;
  user-select:none;
}
/* 標題標籤（機型名稱，固定在畫面頂部）*/
.eq-label-title{
  position:fixed;
  top:14px;
  left:50%;
  transform:translateX(-50%);
  background:rgba(8,18,50,0.90);
  border:2px solid rgba(100,180,255,0.95);
  border-radius:10px;
  padding:7px 28px;
  color:#ffffff;
  font-family:"Arial Black","Arial",sans-serif;
  font-weight:900;
  font-size:18px;
  letter-spacing:1px;
  white-space:nowrap;
  text-shadow:0 0 10px rgba(80,160,255,0.9);
  display:none;
  user-select:none;
  z-index:11;
}

/* ── Loading ── */
#loading-screen{position:fixed;inset:0;background:#050d1a;z-index:900;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;}
#load-pct{font-size:32px;color:#ffa500;}
.bar-wrap{width:280px;height:6px;background:#0a1828;border-radius:3px;}
#load-bar{height:6px;background:linear-gradient(90deg,#4af,#ffa500);
  border-radius:3px;width:0;transition:width .25s;}

/* ── Start Screen ── */
#start-screen{position:fixed;top:0;left:0;width:100%;height:100%;z-index:800;display:none;
  flex-direction:column;align-items:center;justify-content:flex-end;gap:18px;
  background:transparent;padding-bottom:48px;pointer-events:none;}
#start-screen-panel{display:flex;flex-direction:column;align-items:center;gap:18px;
  background:rgba(10,8,0,.78);border:1px solid rgba(255,200,0,.3);
  border-radius:12px;padding:28px 44px;backdrop-filter:blur(6px);
  pointer-events:all;}
#start-screen h1{font-size:20px;letter-spacing:3px;color:#ffe066;text-align:center;margin:0;}
#start-screen h2{font-size:11px;color:#ccaa44;letter-spacing:2px;text-align:center;margin:0;}
.hint{font-size:11px;color:#ccaa66;text-align:center;line-height:2.1;max-width:440px;}
.hint b{color:#ffdd55;}
#diff-row{display:flex;align-items:center;gap:12px;}
#difficulty{background:#1a1000;border:1px solid #664400;color:#ffcc44;
  padding:8px 18px;border-radius:6px;font:13px Consolas,monospace;}
#start-btn{background:linear-gradient(135deg,#332200,#664400);
  border:2px solid #ffaa00;color:#ffdd55;padding:14px 44px;border-radius:8px;
  font:15px Consolas,monospace;cursor:pointer;letter-spacing:2px;transition:.2s;}
#start-btn:hover{box-shadow:0 0 24px rgba(255,180,0,.5);color:#fff;}

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
.qbtn-operate{border-color:#5a3010;color:#ffa060;}
.qbtn-operate:hover{border-color:#ffa060;background:rgba(40,20,5,.9);}
.action-sec{font-size:10px;letter-spacing:1px;margin:8px 0 4px;padding:2px 0;border-bottom:1px solid #1a2a3a;}
.action-sec-inspect{color:#4af;}
.action-sec-operate{color:#ffa060;}
#inspect-close{color:#5a8a9a;font-size:10px;margin-top:6px;cursor:pointer;text-align:center;}
#inspect-close:hover{color:#4af;}
#score-bar{padding:7px 14px;background:rgba(5,13,26,.95);border-bottom:1px solid #1a4a7c;
  display:flex;justify-content:space-between;align-items:center;flex-shrink:0;}
#score-val{color:#4fc;font-size:13px;font-weight:bold;font-family:Consolas,monospace;}
#fault-prog{color:#ffa500;font-size:10px;font-family:Consolas,monospace;}
#hint-btn{background:rgba(60,30,5,.9);border:1px solid #a06030;color:#ffa060;
  padding:5px 10px;border-radius:5px;font:10px Consolas,monospace;cursor:pointer;
  width:calc(100% - 20px);margin:5px 10px 0;transition:.2s;}
#hint-btn:hover{border-color:#ffa060;background:rgba(80,40,5,.9);}
#hint-btn:disabled{opacity:.4;cursor:not-allowed;}

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
/* ── Maintenance Panel ── */
#maint-overlay{position:fixed;top:0;left:0;width:100%;height:100%;z-index:700;
  display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.65);}
#maint-modal{background:linear-gradient(180deg,#07100e,#050e0c);width:520px;max-height:82vh;
  border:1px solid #1a6a4c;border-radius:12px;display:flex;flex-direction:column;
  overflow:hidden;box-shadow:0 0 40px rgba(64,255,170,.12);}
#maint-hdr{background:linear-gradient(135deg,#0a1e18,#081814);
  border-bottom:2px solid #1a5a3c;padding:13px 18px;
  display:flex;justify-content:space-between;align-items:center;flex-shrink:0;}
#maint-hdr-title{color:#4fc;font-size:13px;font-weight:bold;letter-spacing:1.5px;}
#maint-hdr-sub{color:#5a9a7a;font-size:11px;margin-top:2px;}
#maint-close-btn{background:rgba(255,68,68,.15);border:1px solid #ff4444;color:#ff4444;
  padding:5px 14px;border-radius:6px;font:11px Consolas,monospace;cursor:pointer;}
#maint-body{overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;}
.maint-step{display:flex;gap:12px;align-items:flex-start;padding:12px 14px;
  border-radius:8px;border:1px solid #1a3a2c;background:rgba(10,24,18,.6);
  cursor:pointer;transition:.2s;}
.maint-step:hover{border-color:#2a6a4c;background:rgba(10,30,22,.8);}
.maint-step.done{border-color:#1a5a3c;background:rgba(10,40,28,.8);cursor:default;opacity:.7;}
.maint-step.active{border-color:#4fc;background:rgba(10,40,30,.9);box-shadow:0 0 12px rgba(64,255,192,.15);}
.maint-step.locked{opacity:.4;cursor:not-allowed;}
.maint-step-no{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:12px;font-weight:bold;flex-shrink:0;margin-top:1px;}
.maint-step.done .maint-step-no{background:#1a5a3c;color:#4fc;}
.maint-step.active .maint-step-no{background:#1a6a4c;color:#4fc;box-shadow:0 0 8px rgba(64,255,192,.4);}
.maint-step.locked .maint-step-no,.maint-step:not(.done):not(.active):not(.locked) .maint-step-no
  {background:#0a2018;color:#5a8a7a;}
.maint-step-info{flex:1;}
.maint-step-title{font-size:12px;font-weight:bold;color:#9de;margin-bottom:3px;}
.maint-step.done .maint-step-title{color:#5a9a7a;}
.maint-step-desc{font-size:11px;color:#6a9a8a;line-height:1.5;}
.maint-step-action{display:none;margin-top:8px;}
.maint-step.active .maint-step-action{display:block;}
.maint-action-btn{background:linear-gradient(135deg,#0a3028,#0d4038);
  border:1px solid #4fc;color:#4fc;padding:7px 18px;border-radius:6px;
  font-size:11px;cursor:pointer;letter-spacing:.5px;}
.maint-action-btn:hover{background:linear-gradient(135deg,#0d4038,#1a6050);}
.maint-progress{height:4px;background:#0a2018;border-radius:2px;overflow:hidden;margin-bottom:4px;}
.maint-progress-bar{height:100%;background:linear-gradient(90deg,#1a9a6c,#4fc);
  border-radius:2px;transition:width .4s;}
.maint-status{font-size:11px;color:#5a9a7a;display:flex;justify-content:space-between;}
.maint-complete{text-align:center;padding:20px;color:#4fc;font-size:14px;display:none;}
/* ── CDU Tab ── */
#hmi-tabs{display:flex;gap:0;border-bottom:1px solid #1a4a7c;flex-shrink:0;padding:0 14px;}
.hmi-tab{padding:8px 18px;font-size:11px;letter-spacing:1px;color:#5a8a9a;
  cursor:pointer;border-bottom:2px solid transparent;transition:.2s;}
.hmi-tab:hover{color:#9ab;}
.hmi-tab.active{color:#4af;border-bottom-color:#4af;}
#cdu-panel{display:none;flex-direction:column;gap:14px;padding:14px;}
.cdu-controls{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end;}
.cdu-ctrl{display:flex;flex-direction:column;gap:4px;min-width:110px;}
.cdu-ctrl label{font-size:10px;color:#6ab;letter-spacing:1px;}
.cdu-ctrl input[type=range]{width:100%;accent-color:#4af;}
.cdu-ctrl select{background:#0a1828;border:1px solid #1a4a7c;color:#cde;
  padding:4px 8px;border-radius:4px;font-size:11px;}
.cdu-ctrl .val-display{font-size:11px;color:#4af;font-family:Consolas,monospace;text-align:right;}
#cdu-expose-btn{background:linear-gradient(135deg,#0a2a4a,#0d3a6a);
  border:1px solid #4af;color:#4af;padding:8px 20px;border-radius:6px;
  font-size:12px;cursor:pointer;letter-spacing:1px;align-self:flex-end;}
#cdu-expose-btn:hover{background:linear-gradient(135deg,#0d3a6a,#1050a0);}
#cdu-expose-btn:disabled{opacity:.5;cursor:not-allowed;}
.cdu-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;}
.cdu-metric{background:rgba(10,18,32,.8);border:1px solid #1a3a5c;
  border-radius:6px;padding:10px;text-align:center;}
.cdu-metric .label{font-size:9px;color:#6ab;letter-spacing:1px;margin-bottom:4px;}
.cdu-metric .value{font-size:16px;font-weight:bold;font-family:Consolas,monospace;color:#4af;}
.cdu-metric .unit{font-size:9px;color:#5a8a9a;}
.cdu-metric.warn .value{color:#ffaa00;}
.cdu-metric.alarm .value{color:#ff4444;}
#cdu-map-canvas{border:1px solid #1a3a5c;border-radius:6px;background:#030810;}
#cdu-trend-canvas{border:1px solid #1a3a5c;border-radius:6px;background:#030810;}
.cdu-row{display:flex;gap:12px;align-items:flex-start;}
.cdu-col{display:flex;flex-direction:column;gap:6px;}
.cdu-col-label{font-size:10px;color:#6ab;letter-spacing:1px;text-align:center;}
.lens-temps{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;}
.lens-temp-cell{background:rgba(10,18,32,.8);border:1px solid #1a3a5c;
  border-radius:5px;padding:6px 8px;text-align:center;}
.lens-temp-cell .name{font-size:9px;color:#6ab;}
.lens-temp-cell .temp{font-size:13px;font-weight:bold;font-family:Consolas,monospace;}
.fault-btns{display:flex;gap:6px;flex-wrap:wrap;}
.fault-btn{padding:5px 10px;border-radius:4px;font-size:10px;cursor:pointer;
  background:rgba(255,60,60,.1);border:1px solid #ff4444;color:#ff8888;}
.fault-btn:hover{background:rgba(255,60,60,.25);}
.fault-btn.clear{background:rgba(60,255,100,.1);border-color:#44ff88;color:#88ffaa;}
</style>
</head><body>

<!-- 3D 零件標籤疊層 -->
<div id="label-layer"></div>

<!-- Chat Panel -->
<div id="chat-panel">
  <div id="chat-hdr"><div class="alive"></div>AI 學長 — 即時輔導</div>
  <div id="score-bar">
    <span id="score-val">分數：100</span>
    <span id="fault-prog">—</span>
  </div>
  <div id="chat-msgs"><div class="msg ms">⏳ 等待訓練開始…</div></div>
  <button id="hint-btn" onclick="askHint()" disabled>💬 求助學長（-5 分）</button>
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
  <div id="start-screen-panel">
    <div style="font-size:13px;color:#ffee88;letter-spacing:4px;opacity:.7;text-transform:uppercase;">Cleanroom — Yellow Light Zone</div>
    <h1>ASML TWINSCAN NXT:870<br><span style="font-size:14px;color:#ffcc44;letter-spacing:2px;">ArF Immersion DUV Lithography System</span></h1>
    <h2>操作員故障排除訓練 · Virtual Fab</h2>
    <div class="hint">
      <b>點擊「進入機器」</b> 後將進入機器內部第一人稱視角<br>
      <b>WASD</b> 移動 &nbsp;|&nbsp; <b>滑鼠</b> 旋轉視角 &nbsp;|&nbsp; <b>E</b> 靠近部件檢查<br>
      <b>C</b> 與 AI 學長對話 &nbsp;|&nbsp; <b>ESC</b> 暫停
    </div>
    <div id="diff-row">
      <label style="color:#aa8833;font-size:12px;">訓練難度：</label>
      <select id="difficulty">
        <option value="easy">簡單</option>
        <option value="medium" selected>中等</option>
        <option value="hard">困難</option>
      </select>
    </div>
    <button id="start-btn">▶ 進入機器內部</button>
  </div>
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
<!-- Maintenance Panel -->
<div id="maint-overlay">
  <div id="maint-modal">
    <div id="maint-hdr">
      <div>
        <div id="maint-hdr-title">🔧 維修程序</div>
        <div id="maint-hdr-sub"></div>
      </div>
      <button id="maint-close-btn" onclick="closeMaintenance()">✕ 離開</button>
    </div>
    <div id="maint-body">
      <div class="maint-progress">
        <div class="maint-progress-bar" id="maint-prog-bar" style="width:0%"></div>
      </div>
      <div class="maint-status">
        <span id="maint-prog-text">進行中...</span>
        <span id="maint-fault-label"></span>
      </div>
      <div id="maint-steps" style="padding:16px 12px;color:#8ab;font-size:12px;line-height:1.8;">
        請靠近相關零件並按 <b style="color:#ffa500;">[E]</b> 互動，<br>
        自行判斷處理順序。<br><br>
        <span style="color:#5a7a5a;font-size:11px;">▸ 橘色發光的零件是故障相關區域<br>
        ▸ 可按 <b>[C]</b> 與 AI 學長對話<br>
        ▸「求助學長」可獲得提示（-5分）</span>
      </div>
      <div class="maint-complete" id="maint-complete">
        ✅ 故障排除完成！系統已恢復正常。
      </div>
    </div>
  </div>
</div>

<div id="hmi-overlay">
  <div id="hmi-modal">
    <div id="hmi-modal-hdr">
      <span>⚙ ASML TWINSCAN NXT:870 — HMI 控制面板</span>
      <button id="hmi-close" onclick="closeHMI()">✕ 關閉 [ESC]</button>
    </div>
    <!-- Tabs -->
    <div id="hmi-tabs">
      <div class="hmi-tab active" onclick="switchHmiTab('sensor')">感測器 &amp; 警報</div>
      <div class="hmi-tab" onclick="switchHmiTab('cdu')">CDU / Overlay 模擬</div>
    </div>
    <!-- Tab: 感測器 (original) -->
    <div id="hmi-sensor-panel">
      <div id="hmi-content">
        <div style="color:#5a8a9a;text-align:center;padding:24px;">載入感測器資料…</div>
      </div>
    </div>
    <!-- Tab: CDU / Overlay 模擬 -->
    <div id="cdu-panel">
      <!-- 曝光參數控制 -->
      <div class="hmi-section">
        <div class="hmi-section-title">曝光參數控制</div>
        <div class="cdu-controls">
          <div class="cdu-ctrl">
            <label>DOSE (mJ/cm²)</label>
            <input type="range" id="ctrl-dose" min="20" max="50" step="0.5" value="30"
              oninput="document.getElementById('dose-val').textContent=this.value">
            <div class="val-display"><span id="dose-val">30</span> mJ/cm²</div>
          </div>
          <div class="cdu-ctrl">
            <label>FOCUS OFFSET (nm)</label>
            <input type="range" id="ctrl-focus" min="-200" max="200" step="5" value="0"
              oninput="document.getElementById('focus-val').textContent=this.value">
            <div class="val-display"><span id="focus-val">0</span> nm</div>
          </div>
          <div class="cdu-ctrl">
            <label>NA</label>
            <select id="ctrl-na">
              <option value="0.60">0.60 (低)</option>
              <option value="0.75" selected>0.75 (標準)</option>
              <option value="0.85">0.85 (高)</option>
            </select>
          </div>
          <div class="cdu-ctrl">
            <label>SIGMA</label>
            <select id="ctrl-sigma">
              <option value="0.50">0.50 (小)</option>
              <option value="0.75" selected>0.75 (標準)</option>
              <option value="0.90">0.90 (大)</option>
            </select>
          </div>
          <button id="cdu-expose-btn" onclick="runExposure()">▶ 曝光模擬</button>
        </div>
      </div>
      <!-- 故障注入 -->
      <div class="hmi-section">
        <div class="hmi-section-title">故障注入 (SECOM Scenario)</div>
        <div class="fault-btns">
          <button class="fault-btn" onclick="injectFault('dose_drift')">劑量漂移</button>
          <button class="fault-btn" onclick="injectFault('focus_drift')">焦距漂移</button>
          <button class="fault-btn" onclick="injectFault('lens_hotspot')">鏡片過熱</button>
          <button class="fault-btn" onclick="injectFault('contamination')">光罩污染</button>
          <button class="fault-btn" onclick="injectFault('stage_error')">載台誤差</button>
          <button class="fault-btn clear" onclick="clearFault()">✓ 恢復正常</button>
        </div>
        <div id="fault-status" style="margin-top:6px;font-size:11px;color:#88ffaa;"></div>
      </div>
      <!-- 結果指標 -->
      <div class="cdu-metrics" id="cdu-metrics">
        <div class="cdu-metric"><div class="label">CD MEAN</div>
          <div class="value" id="m-cd">—</div><div class="unit">nm</div></div>
        <div class="cdu-metric"><div class="label">CD 3σ</div>
          <div class="value" id="m-cd3s">—</div><div class="unit">nm</div></div>
        <div class="cdu-metric"><div class="label">OVL X 3σ</div>
          <div class="value" id="m-ovx">—</div><div class="unit">nm</div></div>
        <div class="cdu-metric"><div class="label">OVL Y 3σ</div>
          <div class="value" id="m-ovy">—</div><div class="unit">nm</div></div>
        <div class="cdu-metric"><div class="label">FOCUS DRIFT</div>
          <div class="value" id="m-fdrift">—</div><div class="unit">nm</div></div>
        <div class="cdu-metric"><div class="label">MAG ERROR</div>
          <div class="value" id="m-mag">—</div><div class="unit">ppm</div></div>
        <div class="cdu-metric"><div class="label">HEALTH</div>
          <div class="value" id="m-health">—</div><div class="unit">%</div></div>
        <div class="cdu-metric"><div class="label">WAFER</div>
          <div class="value" id="m-wno">—</div><div class="unit">#</div></div>
      </div>
      <!-- CDU Map + Trend Chart -->
      <div class="cdu-row">
        <div class="cdu-col">
          <div class="cdu-col-label">CDU MAP (13×13 grid, nm)</div>
          <canvas id="cdu-map-canvas" width="260" height="260"></canvas>
        </div>
        <div class="cdu-col" style="flex:1;">
          <div class="cdu-col-label">CD / Overlay 趨勢（最近 30 片）</div>
          <canvas id="cdu-trend-canvas" width="340" height="260"></canvas>
          <!-- 鏡片溫度 -->
          <div class="cdu-col-label" style="margin-top:10px;">鏡片溫升 ΔT (K)</div>
          <div class="lens-temps" id="lens-temps"></div>
        </div>
      </div>
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
var COMPONENT_ACTIONS={
  '投影鏡組':{
    inspect:['查看鏡片溫度','確認鏡片溫升趨勢','查看 CDU 數值'],
    operate:['降低曝光劑量','停止曝光','恢復正常劑量']
  },
  '晶圓載台':{
    inspect:['查看 Overlay 數值','查看載台位置誤差','確認氣浮壓力'],
    operate:['執行載台校正','執行 Cal Routine','恢復量產','驗證 Overlay 改善結果']
  },
  '雷射光源':{
    inspect:['確認偏差量','查看劑量讀值','確認光束穩定性'],
    operate:['執行劑量校正','清潔劑量感測器','確認穩定']
  },
  '液浸冷卻':{
    inspect:['確認流量讀值','查看冷卻水溫度','查看冷卻水流量'],
    operate:['關閉進水閥','目視檢查管路','清潔過濾器','恢復供水','確認流量正常']
  },
  '照明系統':{
    inspect:['確認漂移量','查看焦距偏移','查看照明均勻性'],
    operate:['執行 Focus 校正','等待熱穩定','降低劑量']
  },
  '控制系統':{
    inspect:['查看控制系統狀態','查看系統日誌'],
    operate:['降低曝光劑量','停止曝光','恢復曝光','執行校正']
  },
  '通風排氣':{
    inspect:['確認壓力讀值','查看真空壓力','查看氣流量'],
    operate:['關閉閥門','關閉 V-201','目視檢查管路接頭','更換 O-ring 密封圈','重新抽真空並確認壓力','確認完成']
  },
  '光罩載台':{
    inspect:['確認異常 field','查看光罩狀態','目視檢查光罩表面'],
    operate:['停機並卸載光罩','清潔光罩','更換光罩','裝回光罩並執行對準']
  },
  'HMI 螢幕':{
    inspect:['查看 CDU Map','查看感測器數值','查看 Overlay 數值'],
    operate:['降低曝光劑量','停止曝光','執行校正']
  },
  '晶圓傳送':{
    inspect:['確認晶圓傳送狀態','查看 FOUP 狀態'],
    operate:['重新對準傳送手臂','確認 FOUP 鎖定']
  },
  '晶圓傳送手臂':{
    inspect:['確認晶圓傳送狀態','查看手臂馬達電流'],
    operate:['重新對準傳送手臂','檢查 End Effector']
  },
  'DUV光束':{
    inspect:['查看光源強度和穩定性','確認光束穩定性'],
    operate:['對準光束路徑','檢查光束擋板']
  },
  '反射鏡':{
    inspect:['查看光源強度和穩定性','確認反射率'],
    operate:['清潔反射鏡面']
  },
};
(function(){
  for(var i=0;i<10;i++){MA['Lens_'+i]='檢查投影鏡組溫度';ML['Lens_'+i]='投影鏡組';}
  for(var i=0;i<6;i++){MA['IllumLens_'+i]='查看光源強度和穩定性';ML['IllumLens_'+i]='照明系統';}
})();

// ── Three.js Setup ────────────────────────────────────────────────────────────
var CW=window.innerWidth-300, CH=window.innerHeight;
var scene=new THREE.Scene();
scene.background=new THREE.Color(0x1a1200); // 無塵室黃光（鈉黃光氛圍）
scene.fog=new THREE.FogExp2(0x1a1200,0.016);
var renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
renderer.setSize(CW,CH); renderer.shadowMap.enabled=true;
renderer.shadowMap.type=THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);
renderer.domElement.style.width=CW+'px';renderer.domElement.style.height=CH+'px';
var camera=new THREE.PerspectiveCamera(72,CW/CH,0.05,100);
camera.position.set(0,1.6,4);
// Lights
// 無塵室黃光：鈉黃光（589nm）氛圍打光
scene.add(new THREE.AmbientLight(0xffee88,0.55));          // 黃光環境光
var sun=new THREE.DirectionalLight(0xffe566,1.1);          // 主光源（暖黃）
sun.position.set(6,10,6);sun.castShadow=true;scene.add(sun);
var fill=new THREE.DirectionalLight(0xcc9900,0.45);fill.position.set(-6,3,-6);scene.add(fill); // 補光（橘黃）
var rim=new THREE.DirectionalLight(0xffdd44,0.20);rim.position.set(0,8,0);scene.add(rim);      // 頂光（黃）
// 天花板面光（模擬無塵室均勻照明）
var ceil1=new THREE.PointLight(0xffee66,0.8,8);ceil1.position.set(0,4,0);scene.add(ceil1);
var ceil2=new THREE.PointLight(0xffdd44,0.5,6);ceil2.position.set(2,4,2);scene.add(ceil2);
// ── 無塵室環境 ────────────────────────────────────────────────────────────────
// 地板：淺灰（無塵室抗靜電磁磚）
var floorMesh=new THREE.Mesh(new THREE.PlaneGeometry(40,40),
  new THREE.MeshStandardMaterial({color:0xc8c4a0,roughness:.75,metalness:.05}));
floorMesh.rotation.x=-Math.PI/2;floorMesh.receiveShadow=true;scene.add(floorMesh);

// 地板磚縫格線（30cm x 30cm 磁磚）
var _tileGrid=new THREE.GridHelper(40,133,0x999980,0x999980);
_tileGrid.position.y=0.001;_tileGrid.material.opacity=0.25;_tileGrid.material.transparent=true;
scene.add(_tileGrid);

// 天花板
var _ceilMesh=new THREE.Mesh(new THREE.PlaneGeometry(40,40),
  new THREE.MeshStandardMaterial({color:0xf0ead0,roughness:.9,metalness:.0,side:THREE.BackSide}));
_ceilMesh.rotation.x=-Math.PI/2;_ceilMesh.position.y=5.0;scene.add(_ceilMesh);

// 天花板燈管（黃光日光燈條 × 4）
var _lampMat=new THREE.MeshStandardMaterial({color:0xffee88,emissive:0xffcc44,emissiveIntensity:1.8,transparent:true,opacity:0.9});
[[-3,0],[3,0],[-3,3],[3,3]].forEach(function(pos){
  var _lamp=new THREE.Mesh(new THREE.BoxGeometry(0.15,0.04,2.0),_lampMat);
  _lamp.position.set(pos[0],4.95,pos[1]);scene.add(_lamp);
  var _lpt=new THREE.PointLight(0xffee66,0.7,6);_lpt.position.set(pos[0],4.8,pos[1]);scene.add(_lpt);
});

// 後牆
var _wallMat=new THREE.MeshStandardMaterial({color:0xe8e0c0,roughness:.85,metalness:.0});
var _wallBack=new THREE.Mesh(new THREE.PlaneGeometry(40,7),_wallMat);
_wallBack.position.set(0,3.5,-8);scene.add(_wallBack);
// 左牆
var _wallL=new THREE.Mesh(new THREE.PlaneGeometry(20,7),_wallMat.clone());
_wallL.rotation.y=Math.PI/2;_wallL.position.set(-8,3.5,0);scene.add(_wallL);
// 右牆
var _wallR=new THREE.Mesh(new THREE.PlaneGeometry(20,7),_wallMat.clone());
_wallR.rotation.y=-Math.PI/2;_wallR.position.set(8,3.5,0);scene.add(_wallR);

// ── 機器外殼（ASML NXT 外觀，覆蓋內部元件，開始前可見）─────────────────────
var exteriorShell=new THREE.Group();
// 外殼定位（包住現有玻璃箱）
var _sx=0.85,_sy=0,_sz=-0.05; // 外殼左下角 XZ 基準
var _sW=2.95,_sH=2.72,_sD=1.85; // 寬高深
var _sCX=_sx,_sCZ=_sz; // X/Z center

// 上半部：白色機體（掃描頭、光學系統）
var _uH=_sH*0.55; var _uMat=new THREE.MeshStandardMaterial({color:0xf0eeec,metalness:.12,roughness:.35});
var _uBox=new THREE.Mesh(new THREE.BoxGeometry(_sW,_uH,_sD),_uMat);
_uBox.position.set(_sCX,_sH*0.45+_uH/2,_sCZ); exteriorShell.add(_uBox);

// 下半部：深海軍藍底座框架
var _lH=_sH*0.45; var _lMat=new THREE.MeshStandardMaterial({color:0x2c3a4a,metalness:.35,roughness:.30});
var _lBox=new THREE.Mesh(new THREE.BoxGeometry(_sW,_lH,_sD),_lMat);
_lBox.position.set(_sCX,_lH/2,_sCZ); exteriorShell.add(_lBox);

// 頂部深色壓條
var _topBar=new THREE.Mesh(new THREE.BoxGeometry(_sW+0.02,0.06,_sD+0.02),_lMat.clone());
_topBar.position.set(_sCX,_sH-0.03,_sCZ); exteriorShell.add(_topBar);

// 正面垂直面板線（右側 4 條）
var _pMat=new THREE.MeshStandardMaterial({color:0xd8d4d0,metalness:.1,roughness:.45});
var _frontZ=_sCZ+_sD/2+0.005;
for(var _pi=0;_pi<4;_pi++){
  var _pX=_sCX+0.35+_pi*0.42;
  var _pLine=new THREE.Mesh(new THREE.BoxGeometry(0.025,_sH*0.54,0.012),_pMat);
  _pLine.position.set(_pX,_sH*0.45+_sH*0.54/2,_frontZ); exteriorShell.add(_pLine);
}

// 正面：左側控制區（稍微突出的面板）
var _ctrlMat=new THREE.MeshStandardMaterial({color:0xe8e4e0,metalness:.1,roughness:.4});
var _ctrlPanel=new THREE.Mesh(new THREE.BoxGeometry(0.7,_sH*0.54,0.015),_ctrlMat);
_ctrlPanel.position.set(_sCX-0.9,_sH*0.45+_sH*0.54/2,_frontZ); exteriorShell.add(_ctrlPanel);

// 控制面板：HMI 螢幕（深色框，可互動）
var _hmiFace=new THREE.Mesh(new THREE.BoxGeometry(0.28,0.22,0.01),
  new THREE.MeshBasicMaterial({color:0x030810}));
_hmiFace.name='ShellHMI_Screen';
_hmiFace.position.set(_sCX-0.98,_sH*0.45+_sH*0.54*0.45,_frontZ+0.02); exteriorShell.add(_hmiFace);
var shellHMIFace=_hmiFace; // 保存參照，供 createHMIScreen 貼 canvas texture

// LED 燈塔（紅/黃/綠）
var _ledColors=[0x22cc22,0xffaa00,0xee2222];
_ledColors.forEach(function(c,i){
  var _led=new THREE.Mesh(new THREE.CylinderGeometry(0.025,0.025,0.05,8),
    new THREE.MeshStandardMaterial({color:c,emissive:c,emissiveIntensity:0.8}));
  _led.position.set(_sCX-0.68,_sH*0.45+_sH*0.54*0.7+i*0.065,_frontZ+0.01); exteriorShell.add(_led);
});

// ── ASML LOGO（透明背景，放在機殼上半空曠區）─────────────────────────────
(function(){
  var _lc=document.createElement('canvas'); _lc.width=512; _lc.height=160;
  var _lx=_lc.getContext('2d');
  // 完全透明底
  _lx.clearRect(0,0,512,160);
  // "ASML" 深藍字
  _lx.fillStyle='#002b6e';
  _lx.font='bold 130px Arial Black,Arial,sans-serif';
  _lx.textAlign='center'; _lx.textBaseline='middle';
  _lx.fillText('ASML',256,80);
  var _lTex=new THREE.CanvasTexture(_lc);
  var _logoPlate=new THREE.Mesh(
    new THREE.PlaneGeometry(0.52,0.16),
    new THREE.MeshBasicMaterial({map:_lTex,transparent:true,side:THREE.FrontSide}));
  // 放在 HMI 螢幕上方、燈號左邊
  _logoPlate.position.set(_sCX-1.05,_sH*0.45+_sH*0.54*0.85,_frontZ+0.012);
  exteriorShell.add(_logoPlate);
})();

// 底部腳輪/避震腳墊（4 個黑色圓柱）
var _footMat=new THREE.MeshStandardMaterial({color:0x111111,metalness:.6,roughness:.3});
[[-1.1,-0.7],[1.1,-0.7],[-1.1,0.6],[1.1,0.6]].forEach(function(p){
  var _foot=new THREE.Mesh(new THREE.CylinderGeometry(0.08,0.1,0.12,8),_footMat);
  _foot.position.set(_sCX+p[0]*_sW*0.35,0.06,_sCZ+p[1]*_sD*0.4); exteriorShell.add(_foot);
});

scene.add(exteriorShell);

// 外觀模式攝影機初始位置：正對機殼正面 (-Z 方向)
// 機殼正面 Z = _sCZ + _sD/2 ≈ 0.875，攝影機在前方 3.5m 處
// PointerLockControls 預設看向 -Z，所以機殼正好在正前方
camera.position.set(_sCX, 1.55, _sCZ+_sD/2+3.5);

// ── PointerLockControls ───────────────────────────────────────────────────────
var controls=new THREE.PointerLockControls(camera,document.body);
scene.add(controls.getObject());
var moveF=false,moveB=false,moveL=false,moveR=false;
var velocity=new THREE.Vector3();
var clock=new THREE.Clock();
var gameStarted=false,chatFocus=false,inspecting=false,hmiOpen=false;
var insideMode=false; // false=外殼模式, true=已進入機器內部
var glbModel=null;   // GLB 模型根節點
var shellMeshes=[];  // 外殼 mesh 列表

// ── Raycasting & Model ────────────────────────────────────────────────────────
var allMeshes=[],hoveredObj=null,origMats=new Map();
// 收集外殼 mesh 供 raycast 偵測「點擊進入」（必須在 allMeshes/shellMeshes 初始化後）
if(typeof exteriorShell!=='undefined')
  exteriorShell.traverse(function(o){if(o.isMesh){shellMeshes.push(o);allMeshes.push(o);}});
var hlMat=new THREE.MeshStandardMaterial({color:0xffa500,emissive:0x220800,metalness:.3,roughness:.5});
var raycaster=new THREE.Raycaster();raycaster.far=9;
var mixer=null; // GLB AnimationMixer
function getInfo(obj){var o=obj;while(o){if(MA[o.name])return{label:ML[o.name]||o.name,action:MA[o.name]};o=o.parent;}return null;}

// 判斷 mesh 是否屬於外殼
function isShellMesh(obj){return shellMeshes.indexOf(obj)!==-1;}

// 進入機器內部
function enterInterior(){
  insideMode=true;
  if(typeof exteriorShell!=='undefined') exteriorShell.visible=false;
  shellMeshes.forEach(function(m){m.visible=false;});
  if(glbModel) glbModel.visible=true;
  _labelSprites.forEach(function(s){s.visible=true;});
  _outlineMeshes.forEach(function(o){o.visible=true;});
  camera.position.set(0,1.6,4);
  addMsg('sys','已進入機器內部。靠近部件按 <b>E</b> 檢查，靠近 HMI 螢幕按 <b>E</b> 查看感測器數值。');
}

// ── Maintenance SOP 資料 ────────────────────────────────────────────────────────
// 每個故障對應：觸發節點名稱、SOP 步驟、故障描述
var MAINT_SOP = {
  // 真空系統異常（已移除：Duct mesh 隱藏，無法互動）
  vacuum_abnormal_disabled: {
    title: '真空系統異常',
    subtitle: 'Vacuum System Fault — 接頭洩漏 / 閥門故障',
    triggerMeshes: ['Duct_Top','Duct_Vent1','Duct_Vent2'],
    fault_api: null,  // 由 AI 對話觸發，不從 SECOM 注入
    steps: [
      {title:'確認系統狀態', desc:'查看 HMI 真空壓力讀值，確認異常壓力範圍。\n正常值：< 1×10⁻³ mbar', action:'確認壓力讀值'},
      {title:'關閉真空閥門 V-201', desc:'找到排氣管路旁的 V-201 閥門，順時針轉緊關閉，\n防止洩漏範圍擴大。', action:'關閉閥門'},
      {title:'檢查接頭密封性', desc:'目視檢查管路接頭是否有鬆脫或破損，\n用手輕壓接頭確認固定狀態。', action:'確認接頭緊固'},
      {title:'更換 O-ring 密封圈', desc:'若接頭密封圈老化，需更換新的 O-ring（型號：AS-568A-116）\n並確認安裝方向正確。', action:'完成更換'},
      {title:'重新抽真空', desc:'打開泵浦，緩慢開啟 V-201，\n觀察壓力計是否在 5 分鐘內恢復至正常範圍。', action:'開啟抽真空'},
      {title:'確認壓力恢復', desc:'壓力讀值穩定在 < 1×10⁻³ mbar 且無持續下降趨勢，\n系統恢復正常。', action:'確認完成'},
    ]
  },
  // 鏡片過熱（SECOM lens_hotspot）
  lens_hotspot: {
    title: '投影鏡片過熱',
    subtitle: 'Projection Lens Thermal Anomaly — 需降溫處理',
    triggerMeshes: ['POB_Barrel','POB_Top_Cap','POB_Bottom'],
    fault_api: 'lens_hotspot',
    steps: [
      {title:'確認鏡片溫度', desc:'在 HMI CDU 面板查看各鏡片元件溫升。\n正常待機溫升應 < 0.5 K，目前超標。', action:'查看溫度數值'},
      {title:'降低曝光劑量', desc:'立即在 HMI 將 Dose 降低 20%（例如 30→24 mJ/cm²），\n減少熱輸入給鏡片。', action:'已調降 Dose'},
      {title:'等待自然冷卻', desc:'停止曝光，等待鏡片溫度透過自然對流冷卻。\n依熱時間常數（τ₁≈90s, τ₂≈15min），\n需等待約 5 分鐘。', action:'確認溫度下降中'},
      {title:'檢查冷卻水流量', desc:'確認鏡筒冷卻水迴路流量是否正常，\n鏡筒周圍溫度感測器讀值應趨近室溫。', action:'確認冷卻正常'},
      {title:'恢復曝光並監控', desc:'緩慢恢復正常劑量，持續監控 CDU 趨勢圖，\n確認 CD 3σ 回到規格內（< 4 nm）。', action:'確認 CDU 恢復正常'},
    ]
  },
  // 光罩污染（SECOM contamination）
  contamination: {
    title: '光罩污染',
    subtitle: 'Reticle Contamination — 需清潔或更換',
    triggerMeshes: ['Reticle_Stage_Mesh','Reticle_Mesh'],
    fault_api: 'contamination',
    steps: [
      {title:'確認污染位置', desc:'在 HMI 查看 CDU Map，污染通常表現為\n特定 field 位置的系統性 CD 偏移。', action:'確認異常 field'},
      {title:'停機並卸載光罩', desc:'通知工程師停止生產，\n按 SOP 將光罩從 reticle stage 取出並放入專用載具。', action:'光罩已卸載'},
      {title:'目視檢查光罩', desc:'在潔淨燈箱下目視檢查光罩表面，\n尋找顆粒、水漬、或圖案損傷。', action:'確認污染位置'},
      {title:'光罩清潔（或更換）', desc:'輕微污染：使用 DI water + 氮氣吹淨。\n嚴重污染：送回光罩廠重新清潔或更換。', action:'清潔/更換完成'},
      {title:'裝回並執行對準', desc:'裝回光罩，執行 reticle alignment，\n確認套刻誤差在規格內後恢復生產。', action:'對準完成'},
    ]
  },
  // 載台位置誤差（SECOM stage_error）
  stage_error: {
    title: '晶圓載台位置誤差',
    subtitle: 'Wafer Stage Position Error — Overlay 超規',
    triggerMeshes: ['Wafer_Chuck','Stage_Base','Wafer'],
    fault_api: 'stage_error',
    steps: [
      {title:'確認 Overlay 數值', desc:'在 HMI CDU 面板查看 Overlay X/Y 3σ 值，\n超過 4 nm 時需介入。', action:'確認 Overlay 數值'},
      {title:'執行載台校正', desc:'啟動 stage calibration routine，\n系統自動量測 interferometer 讀值並補償。', action:'執行 Cal Routine'},
      {title:'檢查氣浮軸承', desc:'確認載台氣浮壓力正常（0.4–0.6 MPa），\n氣壓不足會導致載台摩擦增加。', action:'確認氣浮壓力'},
      {title:'確認 Overlay 改善', desc:'重新曝光測試片，量測 Overlay，\n確認 X/Y 3σ < 2 nm 後恢復量產。', action:'Overlay 合格'},
    ]
  },
  // 劑量漂移（SECOM dose_drift）
  dose_drift: {
    title: '曝光劑量漂移',
    subtitle: 'Dose Drift — 雷射能量衰減 / 感測器偏移',
    triggerMeshes: ['Laser_Box','Laser_Out','Laser_Vent'],
    fault_api: 'dose_drift',
    steps: [
      {title:'確認劑量讀值', desc:'查看 HMI 的 Dose sensor 讀值與設定值的差異，\n> 1% 偏差即需介入。', action:'確認偏差量'},
      {title:'執行劑量校正', desc:'執行 dose calibration，系統自動調整\n雷射電壓補償能量衰減。', action:'執行校正'},
      {title:'清潔劑量感測器', desc:'雷射出口附近的 dose sensor 玻璃窗\n可能有污染，用 IPA 輕拭後重新校正。', action:'清潔完成'},
      {title:'確認穩定性', desc:'連續量測 10 次劑量值，\n確認 CV（變異係數）< 0.3%。', action:'確認穩定'},
    ]
  },
  // 焦距漂移（SECOM focus_drift）
  focus_drift: {
    title: '焦距異常漂移',
    subtitle: 'Focus Drift — 鏡片熱效應 / 感測器偏移',
    triggerMeshes: ['Illum_Barrel','Label_Illum'],
    fault_api: 'focus_drift',
    steps: [
      {title:'確認焦距漂移量', desc:'查看 HMI CDU 面板的 Focus Drift 值，\n> 30 nm 時會顯著影響 CD。', action:'確認漂移量'},
      {title:'執行 Focus 校正', desc:'使用 ALS（Aerial Latent Scrutiny）測試片\n量測實際最佳焦距，更新補償參數。', action:'執行校正'},
      {title:'查看鏡片溫升', desc:'在 CDU 面板確認各鏡片元件溫升，\n若 PL1–PL3 溫升 > 1.5 K 表示熱效應顯著。', action:'確認溫升'},
      {title:'等待熱穩定或調降劑量', desc:'等待鏡片熱平衡（約 15 min），\n或降低 Dose 減緩熱漂移。', action:'確認焦距穩定'},
    ]
  }
};

// ── Maintenance 狀態 ──────────────────────────────────────────────────────────
var maintOpen=false;
var _maintFaultType=null;
var _maintStepIdx=0;     // 目前進行到第幾步（0-based）
var _maintDone=false;

// 故障狀態快取（由 AI tick 或 SECOM 注入設定）
var _activeFaults={};    // { faultType: true }

function setActiveFault(faultType){
  _activeFaults[faultType]=true;
  // 讓對應 mesh 持續發光提示（橙色 pulse）
  _maintFaultMeshNames = (MAINT_SOP[faultType]||{}).triggerMeshes || [];
}
function clearActiveFault(faultType){
  if(faultType) delete _activeFaults[faultType];
  else _activeFaults={};
  _maintFaultMeshNames=[];
}
var _maintFaultMeshNames=[];

function openMaintenance(faultType){
  var sop=MAINT_SOP[faultType]; if(!sop) return;
  maintOpen=true; _maintFaultType=faultType; _maintStepIdx=0; _maintDone=false;
  controls.unlock();
  document.getElementById('maint-overlay').style.display='flex';
  document.getElementById('maint-hdr-title').textContent='⚠ 故障警報：'+sop.title;
  document.getElementById('maint-hdr-sub').textContent=sop.subtitle;
  document.getElementById('maint-fault-label').textContent='故障類型：'+faultType;
  document.getElementById('maint-complete').style.display='none';
  document.getElementById('maint-prog-bar').style.width='0%';
  document.getElementById('maint-prog-text').textContent='進行中...';
  document.getElementById('maint-steps').innerHTML=
    '<div style="padding:16px 12px;color:#8ab;font-size:12px;line-height:1.8;">'
    +'請靠近相關零件並按 <b style="color:#ffa500;">[E]</b> 互動，<br>'
    +'自行判斷處理順序。<br><br>'
    +'<span style="color:#5a7a5a;font-size:11px;">▸ 橘色發光的零件是故障相關區域<br>'
    +'▸ 可按 <b>[C]</b> 與 AI 學長對話<br>'
    +'▸「求助學長」可獲得提示（-5分）</span></div>';
  document.getElementById('hint-btn').disabled=false;
  addMsg('sys','⚠ 偵測到故障：<b>'+sop.title+'</b>。請自行判斷處理步驟。');
}
window.openMaintenance=openMaintenance;

function updateFaultProgress(current,total){
  var pct=total>0?Math.round(current/total*100):0;
  document.getElementById('maint-prog-bar').style.width=pct+'%';
  document.getElementById('maint-prog-text').textContent='步驟 '+current+' / '+total;
  document.getElementById('fault-prog').textContent=current+'/'+total+' 完成';
}

function closeMaintenance(){
  maintOpen=false;
  document.getElementById('maint-overlay').style.display='none';
  if(gameStarted&&insideMode) controls.lock();
}
window.closeMaintenance=closeMaintenance;

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
  // 把同一個 canvas texture 貼到外殼螢幕
  if(typeof shellHMIFace!=='undefined'&&shellHMIFace){
    shellHMIFace.material=new THREE.MeshBasicMaterial({map:hmiTex,side:THREE.FrontSide});
  }
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

// Load GLB
console.log('[LOAD] GLB loading started');
var loader=new THREE.GLTFLoader();
var _t0=Date.now();
var _hasRealProgress=false;
function _setProgress(percent){
  console.log('[_setProgress] Setting to '+percent+'%');
  var el=document.getElementById('load-pct');
  var bar=document.getElementById('load-bar');
  console.log('[_setProgress] Element found: pct='+!!el+', bar='+!!bar);
  if(el) {
    el.textContent=percent+'%';
    console.log('[_setProgress] Updated pct text to '+percent+'%');
  }
  if(bar) {
    bar.style.width=percent+'%';
    console.log('[_setProgress] Updated bar width to '+percent+'%');
  }
}
console.log('[LOAD] Starting setInterval for progress');
var _progressInterval=setInterval(function(){
  if(!_hasRealProgress){
    var elapsed=Date.now()-_t0;
    var p=Math.min(95, Math.floor(elapsed/80));
    _setProgress(p);
  }
}, 100);
_setProgress(0);
console.log('[LOAD] Initial 0% set, loading glb...');
loader.load('./asml_duv.glb',
  function(gltf){
    try{
      document.getElementById('load-pct').textContent='100%';
      if(document.getElementById('load-bar'))document.getElementById('load-bar').style.width='100%';
      document.getElementById('loading-screen').style.display='none';
      var ss=document.getElementById('start-screen');
      ss.style.display='flex';ss.style.width=CW+'px';ss.style.height=CH+'px';
      var model=gltf.scene;
      glbModel=model;
      var _allNodeNames=[];
      model.traverse(function(o){
        if(o.name)_allNodeNames.push(o.name);
        if(o.isMesh){o.castShadow=true;o.receiveShadow=true;allMeshes.push(o);}
      });
      console.log('[DBG] ALL GLB nodes:',_allNodeNames.join(', '));
      scene.add(model);
      model.visible=false;
      var box=new THREE.Box3().setFromObject(model);
      var c=box.getCenter(new THREE.Vector3()),s=box.getSize(new THREE.Vector3());
      model.position.set(-c.x,-box.min.y,-c.z);

      var worldBox=new THREE.Box3().setFromObject(model);
      createHMIScreen(worldBox);
      var r=Math.max(s.x,s.z)*0.85;
      camera.position.set(r,1.6,r);
      camera.lookAt(new THREE.Vector3(0,s.y*0.4,0));
      if(gltf.animations&&gltf.animations.length>0){
        mixer=new THREE.AnimationMixer(model);
        gltf.animations.forEach(function(clip){
          var action=mixer.clipAction(clip);
          action.setLoop(THREE.LoopRepeat,Infinity);
          action.play();
        });
        console.log('[OK] Playing',gltf.animations.length,'animations:',gltf.animations.map(function(a){return a.name;}).join(', '));
      }
      createProcObjects(model);
      clearInterval(_progressInterval);
    }catch(e){
      clearInterval(_progressInterval);
      var el=document.getElementById('loading-screen');
      if(el)el.innerHTML='<div style="color:#f44;text-align:center;padding:20px;">❌ 模型處理錯誤<br><small style="color:#888">'+e.message+'</small></div>';
      console.error('onLoad error:',e);
    }
  },
  function(xhr){
    if(xhr.total>0){
      _hasRealProgress=true;
      var p=Math.round(xhr.loaded/xhr.total*100);
      _setProgress(p);
    }
  },
  function(err){
    document.getElementById('load-pct').textContent='ERROR';
    var el=document.getElementById('loading-screen');
    if(el)el.innerHTML='<div style="color:#f44;text-align:center;padding:20px;">GLB load failed: '+err+'<br><br><button onclick="location.reload()" style="background:#0d2a4a;border:1px solid #4af;color:#4af;padding:8px 20px;border-radius:6px;cursor:pointer;">Reload</button></div>';
  }
);

// DOM refs
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
// AI 訊息中的故障關鍵字 → 自動 setActiveFault
var _FAULT_KEYWORDS={
  lens_hotspot:['鏡片過熱','lens hot','鏡片溫度','熱膨脹'],
  contamination:['光罩污染','reticle contamination','污染','contamination'],
  stage_error:['載台誤差','stage error','overlay 超規','overlay超規'],
  dose_drift:['劑量漂移','dose drift','劑量異常'],
  focus_drift:['焦距漂移','focus drift','焦距異常'],
};
function _detectFaultInText(text){
  var lower=text.toLowerCase();
  Object.keys(_FAULT_KEYWORDS).forEach(function(ft){
    _FAULT_KEYWORDS[ft].forEach(function(kw){
      if(lower.indexOf(kw.toLowerCase())!==-1) setActiveFault(ft);
    });
  });
}
function addMsg(role,text){
  var w=$msgs.querySelector('.ms');if(w&&w.textContent.includes('等待'))w.remove();
  var d=document.createElement('div');
  d.className='msg '+(role==='user'?'mu':role==='sys'?'ms':'ma');
  d.innerHTML=role==='user'?'你: '+text:role==='sys'?text:'學長: '+text;
  $msgs.appendChild(d);$msgs.scrollTop=$msgs.scrollHeight;
  // AI 或系統訊息中偵測故障關鍵字
  if(role==='ai'||role==='sys') _detectFaultInText(text);
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
  var acts=COMPONENT_ACTIONS[label]||{inspect:[action],operate:[]};
  if(acts.inspect&&acts.inspect.length>0){
    var h1=document.createElement('div');h1.className='action-sec action-sec-inspect';
    h1.textContent='🔍 檢查';$ia.appendChild(h1);
    acts.inspect.forEach(function(a){
      var btn=document.createElement('button');btn.className='qbtn';btn.textContent=a;
      btn.onclick=function(){sendAction(label,a);closeInspect();};$ia.appendChild(btn);
    });
  }
  if(acts.operate&&acts.operate.length>0){
    var h2=document.createElement('div');h2.className='action-sec action-sec-operate';
    h2.textContent='⚙ 操作';$ia.appendChild(h2);
    acts.operate.forEach(function(a){
      var btn=document.createElement('button');btn.className='qbtn qbtn-operate';btn.textContent=a;
      btn.onclick=function(){sendAction(label,a);closeInspect();};$ia.appendChild(btn);
    });
  }
}
function closeInspect(){
  inspecting=false;$ip.style.display='none';
  if(gameStarted&&!hmiOpen)controls.lock();
}
function sendAction(component,action){
  if(!gameStarted)return;
  addMsg('user','['+component+'] '+action);
  var faultType=Object.keys(_activeFaults)[0]||null;
  fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({component:component,action:action,fault_type:faultType})
  }).then(function(r){return r.json();}).then(function(d){
    if(d.feedback)addMsg('ai',d.feedback);
    if(d.score!==undefined)updateScore(d.score);
    if(d.all_done){
      clearActiveFault(faultType);
      if(maintOpen)closeMaintenance();
      document.getElementById('hint-btn').disabled=true;
      document.getElementById('fault-prog').textContent='—';
    }else if(d.step_done){
      updateFaultProgress(d.current_step,d.total_steps);
    }
    if(d.no_fault)sendChat('['+component+'] '+action);
  }).catch(function(){addMsg('sys','⚠ 連線錯誤');});
}
function askHint(){
  if(!gameStarted)return;
  var faultType=Object.keys(_activeFaults)[0]||null;
  fetch('/api/hint',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({fault_type:faultType})
  }).then(function(r){return r.json();}).then(function(d){
    if(d.hint)addMsg('ai','💡 '+d.hint);
    if(d.score!==undefined)updateScore(d.score);
    if(d.current_step!==undefined&&d.total_steps)
      updateFaultProgress(d.current_step,d.total_steps);
  }).catch(function(){addMsg('sys','⚠ 連線錯誤');});
}
function updateScore(score){
  var el=document.getElementById('score-val');
  el.textContent='分數：'+score;
  el.style.color=score>=80?'#4fc':score>=60?'#ffa500':'#f44';
}

// ── HMI Overlay ───────────────────────────────────────────────────────────────
// ── HMI Tab 切換 ──────────────────────────────────────────────────────────
var _hmiCurrentTab='sensor';
function switchHmiTab(tab){
  _hmiCurrentTab=tab;
  document.querySelectorAll('.hmi-tab').forEach(function(el,i){
    el.classList.toggle('active', (i===0&&tab==='sensor')||(i===1&&tab==='cdu'));
  });
  document.getElementById('hmi-sensor-panel').style.display=(tab==='sensor'?'block':'none');
  document.getElementById('cdu-panel').style.display=(tab==='cdu'?'flex':'none');
  if(tab==='cdu') loadWaferHistory();
}
window.switchHmiTab=switchHmiTab;

function showHMIOverlay(){
  hmiOpen=true;controls.unlock();
  $hmiOverlay.style.display='flex';
  $hmiOverlay.style.width=CW+'px';$hmiOverlay.style.height='100vh';
  // 顯示目前 tab
  document.getElementById('hmi-sensor-panel').style.display=(_hmiCurrentTab==='sensor'?'block':'none');
  document.getElementById('cdu-panel').style.display=(_hmiCurrentTab==='cdu'?'flex':'none');
  if(_hmiCurrentTab==='sensor'){
    $hmiContent.innerHTML='<div style="color:#5a8a9a;text-align:center;padding:24px;">載入感測器資料…</div>';
    fetch('/api/hmi').then(function(r){return r.json();}).then(function(d){renderHMI(d);})
    .catch(function(){$hmiContent.innerHTML='<div style="color:#f44;padding:20px;">無法取得 HMI 資料</div>';});
  } else {
    loadWaferHistory();
  }
}
function closeHMI(){
  hmiOpen=false;$hmiOverlay.style.display='none';
  if(gameStarted)controls.lock();
}
window.closeHMI=closeHMI;

// ── CDU / Overlay 模擬 ─────────────────────────────────────────────────────
var _cduHistory=[];

function runExposure(){
  var btn=document.getElementById('cdu-expose-btn');
  btn.disabled=true; btn.textContent='⏳ 計算中…';
  var dose=parseFloat(document.getElementById('ctrl-dose').value);
  var focus=parseFloat(document.getElementById('ctrl-focus').value);
  var na=parseFloat(document.getElementById('ctrl-na').value);
  var sigma=parseFloat(document.getElementById('ctrl-sigma').value);
  fetch('/api/exposure',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({dose:dose,focus:focus,na:na,sigma:sigma})})
  .then(function(r){return r.json();})
  .then(function(d){
    btn.disabled=false; btn.textContent='▶ 曝光模擬';
    if(d.ok) updateCduDisplay(d.result);
  }).catch(function(){btn.disabled=false;btn.textContent='▶ 曝光模擬';});
}
window.runExposure=runExposure;

function injectFault(type){
  fetch('/api/fault',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({type:type})})
  .then(function(r){return r.json();})
  .then(function(d){
    var el=document.getElementById('fault-status');
    if(d.fault) el.textContent='⚠ 故障已注入：'+d.fault.desc+' (健康度 '+(d.health*100).toFixed(0)+'%)';
    el.style.color='#ffaa44';
  });
}
window.injectFault=injectFault;

function clearFault(){
  fetch('/api/fault',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({type:null})})
  .then(function(r){return r.json();})
  .then(function(){
    document.getElementById('fault-status').textContent='✓ 製程已恢復正常';
    document.getElementById('fault-status').style.color='#88ffaa';
  });
}
window.clearFault=clearFault;

function loadWaferHistory(){
  fetch('/api/wafer_map').then(function(r){return r.json();}).then(function(d){
    if(d.ok&&d.history&&d.history.length>0){
      _cduHistory=d.history;
      var last=d.history[d.history.length-1];
      updateCduMetrics(last);
      drawTrendChart(d.history);
      updateLensTemps(d.lens_state||{});
    }
  });
}

function updateCduDisplay(r){
  _cduHistory.push(r);
  updateCduMetrics(r);
  if(r.cdu_map) drawCduMap(r.cdu_map, r.cd_target);
  drawTrendChart(_cduHistory.slice(-30));
  updateLensTemps(r.lens_temps||{});
}

function updateCduMetrics(r){
  function setMetric(id,val,warnThresh,alarmThresh){
    var el=document.getElementById(id); if(!el)return;
    el.textContent=val;
    var card=el.closest('.cdu-metric');
    card.classList.remove('warn','alarm');
    var v=parseFloat(val);
    if(!isNaN(alarmThresh)&&Math.abs(v)>=alarmThresh) card.classList.add('alarm');
    else if(!isNaN(warnThresh)&&Math.abs(v)>=warnThresh) card.classList.add('warn');
  }
  setMetric('m-cd', r.cd_mean?r.cd_mean.toFixed(1):'—', 135, 140);
  setMetric('m-cd3s', r.cd_3sigma?r.cd_3sigma.toFixed(2):'—', 4.0, 6.0);
  setMetric('m-ovx', r.overlay_x_3s?r.overlay_x_3s.toFixed(2):'—', 2.0, 4.0);
  setMetric('m-ovy', r.overlay_y_3s?r.overlay_y_3s.toFixed(2):'—', 2.0, 4.0);
  setMetric('m-fdrift', r.focus_drift?r.focus_drift.toFixed(1):'—', 20, 50);
  setMetric('m-mag', r.mag_error_ppm?r.mag_error_ppm.toFixed(3):'—', 0.05, 0.1);
  var h=r.secom&&r.secom.health!=null?r.secom.health:1;
  var hEl=document.getElementById('m-health');
  if(hEl){hEl.textContent=(h*100).toFixed(0);
    var hCard=hEl.closest('.cdu-metric');hCard.classList.remove('warn','alarm');
    if(h<0.5)hCard.classList.add('alarm'); else if(h<0.75)hCard.classList.add('warn');}
  var wEl=document.getElementById('m-wno'); if(wEl)wEl.textContent=r.wafer_no||'—';
}

function drawCduMap(map, target){
  var cv=document.getElementById('cdu-map-canvas'); if(!cv)return;
  var ctx=cv.getContext('2d'); var W=cv.width,H=cv.height;
  var rows=map.length, cols=map[0].length;
  var cw=W/cols, ch=H/rows;
  ctx.fillStyle='#030810'; ctx.fillRect(0,0,W,H);
  var spec=10; // ±10 nm spec
  for(var i=0;i<rows;i++){
    for(var j=0;j<cols;j++){
      var v=map[i][j];
      if(v===null||v===undefined){continue;}
      var dev=v-(target||130);
      var t=Math.max(-1,Math.min(1,dev/spec)); // -1 to +1
      var r2,g2,b2;
      if(t<0){r2=0;g2=Math.round(255*(1+t));b2=Math.round(255*(-t));}
      else{r2=Math.round(255*t);g2=Math.round(255*(1-t));b2=0;}
      ctx.fillStyle='rgb('+r2+','+g2+','+b2+')';
      ctx.fillRect(j*cw,i*ch,cw-1,ch-1);
      if(cw>16){ctx.fillStyle='rgba(0,0,0,.6)';
        ctx.font='7px Consolas';ctx.textAlign='center';
        ctx.fillText(v.toFixed(1),(j+.5)*cw,(i+.5)*ch+3);}
    }
  }
  // 色階圖例
  var lgW=14,lgH=H-20;
  var lg=ctx.createLinearGradient(W-16,10,W-16,10+lgH);
  lg.addColorStop(0,'rgb(255,0,0)'); lg.addColorStop(0.5,'rgb(0,255,0)'); lg.addColorStop(1,'rgb(0,0,255)');
  ctx.fillStyle=lg; ctx.fillRect(W-18,10,lgW,lgH);
  ctx.fillStyle='#888'; ctx.font='8px Consolas'; ctx.textAlign='right';
  ctx.fillText('+'+(spec)+'nm',W-20,14); ctx.fillText('0',W-20,10+lgH/2); ctx.fillText('-'+(spec)+'nm',W-20,10+lgH);
}

function drawTrendChart(history){
  var cv=document.getElementById('cdu-trend-canvas'); if(!cv||!history||!history.length)return;
  var ctx=cv.getContext('2d'); var W=cv.width,H=cv.height;
  ctx.fillStyle='#030810'; ctx.fillRect(0,0,W,H);
  if(history.length<2)return;
  var pad={l:40,r:10,t:16,b:28};
  var cw=W-pad.l-pad.r, ch=H-pad.t-pad.b;
  // 畫三條線：CD mean, overlay_x_3s, overlay_y_3s
  var series=[
    {key:'cd_mean',   color:'#4af', label:'CD(nm)', ymin:120,ymax:145},
    {key:'overlay_x_3s',color:'#fa4',label:'OvlX 3σ',ymin:0,ymax:5},
    {key:'overlay_y_3s',color:'#f84',label:'OvlY 3σ',ymin:0,ymax:5},
  ];
  // 使用第一條的 Y 軸
  var ys=series[0];
  var xStep=cw/(history.length-1);
  function toX(i){return pad.l+i*xStep;}
  function toY(v,s){return pad.t+ch-(v-s.ymin)/(s.ymax-s.ymin)*ch;}
  // 格線
  ctx.strokeStyle='#0d2a3a';ctx.lineWidth=1;
  for(var gi=0;gi<=4;gi++){
    var gy=pad.t+gi*ch/4;
    ctx.beginPath();ctx.moveTo(pad.l,gy);ctx.lineTo(W-pad.r,gy);ctx.stroke();
  }
  // Y 軸標籤
  ctx.fillStyle='#5a8a9a';ctx.font='9px Consolas';ctx.textAlign='right';
  for(var gi=0;gi<=4;gi++){
    var gv=ys.ymax-(ys.ymax-ys.ymin)*gi/4;
    ctx.fillText(gv.toFixed(0),pad.l-4,pad.t+gi*ch/4+3);
  }
  // 畫各系列
  series.forEach(function(s){
    ctx.strokeStyle=s.color;ctx.lineWidth=1.5;ctx.beginPath();
    history.forEach(function(h,i){
      var v=h[s.key]; if(v==null)return;
      var x=toX(i), y=toY(v,s);
      if(i===0)ctx.moveTo(x,y); else ctx.lineTo(x,y);
    });
    ctx.stroke();
    // 圖例
    var li=series.indexOf(s);
    ctx.fillStyle=s.color;ctx.fillRect(pad.l+li*80,2,10,7);
    ctx.fillStyle='#9ab';ctx.textAlign='left';ctx.font='9px Consolas';
    ctx.fillText(s.label,pad.l+li*80+13,9);
  });
  // X 軸標籤
  ctx.fillStyle='#5a8a9a';ctx.textAlign='center';ctx.font='9px Consolas';
  [0,Math.floor(history.length/2),history.length-1].forEach(function(i){
    if(history[i])ctx.fillText('W'+history[i].wafer_no,toX(i),H-8);
  });
}

function updateLensTemps(temps){
  var el=document.getElementById('lens-temps'); if(!el)return;
  var names=['IL1','IL2','PL1','PL2','PL3'];
  var html='';
  names.forEach(function(n){
    var t=temps[n]?temps[n].T:0;
    var col=t<0.5?'#4af':t<1.5?'#fa4':'#f44';
    html+='<div class="lens-temp-cell"><div class="name">'+n+'</div>'
      +'<div class="temp" style="color:'+col+'">'+t.toFixed(3)+'</div>'
      +'<div style="font-size:9px;color:#5a8a9a">K</div></div>';
  });
  el.innerHTML=html;
}

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
  // 立即設定遊戲場景（同步），讓 controls.lock() 能在 user gesture 內執行
  gameStarted=true;
  insideMode=false;
  _labelSprites.forEach(function(s){s.visible=false;});
  _outlineMeshes.forEach(function(o){o.visible=false;});
  if(typeof exteriorShell!=='undefined') exteriorShell.visible=true;
  if(glbModel) glbModel.visible=false;
  camera.position.set(_sCX, 1.6, _sCZ+_sD/2+3.0);
  $hud.style.display='flex';$ctrl.style.display='block';
  updateHUD();startTick();
  controls.lock(); // 必須在同步 user-gesture 內呼叫，否則瀏覽器拒絕 Pointer Lock
  // 非同步取得 AI 訊息（不影響遊戲啟動）
  fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({difficulty:diff})})
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.ai_msg)addMsg('ai',d.ai_msg);
    addMsg('sys','已進入無塵室。靠近機台後按 <b>E</b> 進入機器內部。');
  })
  .catch(function(e){
    addMsg('sys','⚠ 連線提示: '+e);
  });
});
// 點擊畫布也可重新鎖定指標（例如 ESC 後重新進入）
renderer.domElement.addEventListener('click',function(){
  if(gameStarted&&!controls.isLocked&&!hmiOpen&&!maintOpen&&!inspecting){
    controls.lock();
  }
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
      if(maintOpen){closeMaintenance();break;}
      if(inspecting){closeInspect();break;}
      // 外殼模式：按 E（hover 到外殼 mesh，或靠近機台 2.5m 內）
      if(!insideMode){
        var _camPos=controls.getObject().position;
        var _distToMachine=Math.sqrt(
          Math.pow(_camPos.x-_sCX,2)+Math.pow(_camPos.z-(_sCZ+_sD/2),2));
        if(hoveredObj&&isShellMesh(hoveredObj)){
          if(hoveredObj.name==='ShellHMI_Screen'){showHMIOverlay();}
          else{enterInterior();}
          break;
        } else if(_distToMachine<2.5){
          enterInterior();break;
        }
      }
      if(hoveredObj){
        // 故障維修優先：檢查 hover 的 mesh 是否屬於某個故障的觸發節點
        var _faultForMesh=null;
        Object.keys(_activeFaults).forEach(function(ft){
          var sop=MAINT_SOP[ft];
          if(sop&&sop.triggerMeshes.indexOf(hoveredObj.name)!==-1) _faultForMesh=ft;
        });
        if(_faultForMesh){
          // 故障觸發 mesh → 開啟零件互動面板（讓操作者自行判斷操作）
          var _fInf=getInfo(hoveredObj);
          if(_fInf&&_fInf.label!=='控制系統'&&_fInf.label!=='HMI 控制面板'){
            openInspect(_fInf.label,_fInf.action);
          } else {
            openMaintenance(_faultForMesh);
          }
          break;
        }
        if(hoveredObj.name==='HMI_Screen'){showHMIOverlay();break;}
        var inf=getInfo(hoveredObj);
        if(inf){
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

// ── DOM 標籤系統（瀏覽器原生字型渲染，完全清晰）────────────────────────────────
var _LABEL_TEXT={
  'Label_Stage':    'Wafer Stage',
  'Label_POB':      'Projection Optics',
  'Label_Illum':    'Illumination System',
  'Label_Laser':    '193nm ArF DUV Laser',
  'Label_Immersion':'Immersion Hood',
  'Label_FOUP':     'FOUP Port',
  'Label_Beam':     'Beam Path',
  'Model_Label':    'ASML TWINSCAN NXT:870  |  193nm ArF Immersion'
};

var _labelSprites=[];  // [{div, worldPos}]

// 每個標籤的世界座標偏移 [dx, dy, dz]，避免擋住零件和動畫
// dx=左右, dy=上下, dz=前後（正值靠近觀察者）
var _LABEL_OFFSET={
  'Label_Stage':    [ 0,    0.05,  0],
  'Label_POB':      [ 0,    0.08,  0],
  'Label_Illum':    [ 0.28, 0.08,  0],   // 右移但不太遠
  'Label_Laser':    [ 0,    0.08,  0],
  'Label_Immersion':[ 0,    0.08,  0],
  'Label_FOUP':     [-0.30, 0.08,  0],   // 往左，不擋 FOUP 本體
  'Label_Beam':     [ 0,    0.08,  0],
  'Model_Label':    [ 0,    0,     0],
};

function _refreshLabels(meshMap){
  _labelSprites.forEach(function(item){item.div.remove();});
  _labelSprites=[];
  var layer=document.getElementById('label-layer');
  Object.keys(_LABEL_TEXT).forEach(function(nm){
    var node=meshMap[nm]; if(!node) return;
    node.visible=false;
    var wp=new THREE.Vector3();
    node.getWorldPosition(wp);
    // 套用偏移
    var off=_LABEL_OFFSET[nm]||[0,0,0];
    wp.x+=off[0]; wp.y+=off[1]; wp.z+=off[2];
    var div=document.createElement('div');
    var isTitle=(nm==='Model_Label');
    div.className=isTitle?'eq-label-title':'eq-label';
    div.textContent=_LABEL_TEXT[nm];
    layer.appendChild(div);
    _labelSprites.push({div:div, pos:wp, title:isTitle});
  });
}

// 每幀把 3D 座標投影成螢幕座標
var _proj=new THREE.Vector3();
function _updateLabelPositions(){
  var show=insideMode&&gameStarted;
  _labelSprites.forEach(function(item){
    if(!show){item.div.style.display='none';return;}
    // 標題固定在畫面頂部，不跟隨 3D 座標
    if(item.title){item.div.style.display='block';return;}
    _proj.copy(item.pos).project(camera);
    if(_proj.z>1){item.div.style.display='none';return;}
    var sx=( _proj.x*0.5+0.5)*CW;
    var sy=(-_proj.y*0.5+0.5)*CH;
    item.div.style.display='block';
    item.div.style.left=sx+'px';
    item.div.style.top=sy+'px';
  });
}
// ─────────────────────────────────────────────────────────────────────────────

// 互動設備群組（同一動作的所有 mesh 合為一組，只建一次 outline）
var _INTERACT_GROUPS=[
  ['Reticle_Stage_Mesh','Reticle_Mesh'],
  ['Robot_Arm_Link_Mesh','Robot_Arm_Base'],
  ['Stage_Base','Rail_-0.6','Rail_0.0','Rail_0.6','Wafer_Chuck','Wafer'],
  ['POB_Barrel','POB_Top_Cap','POB_Bottom'],
  ['Illum_Barrel'],
  ['Laser_Box','Laser_Vent','Laser_Out'],
  ['Immersion_Hood','Immersion_Supply','Immersion_Return'],
  ['Cabinet_Main','Cabinet_Panel','Screen','Keyboard'],
  ['FOUP_Port','FOUP_Door'],
];

var _outlineMeshes=[];  // 所有 outline mesh，供 enterInterior 切換

function _buildOutlines(meshMap){
  try{
    var outMat=new THREE.MeshBasicMaterial({
      color:0xffffff,side:THREE.BackSide,
      transparent:true,opacity:0.50,depthWrite:false
    });
    // 先收集，traverse 完再 add，避免修改正在遍歷的 scene graph
    var _pairs=[];
    _INTERACT_GROUPS.forEach(function(group){
      group.forEach(function(nm){
        var node=meshMap[nm]; if(!node) return;
        node.traverse(function(o){
          if(!o.isMesh||!o.geometry) return;
          _pairs.push(o);
        });
      });
    });
    _pairs.forEach(function(o){
      try{
        var ol=new THREE.Mesh(o.geometry,outMat.clone());
        ol.scale.setScalar(1.06);
        ol.renderOrder=5;
        ol.visible=false;
        o.add(ol);
        _outlineMeshes.push(ol);
      }catch(e){}
    });
    console.log('[OK] outlines built:',_outlineMeshes.length);
  }catch(e){console.warn('[outline] error:',e);}
}

function createProcObjects(model){
  model.traverse(function(o){if(o.name)sceneMeshMap[o.name]=o;});
  _refreshLabels(sceneMeshMap);  // 重新渲染所有標籤
  _buildOutlines(sceneMeshMap);  // 建立互動設備白框

  // ── 玻璃外框擴展，容納照明系統與雷射元件（sceneMeshMap 已填充）────────────
  (function(){
    // X 擴展：右牆右移，頂/底/後板加寬
    var wr=sceneMeshMap['Wall_Right']; if(wr) wr.position.x+=0.28;
    var wl=sceneMeshMap['Wall_Left'];  if(wl) wl.position.x-=0.05;
    ['Roof','Inner_Floor','Wall_Back'].forEach(function(n){
      var nd=sceneMeshMap[n]; if(nd) nd.scale.x*=1.16;
    });
    // Y 擴展：頂板上移，三面牆拉高（scale.y），底板不動
    var roof=sceneMeshMap['Roof']; if(roof) roof.position.y+=0.22;
    ['Wall_Right','Wall_Left','Wall_Back'].forEach(function(n){
      var nd=sceneMeshMap[n]; if(nd) nd.scale.y*=1.18;
    });
    // Duct_Top 是通風管頂蓋（Y=2.38 的寬厚板），卡在照明系統上方，隱藏掉
    var ductTop=sceneMeshMap['Duct_Top']; if(ductTop) ductTop.visible=false;
    var dv1=sceneMeshMap['Duct_Vent1']; if(dv1) dv1.visible=false;
    var dv2=sceneMeshMap['Duct_Vent2']; if(dv2) dv2.visible=false;
    // 雷射系統移位：Y+0.15m（升高至光點高度）
    // Z 方向：自動計算讓機器中心 Z 對齊照明桶 Z（往使用者這邊移動）
    var _illumNode0=sceneMeshMap['Illum_Barrel'];
    var _illumW0=new THREE.Vector3();
    if(_illumNode0) _illumNode0.getWorldPosition(_illumW0);
    var _targetZ=_illumW0.z; // 桶的 Z = 目標機器中心 Z
    var _lzBox0=sceneMeshMap['Laser_Box']; var _lzZShift=0;
    if(_lzBox0){
      var _bb0=new THREE.Box3().setFromObject(_lzBox0);
      var _ctr0=new THREE.Vector3(); _bb0.getCenter(_ctr0);
      _lzZShift=_targetZ-_ctr0.z;
      console.log('[DBG] LaserZ: targetZ='+_targetZ.toFixed(3)+' machCtrZ='+_ctr0.z.toFixed(3)+' zShift='+_lzZShift.toFixed(3));
    }
    ['Laser_Box','Laser_Vent','Laser_Out','Label_Laser'].forEach(function(n){
      var nd=sceneMeshMap[n]; if(nd){ nd.position.y+=0.15; nd.position.z+=_lzZShift; }
    });
    scene.updateMatrixWorld(true);
  })();

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
  var pobTop    = sceneMeshMap['POB_Top_Cap'];
  var pobBot    = sceneMeshMap['POB_Bottom'];
  var wChuck    = sceneMeshMap['Wafer_Chuck'];
  var foupPort  = sceneMeshMap['FOUP_Port'];
  var illumBarrel = sceneMeshMap['Illum_Barrel']; // 照明系統圓柱桶體

  var pobTopW =new THREE.Vector3(); var pobBotW=new THREE.Vector3();
  var chuckW  =new THREE.Vector3(); var foupW  =new THREE.Vector3();
  var illumW  =new THREE.Vector3();
  if(pobTop)    pobTop.getWorldPosition(pobTopW);    else pobTopW.set(0.64,2.19,0.12);
  if(pobBot)    pobBot.getWorldPosition(pobBotW);    else pobBotW.set(0.64,0.71,0.12);
  if(wChuck)    wChuck.getWorldPosition(chuckW);     else chuckW.set(0.24,0.62,0.12);
  if(foupPort)  foupPort.getWorldPosition(foupW);    else foupW.set(-0.93,1.04,0.64);
  // 照明系統圓柱的世界座標（光束起點）
  if(illumBarrel) illumBarrel.getWorldPosition(illumW);
  else illumW.set(pobTopW.x+0.38, pobTopW.y+0.30, pobTopW.z);
  // X 不能超出牆壁（安全上限）
  illumW.x = Math.min(illumW.x, pobTopW.x + 0.55);
  console.log('[DBG] Illum_Barrel found:',!!illumBarrel,' illumW:',illumW.x.toFixed(3),illumW.y.toFixed(3));

  // 儲存動畫用基準位置
  procObjs.chuckW  = chuckW.clone();
  procObjs.pobBotW = pobBotW.clone();

  console.log('[DBG] chuckW:',chuckW.x.toFixed(2),chuckW.y.toFixed(2),chuckW.z.toFixed(2),'  pobTopW:',pobTopW.x.toFixed(2),pobTopW.y.toFixed(2),pobTopW.z.toFixed(2),'  illumW:',illumW.x.toFixed(2),illumW.y.toFixed(2),illumW.z.toFixed(2));

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
  // ── UV 光束：直接使用 GLB 內建的正確光路幾何體 ───────────────────────────────
  // GLB 光路：Laser_Out→Beam_H1→Mirror1→Beam_V1（穿照明桶）
  //          →Mirror2→Beam_H2→Mirror3→Beam_V2（穿投影鏡）→Beam_Spot

  // GLB 光束節點套上半透明粉紅材質（遞迴套用，處理 Group 內的子 Mesh）
  function applyBeamMat(node, mat){
    node.visible=true;
    if(node.isMesh) node.material=mat;
    node.children.forEach(function(c){applyBeamMat(c,mat);});
  }
  ['Beam_H1','Beam_V1','Beam_H2','Beam_V2','Laser_Out'].forEach(function(nm){
    var n=sceneMeshMap[nm];
    if(n){
      var m=uvMat.clone();
      // H1/V1 由自訂光路取代，永久設 opacity=0（不從 GLB 顯示）
      m.opacity=(nm==='Beam_H1'||nm==='Beam_V1')?0:0.80;
      applyBeamMat(n,m);
      procObjs['glb_'+nm]=n;
    } else { console.warn('[BEAM] node not found:',nm); }
    if(n){var _wp=new THREE.Vector3();n.getWorldPosition(_wp);console.log('[DBG] beam',nm,'world=',_wp.x.toFixed(3),_wp.y.toFixed(3),_wp.z.toFixed(3));}
  });
  // 折鏡保持原始金屬材質、確保可見
  ['Mirror1','Mirror2','Mirror3'].forEach(function(nm){
    var n=sceneMeshMap[nm];
    if(n){n.visible=true;n.children.forEach(function(c){c.visible=true;});procObjs['glb_'+nm]=n;}
  });
  // Beam_Spot：曝光時才顯示
  var glbSpotNode=sceneMeshMap['Beam_Spot'];
  if(glbSpotNode){glbSpotNode.visible=false;procObjs.glbSpot=glbSpotNode;}

  // ── 照明桶半透明（讓桶內 Beam_V1 可見）──────────────────────────────────────
  var illumBarrelNode=sceneMeshMap['Illum_Barrel'];
  if(illumBarrelNode){
    illumBarrelNode.traverse(function(c){
      if(c.isMesh&&c.material){
        c.material.transparent=true;
        c.material.opacity=0.35;
        c.material.depthWrite=false;
      }
    });
  }

  // IllumLens 鏡片：浮空且令人困惑，隱藏以保持視覺乾淨
  ['IllumLens_0','IllumLens_1','IllumLens_2',
   'IllumLens_3','IllumLens_4','IllumLens_5'].forEach(function(nm){
    var n=sceneMeshMap[nm]; if(n) n.visible=false;
  });

  // 相容性 stub（動畫程式仍引用的舊欄位，設空值避免 null 錯誤）
  procObjs.laserToIllum=null;procObjs.illuBeam=null;
  procObjs.illumToLens=null;procObjs.lensRiser=null;procObjs.hBeam=null;
  procObjs.lzConnect=null; procObjs.lzDeliver=null;
  procObjs.lzBarrelFill=null; procObjs.lzEntry=null; procObjs.lzBarrelThrough=null;

  // ── 雷射→照明系統 L形單彎示意光路 ──────────────────────────────────────────
  // 路徑：雷射箱左側面(lzGlow) → 水平射出(lzEntry) → 彎折球(lzBend) → 垂直穿越桶身(lzBarrelThrough)
  var lzOutNode=sceneMeshMap['Laser_Out'];
  var lzBoxNode=sceneMeshMap['Laser_Box'];
  var _illumBarrelNode2=sceneMeshMap['Illum_Barrel'];
  var _beamH2Node=sceneMeshMap['Beam_H2'];
  procObjs.lzBend=null;
  if(lzOutNode && _illumBarrelNode2){
    var lzOutW=new THREE.Vector3(); lzOutNode.getWorldPosition(lzOutW);
    // 雷射箱高度 & 光束水平起點
    var lzBoxY=0.85; var lzStartX=lzOutW.x;
    if(lzBoxNode){
      // 用 BoundingBox 取機器的視覺中心（X, Y）— GLB 原點位置不固定，bbox 中心最可靠
      var _lzbb2=new THREE.Box3().setFromObject(lzBoxNode);
      var _lzCtr=new THREE.Vector3(); _lzbb2.getCenter(_lzCtr);
      lzBoxY=_lzCtr.y;
      lzStartX=_lzCtr.x; // 球放在機器視覺中心 X
      console.log('[DBG] Laser_Box bbox centerX='+lzStartX.toFixed(3)+' centerY='+lzBoxY.toFixed(3)+' centerZ='+_lzCtr.z.toFixed(3)+' minX='+_lzbb2.min.x.toFixed(3)+' maxX='+_lzbb2.max.x.toFixed(3)+' minZ='+_lzbb2.min.z.toFixed(3)+' maxZ='+_lzbb2.max.z.toFixed(3));
    }
    // 照明桶中心 X（彎折點 & 垂直段位置）
    var _illumCW2=new THREE.Vector3(); _illumBarrelNode2.getWorldPosition(_illumCW2);
    var barrelCX=_illumCW2.x; var barrelCZ=_illumCW2.z; // 用桶本身的 Z（固定不動），不用 Laser_Out Z（會隨機器移動而偏移）
    // 垂直段頂點：Beam_H2 出口（桶頂出口接投影系統）
    var barrelExitY=_illumCW2.y+0.3;
    if(_beamH2Node){var _h2W=new THREE.Vector3();_beamH2Node.getWorldPosition(_h2W);barrelExitY=_h2W.y;}
    console.log('[DBG] lzBoxY='+lzBoxY.toFixed(3)+' lzStartX='+lzStartX.toFixed(3)+' barrelCX='+barrelCX.toFixed(3)+' barrelExitY='+barrelExitY.toFixed(3));

    // ① 發光球：已移除，但保留材質供彎折球使用
    var lzGlowMat=new THREE.MeshStandardMaterial({
      color:0xff44ff,emissive:0xcc00cc,emissiveIntensity:3.0,transparent:true,opacity:0.95});
    procObjs.lzGlow=null;

    // ② 水平段：雷射箱左側面 → 照明桶中心 X（在 lzBoxY 高度水平飛行）
    var _hDist=Math.abs(lzStartX-barrelCX);
    if(_hDist>0.02){
      var _hMidX=(lzStartX+barrelCX)/2;
      var lzHorizMesh=new THREE.Mesh(new THREE.CylinderGeometry(0.016,0.016,_hDist,8),uvMat.clone());
      lzHorizMesh.rotation.z=Math.PI/2;
      lzHorizMesh.position.set(_hMidX, lzBoxY, barrelCZ);
      lzHorizMesh.visible=false;
      scene.add(lzHorizMesh); procObjs.lzEntry=lzHorizMesh;
      console.log('[OK] lzHoriz x='+lzStartX.toFixed(3)+'~'+barrelCX.toFixed(3)+' y='+lzBoxY.toFixed(3));
    }

    // ③ 彎折球：在彎折點放一個小球，視覺上標示 90° 轉向
    var lzBendMesh=new THREE.Mesh(new THREE.SphereGeometry(0.025,10,10),lzGlowMat.clone());
    lzBendMesh.position.set(barrelCX, lzBoxY, barrelCZ);
    lzBendMesh.visible=false;
    scene.add(lzBendMesh); procObjs.lzBend=lzBendMesh;

    // ④ 垂直段：彎折點(barrelCX, lzBoxY) → 照明桶頂出口(barrelCX, barrelExitY)
    //    從彎折點一路垂直穿過照明桶底部到頂部
    var _vLen=barrelExitY-lzBoxY-0.02;
    if(_vLen>0.05){
      var lzRiseAllMesh=new THREE.Mesh(new THREE.CylinderGeometry(0.016,0.016,_vLen,8),uvMat.clone());
      lzRiseAllMesh.position.set(barrelCX, lzBoxY+_vLen/2, barrelCZ);
      lzRiseAllMesh.visible=false;
      scene.add(lzRiseAllMesh); procObjs.lzBarrelThrough=lzRiseAllMesh;
      console.log('[OK] lzRiseAll x='+barrelCX.toFixed(3)+' y='+lzBoxY.toFixed(3)+'~'+barrelExitY.toFixed(3));
    }

    // ── 光路方向箭頭 (ArrowHelper, depthTest:false, 流動式) ──
    procObjs.photonWP=[
      new THREE.Vector3(lzStartX, lzBoxY, barrelCZ),        // P0: 雷射射出點
      new THREE.Vector3(barrelCX,  lzBoxY, barrelCZ),        // P1: 彎折鏡
      new THREE.Vector3(barrelCX,  barrelExitY, barrelCZ),   // P2: 照明系統出口
      // P3 在 rsCX 確定後 push
    ];
    procObjs.barrelCX=barrelCX; procObjs.barrelCZ=barrelCZ;
    // 先建好 photons 陣列（ArrowHelper 在 P3 push 後才建立）
    procObjs.photons=[];
  }

  // ── 掃描曝光光束（細線，跟隨 chuck 位置動畫） ────────────────────────────────
  var beamTop = Math.max(rsY+0.10, illumW.y+0.05, chuckW.y+1.0);
  var beamBot = chuckW.y;
  var beamH   = Math.max(beamTop-beamBot, 0.1);
  var beamMidY= (beamTop+beamBot)/2;
  var beamCyl=new THREE.Mesh(new THREE.CylinderGeometry(.012,.005,beamH,8),uvMat.clone());
  beamCyl.position.set(rsCX,beamMidY,rsCZ);beamCyl.visible=false; // 由 GLB Beam_V2 負責，此自訂桶永久隱藏
  scene.add(beamCyl);procObjs.beamCyl=beamCyl;
  procObjs.beamMidY=beamMidY;procObjs.beamTop=beamTop;procObjs.beamBot=beamBot;
  procObjs.rsCX=rsCX;procObjs.rsCZ=rsCZ;
  // 補全 waypoints：P2.5（照明出口→投影鏡頂水平段）+ P3（晶圓）
  if(procObjs.photonWP){
    var _wp2=procObjs.photonWP;
    var _p2=_wp2[2]; // (barrelCX, barrelExitY, barrelCZ)
    // P2.5：同高度水平移到投影鏡正上方（rsY 是光罩載台頂，再往上一點是 POB 入口）
    var _pobEntryY=Math.max(_p2.y, rsY+0.05);
    _wp2.push(new THREE.Vector3(rsCX, _pobEntryY, rsCZ));
    // P3：投影鏡正下方晶圓
    _wp2.push(new THREE.Vector3(rsCX, chuckW.y+0.04, rsCZ));
    // 建立流動式 ArrowHelper（depthTest:false）
    var _NPER2=6;
    var _aLen=0.18, _aHL=0.09, _aHW=0.06;
    for(var _si2=0;_si2<_wp2.length-1;_si2++){
      var _from2=_wp2[_si2], _to2=_wp2[_si2+1];
      if(_from2.distanceTo(_to2)<0.01) continue; // 跳過零長度段
      var _dir2=new THREE.Vector3().subVectors(_to2,_from2).normalize();
      for(var _ai=0;_ai<_NPER2;_ai++){
        var _arr=new THREE.ArrowHelper(_dir2,_from2.clone(),_aLen,0xff00ff,_aHL,_aHW);
        _arr.line.material.transparent=true; _arr.line.material.depthTest=false; _arr.line.material.opacity=0;
        _arr.cone.material.transparent=true; _arr.cone.material.depthTest=false; _arr.cone.material.opacity=0;
        _arr.line.renderOrder=999; _arr.cone.renderOrder=999; _arr.renderOrder=999;
        _arr.visible=false;
        _arr.userData={seg:_si2, off:_ai/_NPER2};
        scene.add(_arr);
        procObjs.photons.push(_arr);
      }
    }
  }

  // 光罩光暈
  var reticlGlow=new THREE.Mesh(new THREE.CircleGeometry(.14,32),glowMat.clone());
  reticlGlow.rotation.x=-Math.PI/2;
  reticlGlow.position.set(rsCX,rmBaseY-0.002,rsCZ);reticlGlow.visible=false;
  scene.add(reticlGlow);procObjs.reticleGlow=reticlGlow;

  // 晶圓曝光光暈
  var beamSpot=new THREE.Mesh(new THREE.CircleGeometry(.04,32),glowMat.clone());
  beamSpot.rotation.x=-Math.PI/2;
  beamSpot.position.set(rsCX,chuckW.y+0.002,rsCZ);beamSpot.visible=false;
  scene.add(beamSpot);procObjs.beamSpotGlow=beamSpot;

  // 點光源
  var laserPtLight=new THREE.PointLight(0x9900ff,0.3,0.8);
  laserPtLight.position.copy(illumW);scene.add(laserPtLight);
  procObjs.laserPtLight=laserPtLight;procObjs.laserGlow=null;

  beamPtLight=new THREE.PointLight(0x9900ff,0,1.4);
  beamPtLight.position.set(rsCX,chuckW.y+0.06,rsCZ);scene.add(beamPtLight);

  // GLB Wafer_Chuck / Wafer 動畫與製程動畫衝突，停止 GLB 動畫交由製程動畫統一管理
  if(mixer){mixer.stopAllAction();mixer=null;}

  console.log('[OK] Proc objects built. efStart:',procObjs.efStart.x.toFixed(2),procObjs.efStart.z.toFixed(2),'→ efEnd:',procObjs.efEnd.x.toFixed(2),procObjs.efEnd.z.toFixed(2));
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

  // ── UV 光束：只在雷射開啟期間顯示（t>=9 chuck 就位後；t>=10 曝光）──────────
  var laserOn=(t>=9&&t<19.5);   // 雷射開啟窗口
  var exposing=(t>=10&&t<19);    // 曝光中（快速脈衝）

  // 全部光束節點：非 laserOn 期間完全隱藏
  // H1/V1 永久 opacity=0（已由自訂路徑取代），只動畫化 H2/V2/Laser_Out
  var _GLB_BEAMS=['glb_Beam_H2','glb_Beam_V2','glb_Laser_Out'];
  if(!laserOn){
    if(procObjs.beamCyl)procObjs.beamCyl.visible=false;
    if(procObjs.lzGlow){procObjs.lzGlow.visible=false;}
    if(procObjs.lzRise){procObjs.lzRise.visible=false;}
    if(procObjs.lzEntry){procObjs.lzEntry.visible=false;}
    if(procObjs.lzBend){procObjs.lzBend.visible=false;}
    if(procObjs.lzBarrelThrough){procObjs.lzBarrelThrough.visible=false;}
    _GLB_BEAMS.forEach(function(k){
      if(procObjs[k])procObjs[k].traverse(function(c){if(c.isMesh&&c.material)c.material.opacity=0;});
    });
    if(procObjs.glbSpot)procObjs.glbSpot.visible=false;
    if(procObjs.reticleGlow)procObjs.reticleGlow.visible=false;
    if(procObjs.beamSpotGlow)procObjs.beamSpotGlow.visible=false;
    if(beamPtLight)beamPtLight.intensity=0;
    if(procObjs.laserPtLight)procObjs.laserPtLight.intensity=0;
  }

  // 光罩光暈 & 晶圓光暈：只在曝光時顯示
  if(procObjs.reticleGlow)procObjs.reticleGlow.visible=exposing;
  if(procObjs.beamSpotGlow)procObjs.beamSpotGlow.visible=exposing;

  var breathe=0.5+0.5*Math.sin(procElapsed*Math.PI*0.6);

  if(beamPtLight){
    if(wChuck){
      var cwp=new THREE.Vector3();
      wChuck.getWorldPosition(cwp);
      if(exposing){
        // 曝光：快速脈衝，高亮
        var pulse=0.5+0.5*Math.sin(t*Math.PI*12);
        beamPtLight.intensity=pulse*2.0;
        var _op=0.55+pulse*0.40;
        if(procObjs.lzGlow){procObjs.lzGlow.visible=true;procObjs.lzGlow.material.opacity=0.7+pulse*0.3;}
        if(procObjs.lzRise){procObjs.lzRise.visible=true;procObjs.lzRise.material.opacity=_op;}
        if(procObjs.lzEntry){procObjs.lzEntry.visible=true;procObjs.lzEntry.material.opacity=_op;}
        if(procObjs.lzBend){procObjs.lzBend.visible=true;procObjs.lzBend.material.opacity=0.8+pulse*0.2;}
        if(procObjs.lzBarrelThrough){procObjs.lzBarrelThrough.visible=true;procObjs.lzBarrelThrough.material.opacity=_op;}
        _GLB_BEAMS.forEach(function(k){
          if(procObjs[k])procObjs[k].traverse(function(c){if(c.isMesh&&c.material)c.material.opacity=_op;});
        });
        if(procObjs.glbSpot)procObjs.glbSpot.visible=true;
        if(procObjs.laserPtLight)procObjs.laserPtLight.intensity=0.5+pulse*1.2;
        if(procObjs.reticleGlow){
          procObjs.reticleGlow.material.opacity=0.3+pulse*0.4;
          procObjs.reticleGlow.position.x=cwp.x;
          procObjs.reticleGlow.position.z=cwp.z;
        }
        if(procObjs.beamSpotGlow){
          procObjs.beamSpotGlow.material.opacity=0.4+pulse*0.5;
          procObjs.beamSpotGlow.position.x=cwp.x;
          procObjs.beamSpotGlow.position.z=cwp.z;
        }
        beamPtLight.position.x=cwp.x;beamPtLight.position.z=cwp.z;
      } else if(laserOn){
        // 雷射預熱（t=9~10）：低強度穩定光
        var warmOp=0.25+breathe*0.10;
        beamPtLight.intensity=breathe*0.3;
        if(procObjs.lzGlow){procObjs.lzGlow.visible=true;procObjs.lzGlow.material.opacity=warmOp;}
        if(procObjs.lzRise){procObjs.lzRise.visible=true;procObjs.lzRise.material.opacity=warmOp;}
        if(procObjs.lzEntry){procObjs.lzEntry.visible=true;procObjs.lzEntry.material.opacity=warmOp;}
        if(procObjs.lzBend){procObjs.lzBend.visible=true;procObjs.lzBend.material.opacity=warmOp;}
        if(procObjs.lzBarrelThrough){procObjs.lzBarrelThrough.visible=true;procObjs.lzBarrelThrough.material.opacity=warmOp;}
        _GLB_BEAMS.forEach(function(k){
          if(procObjs[k])procObjs[k].traverse(function(c){if(c.isMesh&&c.material)c.material.opacity=warmOp;});
        });
        if(procObjs.laserPtLight)procObjs.laserPtLight.intensity=breathe*0.3;
      } else {
        // 不在 laserOn 範圍：由上方統一設 opacity=0，此處僅保持點光源為 0
        beamPtLight.intensity=0;
      }
    } else {beamPtLight.intensity=0;}
  }

  // ── 10~19s: 光罩掃描（世界座標 Y 軸小幅往復）────────────────────────────
  if(procObjs.rm&&procObjs.rmMarks){
    var rmY=exposing?
      procObjs.rmBaseY+0.012*Math.sin(t*Math.PI*3.5):procObjs.rmBaseY;
    procObjs.rm.position.y=rmY;
    procObjs.rmMarks.forEach(function(m){m.position.y=rmY+0.003;});
  }

  // ── ArrowHelper 流動動畫（depthTest:false，直接顯示在光束上方）──────────────
  if(procObjs.photons&&procObjs.photons.length>0&&procObjs.photonWP&&procObjs.photonWP.length>=4){
    var _wp=procObjs.photonWP;
    var _speed=exposing?2.0:0.7;
    var _maxOp=exposing?0.95:0.6;
    procObjs.photons.forEach(function(_arr){
      var _ud=_arr.userData;
      if(!laserOn){_arr.visible=false;return;}
      var _p=(( t*_speed+_ud.off)%1.0);
      _arr.visible=true;
      _arr.position.lerpVectors(_wp[_ud.seg],_wp[_ud.seg+1],_p);
      // 頭尾稍微淡出，中段全亮
      var _fade=Math.sin(_p*Math.PI)*0.7+0.3;
      var _op=_maxOp*_fade;
      _arr.line.material.opacity=_op;
      _arr.cone.material.opacity=_op;
      // 曝光時縮放脈衝
      var _s=exposing?(1.0+0.3*Math.sin(t*Math.PI*6+_ud.off*10)):1.0;
      _arr.scale.setScalar(_s);
    });
  } else if(procObjs.photons){
    procObjs.photons.forEach(function(_arr){_arr.visible=false;});
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
    var _allHits=raycaster.intersectObjects(allMeshes);
    // Three.js Mesh.raycast() 不檢查 visible，需手動過濾：
    // 外殼模式只看外殼 mesh；內部模式排除外殼 mesh
    var hits=insideMode
      ? _allHits.filter(function(h){return !isShellMesh(h.object);})
      : _allHits.filter(function(h){return isShellMesh(h.object);});
    if(hoveredObj){
      if(origMats.has(hoveredObj))hoveredObj.material=origMats.get(hoveredObj);
      hoveredObj=null;
      if(!inspecting&&!hmiOpen){$prompt.style.display='none';$xhair.classList.remove('hit');}
    }
    if(hits.length>0){
      var obj=hits[0].object;
      // 外殼模式：hover 外殼
      if(!insideMode&&isShellMesh(obj)){
        if(!origMats.has(obj))origMats.set(obj,obj.material);
        obj.material=hlMat;hoveredObj=obj;
        if(!inspecting&&!hmiOpen){
          $prompt.textContent=(obj.name==='ShellHMI_Screen'
            ?'[E] 開啟 HMI 控制面板':'[E] 進入機器內部');
          $prompt.style.left=(CW/2)+'px';$prompt.style.display='block';
          $xhair.classList.add('hit');
        }
      } else {
        var inf=getInfo(obj);
        if(inf){
          if(!origMats.has(obj))origMats.set(obj,obj.material);
          obj.material=hlMat;hoveredObj=obj;
          if(!inspecting&&!hmiOpen&&!maintOpen){
            // 故障維修提示優先
            var _faultPrompt=null;
            Object.keys(_activeFaults).forEach(function(ft){
              var sop=MAINT_SOP[ft];
              if(sop&&sop.triggerMeshes.indexOf(obj.name)!==-1) _faultPrompt=sop.title;
            });
            var isHMITrigger=(obj.name==='HMI_Screen'||inf.label==='控制系統'||inf.label==='HMI 控制面板');
            $prompt.textContent=_faultPrompt
              ?'[E] ⚠ 開始維修：'+_faultPrompt
              :(isHMITrigger?'[E] 開啟 HMI 控制面板（感測器 & ERROR Log）':'[E] 檢查: '+inf.label);
            $prompt.style.left=(CW/2)+'px';$prompt.style.display='block';
            $xhair.classList.add('hit');
          }
        }
      }
    }
  }
  renderer.render(scene,camera);
  _updateLabelPositions();
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
    # 若 static/viewer.html 已存在，保留手動修改版本，不覆蓋
    if out.exists():
        print(f"[OK] viewer.html 從 {out}")
        return
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
