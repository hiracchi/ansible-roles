proxmox_gpu
===========

Proxmox VE ホストで GPU パススルーを構成するための Ansible ロールです。このロールは IOMMU を有効化し、VFIO ドライバを設定し、仮想マシンへの PCI GPU パススルーに必要なカーネルパラメータを設定します。AMD GPU と NVIDIA GPU の両方を扱えます。

前提条件
--------

- Debian 系システム（Proxmox VE）
- IOMMU をサポートする CPU
- AMD GPU または NVIDIA GPU
- BIOS/UEFI で IOMMU が有効になっていること
- `pve-headers` がインストール済みであること（このロールで必要に応じてインストールします）

ロール変数
----------

### デフォルト値（defaults/main.yml）

- `proxmox_gpu_enabled`（bool）: GPU パススルー設定を有効にするかどうか（デフォルト: `true`）
- `proxmox_gpu_vendor`（str）: パススルー対象 GPU ベンダ。`amd` または `nvidia`（デフォルト: `amd`）
- `proxmox_gpu_enable_iommu`（bool）: IOMMU サポートを有効にするかどうか（デフォルト: `true`）
- `proxmox_gpu_iommu_type`（str）: IOMMU の種類 - "amd" または "intel"（デフォルト: `amd`）
- `proxmox_gpu_pcie_acs_override`（bool）: マルチファンクションデバイス向けに PCIe ACS Override を有効にするかどうか（デフォルト: `true`）
- `proxmox_gpu_disable_vga`（bool）: VGA arbiter を無効にするかどうか（デフォルト: `true`）
- `proxmox_gpu_reset_method`（str）: GPU のリセット方式 - "bus"、"function"、"flr" のいずれか（デフォルト: `bus`）
- `proxmox_gpu_packages`（list）: インストールに必要なパッケージ
- `proxmox_gpu_vfio_modules`（list）: 読み込む VFIO モジュール
- `proxmox_gpu_blacklist_host_drivers`（bool）: ホスト側 GPU ドライバを blacklist するかどうか（デフォルト: `true`）

## セットアップ手順

### 事前準備

1. **BIOS/UEFI で IOMMU を有効にする:**
   - AMD の場合は BIOS 設定で "IOMMU" または "AMD-Vi" を有効にします
   - Intel の場合は BIOS 設定で VT-d を有効にします

2. **IOMMU サポートを確認する:**
   ```bash
   dmesg | grep -Ei 'iommu|amd-vi|vt-d'
   ```

3. **GPU デバイス ID を確認する:**
   ```bash
   lspci -nn | grep -Ei 'vga|3d|display'
   ```

### Playbook の例

```yaml
---
- hosts: proxmox_servers
   roles:
      - proxmox_gpu
```

### カスタム設定

```yaml
---
- hosts: proxmox_servers
   roles:
      - role: proxmox_gpu
         vars:
            proxmox_gpu_vendor: nvidia
            proxmox_gpu_iommu_type: intel
            proxmox_gpu_enabled: true
            proxmox_gpu_enable_iommu: true
            proxmox_gpu_pcie_acs_override: true
            proxmox_gpu_disable_vga: true
            proxmox_gpu_reset_method: "bus"
```

## 設定後の確認

このロールを実行した後は、次を確認します。

1. **IOMMU グループを確認する:**
   ```bash
   for d in /sys/kernel/iommu_groups/*/devices/*; do n=${d%/*}; n=${n##*/}; printf '[%s] ' "$n"; lspci -nns "${d##*/}"; done
   ```

2. **VFIO モジュールを確認する:**
   ```bash
   lsmod | grep vfio
   ```

   補足:
   現行の Proxmox VE で使われる新しいカーネルでは、`vfio_virqfd` を個別に読み込む必要は通常ありません。このロールでも `vfio`、`vfio_iommu_type1`、`vfio_pci` のみを対象にしており、`vfio_virqfd` は前提にしていません。

3. **GPU の認識状況を確認する:**
   ```bash
   lspci -k | grep -A 3 -B 3 -Ei 'Radeon|AMD GPU|NVIDIA'
   ```

4. **必要に応じてホスト側 GPU ドライバの blacklist を確認する:**
   ```bash
   cat /etc/modprobe.d/pve-blacklist.conf
   ```

   補足:
   このロールは、ベンダに応じてホスト側 GPU ドライバを blacklist できます。AMD の場合は `amdgpu` と `radeon`、NVIDIA の場合は `nouveau`、`nvidia`、`nvidiafb` を対象にします。ホストがその GPU で画面表示している場合は無効化してください。

## VM での GPU パススルー

ホストの設定が完了したら、Proxmox の CLI を使って GPU を VM にパススルーできます。

```bash
qm set <vmid> -hostpci0 <bus>:<slot>.<function>,x-vga=1
```

例:
```bash
qm set 100 -hostpci0 05:00.0,x-vga=1
```

GPU を 2 枚パススルーする場合:
```bash
qm set 100 -hostpci0 05:00.0 -hostpci1 06:00.0
```

## トラブルシューティング

### IOMMU が有効になっていない

カーネルで IOMMU が有効か確認します。
```bash
cat /proc/cmdline | grep -Eo 'amd_iommu=on|intel_iommu=on'
```

表示されない場合は、BIOS 設定を確認して再起動してください。

### GPU が VFIO から見えていない

1. GPU のデバイスパスを確認します。
   ```bash
   lspci -nn | grep -i gpu
   ```

2. VFIO-PCI ドライバのバインドを確認します。
   ```bash
   lspci -k | grep -A 3 -B 3 -Ei "Radeon|AMD GPU|NVIDIA"
   ```

3. カーネルパラメータを確認します。
   ```bash
   cat /proc/cmdline
   ```

### 再起動が必要

このロールを初めて実行した後は、カーネルパラメータの変更を反映するためにシステムの再起動が必要です。
```bash
systemctl reboot
```

## 参考資料

- [Proxmox PCI Passthrough](https://pve.proxmox.com/wiki/PCI_Passthrough)
- [IOMMU Configuration](https://pve.proxmox.com/wiki/Pci_passthrough#IOMMU_Mapping)
- [VFIO Documentation](https://www.kernel.org/doc/html/latest/driver-api/vfio.html)
- [AMD GPU Passthrough Guide](https://github.com/joeknock90/Single-GPU-Passthrough)

制約
----

- ロール名は `proxmox_gpu` です。設定変数 `proxmox_gpu_vendor` で AMD/NVIDIA を切り替えられます。
- ホスト OS が利用中の primary GPU をそのまま blacklist すると、ホストのローカル表示が失われる可能性があります。
- より確実に運用するには、blacklist だけでなく PCI ID ベースの `vfio-pci` バインド設定も併用してください。

ライセンス
--------

MIT-0（MIT No Attribution）

作者情報
--------

Proxmox VE 向け GPU パススルー用に作成
