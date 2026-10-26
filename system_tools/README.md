# description

非常用・トラブル対応用ターミナルに、障害調査で使うツールを導入します。

- 接続・作業用: tmux、screen、rsync
- ネットワーク調査用: bind9-dnsutils(dig など)、mtr-tiny、nmap、iperf3、tcpdump
- システム調査用: htop、ncdu、lsof

# variables

```
vars:
  system_tools_packages:   # 導入するパッケージ一覧(defaults/main.yml)
    - tmux
    - ...
```

# remarks

- NIS や NFS に依存しない、ローカルで完結する構成を想定しています。
- `ipmitool` は IPMI を搭載したホストだけで使うため、このロールには含めていません。
