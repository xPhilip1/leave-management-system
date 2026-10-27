# config.py
# 数据库配置文件

DB_CONFIG = {
    'host': 'localhost',        # 数据库地址
    'port': 3306,               # 数据库端口
    'user': 'root',             # 数据库用户名
    'password': 'your_db_password',   # ← 改成你自己的数据库密码
    'database': 'campus_leave_system',
    'charset': 'utf8mb4',
    'cursorclass': None         # 在app.py中设置
}

# 服务器配置
SERVER_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}

# 应用配置
APP_CONFIG = {
    'secret_key': 'your-secret-key-change-this-in-production'
}