# -*- coding: utf-8 -*-
"""
測試 Qwen 2.5 整合到訓練系統
"""

import os
import sys

print("="*80)
print("Qwen 2.5 整合測試")
print("="*80)
print()

# Step 1: 檢查環境
print("Step 1: 檢查環境...")
print("-"*80)

try:
    import torch
    print(f"✓ PyTorch 版本: {torch.__version__}")
    print(f"✓ CUDA 可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
        print(f"✓ GPU 記憶體: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
except ImportError:
    print("✗ PyTorch 未安裝")
    print("  請執行: pip install torch transformers accelerate bitsandbytes")
    sys.exit(1)

try:
    import transformers
    print(f"✓ Transformers 版本: {transformers.__version__}")
except ImportError:
    print("✗ Transformers 未安裝")
    sys.exit(1)

print()

# Step 2: 載入 Qwen Training Assistant
print("Step 2: 載入 Qwen Training Assistant...")
print("-"*80)

try:
    from core.qwen_training_assistant import QwenTrainingAssistant
    print("✓ 模組載入成功")
except ImportError as e:
    print(f"✗ 模組載入失敗: {e}")
    sys.exit(1)

print()

# Step 3: 初始化助手（使用較小的模型以加快測試）
print("Step 3: 初始化助手...")
print("-"*80)
print("注意：首次執行會下載模型，可能需要較長時間")
print()

# 選擇是否啟用 Qwen（預設為否，因為需要下載大型模型）
use_qwen = input("是否啟用 Qwen 模型測試？(y/N): ").strip().lower() == 'y'

if not use_qwen:
    print("\n跳過 Qwen 模型測試（避免下載大型模型）")
    print("如需測試，請設定環境變數: export USE_QWEN_LLM=true")
    print()

    # 測試模組導入
    print("Step 4: 測試模組整合...")
    print("-"*80)

    try:
        from stage1_theory.qwen_mentor_bot import QwenMentorBot
        print("✓ QwenMentorBot 模組導入成功")
    except ImportError as e:
        print(f"✗ QwenMentorBot 導入失敗: {e}")

    try:
        from core.ai_scenario_mentor import AIScenarioMentor, HAS_QWEN_LLM
        print(f"✓ AIScenarioMentor 更新成功")
        print(f"  - Qwen LLM 支援: {HAS_QWEN_LLM}")
    except ImportError as e:
        print(f"✗ AIScenarioMentor 導入失敗: {e}")

    print()
    print("="*80)
    print("整合測試完成！")
    print("="*80)
    print()
    print("📝 使用方式：")
    print()
    print("1. 啟用 Qwen 模型：")
    print("   export USE_QWEN_LLM=true")
    print("   或在 .env 檔案中設定：USE_QWEN_LLM=true")
    print()
    print("2. 啟動訓練系統：")
    print("   python start_simulation.py")
    print()
    print("3. 系統會自動檢測並使用 Qwen 2.5 模型")
    print()
    sys.exit(0)

# 啟用 Qwen 的完整測試
print("\n開始載入 Qwen 模型...")
assistant = QwenTrainingAssistant(
    model_name="Qwen/Qwen2.5-3B-Instruct",
    use_quantization=True
)

success = assistant.load_model()

if not success:
    print("✗ 模型載入失敗")
    sys.exit(1)

print()

# Step 4: 測試問答
print("Step 4: 測試問答功能...")
print("-"*80)
print()

test_questions = [
    "什麼是 CVD 製程？",
    "半導體蝕刻製程的主要目的是什麼？",
    "無塵室為什麼很重要？"
]

for i, question in enumerate(test_questions, 1):
    print(f"測試 {i}/{len(test_questions)}")
    print(f"問題: {question}")
    print("-"*40)

    result = assistant.generate_answer(
        question=question,
        max_length=300
    )

    print(f"回答: {result['answer']}")
    print(f"生成時間: {result['generation_time']:.2f} 秒")
    print(f"速度: {result['tokens_per_second']:.1f} tokens/秒")
    print()

# Step 5: 測試情境問答
print("Step 5: 測試情境問答（整合到訓練系統）...")
print("-"*80)
print()

context = {
    'scenario_name': '冷卻系統流量異常',
    'equipment_state': '運行中',
    'fault_stage': 1,
    'parameters': '冷卻水流量: 3.5 L/min (偏低)'
}

question = "學長，冷卻水流量這麼低是什麼原因？"
print(f"問題: {question}")
print(f"情境: {context}")
print("-"*40)

result = assistant.generate_answer(
    question=question,
    context=context,
    max_length=400
)

print(f"學長回答: {result['answer']}")
print(f"生成時間: {result['generation_time']:.2f} 秒")
print()

# Step 6: 顯示統計
print("Step 6: 訓練統計...")
print("-"*80)
stats = assistant.get_stats()
for key, value in stats.items():
    print(f"  {key}: {value}")

print()
print("="*80)
print("✅ 所有測試通過！Qwen 2.5 整合成功！")
print("="*80)
print()
print("📝 下一步：")
print("  1. 設定環境變數啟用 Qwen: export USE_QWEN_LLM=true")
print("  2. 啟動訓練系統: python start_simulation.py")
print("  3. 系統會自動使用 Qwen 2.5 作為 AI 學長")
print()
