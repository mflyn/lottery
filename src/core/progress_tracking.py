def handle_error(self, error_msg, callback=None):
    """处理错误"""
    if callback:
        callback(-1, f'错误: {error_msg}')
    return False

def track_progress(self, total_steps, callback=None):
    """跟踪进度"""
    for i in range(total_steps):
        if callback:
            callback(i / total_steps * 100, f'处理中 {i+1}/{total_steps}')
    return True