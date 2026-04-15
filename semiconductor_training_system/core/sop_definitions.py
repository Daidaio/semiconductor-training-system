# -*- coding: utf-8 -*-
"""
SOP 動作序列定義 + 動作評估引擎
操作者自行判斷互動零件與動作，AI 學長評估對錯並依自適應模式給回饋。
"""
import random

# ── SOP 序列定義 ──────────────────────────────────────────────────────────────
# valid_components: 此步驟應互動的零件群組（前端 label）
# valid_actions:    接受的動作關鍵詞（模糊比對，包含即算對）
# hint_component:   求助或答錯時給的元件方向提示
# hint_action:      求助或答錯時給的動作方向提示
# reason:           為什麼要做這一步（給補救模式用）

SOP_DEFINITIONS = {
    'lens_hotspot': {
        'name': '投影鏡片過熱',
        'fault_system': '投影鏡組熱控系統',
        'steps': [
            {
                'desc': '確認鏡片溫度異常',
                'valid_components': ['投影鏡組'],
                'valid_actions': ['溫度', '溫升', 'CDU', '鏡片', '查看'],
                'hint_component': '投影鏡組',
                'hint_action': '查看鏡片溫度',
                'reason': '需先確認鏡片溫升量才能判斷嚴重程度',
            },
            {
                'desc': '降低曝光dose以減少熱輸入',
                'valid_components': ['控制系統', '雷射光源', 'HMI 螢幕'],
                'valid_actions': ['dose', 'dose', '降低', '調降', '減少'],
                'hint_component': '控制系統',
                'hint_action': '降低曝光dose',
                'reason': '降低dose可以減少對鏡片的熱輸入，阻止溫升繼續惡化',
            },
            {
                'desc': '停止曝光等待冷卻',
                'valid_components': ['投影鏡組', '控制系統'],
                'valid_actions': ['停止', '等待', '冷卻', '降溫', '停機'],
                'hint_component': '控制系統',
                'hint_action': '停止曝光',
                'reason': '停止曝光可讓鏡片透過自然對流冷卻',
            },
            {
                'desc': '確認冷卻水迴路是否正常',
                'valid_components': ['液浸冷卻'],
                'valid_actions': ['冷卻水', '流量', '水流', '液浸', '水溫'],
                'hint_component': '液浸冷卻',
                'hint_action': '確認冷卻水流量',
                'reason': '鏡片冷卻依賴冷卻水迴路，需確認無異常',
            },
            {
                'desc': '恢復曝光並監控 CDU',
                'valid_components': ['控制系統', '投影鏡組', 'HMI 螢幕'],
                'valid_actions': ['恢復', '監控', 'CDU', '正常', '量產'],
                'hint_component': '控制系統',
                'hint_action': '恢復曝光並監控 CDU',
                'reason': '修復後要驗證 CDU 3σ 回到規格內',
            },
        ]
    },
    'contamination': {
        'name': '光罩污染',
        'fault_system': '光罩載台系統',
        'steps': [
            {
                'desc': '確認光源強度與光罩狀態',
                'valid_components': ['光罩載台', '控制系統'],
                'valid_actions': ['光源', '強度', '確認', '查看', '異常', '污染', '光罩'],
                'hint_component': '控制系統',
                'hint_action': '查看光源強度讀值確認是否異常',
                'reason': '光罩污染會造成光源強度下降，先確認強度異常位置',
            },
            {
                'desc': '停機並卸載光罩',
                'valid_components': ['光罩載台', '控制系統'],
                'valid_actions': ['卸載', '停機', '取出', '光罩'],
                'hint_component': '光罩載台',
                'hint_action': '停機並卸載光罩',
                'reason': '處理光罩前必須先停機，防止在運作中損壞光罩',
            },
            {
                'desc': '目視檢查光罩表面',
                'valid_components': ['光罩載台'],
                'valid_actions': ['目視', '檢查', '表面', '光罩', '確認污染'],
                'hint_component': '光罩載台',
                'hint_action': '目視檢查光罩表面',
                'reason': '找出污染的具體位置與類型，決定清潔或更換',
            },
            {
                'desc': '清潔或更換光罩',
                'valid_components': ['光罩載台'],
                'valid_actions': ['清潔', '更換', '完成'],
                'hint_component': '光罩載台',
                'hint_action': '依污染程度清潔或更換光罩',
                'reason': '輕微污染可清潔，嚴重污染需送廠或更換',
            },
            {
                'desc': '裝回光罩並執行對準',
                'valid_components': ['光罩載台', '控制系統'],
                'valid_actions': ['裝回', '對準', '恢復', '執行'],
                'hint_component': '光罩載台',
                'hint_action': '裝回光罩並執行 reticle alignment',
                'reason': '光罩裝回後必須重新對準，確認套刻誤差在規格內',
            },
        ]
    },
    'stage_error': {
        'name': '晶圓載台位置誤差',
        'fault_system': '晶圓載台定位系統',
        'steps': [
            {
                'desc': '確認對準誤差讀值',
                'valid_components': ['晶圓載台', '控制系統'],
                'valid_actions': ['對準', '誤差', '確認', '查看', '載台', '警報', 'alignment'],
                'hint_component': '控制系統',
                'hint_action': '查看對準誤差讀值',
                'reason': '對準誤差超出閾值時需先確認偏差量，才能判斷是否需要校正',
            },
            {
                'desc': '執行載台校正程序',
                'valid_components': ['晶圓載台', '控制系統'],
                'valid_actions': ['校正', 'Cal', 'calibration', '執行', '校準'],
                'hint_component': '晶圓載台',
                'hint_action': '執行載台校正 Cal Routine',
                'reason': '載台校正可自動量測並補償位置誤差',
            },
            {
                'desc': '確認氣浮軸承壓力正常',
                'valid_components': ['晶圓載台'],
                'valid_actions': ['氣浮', '軸承', '壓力', '確認', '查看'],
                'hint_component': '晶圓載台',
                'hint_action': '確認氣浮軸承壓力',
                'reason': '氣浮壓力不足會導致載台摩擦增加，影響定位精度',
            },
            {
                'desc': '確認對準系統恢復正常',
                'valid_components': ['晶圓載台', '控制系統'],
                'valid_actions': ['確認', '正常', '恢復', '完成', '穩定', '合格'],
                'hint_component': '控制系統',
                'hint_action': '確認對準系統警報解除',
                'reason': '校正後需確認警報解除、對準誤差讀值回到正常範圍',
            },
        ]
    },
    'dose_drift': {
        'name': '曝光dose漂移',
        'fault_system': '雷射光源與dose控制',
        'steps': [
            {
                'desc': '確認dose偏差量',
                'valid_components': ['雷射光源', 'HMI 螢幕'],
                'valid_actions': ['偏差', 'dose', '讀值', '確認', '查看', 'dose'],
                'hint_component': '雷射光源',
                'hint_action': '確認dose偏差量',
                'reason': '偏差 > 1% 即需介入，先確認偏差量決定處理優先序',
            },
            {
                'desc': '執行dose校正',
                'valid_components': ['雷射光源', '控制系統'],
                'valid_actions': ['校正', '執行', 'Cal', '校準', '補償'],
                'hint_component': '雷射光源',
                'hint_action': '執行dose校正',
                'reason': 'dose校正可自動調整雷射電壓補償能量衰減',
            },
            {
                'desc': '清潔dose感測器玻璃窗',
                'valid_components': ['雷射光源', '照明系統'],
                'valid_actions': ['清潔', '感測器', '清洗', '完成', '光學元件'],
                'hint_component': '雷射光源',
                'hint_action': '清潔光學元件',
                'reason': '感測器玻璃窗或光學元件污染是dose讀值偏移的常見原因',
            },
            {
                'desc': '確認dose穩定性',
                'valid_components': ['雷射光源', '控制系統'],
                'valid_actions': ['穩定', '確認', 'CV', '驗證', '量測'],
                'hint_component': '雷射光源',
                'hint_action': '確認dose穩定性 CV < 0.3%',
                'reason': '修復後需連續量測確認穩定性，CV < 0.3% 為合格',
            },
        ]
    },
    'focus_drift': {
        'name': '焦距異常漂移',
        'fault_system': '照明系統與焦距控制',
        'steps': [
            {
                'desc': '確認焦距漂移量',
                'valid_components': ['照明系統', 'HMI 螢幕'],
                'valid_actions': ['漂移', '焦距', '確認', '查看', 'focus'],
                'hint_component': '照明系統',
                'hint_action': '確認焦距漂移量',
                'reason': '焦距漂移 > 30 nm 會顯著影響 CD，先確認嚴重程度',
            },
            {
                'desc': '執行 Focus 校正',
                'valid_components': ['照明系統', '控制系統'],
                'valid_actions': ['校正', 'Focus', '執行', '校準', '補償'],
                'hint_component': '照明系統',
                'hint_action': '執行 Focus 校正',
                'reason': '用 ALS 測試片量測實際最佳焦距並更新補償參數',
            },
            {
                'desc': '確認鏡片溫升（熱效應）',
                'valid_components': ['投影鏡組'],
                'valid_actions': ['溫升', '溫度', '鏡片', '熱', '確認'],
                'hint_component': '投影鏡組',
                'hint_action': '確認鏡片溫升情況',
                'reason': '焦距漂移常由鏡片熱效應引起，需確認溫升是否顯著',
            },
            {
                'desc': '等待熱穩定或降低dose',
                'valid_components': ['照明系統', '控制系統', '雷射光源'],
                'valid_actions': ['等待', '穩定', '降低', 'dose', '確認'],
                'hint_component': '控制系統',
                'hint_action': '等待熱穩定或降低dose',
                'reason': '等待熱平衡（約 15 min）或降低 Dose 可減緩熱漂移',
            },
        ]
    },
}

