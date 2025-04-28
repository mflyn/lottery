from lottery_checker_sport import LotteryChecker

def test_real_case():
    checker = LotteryChecker()
    
    # 第25042期大乐透开奖结果
    result_front = [6, 8, 11, 18, 20]
    result_back = [5, 11]
    
    # 测试第2注号码：前区[7, 8, 20, 25, 33]，后区[5, 11]
    my_front = [7, 8, 20, 25, 33]
    my_back = [5, 11]
    
    # 检查中奖结果
    prize = checker.check_win(my_front, my_back, result_front, result_back)
    
    # 计算匹配数量
    front_matches = len(set(my_front) & set(result_front))
    back_matches = len(set(my_back) & set(result_back))
    
    print(f"前区匹配: {front_matches}个 ({set(my_front) & set(result_front)})")
    print(f"后区匹配: {back_matches}个 ({set(my_back) & set(result_back)})")
    print(f"中奖结果: {prize}")
    
    # 验证是否为八等奖
    if prize == "八等奖":
        print("验证成功: 2+2 组合正确地被识别为八等奖")
    else:
        print(f"验证失败: 2+2 组合被识别为 {prize}，应该是八等奖")

if __name__ == "__main__":
    print("测试实际案例...")
    test_real_case()
    print("测试完成")
