# -*- coding: utf-8 -*-
"""
自適應教學策略 - 根據學員回答品質動態調整教學方式

類似於心理診斷 AI 根據患者回答調整診斷策略，
本系統根據學員的理解程度調整：
1. 問題難度
2. 反饋詳細度
3. 提示強度
4. 引導方式
"""

from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class UnderstandingLevel(Enum):
    """理解程度等級"""
    EXCELLENT = "excellent"  # 9-10分：理解透徹
    GOOD = "good"            # 7-8分：理解良好
    FAIR = "fair"            # 5-6分：基本理解
    POOR = "poor"            # 3-4分：部分理解
    VERY_POOR = "very_poor"  # 0-2分：完全不理解


class TeachingMode(Enum):
    """教學模式"""
    CHALLENGE = "challenge"          # 挑戰模式：給高手更難的問題
    STANDARD = "standard"            # 標準模式：正常引導
    SCAFFOLDING = "scaffolding"      # 鷹架模式：分解步驟、多提示
    REMEDIAL = "remedial"            # 補救模式：回到基礎概念


class KnowledgeTracker:
    """知識點追蹤器 - 記錄學員在各主題的表現"""

    def __init__(self):
        """初始化知識追蹤器"""
        # 半導體製程核心主題分類
        self.topic_categories = {
            'thermal': ['熱膨脹', '溫度', '冷卻', '加熱', '散熱'],
            'vacuum': ['真空', '壓力', '真空度', '泵浦', '洩漏'],
            'optical': ['光學', '對準', '曝光', '光強', '折射'],
            'mechanical': ['機械', '定位', '夾持', '振動', '磨損'],
            'chemical': ['化學', 'CVD', '蝕刻', '沉積', '清洗'],
            'electrical': ['電氣', '電源', '電壓', '電流', '接地']
        }

        # 記錄每個主題的得分歷史
        self.topic_scores: Dict[str, List[float]] = {
            topic: [] for topic in self.topic_categories.keys()
        }

        # 記錄每個主題的最後測試時間
        self.last_tested: Dict[str, Optional[datetime]] = {
            topic: None for topic in self.topic_categories.keys()
        }

        # 錯誤模式追蹤
        self.common_mistakes: List[Dict] = []

    def classify_topic(self, question: str, answer: str) -> str:
        """
        根據問題和答案內容分類主題

        Args:
            question: 問題內容
            answer: 系統回答

        Returns:
            主題類別 (thermal/vacuum/optical/...)
        """
        text = (question + " " + answer).lower()

        # 計算每個主題的關鍵字匹配度
        topic_scores = {}
        for topic, keywords in self.topic_categories.items():
            score = sum(1 for kw in keywords if kw in text)
            topic_scores[topic] = score

        # 返回匹配度最高的主題
        if max(topic_scores.values()) > 0:
            return max(topic_scores, key=topic_scores.get)
        else:
            return 'general'  # 未分類

    def update_topic_score(self, topic: str, score: float):
        """
        更新主題得分

        Args:
            topic: 主題類別
            score: 得分 (0-10)
        """
        if topic in self.topic_scores:
            self.topic_scores[topic].append(score)
            self.last_tested[topic] = datetime.now()

    def get_topic_performance(self, topic: str) -> Dict:
        """
        獲取主題表現統計

        Args:
            topic: 主題類別

        Returns:
            {
                'avg_score': 平均分,
                'attempts': 嘗試次數,
                'trend': 趨勢 (improving/stable/declining),
                'mastery_level': 掌握程度
            }
        """
        scores = self.topic_scores.get(topic, [])

        if not scores:
            return {
                'avg_score': 0,
                'attempts': 0,
                'trend': 'unknown',
                'mastery_level': 'untested'
            }

        avg_score = sum(scores) / len(scores)

        # 判斷趨勢（比較最近 3 次和前面的）
        if len(scores) >= 6:
            recent_avg = sum(scores[-3:]) / 3
            earlier_avg = sum(scores[-6:-3]) / 3
            if recent_avg > earlier_avg + 1:
                trend = 'improving'
            elif recent_avg < earlier_avg - 1:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'

        # 判斷掌握程度
        if avg_score >= 8:
            mastery = 'mastered'
        elif avg_score >= 6:
            mastery = 'proficient'
        elif avg_score >= 4:
            mastery = 'developing'
        else:
            mastery = 'struggling'

        return {
            'avg_score': round(avg_score, 1),
            'attempts': len(scores),
            'trend': trend,
            'mastery_level': mastery
        }

    def identify_weak_topics(self, threshold: float = 5.0) -> List[str]:
        """
        識別弱點主題

        Args:
            threshold: 分數閾值，低於此分數視為弱點

        Returns:
            弱點主題列表
        """
        weak_topics = []

        for topic, scores in self.topic_scores.items():
            if scores:  # 有測試過
                avg = sum(scores) / len(scores)
                if avg < threshold:
                    weak_topics.append(topic)

        return weak_topics