# ── 回饋模板 ──────────────────────────────────────────────────────────────────
_CORRECT_TEMPLATES = {
    'challenge': [
        '正確，繼續。',
        '對，往下走。',
        '正確。',
    ],
    'standard': [
        '做得好！接下來想一下{next_hint}的方向。',
        '正確！下一步考慮{next_hint}。',
        '對了，再思考{next_hint}。',
    ],
    'scaffolding': [
        '很好！這步做對了。接下來需要處理{next_hint}，你有想法嗎？',
        '正確！你做「{action}」是因為{reason}。下一步關注{next_hint}。',
        '對！接下來去{next_hint}看看。',
    ],
    'remedial': [
        '做對了！「{action}」就是這步的關鍵，因為{reason}。下一步是{next_step}。',
        '正確！{reason}，所以要先做「{action}」。接下來：{next_step}。',
    ],
}

_WRONG_TEMPLATES = {
    'challenge': [
        '不對，再想想。',
        '這個方向不對。',
        '不是這個，重新思考。',
    ],
    'standard': [
        '這步不太對，試著考慮{hint_component}的方向。',
        '這個動作現在不適合，想想目前最需要確認什麼。',
        '不對，再想想目前問題出在哪個系統。',
    ],
    'scaffolding': [
        '這步不對。現在問題是{fault_system}，先去{hint_component}看看狀況。',
        '先停一下。現在情況是{fault_system}異常，第一步應該去{hint_component}確認。',
        '不對，目前應該先{hint_action}，去{hint_component}操作。',
    ],
    'remedial': [
        '不對，這步應該是：去{hint_component}執行「{hint_action}」。因為{reason}。',
        '讓我說明：現在{fault_system}有問題，正確做法是先去{hint_component}，執行「{hint_action}」。',
    ],
}

