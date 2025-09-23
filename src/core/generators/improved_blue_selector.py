"""
改进的双色球蓝球选择算法

分析现有算法的问题并提供更好的解决方案
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from collections import Counter
import math


class ImprovedBlueSelector:
    """改进的蓝球选择器"""
    
    def __init__(self):
        self.weights = {
            'frequency': 0.4,    # 频率权重
            'missing': 0.3,      # 遗漏权重  
            'trend': 0.2,        # 趋势权重
            'random': 0.1        # 随机性权重
        }
        
    def select_blue_number(self, history_data: pd.DataFrame, periods: int = 50) -> int:
        """
        多因子加权选择蓝球号码
        
        Args:
            history_data: 历史数据
            periods: 分析期数
            
        Returns:
            选中的蓝球号码
        """
        if history_data.empty or len(history_data) < 10:
            return np.random.randint(1, 17)
            
        recent_data = history_data.head(periods)
        blue_numbers = recent_data['blue_number'].tolist()
        
        # 计算各种评分
        frequency_scores = self._calculate_frequency_scores(blue_numbers)
        missing_scores = self._calculate_missing_scores(blue_numbers)
        trend_scores = self._calculate_trend_scores(blue_numbers)
        
        # 综合加权评分
        final_scores = {}
        for num in range(1, 17):
            final_scores[num] = (
                self.weights['frequency'] * frequency_scores.get(num, 0) +
                self.weights['missing'] * missing_scores.get(num, 0) +
                self.weights['trend'] * trend_scores.get(num, 0) +
                self.weights['random'] * np.random.random()  # 加入随机性
            )
        
        # 转换为概率分布
        scores = list(final_scores.values())
        min_score = min(scores)
        adjusted_scores = [s - min_score + 0.1 for s in scores]  # 避免负数和零
        
        probabilities = np.array(adjusted_scores) / sum(adjusted_scores)
        
        # 按概率选择
        return int(np.random.choice(list(range(1, 17)), p=probabilities))
    
    def _calculate_frequency_scores(self, blue_numbers: List[int]) -> Dict[int, float]:
        """计算频率评分"""
        counter = Counter(blue_numbers)
        total = len(blue_numbers)
        
        # 理论频率
        expected_freq = total / 16
        
        scores = {}
        for num in range(1, 17):
            actual_freq = counter.get(num, 0)
            # 使用调和平均避免极端值
            if actual_freq == 0:
                scores[num] = 0.1
            else:
                # 频率越接近理论值，得分越高
                deviation = abs(actual_freq - expected_freq) / expected_freq
                scores[num] = 1.0 / (1.0 + deviation)
        
        return scores
    
    def _calculate_missing_scores(self, blue_numbers: List[int]) -> Dict[int, float]:
        """计算遗漏评分"""
        scores = {}
        
        for num in range(1, 17):
            # 计算最近一次出现的位置
            last_position = -1
            for i, blue in enumerate(blue_numbers):
                if blue == num:
                    last_position = i
                    break
            
            if last_position == -1:
                # 从未出现，给予高分
                missing_periods = len(blue_numbers)
            else:
                missing_periods = last_position
            
            # 遗漏期数越长，得分越高（但有上限）
            scores[num] = min(missing_periods / 10.0, 1.0)
        
        return scores
    
    def _calculate_trend_scores(self, blue_numbers: List[int]) -> Dict[int, float]:
        """计算趋势评分"""
        if len(blue_numbers) < 10:
            return {num: 0.5 for num in range(1, 17)}
        
        scores = {}
        window_size = min(10, len(blue_numbers) // 2)
        
        for num in range(1, 17):
            # 计算近期和远期的出现频率
            recent_count = sum(1 for i in range(window_size) if blue_numbers[i] == num)
            older_count = sum(1 for i in range(window_size, min(window_size * 2, len(blue_numbers))) 
                            if blue_numbers[i] == num)
            
            recent_freq = recent_count / window_size
            older_freq = older_count / window_size if window_size * 2 <= len(blue_numbers) else recent_freq
            
            # 趋势评分：上升趋势得高分
            if older_freq == 0:
                trend_score = recent_freq
            else:
                trend_ratio = recent_freq / older_freq
                trend_score = min(trend_ratio / 2.0, 1.0)  # 限制在[0,1]
            
            scores[num] = trend_score
        
        return scores
    
    def analyze_current_algorithm(self, blue_pattern: Dict) -> Dict:
        """分析当前算法的优缺点"""
        analysis = {
            'current_method': '简单频率加权',
            'advantages': [
                '实现简单，计算效率高',
                '基于统计学原理，有一定合理性',
                '避免了完全随机选择'
            ],
            'disadvantages': [
                '只考虑频率单一因素',
                '忽略了号码的遗漏情况',
                '没有考虑时间趋势',
                '可能过度拟合历史数据',
                '缺乏动态调整机制'
            ],
            'improvements': [
                '引入多因子模型',
                '考虑遗漏期数',
                '加入趋势分析',
                '动态权重调整',
                '增加随机性防过拟合'
            ]
        }
        return analysis
    
    def compare_algorithms(self, history_data: pd.DataFrame, test_periods: int = 20) -> Dict:
        """比较不同算法的表现"""
        if len(history_data) < test_periods + 50:
            return {'error': '数据不足，无法进行比较'}
        
        # 分离训练和测试数据
        test_data = history_data.head(test_periods)
        train_data = history_data.iloc[test_periods:]
        
        results = {
            'original_algorithm': {'hits': 0, 'predictions': []},
            'improved_algorithm': {'hits': 0, 'predictions': []}
        }
        
        for i in range(test_periods):
            actual_blue = test_data.iloc[i]['blue_number']
            
            # 原始算法预测
            blue_freq = Counter(train_data.head(50)['blue_number'].tolist())
            if blue_freq:
                numbers = list(blue_freq.keys())
                probabilities = list(blue_freq.values())
                total_prob = sum(probabilities)
                probabilities = [p/total_prob for p in probabilities]
                original_pred = int(np.random.choice(numbers, p=probabilities))
            else:
                original_pred = np.random.randint(1, 17)
            
            # 改进算法预测
            improved_pred = self.select_blue_number(train_data, 50)
            
            # 记录结果
            results['original_algorithm']['predictions'].append(original_pred)
            results['improved_algorithm']['predictions'].append(improved_pred)
            
            if original_pred == actual_blue:
                results['original_algorithm']['hits'] += 1
            if improved_pred == actual_blue:
                results['improved_algorithm']['hits'] += 1
        
        # 计算命中率
        results['original_algorithm']['hit_rate'] = results['original_algorithm']['hits'] / test_periods
        results['improved_algorithm']['hit_rate'] = results['improved_algorithm']['hits'] / test_periods
        
        return results


def demonstrate_algorithm_analysis():
    """演示算法分析"""
    selector = ImprovedBlueSelector()
    
    # 模拟蓝球历史数据
    np.random.seed(42)
    mock_data = pd.DataFrame({
        'blue_number': np.random.randint(1, 17, 100)
    })
    
    print("=== 双色球蓝球加权算法分析 ===\n")
    
    # 分析当前算法
    analysis = selector.analyze_current_algorithm({})
    print("1. 当前算法分析:")
    print(f"   方法: {analysis['current_method']}")
    print("   优点:")
    for adv in analysis['advantages']:
        print(f"   - {adv}")
    print("   缺点:")
    for dis in analysis['disadvantages']:
        print(f"   - {dis}")
    print("   改进建议:")
    for imp in analysis['improvements']:
        print(f"   - {imp}")
    
    print("\n2. 改进算法权重配置:")
    for factor, weight in selector.weights.items():
        print(f"   {factor}: {weight}")
    
    print("\n3. 算法选择示例:")
    for i in range(5):
        selected = selector.select_blue_number(mock_data)
        print(f"   第{i+1}次选择: {selected}")


if __name__ == "__main__":
    demonstrate_algorithm_analysis()
