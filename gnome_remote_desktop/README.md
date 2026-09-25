# Ansible Role: gnome_remote_desktop

Ubuntu 24.04 / 26.04 向けのシステムレベル GNOME Remote Desktop（RDP）セットアップロールです。
ログイン画面（GDM3）からリモート接続可能なヘッドレス RDP サービスを構築します。

## 機能

- `gnome-remote-desktop` パッケージのインストール
- RDP 通信用の自己署名 TLS 証明書の自動生成
- `grdctl --system` による RDP 有効化および認証情報設定
- `gnome-remote-desktop.service`（system サービス）の有効化・自動起動
- UFW ファイアウォールでのポート（3389/tcp）開放

## 必要条件

- Ubuntu 24.04 (Noble) または 26.04 (Resolute)
- GNOME デスクトップ環境および GDM3 がインストールされていること

## ロール変数

| 変数名 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `gnome_remote_desktop_port` | `3389` | RDP 接続ポート |
| `gnome_remote_desktop_user` | `{{ gnome_remote_desktop_username \| default('toshi') }}` | RDP 接続用ユーザー名 |
| `gnome_remote_desktop_pass` | `{{ gnome_remote_desktop_password \| default('') }}` | RDP 接続用パスワード（Vault 推奨） |
| `gnome_remote_desktop_ufw_enabled` | `true` | UFW でポートを開放するか |
| `gnome_remote_desktop_ufw_from_ip` | `"any"` | 接続を許可する送信元 IP |

## 使用例

```yaml
- hosts: desktops
  roles:
    - role: gnome_remote_desktop
      vars:
        gnome_remote_desktop_user: "toshi"
        gnome_remote_desktop_pass: "{{ vault_rdp_password }}"
```

## クライアントからの接続方法

- **Mac**: App Store の「Windows App（旧 Microsoft Remote Desktop）」等を使用
  - PC name: `<IP_ADDRESS>:3389`
  - User account: 設定した `gnome_remote_desktop_user` と `gnome_remote_desktop_pass`
- **Windows**: 標準の「リモート デスクトップ接続」を使用

## ライセンス

MIT
