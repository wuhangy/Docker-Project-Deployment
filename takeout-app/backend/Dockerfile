FROM python:3.9-slim

WORKDIR /app

# 安装 MySQL 客户端（用于初始化）
RUN apt-get update && apt-get install -y default-mysql-client && rm -rf /var/lib/apt/lists/*

# 先装依赖，利用 Docker 缓存机制
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

# 等待 MySQL 启动并初始化数据
COPY init.sql /init.sql
COPY seed.py /seed.py

# 暴露端口
EXPOSE 5000

CMD ["python", "app.py"]
