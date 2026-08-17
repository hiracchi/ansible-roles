# node_exporter Role

Node Exporter は Prometheus 用の公式ハードウェア・OSメトリクス収集エージェントです。本 Role は対象ノードに Node Exporter のバイナリをセットアップし、systemd サービスとして動かします。

---

## 役割

- 指定バージョンの Node Exporter バイナリを GitHub からダウンロード・配置
- 専用ユーザー `node_exporter` の作成
- systemd サービスファイルの生成・有効化・起動 (デフォルトポート: `9100`)

---

## 主な変数 (`defaults/main.yml`)

| 変数名 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `node_exporter_version` | `"1.8.2"` | インストールする Node Exporter のバージョン |
| `node_exporter_port` | `9100` | Node Exporter がリッスンするポート番号 |
| `node_exporter_user` | `"node_exporter"` | 実行ユーザー名 |
| `node_exporter_group` | `"node_exporter"` | 実行グループ名 |

---

## Playbook での使用例

```yaml
- name: Setup node_exporter
  hosts: ubuntu2604_sudows
  become: true
  roles:
    - role: node_exporter
      vars:
        node_exporter_port: 9100
```
