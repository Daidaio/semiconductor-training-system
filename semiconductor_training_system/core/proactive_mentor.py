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
        self.pending_followup = None   # {'question', 'term_name', 'answer_keywords', 'correct_explanation'}
        self.student_scores: List[int] = []   # 歷史得分，用來調整難度
        self.difficulty = 'standard'   # 'easy' | 'standard' | 'challenge'

    def reset_session(self):
        """新情境開始時重置本次學習狀態（不影響長期記錄）"""
        self.pending_followup = None
        self.student_scores = []
        self.difficulty = 'standard'
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
        opening_question = "先問你：你覺得冷卻系統出問題，溫度偏高，對曝光製程會有什麼影響？"

        self.pending_followup = {
            'question': opening_question,
            'term_name': '熱膨脹',
            'answer_keywords': ['溫度', '體積', '膨脹', '尺寸', '結構', '漂移', '偏移', '對準', '精度', '熱'],
            'correct_explanation': (
                '溫度升高會造成熱膨脹 (thermal expansion)，'
                '曝光機的鏡頭、晶圓夾具等金屬結構尺寸跟著變，'
                '對準精度就下降，上下層圖案偏移，良率也跟著掉。'
            ),
            'socratic_followup': {
                'challenge': "那你知道，熱膨脹造成的對準偏移，大概是什麼量級？怎麼估算？",
                'standard': "那現在你會先去檢查哪個部件？",
            }
        }

        self.technical_terms = {
            'thermal expansion': '熱膨脹',
            'alignment drift': '對準偏移',
            'overlay': '疊對精度',
            'CD uniformity': '關鍵尺寸均勻性',
            'dose': '曝光劑量',
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

        self.pending_followup = {
            'question': "你知道 outgassing 為什麼對光學鏡面這麼傷嗎？",
            'term_name': 'outgassing',
            'answer_keywords': ['氣體', '揮發', '沉積', '污染', '鏡面', '塗層', '透光', '穿透率', 'transmittance', '分子'],
            'correct_explanation': 'Outgassing 是材料在真空環境下釋放吸附氣體或揮發物的現象，這些分子會沉積在光學鏡面上，形成薄膜，讓穿透率 (transmittance) 下降，進而影響曝光劑量和解析度。'
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
        opening_question = "先問你：你知道鏡組溫度偏高，對曝光製程最直接的影響是什麼嗎？"

        self.pending_followup = {
            'question': opening_question,
            'term_name': '折射率',
            'answer_keywords': ['光速', '密度', '溫度', '介質', '光路', '偏折', '焦點', '波長', '材料', '折射', '解析'],
            'correct_explanation': (
                '鏡組溫度升高，折射率 (refractive index) 就會改變，光路跑掉，'
                '造成焦點偏移 (focus shift)，解析度下降，曝光品質就有問題了。'
                '光學系統對溫度非常敏感，差 1°C 就可能超規。'
            ),
            'socratic_followup': {
                'challenge': "那你知道折射率跟溫度的關係可以用什麼來描述？thermo-optic coefficient 你聽過嗎？",
                'standard': "那現在應該先去看哪個部件的狀態？",
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

        alert = f"光源強度掉了，現在只剩 {intensity:.1f}%，正常要 100%，這樣劑量就不夠。\n\n"
        opening_question = "先問你：光源強度不足，你覺得對後續的曝光製程會有什麼影響？"

        self.pending_followup = {
            'question': opening_question,
            'term_name': '光阻',
            'answer_keywords': ['感光', '顯影', '溶解', '圖案', '曝光', '不足', '殘留', '線寬', '光罩', '劑量', '品質'],
            'correct_explanation': (
                '光源強度不足代表到達光阻 (photoresist) 的劑量不夠，'
                '光阻反應不完全，顯影後有殘留，線寬 (CD) 就偏大，圖案不清晰，最終影響良率。'
            ),
            'socratic_followup': {
                'challenge': "那你能說說，光阻感光的機制是什麼？正型跟負型光阻有什麼不同？",
                'standard': "那現在應該先去檢查哪個部件？",
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

        alert = f"哎，對準系統有點問題，X 軸誤差 {align_x:.1f} nm，Y 軸誤差 {align_y:.1f} nm，超出規格了。\n\n"
        # 引導式開場：先問開放問題，不直接說影響
        opening_question = "先問你個問題：你知道對準系統出問題，會對製程有什麼影響嗎？"

        self.pending_followup = {
            'question': opening_question,
            'term_name': '對準系統',
            'answer_keywords': ['overlay', '疊對', '對準', '層', '對齊', '偏移', '短路', '斷路',
                                '良率', 'yield', '圖案', '精度', '誤差', '電路'],
            'correct_explanation': (
                'Overlay（疊對誤差）是關鍵影響。'
                '上下兩層電路圖案對不準，偏太多就可能讓金屬層短路或 via 斷路，良率直接下來。'
                'ASML 的 DUV 製程一般要求對準誤差 < 3~5 nm，越先進的製程標準越嚴。'
            ),
            # 答得好時的 Socratic 追問（依自適應難度）
            'socratic_followup': {
                'challenge': (
                    "那你知道，overlay 誤差多大才算超規嗎？"
                    "DUV 跟 EUV 的標準一樣嗎？"
                ),
                'standard': (
                    "那你覺得，現在要先做什麼來處理這個對準異常？"
                ),
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

        # 關鍵字得分（修正版：避免正確方向的回答得分過低）
        if keywords:
            matched = sum(1 for kw in keywords if kw.lower() in answer_lower)
            if matched == 0:
                score = 0
            else:
                # 至少1個關鍵字 → 基礎分4，再依命中比例線性加分到10
                score = min(10, 4 + int((matched / len(keywords)) * 7))
        else:
            score = 5

        # 長度調整：太短通常沒在認真回答
        if len(answer) < 6:
            score = max(0, score - 3)
        elif len(answer) > 80:
            score = min(10, score + 1)

        # 明確表示不知道 → 直接給 0，讓系統進入說明模式
        if any(w in answer for w in ['不知道', '不確定', '不太清楚', '不太懂', '沒概念', '不清楚']):
            score = 0

        # 記錄並更新難度
        self.student_scores.append(score)
        self._update_difficulty()

        feedback = self._generate_followup_feedback(score, followup, answer)
        return {'score': score, 'feedback': feedback, 'difficulty': self.difficulty}

    def _update_difficulty(self):
        """根據近期得分調整難度"""
        if len(self.student_scores) < 2:
            return
        recent = self.student_scores[-3:]
        avg = sum(recent) / len(recent)
        if avg >= 7.5:
            self.difficulty = 'challenge'
        elif avg <= 3.0:
            self.difficulty = 'easy'
        else:
            self.difficulty = 'standard'

    def _generate_followup_feedback(self, score: int, followup: Dict, user_answer: str = '') -> str:
        """根據得分和自適應難度生成回饋，優先使用 LLM 個人化回應"""
        term = followup['term_name']
        explanation = followup['correct_explanation']
        question = followup.get('question', '')
        socratic = followup.get('socratic_followup', {})

        # 決定追問：不管分數高低，回答完都問一個確認理解的問題
        next_q = None
        if score >= 8:
            # 答得好：問更深的問題
            next_q = socratic.get('challenge') if self.difficulty == 'challenge' else socratic.get('standard')
        elif score >= 5:
            # 方向對：問操作層面引導
            next_q = socratic.get('standard')
        elif score >= 2:
            # 部分理解：問一個更基礎的確認問題
            next_q = f"我剛說明了 {term} 的概念，你現在能用自己的話說說，它對製程最直接的影響是什麼嗎？"
        else:
            # 完全不知道：說明完後確認有沒有聽懂
            next_q = f"我說明完了，你有沒有大致理解 {term} 是怎麼影響製程的？試著說說看。"

        # is_followup_round 為 True 表示這已是第二輪確認追問，回答後不再追問
        is_final_round = followup.get('is_followup_round', False)
        if next_q and not is_final_round:
            self.pending_followup = {
                'question': next_q,
                'term_name': term,
                'answer_keywords': followup.get('answer_keywords', []),
                'correct_explanation': explanation,
                'socratic_followup': {},
                'is_followup_round': True   # 下一輪回答完就結束追問
            }

        # 優先用 LLM 生成個人化回饋
        if self.llm and user_answer:
            llm_feedback = self._llm_generate_feedback(score, question, user_answer, explanation, next_q, followup)
            if llm_feedback:
                return llm_feedback

        # Fallback: 固定模板
        no_q_ending = "這次訓練結束了，繼續加油！" if is_final_round else "繼續保持，有這個概念在後面故障排查會更順。"
        if score >= 8:
            intro = f"對！{term} 你懂得挺清楚的。"
            outro = f"\n\n{next_q}" if next_q else f"\n\n{no_q_ending}"
        elif score >= 5:
            intro = f"方向對，{term} 主要概念有抓到。"
            outro = f"\n\n補充說明：{explanation}\n\n{next_q}" if next_q else f"\n\n{explanation}\n\n{no_q_ending}"
        elif score >= 2:
            intro = f"有些概念抓到了，但 {term} 還有幾個關鍵點。"
            outro = f"\n\n{explanation}\n\n{next_q}"
        else:
            intro = f"沒關係，{term} 這個概念比較深，我幫你說明一下。"
            outro = f"\n\n{explanation}\n\n{next_q}"

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

        _is_final = (followup or {}).get('is_followup_round', False)
        next_q_str = (
            f"\n在回饋最後，自然地接上這個追問：「{next_q}」"
            if next_q else
            "\n回饋後不需要再追問。" + (
                "給予鼓勵性結語，情境已完整結束。" if _is_final else
                "鼓勵學員繼續去處理故障。"
            )
        )

        dont_know_guide = (
            "學員坦誠說不知道，絕對不能說「有點靠近」或給讚美。"
            "直接用耐心語氣說明正確概念。\n"
        ) if dont_know else ""

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
            f"- 不要逐字重複完整說明，挑最關鍵的點補充\n"
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
