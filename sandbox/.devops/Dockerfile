FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_PROJECT_ENVIRONMENT="/venv"
ENV UV_LINK_MODE=copy

# 1. 安装基础工具+OpenSSH Server
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    git \
    sudo \
    openssh-server \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/run/sshd

# 2. 配置 SSH 的账户密码
RUN echo 'root:root' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# 3. 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 4. 设置工作环境
WORKDIR /workspace

# 5. 预先配置环境，将基础依赖项+Python版本同步到沙箱中并创建环境
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# 6. 开发 SSH 端口(22) 和应用端口(9528)
EXPOSE 22 9528

# 7. 启动 SSH 服务(前台运行，否则容器会立即退出)
CMD ["/usr/sbin/sshd", "-D"]

