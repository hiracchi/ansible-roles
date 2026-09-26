# git_credential_manager ロール

Ubuntu/Debian 系ホスト向けに [Git Credential Manager (GCM)](https://github.com/git-ecosystem/git-credential-manager) を公式 GitHub Releases からダウンロード・インストールし、システム全体の Git 認証ヘルパーとして設定する Ansible ロールです。

## 主な機能

1. **前提パッケージの導入**: `curl`, `git`, `libsecret-1-0` をインストール
2. **アーキテクチャの自動判別**: `x86_64` (x64) および `aarch64` (arm64) を自動判定
3. **冪等なインストール**: 既に指定バージョンの GCM がインストールされている場合はダウンロード・再インストールをスキップ
4. **システムワイド設定**: `git-credential-manager configure` を実行し、システム全体 (`/etc/gitconfig`) で GCM を利用可能に設定
5. **クレデンシャルストア設定（任意）**: バックエンド（`secretservice`, `cache`, `gpg`, `plaintext` 等）の指定に対応

## 要件

- 対象 OS: Ubuntu / Debian 系
- コントローラー: Ansible 2.12 以上

## ロール変数 (`defaults/main.yml`)

| 変数名 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `git_credential_manager_version` | `"2.9.1"` | インストールする GCM のバージョン |
| `git_credential_manager_configure_system` | `true` | システム全体（`--system`）に `git-credential-manager configure` を実行するかどうか |
| `git_credential_manager_credential_store` | `""` | クレデンシャルストアのバックエンド（例: `secretservice`, `cache`, `plaintext` など。空文字の場合は設定しない） |
| `git_credential_manager_arch` | 自動判定 | 対象ホストのアーキテクチャ（`x64` または `arm64`） |
| `git_credential_manager_deb_url` | GitHub Release URL | .deb パッケージのダウンロード URL |

## 使用例

### 基本的な使用方法

```yaml
- hosts: all
  become: false
  roles:
    - git_credential_manager
```

### バージョンやクレデンシャルストアを指定する場合

```yaml
- hosts: all
  become: false
  roles:
    - role: git_credential_manager
      vars:
        git_credential_manager_version: "2.9.1"
        git_credential_manager_credential_store: "secretservice"
```

## 動作確認

インストール後、各ノードで以下のコマンドを実行してバージョンと設定を確認できます：

```bash
git-credential-manager --version
git config --system --get-all credential.helper
```
