# hosts

setup /etc/hosts and /etc/hosts.\*


# variables

## hosts_table

```
vars:
  hosts_table:
    - hostname: sample01.localdomain
      ipv4_address: 192.168.0.1
      alias: sample01
```


## hosts_allow_table

list for hosts.allow

```
vars:
  hosts_allow_table:
    daemon_list: ALL
    host_list: ALL
```

## hosts_deny_table

list for hosts.deny

```
vars:
  hosts_deny_table:
    - daemon_list: sshd
      host_list: ALL
```

