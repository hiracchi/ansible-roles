# ubuntu_base

Ubuntu サーバーの基盤環境（システムパラメータ調整、リソース制限、クラッシュダンプ設定、基本ツール・シェル・言語環境、自動セキュリティアップデート）を一括セットアップする Ansible ロールです。

## 対象 OS
- Ubuntu (`ansible_facts['distribution'] == 'Ubuntu'`)

## 主な機能・設定内容

1. **システム & カーネルパラメータ**
   - **シャットダウンタイムアウトの短縮**: `DefaultTimeoutStopSec=10s`（systemd の終了待ち時間を短縮）
   - **リソース制限 (limits.conf)**: memlock 制限値の調整
   - **Apport / コアダンプ設定**: Apport 自動クラッシュレポートの無効化およびコアダンプ出力形式の設定 (`/etc/sysctl.d/90-core-dump.conf`)
   - **デバッグ (ptrace)**: `kernel.yama.ptrace_scope = 0` に設定してプロセスへのアタッチを許可
   - **ファイル監視数**: `fs.inotify.max_user_watches` を拡張し、VS Code や開発ツールの監視エラーを防止 (`/etc/sysctl.d/60-max-user-watches.conf`)

2. **シェル環境**
   - 主要シェルのインストール (`bash`, `zsh`, `tcsh`, `ksh`, `fish`)
   - `/bin/sh` の参照先を `dash` から `bash` に切り替え

3. **基本ツール群**
   - システム管理・ユーティリティツールの導入 (`vim`, `wget`, `curl`, `openssl`, `jq`, `direnv`, `unzip`, `pv`, `pigz`, `smartmontools`, `lsof`, `neofetch` 等)

4. **ランタイム・開発言語**
   - Python 3 (`python3`, `python3-pip`, `python3-venv`)
   - Ruby (`ruby`)

5. **自動セキュリティアップデート (unattended-upgrades)**
   - `unattended-upgrades` によるセキュリティアップデートおよびパッケージリスト更新の自動化 (`/etc/apt/apt.conf.d/20auto-upgrades`)
   - トグル変数により有効/無効の切り替えが可能

## 主な変数 (`defaults/main.yml`)

| 変数名 | デフォルト値 | 説明 |
|---|---|---|
| `ubuntu_base_enable_unattended_upgrades` | `true` | 自動セキュリティアップデート機能の有効/無効 |
| `ubuntu_base_unattended_upgrades_update_package_lists` | `"1"` | パッケージリスト更新の間隔（日数） |
| `ubuntu_base_unattended_upgrades_unattended_upgrade` | `"1"` | セキュリティアップデート自動適用の間隔（日数） |
| `limits` | *(リスト定義)* | `/etc/security/limits.conf` に設定するリソース制限 |
| `ntp_servers` | *(リスト定義)* | NTP サーバー一覧 |

## 使い方

### 通常の利用（自動アップデート有効）

```yaml
- hosts: ubuntu_servers
  become: yes
  roles:
    - role: ubuntu_base
```

### 自動アップデートを無効化する場合

検証環境や本番環境で勝手なパッケージ更新を避けたい場合は、トグル変数を `false` に設定します。

```yaml
- hosts: ubuntu_servers
  become: yes
  roles:
    - role: ubuntu_base
      vars:
        ubuntu_base_enable_unattended_upgrades: false
```
