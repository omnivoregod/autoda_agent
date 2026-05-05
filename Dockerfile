# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 复制wait-for-it脚本并设置执行权限
COPY wait-for-it.sh .
RUN chmod +x wait-for-it.sh

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 启动命令（等待MySQL就绪后再启动Streamlit）
CMD ["./wait-for-it.sh", "mysql:3306", "--", "streamlit", "run", "app.py", "--server.headless=true", "--server.address=0.0.0.0"]
