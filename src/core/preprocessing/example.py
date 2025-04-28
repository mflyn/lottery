# 使用示例
logger = PreprocessingLogger()

# 记录数据统计
logger.log_data_stats(
    "lottery_data",
    row_count=1000,
    column_stats={
        "number": {"mean": 15.5, "std": 5.2},
        "date": {"min": "2020-01-01", "max": "2023-12-31"}
    }
)

# 记录转换操作
logger.log_transformation(
    "normalization",
    params={"method": "min-max"},
    affected_columns=["number", "frequency"]
)

# 记录验证结果
logger.log_validation(
    "missing_values",
    results={"number": True, "date": False},
    threshold=0.01
)

# 导出报告
logger.export_html_report("preprocessing_report.html")