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

### ⚠️ ロール名の一括リネームについて

2026-08 に、上記の命名規則に従い、`_unsupported/` 含む全ロールをハイフン/ドット区切りからアンダースコア区切りに一括リネームしました（例: `nfs-client` → `nfs_client`, `system.users` → `system_users`, `proxmox_pci_passthrough` → `proxmox_gpu`, `_unsupported/docker-compose` → `_unsupported/docker_compose`）。

**このリポジトリを `~/.ansible/roles` にリンクして利用している外部の playbook リポジトリがある場合、以下の対応が必要です。**

- playbook 内の `roles:` / `role:` / `include_role` / `import_role` で旧ロール名（ハイフン・ドット区切り）を参照している箇所を、新しいアンダースコア区切りの名前に修正してください。
- 旧ロール名での参照はディレクトリが存在しないためエラーになります。
- ロール内部の変数名（例: `node_exporter_version` 等）やパッケージ名・サービス名（例: `apt-mirror`, `qemu-guest-agent`）は変更していないため、ロール変数の上書き等は引き続き同じ名前で利用できます。

対象ロール一覧（旧名 → 新名）は Git のコミット履歴（リネームコミット）を参照してください。


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



