from typing import Dict, Any, Type, Optional
from .base_analyzer import BaseAnalyzer
from .frequency_analyzer import FrequencyAnalyzer
from .pattern_analyzer import PatternAnalyzer
from .dlt_analyzer import DLTAnalyzer
from ..exceptions import AnalysisError

class AnalyzerFactory:
    """分析器工厂类"""
    
    _analyzers = {
        'frequency': FrequencyAnalyzer,
        'pattern': PatternAnalyzer,
        'dlt_enhanced': DLTAnalyzer
    }
    
    @classmethod
    def get_analyzer(cls, analysis_type: str, lottery_type: str = 'ssq', **kwargs) -> Any:
        """获取分析器实例
        
        Args:
            analysis_type: 分析类型 ('frequency', 'pattern', 'trend' 等)
            lottery_type: 彩票类型 ('ssq', 'dlt')
            **kwargs: 传递给构造函数的参数
            
        Returns:
            分析器实例
        """
        # 特殊处理大乐透增强版
        if lottery_type == 'dlt' and analysis_type in ['hot_cold', 'missing', 'combinations']:
            return DLTAnalyzer()
            
        analyzer_cls = cls._analyzers.get(analysis_type)
        if not analyzer_cls:
            # 兼容旧代码逻辑
            if analysis_type == 'trend':
                if lottery_type == 'ssq':
                    from ..ssq_analyzer import SSQAnalyzer
                    return SSQAnalyzer()
                else:
                    return DLTAnalyzer()
            raise AnalysisError(f"不支持的分析类型: {analysis_type}")
            
        return analyzer_cls(lottery_type=lottery_type, **kwargs)

    @classmethod
    def register_analyzer(cls, name: str, analyzer_cls: Type):
        """注册新的分析器"""
        cls._analyzers[name] = analyzer_cls
