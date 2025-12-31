# 不動産観測システム CDK

AWS CDK、Lambda、DynamoDBを使用して構築された、モダンでスケーラブルなサーバーレス不動産データ観測アプリケーション。

## 🏗️ アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │────│   Lambda        │────│   DynamoDB      │
│                 │    │   関数群        │    │   テーブル群    │
│  - REST API     │    │  - ヘルスチェック│    │  - 物件情報     │
│  - CORS         │    │  - 物件取得     │    │  - GSI インデックス│
│  - スロットリング│    │  - 物件作成     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │   CloudWatch    │  │   X-Ray         │  │   SNS アラーム  │
    │   - ログ        │  │   - トレーシング │  │   - 通知        │
    │   - メトリクス   │  │   - パフォーマンス│  │   - アラート    │
    │   - ダッシュボード│  │   - デバッグ     │  │                 │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 🚀 機能

- **モダンアーキテクチャ**: AWS LambdaとDynamoDBによるサーバーレスファースト
- **型安全性**: インフラはTypeScript、Lambda関数はPythonによる完全な型サポート
- **観測可能性**: CloudWatch、X-Ray、カスタムメトリクスによる組み込み監視
- **テスト**: pytestによる包括的な単体・統合テスト
- **セキュリティ**: IAM最小権限、APIスロットリング、入力検証
- **マルチ環境**: dev、staging、production環境対応
- **Docker対応**: LocalStackを使用したコンテナ化開発環境
- **CI/CD対応**: デプロイスクリプトとInfrastructure as Code

## 📁 プロジェクト構造

```
real-estate-observability-cdk/
├── README.md
├── .gitignore
├── .env.example
├── Dockerfile
├── docker-compose.yml
│
├── infrastructure/                    # CDK インフラストラクチャ
│   ├── bin/app.ts                    # CDK エントリーポイント
│   ├── lib/
│   │   ├── stacks/                   # CDK スタック
│   │   ├── constructs/               # 再利用可能なコンストラクト
│   │   └── config/                   # 環境設定
│   ├── package.json
│   └── cdk.json
│
├── src/                              # アプリケーションコード
│   ├── handlers/                     # Lambda関数
│   │   ├── api/
│   │   │   ├── properties/           # 物件CRUD操作
│   │   │   ├── health/               # ヘルスチェックエンドポイント
│   │   │   └── common/               # 共有APIユーティリティ
│   │   └── data-processing/          # データ処理Lambda関数
│   ├── shared/                       # 共有ライブラリ
│   │   ├── database/                 # データベースモデルと接続
│   │   ├── logging/                  # 構造化ログ
│   │   └── utils/                    # 共通ユーティリティ
│   └── requirements.txt
│
├── tests/                            # テストスイート
│   ├── unit/                        # 単体テスト
│   ├── integration/                 # 統合テスト
│   ├── e2e/                         # エンドツーエンドテスト
│   ├── conftest.py                  # テスト設定
│   └── requirements.txt
│
├── scripts/                          # デプロイ・開発スクリプト
│   ├── deploy.sh                    # デプロイスクリプト
│   ├── test.sh                      # テストスクリプト
│   └── local-dev.sh                 # ローカル開発スクリプト
│
└── docs/                            # ドキュメント
    ├── api.md                       # API仕様書
    ├── deployment.md                # デプロイガイド
    └── architecture.md              # アーキテクチャ詳細
```

## 🛠️ 前提条件

- **Node.js** >= 18.0.0
- **Python** >= 3.11
- **AWS CLI** 適切な認証情報で設定済み
- **Docker** と **Docker Compose** (ローカル開発用)
- **AWS CDK** >= 2.100.0

## 🚀 クイックスタート

### 1. クローンとセットアップ

```bash
git clone <repository-url>
cd real-estate-observability-cdk

# 環境ファイルをコピー
cp .env.example .env

# 設定を編集
vim .env
```

### 2. Dockerコンテナ内でCDKを実行（推奨）

Dockerコンテナ内でCDKを実行する場合：

```bash
# Dockerコンテナをビルドして起動
docker-compose up -d --build cdk

# コンテナ内でシェルを開く
docker-compose exec cdk bash

# コンテナ内で依存関係をインストール（初回のみ）
cd infrastructure
npm install
cd ..

# AWS認証情報を設定（ホストマシンで）
aws configure
# または環境変数で設定
export AWS_PROFILE=default
export AWS_REGION=ap-northeast-1
```

