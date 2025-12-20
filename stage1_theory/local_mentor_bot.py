# -*- coding: utf-8 -*-
"""
本地 LLM 學長式理論導師 BOT (Local LLM Mentor Bot)
支援 Ollama 本地部署的 Qwen 或其他模型
完全離線運行，不需要 API key
"""

from typing import Dict, List, Tuple, Optional
import json
import requests
import os


class LocalMentorBot:
    """
    本地 LLM 學長式理論導師 BOT

    支援：
    1. Ollama (推薦) - 支援 Qwen, Llama, Mistral 等
    2. vLLM
    3. LM Studio

    特色：
    1. 完全本地運行，無需網路
    2. 免費，無 API 成本
    3. 資料隱私，不外傳
    4. 採用反問機制確認學員理解
    5. 對話風格輕鬆、親切，像學長帶學弟
    """

    def __init__(
        self,
        model_name: str = "qwen2.5:7b",
        ollama_url: str = "http://localhost:11434",
        use_ollama: bool = True
    ):
        """
        初始化本地 LLM 學長導師

        Args:
            model_name: 模型名稱 (例如 "qwen2.5:7b", "llama3:8b", "mistral:7b")
            ollama_url: Ollama API 地址
            use_ollama: 是否使用 Ollama (目前僅支援 Ollama)
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.use_ollama = use_ollama

        # 系統提示詞：定義學長的角色和教學風格（精簡版，加快回應）
        self.system_prompt = """你是半導體設備工程師學長，指導學弟。

風格：
- 親切自然，像學長帶學弟
- 用「欸」「啦」「你看」等口語
- 簡短回答（2-3句）+ 反問確認理解

範例：
「欸，CVD 就是化學氣相沉積啦！讓氣體在高溫下反應，在晶圓上『長』一層膜。我們產線常用 PECVD，溫度比較低。對了，你知道為什麼要在真空下進行嗎？」

