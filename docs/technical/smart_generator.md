# 智能选号生成器技术文档

## 功能概述
智能选号生成器(`SmartNumberGenerator`)是一个基于历史数据分析的号码推荐系统。它通过分析历史开奖数据的多个维度特征，结合概率统计方法，生成符合一定规律的号码组合。

## 核心算法

### 1. 热冷号分析
- **实现类**: `SmartNumberGenerator._analyze_hot_cold_numbers()`
- **功能**: 分析号码在历史数据中的出现频率，将号码分类为热号、冷号和正常号
- **参数配置**:
  - `hot_threshold`: 热号判定阈值(默认0.6)
  - `cold_threshold`: 冷号判定阈值(默认0.3)
  - `analysis_periods`: 分析期数(默认30期)

### 2. 间隔模式分析
- **实现类**: `SmartNumberGenerator._analyze_gap_patterns()`
- **功能**: 分析相邻号码之间的间隔规律
- **统计指标**:
  - 间隔概率分布
  - 平均间隔
  - 间隔标准差

### 3. 号码选择算法
- **实现类**: `SmartNumberGenerator._select_numbers_by_pattern()`
- **选择策略**:
  - 按配置比例选择热号(默认40%)
  - 按配置比例选择冷号(默认20%)
  - 剩余比例选择正常号
  - 权重随机选择

## 配置参数

### 大乐透配置
```python
{
    'front_range': (1, 35),  # 前区号码范围
    'back_range': (1, 12),   # 后区号码范围
    'hot_threshold': 0.6,    # 热号阈值
    'cold_threshold': 0.3,   # 冷号阈值
    'analysis_periods': 30   # 分析期数
}
```

### 双色球配置
```python
{
    'red_range': (1, 33),    # 红球号码范围
    'blue_range': (1, 16),   # 蓝球号码范围
    'hot_threshold': 0.6,    # 热号阈值
    'cold_threshold': 0.3,   # 冷号阈值
    'analysis_periods': 30   # 分析期数
}
```

## 使用示例

```python
# 创建生成器实例
generator = SmartNumberGenerator('dlt')  # 或 'ssq'

# 生成推荐号码
numbers = generator.generate_recommended(count=5)

# 获取分析结果
history_data = data_manager.get_history_data('dlt')
hot_cold_analysis = generator._analyze_hot_cold_numbers(history_data)
gap_analysis = generator._analyze_gap_patterns(history_data)
```

## 性能考虑
1. 数据缓存
   - 历史数据缓存
   - 分析结果缓存
   - 定期更新机制

2. 计算优化
   - 向量化运算
   - 并行处理支持
   - 增量更新

## 扩展建议
1. 特征工程
   - 添加更多统计特征
   - 支持自定义特征

2. 算法优化
   - 支持机器学习模型
   - 添加更多选号策略
   - 优化参数配置

3. 评估系统
   - 历史命中率统计
   - 参数优化反馈
   - 策略评估指标