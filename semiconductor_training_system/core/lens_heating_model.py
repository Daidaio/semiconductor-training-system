# -*- coding: utf-8 -*-
"""
Lens Heating Physics Model — DUV 248nm ArF Excimer Laser Scanner
================================================================
基於文獻的物理模型：
  - 雙指數熱時間常數模型 (SPIE 10587, 2018)
  - Bossung Curve: CD vs focus/dose (標準曝光機模型)
  - Zernike 像差分解 Z4/Z7/Z9 → overlay 誤差
  - Wafer CDU Map 生成（含空間非均勻性）

參考文獻：
  [1] "Fast thermal aberration model" Optics Express 27, 34038 (2019)
  [2] "Prediction of lens heating via particle filter" SPIE 10587 (2018)
  [3] Leviton & Frey, "Temperature-dependent RI of fused silica" SPIE 6273 (2006)
  [4] Corning HPFS 7980 datasheet
"""

import math
import time
import numpy as np
from typing import Dict, List, Tuple


# ── 熔石英材料常數 (248 nm, HPFS grade) ────────────────────────────────────
# Leviton & Frey (2006) + Corning HPFS 7980 datasheet
DN_DT       = 13.5e-6   # K⁻¹  熱光係數 dn/dT at 248 nm
ALPHA_FS    = 0.52e-6   # K⁻¹  熱膨脹係數
N_248       = 1.508     # 折射率 at 248 nm
# 等效熱光係數 α_eff = dn/dT + (n-1)*α
ALPHA_EFF   = DN_DT + (N_248 - 1.0) * ALPHA_FS   # ≈ 13.76e-6 K⁻¹

# ── 投影鏡組系統參數 ────────────────────────────────────────────────────────
# DUV NXT:870 典型規格
DEFAULT_NA      = 0.75      # 數值孔徑 (dry DUV, NXT:870)
DEFAULT_SIGMA   = 0.75      # 照明部分同調度
DEFAULT_DOSE    = 30.0      # mJ/cm²  標準曝光dose
DEFAULT_FOCUS   = 0.0       # nm      焦距偏移（相對最佳焦距）
WAVELENGTH      = 248.0     # nm      KrF 波長

# ── 鏡片熱模型參數 (SPIE 10587 particle filter calibration) ────────────────
# 5 個關鍵鏡片元件：IL1, IL2 (照明鏡組), PL1, PL2, PL3 (投影鏡組)
LENS_ELEMENTS = {
    "IL1": {"role": "illumination", "f_mm": 180, "L_mm": 22,
            "tau1": 45,  "tau2": 480,   # s
            "A1_per_dose": 0.0018, "A2_per_dose": 0.0032,   # K per mJ/cm²
            "sensitivity_focus": 0.35},   # nm focus shift per K
    "IL2": {"role": "illumination", "f_mm": 120, "L_mm": 18,
            "tau1": 60,  "tau2": 600,
            "A1_per_dose": 0.0012, "A2_per_dose": 0.0025,
            "sensitivity_focus": 0.22},
    "PL1": {"role": "projection",   "f_mm":  80, "L_mm": 35,
            "tau1": 90,  "tau2": 900,
            "A1_per_dose": 0.0025, "A2_per_dose": 0.0055,
            "sensitivity_focus": 0.68},
    "PL2": {"role": "projection",   "f_mm":  55, "L_mm": 28,
            "tau1": 75,  "tau2": 720,
            "A1_per_dose": 0.0020, "A2_per_dose": 0.0045,
            "sensitivity_focus": 0.55},
    "PL3": {"role": "projection",   "f_mm":  45, "L_mm": 20,
            "tau1": 50,  "tau2": 540,
            "A1_per_dose": 0.0015, "A2_per_dose": 0.0038,
            "sensitivity_focus": 0.42},
}

# ── Bossung Curve 參數 (248 nm, CD target = 130 nm) ────────────────────────
BOSSUNG = {
    "CD0":       130.0,   # nm  目標線寬 (best focus, nominal dose)
    "a_focus":     0.0008,  # nm / nm²  拋物線曲率 (CD 對焦距偏移的敏感度)
    "b_dose":     -2.1,    # nm / (mJ/cm²)  dose敏感度
    "dose_nom":   30.0,    # mJ/cm²  標準dose
    "focus_best":  0.0,    # nm  最佳焦距
    "EL_plus":   150.0,    # nm  正側曝光容差 (±150 nm process window)
    "EL_minus": -150.0,    # nm  負側
}

