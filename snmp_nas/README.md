# description

NAS(Synology・ReadyNAS など)の SNMP を `snmp_exporter` で取得し、ボリュームの容量を Prometheus に入れます。

- `prom/snmp-exporter` を docker compose で起動します。
- 取得するのは hrStorageTable(`/volume1` などの容量と使用量)です。
- Prometheus の scrape 設定は `plg_monitoring` の `prometheus.yml.j2` にあります。このロールと同じ変数を参照します。

# variables

```
snmp_nas_community: ""          # 読み取り専用の SNMP v2c コミュニティ(host_vars で ansible-vault 暗号化)
snmp_nas_targets:
  - name: jarvis-ds1817-1       # instance ラベル
    ip: 10.71.99.221
snmp_nas_port: 9116             # exporter を公開するポート(docker ホストの全インターフェース)
```

# remarks

- コミュニティ文字列は `snmp.yml`(権限 0600)に入ります。チャットやリポジトリに平文で書かないでください。
- ポート 9116 は docker の経路で ufw を回り込みます。LAN 以外からも届く可能性があります。
- NAS 側で SNMP(v2c、読み取り専用)を有効にしておく必要があります。
