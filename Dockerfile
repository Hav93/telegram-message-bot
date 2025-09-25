# 使用官方Python运行时作为基础镜像
FROM python:3.11-slim

# 设置代理参数
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG http_proxy
ARG https_proxy
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
ENV http_proxy=${http_proxy}
ENV https_proxy=${https_proxy}

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 注释掉Node.js安装，使用预构建的前端文件
# RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
#     && apt-get install -y nodejs \
#     && rm -rf /var/lib/apt/lists/*

# 复制Python依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制前端构建结果（需要先在本地构建）
COPY app/frontend/dist ./frontend/dist

# 复制应用代码 - 后端Python文件
COPY app/backend ./

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/temp /app/sessions

# NAS环境数据库优化已包含在*.py复制中

# 设置权限
RUN chmod -R 755 /app && \
    chmod +x /app/web_enhanced_clean.py

# 创建健康检查脚本
RUN echo '#!/bin/bash\ncurl -f http://localhost:9393/api/system/enhanced-status >/dev/null 2>&1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/healthcheck.sh || exit 1

# 暴露端口
EXPOSE 9393

# 设置卷
VOLUME ["/app/data", "/app/logs", "/app/sessions"]

# 启动命令
CMD ["python", "web_enhanced_clean.py"]