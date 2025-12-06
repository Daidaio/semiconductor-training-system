# -*- coding: utf-8 -*-
"""
AI 情境學長 (AI Scenario Mentor)
使用 LLM 在故障處理情境中提供自然、像學長般的引導
"""

from typing import Dict, List, Optional
import os
import sys

# 嘗試導入 LLM 支援
try:
    from stage1_theory.local_mentor_bot import LocalMentorBot
    HAS_LOCAL_LLM = True
except ImportError:
    HAS_LOCAL_LLM = False

try:
    from stage1_theory.senior_mentor_bot import SeniorMentorBot
    HAS_CLAUDE_API = True
except ImportError:
    HAS_CLAUDE_API = False


class AIScenarioMentor:
    """AI 情境學長 - 在故障處理過程中提供像學長般的自然引導"""

    def __init__(self, use_ai: bool = True):
        """
        初始化 AI 情境學長

        Args:
            use_ai: 是否使用 AI（如果為 False 或 AI 不可用，則使用模板回應）
        """
        self.use_ai = use_ai
        self.ai_bot = None
        self.llm_mode = "mock"

        # 情境上下文
        self.current_scenario_type = None
        self.current_scenario_name = None
        self.scenario_start_time = None
        self.action_count = 0

        # 對話歷史（用於保持上下文）
        self.conversation_history = []

        if use_ai:
            self._initialize_ai()

        print(f"[Init] AI 情境學長模式: {self.llm_mode}")

    def _initialize_ai(self):
        """初始化 AI 引擎（優先順序：Local LLM > Claude API > Mock）"""

        # 1. 嘗試本地 LLM
        if HAS_LOCAL_LLM:
            try:
                local_bot = LocalMentorBot(
                    model_name=os.getenv("LOCAL_LLM_MODEL", "qwen2.5:7b")
                )
                if local_bot._check_ollama_available():
                    self.ai_bot = local_bot
                    self.llm_mode = "local"
                    print(f"[OK] 使用本地 LLM: {local_bot.model_name}")
                    self._customize_for_scenario()
                    return
            except Exception as e:
                print(f"[Info] 本地 LLM 不可用: {e}")

        # 2. 嘗試 Claude API
        if HAS_CLAUDE_API and os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.ai_bot = SeniorMentorBot()
                self.llm_mode = "claude"
                print("[OK] 使用 Claude API")
                self._customize_for_scenario()
                return
            except Exception as e:
                print(f"[Info] Claude API 不可用: {e}")

        # 3. 使用 Mock 模式
        print("[Info] AI 不可用，使用模板回應")
        self.use_ai = False
        self.llm_mode = "mock"

    def _customize_for_scenario(self):
        """客製化 AI 系統提示詞，專注於情境引導"""
        scenario_system_prompt = """你是一位經驗豐富的半導體設備現場學長，正在旁邊協助學弟處理設備故障。

你的角色特點：
1. **像學長，不像老師**：用輕鬆、自然的口吻，不要太正式
2. **邊做邊聊**：就像一起在現場處理問題，自然地給建議
3. **適時引導**：不直接給答案，而是引導思考方向
4. **鼓勵嘗試**：對學弟的想法給予肯定，即使不完全正確也先鼓勵
5. **分享經驗**：會說「我之前遇到過...」「通常這種情況...」這類經驗談

對話風格：
- 使用「你看一下...」「我們先...」「試試...」這類口語
- 適時用「嗯」「對」「沒錯」等語助詞
- 會問「你覺得呢？」「接下來打算怎麼做？」
- 不要長篇大論，簡短自然

情境處理原則：
1. 學弟剛發現問題時：鼓勵觀察，引導思考可能原因
2. 學弟檢查參數時：肯定行動，幫助解讀數據
3. 學弟採取行動時：確認思路，提醒注意事項
4. 學弟問為什麼時：反問引導，讓他自己想通
5. 情況危急時：直接提醒，「這個要趕快處理」

記住：你就是現場的學長，自然、輕鬆、實用。"""

        if self.ai_bot:
            self.ai_bot.system_prompt = scenario_system_prompt

    def set_scenario_context(self, scenario_info: Dict):
        """
        設定當前情境上下文

        Args:
            scenario_info: 情境資訊
        """
        self.current_scenario_type = scenario_info.get("type")
        self.current_scenario_name = scenario_info.get("name")
        self.scenario_start_time = scenario_info.get("start_time")
        self.action_count = 0
        self.conversation_history = []

        # 給 AI 一個情境開場
        if self.use_ai and self.ai_bot:
            context = f"""
[情境開始]
故障類型：{self.current_scenario_name}
描述：{scenario_info.get('description', '')}
初始症狀：{', '.join(scenario_info.get('initial_symptoms', []))}
"""
            self.conversation_history.append({
                "role": "system",
                "content": context
            })

    def respond_to_question(self, question: str, scenario_info: Dict,
                           current_state: Dict, action_history: List[Dict]) -> str:
        """
        回應學員在情境中的提問

        Args:
            question: 學員的問題
            scenario_info: 情境資訊
            current_state: 當前機台狀態
            action_history: 動作歷史

        Returns:
            學長的回應
        """
        self.action_count = len(action_history)

        if self.use_ai and self.ai_bot:
            return self._ai_respond(question, scenario_info, current_state, action_history)
        else:
            return self._template_respond(question, scenario_info, current_state, action_history)

    def _ai_respond(self, question: str, scenario_info: Dict,
                   current_state: Dict, action_history: List[Dict]) -> str:
        """使用 AI 生成自然回應"""

        # 構建上下文提示
        context = self._build_context(scenario_info, current_state, action_history)

        # 完整的問題
        full_question = f"""
{context}

學弟問：「{question}」

請用自然的學長口吻回應，幫助他思考但不直接給答案。回應要簡短（2-3句話）。
"""

        try:
            response = self.ai_bot.ask(full_question, maintain_context=True)

            # 清理回應格式
            response = response.strip()
            if response.startswith("[") and "]" in response:
                # 移除可能的 [學長] 標籤
                response = response[response.index("]")+1:].strip()

            return f"[學長] {response}"

        except Exception as e:
            print(f"[Error] AI 回應失敗: {e}")
            # 降級到模板回應
            return self._template_respond(question, scenario_info, current_state, action_history)

    def _build_context(self, scenario_info: Dict, current_state: Dict,
                      action_history: List[Dict]) -> str:
        """構建上下文資訊"""

        context_parts = []

        # 當前情境階段
        stage = scenario_info.get("current_stage", 0)
        stage_name = ["初期", "發展中", "嚴重", "危急"][min(stage, 3)]
        context_parts.append(f"[情況: {stage_name}]")

        # 經過時間
        time_elapsed = scenario_info.get("time_elapsed", 0)
        if time_elapsed > 0:
            context_parts.append(f"[已處理 {time_elapsed//60} 分鐘]")

        # 最近的動作
        if action_history:
            last_actions = action_history[-3:]
            actions_desc = "、".join([a.get("raw_input", "") for a in last_actions])
            context_parts.append(f"[學弟剛做了: {actions_desc}]")

        # 關鍵狀態資訊
        key_states = []
        if "lens_temp" in current_state:
            key_states.append(f"溫度 {current_state['lens_temp']}°C")
        if "cooling_flow" in current_state:
            key_states.append(f"流量 {current_state['cooling_flow']} L/min")
        if "vacuum_pressure" in current_state:
            key_states.append(f"真空 {current_state['vacuum_pressure']:.2e} Torr")

        if key_states:
            context_parts.append(f"[當前狀態: {', '.join(key_states)}]")

        return "\n".join(context_parts)

    def _template_respond(self, question: str, scenario_info: Dict,
                         current_state: Dict, action_history: List[Dict]) -> str:
        """使用模板生成回應（當 AI 不可用時）"""

        scenario_type = scenario_info.get("type", "unknown")
        stage = scenario_info.get("current_stage", 0)

        # 簡單的關鍵字匹配
        question_lower = question.lower()

        if any(word in question_lower for word in ["為什麼", "原因"]):
            if scenario_type == "cooling_failure":
                if stage == 0:
                    return "[學長] 嗯，溫度上升通常和散熱有關。你覺得冷卻系統的哪個地方可能有問題？"
                else:
                    return "[學長] 你看流量這麼低，通常是什麼原因？想想看過濾器的狀況。"
            else:
                return "[學長] 我們先不急著找原因，先把現在看到的異常現象都確認一遍。你觀察到什麼？"

        elif any(word in question_lower for word in ["怎麼辦", "怎麼做"]):
            if stage >= 2:
                return "[學長] 這個狀況有點嚴重了。你覺得繼續生產安全嗎？優先考慮什麼比較好？"
            else:
                return "[學長] 先別急，我們一步步來。現在最該確認的是什麼？你想想看。"

        elif any(word in question_lower for word in ["對嗎", "正確", "這樣"]):
            if action_history and len(action_history) > 0:
                return "[學長] 對，這個方向沒錯。繼續檢查，看看還有什麼發現。"
            else:
                return "[學長] 這個想法可以試試。動手做做看吧，我在旁邊看著。"

        else:
            # 一般性引導
            if self.action_count == 0:
                return "[學長] 剛發現問題對吧？別緊張，先從基本的檢查開始。你想先看什麼？"
            elif self.action_count < 3:
                return "[學長] 嗯，我們已經檢查了一些東西。你覺得這些現象之間有什麼關聯嗎？"
            else:
                return "[學長] 檢查得差不多了，現在該採取行動了。你打算怎麼處理？"

    def provide_action_feedback(self, action: Dict, action_result: Dict,
                               scenario_info: Dict, current_state: Dict) -> Optional[str]:
        """
        對學員的動作提供即時回饋

        Args:
            action: 動作資訊
            action_result: 動作執行結果
            scenario_info: 情境資訊
            current_state: 當前狀態

        Returns:
            學長的回饋（如果有的話）
        """
        intent = action.get("intent", "")
        target = action.get("target", "")
        success = action_result.get("success", False)

        self.action_count += 1

        # 關鍵動作給予回饋
        if not success:
            if self.use_ai and self.ai_bot:
                feedback = self._ai_action_feedback(action, action_result, scenario_info, current_state, is_success=False)
                return feedback
            else:
                return "[學長] 嗯...這個好像不太對。我們換個方向試試？"

        # 正確的關鍵動作
        key_actions = {
            ("check", "cooling"): "很好，從冷卻系統開始查是對的。",
            ("check", "filter"): "對，注意到過濾器了。看看狀況如何？",
            ("check", "vacuum"): "嗯，真空系統確實該檢查。",
            ("shutdown", None): "這種情況停機是明智的，安全第一。",
            ("replace", "filter"): "換新的過濾器，應該就能恢復了。",
            ("clean", "lens"): "清潔光學元件要小心，別造成二次污染。",
            ("calibrate", "alignment"): "校正對準系統，這個方向對了。",
        }

        action_key = (intent, target)
        if action_key in key_actions:
            if self.use_ai and self.ai_bot:
                return self._ai_action_feedback(action, action_result, scenario_info, current_state, is_success=True)
            else:
                return f"[學長] {key_actions[action_key]}"

        # 特定情境的危險動作警告
        if intent == "adjust" and current_state.get("critical", False):
            return "[學長] 欸等等，情況這麼嚴重了，調整參數可能不夠。要不要考慮更直接的處理？"

        return None

    def _ai_action_feedback(self, action: Dict, action_result: Dict,
                           scenario_info: Dict, current_state: Dict,
                           is_success: bool) -> str:
        """使用 AI 生成動作回饋"""

        intent = action.get("intent", "")
        target = action.get("target", "")
        raw_input = action.get("raw_input", "")

        context = self._build_context(scenario_info, current_state, [])

        prompt = f"""
{context}

學弟剛執行了動作：「{raw_input}」
動作意圖：{intent}
目標：{target}
結果：{'成功' if is_success else '失敗'}

請用一句話給予自然的學長式回饋（不超過20字）。
如果是關鍵正確動作，簡單肯定；如果失敗，友善地提示換個方向。
"""

        try:
            response = self.ai_bot.ask(prompt, maintain_context=False)
            response = response.strip()

            # 清理格式
            if response.startswith("[") and "]" in response:
                response = response[response.index("]")+1:].strip()

            # 限制長度
            if len(response) > 50:
                response = response[:47] + "..."

            return f"[學長] {response}"

        except Exception as e:
            print(f"[Error] AI 回饋失敗: {e}")
            return None

    def provide_stage_transition_comment(self, scenario_info: Dict,
                                        new_stage: int, symptoms: List[str]) -> str:
        """
        在情境階段轉換時提供評論

        Args:
            scenario_info: 情境資訊
            new_stage: 新階段編號
            symptoms: 新症狀

        Returns:
            學長的評論
        """

        if self.use_ai and self.ai_bot:
            context = f"""
[情況發展]
故障情境：{scenario_info.get('name')}
進入階段：{new_stage}
新症狀：{', '.join(symptoms)}
已處理時間：{scenario_info.get('time_elapsed', 0)//60} 分鐘
學弟執行動作數：{self.action_count}
"""

            prompt = f"""
{context}

情況有變化了。請用學長的口吻，簡短（1-2句話）提醒學弟注意。
如果情況變嚴重，語氣要稍微緊張；如果還好，就輕鬆提醒。
"""

            try:
                response = self.ai_bot.ask(prompt, maintain_context=True)
                response = response.strip()

                if response.startswith("[") and "]" in response:
                    response = response[response.index("]")+1:].strip()

                return f"\n[學長] {response}\n"

            except Exception as e:
                print(f"[Error] AI 評論失敗: {e}")

        # 模板回應
        if new_stage == 1:
            return "\n[學長] 欸，情況好像在變化。要加快速度了。\n"
        elif new_stage == 2:
            return "\n[學長] 這個有點嚴重了，我們要趕快處理！\n"
        elif new_stage >= 3:
            return "\n[學長] 狀況很不好！優先考慮安全，該停就停！\n"

        return ""

    def provide_final_review(self, scenario_info: Dict, evaluation: Dict,
                            action_history: List[Dict]) -> str:
        """
        提供情境結束後的復盤

        Args:
            scenario_info: 情境資訊
            evaluation: 評估結果
            action_history: 動作歷史

        Returns:
            學長的復盤
        """

        if self.use_ai and self.ai_bot:
            context = f"""
[情境結束復盤]
故障：{scenario_info.get('name')}
處理時間：{scenario_info.get('time_elapsed', 0)//60} 分鐘
診斷準確度：{evaluation.get('accuracy', 0)*100:.1f}%
處理效率：{evaluation.get('time_score', 0)*100:.1f}%
安全意識：{evaluation.get('safety_score', 0)*100:.1f}%
總分：{evaluation.get('overall_score', 0)*100:.1f}%

學弟執行的動作：
{self._format_actions(action_history)}

標準處理流程：
{self._format_correct_actions(scenario_info.get('correct_actions', []))}
"""

            prompt = f"""
{context}

情境處理完了。請用學長的口吻給個總評：
1. 簡單評價表現（2-3句話）
2. 指出做得好的地方
3. 提示可以改進的地方
4. 分享一個關鍵經驗

要自然、輕鬆，不要太正式。總字數不超過200字。
"""

            try:
                response = self.ai_bot.ask(prompt, maintain_context=False)
                response = response.strip()

                if response.startswith("[") and "]" in response:
                    response = response[response.index("]")+1:].strip()

                return f"\n[學長 - 復盤]\n\n{response}\n"

            except Exception as e:
                print(f"[Error] AI 復盤失敗: {e}")

        # 模板復盤
        accuracy = evaluation.get("accuracy", 0)
        overall = evaluation.get("overall_score", 0)

        review = "\n[學長 - 復盤]\n\n"

        if overall >= 0.8:
            review += "不錯欸！處理得很穩，基本上沒什麼問題。\n\n"
        elif overall >= 0.6:
            review += "還可以，方向是對的，不過有些地方可以更快一點。\n\n"
        else:
            review += "嗯...這次處理有點慢。我們一起看看哪裡可以改進。\n\n"

        if accuracy > 0.7:
            review += "✓ 診斷方向正確，能找到根本原因\n"
        else:
            review += "• 下次診斷可以更系統化，從整體到局部\n"

        review += "\n記住：現場處理要快、要穩、要安全。多練習就會越來越熟練了！\n"

        return review

    def _format_actions(self, action_history: List[Dict]) -> str:
        """格式化動作歷史"""
        if not action_history:
            return "（無動作）"

        actions = []
        for i, action in enumerate(action_history[:10], 1):  # 最多顯示 10 個
            raw_input = action.get("raw_input", "未知動作")
            actions.append(f"{i}. {raw_input}")

        if len(action_history) > 10:
            actions.append(f"... 還有 {len(action_history)-10} 個動作")

        return "\n".join(actions)

    def _format_correct_actions(self, correct_actions: List[str]) -> str:
        """格式化標準動作"""
        if not correct_actions:
            return "（無標準流程）"

        return "\n".join([f"{i}. {action}" for i, action in enumerate(correct_actions, 1)])

    def understand_unclear_input(self, user_input: str, scenario_info: Dict,
                                 current_state: Dict) -> Optional[Dict]:
        """
        使用 AI 理解不明確的輸入

        Args:
            user_input: 學員的原始輸入
            scenario_info: 情境資訊
            current_state: 當前狀態

        Returns:
            AI 建議的動作，如果無法理解則返回 None
        """
        if not self.use_ai or not self.ai_bot:
            return None

        # 構建理解提示
        context = f"""
[當前情境]
故障：{scenario_info.get('name', '未知')}
階段：{scenario_info.get('current_stage', 0)}

[區分「執行動作」與「詢問學長」]

**詢問學長**（問判斷、問建議、問原因）- 優先判斷：
- 「請問學長...」「學長...」開頭 → 一定是詢問學長
- 「插頭鬆了嗎」「溫度正常嗎」「流量OK嗎」→ 問學長判斷
- 「有推薦的處理方式嗎」「該怎麼辦」「為什麼...」→ 問學長建議/原因
- 「什麼情況會...」「怎樣會造成...」→ 問學長解釋
- **判斷規則**：
  1. 以「請問」「學長」「專家」開頭 → 一定是詢問
  2. 以「...嗎？」結尾的問句 → 通常是詢問
  3. 包含「為什麼」「怎麼會」「什麼情況」→ 通常是詢問

**執行動作**（會實際操作設備，返回數據）：
- 「檢查冷卻水」「看一下溫度」「檢查過濾網狀態」
- 這些是要求系統**執行檢查**並返回具體數值
- 特徵：直接命令式，不是疑問句

[可用動作]
1. 檢查設備：檢查冷卻水、檢查溫度、檢查過濾網等
2. 調整參數：調整流量、調整溫度等
3. 更換零件：更換過濾網、更換感測器
4. 停機/重啟
5. 清潔設備：清潔鏡片、清潔過濾網

[學員說]
「{user_input}」

請判斷學員想做什麼：

**如果是問判斷/建議/原因** → 回答「詢問學長」或「問專家」
- 例：「請問學長，什麼情況會造成對準偏移」→「詢問學長」（或「問專家」）
- 例：「插頭鬆了嗎」→「詢問學長」
- 例：「溫度正常嗎」→「問專家溫度是否正常」
- 例：「該怎麼辦」→「詢問學長」
- **重要**：以「請問」「學長」開頭的句子，一律回答「詢問學長」

**如果是要求執行動作** → 回答具體操作
- 例：「檢查冷卻水」→「檢查冷卻水」
- 例：「調整流量」→「調整流量」
- 例：「清理過濾器」→「清潔過濾網」

只回答一個操作，不要解釋。
**再次強調**：看到「請問學長」「學長」「專家」開頭的句子，直接回答「詢問學長」或「問專家」。
"""

        try:
            response = self.ai_bot.ask(context, maintain_context=False)
            response = response.strip()

            # 清理格式
            if response.startswith("[") and "]" in response:
                response = response[response.index("]")+1:].strip()

            # 如果 AI 說「不確定」，返回 None
            if "不確定" in response:
                return None

            # 返回 AI 建議的標準化指令
            return {
                "suggestion": response,
                "original": user_input
            }

        except Exception as e:
            print(f"[Warning] AI 理解輸入失敗: {e}")
            return None

    def reset(self):
        """重置對話歷史"""
        self.conversation_history = []
        self.current_scenario_type = None
        self.action_count = 0

        if self.ai_bot and hasattr(self.ai_bot, 'reset_conversation'):
            self.ai_bot.reset_conversation()
