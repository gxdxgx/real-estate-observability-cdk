# ベースイメージとしてNode.jsの最新LTSバージョンを使用
FROM node:lts

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# AWS CDKをグローバルにインストール
RUN npm install -g aws-cdk

# TypeScriptをグローバルにインストール
RUN npm install -g typescript

# # プロジェクトファイルをコピー
COPY . /app

# # プロジェクトの依存関係をコピーしてインストール
WORKDIR my-cdk-app

RUN npm install

# # デフォルトコマンドを設定
CMD ["bash"]