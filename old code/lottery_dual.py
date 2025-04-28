import random
from collections import Counter

def generate_lottery_numbers():
    """生成一注双色球号码"""
    red_balls = random.sample(range(1, 34), 6)
    blue_ball = random.choice(range(1, 17))
    red_balls.sort()
    return red_balls, blue_ball

def run_simulation(num_runs=10000000):
    """运行模拟，返回红球和蓝球的出现次数统计"""
    red_ball_counts = Counter()
    blue_ball_counts = Counter()

    for _ in range(num_runs):
        red_balls, blue_ball = generate_lottery_numbers()
        for red_ball in red_balls:
            red_ball_counts[red_ball] += 1
        blue_ball_counts[blue_ball] += 1

    return red_ball_counts, blue_ball_counts

def generate_top_numbers():
    """生成出现次数最多的号码"""
    red_ball_counts, blue_ball_counts = run_simulation()

    top_red_balls = [ball for ball, _ in red_ball_counts.most_common(6)]
    top_red_balls.sort()
    top_blue_ball = blue_ball_counts.most_common(1)[0][0]

    return top_red_balls, top_blue_ball

# 生成号码
top_red_balls, top_blue_ball = generate_top_numbers()

# 打印结果
print("生成的号码：")
print(f"红球：{top_red_balls}，蓝球：{top_blue_ball}")