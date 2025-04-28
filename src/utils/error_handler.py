class ErrorHandler:
    """错误处理器"""
    def __init__(self):
        pass
    
    def safe_execute(self, func, *args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return {'success': True, 'result': result}
        except Exception as e:
            return {
                'success': False,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }