# uptime_kuma

[Uptime Kuma](https://github.com/louislam/uptime-kuma) (v2) を Docker Compose で起動するロールです。
ホストの死活監視（ping / TCP / HTTP）と通知を、Prometheus とは別の仕組みで行うために使います。

## 前提

- 対象ホストに Docker と `docker compose` が導入されていること（`docker` ロール）。

## 変数

| 変数 | 既定値 | 説明 |
| :--- | :--- | :--- |
| `uptime_kuma_dir` | `/opt/uptime-kuma` | 配置先ディレクトリ |
| `uptime_kuma_user` | `ansible_user` | 実行ユーザー（`docker compose` の実行と所有者） |
| `uptime_kuma_group` | `uptime_kuma_user` と同じ | 所有グループ |
| `uptime_kuma_image` | `louislam/uptime-kuma:2.5.6` | イメージ（バージョンを固定する） |
| `uptime_kuma_port` | `3001` | Web UI のポート |

## 初期設定（Ansible では自動化されない部分）

1. `http://<ホスト>:<uptime_kuma_port>` を開き、管理者アカウントを作成する。
2. 監視項目（ホストごとの ping / TCP 22 など）と通知先を Web UI から追加する。

ファイアウォール（ufw）でポートを開ける必要がある場合は、利用側の `group_vars` の `ufw_rules` に追加する。

## データ

- 設定と監視履歴は `{{ uptime_kuma_dir }}/data` に保存される（SQLite）。バックアップはこのディレクトリを対象にする。

## 日常運用（ホスト上）

```bash
cd /opt/uptime-kuma
docker compose ps
docker compose logs -f
docker compose pull && docker compose up -d   # イメージを更新する場合（先に uptime_kuma_image を更新）
```
