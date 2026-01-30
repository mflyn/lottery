import pandas as pd
import numpy as np
import json
from typing import List, Any

class NumpyEncoder(json.JSONEncoder):
    """用于处理 NumPy 数据类型的 JSON 编码器"""
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
                              np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def ensure_int_list(value: Any) -> List[int]:
    """将各种格式的号码值转换为整数列表
    
    支持格式：
    - 整数列表/元组
    - NumPy 数组
    - 逗号/空格分隔的字符串
    - JSON 字符串格式的列表
    """
    if value is None:
        return []
    
    # 处理 NumPy 数组
    if hasattr(value, 'tolist') and not isinstance(value, (str, bytes)):
        return ensure_int_list(value.tolist())
    
    # 处理列表/元组/集合
    if isinstance(value, (list, tuple, set)):
        result = []
        for item in value:
            try:
                if pd.isna(item):
                    continue
            except (TypeError, ValueError):
                pass
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                continue
        return result
    
    # 处理字符串
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        
        # 处理 JSON 数组格式 "[1, 2, 3]"
        if text.startswith('[') and text.endswith(']'):
            try:
                import json
                parsed = json.loads(text)
                return ensure_int_list(parsed)
            except Exception:
                text = text[1:-1]
        
        # 统一分隔符并分割
        text = text.replace('，', ',').replace('、', ',').replace(';', ',').replace('；', ',')
        parts = [p.strip() for p in text.replace(' ', ',').split(',') if p.strip()]
        
        result = []
        for part in parts:
            try:
                result.append(int(float(part)))
            except ValueError:
                continue
        return result
    
    # 处理单个数值
    try:
        if pd.isna(value):
            return []
    except (TypeError, ValueError):
        pass
    
    try:
        return [int(value)]
    except (TypeError, ValueError):
        return []
