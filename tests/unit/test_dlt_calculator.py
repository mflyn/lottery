import unittest
from src.core.dlt_calculator import DLTCalculator

class TestDLTCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = DLTCalculator()

    def test_validate_numbers_valid(self):
        self.assertTrue(self.calculator.validate_numbers([1, 5, 10, 20, 35], 'front'))
        self.assertTrue(self.calculator.validate_numbers([1, 12], 'back'))

    def test_validate_numbers_invalid(self):
        self.assertFalse(self.calculator.validate_numbers([0, 36], 'front'))
        self.assertFalse(self.calculator.validate_numbers([0, 13], 'back'))
        self.assertFalse(self.calculator.validate_numbers([], 'front'))

    def test_calculate_complex_bet_basic(self):
        result = self.calculator.calculate_complex_bet([1,2,3,4,5], [1,2])
        self.assertEqual(result.total_bets, 1)
        self.assertEqual(result.total_amount, 2)

    def test_calculate_complex_bet_multiple(self):
        result = self.calculator.calculate_complex_bet([1,2,3,4,5,6], [1,2,3])
        # C(6,5)=6, C(3,2)=3, 6*3=18
        self.assertEqual(result.total_bets, 18)
        self.assertEqual(result.total_amount, 36)

    def test_calculate_complex_bet_additional(self):
        result = self.calculator.calculate_complex_bet([1,2,3,4,5], [1,2], is_additional=True)
        self.assertEqual(result.total_bets, 1)
        self.assertEqual(result.total_amount, 3)

    def test_calculate_complex_bet_invalid(self):
        with self.assertRaises(ValueError):
            self.calculator.calculate_complex_bet([1,2,3,4], [1,2])  # 前区不足5个
        with self.assertRaises(ValueError):
            self.calculator.calculate_complex_bet([1,2,3,4,5], [1])  # 后区不足2个
        with self.assertRaises(ValueError):
            self.calculator.calculate_complex_bet([0,2,3,4,5], [1,2])  # 非法号码

    def test_calculate_dantuo_bet_basic(self):
        result = self.calculator.calculate_dantuo_bet([1], [2,3,4,5], [1], [2])
        # 前区: 1胆码+4拖码，选4拖码中4个，C(4,4)=1；后区: 1胆码+1拖码，选1拖码中1个，C(1,1)=1
        self.assertEqual(result.total_bets, 1)
        self.assertEqual(result.total_amount, 2)

    def test_calculate_dantuo_bet_multiple(self):
        result = self.calculator.calculate_dantuo_bet([1,2], [3,4,5,6], [], [1,2,3])
        # 前区: 2胆码+4拖码，选3拖码中3个，C(4,3)=4；后区: 0胆码+3拖码，选2个，C(3,2)=3
        self.assertEqual(result.total_bets, 12)
        self.assertEqual(result.total_amount, 24)

    def test_calculate_dantuo_bet_invalid(self):
        with self.assertRaises(ValueError):
            self.calculator.calculate_dantuo_bet([1,2,3,4,5], [6,7], [1], [2])  # 前区胆码超限
        with self.assertRaises(ValueError):
            self.calculator.calculate_dantuo_bet([1], [2,3], [1,2], [3,4])  # 后区胆码超限
        with self.assertRaises(ValueError):
            self.calculator.calculate_dantuo_bet([1], [2], [1], [2])  # 拖码数量不足

    def test_check_prize(self):
        # 一等奖
        level, prize = self.calculator.check_prize([1,2,3,4,5,1,2], [1,2,3,4,5,1,2])
        self.assertEqual(level, 1)
        self.assertTrue(prize > 0)
        # 九等奖（前区0+后区2）
        level, prize = self.calculator.check_prize([11,12,13,14,15,1,2], [1,2,3,4,5,1,2])
        self.assertEqual(level, 9)
        # 九等奖（前区1+后区2）
        level, prize = self.calculator.check_prize([1,12,13,14,15,1,2], [1,2,3,4,5,1,2])
        self.assertEqual(level, 9)
        # 九等奖（前区2+后区1）
        level, prize = self.calculator.check_prize([1,2,13,14,15,1,3], [1,2,3,4,5,1,2])
        self.assertEqual(level, 9)
        # 九等奖（前区3+后区0）
        level, prize = self.calculator.check_prize([1,2,3,14,15,3,4], [1,2,3,4,5,1,2])
        self.assertEqual(level, 9)
        # 未中奖
        level, prize = self.calculator.check_prize([6,7,8,9,10,11,12], [1,2,3,4,5,1,2])
        self.assertEqual(level, 0)

    def test_check_prize_additional(self):
        # 一等奖追加
        level, prize = self.calculator.check_prize([1,2,3,4,5,1,2], [1,2,3,4,5,1,2], is_additional=True)
        self.assertEqual(level, 1)
        self.assertTrue(prize > 10000000)

if __name__ == '__main__':
    unittest.main() 