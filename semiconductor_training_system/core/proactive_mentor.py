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

import random
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
        self.pending_followup = None   # {'question', 'term_name', 'answer_keywords', 'correct_explanation'}
        self.student_scores: List[int] = []   # 歷史得分（保留供紀錄用）
        self.difficulty = 'standard'   # 'easy' | 'standard' | 'challenge'
        self.action_score: int = 100   # 從 ActionSession 同步的 0~100 分，決定追問難度

    def reset_session(self):
        """新情境開始時重置本次學習狀態（不影響長期記錄）"""
        self.pending_followup = None
        self.student_scores = []
        self.difficulty = 'standard'
        self.action_score = 100
        self.last_alert = None
        self.technical_terms = {}

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
        elif 'align' in scenario_lower or 'power_fluctuation' in scenario_lower:
            return 'alignment'

        # 從當前狀態推斷（以感測器警告閾值為準）
        cooling_flow = current_state.get('cooling_flow', 5.0)
        vacuum = current_state.get('vacuum_pressure', 1e-6)
        temp = current_state.get('lens_temp', 23.0)
        light = current_state.get('light_intensity', 100.0)
        align_x = current_state.get('alignment_error_x', 0)
        align_y = current_state.get('alignment_error_y', 0)

        # 使用與感測器一致的閾值（lower_is_bad=True: 低於警告值才算異常）
        if cooling_flow < 4.5:  # 冷卻流量低於警告值
            return 'cooling_flow'
        elif vacuum > 2e-6:  # 真空度異常
            return 'vacuum_leak'
        elif temp > 24.0:  # 鏡組溫度高於警告值
            return 'temperature'
        elif light < 92.0:  # 光強低於警告值
            return 'lens_contamination'
        elif abs(align_x) > 10 or abs(align_y) > 10:  # 對準異常
            return 'alignment'

        # 都沒有明顯異常，返回 unknown
        return 'unknown'

    def _generate_cooling_alert(self, fault_info: Dict, state: Dict) -> str:
        """生成冷卻系統異常告警（引導式開場）"""
        flow = state.get('cooling_flow', 5.0)
        temp = state.get('lens_temp', 23.0)

        alert = f"哎，冷卻流量有點怪，現在只有 {flow:.1f} L/min，正常大概要 5.0 左右，鏡頭溫度也飄到 {temp:.1f}°C 了。\n\n"
        opening_question = random.choice([
            "先問你：你覺得冷卻系統出問題，溫度偏高，對曝光製程會有什麼影響？",
            "你知道冷卻水溫度跑掉，對鏡組最直接的衝擊是什麼嗎？",
            "溫度一旦偏高，你覺得哪個製程參數最先出問題？",
        ])

        self.pending_followup = {
            'question': opening_question,
            'term_name': '熱膨脹',
            'answer_keywords': ['溫度', '體積', '膨脹', '尺寸', '結構', '漂移', '偏移', '對準', '精度', '熱'],
            'pass_keyword_groups': [
                ['膨脹', '脹', '變形', '尺寸變', 'expansion', '熱漲', '熱脹'],   # 原理：熱膨脹
                ['對準', '偏移', 'shift', '歪', '漂移', '偏掉', '跑掉', 'alignment', 'overlay'],  # 結果：對準偏移
            ],
            'correct_explanation': (
                '溫度升高會造成熱膨脹 (thermal expansion)，'
                '曝光機的鏡頭、晶圓夾具等金屬結構尺寸跟著變，'
                '對準精度就下降，上下層圖案偏移，良率也跟著掉。'
            ),
            'socratic_followup': {
                'easy':      random.choice([
                    "我剛說到溫度升高金屬會膨脹，機台裡你覺得最怕位移的是哪個部件？",
                    "膨脹會讓零件尺寸改變，你覺得這跟晶圓對準有什麼關係？",
                    "溫度影響結構尺寸，你覺得最先被影響的是曝光的哪個環節？",
                ]),
                'standard':  random.choice([
                    "你知道熱膨脹在曝光機裡大概是什麼量級？溫度差1°C，對對準精度的影響大概有多少nm？",
                    "鏡組材料的熱膨脹係數跟一般金屬比，差很多嗎？為什麼曝光機要特別選低膨脹材料？",
                    "熱膨脹造成的對準偏移，是隨機的還是系統性的誤差？這對補償方法有什麼影響？",
                ]),
                'challenge': random.choice([
                    "那你知道，熱膨脹造成的對準偏移，大概是什麼量級？怎麼估算？",
                    "溫度補償系統是怎麼運作的？它能完全消除熱膨脹的影響嗎？",
                    "熱膨脹係數 (CTE) 跟材料有關，你知道曝光機結構件通常選什麼材料來降低這個影響嗎？",
                ]),
            }
        }

        self.technical_terms = {
            'thermal expansion': '熱膨脹',
            'alignment drift': '對準偏移',
            'overlay': '疊對精度',
            'CD uniformity': '關鍵尺寸均勻性',
            'dose': '曝光dose',
            '熱膨脹': 'thermal expansion',
            '對準偏移': 'alignment drift',
            'wafer': '晶圓'
        }

        return f"{alert}{opening_question}"

    def _generate_vacuum_alert(self, fault_info: Dict, state: Dict) -> str:
        """生成真空系統異常告警"""
        vacuum = state.get('vacuum_pressure', 1e-6)

        alert = f"欸，真空壓力有點偏，現在是 {vacuum:.2e} Torr，正常要維持在 1e-6 左右，差距還挺大的。\n\n"
        alert += f"真空系統不能輕忽，一旦洩漏 (vacuum leak) 微粒就容易跑進去，particle contamination 會讓 defect density 飆上去，光學鏡面沾到 outgassing 的東西更麻煩，很難清。\n\n"
        alert += f"先確認真空泵浦和密封件有沒有問題吧，有不懂的術語隨時問我。"

        _vacuum_opening = random.choice([
            "你知道 outgassing 為什麼對光學鏡面這麼傷嗎？",
            "真空度異常，你覺得最先受影響的是哪個子系統？",
            "你知道真空環境裡的材料為什麼會釋放氣體，又為什麼這很危險嗎？",
        ])
        self.pending_followup = {
            'question': _vacuum_opening,
            'term_name': 'outgassing',
            'answer_keywords': ['氣體', '揮發', '沉積', '污染', '鏡面', '塗層', '透光', '穿透率', 'transmittance', '分子'],
            'pass_keyword_groups': [
                ['沉積', '附著', '薄膜', '積垢', '沾', '污染', 'deposit', '堆積'],          # 原理：分子沉積
                ['穿透率', '透光', '透射', '光量', 'transmittance', '變暗', '透過率'],       # 結果：穿透率下降
            ],
            'correct_explanation': 'Outgassing 是材料在真空環境下釋放吸附氣體或揮發物的現象，這些分子會沉積在光學鏡面上，形成薄膜，讓穿透率 (transmittance) 下降，進而影響曝光dose和解析度。',
            'socratic_followup': {
                'easy':      random.choice([
                    "我說到薄膜讓穿透率下降，這樣到達晶圓的光量會怎樣，對曝光有什麼影響？",
                    "光學鏡面上積了薄膜，你覺得曝光時光線會有什麼問題？",
                    "穿透率下降代表光少了，你覺得這樣 dose 會怎樣？",
                ]),
                'standard':  random.choice([
                    "outgassing 的速率跟材料溫度有什麼關係？為什麼高真空腔體要嚴格控制材料選擇？",
                    "真空洩漏跟 outgassing 都會讓壓力上升，你知道它們在物理上有什麼本質差異嗎？",
                    "為什麼曝光機要維持在 1e-6 Torr 等級的真空？跟大氣壓相比，這個真空度有多難達到？",
                ]),
                'challenge': random.choice([
                    "除了鏡面污染，outgassing 還會影響哪個製程參數？跟 dose uniformity 有關係嗎？",
                    "不同材料的 outgassing 速率不同，你知道光刻系統裡哪些材料的風險最高？",
                    "要預防 outgassing 造成的污染，在材料選擇和設計上有哪些手段？",
                ]),
            }
        }
        alert += f"\n\n{self.pending_followup['question']}"

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
        """生成溫度異常告警（引導式開場）"""
        temp = state.get('lens_temp', 23.0)

        alert = f"剛注意到鏡組溫度跑掉了，現在 {temp:.1f}°C，正常要控在 23°C 附近。\n\n"
        opening_question = random.choice([
            "先問你：你知道鏡組溫度偏高，對曝光製程最直接的影響是什麼嗎？",
            "鏡組溫度跑掉，你覺得光路會發生什麼變化？",
            "溫度影響折射率這件事，你知道對曝光精度有什麼衝擊嗎？",
        ])

        self.pending_followup = {
            'question': opening_question,
            'term_name': '折射率',
            'answer_keywords': ['光速', '密度', '溫度', '介質', '光路', '偏折', '焦點', '波長', '材料', '折射', '解析'],
            'pass_keyword_groups': [
                ['折射', '折射率', '光路', '偏折', 'refractive', '光偏', '光跑掉'],          # 原理：折射率改變
                ['焦點', '焦距', '對焦', 'focus', '散焦', '失焦', '焦跑掉', '焦偏'],        # 結果：焦點偏移
            ],
            'correct_explanation': (
                '鏡組溫度升高，折射率 (refractive index) 就會改變，光路跑掉，'
                '造成焦點偏移 (focus shift)，解析度下降，曝光品質就有問題了。'
                '光學系統對溫度非常敏感，差 1°C 就可能超規。'
            ),
            'socratic_followup': {
                'easy':      random.choice([
                    "我說到焦點跑掉，你覺得晶圓上的圖案會變成什麼樣子？會清楚還是模糊？",
                    "焦點偏了，光阻上的圖案品質會怎樣？",
                    "散焦的話，你覺得 CD 會變大還是變小？",
                ]),
                'standard':  random.choice([
                    "折射率跟溫度的關係大概是什麼量級？溫度差1°C，對 ArF 光源的焦點偏移影響多少？",
                    "為什麼曝光機的溫控要控在 ±0.01°C 等級？比一般實驗室設備嚴格多少倍？",
                    "鏡組溫度變化造成的焦點偏移，跟機械振動造成的焦點偏移，在特性上有什麼不同？",
                ]),
                'challenge': random.choice([
                    "那你知道折射率跟溫度的關係可以用什麼來描述？thermo-optic coefficient 你聽過嗎？",
                    "溫度補償和重新做 focus calibration，在實際操作上你怎麼判斷哪個優先？",
                    "折射率改變對 NA（數值孔徑）和解析度的影響，你能說說它們的關係嗎？",
                ]),
            }
        }

        self.technical_terms = {
            'thermal expansion': '熱膨脹',
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

        return f"{alert}{opening_question}"

    def _generate_optical_alert(self, fault_info: Dict, state: Dict) -> str:
        """生成光學系統異常告警（引導式開場）"""
        intensity = state.get('light_intensity', 100.0)

        alert = f"光源強度掉了，現在只剩 {intensity:.1f}%，正常要 100%，這樣dose就不夠。\n\n"
        opening_question = random.choice([
            "先問你：光源強度不足，你覺得對後續的曝光製程會有什麼影響？",
            "dose 不夠的話，你覺得光阻會發生什麼反應？",
            "光源掉了這麼多，你最擔心哪個製程參數會跑掉？",
        ])

        self.pending_followup = {
            'question': opening_question,
            'term_name': '曝光dose',
            'answer_keywords': ['感光', '顯影', '溶解', '圖案', '曝光', '不足', '殘留', '線寬', 'dose', '品質', '強度'],
            'pass_keyword_groups': [
                ['dose', '曝光量', '光量', '能量', '不足', '偏低', '少了', '劑量'],      # 原理：dose不足
                ['線寬', 'cd', '圖案', '清晰', '殘留', '線條', '尺寸', '良率', '失真'],  # 結果：CD/線寬偏差
            ],
            'correct_explanation': (
                '光源強度不足 → 到達晶圓的曝光dose不夠 → 光阻反應不完全 → '
                '顯影後有殘留，線寬 (CD) 偏大，圖案不清晰，最終影響良率。'
                '光源強度每下降1%，dose就跟著偏低，長期下去 CDU 也會惡化。'
            ),
            'socratic_followup': {
                'easy':      random.choice([
                    "我說到 dose 不夠線寬會偏大，你能說說線寬偏大對元件電氣特性有什麼影響嗎？",
                    "光阻顯影不完全會殘留，你覺得殘留的光阻對後續的蝕刻製程會造成什麼問題？",
                    "dose 偏低的話，你覺得正型和負型光阻各會有什麼不同的反應？",
                ]),
                'standard':  random.choice([
                    "dose margin 和 exposure latitude 這兩個概念，你知道它們怎麼描述製程的容忍度嗎？",
                    "光源強度跟 CDU（關鍵尺寸均勻性）的關係，你能說說是怎麼連結的嗎？",
                    "為什麼曝光機需要定期做 dose calibration？校正不準會導致什麼問題？",
                ]),
                'challenge': random.choice([
                    "那你能說說，光阻感光的化學機制是什麼？正型跟負型光阻在 dose 不足時反應有什麼差別？",
                    "dose margin 和 exposure latitude 有什麼關係？怎麼從製程視窗圖量化它？",
                    "如果光源強度有週期性波動（非固定偏低），對 CDU 的影響跟固定偏低有什麼本質差別？",
                ]),
            }
        }

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

        return f"{alert}{opening_question}"

    def _generate_alignment_alert(self, fault_info: Dict, state: Dict) -> str:
        """生成對準系統異常告警（引導式開場，不直接講答案）"""
        align_x = state.get('alignment_error_x', 0)
        align_y = state.get('alignment_error_y', 0)

        # 單位換算：scenario_engine 存的是 μm，需轉成 nm 顯示
        # 若值在 0 < x < 1.0 範圍，判斷為 μm，乘以 1000 換算成 nm
        if 0 < abs(align_x) < 1.0:
            align_x = round(align_x * 1000, 1)
        if 0 < abs(align_y) < 1.0:
            align_y = round(align_y * 1000, 1)
        # 若感測器數據覆蓋導致值接近零，給合理的對準異常值（nm）
        if abs(align_x) < 0.1 and abs(align_y) < 0.1:
            align_x = round(random.uniform(8.0, 15.0), 1)
            align_y = round(random.uniform(5.0, 11.0), 1)

        alert = f"哎，對準系統有點問題，X 軸誤差 {align_x:.1f} nm，Y 軸誤差 {align_y:.1f} nm，超出規格了。\n\n"
        opening_question = random.choice([
            "先問你個問題：你知道對準系統出問題，會對製程造成什麼影響嗎？",
            "overlay 誤差超規了，你覺得對後續的製程和良率會有什麼問題？",
            "對準系統異常，你覺得最直接的影響會是什麼？",
        ])

        self.pending_followup = {
            'question': opening_question,
            'term_name': '對準系統',
            'answer_keywords': ['overlay', '疊對', '對準', '層', '對齊', '偏移', '短路', '斷路',
                                '良率', 'yield', '圖案', '精度', '誤差', '電路'],
            'pass_keyword_groups': [
                ['偏移', 'shift', '歪', '偏掉', '跑掉', 'overlay', '對不準', '對準誤差', '錯位', '位移'],  # 原理：對準偏移
                ['良率', 'yield', '品質', '短路', '斷路', '壞掉', '出問題', '降低', '變差'],              # 結果：良率下降/電路問題
            ],
            'correct_explanation': (
                'Overlay（疊對誤差）是關鍵影響。'
                '上下兩層電路圖案對不準，偏太多就可能讓金屬層短路或 via 斷路，良率直接下來。'
                'ASML 的 DUV 製程一般要求對準誤差 < 3~5 nm，越先進的製程標準越嚴。'
            ),
            'socratic_followup': {
                'easy':      random.choice([
                    "我說到對準偏移良率會掉，你覺得良率掉是什麼意思？對工廠有什麼實際影響？",
                    "圖案對不準，你覺得電路上會發生什麼問題？",
                    "overlay 誤差太大，你覺得這片晶圓能繼續用嗎？為什麼？",
                ]),
                'standard':  random.choice([
                    "overlay 誤差在多層製程中會累積嗎？你知道每一層的誤差是怎麼疊加的嗎？",
                    "對準標記（alignment mark）的設計跟 overlay 量測精度有什麼關係？為什麼要特別設計？",
                    "系統性 overlay 誤差和隨機性誤差，在分析上有什麼不同的處理方式？",
                ]),
                'challenge': random.choice([
                    "那你知道，overlay 誤差多大才算超規嗎？DUV 跟 EUV 的標準一樣嗎？",
                    "對準誤差的來源有哪些？怎麼區分是 reticle stage 還是 wafer stage 的問題？",
                    "你知道 alignment mark 的設計跟 overlay 量測精度有什麼關係嗎？",
                ]),
            }
        }

        self.technical_terms = {
            'overlay error': '疊對誤差',
            'overlay': '疊對精度',
            'yield loss': '良率損失',
            'pattern placement error': '圖案定位誤差',
            'layer-to-layer misalignment': '層間對位偏差',
            'short': '短路',
            'open': '斷路',
            'defect': '缺陷',
            'wafer-to-wafer variation': '片間變異',
            '良率': 'yield',
            '缺陷': 'defect'
        }

        return f"{alert}{opening_question}"

    def _generate_generic_alert(self, fault_info: Dict, state: Dict) -> str:
        """生成通用異常告警"""
        fault_type = fault_info.get('fault_type', '未知故障')

        alert = f"欸，剛偵測到 {fault_type} 這個異常，先去控制面板看一下相關數值，確認是哪個環節出問題。有什麼看不懂的地方就問我。"

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

    # ── 追問期間的概念詢問處理 ───────────────────────────────────────────────

    def check_clarification_during_followup(self, user_input: str) -> Optional[str]:
        """
        在 pending_followup 等待期間，偵測操作者是否在問一個概念/術語。
        若是，用 LLM 解釋後重新貼上追問，並保持 pending_followup 不變。
        若不是，回傳 None（呼叫端繼續走 evaluate_followup_answer）。
        """
        if not self.pending_followup:
            return None

        q = user_input.strip()
        q_lower = q.lower()

        # 偵測是否是問題句（問法關鍵字）
        clarification_patterns = [
            '是什麼', '是甚麼', '什麼是', '甚麼是', 'what is', "what's",
            '意思', '定義', '解釋', '說明一下', '能解釋', '可以解釋',
            '的意思', '是什么', '啥是', '啥意思',
        ]
        is_question = any(p in q_lower for p in clarification_patterns)
        # 也偵測問號
        if '？' in q or '?' in q:
            is_question = True

        if not is_question:
            return None

        # 先嘗試技術詞典匹配
        explanation = None
        for term, translation in self.technical_terms.items():
            if term.lower() in q_lower:
                explanation = self._explain_term(term, translation)
                break

        # 詞典找不到 → 用 LLM 解釋
        if not explanation:
            if self.llm:
                explanation = self._llm_explain_with_context(q)
            else:
                explanation = "這個問題我先記下，建議你完成反問後再查看相關資料。"

        # 保持 pending_followup 不變，回應末尾重複追問
        pending_q = self.pending_followup['question']
        return f"{explanation}\n\n---\n回到剛才的問題：{pending_q}"

    def _llm_explain_with_context(self, question: str) -> str:
        """用 LLM 解釋操作者在訓練情境中問的概念，語氣口語化"""
        if not self.llm:
            return "抱歉，AI 助手目前不可用。"
        prompt = (
            f"你是半導體設備訓練系統的 AI 學長。\n"
            f"操作者在訓練過程中問了這個問題：「{question}」\n\n"
            f"請用口語、繁體中文，3~4 句以內解釋清楚：\n"
            f"- 先給一句定義\n"
            f"- 舉一個在曝光機或半導體製程中的具體例子\n"
            f"- 說明它為什麼重要\n"
            f"語氣像資深學長在跟新人解釋，不要條列格式，直接說話。"
        )
        try:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(self.llm.ask, prompt, False)
                return future.result(timeout=12) or "這個問題我沒辦法即時回答，先繼續操作吧。"
        except Exception:
            return "這個問題我沒辦法即時回答，先繼續操作吧。"

    # ── 反問評估 ──────────────────────────────────────────────────────────────

    def evaluate_followup_answer(self, answer: str) -> Optional[Dict]:
        """
        評估學員對反問的回答，回傳得分、回饋、新難度。
        呼叫後會清除 pending_followup。
        """
        if not self.pending_followup:
            return None

        followup = self.pending_followup
        self.pending_followup = None

        answer_lower = answer.lower().strip()
        keywords = followup['answer_keywords']

        # ── 無意義回答偵測（亂打、純英文字母、重複字元）────────────
        import re
        is_gibberish = False
        # 純 ASCII 亂碼（a-z、數字、符號，沒有中文）
        if answer and not re.search(r'[\u4e00-\u9fff]', answer):
            is_gibberish = True
        # 字元多樣性極低（< 3 種不同字元且長度 > 3）
        if len(set(answer.replace(' ', ''))) < 3 and len(answer) > 3:
            is_gibberish = True
        # 重複字元（如「啊啊啊」「123123」）
        if len(answer) >= 4 and len(set(answer)) <= 2:
            is_gibberish = True

        if is_gibberish:
            score = 0
        else:
            # ── 廣義關鍵字得分（基礎分）────────────────────────────────
            if keywords:
                matched = sum(1 for kw in keywords
                              if len(kw) >= 2 and kw.lower() in answer_lower)
                if matched == 0:
                    score = 0
                else:
                    score = min(10, 4 + int((matched / len(keywords)) * 7))
            else:
                score = 5

            # ── 核心概念群組判斷（每群組任一同義詞符合即算該概念答到）──────
            # pass_keyword_groups 每個子列表是一個核心概念的同義詞群
            # 全部群組都答到 → 算過（score ≥ 7）；答到一半 → 部分保底
            pass_groups = followup.get('pass_keyword_groups', [])
            if pass_groups:
                matched_groups = sum(
                    1 for group in pass_groups
                    if any(len(kw) >= 2 and kw.lower() in answer_lower for kw in group)
                )
                if matched_groups >= len(pass_groups):
                    score = max(score, 7)   # 所有核心概念都答到 → 算過
                elif matched_groups >= 1:
                    score = max(score, 3)   # 答到部分概念 → 部分分數保底

            # 長度調整
            if len(answer) < 8:
                score = max(0, score - 4)   # 更嚴格的短文懲罰
            elif len(answer) > 80:
                score = min(10, score + 1)

        # 明確表示不知道 → 直接給 0
        if any(w in answer for w in ['不知道', '不確定', '不太清楚', '不太懂', '沒概念', '不清楚']):
            score = 0

        # 記錄並更新難度
        self.student_scores.append(score)
        self._update_difficulty()

        # 計算加/扣回 100 分制的分數
        # 全部核心概念答到（≥7）→ +5；答到部分（3~6）→ +2；幾乎答不到（0~2）→ -3
        if score >= 7:
            score_bonus = 5
        elif score >= 3:
            score_bonus = 2
        else:
            score_bonus = -3   # 答錯/亂打 → 扣 3 分

        feedback = self._generate_followup_feedback(score, followup, answer)
        return {'score': score, 'feedback': feedback, 'difficulty': self.difficulty,
                'score_bonus': score_bonus}

    def _update_difficulty(self):
        """依 ActionSession 0~100 分決定追問難度
        >85  → challenge（挑戰模式）
        64~85 → standard （標準模式）
        <64  → easy    （引導模式）
        """
        score = self.action_score
        if score > 85:
            self.difficulty = 'challenge'
        elif score >= 64:
            self.difficulty = 'standard'
        else:
            self.difficulty = 'easy'

    def _generate_followup_feedback(self, score: int, followup: Dict, user_answer: str = '') -> str:
        """根據得分和自適應難度生成回饋，優先使用 LLM 個人化回應"""
        term = followup['term_name']
        explanation = followup['correct_explanation']
        question = followup.get('question', '')
        socratic = followup.get('socratic_followup', {})

        # is_followup_round 為 True → 這已是第二輪（最後一輪），回答後不再追問
        is_final_round = followup.get('is_followup_round', False)

        # 決定追問：最終輪直接跳過，讓 next_q=None，告知學員去操作
        next_q = None
        if not is_final_round:
            if score >= 8:
                # 答得好：依難度等級給對應深度的追問
                if self.difficulty == 'challenge':
                    next_q = socratic.get('challenge') or socratic.get('standard')
                elif self.difficulty == 'easy':
                    next_q = socratic.get('easy') or socratic.get('standard')
                else:
                    next_q = socratic.get('standard')
            elif score >= 5:
                # 方向對：easy 給引導式問題，其餘給 standard
                if self.difficulty == 'easy':
                    next_q = socratic.get('easy') or socratic.get('standard')
                else:
                    next_q = socratic.get('standard')
            elif score >= 2:
                # 部分理解：問一個更基礎的確認問題
                next_q = f"我剛說明了 {term} 的概念，你現在能用自己的話說說，它對製程最直接的影響是什麼嗎？"
            else:
                # 完全不知道：說明完後確認有沒有聽懂
                next_q = f"我說明完了，你有沒有大致理解 {term} 是怎麼影響製程的？試著說說看。"

        if next_q:
            # 設定第二輪（最終輪）追問：理論深化，不再加新問題
            # 保留原始 correct_explanation，讓第二輪仍能給出完整正確答案
            self.pending_followup = {
                'question': next_q,
                'term_name': term,
                'answer_keywords': [],        # 理論延伸問題用 LLM 評估，不固定關鍵字
                'pass_keyword_groups': [],
                'correct_explanation': explanation,  # ← 帶入原始說明，不換成空泛通用文字
                'socratic_followup': {},
                'is_followup_round': True,    # 這是最後一輪，回答後結束追問
                'is_action_question': False,  # 第二輪仍是理論問題
            }

        # 優先用 LLM 生成個人化回饋
        if self.llm and user_answer:
            llm_feedback = self._llm_generate_feedback(score, question, user_answer, explanation, next_q, followup)
            if llm_feedback:
                return llm_feedback

        # Fallback: 固定模板
        is_closing = followup.get('is_closing_followup', False)
        if is_final_round:
            no_q_ending = "好，概念理解到這邊，去實際操作排除故障吧！靠近部件按 E 開始。"
        elif is_closing:
            no_q_ending = "這次訓練結束了，繼續加油！"
        else:
            no_q_ending = "繼續保持，有這個概念在後面故障排查會更順。"

        # 第二輪（is_final_round）不重複完整說明，只給要點確認
        if is_final_round:
            if score >= 5:
                return f"對，核心有抓到了。{no_q_ending}"
            else:
                # 從 explanation 取第一句作為要點，不重複全段
                key_point = explanation.split('。')[0] + '。' if '。' in explanation else explanation[:60]
                return f"記住這個重點：{key_point}\n\n{no_q_ending}"

        if score >= 8:
            intro = f"對！{term} 你懂得挺清楚的。"
            outro = f"\n\n完整說明：{explanation}\n\n{next_q}" if next_q else f"\n\n完整說明：{explanation}\n\n{no_q_ending}"
        elif score >= 5:
            intro = f"方向對，{term} 主要概念有抓到。"
            outro = f"\n\n補充說明：{explanation}\n\n{next_q}" if next_q else f"\n\n{explanation}\n\n{no_q_ending}"
        elif score >= 2:
            intro = f"有些概念抓到了，但 {term} 還有幾個關鍵點。"
            outro = f"\n\n{explanation}\n\n{next_q}" if next_q else f"\n\n{explanation}\n\n{no_q_ending}"
        else:
            intro = f"沒關係，{term} 這個概念比較深，我幫你說明一下。"
            outro = f"\n\n{explanation}\n\n{next_q}" if next_q else f"\n\n{explanation}\n\n{no_q_ending}"

        return f"{intro}{outro}"

    def _llm_generate_feedback(self, score: int, question: str, user_answer: str,
                                correct_explanation: str, next_q: Optional[str],
                                followup: Optional[Dict] = None) -> Optional[str]:
        """使用 LLM 生成針對學員具體回答的個人化回饋"""
        if not self.llm:
            return None

        difficulty_guide = {
            'challenge': '學員理解不錯，可以用更深的角度挑戰他，不要直接把答案全給出來。',
            'standard':  '補充學員沒說到的重點，語氣像資深學長在指導。',
            'easy':      '用鼓勵語氣耐心解釋，給完整說明，讓學員建立信心。',
        }.get(self.difficulty, '給予適當引導。')

        score_label = (
            '答得很好' if score >= 8 else
            '方向大致對，但還不夠完整' if score >= 5 else
            '有些靠近，但還有重要概念沒提到' if score >= 2 else
            '完全不清楚，需要從頭說明'
        )

        # 明確不知道時的額外指示
        dont_know = any(w in user_answer for w in ['不知道', '不確定', '不太清楚', '不太懂', '沒概念', '不清楚'])

        _is_closing = (followup or {}).get('is_closing_followup', False)
        _is_final_round = (followup or {}).get('is_followup_round', False)
        if next_q:
            next_q_str = f"\n在回饋最後，自然地接上這個追問：「{next_q}」"
        elif _is_closing:
            next_q_str = "\n回饋後不需要再追問。給予鼓勵性結語，情境已完整結束，不要說繼續操作之類的話。"
        elif _is_final_round:
            if dont_know:
                next_q_str = (
                    "\n回饋後不需要再追問。"
                    "學員不清楚這個概念，必須在回饋中先把正確說明講完（原理+製程影響），"
                    "最後才用1句話叫學員去靠近部件按 E 實際操作。"
                )
            else:
                next_q_str = "\n回饋後不需要再追問。結尾請用1句話告訴學員：概念討論到此，現在去靠近部件按 E 開始實際操作排除故障。"
        else:
            next_q_str = "\n回饋後不需要再追問。鼓勵學員繼續去處理故障。"

        if dont_know and _is_final_round:
            dont_know_guide = (
                "學員兩次都說不知道。絕對不能誇讚或說「有點靠近」。"
                "必須先用2~3句話完整說明正確概念（原理＋對製程的影響），"
                "然後才用1句話告訴學員去操作。正確說明就在 correct_explanation 裡，直接引用重點即可。\n"
            )
        elif dont_know:
            dont_know_guide = (
                "學員坦誠說不知道，絕對不能說「有點靠近」或給讚美。"
                "直接用耐心語氣說明正確概念。\n"
            )
        else:
            dont_know_guide = ""

        # 行動型追問（is_action_question）用不同 prompt，避免重複概念解釋
        is_action_q = (followup or {}).get('is_action_question', False)
        if is_action_q:
            prompt = (
                f"你是半導體設備訓練系統的 AI 學長，正在針對操作步驟進行追問。\n\n"
                f"你剛才問學員：「{question}」\n"
                f"學員的回答：「{user_answer}」\n\n"
                f"請生成簡短的學長回饋（繁體中文，口語，2-3句以內）：\n"
                f"- 如果學員說了合理的處理步驟或方向（例如確認某子系統、執行校正、靠近某部件等），給予肯定\n"
                f"- 如果答案太模糊（例如只說「不知道」），給出一個具體行動方向的提示\n"
                f"- 絕對不要重複前面已經解釋過的概念，直接聚焦在這個行動問題上\n"
                f"- 結束時鼓勵學員繼續去實際操作\n"
                f"{next_q_str}"
            )
        elif _is_final_round:
            # 第二輪（最終輪）：前一輪已給完整說明，這裡只給要點確認，不重複整段說明
            prompt = (
                f"你是半導體設備訓練系統的 AI 學長，正在進行第二輪（最終輪）概念確認。\n\n"
                f"上一輪你已經完整說明了 {term} 的概念。\n"
                f"你剛才問學員：「{question}」\n"
                f"學員的回答：「{user_answer}」\n"
                f"評估結果：{score_label}（{score}/10）\n\n"
                f"重要提醒：上一輪已完整解釋過了，這裡絕對不要再完整重複一次說明。\n"
                f"請生成簡短的學長確認回饋（繁體中文，口語，2~3句以內）：\n"
                f"- {dont_know_guide}"
                f"- 根據學員回答，用1句話確認或糾正他的理解\n"
                f"- 如果學員已理解，肯定他並收尾；如果還不清楚，只給1句核心要點（不展開）\n"
                f"{next_q_str}"
            )
        else:
            prompt = (
                f"你是半導體設備訓練系統的 AI 學長，正在對學員的回答給予口語化回饋。\n\n"
                f"你剛才問學員：「{question}」\n"
                f"學員的回答：「{user_answer}」\n"
                f"評估結果：{score_label}（{score}/10）\n\n"
                f"正確的完整說明：{correct_explanation}\n\n"
                f"請生成自然的學長回饋（繁體中文，口語，3-4句以內）：\n"
                f"- {dont_know_guide}"
                f"- 先針對學員的具體回答點評（肯定對的部分，指出缺漏）\n"
                f"- {difficulty_guide}\n"
                f"- 最後一定要用1~2句話給出正確說明重點（原理＋結果），讓學員確認答案\n"
                f"{next_q_str}"
            )

        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(self.llm.ask, prompt, False)
                return future.result(timeout=20)  # 超過 20 秒就退回模板，不阻塞 UI
        except Exception as e:
            print(f"[ProactiveMentor] LLM feedback error/timeout: {e}")
            return None

    # ── 術語解釋 ──────────────────────────────────────────────────────────────

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
  ✗ 曝光dose不均 → CD變異
  ✗ 溫度分布不均 → CD偏移
  ✗ 光學aberration → 解析度下降

改善方法：
  • 優化曝光dose
  • 改善溫控均勻性
  • 校正光學系統""",

            'dose': """【Dose / 曝光dose】

定義：光阻材料接收到的光能量（單位：mJ/cm²）

為什麼重要：
  • dose太低 → 光阻顯影不完全 → 圖案殘留
  • dose太高 → 過度曝光 → 線寬變窄
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
