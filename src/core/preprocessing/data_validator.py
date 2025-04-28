from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging

class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_rules = {}
        
    def add_rule(self, column: str, rule_type: str, params: Dict):
        """添加验证规则"""
        if column not in self.validation_rules:
            self.validation_rules[column] = []
        self.validation_rules[column].append({
            'type': rule_type,
            'params': params
        })
        
    def validate(self, data: pd.DataFrame) -> Dict:
        """执行数据验证
        
        Returns:
            验证结果报告
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        for column, rules in self.validation_rules.items():
            if column not in data.columns:
                results['errors'].append(f"缺少必需列: {column}")
                results['valid'] = False
                continue
                
            for rule in rules:
                try:
                    self._apply_rule(data[column], rule, results)
                except Exception as e:
                    results['errors'].append(f"验证规则执行失败: {str(e)}")
                    results['valid'] = False
                    
        return results
        
    def _apply_rule(self, series: pd.Series, rule: Dict, results: Dict):
        """应用验证规则"""
        rule_type = rule['type']
        params = rule['params']
        
        if rule_type == 'type':
            if not all(isinstance(x, params['type']) for x in series.dropna()):
                results['errors'].append(
                    f"列 {series.name} 包含无效数据类型"
                )
                results['valid'] = False
                
        elif rule_type == 'range':
            if not all(params['min'] <= x <= params['max'] for x in series.dropna()):
                results['errors'].append(
                    f"列 {series.name} 包含超出范围的值"
                )
                results['valid'] = False
                
        elif rule_type == 'unique':
            if params['required'] and series.duplicated().any():
                results['errors'].append(
                    f"列 {series.name} 包含重复值"
                )
                results['valid'] = False
                
        elif rule_type == 'format':
            try:
                series.apply(params['validator'])
            except:
                results['errors'].append(
                    f"列 {series.name} 包含格式错误的值"
                )
                results['valid'] = False