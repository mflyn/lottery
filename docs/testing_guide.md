# 测试用例使用指南

## 1. 测试环境配置

### 1.1 安装依赖
```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio
```

### 1.2 验证安装
```bash
pytest --version
```

## 2. 测试用例说明

### 2.1 单元测试

#### DLT特征处理器测试 (tests/unit/test_dlt_feature_processor.py)
- `test_extract_basic_features`: 测试基础特征提取
- `test_extract_advanced_features`: 测试高级特征提取
- `test_invalid_input`: 测试无效输入处理

使用示例:
```bash
pytest tests/unit/test_dlt_feature_processor.py
pytest tests/unit/test_dlt_feature_processor.py::TestDLTFeatureProcessor::test_extract_basic_features
```

#### 缓存管理测试 (tests/unit/test_feature_engineering.py)
- `test_cache_management`: 测试缓存存储和读取
- `test_cache_refresh`: 测试缓存刷新机制

使用示例:
```bash
pytest tests/unit/test_feature_engineering.py
```

#### 进度跟踪测试 (tests/unit/test_progress_tracking.py)
- `test_progress_callback`: 测试进度回调功能
- `test_error_handling`: 测试错误处理机制

使用示例:
```bash
pytest tests/unit/test_progress_tracking.py
```

#### 特征验证测试 (tests/unit/test_feature_validator.py)
- `test_feature_completeness`: 测试特征完整性验证
- `test_value_validation`: 测试数值有效性验证
- `test_range_validation`: 测试数值范围验证

使用示例:
```bash
pytest tests/unit/test_feature_validator.py
```

#### 特征选择测试 (tests/unit/test_feature_selector.py)
- `test_mutual_info_selection`: 测试互信息特征选择
- `test_correlation_selection`: 测试相关性特征选择
- `test_combined_selection`: 测试组合特征选择

使用示例:
```bash
pytest tests/unit/test_feature_selector.py
```

### 2.2 集成测试

#### 特征处理流水线测试 (tests/integration/test_feature_pipeline.py)
- `test_end_to_end_pipeline`: 测试完整特征处理流程
  - 特征生成
  - 进度跟踪
  - 特征验证
  - 特征选择

使用示例:
```bash
pytest tests/integration/test_feature_pipeline.py
```

## 3. 运行测试命令

### 3.1 运行所有测试
```bash
pytest tests/
```

### 3.2 运行特定测试文件
```bash
pytest tests/unit/test_dlt_feature_processor.py
```

### 3.3 运行特定测试类
```bash
pytest tests/unit/test_feature_validator.py::TestFeatureValidator
```

### 3.4 运行特定测试方法
```bash
pytest tests/unit/test_feature_selector.py::TestFeatureSelector::test_mutual_info_selection
```

### 3.5 生成测试覆盖率报告
```bash
pytest --cov=src tests/ --cov-report=html
```

## 4. 测试报告说明

### 4.1 HTML覆盖率报告
运行覆盖率测试后，将在项目根目录下生成 `htmlcov` 文件夹，包含以下内容：
- `index.html`: 总体覆盖率报告
- 各源代码文件对应的覆盖率详情页面

### 4.2 控制台输出说明
- `.`: 测试通过
- `F`: 测试失败
- `E`: 测试错误
- `s`: 测试跳过
- `x`: 预期失败

## 5. 最佳实践

### 5.1 编写测试用例
- 每个测试方法只测试一个功能点
- 使用有意义的测试方法名称
- 添加清晰的测试文档字符串
- 合理使用 `setUp` 和 `tearDown`

### 5.2 运行测试
- 代码变更后运行完整测试套件
- 定期检查测试覆盖率
- 及时修复失败的测试
- 保持测试代码的整洁和可维护性

### 5.3 测试数据管理
- 使用 `fixtures` 管理测试数据
- 避免测试间的数据依赖
- 及时清理测试数据
- 使用合适的测试数据集

## 6. 故障排除

### 6.1 常见问题
1. 测试无法找到
   - 检查测试文件名是否以 `test_` 开头
   - 检查测试类名是否以 `Test` 开头
   - 检查测试方法名是否以 `test_` 开头

2. 导入错误
   - 检查 `PYTHONPATH` 设置
   - 检查依赖包是否正确安装
   - 检查导入路径是否正确

3. 测试超时
   - 检查测试配置中的超时设置
   - 优化测试执行效率
   - 考虑使用异步测试

### 6.2 调试技巧
- 使用 `-v` 参数获取详细输出
- 使用 `--pdb` 在失败时进入调试器
- 使用 `pytest.set_trace()` 设置断点