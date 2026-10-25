# ansible-roles

## usage
Link this directory to `~/.ansible/roles` before using:

```
$ ln -s `pwd` ~/.ansible/roles
```

or check Environment Variable; ANSIBLE_ROLES_PATH


## develop a new role

```
ansible-galaxy init  new_role
```


## naming convention

新規ロールを追加する際は、単語の区切りに **アンダースコア (`_`)** を使用してください（例: `nfs_client`, `apache2_mod_php`）。

- [ansible-lint の `role-name` ルール](https://docs.ansible.com/projects/lint/rules/role-name/) により、ロール名は小文字の英数字とアンダースコアのみで構成する必要があります（ハイフンやドットは不可）。
- ロール名は先頭を英字にする必要があります。

現状、全ロール（`_unsupported/` 含む）がアンダースコア区切りに統一済みです。新規ロールは必ずアンダースコア区切りにしてください。

### 変数名の規則

- 変数名は小文字の英数字とアンダースコアのみで構成し、先頭は英字にしてください（大文字・ハイフンは不可）。
- 変数名はロール名を接頭辞にしてください（例: `hw_hdd_spindown_uuid`、`move_dir_src`）。他ロールと衝突する汎用的な名前（`ntp_servers`、`limits` など）は避けてください。
- 同じ系統のロール群が接頭辞を共有するのは構いません（例: `slurm_server` と `slurm_client` は `slurm_` を使う）。

### 変数名の変更について（2026-10）

2026-10 に、上記の変数名の規則に従い、以下の変数名を変更しました。

| ロール | 旧名 | 新名 |
|---|---|---|
| `apache2` | `apache2_ServerAdmin` / `apache2_DocumentRoot` | `apache2_server_admin` / `apache2_document_root` |
| `systemd_timesyncd` | `NTP_SERVER` | `systemd_timesyncd_ntp_server` |
| `samba` | `smaba_users`（参照は `samba.users`） | `samba_users` |
| `nis_client` | `nis_servers` | `nis_client_servers` |
| `nis_server` | `nis_servers` | `nis_server_servers` |
| `opencl_nv` | `cuda_version` / `nvidia_driver_version` | `opencl_nv_cuda_version` / `opencl_nv_driver_version` |
| `opencl_nv_ppa` | `cuda_version` / `nvidia_driver_version` | `opencl_nv_ppa_cuda_version` / `opencl_nv_ppa_driver_version` |
| `hw_hdd_spindown` | `spindown_uuid` | `hw_hdd_spindown_uuid` |
| `move_dir` | `movedir_src` / `movedir_dest` | `move_dir_src` / `move_dir_dest` |
| `apt_mirror_client` | `my_apt_server` | `apt_mirror_client_server` |
| `cuda_toolkit` | `disable_graphical` | `cuda_toolkit_disable_graphical` |
| `locale` | `generate_locales` | `locale_generate_list` |
| `ubuntu_base` | `ntp_servers` / `ntp_server` / `limits` | `ubuntu_base_ntp_servers` / `ubuntu_base_ntp_server` / `ubuntu_base_limits` |
| `hardware_raspi` | `sys`（`sys.locale` などの辞書） | `hardware_raspi_sys` |
| `system_users`、`add_users` | `my_users` | `system_users_list` |
| `system_groups`、`add_groups` | `my_groups` | `system_groups_list` |

**移行が必要な場合**

- 上の表の旧名を変数として指定している playbook（`vars:`、`group_vars`、`host_vars`、`-e` オプションなど）は、新しい名前に直してください。
- 旧名のまま指定しても、エラーにならずに無視される場合があります。その場合、そのロールは既定値で動きます。
- `samba` では、既定の `samba_users` を空リストにしました。以前の既定値にあった固定パスワードのユーザーは作られなくなります。必要な場合は `samba_users` をホストごとに指定してください。

### ⚠️ ロール名の一括リネームについて

2026-08 に、上記の命名規則に従い、`_unsupported/` 含む全ロールをハイフン/ドット区切りからアンダースコア区切りに一括リネームしました（例: `nfs-client` → `nfs_client`, `system.users` → `system_users`, `proxmox_pci_passthrough` → `proxmox_gpu`, `_unsupported/docker-compose` → `_unsupported/docker_compose`）。

**このリポジトリを `~/.ansible/roles` にリンクして利用している外部の playbook リポジトリがある場合、以下の対応が必要です。**

- playbook 内の `roles:` / `role:` / `include_role` / `import_role` で旧ロール名（ハイフン・ドット区切り）を参照している箇所を、新しいアンダースコア区切りの名前に修正してください。
- 旧ロール名での参照はディレクトリが存在しないためエラーになります。
- ロール内部の変数名（例: `node_exporter_version` 等）やパッケージ名・サービス名（例: `apt-mirror`, `qemu-guest-agent`）は変更していないため、ロール変数の上書き等は引き続き同じ名前で利用できます（2026-10 に変更した変数名は下記の表を参照）。

対象ロール一覧（旧名 → 新名）は Git のコミット履歴（リネームコミット）を参照してください。

2026-10 には、残っていたハイフン区切りのロール名も変更しました。

- `gh-cli` → `gh_cli`
- `plg-monitoring` → `plg_monitoring`

これらを参照している playbook は、新しい名前に直してください。配置先のパス（例: `/opt/plg-monitoring`）と、GitHub のリポジトリ名（`docker-plg-monitoring`）は変更していません。


## check

未検証/動作要確認のロール一覧です。

- autofs
- docker
- _unsupported/docker_compose
- hw_r8168
- hostname
- hosts
- hw_hdd_spindown
- locale
- nis_client
- nis_server
- show_variables
- samba
- system_groups
- system_users
- timezone
- tmpreaper