**Dockerソケットについて:**
- CDKがLambda互換のDockerイメージでバンドリングするため、Dockerソケット（`/var/run/docker.sock`）をマウントしています
- これにより、コンテナ内からホストのDockerデーモンを使用できます

### 3. ホストマシンでのセットアップ（オプション）

ホストマシンで直接CDKを実行する場合：

```bash
# 必要なツールをインストール
# Node.js (v20以上)
node --version

# AWS CDK CLI
npm install -g aws-cdk@2.1100.1

# Docker (Lambda互換イメージでバンドリングするため)
docker --version

# 依存関係をインストール
cd infrastructure
npm install
cd ..

# AWS認証情報を設定
aws configure
```

### 4. LocalStackによるローカル開発（オプション）

LocalStackを使用する場合：

```bash
# LocalStackを起動
docker-compose up -d localstack

# LocalStackのヘルスチェック
curl http://localhost:4566/health
```

### 5. テスト実行

```bash
# 全テストを実行
./scripts/test.sh

# 単体テストのみ実行
./scripts/test.sh -t unit

# 詳細出力でテスト実行
./scripts/test.sh -v
```

### 6. AWSへのデプロイ

**Dockerコンテナ内からデプロイ（推奨）:**

```bash
# コンテナ内でシェルを開く
docker-compose exec cdk bash

# コンテナ内でデプロイ
cd infrastructure
cdk deploy --all --context environment=dev

# ステージング環境にデプロイ
cdk deploy --all --context environment=staging

# 本番環境にデプロイ（確認あり）
cdk deploy --all --context environment=prod
```

**ホストマシンから直接デプロイ:**

```bash
# 開発環境にデプロイ
cd infrastructure
cdk deploy --all --context environment=dev

# ステージング環境にデプロイ
cdk deploy --all --context environment=staging

# 本番環境にデプロイ（確認あり）
cdk deploy --all --context environment=prod
```

**または、デプロイスクリプトを使用:**

```bash
# 開発環境にデプロイ
./scripts/deploy.sh

# ステージング環境にデプロイ
./scripts/deploy.sh -e staging

# 本番環境にデプロイ（確認あり）
./scripts/deploy.sh -e prod
```

**初回デプロイ前のブートストラップ:**

```bash
# Dockerコンテナ内で実行
docker-compose exec cdk bash -c "cd infrastructure && cdk bootstrap aws://<AWS_ACCOUNT_ID>/<AWS_REGION>"

# またはホストマシンで実行
cd infrastructure
cdk bootstrap aws://<AWS_ACCOUNT_ID>/<AWS_REGION>
```

## 📋 APIエンドポイント

### ヘルスチェック
- `GET /` - APIの情報を含むウェルカムメッセージ
- `GET /health` - データベース状態を含むヘルスチェック

### 物件
- `GET /properties` - 全物件を取得
  - クエリパラメータ: `status`, `location`, `limit`
- `POST /properties` - 新しい物件を作成

### リクエスト/レスポンス例

**物件作成:**
```bash
curl -X POST https://your-api-url/properties \
  -H "Content-Type: application/json" \
  -d '{
    "address": "東京都渋谷区神南1-1-1",
    "price": 50000000,
    "location": "東京",
    "property_type": "マンション",
    "bedrooms": 2,
    "bathrooms": 1.0,
    "square_feet": 70,
    "description": "駅近の便利なマンション",
    "status": "active"
  }'
```

**物件取得:**
```bash
# 全物件を取得
curl https://your-api-url/properties

# ステータスでフィルタ
curl "https://your-api-url/properties?status=active&limit=10"
```

## 🔧 設定

### 環境変数

`.env.example`から`.env`ファイルを作成：

```bash
# AWS設定
AWS_REGION=ap-northeast-1
AWS_PROFILE=default

# 環境
ENVIRONMENT=dev
PROJECT_NAME=real-estate-observability

# データベース
DYNAMODB_TABLE_PREFIX=real-estate-observability

# API設定
API_STAGE=dev
CORS_ORIGINS=*

# ログ
LOG_LEVEL=INFO

# 監視
ENABLE_XRAY=true
ENABLE_CUSTOM_METRICS=true
```

### マルチ環境対応

アプリケーションは異なる設定で複数環境をサポート：

- **dev**: デバッグログ有効の開発環境
- **staging**: テスト用のステージング環境
- **prod**: 最適化設定の本番環境

## 🧪 テスト

プロジェクトには包括的なテストが含まれています：

