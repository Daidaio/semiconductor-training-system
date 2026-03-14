# -*- coding: utf-8 -*-
"""
Qwen Mentor Bot - 使用 Qwen 2.5 的學長導師
整合 Qwen 2.5 3B Instruct 到訓練系統
"""

import sys
import os
from typing import Dict, List, Optional

# 導入 Qwen 訓練助手
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.qwen_training_assistant import QwenTrainingAssistant


class QwenMentorBot:
    """
    使用 Qwen 2.5 的學長導師 Bot
    提供半導體設備故障處理的情境引導
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-3B-Instruct",
        use_quantization: bool = True,
        auto_load: bool = True
    ):
        """
        初始化 Qwen Mentor Bot

        Args:
            model_name: Qwen 模型名稱
            use_quantization: 是否使用量化（節省記憶體）
            auto_load: 是否自動載入模型
        """
        self.model_name = model_name
        self.assistant = QwenTrainingAssistant(
            model_name=model_name,
            use_quantization=use_quantization
        )

        self.is_ready = False

        if auto_load:
            self.is_ready = self.assistant.load_model()

    def ask(
        self,
        question: str,
        context: Optional[Dict] = None,
        include_history: bool = True
    ) -> str:
        """
        向學長詢問問題

        Args:
            question: 問題內容
            context: 情境上下文（設備狀態、故障資訊）
            include_history: 是否包含對話歷史

        Returns:
            學長的回答
        """
        if not self.is_ready:
            return "抱歉，AI 學長還在準備中，請稍後再試。"

        # 生成回答
        result = self.assistant.generate_answer(
            question=question,
            context=context,
            max_length=512,
            temperature=0.7
        )

        return result['answer']

    def get_response_with_stats(
        self,
        question: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        獲取回答及統計資訊

        Args:
            question: 問題
            context: 情境上下文

        Returns:
            包含回答和統計的字典
        """
        if not self.is_ready:
            return {
                'answer': "AI 學長尚未準備好",
                'generation_time': 0,
                'tokens_per_second': 0
            }

        return self.assistant.generate_answer(
            question=question,
            context=context
        )

    def generate_follow_up_question(
        self,
        original_question: str,
        answer: str
    ) -> str:
        """
        生成反問問題（檢驗理解）

        Args:
            original_question: 原始問題
            answer: 學長的回答

        Returns:
            反問問題
        """
        if not self.is_ready:
            return "你理解了嗎？"

        return self.assistant.generate_follow_up(original_question, answer)

    def evaluate_trainee_answer(
        self,
        question: str,
        trainee_answer: str
    ) -> Dict:
        """
        評估學員的回答

        Args:
            question: 問題
            trainee_answer: 學員的回答

        Returns:
            評估結果（分數和反饋）
        """
        if not self.is_ready:
            return {
                'score': 0,
                'feedback': 'AI 學長尚未準備好'
            }

        return self.assistant.evaluate_response(question, trainee_answer)

    def clear_conversation_history(self):
        """清除對話歷史"""
        if self.assistant:
            self.assistant.clear_history()

    def get_training_stats(self) -> Dict:
        """獲取訓練統計"""
        if self.assistant:
            return self.assistant.get_stats()
        return {}

    def is_available(self) -> bool:
        """檢查 Bot 是否可用"""
        return self.is_ready

    def __del__(self):
        """清理資源"""
        # 清理 GPU 記憶體
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass
