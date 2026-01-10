# -*- coding: utf-8 -*-
"""
主動提示學長 (Proactive Mentor)

當故障發生時，AI學長會：
1. 主動說明檢測到的異常
2. 列出可能產生的連鎖問題（使用專業術語）
3. 學員可以追問這些術語的意思

範例：
學長：「檢測到溫度異常！溫度從23°C上升到28°C。
      可能導致：
      - 熱膨脹造成對準偏移
      - wafer overlay shift
      - 光學折射率改變影響曝光品質」

學員：「overlay是什麼？」
學長：「overlay是疊對精度，指的是...」
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime


class ProactiveMentor:
    """主動提示學長 - 偵測異常後主動說明可能問題"""

    def __init__(self, llm_handler=None):
        """
        初始化主動提示學長

        Args:
            llm_handler: LLM處理器（用於生成回答）
        """
        self.llm = llm_handler
        self.last_alert = None  # 最後一次告警
        self.technical_terms = {}  # 記錄提到的專業術語

    def generate_fault_alert(self, fault_info: Dict, current_state: Dict) -> str:
        """
        生成故障告警與可能影響

        Args:
            fault_info: 故障資訊
                {
                    'fault_type': '冷卻流量下降',
                    'root_cause': 'cooling_flow',
                    'severity': 'medium',
                    'scenario_name': 'cooling_system_failure' (可選)
                }
            current_state: 當前設備狀態

        Returns:
            告警訊息（含可能影響和專業術語）
        """
        fault_type = fault_info.get('fault_type', '未知故障')
        root_cause = fault_info.get('root_cause', 'unknown')
        scenario_name = fault_info.get('scenario_name', '')

        # 如果沒有 root_cause，嘗試從 scenario_name 或 current_state 推斷
        if root_cause == 'unknown' or not root_cause:
            root_cause = self._infer_root_cause(scenario_name, current_state)

        # 根據故障類型生成告警
        alert_templates = {
            'cooling_flow': self._generate_cooling_alert,
            'vacuum_leak': self._generate_vacuum_alert,
            'temperature': self._generate_temperature_alert,
            'lens_contamination': self._generate_optical_alert,
            'alignment': self._generate_alignment_alert
        }

        generator = alert_templates.get(root_cause, self._generate_generic_alert)
        alert_message = generator(fault_info, current_state)

        # 記錄這次告警（供後續追問）
        self.last_alert = {
            'fault_type': fault_type,
            'root_cause': root_cause,
            'message': alert_message,
            'timestamp': datetime.now()
        }

        return alert_message

    def _infer_root_cause(self, scenario_name: str, current_state: Dict) -> str:
        """
        從場景名稱或當前狀態推斷根本原因

        Args:
            scenario_name: 場景名稱
            current_state: 當前狀態

        Returns:
            推斷的 root_cause
        """
        # 從場景名稱推斷
        scenario_lower = scenario_name.lower()
        if 'cooling' in scenario_lower or 'flow' in scenario_lower:
            return 'cooling_flow'
        elif 'vacuum' in scenario_lower or 'leak' in scenario_lower:
            return 'vacuum_leak'
        elif 'temp' in scenario_lower or 'thermal' in scenario_lower:
            return 'temperature'
        elif 'lens' in scenario_lower or 'optical' in scenario_lower or 'contamination' in scenario_lower:
            return 'lens_contamination'
        elif 'align' in scenario_lower:
            return 'alignment'

        # 從當前狀態推斷（檢查哪個參數異常）
        cooling_flow = current_state.get('cooling_flow', 5.0)
        vacuum = current_state.get('vacuum_pressure', 1e-6)
        temp = current_state.get('lens_temp', 23.0)
        light = current_state.get('light_intensity', 100.0)
        align_x = current_state.get('alignment_error_x', 0)
        align_y = current_state.get('alignment_error_y', 0)

        # 判斷哪個參數偏離最嚴重
        if abs(cooling_flow - 5.0) > 0.5:  # 冷卻流量異常
            return 'cooling_flow'
        elif vacuum > 2e-6:  # 真空度異常
            return 'vacuum_leak'
        elif abs(temp - 23.0) > 1.0:  # 溫度異常
            return 'temperature'
        elif light < 95.0:  # 光強異常
            return 'lens_contamination'
        elif abs(align_x) > 10 or abs(align_y) > 10:  # 對準異常
            return 'alignment'

        # 都沒有明顯異常，返回 unknown
        return 'unknown'

    def _generate_cooling_alert(self, fault_info: Dict, state: Dict) -> str:
        """生成冷卻系統異常告警"""
        flow = state.get('cooling_flow', 5.0)
        temp = state.get('lens_temp', 23.0)

        alert = f"⚠️ [異常偵測] 冷卻流量異常！\n\n"
        alert += f"📊 當前狀態：\n"
        alert += f"  • 冷卻流量：{flow:.1f} L/min（正常值 5.0 L/min）\n"
        alert += f"  • 鏡頭溫度：{temp:.1f}°C\n\n"

        alert += f"🔍 可能產生的連鎖問題：\n"
        alert += f"  1. 熱膨脹 (thermal expansion) → 機械結構尺寸改變\n"
        alert += f"  2. 對準偏移 (alignment drift) → 影響疊對精度\n"
        alert += f"  3. Wafer overlay shift → CD uniformity 惡化\n"
        alert += f"  4. 光學折射率變化 → 曝光劑量 (dose) 偏移\n\n"

        alert += f"💡 建議：先檢查冷卻系統，再評估熱影響範圍\n"
        alert += f"❓ 有任何不清楚的術語嗎？可以隨時問我！"

        # 記錄提到的專業術語
        self.technical_terms = {
            'thermal expansion': '熱膨脹',
            'alignment drift': '對準偏移',
            'overlay': '疊對精度',
            'overlay shift': 'overlay偏移',
            'CD uniformity': '關鍵尺寸均勻性',
            'dose': '曝光劑量',
            '熱膨脹': 'thermal expansion',
            '對準偏移': 'alignment drift',
            'wafer': '晶圓'
        }

        return alert

    def _generate_vacuum_alert(self, fault_info: Dict, state: Dict) -> str:
        """生成真空系統異常告警"""
        vacuum = state.get('vacuum_pressure', 1e-6)

        alert = f"⚠️ [異常偵測] 真空系統異常！\n\n"
        alert += f"📊 當前狀態：\n"
        alert += f"  • 真空度：{vacuum:.2e} Torr（正常值 1.0e-06 Torr）\n\n"

        alert += f"🔍 可能產生的連鎖問題：\n"
        alert += f"  1. 真空洩漏 (vacuum leak) → 腔體污染\n"
        alert += f"  2. Particle contamination → Defect density ↑\n"
        alert += f"  3. Outgassing → 光學元件表面沉積\n"
        alert += f"  4. 製程壓力不穩 → Critical dimension (CD) 變異\n\n"

        alert += f"💡 建議：立即檢查真空泵浦和密封件\n"
        alert += f"❓ 有任何不清楚的術語嗎？可以隨時問我！"

        self.technical_terms = {
            'vacuum leak': '真空洩漏',
            'particle contamination': '微粒污染',
            'defect density': '缺陷密度',
            'outgassing': '脫氣/放氣',
            'critical dimension': '關鍵尺寸',
            'CD': '關鍵尺寸（Critical Dimension縮寫）',
            '真空洩漏': 'vacuum leak',
            '缺陷': 'defect'
        }

        return alert

    def _generate_temperature_alert(self, fault_info: Dict, state: Dict) -> str:
        """生成溫度異常告警"""
        temp = state.get('lens_temp', 23.0)

        alert = f"⚠️ [異常偵測] 溫度異常！\n\n"
        alert += f"📊 當前狀態：\n"
        alert += f"  • 鏡頭溫度：{temp:.1f}°C（正常值 23.0°C）\n\n"

        alert += f"🔍 可能產生的連鎖問題：\n"
        alert += f"  1. 熱膨脹 (thermal expansion) → Overlay error ↑\n"
        alert += f"  2. 折射率漂移 (refractive index drift) → Focus shift\n"
        alert += f"  3. 光學aberration增加 → Resolution下降\n"
        alert += f"  4. Wafer flatness改變 → Depth of focus不足\n\n"

        alert += f"💡 建議：檢查溫控系統和散熱裝置\n"
        alert += f"❓ 有任何不清楚的術語嗎？可以隨時問我！"

        self.technical_terms = {
            'thermal expansion': '熱膨脹',
            'overlay error': '疊對誤差',
            'refractive index': '折射率',
            'refractive index drift': '折射率漂移',
            'focus shift': '焦點偏移',
            'aberration': '像差',
            'resolution': '解析度',
            'depth of focus': '焦深',
            'DOF': '焦深（Depth of Focus縮寫）',
            '熱膨脹': 'thermal expansion',
            '折射率': 'refractive index',
            '像差': 'aberration'
        }

        return alert

    def _generate_optical_alert(self, fault_info: Dict, state: Dict) -> str:
        """生成光學系統異常告警"""
        intensity = state.get('light_intensity', 100.0)

        alert = f"⚠️ [異常偵測] 光學系統異常！\n\n"
        alert += f"📊 當前狀態：\n"
        alert += f"  • 光學強度：{intensity:.1f}%（正常值 100.0%）\n\n"

        alert += f"🔍 可能產生的連鎖問題：\n"
        alert += f"  1. 鏡頭污染 → Transmittance下降\n"
        alert += f"  2. 曝光劑量不足 → Photoresist顯影不完全\n"
        alert += f"  3. CD bias → Line width變窄\n"
        alert += f"  4. Contrast降低 → Line edge roughness (LER) ↑\n\n"

        alert += f"💡 建議：檢查光源和光學元件清潔度\n"
        alert += f"❓ 有任何不清楚的術語嗎？可以隨時問我！"

        self.technical_terms = {
            'transmittance': '穿透率',
            'photoresist': '光阻',
            'CD bias': 'CD偏移',
            'line width': '線寬',
            'contrast': '對比度',
            'line edge roughness': '線邊緣粗糙度',
            'LER': '線邊緣粗糙度（Line Edge Roughness縮寫）',
            '光阻': 'photoresist',
            '線寬': 'line width'
        }

        return alert

    def _generate_alignment_alert(self, fault_info: Dict, state: Dict) -> str:
        """生成對準系統異常告警"""
        align_x = state.get('alignment_error_x', 0)
        align_y = state.get('alignment_error_y', 0)

        alert = f"⚠️ [異常偵測] 對準系統異常！\n\n"
        alert += f"📊 當前狀態：\n"
        alert += f"  • X軸對準誤差：{align_x:.1f} nm\n"
        alert += f"  • Y軸對準誤差：{align_y:.1f} nm\n\n"

        alert += f"🔍 可能產生的連鎖問題：\n"
        alert += f"  1. Overlay error超規 → Yield loss\n"
        alert += f"  2. Pattern placement error → Device failure\n"
        alert += f"  3. Layer-to-layer misalignment → Short/Open defects\n"
        alert += f"  4. Wafer-to-wafer variation → Process capability ↓\n\n"

        alert += f"💡 建議：重新校正對準系統\n"
        alert += f"❓ 有任何不清楚的術語嗎？可以隨時問我！"

        self.technical_terms = {
            'overlay error': '疊對誤差',
            'yield loss': '良率損失',
            'pattern placement error': '圖案定位誤差',
            'layer-to-layer misalignment': '層間對位偏差',
            'short': '短路',
            'open': '斷路',
            'defect': '缺陷',
            'wafer-to-wafer variation': '片間變異',
            'process capability': '製程能力',
            '良率': 'yield',
            '缺陷': 'defect'
        }

        return alert

    def _generate_generic_alert(self, fault_info: Dict, state: Dict) -> str:
        """生成通用異常告警"""
        fault_type = fault_info.get('fault_type', '未知故障')

        alert = f"⚠️ [異常偵測] 偵測到 {fault_type}！\n\n"
        alert += f"🔍 建議檢查相關參數，評估影響範圍。\n"
        alert += f"❓ 有任何問題嗎？可以隨時問我！"

        return alert

    def answer_followup_question(self, question: str) -> Tuple[bool, str]:
        """
        回答學員的追問（通常是專業術語解釋）

        Args:
            question: 學員的問題

        Returns:
            (is_term_question, answer)
            - is_term_question: 是否是術語解釋問題
            - answer: 回答內容
        """
        # 檢查是否在問專業術語
        question_lower = question.lower().strip()

        # 常見問法
        question_patterns = [
            '是什麼', '是甚麼', 'what is', 'what\'s',
            '意思', '定義', '解釋', 'explain', 'define',
            '的意思', '是什么'
        ]

        is_asking_term = any(pattern in question_lower for pattern in question_patterns)

        if not is_asking_term:
            return False, ""

        # 嘗試匹配提到的術語
        for term, translation in self.technical_terms.items():
            if term.lower() in question_lower:
                return True, self._explain_term(term, translation)

        # 如果沒有匹配到，但確實是在問術語
        # 嘗試用 LLM 回答
        if self.llm:
            return True, self._llm_explain_term(question)
        else:
            return True, "抱歉，這個術語不在我剛才提到的範圍內。可以更具體地問嗎？"

    def _explain_term(self, term: str, translation: str) -> str:
        """
        解釋專業術語（使用預定義模板）

        Args:
            term: 術語
            translation: 翻譯

        Returns:
            解釋內容
        """
        # 預定義的術語解釋
        term_explanations = {
            'thermal expansion': """【熱膨脹 (Thermal Expansion)】

