# rtx1200_backup

Yamaha RTX1200 の `show config` を読み取り専用で取得し、ansible を実行したマシンに保存します。
ルーターの設定は変更しません。

## 前提

- 実行するマシンに `sshpass` が入っていること(`sudo apt install -y sshpass`)
- RTX1200 で SSH を有効にし、ユーザー(`ansible_user`)でログインできること
- 接続情報は `ansible-vault` で暗号化して、ansible-jarvis の `host_vars/jarvis-rtx1200.yml` に置くこと
  (`ansible_user`、暗号化した `ansible_password`、`ansible_ssh_common_args` の互換オプション)

## 仕組み

- `yamaha_network.rtx` コレクションと `network_cli` は使いません(RTX1200 は公式の対応機種外のため)。
- 実行マシンから `sshpass` 経由で SSH ログインし、対話シェルで `show config` を送って結果を受け取ります。
- 設定の内容は表示も記録もしません(タスクは `no_log`)。

## 変数

| 変数 | 既定値 | 説明 |
|---|---|---|
| `rtx_backup_dir` | `~/rtx-backups` | 保存先。ディレクトリは 0700、ファイルは 0600 |
| `rtx_target_host` | `jarvis-rtx1200` | 接続情報を読む inventory のホスト名 |

## 実行

```
cd ~/work/dev/ansible-jarvis
.venv/bin/ansible-playbook rtx_backup.yml --vault-password-file ./.vault_password
```

## 保存されるファイル

`<保存先>/<RTX の IP>-<YYYYmmdd-HHMMSS>.cfg`

## 注意

- 設定にはパスワードなどの秘密が含まれます。保存先をリポジトリに入れないでください。
- 取得に失敗した場合(応答が短い、エラー応答)は保存しません。
- 接続先は inventory の `ansible_host`(10.71.99.1)です。
