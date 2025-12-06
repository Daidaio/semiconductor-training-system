# -*- coding: utf-8 -*-
"""
測試「詢問」vs「檢查」的區分
"""

from core.natural_language_controller import NaturalLanguageController

nlu = NaturalLanguageController()

test_cases = [
    ('插頭鬆了嗎', 'ask'),
    ('溫度正常嗎', 'ask'),
    ('流量OK嗎', 'ask'),
    ('現在還有異常嗎', 'ask'),
    ('檢查冷卻水', 'check'),
    ('看一下溫度', 'check'),
]

print('=' * 60)
print('測試「詢問」vs「檢查」區分')
print('=' * 60)
print()

success = 0
total = len(test_cases)

for user_input, expected_intent in test_cases:
    result = nlu.parse_input(user_input)
    match = result['intent'] == expected_intent

    if match:
        success += 1
        status = '[OK]'
    else:
        status = '[FAIL]'

    print(f'{status} 輸入: {user_input}')
    print(f'     期望意圖: {expected_intent}')
    print(f'     實際意圖: {result["intent"]}')
    print(f'     信心度: {result["confidence"]:.2f}')
    print()

print('=' * 60)
print(f'結果: {success}/{total} 通過 ({success/total*100:.1f}%)')
print('=' * 60)

if success == total:
    print('\n[SUCCESS] 所有測試通過！')
else:
    print(f'\n[WARNING] 有 {total - success} 個測試失敗')
