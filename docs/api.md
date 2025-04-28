# API文档

## 计算器模块 API

### 大乐透计算器
```python
def calculate_complex_bet(front_numbers: List[int], back_numbers: List[int]) -> Dict:
    """计算复式投注注数和金额"""

def calculate_dantuo_bet(front_dan: List[int], front_tuo: List[int],
                        back_dan: List[int], back_tuo: List[int]) -> Dict:
    """计算胆拖投注注数和金额"""
```

### 双色球计算器
```python
def calculate_complex_bet(red_numbers: List[int], blue_numbers: List[int]) -> Dict:
    """计算复式投注注数和金额"""

def calculate_dantuo_bet(red_dan: List[int], red_tuo: List[int],
                        blue_number: int) -> Dict:
    """计算胆拖投注注数和金额"""
```

## 数据分析模块 API

### 数据获取
```python
def fetch_history_data(lottery_type: str, start_date: str, end_date: str) -> List[Dict]:
    """获取历史开奖数据"""

def analyze_number_frequency(data: List[Dict]) -> Dict:
    """分析号码出现频率"""
```

### 数据分析
```python
def calculate_statistics(data: List[Dict]) -> Dict:
    """计算统计指标"""

def generate_analysis_report(data: List[Dict]) -> str:
    """生成分析报告"""
```

## 号码生成模块 API

### 随机生成
```python
def generate_random_numbers(lottery_type: str, count: int) -> List[Dict]:
    """生成随机号码组合"""

def generate_smart_numbers(lottery_type: str, history_data: List[Dict]) -> List[Dict]:
    """基于历史数据生成智能号码组合"""
```