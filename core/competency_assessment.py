# -*- coding: utf-8 -*-
"""
多維度能力評估系統 (Multi-dimensional Competency Assessment System)

評估學員在故障處理過程中的多項能力:
1. 診斷能力 (Diagnostic Competency): 正確識別故障根因的能力
2. 決策速度 (Decision Speed): 在時間壓力下快速做決定
3. 風險意識 (Risk Awareness): 識別並避免高風險操作
4. 系統性思維 (Systems Thinking): 理解參數間的因果關係
5. 優先級判斷 (Prioritization): 多問題並發時的處理順序

基於認知負荷理論與專家-新手差異研究
"""

import time
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ActionRecord:
    """操作記錄"""
    timestamp: float
    action_type: str  # "inspect"/"adjust"/"consult"/"emergency_stop"
    target: str  # 操作對象
    context: Dict  # 當時的系統狀態
    is_correct: bool = None  # 是否正確 (由專家路徑判斷)
    risk_level: str = "low"  # "low"/"medium"/"high"
    decision_time: float = 0.0  # 決策時間 (秒)


@dataclass
class CompetencyMetrics:
    """能力評估指標"""
    # 診斷能力
    diagnostic_accuracy: float = 0.0  # 診斷準確率 (0-100)
    root_cause_identified: bool = False  # 是否找到根因
    diagnosis_steps: int = 0  # 診斷步驟數
    unnecessary_checks: int = 0  # 不必要的檢查次數

    # 決策速度
    avg_decision_time: float = 0.0  # 平均決策時間 (秒)
    total_time: float = 0.0  # 總處理時間 (秒)
    time_efficiency_score: float = 0.0  # 時間效率分數 (0-100)

    # 風險意識
    high_risk_actions: int = 0  # 高風險操作次數
    risk_mitigation_actions: int = 0  # 風險緩解操作次數
    risk_awareness_score: float = 0.0  # 風險意識分數 (0-100)

    # 系統性思維
    coupling_awareness: float = 0.0  # 參數耦合認知 (0-100)
    cascading_effects_considered: int = 0  # 考慮連鎖效應的次數
    holistic_view_score: float = 0.0  # 整體視野分數 (0-100)

    # 優先級判斷
    correct_prioritization: int = 0  # 正確排序次數
    priority_violations: int = 0  # 優先級錯誤次數
    prioritization_score: float = 0.0  # 優先級分數 (0-100)

    # ===== 新增：理論知識能力 =====
    theory_questions_asked: int = 0  # 詢問理論問題次數
    theory_knowledge_score: float = 0.0  # 理論知識分數 (0-100)
    learning_engagement: float = 0.0  # 學習參與度 (0-100)

    # 整體評分
    overall_score: float = 0.0  # 綜合評分 (0-100)
    proficiency_level: str = "Novice"  # "Novice"/"Advanced Beginner"/"Competent"/"Proficient"/"Expert"


