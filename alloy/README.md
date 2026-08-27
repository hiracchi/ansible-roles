# alloy ロール

クラスタノードに **Grafana Alloy**（次世代テレメトリコレクター）を導入し、OSメトリクス（Node Exporter 互換）およびシステムログ・Slurmログを収集・転送する Ansible ロールです。

## 主な機能
- Grafana 公式 APT リポジトリからの `alloy` パッケージの導入
- **メトリクス収集:** `prometheus.exporter.unix` による OS リソース収集と Prometheus (`/api/v1/write`) への Remote Write
- **ログ収集:** Systemd Journald ログおよび `/var/log/*.log`、Slurm ログの収集と Grafana Loki (`/loki/api/v1/push`) への転送
- systemd によるサービス自動起動管理

## 主な変数 (`defaults/main.yml`)
| 変数名 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `alloy_prometheus_url` | `http://10.71.33.194:9090/api/v1/write` | Prometheus Remote Write エンドポイント |
| `alloy_loki_url` | `http://10.71.33.194:3100/loki/api/v1/push` | Grafana Loki Push エンドポイント |
| `alloy_collect_journal` | `true` | Systemd Journald ログ収集の有効化 |
| `alloy_collect_var_logs` | `true` | `/var/log` ファイルログ収集の有効化 |
| `alloy_collect_slurm_logs` | `true` | Slurm ログ収集の有効化 |
