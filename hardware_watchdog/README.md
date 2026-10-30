# description

チップセットに内蔵されたハードウェア watchdog を有効にし、カーネルが完全に止まったときに自動で再起動させます。

- `sp5100_tco` モジュールを読み込み、`/etc/modules-load.d/` で起動時にも読み込みます。
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
