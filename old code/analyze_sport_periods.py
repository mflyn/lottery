import json
from collections import Counter
import pandas as pd

# 加载大乐透历史数据
try:
    with open('sport_history.json', 'r', encoding='utf-8') as f:
        lottery_data = json.load(f)
    
    # 提取数据
    draws = lottery_data.get('data', [])
    total_periods = len(draws)
    
    if total_periods == 0:
        print("未找到有效的大乐透历史数据，请先运行 fetch_history_sport.py 获取数据")
        exit()
except FileNotFoundError:
    print("未找到 sport_history.json 文件，请先运行 fetch_history_sport.py 获取数据")
    exit()
except json.JSONDecodeError:
    print("sport_history.json 文件格式错误，请重新获取数据")
    exit()

# 设置要分析的期数
periods_to_analyze = [100, 200, 300]
if total_periods < max(periods_to_analyze):
    print(f"警告：可用数据期数 ({total_periods}) 少于请求分析的最大期数 ({max(periods_to_analyze)})")
    # 调整分析期数，确保不超过可用数据
    periods_to_analyze = [p for p in periods_to_analyze if p <= total_periods]
    if not periods_to_analyze:
        print("没有足够的数据进行分析")
        exit()

# 设置显示格式
pd.set_option('display.float_format', '{:.2f}'.format)

# 对每个期数进行分析
for periods in periods_to_analyze:
    print(f"\n{'='*80}")
    print(f"分析过去 {periods} 期大乐透开奖结果")
    print(f"{'='*80}")
    
    # 统计前区和后区号码出现次数
    front_balls = []
    back_balls = []
    
    for draw in draws[:periods]:
        front_balls.extend(draw.get('front_numbers', []))
        back_balls.extend(draw.get('back_numbers', []))
    
    # 计数
    front_counter = Counter(front_balls)
    back_counter = Counter(back_balls)
    
    # 确保所有可能的号码都在计数器中
    for i in range(1, 36):
        if i not in front_counter:
            front_counter[i] = 0
    
    for i in range(1, 13):
        if i not in back_counter:
            back_counter[i] = 0
    
    # 排序
    front_sorted = front_counter.most_common()
    back_sorted = back_counter.most_common()
    
    # 计算理论概率
    theoretical_front_prob = 5 / 35  # 每期5个前区号码，总共35个前区号码
    theoretical_back_prob = 2 / 12  # 每期2个后区号码，总共12个后区号码
    
    # 创建DataFrame并添加统计列
    front_df = pd.DataFrame(front_sorted, columns=['前区号码', '出现次数'])
    front_df['出现率'] = front_df['出现次数'] / periods * 100
    front_df['理论次数'] = periods * theoretical_front_prob
    front_df['偏差率'] = (front_df['出现次数'] - front_df['理论次数']) / front_df['理论次数'] * 100
    
    back_df = pd.DataFrame(back_sorted, columns=['后区号码', '出现次数'])
    back_df['出现率'] = back_df['出现次数'] / periods * 100
    back_df['理论次数'] = periods * theoretical_back_prob
    back_df['偏差率'] = (back_df['出现次数'] - back_df['理论次数']) / back_df['理论次数'] * 100
    
    # 定义热门和冷门号码（偏差率超过±20%）
    hot_front = front_df[front_df['偏差率'] > 20]
    cold_front = front_df[front_df['偏差率'] < -20]
    
    hot_back = back_df[back_df['偏差率'] > 20]
    cold_back = back_df[back_df['偏差率'] < -20]
    
    # 打印前区统计
    print("\n前区出现频率 (前10名):")
    print(front_df.head(10).to_string(index=False))
    
    print("\n前区统计信息:")
    print(f"平均出现次数: {front_df['出现次数'].mean():.2f}")
    print(f"最大偏差率: {front_df['偏差率'].abs().max():.2f}%")
    print(f"标准差: {front_df['出现次数'].std():.2f}")
    
    # 打印热门和冷门前区号码
    print("\n热门前区号码 (偏差率 > 20%):")
    if not hot_front.empty:
        print(hot_front.to_string(index=False))
    else:
        print("没有偏差率超过20%的热门前区号码")
    
    print("\n冷门前区号码 (偏差率 < -20%):")
    if not cold_front.empty:
        print(cold_front.to_string(index=False))
    else:
        print("没有偏差率低于-20%的冷门前区号码")
    
    # 打印后区统计
    print("\n后区出现频率 (全部):")
    print(back_df.to_string(index=False))
    
    print("\n后区统计信息:")
    print(f"平均出现次数: {back_df['出现次数'].mean():.2f}")
    print(f"最大偏差率: {back_df['偏差率'].abs().max():.2f}%")
    print(f"标准差: {back_df['出现次数'].std():.2f}")
    
    # 打印热门和冷门后区号码
    print("\n热门后区号码 (偏差率 > 20%):")
    if not hot_back.empty:
        print(hot_back.to_string(index=False))
    else:
        print("没有偏差率超过20%的热门后区号码")
    
    print("\n冷门后区号码 (偏差率 < -20%):")
    if not cold_back.empty:
        print(cold_back.to_string(index=False))
    else:
        print("没有偏差率低于-20%的冷门后区号码")

