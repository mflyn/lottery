import json
from collections import Counter
import pandas as pd

# 加载双色球历史数据
with open('dual_history.json', 'r', encoding='utf-8') as f:
    lottery_data = json.load(f)

# 提取数据
draws = lottery_data.get('data', [])
total_periods = len(draws)

# 设置要分析的期数
periods_to_analyze = [100, 200, 300]

# 设置显示格式
pd.set_option('display.float_format', '{:.2f}'.format)

# 对每个期数进行分析
for periods in periods_to_analyze:
    if periods > total_periods:
        print(f"警告：请求分析的期数 {periods} 超过了可用的总期数 {total_periods}")
        continue
        
    print(f"\n{'='*80}")
    print(f"分析过去 {periods} 期双色球开奖结果")
    print(f"{'='*80}")
    
    # 统计红球和蓝球出现次数
    red_balls = []
    blue_balls = []
    
    for draw in draws[:periods]:
        red_balls.extend(draw.get('red_numbers', []))
        blue_balls.append(draw.get('blue_number'))
    
    # 计数
    red_counter = Counter(red_balls)
    blue_counter = Counter(blue_balls)
    
    # 排序
    red_sorted = red_counter.most_common()
    blue_sorted = blue_counter.most_common()
    
    # 计算理论概率
    theoretical_red_prob = 6 / 33  # 每期6个红球，总共33个红球号码
    theoretical_blue_prob = 1 / 16  # 每期1个蓝球，总共16个蓝球号码
    
    # 创建DataFrame并添加统计列
    red_df = pd.DataFrame(red_sorted, columns=['红球号码', '出现次数'])
    red_df['出现率'] = red_df['出现次数'] / periods * 100
    red_df['理论次数'] = periods * theoretical_red_prob
    red_df['偏差率'] = (red_df['出现次数'] - red_df['理论次数']) / red_df['理论次数'] * 100
    
    blue_df = pd.DataFrame(blue_sorted, columns=['蓝球号码', '出现次数'])
    blue_df['出现率'] = blue_df['出现次数'] / periods * 100
    blue_df['理论次数'] = periods * theoretical_blue_prob
    blue_df['偏差率'] = (blue_df['出现次数'] - blue_df['理论次数']) / blue_df['理论次数'] * 100
    
    # 定义热门和冷门号码（偏差率超过±20%）
    hot_red = red_df[red_df['偏差率'] > 20]
    cold_red = red_df[red_df['偏差率'] < -20]
    
    hot_blue = blue_df[blue_df['偏差率'] > 20]
    cold_blue = blue_df[blue_df['偏差率'] < -20]
    
    # 打印红球统计
    print("\n红球出现频率 (前10名):")
    print(red_df.head(10).to_string(index=False))
    
    print("\n红球统计信息:")
    print(f"平均出现次数: {red_df['出现次数'].mean():.2f}")
    print(f"最大偏差率: {red_df['偏差率'].abs().max():.2f}%")
    print(f"标准差: {red_df['出现次数'].std():.2f}")
    
    # 打印热门和冷门红球
    print("\n热门红球 (偏差率 > 20%):")
    if not hot_red.empty:
        print(hot_red.to_string(index=False))
    else:
        print("没有偏差率超过20%的热门红球")
    
    print("\n冷门红球 (偏差率 < -20%):")
    if not cold_red.empty:
        print(cold_red.to_string(index=False))
    else:
        print("没有偏差率低于-20%的冷门红球")
    
    # 打印蓝球统计
    print("\n蓝球出现频率 (全部):")
    print(blue_df.to_string(index=False))
    
    print("\n蓝球统计信息:")
    print(f"平均出现次数: {blue_df['出现次数'].mean():.2f}")
    print(f"最大偏差率: {blue_df['偏差率'].abs().max():.2f}%")
    print(f"标准差: {blue_df['出现次数'].std():.2f}")
    
    # 打印热门和冷门蓝球
    print("\n热门蓝球 (偏差率 > 20%):")
    if not hot_blue.empty:
        print(hot_blue.to_string(index=False))
    else:
        print("没有偏差率超过20%的热门蓝球")
    
    print("\n冷门蓝球 (偏差率 < -20%):")
    if not cold_blue.empty:
        print(cold_blue.to_string(index=False))
    else:
        print("没有偏差率低于-20%的冷门蓝球")
