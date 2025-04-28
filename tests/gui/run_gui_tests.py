import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'

import unittest
import sys
from pathlib import Path

def run_gui_tests():
    """运行GUI测试"""
    # 添加项目根目录到Python路径
    project_root = Path(__file__).parent.parent.parent
    sys.path.append(str(project_root))
    
    # 加载测试
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_gui_tests()
    sys.exit(0 if success else 1)
