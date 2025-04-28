import json
from collections import Counter
import pandas as pd

# Load the dual_history.json file
with open('dual_history.json', 'r', encoding='utf-8') as f:
    lottery_data = json.load(f)

# Extract the data
draws = lottery_data.get('data', [])

# Count the frequency of red and blue balls
red_balls = []
blue_balls = []

# 处理所有获取到的数据，不限制期数
for draw in draws:
    red_balls.extend(draw.get('red_numbers', []))
    blue_balls.append(draw.get('blue_number'))

# Count occurrences
red_counter = Counter(red_balls)
blue_counter = Counter(blue_balls)

# Sort by frequency (most to least)
red_sorted = red_counter.most_common()
blue_sorted = blue_counter.most_common()

# 计算总期数和理论概率
total_draws = len(draws)
total_red_balls = len(red_balls)
theoretical_red_prob = 6 / 33  # 每期6个红球，总共33个红球号码
theoretical_blue_prob = 1 / 16  # 每期1个蓝球，总共16个蓝球号码

# 创建DataFrame并添加百分比和偏差列
red_df = pd.DataFrame(red_sorted, columns=['红球号码', '出现次数'])
red_df['出现率'] = red_df['出现次数'] / total_draws * 100
red_df['理论次数'] = total_draws * theoretical_red_prob
red_df['偏差率'] = (red_df['出现次数'] - red_df['理论次数']) / red_df['理论次数'] * 100

blue_df = pd.DataFrame(blue_sorted, columns=['蓝球号码', '出现次数'])
blue_df['出现率'] = blue_df['出现次数'] / total_draws * 100
blue_df['理论次数'] = total_draws * theoretical_blue_prob
blue_df['偏差率'] = (blue_df['出现次数'] - blue_df['理论次数']) / blue_df['理论次数'] * 100

# 设置显示格式
pd.set_option('display.float_format', '{:.2f}'.format)

# 打印结果
print(f"分析过去 {total_draws} 期双色球开奖结果:")
print(f"总计分析红球 {total_red_balls} 个，蓝球 {total_draws} 个")

print("\n红球出现频率 (从高到低):")
print(red_df.to_string(index=False))

print("\n红球统计信息:")
print(f"平均出现次数: {red_df['出现次数'].mean():.2f}")
print(f"最大偏差率: {red_df['偏差率'].abs().max():.2f}%")
print(f"标准差: {red_df['出现次数'].std():.2f}")

print("\n蓝球出现频率 (从高到低):")
print(blue_df.to_string(index=False))

print("\n蓝球统计信息:")
print(f"平均出现次数: {blue_df['出现次数'].mean():.2f}")
print(f"最大偏差率: {blue_df['偏差率'].abs().max():.2f}%")
print(f"标准差: {blue_df['出现次数'].std():.2f}")
