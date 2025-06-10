from typing import Dict, Type, List, Optional
from .base import NumberGenerator
from .random_generator import RandomGenerator
from .smart_generator import SmartNumberGenerator
from ..exceptions import GeneratorError
from ..logging_config import get_logger

class GeneratorFactory:
    """号码生成器工厂"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._generators: Dict[str, Type[NumberGenerator]] = {
            'random': RandomGenerator,
            'smart': SmartNumberGenerator
        }
    
    def create_generator(self, generator_type: str, lottery_type: str, **kwargs) -> NumberGenerator:
        """创建生成器实例
        
        Args:
            generator_type: 生成器类型 ('random', 'smart')
            lottery_type: 彩票类型 ('ssq', 'dlt')
            **kwargs: 其他参数
            
        Returns:
            生成器实例
            
        Raises:
            GeneratorError: 当生成器类型不支持时
        """
        try:
            generator_class = self._generators.get(generator_type)
            if not generator_class:
                available_types = list(self._generators.keys())
                raise GeneratorError(
                    f"不支持的生成器类型: {generator_type}，"
                    f"可用类型: {available_types}"
                )
            
            # 创建生成器实例
            generator = generator_class(lottery_type, **kwargs)
            
            self.logger.info(f"成功创建{generator_type}生成器，彩票类型: {lottery_type}")
            return generator
            
        except Exception as e:
            self.logger.error(f"创建生成器失败: {str(e)}")
            raise GeneratorError(f"创建生成器失败: {str(e)}")
    
    def register_generator(self, name: str, generator_class: Type[NumberGenerator]):
        """注册新的生成器类型
        
        Args:
            name: 生成器名称
            generator_class: 生成器类
        """
        if not issubclass(generator_class, NumberGenerator):
            raise GeneratorError(f"生成器类必须继承自NumberGenerator")
        
        self._generators[name] = generator_class
        self.logger.info(f"注册新生成器类型: {name}")
    
    def unregister_generator(self, name: str):
        """注销生成器类型
        
        Args:
            name: 生成器名称
        """
        if name in self._generators:
            del self._generators[name]
            self.logger.info(f"注销生成器类型: {name}")
        else:
            self.logger.warning(f"尝试注销不存在的生成器类型: {name}")
    
    def get_available_generators(self) -> List[str]:
        """获取可用的生成器类型
        
        Returns:
            生成器类型列表
        """
        return list(self._generators.keys())
    
    def get_generator_info(self, generator_type: str) -> Dict:
        """获取生成器信息
        
        Args:
            generator_type: 生成器类型
            
        Returns:
            生成器信息字典
        """
        generator_class = self._generators.get(generator_type)
        if not generator_class:
            return {}
        
        return {
            'name': generator_type,
            'class': generator_class.__name__,
            'module': generator_class.__module__,
            'doc': generator_class.__doc__ or "无描述"
        }
    
    def create_all_generators(self, lottery_type: str) -> Dict[str, NumberGenerator]:
        """创建所有类型的生成器
        
        Args:
            lottery_type: 彩票类型
            
        Returns:
            生成器字典
        """
        generators = {}
        for generator_type in self._generators:
            try:
                generators[generator_type] = self.create_generator(generator_type, lottery_type)
            except Exception as e:
                self.logger.error(f"创建{generator_type}生成器失败: {str(e)}")
        
        return generators

# 全局工厂实例
_factory_instance: Optional[GeneratorFactory] = None

def get_generator_factory() -> GeneratorFactory:
    """获取生成器工厂单例
    
    Returns:
        生成器工厂实例
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = GeneratorFactory()
    return _factory_instance

def create_generator(generator_type: str, lottery_type: str, **kwargs) -> NumberGenerator:
    """便捷函数：创建生成器
    
    Args:
        generator_type: 生成器类型
        lottery_type: 彩票类型
        **kwargs: 其他参数
        
    Returns:
        生成器实例
    """
    factory = get_generator_factory()
    return factory.create_generator(generator_type, lottery_type, **kwargs)

def get_available_generators() -> List[str]:
    """便捷函数：获取可用生成器类型
    
    Returns:
        生成器类型列表
    """
    factory = get_generator_factory()
    return factory.get_available_generators()