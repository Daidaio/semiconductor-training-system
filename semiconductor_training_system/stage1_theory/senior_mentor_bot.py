# -*- coding: utf-8 -*-
"""
學長式理論導師 BOT (Senior Mentor Bot)
採用蘇格拉底式教學法，透過反問確認理解，像學長帶學弟一樣自然對話
"""

from typing import Dict, List, Tuple, Optional
import anthropic
import os


class SeniorMentorBot:
    """
    學長式理論導師 BOT

    特色：
    1. 使用 Claude API 進行自然對話
    2. 採用反問機制確認學員理解
    3. 對話風格輕鬆、親切，像學長帶學弟
    4. 根據學員回答調整教學深度
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化學長式導師 BOT

        Args:
            api_key: Anthropic API key（可選，若無則從環境變數讀取）
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError(
                "請設置 ANTHROPIC_API_KEY 環境變數或傳入 api_key 參數\n"
                "取得 API key: https://console.anthropic.com/"
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)

        # 系統提示詞：定義學長的角色和教學風格
        self.system_prompt = """你是一位經驗豐富的半導體設備工程師學長，正在指導剛進公司的學弟妹。

## 你的角色特質
- **親切自然**：像學長帶學弟一樣輕鬆對話，不要太正式或死板
- **耐心細心**：新人什麼都不懂很正常，要有耐心慢慢教
- **實務導向**：多舉實際工作的例子，不要只講理論
- **確認理解**：用反問的方式確認學弟是否真的懂了

## 教學方法（蘇格拉底式）
1. **先回答問題**：清楚解釋概念，用簡單的話說明
2. **舉實際例子**：連結到真實設備操作情境
3. **反問確認**：問1-2個問題確認理解（重要！）
4. **引導思考**：不直接給答案，引導他們思考

## 對話風格範例

❌ 不好的回答（太正式、太教科書）：
「CVD（Chemical Vapor Deposition）是一種化學氣相沉積技術，利用化學反應在基材表面形成薄膜。主要分為PECVD、LPCVD、APCVD等類型。」

✅ 好的回答（學長風格）：
「欸，CVD 其實就是化學氣相沉積啦！簡單說，就是讓氣體在高溫下產生化學反應，然後在晶圓表面長出一層薄膜。

你可以想像成... 嗯，就像在玻璃上呼一口氣會起霧，但我們是用化學反應讓它形成均勻的薄膜。

我們產線上最常用的是 PECVD，因為它可以在比較低的溫度下操作，對晶圓比較不傷。

對了，你知道為什麼要控制溫度嗎？或者說，你覺得溫度太高會怎樣？」

## 重要規則
1. **一定要反問**：每次回答後至少問1個問題確認理解
2. **用口語化表達**：「啦」「欸」「嗯」「對啊」等語助詞要自然使用
3. **舉例說明**：盡量用產線實際案例
4. **鼓勵為主**：多說「不錯喔」「對對對」「很好的問題」
5. **承認不確定**：如果不確定，可以說「這個我也不是很確定，我們一起查查」

## 半導體設備知識範圍
- CVD/PVD 設備
- 真空系統
- 溫度控制
- 壓力控制
- 冷卻系統
- 對準系統
- 光學系統
- 安全規範和 SOP

記住：你是學長，不是教授！要讓學弟覺得親切、願意發問。"""

        # 對話歷史（用於維持上下文）
        self.conversation_history: List[Dict] = []

    def ask(self, question: str, maintain_context: bool = True) -> str:
        """
        向學長提問

        Args:
            question: 學員的問題
            maintain_context: 是否維持對話上下文

        Returns:
            學長的回答（包含反問）
        """
        # 將問題加入對話歷史
        if maintain_context:
            self.conversation_history.append({
                "role": "user",
                "content": question
            })
        else:
            # 不維持上下文，清空歷史
            self.conversation_history = [{
                "role": "user",
                "content": question
            }]

        try:
            # 呼叫 Claude API
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",  # 使用 Sonnet 3.5
                max_tokens=1024,
                system=self.system_prompt,
                messages=self.conversation_history
            )

            # 提取回答
            answer = response.content[0].text

            # 將回答加入歷史
            if maintain_context:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": answer
                })

            return answer

        except anthropic.APIError as e:
            return f"抱歉，系統出了點問題：{str(e)}\n\n你可以再問一次，或者我們換個方式討論～"

    def check_understanding(self, student_answer: str, expected_keywords: List[str]) -> Tuple[bool, str]:
        """
        檢查學員對反問的回答，判斷是否理解

        Args:
            student_answer: 學員的回答
            expected_keywords: 期望的關鍵字列表

        Returns:
            (是否理解, 反饋訊息)
        """
        # 使用 Claude 判斷理解程度
        check_prompt = f"""學弟剛才回答了：「{student_answer}」

請判斷他是否理解了概念。期望的關鍵概念包括：{', '.join(expected_keywords)}

請用學長的口吻給予反饋：
- 如果理解正確：給予肯定和鼓勵，可以深入一點
- 如果部分理解：指出對的地方，引導思考錯的部分
- 如果不理解：換個方式重新解釋，舉更簡單的例子

你的反饋（直接回答，不要前綴）："""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                system=self.system_prompt,
                messages=[{"role": "user", "content": check_prompt}]
            )

            feedback = response.content[0].text

            # 簡單判斷是否理解（檢查關鍵字）
            answer_lower = student_answer.lower()
            understood = any(keyword.lower() in answer_lower for keyword in expected_keywords)

            return understood, feedback

        except anthropic.APIError as e:
            return False, f"嗯... 系統有點問題，但沒關係！我們繼續聊～"

    def reset_conversation(self):
        """重置對話歷史"""
        self.conversation_history = []

    def get_conversation_summary(self) -> str:
        """獲取對話摘要"""
        if not self.conversation_history:
            return "目前還沒有對話記錄"

        summary_prompt = "請簡單總結一下我們剛才討論了哪些主題，學弟學到了什麼？（3-5句話）"

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=256,
                system=self.system_prompt,
                messages=self.conversation_history + [{
                    "role": "user",
                    "content": summary_prompt
                }]
            )

            return response.content[0].text

        except anthropic.APIError as e:
            return "總結生成失敗"


# 使用範例
if __name__ == "__main__":
    print("=== 學長式理論導師 BOT 測試 ===\n")

    # 檢查 API key
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("⚠️ 請先設置 ANTHROPIC_API_KEY 環境變數")
        print("Windows: set ANTHROPIC_API_KEY=your-api-key")
        print("Linux/Mac: export ANTHROPIC_API_KEY=your-api-key")
        print()
        print("或直接在程式中設置：")
        print("bot = SeniorMentorBot(api_key='your-api-key')")
        exit(1)

    # 創建學長 BOT
    bot = SeniorMentorBot(api_key=api_key)

    print("學長 BOT 已上線！輸入 'quit' 結束對話\n")
    print("=" * 60)

    while True:
        # 學員提問
        question = input("\n你: ")

        if question.lower() in ['quit', 'exit', '結束', '退出']:
            # 生成對話摘要
            print("\n" + "=" * 60)
            print("\n學長: 好的！我們今天就聊到這～")
            print("\n📝 對話摘要：")
            print(bot.get_conversation_summary())
            print("\n有問題隨時再來找我！加油💪")
            break

        if not question.strip():
            continue

        # 獲取學長回答
        print("\n學長: ", end="")
        answer = bot.ask(question)
        print(answer)

        # 如果學長問了問題，等待學員回答
        if "？" in answer or "?" in answer:
            print("\n（學長在等你回答...）")

