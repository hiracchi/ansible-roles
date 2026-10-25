# system.users

make users

## example

```
vars:
  - system_users_list:
    - user: someone
      group: somegroup
      groups: somegroup,adm,sudo
      password: hogehoge
      uid: 10000
      createhome: yes
```

## how to make password string

```
# for SHA512
python3 -c "import crypt; print(crypt.crypt('password','\$6\$salt\$'))"
```

