FROM python:3.9-slim
WORKDIR /app
# 优化：先装依赖，利用 Docker 缓存机制
COPY requirements.txt .
RUN pip install --no-cache-dif -r flask flask-cors redis -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . .
CMD ["python", "app.py"]
