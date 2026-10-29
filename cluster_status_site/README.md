# description

Prometheus の値から静的なクラスタ状態ページを作り、LAN 内に配信します。
ブラウザで開くだけで、各ホストの稼働状態・ロードアベレージ・メモリ使用量・ディスクの空き容量・スペックを確認できます。

- **生成**: `generate.py` が `cluster_status_site_interval` 秒(既定 60 秒)ごとに Prometheus の HTTP API から値を取り、静的な `index.html` を書き出す(標準ライブラリのみ)。
- **配信**: nginx コンテナが、生成された `index.html` を `cluster_status_site_bind_ip:cluster_status_site_port` で配信する。
- **構成**: docker compose で 2 つのコンテナ(generator、web)を動かし、共有ボリューム `site` でつなぐ。

# variables

```
cluster_status_site_dir: /opt/cluster-status
cluster_status_site_bind_ip: "{{ ansible_host }}"   # LAN の IP に限定する
cluster_status_site_port: 8080
cluster_status_site_prometheus_url: "http://{{ cluster_status_site_bind_ip }}:9090"
cluster_status_site_interval: 60
cluster_status_site_cluster_name: "JARVIS"
```

# remarks

- Prometheus のラベル(`instance`、`job="node_exporter"`)は alloy の設定に合わせています。
- 直近 30 日に一度も報告がないホストは表示しません。一度でも報告したホストは、停止中なら「停止」、報告がなければ「報告なし」と表示します。
- Prometheus に接続できないときは、エラーを表示したページに置き換えます。
- Docker が公開するポートは ufw を通らないため、バインド先を LAN の IP に限定しています。
- NAS など、node_exporter を動かしていない機器は表示対象外です。
- CPU のモデル名は node_exporter の既定の項目に含まれないため、表示していません。
