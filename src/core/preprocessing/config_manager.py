from typing import Dict, Any, List
from pathlib import Path
import yaml

class PreprocessingConfigManager:
    """预处理配置管理器"""
    
    def __init__(self, config_dir: str = 'configs/preprocessing'):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def save_config(self, name: str, config: Dict[str, Any]):
        """保存配置"""
        filepath = self.config_dir / f"{name}.yaml"
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
            
    def load_config(self, name: str) -> Dict[str, Any]:
        """加载配置"""
        filepath = self.config_dir / f"{name}.yaml"
        if not filepath.exists():
            raise FileNotFoundError(f"配置文件不存在: {filepath}")
            
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def list_configs(self) -> List[str]:
        """列出所有可用配置"""
        return [f.stem for f in self.config_dir.glob("*.yaml")]
        
    def delete_config(self, name: str):
        """删除配置"""
        filepath = self.config_dir / f"{name}.yaml"
        if filepath.exists():
            filepath.unlink()
            
    def create_default_config(self) -> Dict[str, Any]:
        """创建默认配置"""
        # General tables and both lottery types share an unconstrained default.
        # Dataset-specific validation/transforms can be saved in named configs.
        return {
            'validation_rules': {},
            'transformers': {},
            'cleaning': {'remove_duplicates': True}
        }
