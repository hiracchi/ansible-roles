# description

物理ホストで温度・電圧・ファンなどのハードウェア状態を確認するためのツールを導入します。

- `lm-sensors`(`sensors` コマンド)を全ホストに導入します。
- `ipmitool` は IPMI(BMC)のデバイスが存在するホストだけに導入します。

# variables

```
hardware_monitoring_packages: [lm-sensors]
hardware_monitoring_ipmi_packages: [ipmitool]
hardware_monitoring_ipmi_devices: [/dev/ipmi0, /dev/ipmi/0, /dev/ipmidev/0]
```

# remarks

- `sensors-detect` は対話式のため実行しません。センサーが認識されない場合は手動で実行してください。
- 仮想マシンでは `lm-sensors` の出力がほぼ空になることがあります(異常ではありません)。
- 温度などを Alloy から収集する設定は、このロールには含めていません。