# 提示層級由「目前分數」決定（非 adaptive_mode）：
#   85+  → hint_challenge ：不給實質提示，讓高分學員自行思考
#   65~84 → hint_standard  ：給部件方向，不說具體動作
#   40~64 → hint_scaffolding：給部件 + 動作方向
#   <40  → hint_remedial  ：完整步驟指引
_HINT_TEMPLATES = {
    'hint_challenge': [
        '這個問題你有能力自己判斷，仔細看一下警報訊息，答案就在那裡。',
        '分析一下目前的異常現象，思考問題出在哪個系統，你可以的。',
    ],
    'hint_standard': [
        '先看一下讀值確認偏差，再去找{hint_component}，靠近後按 E 選擇對應操作。',
        '確認一下目前的讀值，判斷問題後，靠近{hint_component}，按 E 看看有哪些選項。',
    ],
    'hint_scaffolding': [
        '先看{fault_system}的讀值確認問題，再走到{hint_component}旁邊，按 E 選「{hint_action}」。',
        '第{step_num}步：確認讀值偏差後，靠近{hint_component}，按 E 找到「{hint_action}」相關選項。',
    ],
    'hint_remedial': [
        '直接告訴你：走到{hint_component}旁邊，按 E 選「{hint_action}」，因為{reason}。',
        '第{step_num}步：靠近{hint_component}，按 E，選「{hint_action}」，這樣就對了。',
    ],
}

