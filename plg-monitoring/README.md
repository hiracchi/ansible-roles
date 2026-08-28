# plg-monitoring ロール

`jarvis-prxvm-docker-01` などの Docker ホスト上に、[docker-plg-monitoring](https://github.com/hiracchi/docker-plg-monitoring) をベースにした PLG 監視スタック（Prometheus + Loki + Grafana）をデプロイ・管理する Ansible ロールです。

## 主な機能
- `/opt/plg-monitoring` への Docker Compose 環境の配置（所有者: `toshi:hirano-lab`）
- Prometheus, Loki, Grafana のコンテナ自動起動およびデータ永続化 (`/opt/plg-monitoring/data`)
- Prometheus 監視ターゲット（クラスタノードの `node_exporter`, `nvidia_gpu_exporter`）の自動構成
- Grafana のデータソースおよび標準ダッシュボード自動読み込み
- 管理用ヘルパー `Makefile` の配置

## 主な変数 (`defaults/main.yml`)

| 変数名                                 | デフォルト値          | 説明                                 |
| :------------------------------------- | :-------------------- | :----------------------------------- |
| `plg_monitoring_dir`                   | `/opt/plg-monitoring` | デプロイ先ディレクトリ               |
| `plg_monitoring_user`                  | `toshi`               | 実行ユーザー                         |
| `plg_monitoring_group`                 | `hirano-lab`          | 所有グループ                         |
| `plg_monitoring_grafana_port`          | `3000`                | Grafana Web UI ポート                |
| `plg_monitoring_prometheus_port`       | `9090`                | Prometheus ポート                    |
| `plg_monitoring_loki_port`             | `3100`                | Grafana Loki ポート                  |
| `plg_monitoring_node_exporter_targets` | 各ノードのリスト      | 監視対象 node_exporter アドレス一覧  |

## 日常運用コマンド (ホスト上での操作)

`toshi` ユーザーでホストに SSH ログイン後、以下のコマンドで操作できます。

```bash
cd /opt/plg-monitoring

make status   # コンテナのステータス確認
make logs     # ログの追跡表示
make start    # 起動
make stop     # 停止
make restart  # 再起動
```

## アラート・通知機能の設定方法

本ロールでは、Grafana Unified Alerting による自動監視および複数チャネル（Discord / Gmail / Slack / Webhook）への通知が可能です。

### 1. Discord Webhook URL の取得方法
1. Discord で通知を受け取りたいテキストチャンネル（例: `#server-alerts`）の **歯車アイコン（チャンネルの編集）** を開く。
2. 左メニューの **「連携サービス」** → **「ウェブフック」**（または「ウェブフックを作成」）を選択。
3. ボット名（例: `Grafana Alerts`）を設定し、**「ウェブフック URL をコピー」** をクリック。
   - コピーされる URL 形式: `https://discord.com/api/webhooks/1234567890/abcdef...`

### 2. Gmail 送信（SMTP）の設定準備
1. 送信元とする Google アカウントで [Google セキュリティ設定](https://myaccount.google.com/security) を開く。
2. **2 段階認証** を有効にし、**「アプリ パスワード」** を新規発行（16文字の英数字）。

### 3. Playbook での設定例 (`group_vars/all.yml`)
```yaml
# アラート機能の有効化
plg_monitoring_alerts_enabled: true

# （任意）Gmail 送信元設定
plg_monitoring_smtp_enabled: true
plg_monitoring_smtp_user: "your-lab@gmail.com"
plg_monitoring_smtp_password: "abcd efgh ijkl mnop" # 16文字のアプリパスワード

# 複数通知先リスト
plg_monitoring_alert_receivers:
  - name: "Discord Alerts"
    type: "discord"
    url: "https://discord.com/api/webhooks/1234567890/xxxxxxxxx"
  - name: "Admin Email"
    type: "email"
    addresses:
      - "admin@example.com"
```

## 今後の拡張予定 (TODO: アラート・通知機能)

> [!NOTE]
> 段階的な実装手順や検証計画の詳細は [実装計画書 (ALERTING_PLAN.md)](./ALERTING_PLAN.md) をご参照ください。

- [x] **Grafana Alerting による自動監視・通知機能の実装**
  - [x] **ホスト死活監視**: `up == 0`（2分間継続で Critical 通知）および復旧（Resolved）通知
  - [x] **リソース枯渇監視**: ディスク空き容量 10% 未満、高CPU負荷（90%以上）
  - [x] **GPU 異常検知**: GPU 温度異常（85℃以上）、VRAM 枯渇、GPU 認識外れ
  - [x] **ログベース障害検知**: Loki による OOM Killer（`Out of memory`）発生検知
  - [ ] **NFS マウント監視**: `/mnt/nfs1` などのマウント外れ検知 (将来拡張)
- [x] **複数通知先（マルチレシーバー）対応**
  - [x] **Discord 連携**: 指定テキストチャンネルへの Webhook 埋め込みカード通知・メンション機能
  - [x] **Gmail / SMTP 連携**: `smtp.gmail.com:587`（アプリパスワード）経由での管理者宛て同報メール送信
  - [x] **Slack / 汎用 Webhook 連携**
- [x] **データ保持期間（Retention）の自動管理**
  - [x] Prometheus TSDB 保持期間設定 (`--storage.tsdb.retention.time=30d`)
  - [x] Loki ログ保持期間設定 (`retention_period: 30d`)
