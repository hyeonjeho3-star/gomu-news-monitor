# Gomu News Monitor 🔔

高品質な生産レベルのニュースモニタリングシステム / Production-grade news monitoring system for [gomuhouchi.com](https://gomuhouchi.com/)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 概要 / Overview

Gomu News Monitorは、ゴム業界ニュースサイト（gomuhouchi.com）を自動的に監視し、指定されたキーワードに一致する新しい記事が公開されたときにメール通知を送信するPython製のモニタリングシステムです。

**主な機能:**
- ✅ 自動的なウェブスクレイピング（Selenium + BeautifulSoup）
- ✅ キーワードベースのフィルタリング
- ✅ HTML形式のメール通知
- ✅ **スマート重複防止**（GitHub Actions Artifacts + SQLite）
- ✅ **日本語→韓国語自動翻訳**（記事タイトル）
- ✅ プレミアムコンテンツへのログイン対応
- ✅ エラーハンドリングと再試行ロジック
- ✅ 継続的モニタリング（デーモンモード）
- ✅ 詳細なログ記録と統計

### 🔄 スマート重複防止機能

GitHub Actions Artifactsを活用した高度な重複防止システム：

**動作原理:**
```
実行1 (09:00) → 5件の記事発見 → 5件のメール送信 ✉️
実行2 (12:00) → 7件の記事発見 → 2件のみメール送信 ✉️ (5件は重複)
実行3 (15:00) → 7件の記事発見 → メール送信なし (すべて重複)
```

**主な特徴:**
- ✅ 既に通知した記事は再送信しない
- ✅ GitHub Actions Artifactsでデータベースを90日間保持
- ✅ ローカル実行とクラウド実行の両方に対応
- ✅ 自動的なデータベース復元とアップロード
- ✅ 最大圧縮（レベル9）で容量を節約

**詳細ガイド:**
完全な動作原理、検証方法、トラブルシューティングについては [GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md) の「🔄 中複 기사 방지 기능」セクションをご覧ください。

### 🌐 日本語→韓国語自動翻訳

記事タイトルを自動的に日本語から韓国語に翻訳：

**機能:**
- ✅ Google Translate APIを使用した高品質な翻訳
- ✅ 翻訳キャッシュで性能向上
- ✅ メール通知に原文と翻訳文の両方を表示
- ✅ 翻訳エラー時も通常動作を継続

**設定:**
```yaml
# config.yaml
translation:
  enabled: true              # 翻訳機能を有効化
  cache_enabled: true        # 翻訳キャッシュを有効化
  fallback_on_error: true    # エラー時も継続
```

## 🏗️ プロジェクト構造 / Project Structure

```
gomu-news-monitor/
├── src/
│   ├── __init__.py          # パッケージ初期化
│   ├── config.py            # 設定管理
│   ├── database.py          # SQLiteデータベース操作
│   ├── auth.py              # 認証とセッション管理
│   ├── scraper.py           # ウェブスクレイピングロジック
│   └── notifier.py          # メール通知
├── data/
│   └── articles.db          # SQLiteデータベース
├── logs/
│   └── monitor.log          # ログファイル
├── tests/
│   └── test_scraper.py      # ユニットテスト
├── .env.example             # 環境変数テンプレート
├── config.yaml              # メイン設定ファイル
├── requirements.txt         # Python依存関係
├── main.py                  # メインエントリーポイント
└── README.md                # このファイル
```

## 🚀 クイックスタート / Quick Start

### 1. 必要要件 / Prerequisites

- Python 3.8以上
- Google Chrome ブラウザ
- Gmail アカウント（またはSMTPサーバー）

### 2. インストール / Installation

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/gomu-news-monitor.git
cd gomu-news-monitor

# 依存関係をインストール
pip install -r requirements.txt
```

### 3. 設定 / Configuration

#### A. 環境変数の設定

```bash
# .envファイルを作成
cp .env.example .env

# .envを編集して資格情報を入力
nano .env
```

**必須の環境変数:**

```ini
# サイトログイン情報
LOGIN_EMAIL=your_email@example.com
LOGIN_PASSWORD=your_password

# メール設定（Gmail推奨）
EMAIL_FROM=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_TO=recipient@example.com
```

**Gmail App Passwordの取得方法:**
1. [Google アカウント](https://myaccount.google.com/) にアクセス
2. セキュリティ → 2段階認証プロセスを有効化
3. アプリパスワードを生成
4. 生成されたパスワードを `EMAIL_PASSWORD` に設定

#### B. 設定ファイルのカスタマイズ

`config.yaml` を必要に応じて編集:

```yaml
site:
  url: "https://gomuhouchi.com/"
  keywords:
    - "バンドー化学"
    - "三ツ星ベルト"

monitoring:
  check_interval_minutes: 60

email:
  batch_notifications: true
  max_articles_per_email: 10
```

### 4. 実行 / Running

#### テストモード（1回実行）

```bash
python main.py --mode test
```

#### メール設定テスト

```bash
python main.py --test-email
```

#### デーモンモード（継続的監視）

```bash
python main.py --mode daemon
```

#### 統計表示

```bash
python main.py --stats --days 7
```

## 📖 詳細ドキュメント / Detailed Documentation

### コマンドラインオプション

```bash
python main.py [OPTIONS]

オプション:
  --mode {test,daemon}    実行モード（デフォルト: test）
                          test: 1回だけ実行
                          daemon: 継続的に実行

  --config PATH           設定ファイルのパス（デフォルト: config.yaml）

  --stats                 統計を表示して終了

  --test-email            テストメールを送信して終了

  --days N                統計の日数（デフォルト: 7）
```

### 設定オプション詳細

#### `config.yaml` の主要セクション

**1. サイト設定 (`site`)**

```yaml
site:
  url: "https://gomuhouchi.com/"

  # 通常キーワード
  keywords:
    - "バンドー化学"
    - "三ツ星ベルト"

  # 緊急キーワード（即時通知）
  urgent_keywords:
    - "リコール"
    - "事故"
```

**2. モニタリング設定 (`monitoring`)**

```yaml
monitoring:
  check_interval_minutes: 60        # チェック間隔
  request_timeout_seconds: 30       # リクエストタイムアウト
  max_retries: 3                    # 最大再試行回数
```

**3. メール設定 (`email`)**

```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  use_tls: true
  batch_notifications: true         # バッチ通知を有効化
  max_articles_per_email: 10        # メールあたりの最大記事数
```

**4. スクレイピング設定 (`scraping`)**

```yaml
scraping:
  headless: true                    # ヘッドレスモード
  user_agent_rotation: true         # User-Agentローテーション
  delay_between_requests_min: 1     # 最小遅延（秒）
  delay_between_requests_max: 3     # 最大遅延（秒）
  max_pages_to_scrape: 5            # 最大ページ数
```

**5. データベース設定 (`database`)**

```yaml
database:
  path: "data/articles.db"
  cleanup_enabled: true
  keep_records_days: 90             # レコード保持日数
```

## 🔒 セキュリティのベストプラクティス

1. **環境変数の使用**: パスワードをコードにハードコーディングしない
2. **`.env` をgitignore**: 資格情報をバージョン管理にコミットしない
3. **App Passwordの使用**: Gmailの実際のパスワードを使用しない
4. **HTTPS**: 常にHTTPS接続を使用
5. **レート制限**: サーバー負荷を避けるため遅延を設定

## 📊 データベーススキーマ

### `articles` テーブル

| カラム | 型 | 説明 |
|--------|------|-------------|
| id | INTEGER | 主キー |
| article_id | TEXT | 一意の記事識別子 |
| title | TEXT | 記事タイトル |
| url | TEXT | 記事URL |
| published_date | DATETIME | 公開日 |
| matched_keyword | TEXT | マッチしたキーワード |
| full_content | TEXT | 記事全文 |
| notified | BOOLEAN | 通知済みフラグ |
| created_at | DATETIME | 作成日時 |

### `monitoring_logs` テーブル

| カラム | 型 | 説明 |
|--------|------|-------------|
| id | INTEGER | 主キー |
| check_time | DATETIME | チェック時刻 |
| articles_found | INTEGER | 見つかった記事数 |
| new_articles | INTEGER | 新規記事数 |
| status | TEXT | ステータス |
| error_message | TEXT | エラーメッセージ |
| execution_time_seconds | REAL | 実行時間 |

## 🧪 テスト / Testing

### ユニットテストの実行

```bash
# すべてのテストを実行
pytest tests/

# 詳細出力付き
pytest tests/ -v

# カバレッジ付き
pytest tests/ --cov=src --cov-report=html
```

### 手動テスト

```bash
# 設定の確認
python -c "from src.config import Config; c = Config(); print(c.site_url)"

# データベースのテスト
python -c "from src.database import Database; db = Database(); print(db.get_article_count())"

# メール送信のテスト
python main.py --test-email
```

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### 1. ChromeDriverエラー

**問題**: `WebDriverException: chromedriver not found`

**解決策**:
```bash
# webdriver-managerが自動的にダウンロードします
# それでも問題がある場合:
pip install --upgrade webdriver-manager
```

#### 2. Gmail認証エラー

**問題**: `SMTPAuthenticationError: Username and Password not accepted`

**解決策**:
- Gmailアプリパスワードを使用していることを確認
- 2段階認証が有効になっていることを確認
- `EMAIL_PASSWORD` に実際のパスワードではなくアプリパスワードを使用

#### 3. スクレイピングエラー

**問題**: 記事が見つからない

**解決策**:
- サイト構造が変更された可能性があります
- `scraper.py` のセレクターを更新
- ヘッドレスモードを無効にしてデバッグ:
  ```yaml
  scraping:
    headless: false
  ```

#### 4. 日本語文字化け

**問題**: メールの日本語が文字化け

**解決策**:
- UTF-8エンコーディングが正しく設定されていることを確認
- ログファイルのエンコーディング:
  ```python
  # すでにnotifier.pyで設定済み
  MIMEText(text, 'plain', 'utf-8')
  ```

## 🚀 デプロイオプション / Deployment Options

このモニタリングシステムは、3つの主要な方法でデプロイできます。それぞれの特徴を理解して、あなたのニーズに最適な方法を選択してください。

### 🎯 デプロイ方法の比較

| 方法 | コスト | セットアップ時間 | メリット | デメリット | 推奨度 |
|------|--------|----------------|----------|-----------|--------|
| **ローカル実行** | 無料 | 5分 | ・即座に開始可能<br>・デバッグが容易<br>・完全なコントロール | ・PCを常時起動する必要<br>・電気代がかかる<br>・ネット接続が必須 | ⭐⭐ |
| **GitHub Actions** | 無料 | 10分 | ・完全無料 (Public repo)<br>・PCを切ってもOK<br>・自動実行<br>・クラウドで安定<br>・メンテナンス不要 | ・10分程度の初期設定<br>・月2000分の制限<br>・デバッグがやや困難 | ⭐⭐⭐⭐⭐ |
| **クラウドサーバー**<br>(AWS/GCP/Heroku) | $5-20/月 | 30-60分 | ・最も安定<br>・高度なカスタマイズ<br>・スケーラブル | ・月額費用がかかる<br>・サーバー管理が必要<br>・設定が複雑 | ⭐⭐⭐ |

### 💡 推奨デプロイ方法: GitHub Actions

**GitHub Actionsが最適な理由:**
- ✅ 完全無料（Public repositoryの場合）
- ✅ PCを切っても24/7自動実行
- ✅ 3時間ごとに自動チェック
- ✅ 設定はわずか10分
- ✅ GitHub Secretsで安全な資格情報管理
- ✅ メンテナンス不要

**📖 詳細な設定ガイド:**

GitHub Actionsを使った完全自動デプロイの詳細手順は、専用ガイドをご覧ください：

➡️ **[GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)** - 画像付き完全ガイド

このガイドには以下が含まれます：
- ステップバイステップのセットアップ手順
- GitHub Secretsの設定方法（7つのシークレット）
- Cronスケジュールのカスタマイズ方法
- トラブルシューティング（7つ以上の一般的な問題）
- コスト分析と月間実行時間の見積もり

---

### その他のデプロイオプション

GitHub Actions以外の方法で実行したい場合、以下のオプションもあります。

### 1. ローカル実行（Windows/Mac/Linux）

#### Option A: デーモンモード（継続実行）

```bash
# バックグラウンドで実行
python main.py --mode daemon
```

#### Option B: タスクスケジューラ / Cron

**Windows タスクスケジューラ:**
1. タスクスケジューラを開く
2. 「基本タスクの作成」をクリック
3. トリガー: 毎時
4. 操作: プログラムの起動
   - プログラム: `python.exe`
   - 引数: `C:\path\to\main.py --mode test`

**Linux/Mac Cronジョブ:**

```bash
# crontabを編集
crontab -e

# 1時間ごとに実行
0 * * * * cd /path/to/gomu-news-monitor && /usr/bin/python3 main.py --mode test >> /var/log/gomu-monitor.log 2>&1
```

### 2. Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Chrome インストール
RUN apt-get update && apt-get install -y \
    wget gnupg chromium chromium-driver

COPY . .

CMD ["python", "main.py", "--mode", "daemon"]
```

```bash
# ビルドと実行
docker build -t gomu-monitor .
docker run -d --name gomu-monitor \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  gomu-monitor
```

### 3. Heroku

```yaml
# Procfile
worker: python main.py --mode daemon
```

```bash
heroku create gomu-news-monitor
heroku config:set LOGIN_EMAIL=your@email.com
heroku config:set LOGIN_PASSWORD=yourpassword
# ... 他の環境変数も設定
git push heroku main
heroku ps:scale worker=1
```

### 4. AWS Lambda + EventBridge

Lambda関数として`main.py`をデプロイし、EventBridgeで定期実行をスケジュール。

## 📈 パフォーマンス最適化

### スクレイピング速度の改善

```yaml
scraping:
  headless: true                    # ヘッドレスモードで高速化
  delay_between_requests_min: 0.5   # 遅延を短縮（サイトポリシーを確認）
  max_pages_to_scrape: 3            # ページ数を制限
```

### データベースの最適化

```python
# 定期的にVACUUMを実行
sqlite3 data/articles.db "VACUUM;"

# インデックスの確認
sqlite3 data/articles.db ".schema articles"
```

### メモリ使用量の削減

```python
# バッチサイズを小さく
email:
  max_articles_per_email: 5
```

## 🔧 高度な機能

### カスタムセレクターの設定

サイト構造が変更された場合、`scraper.py`のセレクターを更新:

```python
# scraper.py の _extract_articles_from_page() メソッド
article_selectors = [
    'article.custom-class',  # カスタムセレクターを追加
    '.news-item',
    # ...
]
```

### 複数サイトのモニタリング

設定ファイルを複数作成:

```bash
python main.py --config config_site1.yaml --mode daemon &
python main.py --config config_site2.yaml --mode daemon &
```

### Webhook統合

`notifier.py`にWebhook送信機能を追加:

```python
import requests

def send_webhook(articles):
    webhook_url = "https://your-webhook-url.com"
    requests.post(webhook_url, json={'articles': articles})
```

## 📝 ログとモニタリング

### ログレベル

```yaml
logging:
  level: "DEBUG"   # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### ログの確認

```bash
# リアルタイムでログを表示
tail -f logs/monitor.log

# エラーのみ表示
grep ERROR logs/monitor.log

# 最新100行
tail -100 logs/monitor.log
```

### 統計の確認

```bash
# 過去7日間の統計
python main.py --stats --days 7

# 過去30日間
python main.py --stats --days 30
```

## 🤝 貢献 / Contributing

貢献を歓迎します！

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📜 ライセンス / License

このプロジェクトはMITライセンスの下でライセンスされています。

## ⚠️ 免責事項 / Disclaimer

このツールは教育目的で作成されました。使用する際は以下を遵守してください:

- 対象サイトの利用規約を確認
- 過度なリクエストを避ける（レート制限を設定）
- robots.txtを尊重
- 個人情報保護法を遵守

## 📞 サポート / Support

問題が発生した場合:

1. [Issues](https://github.com/yourusername/gomu-news-monitor/issues) を確認
2. 新しいIssueを作成
3. ログファイルを添付

## 🙏 謝辞 / Acknowledgments

- [Selenium](https://www.selenium.dev/) - ブラウザ自動化
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML解析
- [SQLite](https://www.sqlite.org/) - データベース

---

**Made with ❤️ for the rubber industry news monitoring**

**バージョン**: 1.0.0
**最終更新**: 2024年1月
**作者**: Gomu Monitor Team
