# orca_headless

[Orca](https://www.onorca.dev/) を Linux サーバー上でヘッドレス（`orca serve`）モードとして動作させ、systemd サービスとして自動管理するための Ansible ロールです。

公式ドキュメント: [Headless Linux Server (GitHub)](https://github.com/stablyai/orca/blob/main/docs/reference/headless-linux-server.md)

## 特徴・仕様

- **Electron 依存関係のバージョン自動判別**: Ubuntu 24.04+ / Debian 13+ の 64-bit `time_t` 移行（`t64` パッケージ）と、従来の Ubuntu 20.04/22.04 / Debian 12 のパッケージ差異を自動吸収します。
- **セキュリティ**: root 権限ではなく専用のシステムユーザー（デフォルト: `orca`）で動作させ、Chromium サンドボックスを有効に維持します。
- **セッション保護 (systemd lingering)**: `loginctl enable-linger` を有効化することで、Orca のバックグラウンドターミナルデーモン（PTYセッション）が独立した systemd ユーザースコープで保護され、サービス再起動時にもプロセスが生存します。
- **適切な終了シグナル**: `KillMode=mixed` を指定し、Orca が所有する仮想ディスプレイ（Xvfb）を正常終了させます。

## 要件

- 対象 OS:
  - Ubuntu 20.04 (Focal), 22.04 (Jammy), 24.04 (Noble) 以降
  - Debian 12 (Bookworm), Debian 13 (Trixie) 以降
- 特権昇格 (`become: true`) が必要です。

## ロール変数

`defaults/main.yml` で定義されている主な変数です:

| 変数名 | デフォルト値 | 説明 |
|---|---|---|
| `orca_version` | `"latest"` | Orca のバージョン |
| `orca_appimage_url` | `"https://github.com/stablyai/orca/releases/latest/download/orca-linux.AppImage"` | ダウンロード先 URL |
| `orca_install_dir` | `"/opt/orca"` | AppImage のインストール先ディレクトリ |
| `orca_bin_name` | `"orca-linux.AppImage"` | 配置バイナリ名 |
| `orca_user` | `"orca"` | サービス実行システムユーザー |
| `orca_group` | `"orca"` | サービス実行グループ |
| `orca_home` | `"/home/orca"` | 実行ユーザーのホームディレクトリ |
| `orca_enable_linger` | `true` | `loginctl enable-linger` を有効にするか |
| `orca_port` | `6768` | WebSocket リスナーのポート番号 |
| `orca_pairing_address` | `""` | クライアントに通知するペアリング用アドレス（LAN IP / Tailscale IP / ドメイン等）。空文字の場合はオプションを渡しません |
| `orca_service_enabled` | `true` | サービスを自動起動にするか |
| `orca_service_state` | `"started"` | サービスの実行状態 (`started` / `stopped`) |

## Playbook の使用例

### 基本例

```yaml
- hosts: servers
  become: true
  roles:
    - role: orca_headless
```

### Tailscale IP やホスト名を指定する例

```yaml
- hosts: servers
  become: true
  roles:
    - role: orca_headless
      vars:
        orca_pairing_address: "100.64.1.20"
        orca_port: 6768
```

## ペアリング URL の確認

本ロールでは、サーバーのステータスや最新のペアリング URL を手軽に確認できるヘルパースクリプト **`orca-pairing-info`**（`/usr/local/bin/orca-pairing-info`）を自動インストールします。

### ヘルパースクリプトの利用（推奨）

```bash
# 全ステータス & ペアリング URL を整形表示
orca-pairing-info

# アプリ用 Pairing URL のみを出力（クリップボード等に渡す場合）
orca-pairing-info --url

# ブラウザ用 Web Client URL のみを出力
orca-pairing-info --web

# QR コードを表示（qrencode がインストールされている場合）
orca-pairing-info --qr
```

### 手動でログから確認する場合

```bash
# ペアリング情報（URL や QR コード等）を含む準備完了ログを表示
sudo journalctl -u orca-serve.service -o cat | jq -Rrc 'fromjson? | select(.type == "orca_server_ready")'

# 直近のログから Pairing URL を抽出
sudo journalctl -u orca-serve.service -o cat | grep -E 'Pairing URL|Web client URL' | tail -n 2
```

## ライセンス

MIT