```bash
# カバレッジ付きで全テストを実行
./scripts/test.sh

# 特定のテストタイプを実行
./scripts/test.sh -t unit        # 単体テストのみ
./scripts/test.sh -t integration # 統合テストのみ
./scripts/test.sh -t e2e         # エンドツーエンドテストのみ

# カバレッジなしでテスト実行
./scripts/test.sh -c

# 詳細テスト出力
./scripts/test.sh -v
```

## 🚀 デプロイ

### 手動デプロイ

```bash
# 開発環境にデプロイ
./scripts/deploy.sh

# 自動承認でステージングにデプロイ
./scripts/deploy.sh -e staging -y

# 本番にデプロイ（手動確認が必要）
./scripts/deploy.sh -e prod

# デプロイ中にテストをスキップ
./scripts/deploy.sh -t
```

### デプロイプロセス

1. **前提条件チェック**: AWS CLI、CDK、認証情報を検証
2. **テスト**: テストスイートを実行（スキップされない限り）
3. **ビルド**: TypeScriptをコンパイルし依存関係をインストール
4. **ブートストラップ**: 対象アカウントでCDKがブートストラップされていることを確認
5. **シンセシス**: CloudFormationテンプレートを生成
6. **デプロイ**: 全スタックをAWSにデプロイ
7. **出力**: デプロイ結果と次のステップを表示

## 📊 監視・観測可能性

### 組み込み監視

- **CloudWatch Logs**: 相関IDを含む構造化ログ
- **CloudWatch Metrics**: ビジネスKPI用カスタムメトリクス
- **X-Rayトレーシング**: パフォーマンス監視用の分散トレーシング
- **CloudWatch Alarms**: エラーとパフォーマンスの自動アラート
- **SNS通知**: 重要な問題に対するメール/SMS アラート

### ダッシュボード

デプロイによって以下を含むCloudWatchダッシュボードが作成されます：
- API Gateway メトリクス（リクエスト、レイテンシ、エラー）
- Lambda関数メトリクス（実行回数、実行時間、エラー）
- DynamoDB メトリクス（読み取り/書き込み容量、スロットリング）
- カスタムビジネスメトリクス

## 🔒 セキュリティ

- **IAM最小権限**: 関数は必要最小限の権限のみを持つ
- **APIスロットリング**: 悪用を防ぐレート制限
- **入力検証**: データ検証用のPydanticモデル
- **シークレット管理**: 機密データ用のAWS Secrets Manager
- **CORS設定**: 適切に設定されたクロスオリジンポリシー
- **ハードコードされたシークレットなし**: 環境変数とAWSサービスを使用

## 🛠️ 開発

### ローカル開発

```bash
# 開発環境を開始
./scripts/local-dev.sh start

# ログを表示
./scripts/local-dev.sh logs

# 環境を停止
./scripts/local-dev.sh stop

# コンテナ内でテスト実行
./scripts/local-dev.sh test
```

### 新機能の追加

1. **Lambda関数作成**: `src/handlers/`に新しいハンドラーを追加
2. **CDKスタック更新**: LambdaとAPI Gatewayリソースを追加
3. **テスト追加**: 単体・統合テストを作成
4. **ドキュメント更新**: API仕様書を追加
5. **デプロイ**: デプロイスクリプトを使用して変更をデプロイ

### コードスタイル

- **TypeScript**: インフラコード用のESLint + Prettier
- **Python**: Lambda関数用のBlack + isort
- **コミットメッセージ**: Conventional commitsフォーマット
- **プリコミットフック**: 自動コードフォーマットとリント

## 📚 ドキュメント

- [API仕様書](docs/api.md) - 詳細なAPIリファレンス
- [デプロイガイド](docs/deployment.md) - 本番環境デプロイガイド
- [アーキテクチャ詳細](docs/architecture.md) - 詳細なアーキテクチャドキュメント

## 🤝 貢献

1. リポジトリをフォーク
2. フィーチャーブランチを作成: `git checkout -b feature/new-feature`
3. 変更を加えテストを追加
4. テストを実行: `./scripts/test.sh`
5. 変更をコミット: `git commit -am '新機能を追加'`
6. ブランチをプッシュ: `git push origin feature/new-feature`
7. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🆘 サポート

質問やサポートについては：

- リポジトリでissueを作成
- `docs/`ディレクトリのドキュメントを確認
- ランタイム問題についてはCloudWatchログを確認
- パフォーマンスデバッグにはAWS X-Rayを使用

---

**AWS CDK、Lambda、DynamoDBを使用して❤️で構築**