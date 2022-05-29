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
  nis_servers:
    - localhost
  nis_securenets_netmask: 255.255.255.0
  nis_securenets_network: 192.168.0.0
```


# remarks

- NIS server must be an NIS client.

