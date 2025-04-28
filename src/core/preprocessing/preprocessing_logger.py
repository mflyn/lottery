import logging
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

class PreprocessingLogger:
    """预处理日志记录器"""
    
    def __init__(self, log_dir: str = 'logs/preprocessing'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置文件处理器
        self.logger = logging.getLogger('preprocessing')
        self.logger.setLevel(logging.INFO)
        
        # 创建新的日志文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f"preprocessing_{timestamp}.log"
        
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
        
        # 记录详细信息的字典
        self.details = {
            'start_time': datetime.now().isoformat(),
            'operations': [],
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
    def log_operation(self, 
                     operation: str, 
                     details: Dict[str, Any],
                     status: str = 'success'):
        """记录操作"""
        self.details['operations'].append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'details': details,
            'status': status
        })
        
        self.logger.info(
            f"Operation: {operation} - Status: {status} - "
            f"Details: {json.dumps(details, ensure_ascii=False)}"
        )
        
    def log_error(self, error_msg: str, details: Dict[str, Any]):
        """记录错误"""
        self.details['errors'].append({
            'timestamp': datetime.now().isoformat(),
            'message': error_msg,
            'details': details
        })
        
        self.logger.error(
            f"Error: {error_msg} - "
            f"Details: {json.dumps(details, ensure_ascii=False)}"
        )
        
    def log_warning(self, warning_msg: str, details: Dict[str, Any]):
        """记录警告"""
        self.details['warnings'].append({
            'timestamp': datetime.now().isoformat(),
            'message': warning_msg,
            'details': details
        })
        
        self.logger.warning(
            f"Warning: {warning_msg} - "
            f"Details: {json.dumps(details, ensure_ascii=False)}"
        )
        
    def update_statistics(self, stats: Dict[str, Any]):
        """更新统计信息"""
        self.details['statistics'].update(stats)
        
    def export_report(self, filepath: str):
        """导出完整的处理报告"""
        self.details['end_time'] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.details, f, ensure_ascii=False, indent=2)

    def log_data_stats(self, 
                      dataset_name: str,
                      row_count: int,
                      column_stats: Dict[str, Dict[str, Any]]):
        """记录数据集统计信息
        
        Args:
            dataset_name: 数据集名称
            row_count: 行数
            column_stats: 列统计信息
        """
        stats = {
            'dataset': dataset_name,
            'timestamp': datetime.now().isoformat(),
            'row_count': row_count,
            'columns': column_stats
        }
        
        self.details['statistics'][dataset_name] = stats
        self.logger.info(
            f"Dataset Stats - {dataset_name} - "
            f"Rows: {row_count} - "
            f"Columns: {len(column_stats)}"
        )

    def log_transformation(self,
                         transform_type: str,
                         params: Dict[str, Any],
                         affected_columns: List[str]):
        """记录数据转换操作
        
        Args:
            transform_type: 转换类型
            params: 转换参数
            affected_columns: 受影响的列
        """
        transform_info = {
            'type': transform_type,
            'params': params,
            'affected_columns': affected_columns,
            'timestamp': datetime.now().isoformat()
        }
        
        self.details['operations'].append({
            'category': 'transformation',
            'info': transform_info
        })
        
        self.logger.info(
            f"Transform: {transform_type} - "
            f"Columns: {', '.join(affected_columns)}"
        )

    def log_validation(self,
                      validation_type: str,
                      results: Dict[str, Any],
                      threshold: Optional[float] = None):
        """记录数据验证结果
        
        Args:
            validation_type: 验证类型
            results: 验证结果
            threshold: 验证阈值（可选）
        """
        validation_info = {
            'type': validation_type,
            'results': results,
            'threshold': threshold,
            'timestamp': datetime.now().isoformat()
        }
        
        if not all(results.values()):
            self.log_warning(
                f"Validation failed: {validation_type}",
                validation_info
            )
        
        self.details['operations'].append({
            'category': 'validation',
            'info': validation_info
        })

    def generate_summary(self) -> Dict[str, Any]:
        """生成处理摘要
        
        Returns:
            包含处理摘要信息的字典
        """
        return {
            'duration': (
                datetime.fromisoformat(self.details['operations'][-1]['timestamp'])
                - datetime.fromisoformat(self.details['start_time'])
            ).total_seconds(),
            'operation_count': len(self.details['operations']),
            'error_count': len(self.details['errors']),
            'warning_count': len(self.details['warnings']),
            'datasets_processed': list(self.details['statistics'].keys())
        }

    def export_html_report(self, filepath: str):
        """导出HTML格式的报告
        
        Args:
            filepath: 报告文件路径
        """
        summary = self.generate_summary()
        
        html_content = [
            "<html><head><style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            ".error { color: red; }",
            ".warning { color: orange; }",
            "</style></head><body>",
            "<h1>数据预处理报告</h1>",
            f"<h2>处理摘要</h2>",
            f"<p>处理时长: {summary['duration']:.2f} 秒</p>",
            f"<p>操作数量: {summary['operation_count']}</p>",
            f"<p>错误数量: {summary['error_count']}</p>",
            f"<p>警告数量: {summary['warning_count']}</p>"
        ]
        
        # 添加操作日志表格
        html_content.extend([
            "<h2>操作日志</h2>",
            "<table>",
            "<tr><th>时间</th><th>操作</th><th>状态</th><th>详情</th></tr>"
        ])
        
        for op in self.details['operations']:
            html_content.append(
                f"<tr><td>{op['timestamp']}</td>"
                f"<td>{op.get('operation', op.get('category', ''))}</td>"
                f"<td>{op.get('status', '')}</td>"
                f"<td>{json.dumps(op.get('details', op.get('info', '')), ensure_ascii=False)}</td></tr>"
            )
        
        html_content.append("</table></body></html>")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
