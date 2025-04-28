from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class ValidationRule:
    """验证规则基类"""
    name: str
    description: str
    severity: str  # 'error' or 'warning'
    
class BaseValidator(ABC):
    """验证器基类"""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
        self.validation_results: Dict[str, Any] = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
    
    def add_rule(self, rule: ValidationRule):
        """添加验证规则"""
        self.rules.append(rule)
    
    def add_error(self, message: str):
        """添加错误信息"""
        self.validation_results['errors'].append(message)
        self.validation_results['valid'] = False
    
    def add_warning(self, message: str):
        """添加警告信息"""
        self.validation_results['warnings'].append(message)
    
    @abstractmethod
    def validate(self, data: Any) -> Dict[str, Any]:
        """执行验证"""
        pass