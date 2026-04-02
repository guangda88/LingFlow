# LingFlow GitHub Action - Dockerfile
# 基于 Python 3.11，安装 LingFlow CLI

FROM python:3.11-slim as base

# 设置工作目录
WORKDIR /action

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# 安装 GitHub CLI（用于 PR 评论）
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && \
    apt-get install -y gh && \
    apt-get clean

# 复制 LingFlow 源码
COPY . /tmp/lingflow/
WORKDIR /tmp/lingflow

# 安装 LingFlow
RUN pip install --no-cache-dir -e .

# 切换到工作目录
WORKDIR /github/workspace

# 复制入口脚本
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 创建输出目录
RUN mkdir -p /github/workspace/.lingflow

# 设置入口点
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# 默认参数
CMD ["review", "./src", "markdown", "false", ""]
