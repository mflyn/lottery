from lottery_checker_sport import LotteryChecker

def test_prize_rules():
    checker = LotteryChecker()

    # 测试所有可能的中奖组合
    test_cases = [
        # 前区匹配数, 后区匹配数, 预期奖级
        (5, 2, "一等奖"),  # 5+2
        (5, 1, "二等奖"),  # 5+1
        (5, 0, "三等奖"),  # 5+0
        (4, 2, "四等奖"),  # 4+2
        (4, 1, "五等奖"),  # 4+1
        (3, 2, "六等奖"),  # 3+2
        (4, 0, "七等奖"),  # 4+0
        (3, 1, "八等奖"),  # 3+1
        (2, 2, "八等奖"),  # 2+2
        (3, 0, "九等奖"),  # 3+0
        (1, 2, "九等奖"),  # 1+2
        (2, 1, "九等奖"),  # 2+1
        (0, 2, "九等奖"),  # 0+2
        (2, 0, None),      # 2+0 不中奖
        (1, 1, None),      # 1+1 不中奖
        (1, 0, None),      # 1+0 不中奖
        (0, 1, None),      # 0+1 不中奖
        (0, 0, None)       # 0+0 不中奖
    ]

    # 模拟开奖号码
    result_front = [1, 2, 3, 4, 5]
    result_back = [1, 2]

    # 直接测试匹配数量
    for front_matches, back_matches, expected_prize in test_cases:
        # 直接使用内部方法模拟匹配数量
        class MockChecker(LotteryChecker):
            def check_win(self, my_front, my_back, result_front, result_back):
                # 覆盖原方法，直接使用指定的匹配数量
                for rule in self.prize_rules:
                    if front_matches == rule["front"] and back_matches == rule["back"]:
                        return rule["level"]
                return None

        mock_checker = MockChecker()
        prize = mock_checker.check_win([], [], [], [])  # 参数不重要，因为我们覆盖了方法

        # 验证结果
        if prize == expected_prize:
            result = "通过"
        else:
            result = f"失败 (得到 {prize}, 期望 {expected_prize})"

        print(f"测试 {front_matches}+{back_matches}: {result}")

if __name__ == "__main__":
    print("开始测试大乐透中奖规则...")
    test_prize_rules()
    print("测试完成")
