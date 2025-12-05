# -*- coding: utf-8 -*-
"""
AI 專家顧問 (AI Expert Advisor)
使用蘇格拉底式提問引導學員思考，不直接給答案
"""

from typing import Dict, List, Optional
import random


class AIExpertAdvisor:
    """AI 專家顧問 - 蘇格拉底式引導"""

    def __init__(self):
        """初始化 AI 專家"""

        # 蘇格拉底式提問模板
        self.question_templates = {
            "observation": [
                "你觀察到哪些異常現象？",
                "除了這個，還有其他異常嗎？",
                "這些現象之間有什麼關聯？",
                "哪個參數變化最明顯？"
            ],
            "analysis": [
                "為什麼會出現這種情況？",
                "可能的原因有哪些？",
                "這個原因合理嗎？有沒有其他可能？",
                "如果是XX原因，應該會看到什麼現象？"
            ],
            "action": [
                "現在最優先要做什麼？",
                "這個動作會帶來什麼效果？",
                "有沒有風險？",
                "還有其他選擇嗎？"
            ],
            "verification": [
                "怎麼確認你的判斷是對的？",
                "需要檢查什麼來驗證？",
                "如果檢查結果是XX，代表什麼？"
            ]
        }

        # 情境特定的引導
        self.scenario_guidance = {
            "cooling_failure": {
                "hints": {
                    "early": "溫度上升時，你會想到哪些可能的原因？",
                    "middle": "冷卻系統的哪個部分最容易出問題？",
                    "late": "流量異常，通常是什麼原因？"
                },
                "affirmations": {
                    "check_cooling": "很好，從冷卻系統開始檢查是正確的思路",
                    "check_filter": "注意到過濾網了，觀察很仔細",
                    "shutdown": "在這種情況下停機是明智的決定"
                }
            },
            "vacuum_leak": {
                "hints": {
                    "early": "真空度下降，可能的原因有哪些？",
                    "middle": "有什麼工具可以幫助定位洩漏點？",
                    "late": "密封部位是不是該檢查了？"
                },
                "affirmations": {
                    "check_vacuum": "對，先確認真空系統的狀態",
                    "use_detector": "使用氦氣檢測器是專業的做法",
                    "locate_leak": "找到洩漏點了，很好"
                }
            },
            "alignment_drift": {
                "hints": {
                    "early": "對準誤差增加，會影響什麼？",
                    "middle": "繼續生產的風險是什麼？",
                    "late": "這種情況下需要校正還是維修？"
                },
                "affirmations": {
                    "check_alignment": "檢查對準數據是第一步",
                    "stop_production": "及時停止生產，避免更大損失",
                    "calibrate": "執行校正是正確的處置"
                }
            },
            "optical_contamination": {
                "hints": {
                    "early": "光源強度下降，除了光源本身，還可能是什麼問題？",
                    "middle": "鏡片污染會有什麼影響？",
                    "late": "清潔光學元件要注意什麼？"
                },
                "affirmations": {
                    "check_light": "確認光源狀態是對的",
                    "check_lens": "想到檢查鏡片，很好",
                    "clean_carefully": "注意清潔方法，避免二次污染"
                }
            },
            "power_fluctuation": {
                "hints": {
                    "early": "多個系統同時異常，這說明什麼？",
                    "middle": "有沒有共同的上游原因？",
                    "late": "這種情況下最安全的做法是什麼？"
                },
                "affirmations": {
                    "multiple_alarms": "注意到多系統異常，思路正確",
                    "suspect_power": "懷疑電源問題，判斷準確",
                    "emergency_stop": "緊急停機是最安全的選擇"
                }
            }
        }

        # 對話歷史
        self.conversation_history = []

    def respond_to_question(self, question: str, scenario_info: Dict,
                           current_state: Dict, action_history: List[Dict]) -> str:
        """
        回應學員的問題

        Args:
            question: 學員的問題
            scenario_info: 情境資訊
            current_state: 當前狀態
            action_history: 動作歷史

        Returns:
            AI 專家的回應
        """
        scenario_type = scenario_info.get("type", "unknown")

        # 記錄對話
        self.conversation_history.append({
            "student": question,
            "scenario": scenario_type,
            "stage": scenario_info.get("current_stage", 0)
        })

        # 判斷問題類型
        question_type = self._classify_question(question)

        # 根據情境和階段生成回應
        response = self._generate_response(
            question_type, scenario_type, scenario_info,
            current_state, action_history
        )

        self.conversation_history[-1]["expert"] = response

        return response

    def _classify_question(self, question: str) -> str:
        """分類問題類型"""
        question_lower = question.lower()

        if any(word in question_lower for word in ["為什麼", "原因", "怎麼會"]):
            return "why"
        elif any(word in question_lower for word in ["怎麼辦", "怎麼做", "如何", "該"]):
            return "how"
        elif any(word in question_lower for word in ["建議", "意見", "看法"]):
            return "advice"
        elif any(word in question_lower for word in ["對嗎", "正確", "可以"]):
            return "verification"
        else:
            return "general"

    def _generate_response(self, question_type: str, scenario_type: str,
                          scenario_info: Dict, current_state: Dict,
                          action_history: List[Dict]) -> str:
        """生成回應"""

        current_stage = scenario_info.get("current_stage", 0)
        stage_name = "early" if current_stage == 0 else "middle" if current_stage == 1 else "late"

        response = "[AI 專家] \n\n"

        # 根據問題類型回應
        if question_type == "why":
            response += self._respond_why(scenario_type, stage_name, current_state, action_history)

        elif question_type == "how":
            response += self._respond_how(scenario_type, stage_name, current_state, action_history)

        elif question_type == "advice":
            response += self._respond_advice(scenario_type, stage_name, current_state, action_history)

        elif question_type == "verification":
            response += self._respond_verification(scenario_type, current_state, action_history)

        else:
            response += self._respond_general(scenario_type, stage_name, current_state)

        # 添加蘇格拉底式反問
        response += "\n\n" + self._add_socratic_question(question_type, scenario_type, stage_name)

        return response

    def _respond_why(self, scenario_type: str, stage: str,
                    current_state: Dict, action_history: List[Dict]) -> str:
        """回應「為什麼」類問題"""

        if scenario_type == "cooling_failure":
            if stage == "early":
                return "溫度上升通常和散熱有關。你覺得散熱系統的哪個環節可能有問題？"
            elif stage == "middle":
                return "你已經看到流量下降了。想想看，什麼情況會讓流量減少？"
            else:
                return "過濾網堵塞是常見原因。你還記得上次更換是什麼時候嗎？"

        elif scenario_type == "vacuum_leak":
            if stage == "early":
                return "真空系統很複雜，有很多密封點。你會從哪裡開始查？"
            else:
                return "密封圈老化是真空洩漏的主要原因。哪些部位的密封圈最容易老化？"

        elif scenario_type == "alignment_drift":
            return "對準偏移可能是機械問題或環境因素。你觀察到有振動或溫度變化嗎？"

        elif scenario_type == "optical_contamination":
            return "光學污染可能來自環境或製程。最近有什麼特殊情況嗎？"

        else:
            return "讓我們一起分析可能的原因。你先說說看到了什麼現象？"

    def _respond_how(self, scenario_type: str, stage: str,
                    current_state: Dict, action_history: List[Dict]) -> str:
        """回應「怎麼辦」類問題"""

        # 不直接給答案，引導思考
        response = "在回答「怎麼做」之前，我們先想想：\n\n"

        response += "1. 現在的狀況有多緊急？\n"
        response += "2. 繼續生產的風險是什麼？\n"
        response += "3. 你有足夠的資訊做決定嗎？\n\n"

        response += "根據這些，你覺得應該優先做什麼？"

        return response

    def _respond_advice(self, scenario_type: str, stage: str,
                       current_state: Dict, action_history: List[Dict]) -> str:
        """回應「建議」類問題"""

        # 評估學員目前的進展
        num_actions = len(action_history)

        if num_actions == 0:
            return "你還沒有採取任何行動。我建議先從觀察和檢查開始。你覺得應該先檢查什麼？"

        elif num_actions < 3:
            return "你已經開始行動了，這很好。現在掌握的資訊夠做判斷了嗎？還需要檢查什麼？"

        else:
            # 檢查是否在正確方向
            last_action = action_history[-1]

            if self._is_action_appropriate(last_action, scenario_type, stage):
                return "你的思路是對的，繼續下去。下一步打算怎麼做？"
            else:
                return "我注意到你做了很多檢查。有沒有發現什麼關鍵線索？試著把現象串聯起來看。"

    def _respond_verification(self, scenario_type: str, current_state: Dict,
                             action_history: List[Dict]) -> str:
        """回應「驗證」類問題"""

        if not action_history:
            return "想法不錯，但還需要更多資訊。你打算怎麼驗證這個想法？"

        last_action = action_history[-1]
        intent = last_action.get("intent", "")

        if intent == "check":
            return "檢查是對的方向。檢查結果告訴你什麼？"
        elif intent == "shutdown":
            return "考慮停機是謹慎的。你確定現在的情況需要停機嗎？"
        elif intent == "replace" or intent == "clean":
            return "這個動作可以解決問題嗎？有沒有先確認根本原因？"
        else:
            return "這個想法可行。執行前還需要考慮什麼？"

    def _respond_general(self, scenario_type: str, stage: str, current_state: Dict) -> str:
        """一般性回應"""

        guidance = self.scenario_guidance.get(scenario_type, {})
        hints = guidance.get("hints", {})

        hint = hints.get(stage, "讓我們一起分析現在的情況")

        return hint

    def _add_socratic_question(self, question_type: str, scenario_type: str, stage: str) -> str:
        """添加蘇格拉底式反問"""

        # 根據對話次數調整反問深度
        num_conversations = len(self.conversation_history)

        if num_conversations <= 2:
            # 初期：引導觀察
            return random.choice([
                "你看到了什麼異常？",
                "還有其他現象嗎？",
                "哪個參數最值得注意？"
            ])

        elif num_conversations <= 5:
            # 中期：引導分析
            return random.choice([
                "這些現象之間有什麼關聯？",
                "可能的根本原因是什麼？",
                "如何驗證你的判斷？"
            ])

        else:
            # 後期：引導行動
            return random.choice([
                "現在應該採取什麼行動？",
                "這個行動的風險是什麼？",
                "還需要考慮什麼？"
            ])

    def _is_action_appropriate(self, action: Dict, scenario_type: str, stage: str) -> bool:
        """判斷動作是否合適"""

        intent = action.get("intent", "")
        target = action.get("target", "")

        # 簡化的判斷邏輯
        if scenario_type == "cooling_failure":
            if stage == "early" and intent == "check" and target == "cooling":
                return True
            elif stage == "middle" and intent == "check" and target == "filter":
                return True
            elif stage == "late" and intent == "shutdown":
                return True

        elif scenario_type == "vacuum_leak":
            if intent == "check" and target == "vacuum":
                return True

        elif scenario_type == "alignment_drift":
            if intent == "check" and target == "alignment":
                return True
            elif intent == "calibrate":
                return True

        elif scenario_type == "optical_contamination":
            if intent == "check" and ("light" in target or "lens" in target):
                return True
            elif intent == "clean":
                return True

        # 任何時候檢查都是合理的
        if intent == "check":
            return True

        return False

    def provide_affirmation(self, action: Dict, scenario_type: str) -> Optional[str]:
        """
        對正確的動作給予肯定

        Args:
            action: 動作資訊
            scenario_type: 情境類型

        Returns:
            肯定訊息，如果不是關鍵動作則返回 None
        """
        intent = action.get("intent", "")
        target = action.get("target", "")

        guidance = self.scenario_guidance.get(scenario_type, {})
        affirmations = guidance.get("affirmations", {})

        # 檢查是否有匹配的肯定訊息
        for key, message in affirmations.items():
            if key in intent or key in target:
                return f"[AI 專家] {message}"

        return None

    def provide_final_review(self, scenario_info: Dict, evaluation: Dict,
                            action_history: List[Dict]) -> str:
        """
        提供最終復盤

        Args:
            scenario_info: 情境資訊
            evaluation: 評估結果
            action_history: 動作歷史

        Returns:
            復盤內容
        """
        response = "[AI 專家 - 最終復盤]\n\n"

        # 1. 情境回顧
        response += f"## 情境回顧\n"
        response += f"本次故障：{scenario_info['name']}\n"
        response += f"根本原因：{scenario_info['root_cause']}\n\n"

        # 2. 你的表現
        accuracy = evaluation.get("accuracy", 0)
        time_score = evaluation.get("time_score", 0)
        safety_score = evaluation.get("safety_score", 0)

        response += f"## 你的表現\n"
        response += f"診斷準確度：{accuracy*100:.1f}%\n"
        response += f"處理效率：{time_score*100:.1f}%\n"
        response += f"安全意識：{safety_score*100:.1f}%\n\n"

        # 3. 做得好的地方
        response += f"## 做得好的地方\n"
        if accuracy > 0.7:
            response += "- 診斷方向正確，能找到根本原因\n"
        if time_score > 0.7:
            response += "- 處理迅速，沒有浪費時間\n"
        if safety_score > 0.8:
            response += "- 安全意識強，該停機時果斷停機\n"

        # 4. 可以改進的地方
        response += f"\n## 可以改進的地方\n"
        if accuracy < 0.7:
            response += "- 診斷時可以更系統化，從整體到局部\n"
        if time_score < 0.7:
            response += "- 發現問題後要快速行動，避免情況惡化\n"
        if safety_score < 0.8:
            response += "- 情況嚴重時要優先考慮安全，及時停機\n"

        # 5. 標準處理流程
        response += f"\n## 標準處理流程\n"
        for i, action in enumerate(scenario_info.get("correct_actions", []), 1):
            response += f"{i}. {action}\n"

        # 6. 關鍵學習點
        response += f"\n## 關鍵學習點\n"
        response += self._get_key_learning(scenario_info["type"])

        return response

    def _get_key_learning(self, scenario_type: str) -> str:
        """獲取關鍵學習點"""

        key_learnings = {
            "cooling_failure": """
- 溫度異常要優先檢查冷卻系統
- 過濾網堵塞是常見問題，定期保養很重要
- 發現流量異常要及時處理，避免設備損壞
""",
            "vacuum_leak": """
- 真空洩漏用氦氣檢測器最有效
- 密封圈是易損件，要定期更換
- 真空度異常會嚴重影響產品品質
""",
            "alignment_drift": """
- 對準誤差直接影響良率
- 發現偏移要立即停止生產
- 環境振動和溫度變化都可能造成偏移
""",
            "optical_contamination": """
- 光學元件清潔要使用專用工具
- 環境管控很重要，防止二次污染
- 定期檢查光源強度，及早發現問題
""",
            "power_fluctuation": """
- 多系統異常要懷疑共同原因
- 電源問題有跳機風險，要緊急處理
- UPS 和穩壓設備的維護不可忽視
"""
        }

        return key_learnings.get(scenario_type, "持續學習，積累經驗")

    def reset(self):
        """重置對話歷史"""
        self.conversation_history = []
