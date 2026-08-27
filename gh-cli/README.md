# gh-cli

Ubuntu/Debian 系ホスト向けに [GitHub CLI (`gh`)](https://cli.github.com/) を公式 APT リポジトリからインストールする Ansible ロール。

## 概要

このロールは以下を行います：

1. 前提パッケージ (`curl`, `gnupg`, `ca-certificates`) をインストール
2. GitHub CLI 公式 GPG キーを `/etc/apt/keyrings/githubcli-archive-keyring.gpg` に配置
3. GitHub CLI 公式 APT リポジトリ (`https://cli.github.com/packages`) を追加
4. `gh` パッケージをインストール

## 要件

- Ubuntu/Debian 系ホスト
- Ansible 2.12 以上

## ロール変数

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `gh_cli_state` | `"present"` | `gh` パッケージの状態 (`present` または `latest`) |

## 使用例

### Playbook での使用

```yaml
- hosts: all
  become: false
  roles:
    - gh-cli
```

### 常に最新版にアップグレードしたい場合

```yaml
- hosts: all
  become: false
  roles:
    - role: gh-cli
      vars:
        gh_cli_state: latest
```

## ファイル配置

| パス | 内容 |
|------|------|
| `/etc/apt/keyrings/githubcli-archive-keyring.gpg` | GitHub CLI 公式 GPG キーリング |
| `/etc/apt/sources.list.d/github-cli.list` | GitHub CLI APT リポジトリ定義 |

## 動作確認

```bash
gh --version
```

## ライセンス

MIT
