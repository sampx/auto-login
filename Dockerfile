# 使用Python官方镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置时区为中国时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 文件并安装 Python 依赖
# 由于 requirements.txt 通常不会每次都改变，所以把它放在靠前的位置，以便利用缓存
COPY requirements.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright的浏览器
RUN playwright install chromium
RUN playwright install-deps

# 复制项目文件
# 由于项目文件可能频繁改变，因此放在 Dockerfile 的最后部分
COPY . .

# 运行应用
CMD ["python", "auto_login.py"]
