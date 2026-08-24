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
