import time
from concurrent.futures import ThreadPoolExecutor
from src.core.number_generator import LotteryNumberGenerator
from src.core.features.feature_engineering import FeatureEngineering

class LoadTester:
    """负载测试类"""
    
    def __init__(self):
        self.number_generator = LotteryNumberGenerator()
        self.feature_engineering = FeatureEngineering()
    
    def test_concurrent_users(self, num_users: int, duration: int):
        """测试并发用户"""
        start_time = time.time()
        results = []
        
        def user_session():
            while time.time() - start_time < duration:
                try:
                    # 模拟用户操作
                    self.number_generator.generate_dlt_numbers()
                    self.feature_engineering.extract_basic_features()
                    time.sleep(0.1)  # 模拟思考时间
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
                    return
                
            results.append({"success": True})
        
        # 创建并发用户
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_session) for _ in range(num_users)]
            for future in futures:
                future.result()
        
        return results
    
    def test_large_dataset(self, size: int):
        """测试大数据集处理"""
        import psutil
        process = psutil.Process()
        
        start_time = time.time()
        initial_memory = process.memory_info().rss
        
        # 生成大量测试数据
        test_data = [i for i in range(size)]
        
        try:
            # 执行特征工程
            self.feature_engineering.process_large_dataset(test_data)
            
            end_time = time.time()
            final_memory = process.memory_info().rss
            
            return {
                "success": True,
                "processing_time": end_time - start_time,
                "memory_usage": final_memory - initial_memory,
                "data_size": size
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_memory_stress(self, target_size: str):
        """测试内存压力"""
        import gc
        
        # 将目标大小转换为字节
        size_map = {'MB': 1024*1024, 'GB': 1024*1024*1024}
        size_value = int(target_size[:-2])
        size_unit = target_size[-2:]
        target_bytes = size_value * size_map[size_unit]
        
        try:
            # 逐步增加内存使用
            data = []
            current_size = 0
            chunk_size = 1024 * 1024  # 1MB
            
            while current_size < target_bytes:
                data.append([0] * chunk_size)
                current_size += chunk_size * 8  # 假设每个数字占8字节
                
                # 执行一些计算
                self.feature_engineering.process_chunk(data[-1])
            
            # 清理内存
            del data
            gc.collect()
            
            return {"success": True}
            
        except MemoryError as e:
            return {
                "success": False,
                "error": "内存不足",
                "details": str(e)
            }