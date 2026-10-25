# description

setup NIS server


# variables

```
vars:
  nis_task: "master"
  nis_initialize: false
  nis_merge_passwd: true
  nis_merge_group: true

  nis_domainname: local
  nis_server_servers:
    - localhost
  nis_securenets_netmask: 255.255.255.0
  nis_securenets_network: 192.168.0.0
```


## users and groups (optional)

NIS accounts can be created on the master with `nis_groups` / `nis_users`.

```
vars:
  nis_groups:
    lab:
      gid: 10100

  nis_users:
    alice:
      uid: 10101
      group: lab
      groups: "sudo"          # optional
      home: /home/alice
      shell: /bin/bash        # optional (default: /bin/bash)
      createhome: true        # optional (default: false)
      ssh_keys:               # optional, list of public keys for authorized_keys
        - "ssh-ed25519 AAAA... alice@laptop"
      password: !vault |      # optional, plain text (use ansible-vault encrypt_string)
        ...
      update_password: true   # optional, update the password on every run
```

- Only UID/GID >= 1000 are exported to NIS (`MINUID` / `MINGID` in `/var/yp/Makefile`).
- `ssh_keys` requires the `ansible.posix` collection and an existing home directory
  (`createhome: true`, or the home provided by NFS).
- When users or groups are changed, the NIS maps are rebuilt (`make -C /var/yp`).
  This is skipped until the maps have been created (see `nis_initialize`).


# remarks

- NIS server must be an NIS client.
- `nis_initialize: true` runs `ypinit -m` non-interactively (stdin from `/dev/null`) after the
  users and groups are created, only when no NIS map exists yet. It is `false` by default;
  in that case run `sudo /usr/lib/yp/ypinit -m` once by hand on the master.