class CompetencyAssessmentSystem:
    """多維度能力評估系統"""

    def __init__(self):
        """初始化評估系統"""
        self.action_history: List[ActionRecord] = []
        self.scenario_start_time: float = None
        self.scenario_type: str = None
        self.expert_path: List[str] = []  # 專家操作路徑
        self.fault_root_cause: str = None  # 故障根因
        self.qa_stats: Dict = {}  # QA Assistant 統計（理論知識）

    def start_scenario(self, scenario_type: str, fault_root_cause: str):
        """
        開始新場景評估

        Args:
            scenario_type: 場景類型
            fault_root_cause: 故障根因
        """
        self.scenario_start_time = time.time()
        self.scenario_type = scenario_type
        self.fault_root_cause = fault_root_cause
        self.action_history = []

        # 載入專家路徑
        self.expert_path = self._get_expert_path(scenario_type)

    def record_action(self, action_type: str, target: str, context: Dict,
                     decision_time: float = 0.0):
        """
        記錄學員操作

        Args:
            action_type: 操作類型
            target: 操作對象
            context: 系統狀態
            decision_time: 決策時間
        """
        # 判斷操作是否正確
        is_correct = self._evaluate_action(action_type, target, len(self.action_history))

        # 判斷風險等級
        risk_level = self._assess_risk(action_type, target, context)

        action = ActionRecord(
            timestamp=time.time(),
            action_type=action_type,
            target=target,
            context=context.copy(),
            is_correct=is_correct,
            risk_level=risk_level,
            decision_time=decision_time
        )

        self.action_history.append(action)

    def compute_competency_metrics(self) -> CompetencyMetrics:
        """
        計算能力評估指標

        Returns:
            能力評估指標
        """
        metrics = CompetencyMetrics()

        if not self.action_history:
            return metrics

        # === 1. 診斷能力評估 ===
        diagnostic_metrics = self._assess_diagnostic_competency()
        metrics.diagnostic_accuracy = diagnostic_metrics['accuracy']
        metrics.root_cause_identified = diagnostic_metrics['root_cause_found']
        metrics.diagnosis_steps = diagnostic_metrics['steps']
        metrics.unnecessary_checks = diagnostic_metrics['unnecessary_checks']

        # === 2. 決策速度評估 ===
        speed_metrics = self._assess_decision_speed()
        metrics.avg_decision_time = speed_metrics['avg_time']
        metrics.total_time = speed_metrics['total_time']
        metrics.time_efficiency_score = speed_metrics['efficiency_score']

        # === 3. 風險意識評估 ===
        risk_metrics = self._assess_risk_awareness()
        metrics.high_risk_actions = risk_metrics['high_risk_count']
        metrics.risk_mitigation_actions = risk_metrics['mitigation_count']
        metrics.risk_awareness_score = risk_metrics['awareness_score']

        # === 4. 系統性思維評估 ===
        systems_metrics = self._assess_systems_thinking()
        metrics.coupling_awareness = systems_metrics['coupling_awareness']
        metrics.cascading_effects_considered = systems_metrics['cascading_considered']
        metrics.holistic_view_score = systems_metrics['holistic_score']

        # === 5. 優先級判斷評估 ===
        priority_metrics = self._assess_prioritization()
        metrics.correct_prioritization = priority_metrics['correct_count']
        metrics.priority_violations = priority_metrics['violation_count']
        metrics.prioritization_score = priority_metrics['priority_score']

        # === 6. 理論知識評估（新增）===
        if self.qa_stats:
            metrics.theory_questions_asked = self.qa_stats.get('theory_questions', 0)
            metrics.theory_knowledge_score = self.qa_stats.get('knowledge_score', 0.0) * 10  # 轉為 0-100 尺度
            # 學習參與度 = (理論問題數 / 總診斷步驟) * 100
            if metrics.diagnosis_steps > 0:
                metrics.learning_engagement = min(100, (metrics.theory_questions_asked / metrics.diagnosis_steps) * 100)
            else:
                metrics.learning_engagement = 0.0

        # === 7. 計算整體評分 ===
        metrics.overall_score = self._compute_overall_score(metrics)
        metrics.proficiency_level = self._determine_proficiency_level(metrics.overall_score)

        return metrics

    def _assess_diagnostic_competency(self) -> Dict:
        """評估診斷能力"""
        inspect_actions = [a for a in self.action_history if a.action_type == "inspect"]

        if not inspect_actions:
            return {
                'accuracy': 0.0,
                'root_cause_found': False,
                'steps': 0,
                'unnecessary_checks': 0
            }

        # 計算準確率
        correct_inspections = len([a for a in inspect_actions if a.is_correct])
        accuracy = (correct_inspections / len(inspect_actions)) * 100

        # 判斷是否找到根因
        root_cause_found = any(
            a.target == self.fault_root_cause for a in inspect_actions
        )

        # 計算不必要的檢查
        unnecessary = len([a for a in inspect_actions if not a.is_correct])

        return {
            'accuracy': accuracy,
            'root_cause_found': root_cause_found,
            'steps': len(inspect_actions),
            'unnecessary_checks': unnecessary
        }

    def _assess_decision_speed(self) -> Dict:
        """評估決策速度"""
        if not self.action_history or not self.scenario_start_time:
            return {
                'avg_time': 0.0,
                'total_time': 0.0,
                'efficiency_score': 0.0
            }

        # 平均決策時間
        decision_times = [a.decision_time for a in self.action_history if a.decision_time > 0]
        avg_time = sum(decision_times) / len(decision_times) if decision_times else 0.0

        # 總處理時間
        total_time = self.action_history[-1].timestamp - self.scenario_start_time

        # 時間效率分數 (與專家路徑比較)
        expert_time = len(self.expert_path) * 15  # 假設專家每步 15 秒
        if total_time > 0:
            efficiency_score = min(100, (expert_time / total_time) * 100)
        else:
            efficiency_score = 0.0

        return {
            'avg_time': avg_time,
            'total_time': total_time,
            'efficiency_score': efficiency_score
        }

    def _assess_risk_awareness(self) -> Dict:
        """評估風險意識"""
        high_risk_actions = [a for a in self.action_history if a.risk_level == "high"]
        medium_risk_actions = [a for a in self.action_history if a.risk_level == "medium"]

        # 計算風險緩解操作 (先檢查再操作)
        mitigation_count = 0
        for i, action in enumerate(self.action_history):
            if action.action_type == "adjust" and i > 0:
                prev_action = self.action_history[i-1]
                if prev_action.action_type == "inspect" and prev_action.target == action.target:
                    mitigation_count += 1

        # 風險意識分數
        total_actions = len(self.action_history)
        if total_actions == 0:
            awareness_score = 0.0
        else:
            # 扣分: 高風險操作，加分: 風險緩解
            score = 100 - (len(high_risk_actions) * 20) - (len(medium_risk_actions) * 5) + (mitigation_count * 10)
            awareness_score = max(0, min(100, score))

        return {
            'high_risk_count': len(high_risk_actions),
            'mitigation_count': mitigation_count,
            'awareness_score': awareness_score
        }

    def _assess_systems_thinking(self) -> Dict:
        """評估系統性思維"""
        # 檢查是否考慮參數耦合
        coupling_checks = 0
        cascading_considered = 0

        # 定義參數關聯 (基於物理耦合模型)
        parameter_couplings = {
            'cooling_flow': ['lens_temp', 'alignment_error'],
            'lens_temp': ['alignment_error', 'light_intensity'],
            'filter_pressure_drop': ['cooling_flow', 'vacuum_pressure'],
            'vacuum_pressure': ['light_intensity']
        }

        for i, action in enumerate(self.action_history):
            if action.action_type == "inspect" and i > 0:
                prev_action = self.action_history[i-1]
                # 檢查是否檢查了相關參數
                if prev_action.target in parameter_couplings:
                    related_params = parameter_couplings[prev_action.target]
                    if action.target in related_params:
                        coupling_checks += 1
                        cascading_considered += 1

        # 系統性思維分數
        if len(self.action_history) == 0:
            coupling_awareness = 0.0
            holistic_score = 0.0
        else:
            coupling_awareness = (coupling_checks / len(self.action_history)) * 100
            holistic_score = min(100, (cascading_considered / max(1, len(self.expert_path))) * 100)

        return {
            'coupling_awareness': coupling_awareness,
            'cascading_considered': cascading_considered,
            'holistic_score': holistic_score
        }

    def _assess_prioritization(self) -> Dict:
        """評估優先級判斷"""
        # 定義優先級規則
        # 1. 安全 > 品質 > 產能
        # 2. 緊急 > 重要 > 一般

        priority_order = {
            'emergency_stop': 1,  # 最高優先級
            'cooling_flow': 2,  # 影響安全
            'lens_temp': 3,  # 影響品質
            'vacuum_pressure': 4,
            'light_intensity': 5,
            'alignment_error': 6,
            'filter_pressure_drop': 7  # 最低優先級
        }

        correct_count = 0
        violation_count = 0

        # 檢查操作順序是否符合優先級
        for i in range(len(self.action_history) - 1):
            current_priority = priority_order.get(self.action_history[i].target, 99)
            next_priority = priority_order.get(self.action_history[i + 1].target, 99)

            if current_priority < next_priority:
                correct_count += 1
            elif current_priority > next_priority + 2:  # 允許一定彈性
                violation_count += 1

        # 優先級分數
        total_transitions = len(self.action_history) - 1
        if total_transitions == 0:
            priority_score = 0.0
        else:
            priority_score = (correct_count / total_transitions) * 100

        return {
            'correct_count': correct_count,
            'violation_count': violation_count,
            'priority_score': priority_score
        }

    def _compute_overall_score(self, metrics: CompetencyMetrics) -> float:
        """計算整體評分 (加權平均，含理論知識)"""
        weights = {
            'diagnostic': 0.25,  # 診斷能力權重 25%
            'speed': 0.12,  # 決策速度權重 12%
            'risk': 0.20,  # 風險意識權重 20%
            'systems': 0.18,  # 系統性思維權重 18%
            'priority': 0.10,  # 優先級判斷權重 10%
            'theory': 0.15  # 理論知識權重 15% (NEW)
        }

        overall = (
            metrics.diagnostic_accuracy * weights['diagnostic'] +
            metrics.time_efficiency_score * weights['speed'] +
            metrics.risk_awareness_score * weights['risk'] +
            metrics.holistic_view_score * weights['systems'] +
            metrics.prioritization_score * weights['priority'] +
            metrics.theory_knowledge_score * weights['theory']
        )

        return round(overall, 2)

    def _determine_proficiency_level(self, score: float) -> str:
        """根據評分判定熟練度等級 (Dreyfus Model)"""
        if score >= 90:
            return "Expert"  # 專家: 直覺式判斷，能處理複雜情況
        elif score >= 75:
            return "Proficient"  # 精通: 整體視野，能權衡取捨
        elif score >= 60:
            return "Competent"  # 勝任: 有計畫性，能獨立處理
        elif score >= 40:
            return "Advanced Beginner"  # 高級初學者: 需要指導
        else:
            return "Novice"  # 新手: 需要明確規則

    def _evaluate_action(self, action_type: str, target: str, step_index: int) -> bool:
        """評估操作是否正確 (與專家路徑比較)"""
        if step_index < len(self.expert_path):
            expected_action = self.expert_path[step_index]
            return target == expected_action
        return False

    def _assess_risk(self, action_type: str, target: str, context: Dict) -> str:
        """評估操作風險等級"""
        # 調整類操作風險較高
        if action_type == "adjust":
            # 未檢查就調整 → 高風險
            if not any(a.target == target and a.action_type == "inspect"
                      for a in self.action_history):
                return "high"
            # 偏離正常範圍較大 → 中風險
            return "medium"

        # 緊急停機 → 高風險 (影響產能)
        if action_type == "emergency_stop":
            return "high"

        # 檢查類操作 → 低風險
        return "low"

    def _get_expert_path(self, scenario_type: str) -> List[str]:
        """獲取專家操作路徑"""
        expert_paths = {
            'cooling_failure': [
                'cooling_flow',  # 1. 檢查冷卻流量
                'lens_temp',  # 2. 確認溫度上升
                'filter_pressure_drop',  # 3. 檢查過濾器
                'cooling_flow',  # 4. 調整冷卻
                'lens_temp'  # 5. 確認溫度恢復
            ],
            'vacuum_leak': [
                'vacuum_pressure',
                'filter_pressure_drop',
                'vacuum_pressure'
            ],
            'optical_degradation': [
                'light_intensity',
                'lens_temp',
                'vacuum_pressure',
                'light_intensity'
            ]
        }

        return expert_paths.get(scenario_type, [])

    def generate_feedback_report(self, metrics: CompetencyMetrics) -> str:
        """
        生成詳細反饋報告

        Args:
            metrics: 能力評估指標

        Returns:
            反饋報告 (Markdown 格式)
        """
        report = f"""
# 能力評估報告

## 整體表現
- **綜合評分**: {metrics.overall_score:.1f}/100
- **熟練度等級**: {metrics.proficiency_level}
- **總處理時間**: {metrics.total_time:.1f} 秒

---

## 各維度評估

### 1. 診斷能力 ({metrics.diagnostic_accuracy:.1f}/100)
- 診斷準確率: {metrics.diagnostic_accuracy:.1f}%
- 是否找到根因: {'[OK] 是' if metrics.root_cause_identified else '[X] 否'}
- 診斷步驟數: {metrics.diagnosis_steps}
- 不必要檢查: {metrics.unnecessary_checks} 次

**建議**: {'表現優秀！' if metrics.diagnostic_accuracy >= 80 else '建議多關注參數間的因果關係，減少不必要的檢查。'}

### 2. 決策速度 ({metrics.time_efficiency_score:.1f}/100)
- 平均決策時間: {metrics.avg_decision_time:.1f} 秒
- 時間效率分數: {metrics.time_efficiency_score:.1f}/100

**建議**: {'決策迅速！' if metrics.time_efficiency_score >= 70 else '可嘗試建立故障處理的心智模型，加快診斷速度。'}

### 3. 風險意識 ({metrics.risk_awareness_score:.1f}/100)
- 高風險操作次數: {metrics.high_risk_actions}
- 風險緩解操作: {metrics.risk_mitigation_actions} 次

**建議**: {'風險控制良好！' if metrics.high_risk_actions == 0 else '建議在調整參數前先進行檢查，降低風險。'}

### 4. 系統性思維 ({metrics.holistic_view_score:.1f}/100)
- 參數耦合認知: {metrics.coupling_awareness:.1f}%
- 考慮連鎖效應: {metrics.cascading_effects_considered} 次

**建議**: {'系統性思維優秀！' if metrics.holistic_view_score >= 70 else '建議多思考參數間的關聯，例如冷卻問題會影響溫度和對準。'}

### 5. 優先級判斷 ({metrics.prioritization_score:.1f}/100)
- 正確排序次數: {metrics.correct_prioritization}
- 優先級錯誤: {metrics.priority_violations} 次

**建議**: {'優先級判斷準確！' if metrics.priority_violations == 0 else '記住：安全 > 品質 > 產能的優先順序。'}

### 6. 理論知識 ({metrics.theory_knowledge_score:.1f}/100) ⭐ 新增
- 理論問題詢問: {metrics.theory_questions_asked} 次
- 知識評分: {metrics.theory_knowledge_score:.1f}/100
- 學習參與度: {metrics.learning_engagement:.1f}%

**建議**: {'理論基礎扎實！' if metrics.theory_knowledge_score >= 70 else '建議多詢問「為什麼」，加深對原理的理解。'}

---

## 成長路徑

當前等級: **{metrics.proficiency_level}**

"""
        # 根據等級提供成長建議
        growth_path = {
            "Novice": "下一步: 熟悉基本診斷流程，建立參數正常範圍的認知",
            "Advanced Beginner": "下一步: 理解參數間的因果關係，減少試錯次數",
            "Competent": "下一步: 培養整體視野，能同時處理多個問題",
            "Proficient": "下一步: 精進直覺判斷，提升複雜情境的應對能力",
            "Expert": "恭喜達到專家水準！可嘗試指導他人或處理罕見案例"
        }

        report += growth_path.get(metrics.proficiency_level, "")

        return report

    def update_theory_knowledge(self, qa_stats: Dict):
        """
        更新理論知識評估（從 QA Assistant 獲取）

        Args:
            qa_stats: QA Assistant 的統計資料
                {
                    'theory_questions': int,
                    'knowledge_score': float (0-10),
                    'total_interactions': int
                }
        """
        self.qa_stats = qa_stats


if __name__ == "__main__":
    # 測試能力評估系統
    print("=" * 70)
    print("多維度能力評估系統測試")
    print("=" * 70)

    system = CompetencyAssessmentSystem()

    # 模擬場景
    system.start_scenario("cooling_failure", "cooling_flow")

    # 模擬學員操作
    print("\n模擬學員操作流程:")
    print("-" * 70)

    # 操作序列
    actions = [
        ("inspect", "cooling_flow", 5.0),
        ("inspect", "lens_temp", 3.0),
        ("inspect", "filter_pressure_drop", 4.0),
        ("adjust", "cooling_flow", 8.0),
        ("inspect", "lens_temp", 2.0)
    ]

    for i, (action_type, target, decision_time) in enumerate(actions):
        print(f"{i+1}. {action_type} {target} (決策時間: {decision_time:.1f}s)")
        system.record_action(action_type, target, {}, decision_time)
        time.sleep(0.1)

    # 計算評估指標
    print("\n" + "=" * 70)
    print("評估結果:")
    print("=" * 70)
    metrics = system.compute_competency_metrics()

    # 生成報告
    report = system.generate_feedback_report(metrics)
    print(report)