_DONE_TEMPLATES = {
    'challenge': '故障排除完成。',
    'standard': '完成！{fault_name}已排除，系統恢復正常。',
    'scaffolding': '很好，你完成了全部步驟！{fault_name}已排除，你表現不錯。',
    'remedial': '恭喜完成！整個流程是：{steps_summary}。下次遇到{fault_name}就知道怎麼做了。',
}


# ── 動作評估引擎 ──────────────────────────────────────────────────────────────

class ActionSession:
    """追蹤單次故障排除的 session 狀態"""

    def __init__(self, fault_type: str):
        sop = SOP_DEFINITIONS.get(fault_type)
        if not sop:
            raise ValueError(f'Unknown fault type: {fault_type}')
        self.fault_type = fault_type
        self.sop = sop
        self.current_step = 0
        self.total_steps = len(sop['steps'])
        self.mistake_count = 0
        self.consecutive_mistakes = 0
        self.consecutive_correct = 0
        self.hint_count = 0
        self.score = 100
        self.adaptive_mode = 'standard'
        self.completed = False

    # ── 自適應模式更新 ────────────────────────────────────────────────────────
    def _update_adaptive_mode(self, was_correct: bool):
        if was_correct:
            self.consecutive_mistakes = 0
            self.consecutive_correct += 1
            if self.consecutive_correct >= 3 and self.adaptive_mode != 'challenge':
                modes = ['remedial', 'scaffolding', 'standard', 'challenge']
                idx = modes.index(self.adaptive_mode)
                self.adaptive_mode = modes[min(idx + 1, 3)]
        else:
            self.consecutive_correct = 0
            self.consecutive_mistakes += 1
            if self.consecutive_mistakes >= 2 and self.adaptive_mode == 'challenge':
                self.adaptive_mode = 'standard'
            elif self.consecutive_mistakes >= 3 and self.adaptive_mode == 'standard':
                self.adaptive_mode = 'scaffolding'
            elif self.consecutive_mistakes >= 5 and self.adaptive_mode == 'scaffolding':
                self.adaptive_mode = 'remedial'

    # ── 動作比對（模糊） ──────────────────────────────────────────────────────
    def _match_component(self, component: str, step: dict) -> bool:
        return component in step['valid_components']

    def _match_action(self, action: str, step: dict) -> bool:
        action_lower = action.lower()
        for kw in step['valid_actions']:
            if kw.lower() in action_lower:
                return True
        return False

    # ── 評估動作 ──────────────────────────────────────────────────────────────
    def evaluate(self, component: str, action: str) -> dict:
        if self.completed:
            return {'correct': True, 'all_done': True, 'feedback': '故障已排除完成。', 'score': self.score}

        step = self.sop['steps'][self.current_step]
        comp_ok = self._match_component(component, step)
        act_ok = self._match_action(action, step)
        correct = comp_ok and act_ok

        result = {
            'correct': correct,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'step_done': False,
            'all_done': False,
            'adaptive_mode': self.adaptive_mode,
            'score': self.score,
        }

        if correct:
            self.score = max(0, self.score)  # 答對不扣分
            self._update_adaptive_mode(True)   # 先更新模式，result 回傳最新狀態
            self.current_step += 1
            result['step_done'] = True
            result['current_step'] = self.current_step
            result['adaptive_mode'] = self.adaptive_mode  # 覆寫為更新後的模式

            if self.current_step >= self.total_steps:
                self.completed = True
                result['all_done'] = True
                result['feedback'] = self._gen_done_feedback()
            else:
                next_step = self.sop['steps'][self.current_step]
                result['feedback'] = self._gen_correct_feedback(action, step, next_step)
        else:
            self.mistake_count += 1
            # 依錯誤嚴重程度判斷錯誤類型
            if comp_ok and not act_ok:
                # 零件對但動作錯 → 方向正確，輕度錯誤
                mistake_level = 'partial_action'
            elif not comp_ok and act_ok:
                # 動作類型對但零件錯 → 中度錯誤
                mistake_level = 'partial_component'
            else:
                # 零件和動作都錯 → 完全偏離，重度錯誤
                mistake_level = 'full_wrong'
            # 先更新自適應模式（與自適應系統統一：扣分用更新後的模式）
            # 這樣第 N 次連錯觸發降級時，本次扣分就已反映新模式，不落後一步
            self._update_adaptive_mode(False)
            # 扣分依更新後的自適應模式 × 錯誤嚴重度決定
            # challenge：要求高，扣較多；remedial：學習中，扣較少
            _DEDUCTION_TABLE = {
                #                partial_action  partial_component  full_wrong
                'challenge':   {'partial_action': 8, 'partial_component': 10, 'full_wrong': 15},
                'standard':    {'partial_action': 5, 'partial_component':  7, 'full_wrong': 12},
                'scaffolding': {'partial_action': 3, 'partial_component':  5, 'full_wrong':  8},
                'remedial':    {'partial_action': 2, 'partial_component':  3, 'full_wrong':  5},
            }
            deduction = _DEDUCTION_TABLE[self.adaptive_mode][mistake_level]
            self.score = max(0, self.score - deduction)
            result['feedback'] = self._gen_wrong_feedback(component, action, step,
                                                          mistake_level=mistake_level)
            result['score'] = self.score
            result['adaptive_mode'] = self.adaptive_mode  # 覆寫為更新後的模式
            result['mistake_level'] = mistake_level
            result['deduction'] = deduction

        return result

    # ── 求助提示 ──────────────────────────────────────────────────────────────
    def get_hint(self) -> dict:
        self.hint_count += 1
        # 依扣分前的分數決定提示層級（分數愈高提示愈少）
        if self.score >= 85:
            hint_mode = 'hint_challenge'
        elif self.score >= 65:
            hint_mode = 'hint_standard'
        elif self.score >= 40:
            hint_mode = 'hint_scaffolding'
        else:
            hint_mode = 'hint_remedial'
        self.score = max(0, self.score - 10)
        step = self.sop['steps'][self.current_step]
        tmpl = random.choice(_HINT_TEMPLATES[hint_mode])
        hint = tmpl.format(
            fault_system=self.sop['fault_system'],
            hint_component=step['hint_component'],
            hint_action=step['hint_action'],
            reason=step['reason'],
            step_num=self.current_step + 1,
        )
        return {
            'hint': hint,
            'score': self.score,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'adaptive_mode': self.adaptive_mode,
            'hint_mode': hint_mode,
        }

    # ── 回饋生成 ──────────────────────────────────────────────────────────────
    def _gen_correct_feedback(self, action: str, step: dict, next_step: dict) -> str:
        tmpl = random.choice(_CORRECT_TEMPLATES[self.adaptive_mode])
        return tmpl.format(
            action=action,
            reason=step['reason'],
            next_hint=next_step['hint_component'],
            next_step=next_step['hint_action'],
        )

    def _gen_wrong_feedback(self, component: str, action: str, step: dict,
                            mistake_level: str = 'full_wrong') -> str:
        # 依錯誤嚴重度加上前綴說明，再套用對應模式模板
        if mistake_level == 'partial_action':
            prefix = f'零件「{component}」選對了，但這步的動作不對。'
        elif mistake_level == 'partial_component':
            prefix = f'動作方向有點接近，但零件選錯了。'
        else:
            prefix = ''  # 完全錯誤，直接給模板提示

        tmpl = random.choice(_WRONG_TEMPLATES[self.adaptive_mode])
        body = tmpl.format(
            fault_system=self.sop['fault_system'],
            hint_component=step['hint_component'],
            hint_action=step['hint_action'],
            reason=step['reason'],
        )
        return f'{prefix}{body}' if prefix else body

    def _gen_done_feedback(self) -> str:
        tmpl = _DONE_TEMPLATES[self.adaptive_mode]
        steps_summary = ' → '.join(s['desc'] for s in self.sop['steps'])
        return tmpl.format(
            fault_name=self.sop['name'],
            steps_summary=steps_summary,
        )
