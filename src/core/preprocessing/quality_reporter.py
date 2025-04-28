from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime
import json

class DataQualityReporter:
    """数据质量报告生成器"""
    
    def __init__(self):
        self.report_sections = [
            'basic_info',
            'missing_values',
            'duplicates',
            'data_types',
            'value_distribution',
            'anomalies'
        ]
        
    def generate_report(self, data: pd.DataFrame) -> Dict:
        """生成完整的数据质量报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'dataset_name': getattr(data, 'name', 'unnamed_dataset'),
            'sections': {}
        }
        
        for section in self.report_sections:
            method = getattr(self, f'_analyze_{section}')
            report['sections'][section] = method(data)
            
        return report
        
    def _analyze_basic_info(self, data: pd.DataFrame) -> Dict:
        """基础信息分析"""
        return {
            'row_count': len(data),
            'column_count': len(data.columns),
            'memory_usage': data.memory_usage(deep=True).sum(),
            'columns': list(data.columns)
        }
        
    def _analyze_missing_values(self, data: pd.DataFrame) -> Dict:
        """缺失值分析"""
        missing = data.isnull().sum()
        return {
            'total_missing': int(missing.sum()),
            'missing_by_column': {
                col: int(count) for col, count in missing.items() if count > 0
            },
            'missing_percentages': {
                col: float(count/len(data)) 
                for col, count in missing.items() if count > 0
            }
        }
        
    def _analyze_duplicates(self, data: pd.DataFrame) -> Dict:
        """重复值分析"""
        duplicates = data.duplicated()
        return {
            'total_duplicates': int(duplicates.sum()),
            'duplicate_percentage': float(duplicates.sum()/len(data)),
            'duplicate_rows': data[duplicates].index.tolist()
        }
        
    def _analyze_data_types(self, data: pd.DataFrame) -> Dict:
        """数据类型分析"""
        return {
            'type_summary': {
                str(dtype): int(count) 
                for dtype, count in data.dtypes.value_counts().items()
            },
            'column_types': {
                col: str(dtype) for col, dtype in data.dtypes.items()
            }
        }
        
    def _analyze_value_distribution(self, data: pd.DataFrame) -> Dict:
        """值分布分析"""
        distributions = {}
        
        for col in data.columns:
            if data[col].dtype in ['int64', 'float64']:
                distributions[col] = {
                    'min': float(data[col].min()),
                    'max': float(data[col].max()),
                    'mean': float(data[col].mean()),
                    'std': float(data[col].std()),
                    'quartiles': [
                        float(q) for q in data[col].quantile([.25, .5, .75])
                    ]
                }
            elif data[col].dtype == 'object':
                value_counts = data[col].value_counts()
                distributions[col] = {
                    'unique_count': int(len(value_counts)),
                    'top_values': {
                        str(val): int(count) 
                        for val, count in value_counts.head().items()
                    }
                }
                
        return distributions
        
    def _analyze_anomalies(self, data: pd.DataFrame) -> Dict:
        """异常值分析"""
        anomalies = {}
        
        for col in data.select_dtypes(include=['int64', 'float64']).columns:
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = data[col][(data[col] < Q1 - 1.5*IQR) | 
                                (data[col] > Q3 + 1.5*IQR)]
            if len(outliers) > 0:
                anomalies[col] = {
                    'count': int(len(outliers)),
                    'percentage': float(len(outliers)/len(data)),
                    'values': outliers.tolist()
                }
                
        return anomalies
        
    def save_report(self, report: Dict, filepath: str):
        """保存报告到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)