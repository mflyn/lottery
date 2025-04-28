import unittest
import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.core.ssq_analyzer import SSQAnalyzer

class TestNumberPatterns(unittest.TestCase):
    def setUp(self):
        self.analyzer = SSQAnalyzer(debug_mode=True)
        
        # 测试数据
        self.test_data = [
            {
                'date': '2024-01-01',
                'red': '1,2,3,15,25,33',
                'blue': '16'
            },
            {
                'date': '2024-01-03',
                'red': '2,3,8,15,25,33',
                'blue': '12'
            },
            {
                'date': '2024-01-05',
                'red': '5,7,9,11,13,31',
                'blue': '8'
            },
            {
                'date': '2024-01-07',
                'red': '2,4,6,8,10,32',
                'blue': '5'
            }
        ]

    def test_consecutive_numbers(self):
        """测试连号分析"""
        result = self.analyzer._analyze_consecutive_numbers(self.test_data)
        self.assertIsInstance(result, dict)
        self.assertIn('consecutive_distribution', result)
        self.assertIn('max_consecutive_found', result)

if __name__ == '__main__':
    unittest.main()
