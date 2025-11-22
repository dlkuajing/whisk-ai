#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试100张图片限制自动处理功能
"""

import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from whisk_core_v2 import WhiskAutomationCoreV2

def test_limit_handling():
    """测试限制处理功能"""

    print("=" * 60)
    print("100张图片限制处理功能测试")
    print("=" * 60)

    # 创建自动化实例
    automator = WhiskAutomationCoreV2(save_directory="downloads")

    try:
        # 连接浏览器
        print("\n1. 连接浏览器...")
        automator.connect_browser()
        print("   [OK] 浏览器已连接")
        time.sleep(2)

        # 测试页面检测
        print("\n2. 测试页面状态检测...")
        result = automator.check_and_handle_limit_page()
        if result:
            print("   [INFO] 检测到限制页面并尝试恢复")
        else:
            print("   [OK] 当前页面正常")

        # 测试输入提示词（会自动处理限制页面）
        print("\n3. 测试输入提示词功能...")
        test_prompt = "测试提示词 - Test Prompt"
        try:
            automator.input_prompt(test_prompt)
            print("   [OK] 提示词输入成功")
        except Exception as e:
            print(f"   [ERROR] 提示词输入失败: {e}")

        # 如果需要测试完整的生成流程
        print("\n4. 测试小批量生成（模拟接近限制）...")
        print("   提示：这将生成2次（4张图片）用于测试")
        response = input("   是否继续？(y/n): ")

        if response.lower() == 'y':
            # 设置生成计数器以模拟接近限制
            automator.generation_count = 43  # 设置为接近45的值

            # 执行生成
            automator.generate_images(
                prompt="测试图片生成",
                count=1,  # 只生成1次
                aspect_ratio="1:1",
                min_delay=3,
                max_delay=5
            )
            print("   [OK] 测试生成完成")

        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 测试过程出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理
        if automator.page:
            print("\n正在关闭浏览器...")
            automator.page.close()
        if automator.browser:
            automator.browser.close()
        print("测试结束")

if __name__ == "__main__":
    test_limit_handling()