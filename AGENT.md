# Lottery Analysis Agent

## 项目概述

彩票数据分析与智能号码生成工具，支持中国福利彩票双色球(SSQ)和体育彩票大乐透(DLT)。通过历史数据分析、模式识别和智能算法，为彩票爱好者提供数据支持和参考。

## 支持的彩票类型

- **双色球 (SSQ)**: 红球区(1-33)选6个，蓝球区(1-16)选1个
- **大乐透 (DLT)**: 前区(1-35)选5个，后区(1-12)选2个

## 核心功能

### 数据分析

- 历史开奖数据获取与分析
- 号码频率、遗漏、热冷分析
- 走势图表可视化
- 奇偶、大小、区间分布统计
- 模式识别与特征工程

### 智能推荐

- 基于历史数据的智能号码生成
- 多种选号策略(随机、智能、混合)
- 号码评分与推荐
- 复式、胆拖投注方案设计
- XGBoost机器学习模型预测

### 实用工具

- 中奖核对功能
- 奖金计算器
- 用户友好的图形界面(Tkinter)
- 数据导入导出功能

## 项目结构

```
lottery-analysis/
├── data/                  # 历史数据文件
├── docs/                  # 文档
├── src/                   # 源代码
│   ├── core/              # 核心功能模块
│   │   ├── analyzers/     # 分析器模块
│   │   ├── features/      # 特征工程
│   │   ├── generators/    # 号码生成器
│   │   ├── evaluators/    # 号码评估器
│   │   ├── filters/       # 过滤器
│   │   ├── model/         # 机器学习模型
│   │   ├── preprocessing/ # 数据预处理
│   │   ├── validation/    # 数据验证
│   │   ├── strategy/      # 策略模块
│   │   └── ...
│   ├── gui/               # 图形界面
│   ├── utils/             # 工具函数
│   ├── visualization/     # 数据可视化
│   ├── data/              # 数据处理
│   └── examples/          # 示例代码
├── tests/                 # 测试代码
├── scripts/               # 脚本工具
├── logs/                  # 日志文件
├── run.py                 # 主程序入口
├── requirements.txt       # 依赖包列表
└── pyproject.toml         # 项目配置
```

## 技术栈

- **语言**: Python 3.8+
- **数据处理**: pandas, numpy, scipy
- **机器学习**: scikit-learn, xgboost
- **可视化**: matplotlib, seaborn, plotly
- **GUI**: tkinter
- **网络请求**: requests, beautifulsoup4
- **配置管理**: pyyaml
- **测试**: pytest

## 核心模块说明

### 分析器 (src/core/analyzers/)

- `base_analyzer.py`: 分析器基类
- `ssq_analyzer.py`: 双色球分析器
- `dlt_analyzer.py`: 大乐透分析器
- `frequency_analyzer.py`: 频率分析
- `pattern_analyzer.py`: 模式分析

### 号码生成器 (src/core/generators/)

- 多种生成策略
- 智能推荐算法
- 历史数据驱动的预测

### 评估器 (src/core/evaluators/)

- 号码评分系统
- 多维度评估指标
- 历史回测验证

### 机器学习模型 (src/core/model/)

- XGBoost预测模型
- 特征工程
- 模型训练与优化

### 数据管理 (src/core/)

- `data_manager.py`: 数据管理器
- `data_fetcher.py`: 数据获取器
- `ssq_fetcher.py`: 双色球数据获取
- `dlt_fetcher.py`: 大乐透数据获取

### 配置管理 (src/core/)

- `config_manager.py`: 配置管理器
- 支持YAML配置文件
- 配置验证机制

### 日志系统 (src/core/)

- `logging_config.py`: 日志配置
- 多级别日志记录
- 文件和控制台输出

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动应用

```bash
python run.py
```

### 运行测试

```bash
pytest tests/
```

## 主要入口文件

- **run.py**: 主程序入口，启动GUI应用
- **generate_ssq.py**: 双色球号码生成脚本
- **evaluate_number.py**: 号码评估工具
- **analyze_recent_draws.py**: 近期开奖分析

## 配置文件

配置文件位于 `config/` 目录，支持:

- 数据源配置
- 分析参数设置
- 生成策略配置
- 模型参数配置

## 日志管理

日志文件存储在 `logs/` 目录，按日期自动归档，支持多级别日志输出。

## 开发规范

- 使用类型提示
- 遵循PEP 8代码风格
- 编写单元测试
- 使用日志记录而非print
- 异常处理和错误提示

## 免责声明

本工具仅供娱乐和参考，不构成任何投注建议。彩票有风险，投注需谨慎。开发者不对使用本工具产生的任何损失负责。