定義：材料受熱時體積增大的物理現象。

原理：溫度升高時，原子振動增強，原子間距變大，導致整體尺寸增加。

半導體應用：
  • CVD製程中，晶圓從室溫加熱到400°C時，直徑可能增加約0.1mm
  • 曝光機的鏡頭和腔體在溫度變化時會膨脹，影響對準精度
  • 不同材料的熱膨脹係數不同，溫度變化會產生應力

實際影響：
  ✗ 晶圓夾持失效
  ✗ 腔體密封洩漏
  ✗ 對準精度下降

新人常見誤解：只有金屬會熱膨脹
正確觀念：矽晶圓、石英腔體都有明顯的熱脹冷縮""",

            'overlay': """【Overlay / 疊對精度】

定義：多層製程中，上層圖案對下層圖案的對準精度。

為什麼重要：
  • 現代IC有50+層結構，每層都要精準對齊
  • Overlay error > 3nm → 可能造成短路或斷路
  • 是影響良率的關鍵指標

測量方式：
  • 用overlay mark（對準標記）測量上下層偏移量
  • X/Y方向分別測量
  • 單位：nm（奈米）

實際案例：
  ✓ Overlay < 2nm：良好
  ⚠️ Overlay 2-5nm：警告
  ✗ Overlay > 5nm：不良