# ── Zernike 係數 → Overlay 轉換係數 ────────────────────────────────────────
# overlay ≈ Z7_coeff / NA × process_factor
COMA_OVERLAY_FACTOR = 1.8   # nm overlay per nm Z7 coma (at NA=0.75)


class LensHeatingEngine:
    """
    物理驅動的鏡片熱模型引擎

    使用雙指數熱時間常數模擬每個鏡片元件的溫升，
    再透過 Bossung curve 和 Zernike 分解計算 CD 及 Overlay 誤差。
    """

    def __init__(self):
        self._reset_state()

    def _reset_state(self):
        # 每個鏡片的熱狀態：{name: {"T": float, "acc1": float, "acc2": float}}
        self._lens_state = {
            name: {"T": 0.0, "acc1": 0.0, "acc2": 0.0}
            for name in LENS_ELEMENTS
        }
        self._last_exposure_time = None   # 上次曝光時間戳
        self._exposure_count = 0
        self._history: List[Dict] = []    # 每片 wafer 的結果歷史

    def reset(self):
        self._reset_state()

    # ── 核心：雙指數熱模型 ──────────────────────────────────────────────────
    def _update_lens_temperature(self, name: str, dose: float, dt: float) -> float:
        """
        雙指數模型更新鏡片溫度。
        W(t) = A1*(1-exp(-t/τ1)) + A2*(1-exp(-t/τ2))
        dt: 距上次曝光的時間（秒）
        dose: 本次曝光dose mJ/cm²
        """
        el   = LENS_ELEMENTS[name]
        st   = self._lens_state[name]
        tau1, tau2 = el["tau1"], el["tau2"]
        A1   = el["A1_per_dose"] * dose
        A2   = el["A2_per_dose"] * dose

        # 先讓現有熱量冷卻 dt 秒
        if dt > 0:
            st["acc1"] *= math.exp(-dt / tau1)
            st["acc2"] *= math.exp(-dt / tau2)

        # 本次曝光加熱
        st["acc1"] += A1
        st["acc2"] += A2

        # 總溫升
        st["T"] = st["acc1"] + st["acc2"]
        return st["T"]

    def _cool_down(self, dt: float):
        """純冷卻（無曝光時呼叫）"""
        for name, el in LENS_ELEMENTS.items():
            st = self._lens_state[name]
            st["acc1"] *= math.exp(-dt / el["tau1"])
            st["acc2"] *= math.exp(-dt / el["tau2"])
            st["T"] = st["acc1"] + st["acc2"]

    # ── 焦距偏移計算 ────────────────────────────────────────────────────────
    def _calc_focus_shift(self) -> float:
        """
        各鏡片溫升 → 焦距偏移 (nm)
        Δf = Σ sensitivity_focus_i * ΔT_i
        """
        return sum(
            LENS_ELEMENTS[n]["sensitivity_focus"] * self._lens_state[n]["T"]
            for n in LENS_ELEMENTS
        )

    # ── Zernike 像差分解 ────────────────────────────────────────────────────
    def _calc_zernike(self, focus_total: float, na: float, sigma: float) -> Dict:
        """
        由焦距偏移和 NA/sigma 計算主要 Zernike 係數 (nm rms)
        - Z4  defocus: 主要焦距漂移貢獻
        - Z9  spherical: 熱梯度引起的球差
        - Z7  coma: off-axis 照明引起的彗差 (與 sigma 相關)
        """
        # Z4 defocus ≈ 焦距偏移 × NA² / (2√3)
        z4 = focus_total * na**2 / (2 * math.sqrt(3))

        # Z9 primary spherical ≈ k * Z4 * NA² (典型比例 ~0.12)
        z9 = 0.12 * abs(z4) * na**2

        # Z7 coma ≈ sigma_center * focus_shift * NA (off-axis 效應)
        sigma_c = sigma * 0.6   # 等效 sigma center
        z7 = sigma_c * focus_total * na * 0.015

        return {"Z4": z4, "Z7": z7, "Z9": z9}

    # ── Bossung Curve → CD ─────────────────────────────────────────────────
    def _bossung_cd(self, focus_actual: float, dose: float) -> float:
        """
        CD = CD0 + a*(focus - f_best)² + b*(dose - dose_nom)
        focus_actual: 實際焦距偏移 = 設定值 + 熱漂移
        """
        b = BOSSUNG
        cd = (b["CD0"]
              + b["a_focus"] * (focus_actual - b["focus_best"])**2
              + b["b_dose"]  * (dose - b["dose_nom"]))
        return max(cd, 1.0)  # 防止負值

    # ── CDU Map（空間分佈）──────────────────────────────────────────────────
    def _build_cdu_map(self, cd_mean: float, na: float,
                       noise_sigma: float, grid: int = 13) -> List[List[float]]:
        """
        生成 grid×grid 的 CDU map（nm）
        包含：場邊緣像差（field curvature）+ 隨機製程噪聲
        """
        rng = np.random.default_rng(seed=int(cd_mean * 1000) % 9999)
        cx, cy = grid // 2, grid // 2
        radius = grid // 2

        cdu = []
        for i in range(grid):
            row = []
            for j in range(grid):
                # 在圓形 wafer 邊界外設為 None
                r_norm = math.sqrt((i - cx)**2 + (j - cy)**2) / radius
                if r_norm > 1.0:
                    row.append(None)
                    continue
                # field curvature: 邊緣比中心多 +0.8 nm per unit²
                field_curv = 0.8 * r_norm**2
                # NA 相關的邊緣 CD roll-off
                edge_rolloff = 1.2 * r_norm**3 * (na / DEFAULT_NA)
                # 高斯隨機噪聲 (製程變異)
                noise = float(rng.normal(0, noise_sigma))
                cd_ij = cd_mean + field_curv + edge_rolloff + noise
                row.append(round(cd_ij, 2))
            cdu.append(row)
        return cdu

    # ── Overlay 向量場 ──────────────────────────────────────────────────────
    def _build_overlay_map(self, zernike: Dict, na: float,
                           grid: int = 7) -> List[Dict]:
        """
        生成 overlay 量測點（模擬 ASML 5x5 grid + edge points）
        回傳：[{x_field, y_field, dx_nm, dy_nm}, ...]
        """
        z7 = zernike["Z7"]
        z4 = zernike["Z4"]
        overlay_pts = []
        step = 2.0 / (grid - 1)
        for i in range(grid):
            for j in range(grid):
                fx = -1.0 + i * step   # field position -1 ~ +1
                fy = -1.0 + j * step
                r  = math.sqrt(fx**2 + fy**2)
                if r > 1.05:
                    continue
                # 彗差 coma → 徑向 overlay
                dx = COMA_OVERLAY_FACTOR * z7 * fx / (na * max(r, 0.01))
                dy = COMA_OVERLAY_FACTOR * z7 * fy / (na * max(r, 0.01))
                # defocus coupling → 小的 overlay 殘差
                dx += 0.15 * z4 * fx
                dy += 0.15 * z4 * fy
                overlay_pts.append({
                    "x": round(fx, 3), "y": round(fy, 3),
                    "dx": round(dx, 3), "dy": round(dy, 3)
                })
        return overlay_pts

    # ── 主入口：模擬一片 Wafer 曝光 ────────────────────────────────────────
    def expose_wafer(self, dose: float = DEFAULT_DOSE,
                     focus: float = DEFAULT_FOCUS,
                     na: float = DEFAULT_NA,
                     sigma: float = DEFAULT_SIGMA,
                     noise_sigma: float = 1.5) -> Dict:
        """
        模擬一片 wafer 曝光，回傳完整物理結果。

        Parameters
        ----------
        dose       : 曝光dose (mJ/cm²)
        focus      : 使用者設定的焦距偏移 (nm)
        na         : 數值孔徑
        sigma      : 照明部分同調度
        noise_sigma: SECOM 注入的製程噪聲 (nm)

        Returns
        -------
        dict 包含 CD、overlay、溫度、Zernike 等完整資訊
        """
        now = time.time()
        if self._last_exposure_time is not None:
            dt = now - self._last_exposure_time
        else:
            dt = 0.0
        self._last_exposure_time = now
        self._exposure_count += 1

        # 1. 更新各鏡片溫度
        lens_temps = {}
        for name in LENS_ELEMENTS:
            lens_temps[name] = round(
                self._update_lens_temperature(name, dose, dt), 4)

        # 2. 焦距熱漂移
        thermal_focus_drift = self._calc_focus_shift()
        focus_actual = focus + thermal_focus_drift  # 實際焦距 = 設定 + 熱漂移

        # 3. Zernike 像差
        zernike = self._calc_zernike(focus_actual, na, sigma)

        # 4. Bossung → CD
        cd_mean = self._bossung_cd(focus_actual, dose)

        # 5. CDU map (13×13 grid)
        cdu_map = self._build_cdu_map(cd_mean, na, noise_sigma)

        # 6. CD 統計
        flat = [v for row in cdu_map for v in row if v is not None]
        cd_std  = float(np.std(flat))
        cd_3sig = 3.0 * cd_std

        # 7. Overlay map
        overlay_map = self._build_overlay_map(zernike, na)
        dx_vals = [p["dx"] for p in overlay_map]
        dy_vals = [p["dy"] for p in overlay_map]
        ov_x_3s = round(3.0 * float(np.std(dx_vals)), 3)
        ov_y_3s = round(3.0 * float(np.std(dy_vals)), 3)

        # 8. Magnification error (ppm) ← Z4 引起的等效放大率誤差
        mag_error_ppm = round(zernike["Z4"] * 0.008, 4)

        # 9. Yield prediction (基於 CD 偏移的簡化模型)
        cd_dev = abs(cd_mean - BOSSUNG["CD0"])
        spec_limit = 10.0  # ±10 nm spec
        yield_prob = max(0.0, 1.0 - (cd_dev / spec_limit)**1.5)

        result = {
            "wafer_no":    self._exposure_count,
            "timestamp":   round(now, 2),
            # ── CD ──
            "cd_mean":     round(cd_mean, 2),
            "cd_3sigma":   round(cd_3sig, 3),
            "cd_target":   BOSSUNG["CD0"],
            "cdu_map":     cdu_map,
            # ── Overlay ──
            "overlay_x_3s": ov_x_3s,
            "overlay_y_3s": ov_y_3s,
            "overlay_map":  overlay_map,
            "mag_error_ppm": mag_error_ppm,
            # ── 物理中間量 ──
            "focus_set":   round(focus, 2),
            "focus_drift": round(thermal_focus_drift, 3),
            "focus_actual":round(focus_actual, 3),
            "dose":        round(dose, 2),
            "na":          round(na, 3),
            "sigma":       round(sigma, 3),
            # ── Zernike ──
            "zernike":     {k: round(v, 4) for k, v in zernike.items()},
            # ── 鏡片溫度 ──
            "lens_temps":  lens_temps,
            "lens_temp_max": round(max(lens_temps.values()), 4),
            # ── 良率 ──
            "yield_prob":  round(yield_prob, 4),
            "pass_fail":   1 if yield_prob > 0.85 else -1,
        }

        self._history.append({k: v for k, v in result.items()
                               if k not in ("cdu_map", "overlay_map")})
        return result

    def get_history(self) -> List[Dict]:
        return list(self._history)

    def get_lens_state(self) -> Dict:
        return {n: {"T": round(s["T"], 4)} for n, s in self._lens_state.items()}

    def get_process_window(self, na: float = DEFAULT_NA) -> Dict:
        """計算目前條件下的製程窗口 (focus range @ ±10% CD tolerance)"""
        cd_target = BOSSUNG["CD0"]
        spec = cd_target * 0.10   # ±10%
        # 解 a*(f-f_best)² = spec → f = f_best ± sqrt(spec/a)
        if BOSSUNG["a_focus"] > 0:
            half_pw = math.sqrt(spec / BOSSUNG["a_focus"])
        else:
            half_pw = 200.0
        return {
            "focus_range_nm": round(2 * half_pw, 1),
            "dose_latitude_pct": round(
                abs(spec / (BOSSUNG["b_dose"] * BOSSUNG["dose_nom"])) * 100, 1),
            "dof_nm": round(WAVELENGTH / (2 * na**2), 1),  # 瑞利 DOF
        }


