from typing import Dict, List, Optional
import pandas as pd
from .data_cleaner import DataCleaner
from .data_validator import DataValidator
from .data_transformer import DataTransformer
from .quality_reporter import DataQualityReporter
from .config_manager import PreprocessingConfigManager
from .preprocessing_logger import PreprocessingLogger

class DataPreprocessor:
    """增强的数据预处理器"""
    
    def __init__(self, config_name: Optional[str] = None):
        self.cleaner = DataCleaner()
        self.validator = DataValidator()
        self.transformer = DataTransformer()
        self.reporter = DataQualityReporter()
        self.config_manager = PreprocessingConfigManager()
        self.logger = PreprocessingLogger()
        
        # 加载配置
        if config_name:
            self.load_config(config_name)
        else:
            self._setup_default_config()
            
    def load_config(self, config_name: str):
        """加载预处理配置"""
        config = self.config_manager.load_config(config_name)
        self._apply_config(config)
        
    def save_config(self, config_name: str):
        """保存当前配置"""
        config = self._get_current_config()
        self.config_manager.save_config(config_name, config)
        
    def preprocess_data(self, 
                       data: pd.DataFrame,
                       categorical_columns: List[str] = None,
                       numerical_columns: List[str] = None,
                       generate_report: bool = True) -> pd.DataFrame:
        """执行完整的数据预处理流程"""
        try:
            results = {
                'status': 'success',
                'processed_data': None,
                'quality_report': None,
                'validation_results': None
            }
            
            # 1. 生成初始质量报告
            if generate_report:
                initial_report = self.reporter.generate_report(data)
                self.logger.update_statistics({
                    'initial_quality': initial_report['sections']['basic_info']
                })
            
            # 2. 数据验证
            validation_results = self.validator.validate(data)
            results['validation_results'] = validation_results
            
            if not validation_results['valid']:
                self.logger.log_error(
                    "数据验证失败",
                    {'errors': validation_results['errors']}
                )
                results['status'] = 'validation_failed'
                return results
            
            # 3. 数据转换
            df = self.transformer.transform(data)
            self.logger.log_operation(
                'transform',
                {'columns_transformed': list(self.transformer.transformers.keys())}
            )
            
            # 4. 数据清洗
            df = self.cleaner.clean_data(df)
            self.logger.log_operation(
                'clean',
                {'rows_before': len(data), 'rows_after': len(df)}
            )
            
            # 5. 生成最终质量报告
            if generate_report:
                final_report = self.reporter.generate_report(df)
                results['quality_report'] = final_report
                self.logger.update_statistics({
                    'final_quality': final_report['sections']['basic_info']
                })
            
            # 返回处理后的数据，而不是结果字典，以兼容测试
            return df
            
        except Exception as e:
            self.logger.log_error("预处理失败", {'error': str(e)})
            raise
            
    def get_preprocessing_summary(self, original_data: pd.DataFrame, processed_data: pd.DataFrame) -> Dict:
        """获取预处理摘要信息
        
        Args:
            original_data: 原始数据
            processed_data: 处理后的数据
            
        Returns:
            包含预处理摘要信息的字典
        """
        # 获取原始数据和处理后数据的形状
        original_shape = original_data.shape
        processed_shape = processed_data.shape
        
        # 获取数据清洗报告
        cleaning_report = {
            '移除的行数': original_shape[0] - processed_shape[0],
            '移除行比例': (original_shape[0] - processed_shape[0]) / original_shape[0] if original_shape[0] > 0 else 0,
            '处理前缺失值总数': original_data.isnull().sum().sum(),
            '处理后缺失值总数': processed_data.isnull().sum().sum()
        }
        
        # 获取数据质量报告
        quality_report = None
        if hasattr(self, 'reporter') and self.reporter:
            quality_report = self.reporter.generate_report(processed_data)
        
        # 返回摘要信息
        return {
            'original_shape': original_shape,
            'processed_shape': processed_shape,
            'cleaning_report': cleaning_report,
            'quality_report': quality_report
        }
