# -*- coding: utf-8 -*-
"""
理論知識問答助手 - 基於 LLM 的蘇格拉底式教學
整合到故障診斷訓練系統中
"""

import time
from typing import Dict, Optional, List
from datetime import datetime


class TrainingAssistant:
    """
    新人訓練問答助手

    功能：
    1. 回答理論問題
    2. 生成反問問題（蘇格拉底式）
    3. 評估新人回答
    4. 追蹤學習進度
    """

    def __init__(self, llm_handler):
        """
        初始化問答助手

        Args:
            llm_handler: LLM 處理器（使用現有的 nlu_handler）
        """
        self.llm = llm_handler

        # 訓練統計
        self.stats = {
            'questions_asked': 0,
            'answers_given': 0,
            'theory_questions': 0,
            'follow_ups': 0,
            'evaluations': 0,
            'session_start': time.time(),
            'knowledge_score': 0.0
        }

        # 對話歷史（用於上下文）
        self.conversation_history: List[Dict] = []

        # 快取判斷結果（避免重複判斷相同問題）
        self.question_type_cache: Dict[str, bool] = {}

    def generate_answer(self, question: str, context: str = None) -> Dict:
        """
        回答新人的理論問題

        Args:
            question: 新人的問題
            context: 可選的上下文（例如當前故障場景）

        Returns:
            {
                'answer': 回答內容,
                'generation_time': 生成時間,
                'mode': 'theory' 或 'diagnostic'
            }
        """
        start_time = time.time()

        # 構建 prompt
        system_prompt = """你是一位經驗豐富的半導體製程專家和設備維護工程師，正在培訓新進工程師。

【回答原則】
1. **只回答半導體製程、設備、故障診斷相關的問題**
2. 先用一句話說明核心概念或定義
3. 舉半導體製程中的實際例子（如：CVD、蝕刻、黃光製程等）
4. 如果適用，指出新人常見的誤解
5. 控制在 3-5 句話內，簡潔明瞭

【回答範例】
Q: 什麼是熱膨脹？
A: 熱膨脹是指材料受熱時體積增大的物理現象，主要原因是溫度升高時原子振動增強、間距變大。在半導體製程中，晶圓和腔體在加熱時都會膨脹，例如 CVD 製程從室溫加熱到 400°C 時，矽晶圓直徑可能增加約 0.1mm。如果設備設計不考慮熱膨脹，可能導致晶圓夾持失效或腔體密封洩漏。新人常誤以為只有金屬會熱膨脹，其實矽晶圓、石英腔體都會有明顯的熱脹冷縮。

【語氣】用資深學長的口吻，專業但親切，像在現場教導一樣。"""

        if context:
            user_prompt = f"""當前情境：{context}

新人問題：{question}

請回答："""
        else:
            user_prompt = f"""新人問題：{question}

請回答："""

        # 使用現有的 LLM handler (LocalMentorBot 使用 ask 方法)
        # 臨時設置系統提示
        original_prompt = self.llm.system_prompt
        self.llm.system_prompt = system_prompt

        answer = self.llm.ask(user_prompt, maintain_context=False)

        # 恢復原始提示
        self.llm.system_prompt = original_prompt

        gen_time = time.time() - start_time

        # 更新統計
        self.stats['answers_given'] += 1
        self.stats['theory_questions'] += 1

        # 記錄對話
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'type': 'question',
            'content': question,
            'context': context
        })

        self.conversation_history.append({
            'timestamp': datetime.now(),
            'type': 'answer',
            'content': answer
        })

        return {
            'answer': answer,
            'generation_time': gen_time,
            'mode': 'theory'
        }

    def generate_follow_up(self, question: str, answer: str,
                          scenario_context: str = None) -> str:
        """
        生成反問問題（蘇格拉底式）

        Args:
            question: 原始問題
            answer: 系統的回答
            scenario_context: 當前場景上下文

        Returns:
            反問問題
        """
        system_prompt = """你是半導體製程培訓導師，剛回答了新人的理論問題。
現在要反問一個問題來檢驗他們是否真正理解這個概念。

【反問原則】
1. 問題要能檢驗**核心概念的理解**，而非記憶
2. 難度適中：不要問太細節的數值，但要問因果關係
3. 最好能連結到**實際製程應用或故障診斷**
4. 只問一個問題，一句話內完成

【反問範例】
剛才解釋了「熱膨脹」→ 反問：「那你覺得如果 CVD 腔體溫度突然升高 50°C，可能會對製程造成什麼影響？」
剛才解釋了「真空度」→ 反問：「如果真空泵浦效率下降，你會先檢查哪個參數來確認？」"""

        if scenario_context:
            user_prompt = f"""剛才的問答：
Q: {question}
A: {answer}

當前場景：{scenario_context}

請生成一個反問問題，結合場景檢驗理解："""
        else:
            user_prompt = f"""剛才的問答：
Q: {question}
A: {answer}

請生成一個反問問題來檢驗理解："""

        # 使用 LLM (臨時設置系統提示)
        original_prompt = self.llm.system_prompt
        self.llm.system_prompt = system_prompt

        follow_up = self.llm.ask(user_prompt, maintain_context=False)

        # 恢復原始提示
        self.llm.system_prompt = original_prompt

        # 更新統計
        self.stats['questions_asked'] += 1
        self.stats['follow_ups'] += 1

        # 記錄對話
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'type': 'follow_up',
            'content': follow_up
        })

        return follow_up.strip()

    def evaluate_response(self, follow_up_q: str, trainee_answer: str) -> Dict:
        """
        評估新人的回答

        Args:
            follow_up_q: 反問的問題
            trainee_answer: 新人的回答

        Returns:
            {
                'score': 分數 (0-10),
                'feedback': 評估反饋,
                'understanding_level': 理解程度 ('excellent'/'good'/'fair'/'poor')
            }
        """
        if not trainee_answer or len(trainee_answer.strip()) < 5:
            return {
                'score': 0,
                'feedback': '回答太簡短，請提供更詳細的說明。',
                'understanding_level': 'poor'
            }

        system_prompt = """你是半導體製程培訓導師，需要評估新人對理論概念的理解程度。

【評分標準】
9-10分：理解透徹，能舉一反三，並連結到實際製程應用
7-8分：理解正確核心概念，表達清楚，有具體例子
5-6分：基本理解概念，但遺漏關鍵點或例子不夠貼切
3-4分：部分理解，有明顯概念錯誤或混淆
0-2分：完全未理解或答非所問

【回覆格式】
必須使用「分數|評語|建議回答」格式（用 | 分隔三部分），例如：
8|你正確理解了熱膨脹對晶圓的影響，也提到了腔體密封問題。建議可以進一步思考溫度變化速率的影響。|完整回答應包含：溫度升高會導致腔體和晶圓同時膨脹，若膨脹係數不同會產生應力，可能導致晶圓變形或夾持失效，進而影響曝光精度。

請提供：1) 分數 2) 簡短評估（2-3句話）3) 建議的完整回答（供學員參考）"""

        user_prompt = f"""問題：{follow_up_q}

新人回答：{trainee_answer}

請評估（格式：分數|評語|建議回答）："""

        # 使用 LLM (臨時設置系統提示)
        original_prompt = self.llm.system_prompt
        self.llm.system_prompt = system_prompt

        evaluation = self.llm.ask(user_prompt, maintain_context=False)

        # 恢復原始提示
        self.llm.system_prompt = original_prompt

        # 解析分數、評語、建議回答
        suggested_answer = None
        try:
            if '|' in evaluation:
                parts = evaluation.split('|')
                if len(parts) >= 3:
                    # 有建議回答
                    score_str = parts[0].strip()
                    feedback = parts[1].strip()
                    suggested_answer = parts[2].strip()
                    score = float(score_str)
                elif len(parts) == 2:
                    # 只有分數和評語
                    score_str = parts[0].strip()
                    feedback = parts[1].strip()
                    score = float(score_str)
                else:
                    score = 5.0
                    feedback = evaluation
            else:
                # 簡單評分（根據回答長度和關鍵字）
                score = min(10, len(trainee_answer.split()) / 3)
                feedback = evaluation
        except:
            score = 5.0
            feedback = evaluation

        # 判斷理解程度
        if score >= 9:
            understanding_level = 'excellent'
        elif score >= 7:
            understanding_level = 'good'
        elif score >= 5:
            understanding_level = 'fair'
        else:
            understanding_level = 'poor'

        # 更新統計
        self.stats['evaluations'] += 1
        self.stats['knowledge_score'] = (
            self.stats['knowledge_score'] * 0.7 + score * 0.3
        )

        # 記錄對話
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'type': 'trainee_answer',
            'content': trainee_answer
        })

        self.conversation_history.append({
            'timestamp': datetime.now(),
            'type': 'evaluation',
            'content': feedback,
            'score': score
        })

        result = {
            'score': score,
            'feedback': feedback.strip(),
            'understanding_level': understanding_level
        }

        # 加入建議回答（如果有的話）
        if suggested_answer:
            result['suggested_answer'] = suggested_answer

        return result

    def generate_scenario_reflection(self, scenario_summary: Dict) -> str:
        """
        場景結束後生成反思問題

        Args:
            scenario_summary: 場景摘要
                {
                    'fault_type': 故障類型,
                    'actions_taken': 採取的行動,
                    'time_taken': 用時,
                    'mistakes': 錯誤次數
                }

        Returns:
            反思問題
        """
        system_prompt = """你是半導體製程培訓導師，學員剛完成一個故障診斷場景。
請生成一個反思問題，幫助他們從實作經驗中提煉理論知識。

【反思問題原則】
1. 針對場景中的**關鍵決策點或錯誤**
2. 引導思考「為什麼」和「如果...會怎樣」（因果關係）
3. 鼓勵反思改進空間和預防措施
4. 連結理論知識與實際操作
5. 一句話內完成

【反思問題範例】
場景：溫度異常，學員先檢查了壓力 → 反思：「為什麼溫度異常時，先檢查加熱器比先檢查壓力更有效？」
場景：真空度下降，學員多次嘗試錯誤 → 反思：「如果一開始就檢查真空計校正狀態，能節省多少診斷時間？」"""

        user_prompt = f"""場景摘要：
- 故障類型：{scenario_summary.get('fault_type', '未知')}
- 處理行動：{scenario_summary.get('actions_taken', '無')}
- 用時：{scenario_summary.get('time_taken', 0)} 秒
- 錯誤次數：{scenario_summary.get('mistakes', 0)}

請生成反思問題："""

        # 使用 LLM (臨時設置系統提示)
        original_prompt = self.llm.system_prompt
        self.llm.system_prompt = system_prompt

        reflection = self.llm.ask(user_prompt, maintain_context=False)

        # 恢復原始提示
        self.llm.system_prompt = original_prompt

        return reflection.strip()

    def is_theory_question(self, user_input: str) -> bool:
        """
        使用 LLM 判斷是否為理論問題（智能判斷 + 快取優化）

        Args:
            user_input: 使用者輸入

        Returns:
            是否為理論問題
        """
        # 先檢查快取
        if user_input in self.question_type_cache:
            return self.question_type_cache[user_input]

        # 快速關鍵字預判（減少 LLM 呼叫）
        theory_keywords = [
            '什麼是', '為什麼', '原理', '如何', '怎麼',
            '差異', '區別', '比較', '定義', '解釋',
            '是什麼', '為何', '原因', '機制', '作用'
        ]

        action_keywords = [
            '檢查', '測試', '調整', '更換', '重啟',
            '停機', '開始', '確認', '修復', '處理'
        ]

        # 明確的診斷動作（不含理論關鍵字） → 直接判定
        has_theory_kw = any(kw in user_input for kw in theory_keywords)
        has_action_kw = any(kw in user_input for kw in action_keywords)

        if has_action_kw and not has_theory_kw:
            # 純診斷動作，無需 LLM 判斷
            self.question_type_cache[user_input] = False
            return False

        if has_theory_kw and not has_action_kw:
            # 純理論問題，無需 LLM 判斷
            self.question_type_cache[user_input] = True
            return True

        # 混合型問題 → 使用 LLM 精確判斷
        system_prompt = """分類器：判斷是「理論問題」還是「診斷動作」。

理論問題 = 詢問概念/原理/原因
診斷動作 = 執行具體操作

只回答 YES 或 NO：
YES = 理論問題
NO = 診斷動作"""

        user_prompt = f"「{user_input}」是理論問題嗎？"

        # 使用 LLM 判斷
        original_prompt = self.llm.system_prompt
        self.llm.system_prompt = system_prompt

        try:
            response = self.llm.ask(user_prompt, maintain_context=False).strip().upper()
            self.llm.system_prompt = original_prompt

            result = 'YES' in response or '是' in response
            self.question_type_cache[user_input] = result
            return result
        except:
            # LLM 出錯 → 回退到關鍵字
            self.llm.system_prompt = original_prompt
            result = has_theory_kw
            self.question_type_cache[user_input] = result
            return result

    def get_stats(self) -> Dict:
        """
        獲取訓練統計

        Returns:
            統計資訊
        """
        session_duration = time.time() - self.stats['session_start']
        minutes = int(session_duration / 60)

        return {
            'session_duration': f"{minutes} 分鐘",
            'theory_questions': self.stats['theory_questions'],
            'follow_ups': self.stats['follow_ups'],
            'evaluations': self.stats['evaluations'],
            'knowledge_score': round(self.stats['knowledge_score'], 1),
            'total_interactions': len(self.conversation_history)
        }

    def reset_stats(self):
        """重置統計"""
        self.stats = {
            'questions_asked': 0,
            'answers_given': 0,
            'theory_questions': 0,
            'follow_ups': 0,
            'evaluations': 0,
            'session_start': time.time(),
            'knowledge_score': 0.0
        }
        self.conversation_history = []