# ── 模組層級的單例引擎（供 API 使用）──────────────────────────────────────
_engine = LensHeatingEngine()


def get_engine() -> LensHeatingEngine:
    return _engine


# ── 快速測試 ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    eng = LensHeatingEngine()
    print("=== Lens Heating Model — Quick Test ===\n")
    print("模擬 10 片 wafer 連續曝光 (dose=30 mJ/cm^2, focus=0 nm)\n")
    for i in range(10):
        r = eng.expose_wafer(dose=30.0, focus=0.0)
        print(f"  W{r['wafer_no']:02d} | CD={r['cd_mean']:6.2f} nm  "
              f"3σ={r['cd_3sigma']:5.3f}  "
              f"Ov_X={r['overlay_x_3s']:5.3f} nm  "
              f"T_PL1={r['lens_temps']['PL1']:.4f} K  "
              f"drift={r['focus_drift']:+.3f} nm")

    print("\n--- 製程窗口 ---")
    pw = eng.get_process_window()
    print(f"  Focus range : ±{pw['focus_range_nm']/2:.0f} nm  (total {pw['focus_range_nm']} nm)")
    print(f"  Dose latitude: {pw['dose_latitude_pct']:.1f} %")
    print(f"  DOF (Rayleigh): {pw['dof_nm']:.0f} nm")
