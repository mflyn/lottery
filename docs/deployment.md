# 部署指南

## 1. 系统要求
- 操作系统: Windows 7+/macOS/Linux
- Python: 3.8+
- 内存: ≥4GB
- 磁盘空间: ≥1GB

## 2. 安装步骤

### 2.1 环境准备
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2.2 配置文件
1. 复制配置模板
```bash
cp config/config.template.yaml config/config.yaml
```

2. 修改配置参数
- 数据库连接
- 缓存设置
- 日志配置

### 2.3 初始化数据
```bash
python scripts/init_database.py
python scripts/import_history.py
```

## 3. 启动服务
```bash
python src/main.py
```

## 4. 更新维护

### 4.1 数据更新
```bash
python scripts/update_data.py
```

### 4.2 备份还原
```bash
# 备份数据
python scripts/backup.py

# 还原数据
python scripts/restore.py [backup_file]
```

## 5. 故障排除
- 检查日志文件: logs/app.log
- 验证配置文件
- 确认数据完整性