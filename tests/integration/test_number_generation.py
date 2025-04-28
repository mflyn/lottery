import unittest
import pandas as pd
from src.core.models.lottery_number import LotteryNumber, DLTNumber, SSQNumber
from src.core.number_generator import LotteryNumberGenerator
from src.core.analyzers import PatternAnalyzer, FrequencyAnalyzer

class TestNumberGenerationSystem(unittest.TestCase):
    """号码生成系统集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.dlt_generator = LotteryNumberGenerator('dlt')
        cls.ssq_generator = LotteryNumberGenerator('ssq')
        cls.test_data = cls._load_test_data()
    
    @staticmethod
    def _load_test_data():
        """加载测试数据"""
        # 创建示例数据
        dlt_data = {
            'date': ['2024-01-01', '2024-01-03', '2024-01-05'],
            'front_numbers': ['01,04,17,25,32', '03,08,15,27,35', '02,07,13,24,31'],
            'back_numbers': ['06,11', '04,09', '05,10']
        }
        return pd.DataFrame(dlt_data)
    
    def test_random_generation(self):
        """测试随机生成功能"""
        # 1. 大乐透随机生成
        dlt_numbers = self.dlt_generator.generate_numbers(
            count=5,
            strategy='random'
        )
        
        self.assertEqual(len(dlt_numbers), 5)
        for number in dlt_numbers:
            self.assertEqual(number.lottery_type, 'dlt')
            self.assertEqual(len(number.front), 5)
            self.assertEqual(len(number.back), 2)
            
        # 2. 双色球随机生成
        ssq_numbers = self.ssq_generator.generate_numbers(
            count=5,
            strategy='random'
        )
        
        self.assertEqual(len(ssq_numbers), 5)
        for number in ssq_numbers:
            self.assertEqual(number.lottery_type, 'ssq')
            self.assertEqual(len(number.red), 6)
            self.assertIsInstance(number.blue, int)
    
    def test_smart_generation(self):
        """测试智能生成功能"""
        # 1. 准备测试数据
        dlt_numbers = self.dlt_generator.generate_numbers(
            count=3,
            strategy='smart',
            history_data=self.test_data,
            weights={
                'frequency': 0.4,
                'pattern': 0.3,
                'random': 0.3
            }
        )
        
        # 2. 验证结果
        self.assertEqual(len(dlt_numbers), 3)
        for number in dlt_numbers:
            # 验证号码格式
            self.assertEqual(number.lottery_type, 'dlt')
            self.assertEqual(len(number.front), 5)
            self.assertEqual(len(number.back), 2)
            
            # 验证号码范围
            for n in number.front:
                self.assertTrue(1 <= n <= 35)
            for n in number.back:
                self.assertTrue(1 <= n <= 12)
            
            # 验证号码排序
            self.assertEqual(number.front, sorted(number.front))
            self.assertEqual(number.back, sorted(number.back))
    
    def test_end_to_end_workflow(self):
        """测试完整工作流"""
        try:
            # 1. 准备数据
            history_data = self.test_data
            
            # 2. 初始化分析器
            pattern_analyzer = PatternAnalyzer('dlt')
            frequency_analyzer = FrequencyAnalyzer('dlt')
            
            # 3. 分析历史数据
            pattern_data = pattern_analyzer.analyze(history_data)
            frequency_data = frequency_analyzer.analyze(history_data)
            
            # 4. 生成号码
            numbers = self.dlt_generator.generate_numbers(
                count=5,
                strategy='smart',
                history_data=history_data,
                pattern_data=pattern_data,
                frequency_data=frequency_data
            )
            
            # 5. 验证结果
            self.assertEqual(len(numbers), 5)
            for number in numbers:
                # 基本验证
                self.assertIsNotNone(number)
                self.assertEqual(number.lottery_type, 'dlt')
                
                # 格式验证
                self.assertEqual(len(number.front), 5)
                self.assertEqual(len(number.back), 2)
                
                # 范围验证
                for n in number.front:
                    self.assertTrue(1 <= n <= 35)
                for n in number.back:
                    self.assertTrue(1 <= n <= 12)
                    
                # 重复验证
                self.assertEqual(len(set(number.front)), 5)
                self.assertEqual(len(set(number.back)), 2)
            
        except Exception as e:
            self.fail(f"测试流程失败: {str(e)}")

if __name__ == '__main__':
    unittest.main()
