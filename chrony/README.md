chrony role
=============

このロールは Chrony をインストールし、/etc/chrony.conf または適切な conf.d フォルダにテンプレートをデプロイします。

主な変数（defaults/main.yml）

- chrony_manage_package: true
  - パッケージ管理の有無
- chrony_package_name: chrony
  - インストールするパッケージ名（ディストリによって変更してください）
- chrony_service_name: chronyd
  - サービス名。必要に応じて "chrony" に変更してください。
- chrony_ntp_servers: (list)
  - NTP サーバーのリスト。各行はそのまま `server ...` として config に挿入されます。
  - 例: ["0.pool.ntp.org iburst", "1.pool.ntp.org iburst"]
- chrony_driftfile: /var/lib/chrony/drift
- chrony_makestep: "1.0 3"
- chrony_allow_networks: []
  - このホストを NTP サーバーとして公開する場合に許可するネットワークを指定（例: ["192.168.0.0/24"])。
- chrony_local_stratum: 10
- chrony_logdir, chrony_log_tracking, chrony_enable_rtc_sync
- chrony_conf_dest: /etc/chrony.conf
  - 生成する設定ファイルのフルパス。Ubuntu 26.04+ のように断片ファイルを使うディストリでは `/etc/chrony/conf.d/<filename>` を指定してください。

使い方（playbook の一例）:

- hosts: time_servers
  roles:
    - role: hirano-lab.chrony
      vars:
        chrony_ntp_servers:
          - "0.jp.pool.ntp.org iburst"
          - "1.jp.pool.ntp.org iburst"
        chrony_allow_networks:
          - "10.0.0.0/8"
        chrony_service_name: chrony

注意: Ubuntu 26.04 などの新しいバージョンでは、Chrony のメイン設定ファイルとして `/etc/chrony/conf.d/` に断片ファイルを置く必要があります。
このロールはデフォルトで `/etc/chrony.conf` を使いますが、実行時に自動的に検出して Ubuntu 26.04 以上の場合は `/etc/chrony/conf.d/chrony-ansible.conf` を配置します。
必要なら playbook 側で `chrony_conf_dest` を明示的に上書きしてください。

推奨追加設定 / 注意点

- OS によってパッケージ名・サービス名が異なるため、必要に応じて playbook 側で変数を上書きしてください。
- セキュリティ: NTP サーバーとして公開する場合は `chrony_allow_networks` を使ってアクセス元を限定してください。
- 監視: chrony の同期状態を監視（chronyc tracking / sources）すると問題検知が早くなります。
- iburst オプション: サーバー定義に `iburst` を付けると初回同期が高速化されます。
- 大規模展開: 内部 NTP サーバーを立てる場合は階層（stratum）設計を検討してください。