相關術語：
  • Alignment error：對準誤差
  • Registration：套準""",

            'overlay shift': """【Overlay Shift / 疊對偏移】

定義：上層圖案相對下層圖案產生位移。

常見原因：
  1. 熱膨脹 → 晶圓尺寸改變
  2. 對準系統漂移
  3. 製程應力 → 晶圓變形
  4. 機台振動

影響：
  • 金屬層對不準 → 電路短路/斷路
  • Via hole偏移 → 接觸電阻增加
  • Pattern placement error → Device failure

檢測方法：
  • 用SEM測量overlay mark
  • X/Y方向分別檢查
  • 全片分布圖(wafer map)分析""",

            'CD uniformity': """【CD Uniformity / 關鍵尺寸均勻性】

定義：晶圓上不同位置的線寬一致性。

CD (Critical Dimension)：
  • 電路中最小的線寬或孔徑
  • 例如：7nm製程 → 最小線寬約7nm

Uniformity：
  • 全片CD變異 < 3% → 優良
  • CD變異 > 5% → 可能良率問題

影響因素：
  ✗ 曝光劑量不均 → CD變異
  ✗ 溫度分布不均 → CD偏移
  ✗ 光學aberration → 解析度下降

改善方法：
  • 優化曝光劑量
  • 改善溫控均勻性
  • 校正光學系統""",

            'dose': """【Dose / 曝光劑量】