記住：簡短、口語、反問。"""

        # 對話歷史
        self.conversation_history: List[Dict] = []

        # 檢查 Ollama 是否可用
        self._check_ollama_available()

    def _check_ollama_available(self) -> bool:
        """檢查 Ollama 是否正在運行"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]

                if self.model_name in model_names:
                    print(f"[OK] 找到本地模型: {self.model_name}")
                    return True
                else:
                    print(f"[Warning] 模型 {self.model_name} 未安裝")
                    print(f"[Info] 可用模型: {', '.join(model_names) if model_names else '無'}")
                    print(f"[Info] 安裝指令: ollama pull {self.model_name}")
                    return False
            return False
        except Exception as e:
            print(f"[Warning] 無法連接到 Ollama: {e}")
            print(f"[Info] 請確認 Ollama 是否已啟動")
            print(f"[Info] 下載地址: https://ollama.com/download")
            return False

    def ask(self, question: str, maintain_context: bool = True) -> str:
        """
        向學長提問

        Args:
            question: 學員的問題
            maintain_context: 是否維持對話歷史（預設 True）

        Returns:
            學長的回答（包含反問）
        """
        if not question.strip():
            return "欸，你有什麼想問的嗎？別客氣啦！"

        # 構建訊息
        messages = []

        # 添加歷史對話
        if maintain_context and self.conversation_history:
            messages.extend(self.conversation_history)

        # 添加當前問題
        user_message = {"role": "user", "content": question}
        messages.append(user_message)

        # 呼叫 Ollama API
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": self.system_prompt}
                    ] + messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,  # 稍微有點創意
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_predict": 150,  # 限制最大輸出長度，加快回應
                    }
                },
                timeout=15  # 降低 timeout 從 60 秒到 15 秒
            )

            if response.status_code == 200:
                result = response.json()
                answer = result["message"]["content"]

                # 更新對話歷史
                if maintain_context:
                    self.conversation_history.append(user_message)
                    self.conversation_history.append({"role": "assistant", "content": answer})

                    # 限制歷史長度（最多保留 10 輪對話）
                    if len(self.conversation_history) > 20:
                        self.conversation_history = self.conversation_history[-20:]

                return answer
            else:
                return f"欸，系統好像有點問題 (錯誤碼: {response.status_code})，你可以再問一次嗎？"

        except requests.exceptions.Timeout:
            return "欸，模型回應有點慢，可能是在思考比較複雜的問題，要不要換個簡單點的問法？"
        except Exception as e:
            print(f"[Error] 呼叫 Ollama 失敗: {e}")
            return "抱歉啦，系統暫時出了點問題，你可以稍後再試試看，或者先看看 SOP 文件！"

    def check_understanding(
        self,
        student_answer: str,
        expected_keywords: List[str]
    ) -> Tuple[bool, str]:
        """
        檢查學員回答是否理解

        Args:
            student_answer: 學員的回答
            expected_keywords: 預期應包含的關鍵詞

        Returns:
            (是否理解, 反饋訊息)
        """
        if not student_answer.strip():
            return False, "欸，你還沒回答欸！別害羞，試著說說看你的想法！"

        # 構建檢查提示
        check_prompt = f"""學弟剛剛的回答是：「{student_answer}」

請判斷他是否理解了概念。預期他的回答應該包含這些關鍵詞的其中幾個：{', '.join(expected_keywords)}

請用學長的口吻給予反饋：
1. 如果理解正確：鼓勵他，並進一步深入說明
2. 如果部分正確：肯定對的部分，補充不足的地方
3. 如果不太正確：溫和地指出問題，重新解釋

記得保持親切、鼓勵的態度！"""

        feedback = self.ask(check_prompt, maintain_context=False)

        # 簡單判斷是否理解（檢查是否提到關鍵詞）
        answer_lower = student_answer.lower()
        keywords_lower = [kw.lower() for kw in expected_keywords]
        matches = sum(1 for kw in keywords_lower if kw in answer_lower)

        understood = matches >= len(expected_keywords) * 0.5  # 至少對一半

        return understood, feedback

    def get_conversation_summary(self) -> str:
        """
        獲取對話摘要

        Returns:
            對話摘要文字
        """
        if not self.conversation_history:
            return "還沒有開始對話喔！"

        summary_prompt = """請幫我總結一下剛剛我們討論了哪些主題，以及學弟目前的理解程度。

格式：
## 討論主題
- [主題1]
- [主題2]

## 學習狀況
- 已理解：[內容]
- 需加強：[內容]

## 建議
[下一步學習建議]"""

        return self.ask(summary_prompt, maintain_context=False)

    def reset_conversation(self):
        """重置對話歷史"""
        self.conversation_history = []
        print("[Info] 對話已重置，開始新的學習話題")

    def get_model_info(self) -> Dict:
        """
        獲取當前模型資訊

        Returns:
            模型資訊字典
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/show",
                json={"name": self.model_name},
                timeout=5
            )

            if response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}


# ===== 便利函數 =====

def create_local_bot(model: str = "qwen2.5:7b") -> LocalMentorBot:
    """
    創建本地學長 BOT（快速初始化）

    Args:
        model: 模型名稱，可選：
               - "qwen2.5:7b" (推薦，中文好)
               - "qwen2.5:14b" (更強，需要更多記憶體)
               - "llama3.1:8b" (英文好，中文普通)
               - "mistral:7b" (速度快)

    Returns:
        LocalMentorBot 實例
    """
    return LocalMentorBot(model_name=model)


def test_local_bot():
    """測試本地 BOT 是否正常運作"""
    print("="*60)
    print("本地 LLM 學長 BOT 測試")
    print("="*60)

    bot = create_local_bot()

    # 測試問答
    print("\n[測試] 學員提問：什麼是 CVD？")
    answer = bot.ask("什麼是 CVD？")
    print(f"\n[學長回答]\n{answer}")

    print("\n" + "="*60)
    print("[測試完成]")
    print("="*60)


if __name__ == "__main__":
    # 執行測試
    test_local_bot()
