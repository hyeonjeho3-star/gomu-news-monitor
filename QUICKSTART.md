# 🚀 クイックスタートガイド / Quick Start Guide

このガイドでは、5分で Gomu News Monitor を起動する方法を説明します。

## ステップ 1: インストール

```bash
# 依存関係をインストール
pip install -r requirements.txt
```

## ステップ 2: 環境変数の設定

```bash
# .env ファイルを作成
cp .env.example .env
```

`.env` ファイルを編集して以下を入力:

```ini
# 必須項目
LOGIN_EMAIL=your_gomuhouchi_email@example.com
LOGIN_PASSWORD=your_gomuhouchi_password

EMAIL_FROM=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_TO=recipient@example.com
```

### Gmail App Password の取得方法

1. [Google アカウント](https://myaccount.google.com/) → セキュリティ
2. 2段階認証を有効化
3. 「アプリパスワード」を生成
4. 生成されたパスワードを `EMAIL_PASSWORD` に設定

## ステップ 3: テスト実行

### メール設定をテスト

```bash
python main.py --test-email
```

メールが届いたら設定成功！

### 実際にスクレイピングをテスト

```bash
python main.py --mode test
```

## ステップ 4: 継続的モニタリング

```bash
# バックグラウンドで実行（デーモンモード）
python main.py --mode daemon
```

Ctrl+C で停止できます。

## トラブルシューティング

### ChromeDriver エラー

```bash
pip install --upgrade webdriver-manager
```

### Gmail 認証エラー

- Gmail App Password（アプリパスワード）を使用していますか？
- 2段階認証は有効ですか？

### 日本語が文字化け

- すでにUTF-8対応済みですが、それでも問題がある場合は Issue を報告してください。

## 次のステップ

- `config.yaml` でキーワードをカスタマイズ
- チェック間隔を調整
- 統計を確認: `python main.py --stats`

詳細は [README.md](README.md) を参照してください。

---

**問題がありますか？** → [Issues](https://github.com/yourusername/gomu-news-monitor/issues)
