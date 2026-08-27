chrony role
=============

このロールは Chrony をインストールし、`/etc/chrony.conf` または `/etc/chrony/chrony.conf` / `/etc/chrony/conf.d/` などの環境に適した場所に設定をデプロイします。
また、Ubuntu/Debian 等で競合する `systemd-timesyncd` の自動停止・無効化にも対応しています。

主な変数（defaults/main.yml）
------------------------------

- `chrony_manage_package`: `true`
  - パッケージ管理の有無
- `chrony_package_name`: `chrony`
  - インストールするパッケージ名
- `chrony_service_name`: `chronyd`
  - サービス名（Debian/Ubuntu 環境では自動的に `chrony` が適用されます）
- `chrony_disable_timesyncd`: `true`
  - `systemd-timesyncd` サービスを停止・無効化して時刻同期の競合を防止
- `chrony_ntp_servers`: (list)
  - NTP サーバーのリスト。各行はそのまま `server ...` として設定に挿入されます。
  - 例: `["0.pool.ntp.org iburst", "1.pool.ntp.org iburst"]`
- `chrony_sourcedirs`: (list)
  - 追加設定ディレクトリの読み込み指定（例: `["/run/chrony-dhcp", "/etc/chrony/sources.d"]`）
- `chrony_driftfile`: `/var/lib/chrony/drift`
- `chrony_makestep`: `"1.0 3"`
- `chrony_allow_networks`: `[]`
  - このホストを NTP サーバーとして公開する場合に許可するネットワークを指定（例: `["192.168.0.0/24"]`）。
- `chrony_local_stratum`: `10`
- `chrony_logdir`: `/var/log/chrony`
- `chrony_log_tracking`: `false`
- `chrony_enable_rtc_sync`: `true`
- `chrony_conf_dest`: `/etc/chrony.conf`
  - 生成する設定ファイルのフルパス（環境内の `/etc/chrony/conf.d` や `/etc/chrony/chrony.conf` の存在に応じて自動判別されます）。
- `chrony_conf_d_filename`: `chrony-ansible.conf`

使い方（playbook の一例）:
---------------------------

```yaml
- hosts: all
  become: yes
  roles:
    - role: chrony
      vars:
        chrony_ntp_servers:
          - "ntp.nict.jp iburst"
          - "0.jp.pool.ntp.org iburst"
        chrony_allow_networks:
          - "192.168.1.0/24"
```

推奨追加設定 / 注意点
---------------------

- **競合防止**: Ubuntu/Debian などで `systemd-timesyncd` が動いている場合は `chrony_disable_timesyncd: true` により自動停止されます。
- **セキュリティ**: NTP サーバーとして公開する場合は `chrony_allow_networks` を使ってアクセス元を限定してください。
- **監視**: chrony の同期状態を監視（`chronyc tracking` / `chronyc sources`）すると問題検知が早くなります。
- **iburst オプション**: サーバー定義に `iburst` を付けると初回同期が高速化されます。