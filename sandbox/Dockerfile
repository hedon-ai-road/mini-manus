# 使用ubuntu基础镜像来源
FROM ubuntu:22.04

# 安装过程避免交互式提示并设置主机名
ENV DEBIAN_FRONTEND=noninteractive
ENV HOSTNAME=sandbox

# 将ubuntu默认的apt软件源地址统一换成阿里云镜像源
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' /etc/apt/sources.list && \
    sed -i 's|http://security.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' /etc/apt/sources.list && \
    sed -i 's|http://ports.ubuntu.com/ubuntu-ports/|http://mirrors.aliyun.com/ubuntu-ports/|g' /etc/apt/sources.list

# 更新和安装基础软件后并移除依赖
RUN apt-get update && apt-get install -y \
    sudo bc curl wget gnupg software-properties-common supervisor \
    xterm socat xvfb x11vnc websockify\
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 创建用户ubuntu并赋予sudo权限
RUN useradd -m -d /home/ubuntu -s /bin/bash ubuntu && \
    echo "ubuntu ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ubuntu

# 安装Python 3.10版本(非uv)
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-venv python3.10-dev python3-pip && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 为pip3配置阿里云镜像源
RUN pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 安装 node.js 24.12.0 版本(lts)
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 将npm镜像源设置为阿里云镜像源
RUN npm config set registry https://registry.npmmirror.com

# 安装 Google chrome 浏览器
RUN add-apt-repository ppa:xtradeb/apps -y && \
    apt-get update && \
    apt-get install -y chromuim --no-install-recommends && \
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

# 设置工作空间
WORKDIR /sandbox

# 拷贝项目依赖文件到工作空间并安装依赖
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# 拷贝项目文件
COPY . .

# 将supervisor配置文件拷贝到supervisor服务的配置目录
COPY supervisor.conf /etc/supervisor/conf.d/sandbox.conf

# 暴露端口 9528(FastAPI) 9222(CDP) 5900(VNC) 5901(Websocket)
EXPOSE 9528 9222 5900 5901

# 额外的环境变量配置
ENV ENV_CHROME_ARGS=""
ENV CHROME_ARGS=""
ENV UVI_ARGS=""

# 启动supervisor服务
CMD ["supervisord", "-n", "-c", "/sandbox/supervisor.conf"]