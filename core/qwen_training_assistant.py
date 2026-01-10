# -*- coding: utf-8 -*-
"""
Qwen 2.5 訓練助手整合模組
整合您原有的 Qwen 2.5 3B Instruct LLM 系統到半導體訓練平台
"""

import torch
import time
from typing import Dict, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


class QwenTrainingAssistant:
    """
    使用 Qwen 2.5 3B Instruct 的訓練助手
    整合到半導體設備故障處理訓練系統
    """

    def __init__(self, model_name: str = "Qwen/Qwen2.5-3B-Instruct", use_quantization: bool = True):
        """
        初始化 Qwen 訓練助手

        Args:
            model_name: 模型名稱
            use_quantization: 是否使用 4-bit 量化（節省記憶體）
        """
        self.model_name = model_name
        self.use_quantization = use_quantization
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # 訓練統計
        self.stats = {
            'questions_asked': 0,
            'answers_given': 0,
            'session_start': time.time(),
            'total_tokens_generated': 0,
            'average_response_time': 0
        }

        # 對話歷史
        self.conversation_history = []

        print(f"[Init] Qwen 訓練助手")
        print(f"  - 模型: {model_name}")
        print(f"  - 設備: {self.device}")
        print(f"  - 量化: {'啟用' if use_quantization else '停用'}")

    def load_model(self):
        """載入 Qwen 模型"""
        print(f"\n[Loading] 載入 Qwen 模型...")
        start_time = time.time()

        try:
            # 載入 tokenizer
            print("  - 載入 tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # 量化配置
            quantization_config = None
            if self.use_quantization and self.device == "cuda":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )

            # 載入模型
            print("  - 載入模型...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )

            if self.device == "cpu":
                self.model = self.model.to("cpu")

            load_time = time.time() - start_time

            print(f"\n[OK] 模型載入成功！用時: {load_time:.1f} 秒")

            # 顯示記憶體使用
            if self.device == "cuda":
                allocated = torch.cuda.memory_allocated(0) / 1024**3
                print(f"[Info] GPU 記憶體使用: {allocated:.2f} GB")

            return True

        except Exception as e:
            print(f"[Error] 模型載入失敗: {e}")
            return False

    def generate_answer(
        self,
        question: str,
        context: Optional[Dict] = None,
        max_length: int = 512,
        temperature: float = 0.7
    ) -> Dict:
        """
        生成回答（針對半導體設備故障處理情境）

        Args:
            question: 新人問題
            context: 情境上下文（設備狀態、故障資訊等）
            max_length: 最大生成長度
            temperature: 生成溫度

        Returns:
            包含回答和統計資訊的字典
        """
        if self.model is None or self.tokenizer is None:
            return {
                'answer': '模型尚未載入，請先執行 load_model()',
                'generation_time': 0,
                'tokens_per_second': 0
            }

        # 構建情境化 prompt
        prompt = self._build_scenario_prompt(question, context)

        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        )

        if self.device == "cuda":
            inputs = inputs.to("cuda")

        # 生成
        start_time = time.time()

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=temperature,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        gen_time = time.time() - start_time

        # 解碼
        generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
        answer = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

        # 統計
        tokens_generated = len(generated_ids)
        tokens_per_sec = tokens_generated / gen_time if gen_time > 0 else 0

        self.stats['answers_given'] += 1
        self.stats['total_tokens_generated'] += tokens_generated

        # 更新平均響應時間
        total_answers = self.stats['answers_given']
        self.stats['average_response_time'] = (
            (self.stats['average_response_time'] * (total_answers - 1) + gen_time) / total_answers
        )

        # 加入對話歷史
        self.conversation_history.append({
            'role': 'user',
            'content': question
        })
        self.conversation_history.append({
            'role': 'assistant',
            'content': answer.strip()
        })

        return {
            'answer': answer.strip(),
            'generation_time': gen_time,
            'tokens_per_second': tokens_per_sec,
            'tokens_generated': tokens_generated
        }

    def _build_scenario_prompt(self, question: str, context: Optional[Dict] = None) -> str:
        """
        構建情境化 prompt（針對設備故障處理）

        Args:
            question: 問題
            context: 情境上下文

        Returns:
            完整的 prompt
        """
        # 基礎系統提示詞
        system_prompt = """你是一位經驗豐富的半導體設備現場學長，正在協助新進工程師處理設備故障。

你的角色特點：
1. **像學長，不像老師**：用輕鬆、自然的口吻，不要太正式
2. **邊做邊聊**：就像一起在現場處理問題，自然地給建議
3. **適時引導**：不直接給答案，而是引導思考方向
4. **鼓勵嘗試**：對學弟的想法給予肯定，即使不完全正確也先鼓勵
5. **分享經驗**：會說「我之前遇到過...」「通常這種情況...」這類經驗談

對話風格：
- 使用「你看一下...」「我們先...」「試試...」這類口語
- 適時用「嗯」「對」「沒錯」等語助詞
- 回答簡潔（2-3 句話為主），不要長篇大論
- 用實際例子說明，而非理論"""

        # 加入情境資訊
        context_info = ""
        if context:
            context_info = "\n\n【當前情境】\n"
            if 'scenario_name' in context:
                context_info += f"故障場景: {context['scenario_name']}\n"
            if 'equipment_state' in context:
                context_info += f"設備狀態: {context['equipment_state']}\n"
            if 'fault_stage' in context:
                context_info += f"故障階段: Stage {context['fault_stage']}\n"
            if 'parameters' in context:
                context_info += f"異常參數: {context['parameters']}\n"

        # 組合 prompt
        prompt = f"""{system_prompt}
{context_info}

新人問題：{question}

學長回答："""

        return prompt

    def generate_follow_up(self, question: str, answer: str) -> str:
        """
        生成反問問題（檢驗理解）

        Args:
            question: 原始問題
            answer: 系統回答

        Returns:
            反問問題
        """
        if self.model is None or self.tokenizer is None:
            return "你理解了嗎？"

        prompt = f"""你是培訓學長，剛才回答了新人的問題。現在要反問一個問題來檢驗他們是否真正理解。

原始問題：{question}

你的回答：{answer}

請生成一個簡短的反問問題（一句話），用於檢驗理解程度："""

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        )

        if self.device == "cuda":
            inputs = inputs.to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.8,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        follow_up = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        ).strip()

        self.stats['questions_asked'] += 1

        return follow_up

    def evaluate_response(self, follow_up_q: str, trainee_answer: str) -> Dict:
        """
        評估新人回答

        Args:
            follow_up_q: 反問的問題
            trainee_answer: 新人的回答

        Returns:
            評估結果（分數和反饋）
        """
        if self.model is None or self.tokenizer is None:
            return {'score': 5, 'feedback': '請先載入模型'}

        if not trainee_answer or len(trainee_answer.strip()) < 5:
            return {
                'score': 0,
                'feedback': '回答太簡短，請提供更詳細的說明。'
            }

        prompt = f"""你是培訓學長，需要評估新人的回答。

問題：{follow_up_q}

新人回答：{trainee_answer}

請簡短評估（1-2句話）：
1. 回答是否理解了核心概念
2. 給予建設性反饋

評估："""

        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True)

        if self.device == "cuda":
            inputs = inputs.to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=150,
                temperature=0.5,
                top_p=0.9,
                do_sample=True
            )

        evaluation = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        ).strip()

        # 簡單評分（根據回答長度和關鍵字）
        score = min(10, len(trainee_answer.split()) / 2)

        return {
            'score': score,
            'feedback': evaluation
        }

    def get_stats(self) -> Dict:
        """獲取訓練統計"""
        session_duration = time.time() - self.stats['session_start']
        minutes = int(session_duration / 60)

        return {
            'session_duration': f"{minutes} 分鐘",
            'questions_asked': self.stats['questions_asked'],
            'answers_given': self.stats['answers_given'],
            'total_tokens': self.stats['total_tokens_generated'],
            'avg_response_time': f"{self.stats['average_response_time']:.2f} 秒"
        }

    def clear_history(self):
        """清除對話歷史"""
        self.conversation_history = []
        print("[Info] 對話歷史已清除")

    def reset_stats(self):
        """重置統計資訊"""
        self.stats = {
            'questions_asked': 0,
            'answers_given': 0,
            'session_start': time.time(),
            'total_tokens_generated': 0,
            'average_response_time': 0
        }
        print("[Info] 統計資訊已重置")
