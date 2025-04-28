# 测试文档

## 1. 测试环境配置

### 1.1 安装测试依赖
```bash
# 安装测试所需包
pip install pytest pytest-cov pytest-mock pytest-asyncio pytest-benchmark psutil

# 验证安装
pytest --version
```

### 1.2 配置测试环境
```bash
# 创建测试配置文件 pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    boundary: 边界测试
    performance: 性能测试
    integration: 集成测试
```

## 2. 测试用例说明

### 2.1 边界测试 (tests/boundary_tests.py)
- `test_empty_dataset`: 测试空数据集处理
- `test_single_row`: 测试单行数据处理
- `test_duplicate_numbers`: 测试重复号码处理
- `test_invalid_numbers`: 测试无效号码处理

使用示例:
```bash
# 运行所有边界测试
pytest tests/boundary_tests.py

# 运行特定边界测试
pytest tests/boundary_tests.py::TestBoundaries::test_empty_dataset
```

### 2.2 单元测试

#### 特征处理器测试 (tests/unit/test_feature_processor.py)
- `test_interval_features`: 测试区间特征计算
- `test_number_properties`: 测试数字特性计算
- `test_historical_combinations`: 测试历史组合特征

使用示例:
```bash
pytest tests/unit/test_feature_processor.py
```

#### 缓存管理测试 (tests/unit/test_cache.py)
- `test_cache_mechanism`: 测试缓存存储和读取
- `test_cache_expiration`: 测试缓存过期机制
- `test_cache_invalidation`: 测试缓存失效处理

使用示例:
```bash
pytest tests/unit/test_cache.py
```

### 2.3 集成测试 (tests/integration/)

#### 特征工程流水线测试 (test_feature_pipeline.py)
- `test_complete_pipeline`: 测试完整特征处理流程
- `test_feature_storage`: 测试特征存储和加载
- `test_feature_validation`: 测试特征验证流程

使用示例:
```bash
pytest tests/integration/test_feature_pipeline.py
```

#### 可视化测试 (test_visualization.py)
- `test_correlation_heatmap`: 测试相关性热力图
- `test_importance_plot`: 测试特征重要性图
- `test_distribution_plot`: 测试特征分布图

使用示例:
```bash
pytest tests/integration/test_visualization.py
```

### 2.4 性能测试 (tests/performance/)
- `test_feature_generation_performance`: 测试特征生成性能
- `test_memory_usage`: 测试内存使用情况
- `test_cache_performance`: 测试缓存性能
- `test_large_dataset`: 测试大数据集处理能力

使用示例:
```bash
# 运行所有性能测试
pytest tests/performance/

# 运行特定性能测试
pytest tests/performance/test_performance.py::TestPerformance::test_cache_performance
```

## 3. 运行测试命令

### 3.1 基本命令
```bash
# 运行所有测试
pytest

# 显示详细输出
pytest -v

# 显示测试进度
pytest --progress

# 并行执行测试
pytest -n auto

# 停在第一个失败的测试
pytest -x
```

### 3.2 测试过滤
```bash
# 运行特定标记的测试
pytest -m performance

# 运行包含特定名称的测试
pytest -k "feature"

# 排除特定标记的测试
pytest -m "not performance"
```

### 3.3 测试覆盖率
```bash
# 生成覆盖率报告
pytest --cov=src tests/

# 生成HTML格式报告
pytest --cov=src --cov-report=html tests/

# 生成XML格式报告（用于CI集成）
pytest --cov=src --cov-report=xml tests/
```

## 4. 编写测试用例

### 4.1 测试用例结构
```python
import pytest
from src.core.features import FeatureEngineering

class TestFeatureEngineering:
    @pytest.fixture
    def feature_engineering(self):
        """创建特征工程实例"""
        return FeatureEngineering()
    
    @pytest.mark.boundary
    def test_empty_dataset(self, feature_engineering):
        """测试空数据集处理"""
        with pytest.raises(ValueError):
            feature_engineering.process([])
    
    @pytest.mark.performance
    def test_large_dataset(self, feature_engineering, benchmark):
        """测试大数据集性能"""
        data = generate_large_dataset()
        result = benchmark(feature_engineering.process, data)
        assert result.stats.mean < 1.0  # 平均执行时间应小于1秒
```

### 4.2 使用 Fixtures
```python
@pytest.fixture(scope="module")
def test_data():
    """准备测试数据"""
    data = pd.DataFrame({
        'red_1': [1, 2, 3],
        'red_2': [4, 5, 6],
        'blue': [1, 2, 3]
    })
    return data

def test_feature_generation(test_data):
    """使用测试数据"""
    result = process_features(test_data)
    assert result.shape[1] == 10
```

### 4.3 参数化测试
```python
@pytest.mark.parametrize("input_data,expected", [
    ([1, 2, 3], 6),
    ([4, 5, 6], 15),
    ([7, 8, 9], 24),
])
def test_calculations(input_data, expected):
    """参数化测试计算功能"""
    assert sum(input_data) == expected
```

## 5. 最佳实践

### 5.1 测试设计原则
- 每个测试只测试一个功能点
- 使用有意义的测试名称
- 添加清晰的测试文档字符串
- 合理使用 fixtures 和 setup/teardown

### 5.2 测试执行建议
- 定期运行完整测试套件
- 配置持续集成自动运行测试
- 保持测试代码的整洁和可维护性
- 及时更新测试用例

### 5.3 测试数据管理
- 使用小型数据集进行单元测试
- 使用真实数据样本进行集成测试
- 使用大型数据集进行性能测试
- 妥善管理测试数据文件

## 6. 故障排除

### 6.1 常见问题
1. 测试发现问题
   - 检查测试文件命名（test_*.py）
   - 检查测试类命名（Test*）
   - 检查测试方法命名（test_*）

2. 导入错误
   - 检查 PYTHONPATH 设置
   - 验证依赖包安装
   - 检查导入路径

3. 性能问题
   - 检查测试数据大小
   - 优化测试执行顺序
   - 使用并行测试运行

### 6.2 调试技巧
- 使用 pytest -v 查看详细输出
- 使用 pytest --pdb 在失败处进入调试器
- 使用 pytest.set_trace() 设置断点
- 使用 pytest -s 显示打印输出
