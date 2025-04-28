# API 参考文档

## 核心模块 (core)

### SmartNumberGenerator
智能选号生成器类

#### 方法
- `generate_recommended(count: int) -> List[NumberType]`
  - 功能: 生成推荐号码
  - 参数: count - 生成注数
  - 返回: 号码列表

- `analyze_history(periods: int) -> Dict[str, Any]`
  - 功能: 分析历史数据
  - 参数: periods - 分析期数
  - 返回: 分析结果字典

### DataManager
数据管理类

#### 方法
- `get_history_data(lottery_type: str) -> DataFrame`
  - 功能: 获取历史数据
  - 参数: lottery_type - 彩票类型('dlt'/'ssq')
  - 返回: pandas DataFrame

- `update_data() -> bool`
  - 功能: 更新最新数据
  - 返回: 更新是否成功

## GUI模块 (gui)

### MainWindow
主窗口类

#### 方法
- `show() -> None`
  - 功能: 显示主窗口

- `update_display() -> None`
  - 功能: 更新显示内容

### AnalysisTab
分析页面类

#### 方法
- `plot_statistics() -> None`
  - 功能: 绘制统计图表

- `export_results(path: str) -> bool`
  - 功能: 导出分析结果