# 创建一个分析所有历史数据的函数
def analyze_all_history():
    print(f"\n{'='*80}")
    print(f"分析全部 {total_periods} 期大乐透开奖结果")
    print(f"{'='*80}")
    
    # 统计前区和后区号码出现次数
    front_balls = []
    back_balls = []
    
    for draw in draws:
        front_balls.extend(draw.get('front_numbers', []))
        back_balls.extend(draw.get('back_numbers', []))
    
    # 计数
    front_counter = Counter(front_balls)
    back_counter = Counter(back_balls)
    
    # 确保所有可能的号码都在计数器中
    for i in range(1, 36):
        if i not in front_counter:
            front_counter[i] = 0
    
    for i in range(1, 13):
        if i not in back_counter:
            back_counter[i] = 0
    
    # 排序
    front_sorted = front_counter.most_common()
    back_sorted = back_counter.most_common()
    
    # 计算理论概率
    theoretical_front_prob = 5 / 35  # 每期5个前区号码，总共35个前区号码
    theoretical_back_prob = 2 / 12  # 每期2个后区号码，总共12个后区号码
    
    # 创建DataFrame并添加统计列
    front_df = pd.DataFrame(front_sorted, columns=['前区号码', '出现次数'])
    front_df['出现率'] = front_df['出现次数'] / total_periods * 100
    front_df['理论次数'] = total_periods * theoretical_front_prob
    front_df['偏差率'] = (front_df['出现次数'] - front_df['理论次数']) / front_df['理论次数'] * 100
    
    back_df = pd.DataFrame(back_sorted, columns=['后区号码', '出现次数'])
    back_df['出现率'] = back_df['出现次数'] / total_periods * 100
    back_df['理论次数'] = total_periods * theoretical_back_prob
    back_df['偏差率'] = (back_df['出现次数'] - back_df['理论次数']) / back_df['理论次数'] * 100
    
    # 打印前区统计
    print("\n前区出现频率 (全部):")
    print(front_df.to_string(index=False))
    
    print("\n前区统计信息:")
    print(f"平均出现次数: {front_df['出现次数'].mean():.2f}")
    print(f"最大偏差率: {front_df['偏差率'].abs().max():.2f}%")
    print(f"标准差: {front_df['出现次数'].std():.2f}")
    
    # 打印后区统计
    print("\n后区出现频率 (全部):")
    print(back_df.to_string(index=False))
    
    print("\n后区统计信息:")
    print(f"平均出现次数: {back_df['出现次数'].mean():.2f}")
    print(f"最大偏差率: {back_df['偏差率'].abs().max():.2f}%")
    print(f"标准差: {back_df['出现次数'].std():.2f}")

# 分析所有历史数据
analyze_all_history()
