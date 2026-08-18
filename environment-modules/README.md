# environment_modules Role

Environment Modules (Tcl版) をシステムにインストールし、共通のモジュールファイルディレクトリを確保する汎用ロールです。
他のロール（例：`nvidia_cuda` 等）で `module load` を用いた動的な環境変数切り替えを使用する前に実行するか、依存関係として設定します。

## 特徴

- **Debian/Ubuntu ファミリー対応**: OSファミリを確認するアサーションを含みます。
- **モジュールディレクトリの自動構成**: 各種ツールやライブラリのモジュールファイルを配置するベースディレクトリをパーミッション `0755` で作成します。
- **ログイン時自動ロード**: `environment-modules` のインストールにより、シェルログイン時に自動で `module` コマンドがインポートされます。

## ロール変数

`defaults/main.yml` で定義されている変数です。

| 変数名 | デフォルト値 | 説明 |
|---|---|---|
| `environment_modules_enabled` | `true` | ロール全体の有効・無効フラグ |
| `environment_modules_dir` | `"/usr/share/modules/modulefiles"` | 各種ツール等のモジュールファイル（Tcl）を配置するベースディレクトリの絶対パス |

## 使用例

### 単体での利用例

```yaml
- name: Setup HPC Environment Modules
  hosts: all
  roles:
    - role: environment_modules
```

### 他のロールへの依存関係設定例

`meta/main.yml` で依存関係を定義することで、当ロールが自動的に先に実行されます。

```yaml
# 依存する側のロール (例: roles/some_app/meta/main.yml)
---
dependencies:
  - role: environment_modules
    vars:
      environment_modules_dir: "/usr/share/modules/modulefiles"
```
