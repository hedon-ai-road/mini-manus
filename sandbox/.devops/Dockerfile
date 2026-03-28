# 使用ubuntu基础镜像来源
FROM ubuntu:22.04

# 安装过程避免交互式提示并设置主机名、uv环境目录、uv连接模式
ENV DEBIAN_FRONTEND=noninteractive
ENV HOSTNAME=sandbox
ENV UV_PROJECT_ENVIRONMENT="/venv"
ENV UV_LINK_MODE=copy

# 将ubuntu默认的apt软件源地址统一换成阿里云镜像源
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' /etc/apt/sources.list && \
    sed -i 's|http://security.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' /etc/apt/sources.list && \
    sed -i 's|http://ports.ubuntu.com/ubuntu-ports/|http://mirrors.aliyun.com/ubuntu-ports/|g' /etc/apt/sources.list

# 更新和安装基础软件（含SSH服务）后并移除依赖
# mkdir /var/run/sshd 是SSH服务启动必须的目录
RUN apt-get update && apt-get install -y \
    sudo bc curl wget gnupg software-properties-common \
    ca-certificates git openssh-server \
    supervisor xterm socat xvfb x11vnc websockify \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir /var/run/sshd

# 创建用户ubuntu并赋予sudo权限
RUN useradd -m -d /home/ubuntu -s /bin/bash ubuntu && \
    echo "ubuntu ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ubuntu

# 配置SSH的账户密码(开发环境设置root账号密码为root)
RUN echo 'root:root' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# 安装 node.js 24.x 版本(lts)
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 将npm镜像源设置为阿里云镜像源
RUN npm config set registry https://registry.npmmirror.com

# 安装 Google Chrome 浏览器
RUN add-apt-repository ppa:xtradeb/apps -y && \
    apt-get update && \
    apt-get install -y chromium --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 安装中文字体和语言支持
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    language-pack-zh-hans \
    locales && \
    locale-gen zh_CN.UTF-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置默认编码
ENV LANG=zh_CN.UTF-8
ENV LANGUAGE=zh_CN:zh
ENV LC_ALL=zh_CN.UTF-8

# 安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 设置工作空间
WORKDIR /sandbox

# 拷贝项目依赖文件到工作空间并同步uv环境
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# 拷贝项目文件
COPY . .

# 暴露端口 22(SSH) 9528(FastAPI) 9222(CDP) 5900(VNC) 5901(Websocket)
EXPOSE 22 9528 9222 5900 5901

# 额外的环境变量配置
ENV ENV_CHROME_ARGS=""
ENV CHROME_ARGS=""
ENV UVI_ARGS=""

# 启动supervisor服务
CMD ["supervisord", "-n", "-c", "/sandbox/.devops/supervisord.conf"]
