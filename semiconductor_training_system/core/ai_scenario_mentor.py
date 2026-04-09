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
    from stage1_theory.qwen_mentor_bot import QwenMentorBot
    HAS_QWEN_LLM = True
except ImportError:
    HAS_QWEN_LLM = False

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

        # 自適應教學模式（由外部設定）
        self.teaching_mode = "standard"

        # 對話歷史（用於保持上下文）
        self.conversation_history = []

        if use_ai:
            self._initialize_ai()

        print(f"[Init] AI 情境學長模式: {self.llm_mode}")

    def _initialize_ai(self):
        """初始化 AI 引擎（優先順序：Qwen LLM > Ollama LLM > Claude API > Mock）"""

        # 1. 嘗試 Qwen 本地 LLM（Transformers）
        if HAS_QWEN_LLM and os.getenv("USE_QWEN_LLM", "false").lower() == "true":
            try:
                print("[Info] 正在載入 Qwen 2.5 模型（這可能需要幾分鐘）...")
                qwen_bot = QwenMentorBot(auto_load=True)
                if qwen_bot.is_available():
                    self.ai_bot = qwen_bot
                    self.llm_mode = "qwen"
                    print(f"[OK] 使用 Qwen LLM: {qwen_bot.model_name}")
                    return
            except Exception as e:
                print(f"[Info] Qwen LLM 不可用: {e}")

        # 2. 嘗試 Ollama 本地 LLM
        if HAS_LOCAL_LLM:
            try:
                local_bot = LocalMentorBot(
                    model_name=os.getenv("LOCAL_LLM_MODEL", "qwen2.5:7b")
                )
                if local_bot._check_ollama_available():
                    self.ai_bot = local_bot
                    self.llm_mode = "local"
                    print(f"[OK] 使用 Ollama LLM: {local_bot.model_name}")
                    self._customize_for_scenario()
                    return
            except Exception as e:
                print(f"[Info] Ollama LLM 不可用: {e}")

        # 3. 嘗試 Claude API
        if HAS_CLAUDE_API and os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.ai_bot = SeniorMentorBot()
                self.llm_mode = "claude"
                print("[OK] 使用 Claude API")
                self._customize_for_scenario()
                return
            except Exception as e:
                print(f"[Info] Claude API 不可用: {e}")

        # 4. 使用 Mock 模式
        print("[Info] AI 不可用，使用模板回應")
        self.use_ai = False
        self.llm_mode = "mock"

    def _customize_for_scenario(self):
        """客製化 AI 系統提示詞：以 standard 模式初始化，之後由自適應機制動態切換"""
        self.teaching_mode = ""  # 強制觸發更新
        self.set_teaching_mode("standard")

    def set_teaching_mode(self, mode: str):
        """
        根據自適應評估結果動態切換 LLM 的教學風格

        Args:
            mode: 'challenge' | 'standard' | 'scaffolding' | 'remedial'
        """
        if mode == self.teaching_mode:
            return  # 沒變就不動

        self.teaching_mode = mode
        if not self.ai_bot:
            return

        _PROMPTS = {
            "challenge": """你是一位經驗豐富的半導體設備現場學長，學弟目前表現優秀。

教學風格：挑戰模式
- 不給現成答案，要求學弟自己推導
- 問進階問題：「你覺得這個現象背後的物理機制是？」
- 引導跨概念連結：「這和你之前說的 overlay 有什麼關係？」
- 偶爾故意挑戰他的答案，看他能不能辯護
- 口吻輕鬆但要求嚴格

【虛擬環境操作說明】這是 3D 虛擬訓練環境。學弟要操作時，必須靠近對應部件按 E，在跳出的選單中選擇「檢查」或「操作」動作（例如：清潔光學元件、執行校正、確認數值等）。如果學弟問「怎麼做某個操作」，請告訴他去靠近哪個部件（雷射光源、照明系統、投影鏡組、晶圓載台等），按 E 後在選單選對應動作。不要叫他進行任何現實世界的物理操作。""",

            "standard": """你是一位經驗豐富的半導體設備現場學長，正在協助學弟處理設備故障。

教學風格：標準模式
- 適時引導，不直接給答案
- 偶爾反問：「你覺得呢？」「接下來打算怎麼做？」
- 肯定學弟的嘗試，鼓勵繼續深入
- 分享自己的現場經驗：「我之前遇過...」

【虛擬環境操作說明】這是 3D 虛擬訓練環境。學弟要操作時，必須靠近對應部件按 E，在跳出的選單中選擇「檢查」或「操作」動作（例如：清潔光學元件、執行校正、確認數值等）。如果學弟問「怎麼做某個操作」，請告訴他去靠近哪個部件（雷射光源、照明系統、投影鏡組、晶圓載台等），按 E 後在選單選對應動作。不要叫他進行任何現實世界的物理操作。""",

            "scaffolding": """你是一位經驗豐富的半導體設備現場學長，學弟目前需要更多引導。

教學風格：鷹架模式
- 把複雜步驟分解成小問題，一步一步引導
- 多提示：「你有沒有注意到控制面板上的 XX 數值？」
- 給選項幫助思考：「你覺得是 A 還是 B 比較有可能？」
- 肯定任何嘗試，降低焦慮感
- 說明「為什麼這個步驟重要」

【虛擬環境操作說明】這是 3D 虛擬訓練環境。學弟要操作時，必須靠近對應部件按 E，在跳出的選單中選擇「檢查」或「操作」動作（例如：清潔光學元件、執行校正、確認數值等）。如果學弟問「怎麼做某個操作」，請告訴他去靠近哪個部件（雷射光源、照明系統、投影鏡組、晶圓載台等），按 E 後在選單選對應動作。不要叫他進行任何現實世界的物理操作。""",

            "remedial": """你是一位耐心的半導體設備現場學長，學弟目前需要從基礎建立概念。

教學風格：補救模式
- 先確認最基本的概念有沒有問題
- 用類比解釋：「就像家裡的冷氣...」「想像水管...」
- 每次只講一個重點，不要同時給太多資訊
- 多鼓勵：「這個概念本來就不好懂，你問得很好」
- 檢查理解：「我說的這樣，你覺得對不對？」

【虛擬環境操作說明】這是 3D 虛擬訓練環境。學弟要操作時，必須靠近對應部件按 E，在跳出的選單中選擇「檢查」或「操作」動作（例如：清潔光學元件、執行校正、確認數值等）。如果學弟問「怎麼做某個操作」，請告訴他去靠近哪個部件（雷射光源、照明系統、投影鏡組、晶圓載台等），按 E 後在選單選對應動作。不要叫他進行任何現實世界的物理操作。"""
        }

        new_prompt = _PROMPTS.get(mode, _PROMPTS["standard"])
        self.ai_bot.system_prompt = new_prompt
        print(f"[Adaptive] AI 學長教學模式切換為：{mode}")

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
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(self.ai_bot.ask, full_question, True)
                response = future.result(timeout=15)

            # 清理回應格式
            response = response.strip()
            if response.startswith("[") and "]" in response:
                # 移除可能的 [學長] 標籤
                response = response[response.index("]")+1:].strip()

            return f"[學長] {response}"

        except Exception as e:
            print(f"[Error] AI 回應失敗/超時: {e}")
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
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(self.ai_bot.ask, prompt, False)
                response = future.result(timeout=10)
            response = response.strip()

            # 清理格式
            if response.startswith("[") and "]" in response:
                response = response[response.index("]")+1:].strip()

            # 限制長度
            if len(response) > 50:
                response = response[:47] + "..."

            return f"[學長] {response}"

        except Exception as e:
            print(f"[Error] AI 回饋失敗/超時: {e}")
            return None

    def provide_sop_wrong_feedback(self, component: str, action: str,
                                    fault_system: str, mistake_level: str,
                                    template_hint: str) -> Optional[str]:
        """
        當學員 SOP 操作錯誤時，依當前 teaching_mode 用 LLM 生成自然回饋。
        teaching_mode 已由 set_teaching_mode() 寫入 ai_bot.system_prompt。

        Args:
            component:     學員點選的零件
            action:        學員選擇的動作
            fault_system:  本次故障涉及的子系統
            mistake_level: 'partial_action' | 'partial_component' | 'full_wrong'
            template_hint: sop_definitions 產生的模板提示（作為參考，不要逐字複述）

        Returns:
            學長的自然語言回饋，或 None（降級用模板）
        """
        if not (self.use_ai and self.ai_bot):
            return None

        mistake_desc = {
            'partial_action':    f'零件選對了（{component}），但動作不太對',
            'partial_component': f'動作方向有點接近，但零件選錯了（選了 {component}）',
            'full_wrong':        f'零件（{component}）和動作（{action}）都偏離了',
        }.get(mistake_level, f'操作 {component} / {action} 不對')

        mode_instruction = {
            'challenge':   '你在挑戰模式。不要給答案，用反問讓他自己找出方向。一句話。',
            'standard':    '用標準引導語氣，暗示他方向但不說出正確答案。一到兩句。',
            'scaffolding': '學員需要協助。告訴他現在問題在哪個系統，引導他去對的地方，但不說出具體動作。兩句以內。',
            'remedial':    '學員很卡。明確告訴他應該去哪個子系統，因為什麼原因，語氣要鼓勵。兩到三句。',
        }.get(self.teaching_mode, '用標準引導語氣，不直接給答案。')

        prompt = f"""[情境] 故障系統：{fault_system}
[學員操作] {mistake_desc}
[模板提示參考]（不要逐字複述，只作為方向依據）：{template_hint}

{mode_instruction}
用台灣繁體中文，像學長跟學弟說話的口氣，不要加任何標籤或符號前綴。"""

        try:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(self.ai_bot.ask, prompt, False)
                response = future.result(timeout=15)
            response = response.strip()
            # 清除可能的角色標籤
            if response.startswith("[") and "]" in response:
                response = response[response.index("]")+1:].strip()
            return response if response else None
        except Exception as e:
            print(f"[Error] SOP wrong feedback LLM 失敗/超時: {e}")
            return None

    def generate_closing_question(self, fault_type: str, score: int) -> str:
        """
        故障排除完成後，依自適應模式生成一個反思問題，讓學員總結所學。
        """
        _CLOSING = {
            'alignment_drift': {
                'question': '你剛完成了對準系統的故障排除。回想一下，對準誤差超規最主要的連鎖影響是什麼？用自己的話說說看。',
                'keywords': ['overlay', '疊對', '良率', '短路', '斷路', '偏移', '精度'],
                'explanation': 'Overlay（疊對誤差）是核心影響：上下層電路圖案對不準，偏差過大就導致金屬層短路或 via 斷路，直接影響良率。DUV 製程要求 <3~5nm。'
            },
            'optical_contamination': {
                'question': '光學污染處理完了。你覺得光源強度下降，最直接影響的是哪個製程參數？為什麼？',
                'keywords': ['劑量', '曝光', '光阻', 'CD', '線寬', '圖案', '穿透率'],
                'explanation': '光源強度下降→到達光阻的曝光劑量不足→光阻反應不完全→顯影後殘留→CD偏大，圖案不清晰，影響良率。'
            },
            'cooling_failure': {
                'question': '冷卻問題解決了。溫度升高對鏡組最關鍵的影響是什麼？',
                'keywords': ['熱膨脹', '折射率', '溫度', '對準', '焦點', '解析度'],
                'explanation': '溫度升高→鏡組熱膨脹+折射率改變→光路偏移→焦點漂移、解析度下降，同時熱膨脹影響機械對準精度。'
            },
            'vacuum_leak': {
                'question': '真空洩漏修好了。你能說說，真空環境對曝光製程為什麼這麼重要嗎？',
                'keywords': ['污染', '微粒', '光學', '氣體', '折射', '穿透率'],
                'explanation': '真空防止空氣中微粒污染光學鏡面（降低穿透率）；也防止空氣折射率變化影響光路；同時避免 outgassing 沉積在鏡面。'
            },
        }
        info = _CLOSING.get(fault_type, {
            'question': f'故障排除完成了。回想整個過程，你覺得這次 {fault_type} 故障，最關鍵的診斷步驟是哪一個？為什麼？',
            'keywords': ['檢查', '確認', '異常', '系統', '數值'],
            'explanation': '有系統地從症狀→根因→處置，是故障排除的核心思路。'
        })

        if self.use_ai and self.ai_bot:
            mode_guide = {
                'challenge':   '用挑戰語氣，讓他深入分析機制，不給提示。',
                'standard':    '用引導語氣，讓他回顧關鍵概念。',
                'scaffolding': '用鼓勵語氣，給一點方向再讓他說。',
                'remedial':    '用鼓勵語氣，問一個最基礎的核心概念就好。',
            }.get(self.teaching_mode, '用引導語氣。')
            prompt = (
                f"故障類型：{fault_type}，學員得分：{score}分。\n"
                f"情境剛結束，請用學長口吻說一句收尾語（肯定完成），\n"
                f"再問一個反思問題（繁體中文，一句話，不要給答案）。\n"
                f"{mode_guide}"
            )
            try:
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=1) as ex:
                    q = ex.submit(self.ai_bot.ask, prompt, False).result(timeout=15)
                if q and q.strip():
                    return q.strip()
            except Exception:
                pass

        # fallback 固定問題
        return f"做得好，故障排除完成！最後問你一個問題：{info['question']}"

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
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(self.ai_bot.ask, prompt, True)
                    response = future.result(timeout=10)
                response = response.strip()

                if response.startswith("[") and "]" in response:
                    response = response[response.index("]")+1:].strip()

                return f"\n[學長] {response}\n"

            except Exception as e:
                print(f"[Error] AI 評論失敗/超時: {e}")

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
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(self.ai_bot.ask, context, False)
                response = future.result(timeout=10)
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
            print(f"[Warning] AI 理解輸入失敗/超時: {e}")
            return None

    def reset(self):
        """重置對話歷史"""
        self.conversation_history = []
        self.current_scenario_type = None
        self.action_count = 0

        if self.ai_bot and hasattr(self.ai_bot, 'reset_conversation'):
            self.ai_bot.reset_conversation()
