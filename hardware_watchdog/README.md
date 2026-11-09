# description

チップセットに内蔵されたハードウェア watchdog を有効にし、カーネルが完全に止まったときに自動で再起動させます。

- `sp5100_tco` モジュールを読み込みます。起動時の読み込みは、`hardware-watchdog-module.service`(`modprobe` を実行する oneshot の unit)で行います。
  Ubuntu のカーネルパッケージが `sp5100_tco` を blacklist に入れているため、`/etc/modules-load.d/` への記載は
  `systemd-modules-load` に拒否されて効きません(`Module 'sp5100_tco' is deny-listed (by kmod)`)。
  明示的な `modprobe` は blacklist を無視します。
- systemd が `RuntimeWatchdogSec` の間隔で watchdog を叩きます。叩けなくなると、ハードウェアが再起動します。
- `/dev/watchdog0` が無い場合は失敗させます(BIOS で無効化されている可能性があります)。

対象は AMD FCH(SB800 以降)のチップセットです。Intel のボードでは、`iTCO_wdt` などに変えてください。

# variables

```
hardware_watchdog_module: sp5100_tco
hardware_watchdog_timeout_sec: 60
```

# remarks

- watchdog は再起動させるだけで、原因は特定できません。再起動の記録は `journalctl --list-boots` で確認します。
- `systemd` の設定を変えるため、適用時に `systemctl daemon-reexec` を実行します。
- 再起動後に有効かどうかは、`ls /dev/watchdog0`、`wdctl`、`journalctl -b | grep -i watchdog` で確認します。
  `Failed to open any watchdog device` が出ていれば、起動時の読み込みが間に合っていません。
