# Lambda互換イメージをベースに、開発環境を構築
FROM public.ecr.aws/lambda/python:3.12

# Lambdaイメージのエントリーポイントを無効化（開発用）
ENTRYPOINT []

# システムパッケージの更新とNode.jsのインストール
# Lambda互換イメージはAmazon Linux 2023ベース（microdnf使用）
RUN microdnf update -y && \
    microdnf install -y git unzip tar gzip xz && \
    # Node.js 20のインストール（バイナリから直接インストール）
    curl -fsSL https://nodejs.org/dist/v20.18.0/node-v20.18.0-linux-x64.tar.xz | tar -xJ -C /usr/local --strip-components=1 && \
    # クリーンアップ
    microdnf clean all

# AWS CDKとTypeScriptをグローバルにインストール
RUN npm install -g aws-cdk@2.1100.1 typescript@latest

# AWS CLIのインストール
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf aws awscliv2.zip

# Docker CLIのインストール（CDK bundling用）
RUN DOCKER_VERSION=24.0.7 && \
    curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz | \
    tar -xzC /tmp && \
    mv /tmp/docker/docker /usr/local/bin/ && \
    rm -rf /tmp/docker && \
    chmod +x /usr/local/bin/docker

# アプリケーションディレクトリの作成
RUN mkdir -p /app
WORKDIR /app

# パッケージファイルをコピー（依存関係インストール用）
COPY infrastructure/package*.json ./infrastructure/
COPY src/requirements.txt ./src/
COPY tests/requirements.txt ./tests/

# Node.js依存関係のインストール
WORKDIR /app/infrastructure
RUN npm install

RUN /var/lang/bin/python3.12 -m pip install --upgrade pip

# Lambda Layerのビルド（requirements.txtから直接インストール）
# COPY . /app/の前に実行することで、古いLayerが上書きされない
RUN mkdir -p /app/lambda-layer && \
    /var/lang/bin/python3.12 -m pip install \
      --no-cache-dir \
      --only-binary=:all: \
      -r /app/src/requirements.txt \
      -t /app/lambda-layer/python

# アプリケーションコードをコピー（lambda-layerは.dockerignoreで除外されている）
COPY . /app/

# スクリプトを実行可能に
RUN chmod +x /app/scripts/*.sh

# 環境変数設定
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV NODE_ENV=development

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node --version && /var/lang/bin/python3.12 --version && cdk --version

# デフォルトコマンド
CMD ["bash"]
