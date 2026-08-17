# promtail Role

Promtail は Grafana Loki 用のログ収集エージェントです。本 Role は対象ノードの syslog、`/var/log/*.log`、および `systemd-journal` ログを収集し、中央の Loki サーバーへ送信します。

---

## 役割

- Promtail バイナリのダウンロード・配置
- 収集設定（`/var/log/*.log` および `journald` ログ）の生成
- 中央 Loki サーバーのアドレス指定
- systemd サービス（`promtail`）の有効化・起動

---

## 主な変数 (`defaults/main.yml`)

| 変数名 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `promtail_version` | `"2.9.8"` | インストールする Promtail のバージョン |
| `promtail_loki_url` | `"http://10.79.1.51:3100/loki/api/v1/push"` | 送信先 Loki サーバーの Push API URL |
| `promtail_user` | `"promtail"` | 実行ユーザー名 |
| `promtail_group` | `"promtail"` | 実行グループ名 |

---

## Playbook での使用例

```yaml
- name: Setup Promtail
  hosts: ubuntu2604_sudows
  become: true
  roles:
    - role: promtail
      vars:
        promtail_loki_url: "http://10.79.1.51:3100/loki/api/v1/push"
```
