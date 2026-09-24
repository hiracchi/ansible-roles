# `aider` ロール

Ubuntu / Debian 系ホスト向けに Aider (AI Pair Programming CLI) を専用仮想環境（`/opt/aider`）に導入し、システム全体（`/usr/local/bin/aider`）から利用可能にする Ansible ロールです。

---

## 🌟 特徴

* **クリーンな仮想環境**: OS のシステム Python 環境を汚さず、`uv tool` により隔離された Python 3.12 環境（`/opt/aider`）内に完全カプセル化して導入。
* **全ユーザー共通利用**: `/usr/local/bin/aider` にバイナリを配置し、全ユーザーから追加 PATH なしで `aider` コマンドが実行可能。
* **ローカル LLM (Ollama) 自動連携**: `/etc/profile.d/aider.sh` により、ログイン時にデフォルトでクラスタ内の Ollama API エンドポイント（`OLLAMA_API_BASE`）およびモデル（`AIDER_MODEL`）を環境変数に自動設定。

---

## 🔧 変数一覧 (`defaults/main.yml`)

| 変数名 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `aider_venv_dir` | `/opt/aider` | Aider 専用仮想環境の作成先パス |
| `aider_bin_link` | `/usr/local/bin/aider` | コマンドの配置先パス |
| `aider_pip_packages` | `["aider-chat"]` | インストールする pip パッケージ |
| `aider_ollama_api_base` | `"http://asuka-z4-01:11434"` | `OLLAMA_API_BASE` に設定する Ollama 接続 URL |
| `aider_model` | `"ollama/qwen2.5-coder:7b"` | `AIDER_MODEL` に設定するデフォルト LLM モデル |
| `aider_setup_profile` | `true` | `/etc/profile.d/aider.sh` を配備するか |

---

## 📖 使用例

```yaml
- name: Setup Aider CLI
  hosts: slurm_controller
  become: true
  roles:
    - role: aider
      vars:
        aider_ollama_api_base: "http://asuka-z4-01:11434"
        aider_model: "ollama/qwen2.5-coder:7b"
```
