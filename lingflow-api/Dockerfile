# LingFlow REST API - Dockerfile
# 多阶段构建，优化镜像大小

# ===========================
# Stage 1: 基础环境
# ===========================
FROM python:3.11-slim as base

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ===========================
# Stage 2: CLI 镜像
# ===========================
FROM base as cli

# 复制 LingFlow 核心库
COPY lingflow/ /app/lingflow/
COPY setup.py /app/
COPY pyproject.toml /app/

# 安装 LingFlow
RUN pip install -e .

# 设置入口点
ENTRYPOINT ["lingflow"]

# ===========================
# Stage 3: API 镜像
# ===========================
FROM base as api

# 复制应用代码
COPY lingflow-api/app/ /app/app/
COPY lingflow/ /app/lingflow/

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ===========================
# Stage 4: MCP Server 镜像
# ===========================
FROM base as mcp

# 复制代码
COPY mcp_server/ /app/mcp_server/
COPY lingflow/ /app/lingflow/

# 安装 LingFlow MCP Server
RUN cd /app/mcp_server && pip install -e .

# 启动命令
CMD ["lingflow-mcp", "run"]

# ===========================
# Stage 5: 生产镜像（最小化）
# ===========================
FROM python:3.11-slim as production

# 非root用户
RUN useradd -m -u 1000 lingflow

WORKDIR /app

# 只复制运行时需要的文件
COPY --from=api /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=api /app /app

# 切换用户
USER lingflow

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
