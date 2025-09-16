#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def generate_ssq_numbers():
    """Generates 10 sets of smart SSQ numbers."""
    try:
        from core.generators.factory import create_generator
        from core.logging_config import setup_logging, get_logger

        # Setup logging
        setup_logging()
        logger = get_logger(__name__)

        logger.info("使用优化后算法，生成10注双色球号码...")
        ssq_smart_generator = create_generator('smart', 'ssq')
        ssq_smart_numbers = ssq_smart_generator.generate(count=10)

        if ssq_smart_numbers:
            print("--- 10注备选号码 ---")
            for i, number in enumerate(ssq_smart_numbers, 1):
                # A special format to make it easy to parse later
                print(f"CANDIDATE:{number.red}|{number.blue}")
            print("------------------")
        else:
            print("生成号码失败。")

    except Exception as e:
        print(f"执行过程中发生错误: {e}")

if __name__ == "__main__":
    generate_ssq_numbers()
