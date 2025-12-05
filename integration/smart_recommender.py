# -*- coding: utf-8 -*-
"""
智能推薦器 (Smart Recommender)
分析學員實作中的錯誤，識別知識盲點，推薦理論複習主題
"""

from typing import Dict, List, Optional, Set
from collections import defaultdict, Counter
import json
from pathlib import Path


class SmartRecommender:
    """
    智能推薦器

    職責：
    1. 分析實作操作失敗原因
    2. 識別知識盲點
    3. 推薦理論複習主題
    4. 生成個性化學習路徑

    使用範例：
    ```python
    recommender = SmartRecommender()

    # 分析失敗操作
    failed_ops = [
        {"operation": "檢查冷卻水流量", "topic": "冷卻系統"},
        {"operation": "調整真空壓力", "topic": "真空系統"}
    ]

    # 獲取推薦
    recommendations = recommender.analyze_and_recommend(failed_ops, knowledge_gaps)
    ```
    """

    # 操作類型到理論主題的映射
    OPERATION_TOPIC_MAPPING = {
        # 冷卻系統相關
        "冷卻": {
            "topics": ["冷卻系統原理", "熱管理基礎", "過濾網維護", "冷卻液循環"],
            "priority": "high",
            "keywords": ["冷卻", "降溫", "散熱", "水流", "風扇", "溫度過高"]
        },

        # 真空系統相關
        "真空": {
            "topics": ["真空系統原理", "真空泵操作", "洩漏檢測", "真空度控制"],
            "priority": "high",
            "keywords": ["真空", "壓力", "抽氣", "洩漏", "真空泵", "真空度"]
        },

        # 對準系統相關
        "對準": {
            "topics": ["對準系統原理", "機械穩定性", "振動控制", "精密定位"],
            "priority": "medium",
            "keywords": ["對準", "定位", "偏移", "精度", "校準", "振動"]
        },

        # 光學系統相關
        "光學": {
            "topics": ["光學系統原理", "鏡片清潔維護", "光源管理", "光路調整"],
            "priority": "high",
            "keywords": ["光學", "鏡片", "透鏡", "光源", "聚焦", "光路"]
        },

        # 溫度控制相關
        "溫度": {
            "topics": ["溫控系統原理", "熱平衡原理", "溫度感測器", "PID控制"],
            "priority": "high",
            "keywords": ["溫度", "溫控", "加熱", "恆溫", "熱平衡", "溫度波動"]
        },

        # 壓力控制相關
        "壓力": {
            "topics": ["壓力控制原理", "氣體供應系統", "壓力感測器", "壓力調節"],
            "priority": "medium",
            "keywords": ["壓力", "氣壓", "調壓", "壓力表", "氣體", "壓力波動"]
        },

        # 化學相關
        "化學": {
            "topics": ["CVD原理", "化學反應", "氣體化學", "沉積機制"],
            "priority": "medium",
            "keywords": ["化學", "反應", "氣體", "cvd", "沉積", "化學品"]
        },

        # 電氣相關
        "電氣": {
            "topics": ["電氣系統原理", "電源管理", "接地與安全", "電氣故障排除"],
            "priority": "low",
            "keywords": ["電氣", "電源", "電壓", "電流", "短路", "斷路"]
        },

        # 機械相關
        "機械": {
            "topics": ["機械結構", "傳動系統", "潤滑維護", "機械故障診斷"],
            "priority": "low",
            "keywords": ["機械", "馬達", "軸承", "傳動", "卡住", "摩擦"]
        },

        # 安全與緊急處理
        "安全": {
            "topics": ["安全規範", "緊急停機程序", "SOP標準", "風險評估"],
            "priority": "critical",
            "keywords": ["安全", "緊急", "停機", "警報", "sop", "風險"]
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化智能推薦器

        Args:
            config_path: 配置檔案路徑（可選）
        """
        self.config = self._load_config(config_path) if config_path else {}

        # 推薦歷史
        self.recommendation_history = []

    def _load_config(self, config_path: str) -> Dict:
        """載入配置檔案"""
        path = Path(config_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def analyze_failed_operations(self, failed_operations: List[Dict]) -> Dict:
        """
        分析失敗的操作

        Args:
            failed_operations: 失敗操作列表，每項包含：
                {
                    "operation": str,  # 操作描述
                    "topic": str,      # 主題（可選）
                    "error_type": str  # 錯誤類型（可選）
                }

        Returns:
            分析結果：
            {
                "total_failures": int,
                "failure_by_category": {...},
                "identified_topics": [...]
            }
        """
        failure_categories = defaultdict(int)
        identified_topics = set()

        for operation in failed_operations:
            op_text = operation.get("operation", "").lower()
            topic = operation.get("topic", "unknown")

            # 根據操作內容識別類別
            for category, mapping in self.OPERATION_TOPIC_MAPPING.items():
                if any(keyword in op_text for keyword in mapping["keywords"]):
                    failure_categories[category] += 1
                    identified_topics.update(mapping["topics"])

        return {
            "total_failures": len(failed_operations),
            "failure_by_category": dict(failure_categories),
            "identified_topics": list(identified_topics)
        }

    def analyze_knowledge_gaps(self, knowledge_gaps: List[Dict]) -> Dict:
        """
        分析知識盲點

        Args:
            knowledge_gaps: 知識盲點列表（來自 ProgressTracker）

        Returns:
            分析結果：
            {
                "critical_gaps": [...],  # 嚴重盲點
                "moderate_gaps": [...],   # 中等盲點
                "minor_gaps": [...]       # 輕微盲點
            }
        """
        critical_gaps = []
        moderate_gaps = []
        minor_gaps = []

        for gap in knowledge_gaps:
            accuracy = gap.get("accuracy", 0)
            attempts = gap.get("total_attempts", 0)

            if accuracy < 40 and attempts >= 5:
                critical_gaps.append(gap)
            elif accuracy < 60 and attempts >= 3:
                moderate_gaps.append(gap)
            else:
                minor_gaps.append(gap)

        return {
            "critical_gaps": critical_gaps,
            "moderate_gaps": moderate_gaps,
            "minor_gaps": minor_gaps
        }

    def recommend_topics(self,
                        failed_operations: Optional[List[Dict]] = None,
                        knowledge_gaps: Optional[List[Dict]] = None,
                        max_recommendations: int = 5) -> List[Dict]:
        """
        推薦理論複習主題

        Args:
            failed_operations: 失敗操作列表
            knowledge_gaps: 知識盲點列表
            max_recommendations: 最多推薦數量

        Returns:
            推薦主題列表，每項包含：
            {
                "topic": str,
                "priority": str,  # critical/high/medium/low
                "reason": str,
                "related_operations": [...]
            }
        """
        recommendations = []
        topic_scores = defaultdict(lambda: {"score": 0, "reasons": [], "operations": []})

        # 1. 根據失敗操作推薦
        if failed_operations:
            failure_analysis = self.analyze_failed_operations(failed_operations)

            for category, count in failure_analysis["failure_by_category"].items():
                mapping = self.OPERATION_TOPIC_MAPPING[category]
                priority_score = self._get_priority_score(mapping["priority"])

                for topic in mapping["topics"]:
                    topic_scores[topic]["score"] += count * priority_score
                    topic_scores[topic]["reasons"].append(
                        f"在{category}相關操作中失敗{count}次"
                    )
                    topic_scores[topic]["priority"] = mapping["priority"]

        # 2. 根據知識盲點推薦
        if knowledge_gaps:
            gap_analysis = self.analyze_knowledge_gaps(knowledge_gaps)

            # 嚴重盲點加權最高
            for gap in gap_analysis["critical_gaps"]:
                topic = gap["topic"]
                topic_scores[topic]["score"] += 10
                topic_scores[topic]["reasons"].append(
                    f"該主題正確率僅{gap['accuracy']}%（嚴重盲點）"
                )
                topic_scores[topic]["priority"] = "critical"

            # 中等盲點
            for gap in gap_analysis["moderate_gaps"]:
                topic = gap["topic"]
                topic_scores[topic]["score"] += 5
                topic_scores[topic]["reasons"].append(
                    f"該主題正確率{gap['accuracy']}%（需加強）"
                )
                if "priority" not in topic_scores[topic]:
                    topic_scores[topic]["priority"] = "high"

        # 3. 排序並生成推薦
        sorted_topics = sorted(
            topic_scores.items(),
            key=lambda x: (
                self._get_priority_score(x[1].get("priority", "low")),
                x[1]["score"]
            ),
            reverse=True
        )

        for topic, data in sorted_topics[:max_recommendations]:
            recommendations.append({
                "topic": topic,
                "priority": data.get("priority", "medium"),
                "score": data["score"],
                "reasons": data["reasons"],
                "recommendation": self._generate_recommendation_text(topic, data)
            })

        # 記錄推薦歷史
        self.recommendation_history.append({
            "timestamp": self._get_timestamp(),
            "recommendations": recommendations
        })

        return recommendations

    def _get_priority_score(self, priority: str) -> int:
        """優先級轉分數"""
        priority_map = {
            "critical": 100,
            "high": 50,
            "medium": 20,
            "low": 10
        }
        return priority_map.get(priority, 10)

    def _generate_recommendation_text(self, topic: str, data: Dict) -> str:
        """生成推薦文字"""
        priority = data.get("priority", "medium")
        reasons = data["reasons"]

        if priority == "critical":
            prefix = "⚠️ 強烈建議立即複習"
        elif priority == "high":
            prefix = "📌 建議優先複習"
        else:
            prefix = "💡 建議複習"

        reason_text = "、".join(reasons[:2])  # 最多顯示2個原因

        return f"{prefix}「{topic}」- {reason_text}"

    def generate_learning_path(self, recommendations: List[Dict]) -> List[Dict]:
        """
        生成個性化學習路徑

        Args:
            recommendations: 推薦主題列表

        Returns:
            學習路徑，按優先級和依賴關係排序
        """
        # 主題依賴關係（某些主題需要先學其他主題）
        dependencies = {
            "CVD原理": [],
            "化學反應": ["CVD原理"],
            "冷卻系統原理": [],
            "熱管理基礎": ["冷卻系統原理"],
            "真空系統原理": [],
            "真空泵操作": ["真空系統原理"],
            "對準系統原理": [],
            "精密定位": ["對準系統原理"]
        }

        learning_path = []
        completed_topics = set()

        # 按優先級分組
        critical = [r for r in recommendations if r["priority"] == "critical"]
        high = [r for r in recommendations if r["priority"] == "high"]
        medium = [r for r in recommendations if r["priority"] == "medium"]
        low = [r for r in recommendations if r["priority"] == "low"]

        # 處理每個優先級組
        for group in [critical, high, medium, low]:
            for rec in group:
                topic = rec["topic"]

                # 檢查依賴
                deps = dependencies.get(topic, [])
                missing_deps = [d for d in deps if d not in completed_topics]

                if missing_deps:
                    # 先加入缺少的依賴主題
                    for dep in missing_deps:
                        if dep not in completed_topics:
                            learning_path.append({
                                "topic": dep,
                                "priority": "prerequisite",
                                "reason": f"「{topic}」的前置知識"
                            })
                            completed_topics.add(dep)

                # 加入主要主題
                learning_path.append({
                    "topic": topic,
                    "priority": rec["priority"],
                    "reasons": rec["reasons"],
                    "estimated_time_minutes": self._estimate_study_time(topic)
                })
                completed_topics.add(topic)

        return learning_path

    def _estimate_study_time(self, topic: str) -> int:
        """估算學習時間（分鐘）"""
        # 根據主題複雜度估算
        complex_topics = ["CVD原理", "化學反應", "真空系統原理", "PID控制"]
        medium_topics = ["溫控系統原理", "壓力控制原理", "對準系統原理"]

        if topic in complex_topics:
            return 45
        elif topic in medium_topics:
            return 30
        else:
            return 20

    def should_trigger_recommendation(self,
                                     recent_failures: List[Dict],
                                     failure_threshold: int = 3) -> bool:
        """
        判斷是否應該觸發推薦

        Args:
            recent_failures: 最近的失敗記錄
            failure_threshold: 失敗次數閾值

        Returns:
            是否應該推薦
        """
        if len(recent_failures) >= failure_threshold:
            return True

        # 檢查連續失敗
        if len(recent_failures) >= 3:
            # 如果最近3次都失敗，也觸發
            return True

        return False

    def _get_timestamp(self) -> str:
        """獲取時間戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def export_recommendations(self, output_file: str, recommendations: List[Dict]):
        """
        匯出推薦結果

        Args:
            output_file: 輸出檔案路徑
            recommendations: 推薦列表
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": self._get_timestamp(),
                "recommendations": recommendations
            }, f, ensure_ascii=False, indent=2)


# 使用範例
if __name__ == "__main__":
    print("=== Smart Recommender 使用範例 ===\n")

    # 1. 創建推薦器
    recommender = SmartRecommender()

    # 2. 模擬失敗操作
    failed_operations = [
        {"operation": "檢查冷卻水流量是否正常", "topic": "冷卻系統"},
        {"operation": "調整真空壓力到標準值", "topic": "真空系統"},
        {"operation": "檢查冷卻風扇運轉", "topic": "冷卻系統"},
        {"operation": "檢測真空洩漏", "topic": "真空系統"},
        {"operation": "校準對準系統", "topic": "對準系統"}
    ]

    # 3. 模擬知識盲點
    knowledge_gaps = [
        {"topic": "冷卻系統", "accuracy": 35, "total_attempts": 6, "error_count": 4},
        {"topic": "真空系統", "accuracy": 55, "total_attempts": 4, "error_count": 2},
        {"topic": "CVD", "accuracy": 45, "total_attempts": 5, "error_count": 3}
    ]

    # 4. 分析失敗操作
    print("分析失敗操作...")
    failure_analysis = recommender.analyze_failed_operations(failed_operations)
    print(f"總失敗次數: {failure_analysis['total_failures']}")
    print(f"失敗類別分布: {failure_analysis['failure_by_category']}")
    print()

    # 5. 分析知識盲點
    print("分析知識盲點...")
    gap_analysis = recommender.analyze_knowledge_gaps(knowledge_gaps)
    print(f"嚴重盲點: {len(gap_analysis['critical_gaps'])} 個")
    print(f"中等盲點: {len(gap_analysis['moderate_gaps'])} 個")
    print()

    # 6. 生成推薦
    print("生成推薦主題...")
    recommendations = recommender.recommend_topics(
        failed_operations=failed_operations,
        knowledge_gaps=knowledge_gaps,
        max_recommendations=5
    )

    print(f"\n推薦 {len(recommendations)} 個主題:\n")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['recommendation']}")
        print(f"   優先級: {rec['priority']}")
        print(f"   分數: {rec['score']}")
        print()

    # 7. 生成學習路徑
    print("生成學習路徑...")
    learning_path = recommender.generate_learning_path(recommendations)

    print(f"\n建議學習順序 (共 {len(learning_path)} 個主題):\n")
    total_time = 0
    for i, step in enumerate(learning_path, 1):
        time = step.get("estimated_time_minutes", 0)
        total_time += time
        print(f"{i}. {step['topic']} ({time}分鐘)")
        if "reasons" in step:
            print(f"   原因: {step['reasons'][0]}")

    print(f"\n預估總學習時間: {total_time} 分鐘 ({total_time/60:.1f} 小時)")

    # 8. 檢查是否應該觸發推薦
    print("\n檢查觸發條件...")
    should_trigger = recommender.should_trigger_recommendation(failed_operations)
    print(f"應該觸發推薦: {'是' if should_trigger else '否'}")
