from typing import Dict, Type
from .base import NumberGenerator
from .random_generator import RandomGenerator
from .smart_generator import SmartGenerator

class GeneratorFactory:
    """号码生成器工厂"""
    
    _generators: Dict[str, Type[NumberGenerator]] = {
        'random': RandomGenerator,
        'smart': SmartGenerator
    }
    
    @classmethod
    def create_generator(cls, generator_type: str, lottery_type: str) -> NumberGenerator:
        """创建生成器实例"""
        generator_class = cls._generators.get(generator_type)
        if not generator_class:
            raise ValueError(f"Unsupported generator type: {generator_type}")
        return generator_class(lottery_type)