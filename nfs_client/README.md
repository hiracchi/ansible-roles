# `nfs_client` ロール

Ubuntu / Debian 系ホスト向けに NFS クライアントパッケージ（`nfs-common`）を導入し、NFS 共有ストレージのマウントポイント作成、`/etc/fstab` 登録、マウント実行（または `systemd.automount` によるオートマウント構成）を安全に行う Ansible ロールです。

---

## 🌟 特徴

* **複数マウント対応:** `nfs_client_mounts` リストで複数の NFS 共有を一度に一括定義可能。
* **マウントポイント自動作成:** 指定したローカルパスが存在しない場合、パーミッション `0755` で自動生成。
* **`systemd.automount` 安全対応:** `opts` に `noauto` が指定されている場合は稼働中プロセスの強制アンマウント（`busy` エラー）を回避し、`/etc/fstab` 更新と `systemctl daemon-reload` を安全に実施。
* **柔軟なソース指定:** `src: "server:/export/path"` または `server` + `remote_path` の両方の記法に対応し、変数定義を自動バリデーション。

---

## 🔧 変数一覧 (`defaults/main.yml`)

| 変数名 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `nfs_client_mounts` | `[]` | マウント設定のリスト（詳細は下記） |
| `nfs_client_package` | `"nfs-common"` | インストールする NFS クライアントパッケージ |
| `nfs_client_default_opts` | `"defaults,_netdev"` | オプション未指定時のデフォルトマウントオプション |
| `nfs_client_default_fstype` | `"nfs"` | ファイルシステム種別 |

### `nfs_client_mounts` の要素仕様

* `src` (string): NFS ソース文字列（例: `server:/export/path`）
* `server` (string): サーバ名（`remote_path` と併用）
* `remote_path` (string): リモートエクスポートパス（`server` と併用）
* `mount_point` (string): ローカルのマウント先（**必須**）
* `fstype` (string): ファイルシステム種別（省略時: `nfs`）
* `opts` (string): マウントオプション（省略時: `defaults,_netdev`）
* `state` (string): `mounted`, `present`, `absent` 等（省略時: `noauto` 指定時は `present`、通常は `mounted`）
* `create_mountpoint` (bool): マウント先ディレクトリを自動作成するか（デフォルト: `true`）

---

## 📖 使用例

### 1. 通常のマウント設定
```yaml
- hosts: all
  roles:
    - role: nfs_client
      vars:
        nfs_client_mounts:
          - src: "nas01.example.com:/volume1/data"
            mount_point: "/mnt/data"
            opts: "rw,hard,intr,nfsvers=4"
```

### 2. 高速・高耐障害な `systemd.automount` オートマウント設定（推奨）
```yaml
- hosts: all
  roles:
    - role: nfs_client
      vars:
        nfs_client_mounts:
          - src: "nas01.example.com:/volume1/home"
            mount_point: "/mnt/home"
            opts: "rw,_netdev,noauto,x-systemd.automount,x-systemd.idle-timeout=300,x-systemd.mount-timeout=15,nfsvers=4,proto=tcp,hard,timeo=600,retrans=3,rsize=1048576,wsize=1048576,noatime"
```

---

## 📄 ライセンス

MIT-0 / BSD