class AdaptiveTeachingStrategy:
    """
    自適應教學策略引擎

    根據學員回答品質動態調整：
    - 問題難度
    - 反饋詳細度
    - 提示強度
    - 引導方式
    """

    def __init__(self, llm_handler):
        """
        初始化自適應教學系統

        Args:
            llm_handler: LLM 處理器
        """
        self.llm = llm_handler
        self.knowledge_tracker = KnowledgeTracker()

        # 當前教學模式
        self.current_mode = TeachingMode.STANDARD

        # 連續表現追蹤（用於調整模式）
        self.recent_scores = []  # 最近 5 次的得分
        self.max_recent_scores = 5

        # 學習曲線數據
        self.learning_curve = []  # [(timestamp, score, topic)]

    def evaluate_and_adapt(self, question: str, system_answer: str,
                           trainee_answer: str, score: float,
                           understanding_level: str) -> Dict:
        """
        評估學員回答並調整教學策略

        Args:
            question: 原始問題
            system_answer: 系統的回答
            trainee_answer: 學員的回答
            score: 評分 (0-10)
            understanding_level: 理解程度 (excellent/good/fair/poor)

        Returns:
            {
                'teaching_mode': 調整後的教學模式,
                'next_question_difficulty': 下次問題難度,
                'feedback_style': 反饋風格,
                'hint_level': 提示強度,
                'suggested_actions': 建議的教學行動
            }
        """
        # 1. 更新知識追蹤
        topic = self.knowledge_tracker.classify_topic(question, system_answer)
        self.knowledge_tracker.update_topic_score(topic, score)

        # 2. 更新最近表現
        self.recent_scores.append(score)
        if len(self.recent_scores) > self.max_recent_scores:
            self.recent_scores.pop(0)

        # 3. 記錄學習曲線
        self.learning_curve.append((datetime.now(), score, topic))

        # 4. 根據表現調整教學模式
        avg_recent = sum(self.recent_scores) / len(self.recent_scores) if self.recent_scores else 5.0

        if avg_recent >= 8.5:
            # 連續高分 → 挑戰模式
            self.current_mode = TeachingMode.CHALLENGE
            difficulty = "advanced"
            feedback_style = "concise"
            hint_level = 0  # 不給提示

        elif avg_recent >= 6.5:
            # 表現良好 → 標準模式
            self.current_mode = TeachingMode.STANDARD
            difficulty = "moderate"
            feedback_style = "balanced"
            hint_level = 1  # 適度提示

        elif avg_recent >= 4.0:
            # 表現普通 → 鷹架模式（分解步驟）
            self.current_mode = TeachingMode.SCAFFOLDING
            difficulty = "basic"
            feedback_style = "detailed"
            hint_level = 2  # 較多提示

        else:
            # 表現不佳 → 補救模式（回到基礎）
            self.current_mode = TeachingMode.REMEDIAL
            difficulty = "fundamental"
            feedback_style = "very_detailed"
            hint_level = 3  # 大量提示，幾乎手把手

        # 5. 生成建議的教學行動
        suggested_actions = self._generate_teaching_actions(
            score, understanding_level, topic, avg_recent
        )

        return {
            'teaching_mode': self.current_mode.value,
            'next_question_difficulty': difficulty,
            'feedback_style': feedback_style,
            'hint_level': hint_level,
            'suggested_actions': suggested_actions,
            'weak_topics': self.knowledge_tracker.identify_weak_topics(),
            'topic_performance': self.knowledge_tracker.get_topic_performance(topic)
        }

    def _generate_teaching_actions(self, score: float, understanding_level: str,
                                   topic: str, avg_recent: float) -> List[str]:
        """
        生成建議的教學行動

        Returns:
            建議行動列表
        """
        actions = []

        # 根據單次表現
        if score < 3:
            actions.append(f"重新解釋 {topic} 的基礎概念")
            actions.append("提供具體的半導體製程例子")
            actions.append("用類比方式說明（例如：日常生活中的相似現象）")
        elif score < 5:
            actions.append(f"補充 {topic} 的關鍵細節")
            actions.append("引導學員思考因果關係")
        elif score < 7:
            actions.append("鼓勵學員嘗試舉例說明")
            actions.append("提問更深入的應用問題")
        else:
            actions.append("挑戰學員思考跨領域應用")
            actions.append("引導學員發現潛在問題")

        # 根據整體趨勢
        if len(self.recent_scores) >= 3:
            if self.recent_scores[-1] < self.recent_scores[-3] - 2:
                actions.append("⚠️ 表現下滑，建議休息或降低難度")
            elif self.recent_scores[-1] > self.recent_scores[-3] + 2:
                actions.append("✅ 進步明顯，可以嘗試更難的主題")

        # 根據知識盲點
        weak_topics = self.knowledge_tracker.identify_weak_topics()
        if topic in weak_topics:
            actions.append(f"💡 {topic} 是弱點主題，建議額外練習")

        return actions

    def generate_adaptive_followup(self, original_question: str,
                                   system_answer: str,
                                   trainee_performance: Dict,
                                   scenario_context: str = None) -> str:
        """
        根據學員表現生成自適應反問問題

        Args:
            original_question: 原始問題
            system_answer: 系統回答
            trainee_performance: 學員表現評估結果
            scenario_context: 場景上下文

        Returns:
            自適應反問問題
        """
        mode = trainee_performance.get('teaching_mode', 'standard')
        difficulty = trainee_performance.get('next_question_difficulty', 'moderate')
        hint_level = trainee_performance.get('hint_level', 1)

        # 根據教學模式調整 prompt
        if mode == 'challenge':
            system_prompt = """你是半導體製程培訓導師，學員表現優異。
請生成一個**挑戰性問題**：
- 涉及多個概念的整合應用
- 需要跨領域思考（例如：熱學+光學+機械）
- 模擬真實故障診斷的複雜情境
- 不提供任何提示"""

        elif mode == 'scaffolding':
            system_prompt = """你是半導體製程培訓導師，學員需要更多引導。
請生成一個**分解式問題**（鷹架教學）：
- 將複雜問題分解成小步驟
- 每個步驟提供適度提示
- 引導學員一步步推理
- 例如：「首先想想...然後...最後...」"""

        elif mode == 'remedial':
            system_prompt = """你是半導體製程培訓導師，學員基礎概念不穩固。
請生成一個**基礎概念確認問題**：
- 回到最核心的定義和原理
- 用簡單的是非題或選擇題形式
- 提供明確的提示和例子
- 確保學員能答對，重建信心"""

        else:  # standard
            system_prompt = """你是半導體製程培訓導師。
請生成一個**標準難度的反問問題**：
- 檢驗核心概念理解
- 連結實際應用
- 適度引導但不直接給答案"""

        user_prompt = f"""剛才的問答：
Q: {original_question}
A: {system_answer}

學員表現：{mode} 模式，難度 {difficulty}

"""

        if scenario_context:
            user_prompt += f"當前場景：{scenario_context}\n\n"

        user_prompt += "請生成下一個自適應問題："

        # 使用 LLM 生成
        original_prompt = self.llm.system_prompt
        self.llm.system_prompt = system_prompt

        followup = self.llm.ask(user_prompt, maintain_context=False)

        self.llm.system_prompt = original_prompt

        return followup.strip()

    def generate_adaptive_feedback(self, score: float, feedback: str,
                                   trainee_performance: Dict) -> str:
        """
        根據學員表現生成自適應反饋

        Args:
            score: 評分
            feedback: 原始反饋
            trainee_performance: 學員表現評估

        Returns:
            增強版反饋
        """
        mode = trainee_performance['teaching_mode']
        actions = trainee_performance['suggested_actions']

        # 根據模式調整反饋語氣和內容
        if mode == 'challenge':
            tone = "簡潔專業，像對話資深工程師"
            enhanced_feedback = f"[挑戰模式] {feedback}\n\n"
            enhanced_feedback += "你已經掌握基礎概念，接下來試試更複雜的情境。"

        elif mode == 'scaffolding':
            tone = "耐心引導，逐步分解"
            enhanced_feedback = f"[鷹架引導] {feedback}\n\n"
            enhanced_feedback += "讓我們一步步來理解這個概念：\n"
            for i, action in enumerate(actions[:3], 1):
                enhanced_feedback += f"{i}. {action}\n"

        elif mode == 'remedial':
            tone = "鼓勵為主，重建信心"
            enhanced_feedback = f"[基礎鞏固] 沒關係，這個概念確實不容易。\n\n"
            enhanced_feedback += f"{feedback}\n\n"
            enhanced_feedback += "💡 建議：先掌握基礎定義，再慢慢應用到實際情境。"

        else:  # standard
            enhanced_feedback = f"{feedback}\n\n"
            if actions:
                enhanced_feedback += f"💡 建議：{actions[0]}"

        return enhanced_feedback

    def get_learning_analytics(self) -> Dict:
        """
        獲取學習分析報告

        Returns:
            詳細的學習分析數據
        """
        analytics = {
            'current_mode': self.current_mode.value,
            'recent_avg_score': round(sum(self.recent_scores) / len(self.recent_scores), 1) if self.recent_scores else 0,
            'total_attempts': len(self.learning_curve),
            'weak_topics': self.knowledge_tracker.identify_weak_topics(),
            'topic_breakdown': {}
        }

        # 各主題表現
        for topic in self.knowledge_tracker.topic_categories.keys():
            perf = self.knowledge_tracker.get_topic_performance(topic)
            if perf['attempts'] > 0:
                analytics['topic_breakdown'][topic] = perf

        # 學習趨勢
        if len(self.learning_curve) >= 5:
            recent_5 = [score for _, score, _ in self.learning_curve[-5:]]
            earlier_5 = [score for _, score, _ in self.learning_curve[-10:-5]] if len(self.learning_curve) >= 10 else []

            if earlier_5:
                recent_avg = sum(recent_5) / len(recent_5)
                earlier_avg = sum(earlier_5) / len(earlier_5)

                if recent_avg > earlier_avg + 1:
                    analytics['trend'] = 'improving'
                elif recent_avg < earlier_avg - 1:
                    analytics['trend'] = 'declining'
                else:
                    analytics['trend'] = 'stable'
            else:
                analytics['trend'] = 'insufficient_data'
        else:
            analytics['trend'] = 'just_started'

        return analytics
