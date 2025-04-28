import unittest
from src.core.ssq_calculator import SSQCalculator

class TestSSQCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = SSQCalculator()

    def test_validate_numbers_valid(self):
        self.assertTrue(self.calculator.validate_numbers([1, 5, 10, 20, 33], 'red'))
        self.assertTrue(self.calculator.validate_numbers([1, 16], 'blue'))

    def test_validate_numbers_invalid(self):
        self.assertFalse(self.calculator.validate_numbers([0, 34], 'red'))
        self.assertFalse(self.calculator.validate_numbers([0, 17], 'blue'))
        self.assertFalse(self.calculator.validate_numbers([], 'red'))

    def test_calculate_complex_bet_basic(self):
        result = self.calculator.calculate_complex_bet([1,2,3,4,5,6], [1])
        self.assertEqual(result.total_bets, 1)
        self.assertEqual(result.total_amount, 2)

    def test_calculate_complex_bet_multiple(self):
        result = self.calculator.calculate_complex_bet([1,2,3,4,5,6,7], [1,2])
        # C(7,6)=7, 2蓝球，7*2=14
        self.assertEqual(result.total_bets, 14)
        self.assertEqual(result.total_amount, 28)

    def test_calculate_complex_bet_invalid(self):
        with self.assertRaises(ValueError):
            self.calculator.calculate_complex_bet([1,2,3,4,5], [1])  # 红球不足6个
        with self.assertRaises(ValueError):
            self.calculator.calculate_complex_bet([1,2,3,4,5,6], [])  # 蓝球不足1个
        with self.assertRaises(ValueError):
            self.calculator.calculate_complex_bet([0,2,3,4,5,6], [1])  # 非法号码

    def test_calculate_dantuo_bet_basic(self):
        result = self.calculator.calculate_dantuo_bet([1], [2,3,4,5,6], [1])
        # 1胆码+5拖码，选5拖码中5个，C(5,5)=1
        self.assertEqual(result.total_bets, 1)
        self.assertEqual(result.total_amount, 2)

    def test_calculate_dantuo_bet_multiple(self):
        result = self.calculator.calculate_dantuo_bet([1,2], [3,4,5,6,7], [1,2])
        # 2胆码+5拖码，选4拖码中4个，C(5,4)=5，2蓝球，5*2=10
        self.assertEqual(result.total_bets, 10)
        self.assertEqual(result.total_amount, 20)

    def test_calculate_dantuo_bet_invalid(self):
        with self.assertRaises(ValueError):
            self.calculator.calculate_dantuo_bet([1,2,3,4,5,6], [7,8], [1])  # 红球胆码超限
        with self.assertRaises(ValueError):
            self.calculator.calculate_dantuo_bet([1], [2,3], [])  # 蓝球不足
        with self.assertRaises(ValueError):
            self.calculator.calculate_dantuo_bet([1], [2], [0])  # 非法蓝球

    def test_check_prize(self):
        # 一等奖
        level, prize = self.calculator.check_prize([1,2,3,4,5,6,1], [1,2,3,4,5,6,1])
        self.assertEqual(level, 1)
        self.assertTrue(prize > 0)
        # 六等奖
        level, prize = self.calculator.check_prize([1,2,3,4,5,6,1], [7,8,9,10,11,12,1])
        self.assertEqual(level, 6)
        # 未中奖
        level, prize = self.calculator.check_prize([1,2,3,4,5,6,1], [7,8,9,10,11,12,2])
        self.assertEqual(level, 0)

if __name__ == '__main__':
    unittest.main() 