定義：光阻材料接收到的光能量（單位：mJ/cm²）

為什麼重要：
  • 劑量太低 → 光阻顯影不完全 → 圖案殘留
  • 劑量太高 → 過度曝光 → 線寬變窄
  • 需要精確控制在±2%以內

影響因素：
  1. 光源強度
  2. 曝光時間
  3. 鏡頭穿透率
  4. 光阻靈敏度

實際應用：
  • DUV製程：25-30 mJ/cm²
  • EUV製程：15-20 mJ/cm²

調整方式：
  • 改變曝光時間
  • 調整光源功率
  • 補償鏡頭穿透率變化""",

            'vacuum leak': """【Vacuum Leak / 真空洩漏】

定義：真空腔體密封不良，外界空氣滲入。

偵測方法：
  • 真空度無法達到目標值
  • 抽真空時間異常增加
  • 用氦氣偵漏儀定位洩漏點

常見原因：
  1. O-ring老化或損壞
  2. 法蘭密封面刮傷
  3. 閥門密封不良
  4. 腔體本體裂縫

影響：
  ✗ 製程壓力不穩 → CD變異
  ✗ 微粒污染 → Defect ↑
  ✗ 光學元件污染 → Transmittance ↓

處理步驟：
  1. 用氦氣偵漏儀找洩漏點
  2. 檢查O-ring和密封面
  3. 更換損壞零件
  4. 重新抽真空驗證""",

            'photoresist': """【Photoresist / 光阻】

