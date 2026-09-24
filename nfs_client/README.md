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

#### 💡 推奨マウントオプションの解説

上記の設定は、**「オンデマンド自動マウントによる起動時・停止時の安定性」**、**「10GbE等の高速環境向けスループット最適化」**、**「データ保護」** を両立させた推奨パラメータです。

| オプション | 分類 | 役割・設定理由 |
| :--- | :--- | :--- |
| **`rw`** | 基本動作 | 読み書き両用（Read-Write）でマウントします。 |
| **`noatime`** | 性能向上 | 読み出し時にアクセス日時（atime）の更新を行わず、不要なメタデータ書き込みを削減して I/O パフォーマンスを向上させます。 |
| **`_netdev`** | 起動制御 | ネットワークを必要とするファイルシステムであることを明示し、ネットワーク未確立時のマウント失敗やシャットダウン時の切断順序問題を防止します。 |
| **`noauto`** | 起動制御 | 起動時の一括自動マウント（`mount -a`）を行わず、systemd のオンデマンドマウントに任せます。 |
| **`x-systemd.automount`** | 自動マウント | マウントポイントへアクセスが発生した初回に自動マウントします。サーバー起動時に NFS サーバーが停止していても起動プロセスがハングしません。 |
| **`x-systemd.idle-timeout=300`** | 自動マウント | 300秒（5分間）無アクセスが続いた場合、自動でアンマウントしてリソースや不要なセッションを解放します。 |
| **`x-systemd.mount-timeout=15`** | 自動マウント | マウント試行のタイムアウトを 15秒 に制限し、NFS サーバー無応答時のプロセスハングを防ぎます。 |
| **`nfsvers=4`** | プロトコル | NFS バージョン 4 を使用します。 |
| **`proto=tcp`** | プロトコル | 転送プロトコルに TCP を使用し、パケット損失時の信頼性を確保します。 |
| **`hard`** | 耐障害性 | サーバー無応答時に途中で I/O エラーを返さず復旧まで再試行し、データ破損を防ぎます（データ保護最優先）。 |
| **`timeo=600`** | 耐障害性 | 応答がない場合の再送タイムアウト時間（600デシ秒 = 60秒）。 |
| **`retrans=3`** | 耐障害性 | タイムアウト後の再試行回数（3回）。 |
| **`rsize=1048576`** | 転送性能 | 読み込み最大バッファサイズ（1 MiB）。大容量ファイルの連続転送性能を最大化します。 |
| **`wsize=1048576`** | 転送性能 | 書き込み最大バッファサイズ（1 MiB）。大容量ファイルの書き込み性能を最大化します。 |

---

## 📄 ライセンス

MIT-0 / BSD
