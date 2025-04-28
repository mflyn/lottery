import unittest
from src.core.generators.base import NumberGenerator
from src.core.generators.random_generator import RandomGenerator

class TestRandomGenerator(unittest.TestCase):
    
    def setUp(self):
        self.dlt_generator = RandomGenerator('dlt')
        self.ssq_generator = RandomGenerator('ssq')
    
    def test_invalid_lottery_type(self):
        """测试无效的彩票类型"""
        with self.assertRaises(ValueError):
            RandomGenerator('invalid')
    
    def test_generate_single_dlt(self):
        """测试大乐透单注生成"""
        numbers = self.dlt_generator.generate_single()
        
        # 验证结构
        self.assertIn('front', numbers)
        self.assertIn('back', numbers)
        
        # 验证前区号码
        self.assertEqual(len(numbers['front']), 5)
        self.assertTrue(all(1 <= n <= 35 for n in numbers['front']))
        self.assertEqual(len(set(numbers['front'])), 5)  # 确保无重复
        
        # 验证后区号码
        self.assertEqual(len(numbers['back']), 2)
        self.assertTrue(all(1 <= n <= 12 for n in numbers['back']))
        self.assertEqual(len(set(numbers['back'])), 2)  # 确保无重复
    
    def test_generate_single_ssq(self):
        """测试双色球单注生成"""
        numbers = self.ssq_generator.generate_single()
        
        # 验证结构
        self.assertIn('red', numbers)
        self.assertIn('blue', numbers)
        
        # 验证红球号码
        self.assertEqual(len(numbers['red']), 6)
        self.assertTrue(all(1 <= n <= 33 for n in numbers['red']))
        self.assertEqual(len(set(numbers['red'])), 6)  # 确保无重复
        
        # 验证蓝球号码
        self.assertEqual(len(numbers['blue']), 1)
        self.assertTrue(1 <= numbers['blue'][0] <= 16)
    
    def test_generate_multiple(self):
        """测试多注生成"""
        count = 5
        numbers_list = self.dlt_generator.generate_multiple(count)
        
        # 验证生成数量
        self.assertEqual(len(numbers_list), count)
        
        # 验证每注号码格式
        for numbers in numbers_list:
            self.assertTrue(self.dlt_generator.validate_numbers(numbers))
    
    def test_validate_numbers(self):
        """测试号码验证"""
        # 测试有效号码
        valid_dlt = {
            'front': [1, 2, 3, 4, 5],
            'back': [1, 2]
        }
        self.assertTrue(self.dlt_generator.validate_numbers(valid_dlt))
        
        # 测试无效号码
        invalid_cases = [
            {'front': [1, 2, 3, 4], 'back': [1, 2]},  # 前区号码不足
            {'front': [1, 2, 3, 4, 36], 'back': [1, 2]},  # 前区号码超范围
            {'front': [1, 2, 3, 4, 5], 'back': [1]},  # 后区号码不足
            {'front': [1, 2, 3, 4, 5], 'back': [1, 13]},  # 后区号码超范围
            {'front': [1, 1, 2, 3, 4], 'back': [1, 2]},  # 前区号码重复
            {'front': [1, 2, 3, 4, 5], 'back': [1, 1]},  # 后区号码重复
        ]
        
        for invalid_case in invalid_cases:
            self.assertFalse(self.dlt_generator.validate_numbers(invalid_case))

if __name__ == '__main__':
    unittest.main()