定義：對光敏感的高分子材料，用於轉移圖案。

工作原理：
  1. 塗佈光阻在晶圓上
  2. 曝光（透過光罩）
  3. 顯影（溶解曝光/未曝光區域）
  4. 蝕刻（轉移圖案）
  5. 去光阻

兩大類型：
  • Positive PR：曝光區域可溶解
  • Negative PR：曝光區域硬化

關鍵參數：
  • 靈敏度（dose需求）
  • 解析度（能印多細的線）
  • 對比度（圖案清晰度）

常見問題：
  ✗ 光阻殘留 → Particle
  ✗ 顯影不均 → CD變異
  ✗ 黏附性差 → Pattern剝落"""
        }

        explanation = term_explanations.get(term.lower())

        if explanation:
            return explanation
        else:
            # 簡單的備用解釋
            return f"【{term}】\n\n中文：{translation}\n\n這是半導體製程中的專業術語。如需更詳細的解釋，請告訴我您想了解的具體方面！"

    def _llm_explain_term(self, question: str) -> str:
        """
        使用 LLM 解釋術語

        Args:
            question: 學員的問題

        Returns:
            LLM生成的解釋
        """
        if not self.llm:
            return "抱歉，AI助手目前不可用。"

        system_prompt = """你是半導體製程專家，正在向新人解釋專業術語。

解釋格式：
1. 定義（一句話）
2. 詳細說明（2-3句）
3. 半導體製程中的應用舉例
4. 實際影響或常見問題

語氣：專業但親切，像資深學長在教導"""

        try:
            # 臨時設置系統提示
            original_prompt = self.llm.system_prompt
            self.llm.system_prompt = system_prompt

            answer = self.llm.ask(question, maintain_context=False)

            # 恢復原始提示
            self.llm.system_prompt = original_prompt

            return answer
        except Exception as e:
            return f"抱歉，解釋術語時發生錯誤：{e}"

    def get_mentioned_terms(self) -> List[str]:
        """獲取最近告警中提到的專業術語列表"""
        return list(self.technical_terms.keys())
