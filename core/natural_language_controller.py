# -*- coding: utf-8 -*-
"""
自然語言控制器 (Natural Language Controller)
解析學員的自然語言輸入，識別意圖並執行對應動作
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class NaturalLanguageController:
    """自然語言控制器 - 理解並執行學員的文字指令"""

    def __init__(self):
        """初始化 NLU 引擎"""

        # 意圖關鍵字字典
        self.intent_keywords = {
            "check": {
                "keywords": ["檢查", "查看", "看", "觀察", "確認", "測量", "讀取", "顯示"],
                "targets": {
                    "cooling": ["冷卻", "冷卻水", "水流", "流量", "冷卻系統"],
                    "temperature": ["溫度", "溫控", "熱", "加熱", "散熱"],
                    "vacuum": ["真空", "壓力", "氣壓", "真空度"],
                    "alignment": ["對準", "校正", "位置", "偏移", "對齊"],
                    "light": ["光", "光源", "強度", "照明", "曝光"],
                    "filter": ["過濾", "過濾網", "濾網", "濾心"],
                    "sensor": ["感測器", "sensor", "偵測器"],
                    "power": ["電力", "電源", "供電", "電壓", "電流"],
                }
            },
            "adjust": {
                "keywords": ["調整", "改變", "設定", "修改", "增加", "減少", "提高", "降低"],
                "targets": {
                    "cooling_flow": ["流量", "水流", "冷卻水"],
                    "temperature": ["溫度", "溫控"],
                    "vacuum": ["真空", "壓力"],
                    "light_intensity": ["光源", "強度", "曝光"],
                    "power": ["功率", "電力"],
                }
            },
            "replace": {
                "keywords": ["更換", "替換", "換", "安裝新的"],
                "targets": {
                    "filter": ["過濾網", "濾網", "過濾器"],
                    "sensor": ["感測器", "sensor"],
                    "part": ["零件", "部件", "元件"],
                }
            },
            "shutdown": {
                "keywords": ["停機", "關機", "停止", "關閉", "中止", "緊急停止"],
                "urgency": {
                    "emergency": ["緊急", "立即", "馬上"],
                    "normal": ["正常", "安全"]
                }
            },
            "restart": {
                "keywords": ["重啟", "重新啟動", "開機", "啟動", "重開"]
            },
            "calibrate": {
                "keywords": ["校正", "校準", "對準", "調校"],
                "targets": {
                    "alignment": ["對準", "位置", "座標"],
                    "sensor": ["感測器", "偵測器"]
                }
            },
            "clean": {
                "keywords": ["清潔", "清理", "擦拭", "清洗"],
                "targets": {
                    "lens": ["鏡頭", "鏡片", "透鏡", "光學"],
                    "chamber": ["腔體", "chamber"],
                }
            },
            "ask": {
                "keywords": ["為什麼", "怎麼", "如何", "原因", "幫忙", "建議", "專家", "請教"],
                "types": {
                    "cause": ["為什麼", "原因", "導致"],
                    "solution": ["怎麼辦", "如何", "怎麼做"],
                    "advice": ["建議", "意見", "專家"]
                }
            },
            "wait": {
                "keywords": ["等", "觀察", "先不", "再看看"]
            }
        }

        # 數值提取模式
        self.number_pattern = re.compile(r'(\d+\.?\d*)\s*(度|℃|°C|L/min|%|秒|分鐘)?')

    def parse_input(self, user_input: str) -> Dict:
        """
        解析學員輸入

        Args:
            user_input: 學員輸入的文字

        Returns:
            {
                "intent": "check/adjust/replace/shutdown/...",
                "target": "cooling/temperature/...",
                "parameters": {...},
                "confidence": 0.0-1.0,
                "raw_input": "..."
            }
        """
        user_input = user_input.strip()

        if not user_input:
            return self._create_result("unknown", None, {}, 0.0, user_input)

        # 識別意圖
        intent, confidence = self._identify_intent(user_input)

        # 識別目標
        target = self._identify_target(user_input, intent)

        # 提取參數
        parameters = self._extract_parameters(user_input, intent, target)

        return self._create_result(intent, target, parameters, confidence, user_input)

    def _identify_intent(self, text: str) -> Tuple[str, float]:
        """識別意圖"""
        text_lower = text.lower()

        # 計算每個意圖的匹配分數
        scores = {}

        for intent, config in self.intent_keywords.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword in text:
                    score += 1

            if score > 0:
                scores[intent] = score

        if not scores:
            return "unknown", 0.0

        # 找到最高分的意圖
        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]

        # 計算信心度
        confidence = min(max_score / 2.0, 1.0)

        return best_intent, confidence

    def _identify_target(self, text: str, intent: str) -> Optional[str]:
        """識別操作目標"""
        if intent not in self.intent_keywords:
            return None

        config = self.intent_keywords[intent]

        if "targets" not in config:
            return None

        # 檢查每個目標的關鍵字
        for target, keywords in config["targets"].items():
            for keyword in keywords:
                if keyword in text:
                    return target

        return None

    def _extract_parameters(self, text: str, intent: str, target: Optional[str]) -> Dict:
        """提取參數"""
        params = {}

        # 提取數值
        numbers = self.number_pattern.findall(text)
        if numbers:
            value, unit = numbers[0]
            params["value"] = float(value)
            if unit:
                params["unit"] = unit

        # 識別緊急程度（針對停機）
        if intent == "shutdown":
            if any(word in text for word in ["緊急", "立即", "馬上"]):
                params["urgency"] = "emergency"
            else:
                params["urgency"] = "normal"

        # 識別提問類型
        if intent == "ask":
            if "為什麼" in text or "原因" in text:
                params["question_type"] = "cause"
            elif "怎麼" in text or "如何" in text:
                params["question_type"] = "solution"
            else:
                params["question_type"] = "advice"

        return params

    def _create_result(self, intent: str, target: Optional[str],
                      parameters: Dict, confidence: float, raw_input: str) -> Dict:
        """建立解析結果"""
        return {
            "intent": intent,
            "target": target,
            "parameters": parameters,
            "confidence": confidence,
            "raw_input": raw_input,
            "timestamp": datetime.now().isoformat()
        }

    def validate_action(self, parsed_input: Dict, current_state: Dict) -> Tuple[bool, str]:
        """
        驗證動作是否可執行

        Args:
            parsed_input: 解析後的輸入
            current_state: 當前機台狀態

        Returns:
            (is_valid, message)
        """
        intent = parsed_input["intent"]
        target = parsed_input["target"]

        # 未知意圖
        if intent == "unknown":
            return False, "抱歉，我不太理解你的意思。請用更明確的指令，例如：「檢查冷卻水流量」"

        # 低信心度
        if parsed_input["confidence"] < 0.3:
            suggestions = self._get_suggestions(intent, target)
            return False, f"你是想要 {suggestions} 嗎？請說得更明確一點。"

        # 停機需要確認
        if intent == "shutdown" and not current_state.get("shutdown_confirmed"):
            return False, "warning_shutdown"

        # 需要先停機才能執行的動作
        if intent == "replace" and current_state.get("is_running"):
            return False, "更換零件前需要先停機。請先執行停機程序。"

        return True, "OK"

    def _get_suggestions(self, intent: str, target: Optional[str]) -> str:
        """生成建議"""
        if intent == "check":
            return "檢查某個系統或參數"
        elif intent == "adjust":
            return "調整某個參數"
        elif intent == "replace":
            return "更換某個零件"
        else:
            return "執行某個操作"

    def generate_action_description(self, parsed_input: Dict) -> str:
        """生成動作描述（用於日誌）"""
        intent = parsed_input["intent"]
        target = parsed_input["target"]
        params = parsed_input["parameters"]

        intent_names = {
            "check": "檢查",
            "adjust": "調整",
            "replace": "更換",
            "shutdown": "停機",
            "restart": "重啟",
            "calibrate": "校正",
            "clean": "清潔",
            "ask": "詢問",
            "wait": "等待觀察"
        }

        target_names = {
            "cooling": "冷卻系統",
            "temperature": "溫度",
            "vacuum": "真空系統",
            "alignment": "對準系統",
            "light": "光源",
            "filter": "過濾網",
            "sensor": "感測器",
            "cooling_flow": "冷卻水流量",
            "light_intensity": "光源強度",
        }

        action = intent_names.get(intent, intent)
        target_name = target_names.get(target, target) if target else ""

        if params.get("value"):
            return f"{action}{target_name}至 {params['value']}{params.get('unit', '')}"
        else:
            return f"{action}{target_name}"


class ActionExecutor:
    """動作執行引擎 - 執行學員的指令並返回結果"""

    def __init__(self, digital_twin):
        """
        初始化執行引擎

        Args:
            digital_twin: 數位孿生實例
        """
        self.digital_twin = digital_twin
        self.action_history = []

    def execute(self, parsed_input: Dict, current_state: Dict) -> Dict:
        """
        執行動作

        Args:
            parsed_input: NLU 解析結果
            current_state: 當前狀態

        Returns:
            {
                "success": True/False,
                "message": "自然語言描述",
                "state_changes": {...},
                "observations": [...],
                "warnings": [...]
            }
        """
        intent = parsed_input["intent"]

        # 根據意圖執行對應動作
        if intent == "check":
            return self._execute_check(parsed_input, current_state)
        elif intent == "adjust":
            return self._execute_adjust(parsed_input, current_state)
        elif intent == "replace":
            return self._execute_replace(parsed_input, current_state)
        elif intent == "shutdown":
            return self._execute_shutdown(parsed_input, current_state)
        elif intent == "restart":
            return self._execute_restart(parsed_input, current_state)
        elif intent == "calibrate":
            return self._execute_calibrate(parsed_input, current_state)
        elif intent == "clean":
            return self._execute_clean(parsed_input, current_state)
        elif intent == "wait":
            return self._execute_wait(parsed_input, current_state)
        else:
            return self._create_result(False, "無法執行此動作", {}, [], [])

    def _execute_check(self, parsed_input: Dict, current_state: Dict) -> Dict:
        """執行檢查動作"""
        target = parsed_input["target"]

        observations = []
        warnings = []

        if target == "cooling":
            flow = current_state.get("cooling_flow", 5.0)
            pressure = current_state.get("cooling_pressure", 2.5)
            filter_status = current_state.get("filter_blocked", False)

            observations.append(f"冷卻水流量計顯示：{flow:.1f} L/min（正常範圍：4.5-5.5）")
            observations.append(f"管路壓力：{pressure:.1f} bar")

            if filter_status:
                observations.append("過濾器指示燈：[紅色] 堵塞警告")
                warnings.append("過濾器可能需要更換")
            else:
                observations.append("過濾器指示燈：[綠色] 正常")

            if flow < 4.0:
                warnings.append("流量偏低，可能影響散熱效果")

            message = "[檢查冷卻水系統]\n" + "\n".join(observations)

        elif target == "temperature":
            temp = current_state.get("lens_temp", 23.0)
            temp_trend = current_state.get("temp_trend", "stable")

            observations.append(f"鏡頭溫度：{temp:.1f}°C（正常：22-24°C）")

            if temp_trend == "rising":
                observations.append("溫度趨勢：[上升中] ↑↑↑")
                warnings.append("溫度持續上升，需盡快處理")
            elif temp_trend == "falling":
                observations.append("溫度趨勢：[下降中] ↓↓↓")
            else:
                observations.append("溫度趨勢：[穩定]")

            message = "[檢查溫度]\n" + "\n".join(observations)

        elif target == "vacuum":
            pressure = current_state.get("vacuum_pressure", 1e-6)
            leak_detected = current_state.get("vacuum_leak", False)

            observations.append(f"真空壓力：{pressure:.2e} Torr（標準：1e-6）")

            if leak_detected:
                observations.append("氦氣偵測：[檢測到洩漏] ⚠")
                warnings.append("真空系統有洩漏，需要檢修")
            else:
                observations.append("氦氣偵測：[無洩漏]")

            message = "[檢查真空系統]\n" + "\n".join(observations)

        elif target == "filter":
            filter_blocked = current_state.get("filter_blocked", False)
            last_replace = current_state.get("filter_last_replace", "3個月前")

            observations.append(f"過濾網狀態：{'堵塞' if filter_blocked else '正常'}")
            observations.append(f"上次更換時間：{last_replace}")

            if filter_blocked:
                warnings.append("過濾網已堵塞，建議立即更換")

            message = "[檢查過濾網]\n" + "\n".join(observations)

        else:
            message = f"[檢查{target}]\n目前狀態正常"
            observations.append("所有參數在正常範圍內")

        return self._create_result(True, message, {}, observations, warnings)

    def _execute_adjust(self, parsed_input: Dict, current_state: Dict) -> Dict:
        """執行調整動作"""
        target = parsed_input["target"]
        params = parsed_input["parameters"]

        message = f"[調整{target}]\n"
        state_changes = {}
        observations = []
        warnings = []

        if target == "cooling_flow":
            new_value = params.get("value", current_state.get("cooling_flow", 5.0) * 1.1)
            old_value = current_state.get("cooling_flow", 5.0)

            state_changes["cooling_flow"] = new_value

            observations.append(f"調整前：{old_value:.1f} L/min")
            observations.append(f"調整後：{new_value:.1f} L/min")

            if new_value > 6.0:
                warnings.append("流量過高可能造成壓力異常")

            message += "\n".join(observations)
            message += "\n\n[等待系統穩定...] ▓▓▓░░░░░░░ 30%"

        else:
            message += f"正在調整 {target}..."
            observations.append("調整完成")

        return self._create_result(True, message, state_changes, observations, warnings)

    def _execute_replace(self, parsed_input: Dict, current_state: Dict) -> Dict:
        """執行更換動作"""
        target = parsed_input["target"]

        if current_state.get("is_running", True):
            return self._create_result(
                False,
                "錯誤：機台運行中無法更換零件\n請先執行停機程序",
                {}, [], ["需要先停機"]
            )

        message = f"[更換{target}]\n"
        observations = []
        state_changes = {}

        if target == "filter":
            observations.append("1. 關閉冷卻水閥門... ✓")
            observations.append("2. 卸下舊過濾網... ✓")
            observations.append("3. 安裝新過濾網... ✓")
            observations.append("4. 開啟冷卻水閥門... ✓")
            observations.append("5. 檢查是否洩漏... ✓")

            state_changes["filter_blocked"] = False
            state_changes["filter_last_replace"] = "剛剛"
            state_changes["cooling_flow"] = 5.0

            message += "\n".join(observations)
            message += "\n\n✓ 更換完成！冷卻水流量已恢復正常。"

        return self._create_result(True, message, state_changes, observations, [])

    def _execute_shutdown(self, parsed_input: Dict, current_state: Dict) -> Dict:
        """執行停機"""
        urgency = parsed_input["parameters"].get("urgency", "normal")

        message = "[執行停機程序]\n"
        observations = []
        state_changes = {"is_running": False, "shutdown_time": datetime.now().isoformat()}

        if urgency == "emergency":
            observations.append("!! 緊急停機 !!")
            observations.append("1. 立即切斷曝光光源... ✓")
            observations.append("2. 關閉所有氣體供應... ✓")
            observations.append("3. 啟動緊急排氣... ✓")
            message += "\n".join(observations)
            message += "\n\n!! 緊急停機完成"
        else:
            observations.append("1. 通知產線主管... ✓")
            observations.append("2. 保存當前製程數據... ✓")
            observations.append("3. 完成當前晶圓曝光... ✓")
            observations.append("4. 安全關閉曝光光源... ✓")
            observations.append("5. 降低真空度... ✓")
            observations.append("6. 系統進入待機模式... ✓")
            message += "\n".join(observations)
            message += "\n\n✓ 安全停機完成，可以進行維護作業"

        return self._create_result(True, message, state_changes, observations, [])

    def _execute_restart(self, parsed_input: Dict, current_state: Dict) -> Dict:
        """執行重啟"""
        message = "[重新啟動系統]\n"
        observations = [
            "1. 系統自檢... ✓",
            "2. 啟動真空泵... ✓",
            "3. 真空度達標... ✓",
            "4. 啟動冷卻系統... ✓",
            "5. 光源預熱... ▓▓▓▓▓░░░░░ 50%",
            "6. 載入製程參數... ⏳"
        ]

        state_changes = {"is_running": True, "restart_time": datetime.now().isoformat()}

        message += "\n".join(observations)
        message += "\n\n預計 5 分鐘後可恢復生產"

        return self._create_result(True, message, state_changes, observations, [])

    def _execute_calibrate(self, parsed_input: Dict, current_state: Dict) -> Dict:
        """執行校正"""
        target = parsed_input["target"]

        message = f"[執行校正 - {target}]\n"
        observations = [
            "正在執行自動校正程序...",
            "校正完成 ✓"
        ]

        state_changes = {}
        if target == "alignment":
            state_changes["alignment_error_x"] = 0.0
            state_changes["alignment_error_y"] = 0.0

        message += "\n".join(observations)

        return self._create_result(True, message, state_changes, observations, [])

    def _execute_clean(self, parsed_input: Dict, current_state: Dict) -> Dict:
        """執行清潔"""
        target = parsed_input["target"]

        message = f"[清潔{target}]\n"
        observations = [
            "使用專用清潔工具進行清潔...",
            "清潔完成 ✓"
        ]

        state_changes = {}
        if target == "lens":
            state_changes["lens_contamination"] = 0.0

        message += "\n".join(observations)

        return self._create_result(True, message, state_changes, observations, [])

    def _execute_wait(self, parsed_input: Dict, current_state: Dict) -> Dict:
        """執行等待觀察"""
        message = "[持續觀察中...]\n"
        observations = ["保持當前狀態，持續監控參數變化"]

        return self._create_result(True, message, {}, observations,
                                   ["注意：如果問題持續惡化，需要立即採取行動"])

    def _create_result(self, success: bool, message: str,
                       state_changes: Dict, observations: List[str],
                       warnings: List[str]) -> Dict:
        """建立執行結果"""
        result = {
            "success": success,
            "message": message,
            "state_changes": state_changes,
            "observations": observations,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }

        self.action_history.append(result)

        return result
