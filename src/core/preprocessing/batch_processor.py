from typing import List, Dict, Optional
import pandas as pd
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
from .data_preprocessor import DataPreprocessor

class BatchProcessor:
    """数据批处理器"""
    
    def __init__(self, preprocessor: DataPreprocessor):
        self.preprocessor = preprocessor
        self.logger = logging.getLogger(__name__)
        
    def process_files(self, 
                     input_files: List[str],
                     output_dir: str,
                     max_workers: int = 4) -> Dict[str, Dict]:
        """批量处理多个文件"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self._process_single_file, 
                              input_file, 
                              output_dir): input_file
                for input_file in input_files
            }
            
            for future in future_to_file:
                input_file = future_to_file[future]
                try:
                    results[input_file] = future.result()
                except Exception as e:
                    self.logger.error(f"处理文件失败 {input_file}: {str(e)}")
                    results[input_file] = {'status': 'error', 'error': str(e)}
                    
        return results
        
    def _process_single_file(self, 
                           input_file: str, 
                           output_dir: str) -> Dict:
        """处理单个文件"""
        try:
            # 读取数据
            data = pd.read_csv(input_file)
            
            # 预处理
            processed_data = self.preprocessor.preprocess_data(data)
            
            # 保存结果
            output_path = Path(output_dir) / f"processed_{Path(input_file).name}"
            processed_data.to_csv(output_path, index=False)
            
            return {
                'status': 'success',
                'input_rows': len(data),
                'output_rows': len(processed_data),
                'output_path': str(output_path)
            }
            
        except Exception as e:
            raise Exception(f"处理文件 {input_file} 失败: {str(e)}")