# xestrata_service

[XeStrata](https://github.com/MistVVK/XeStrata)(GPU 1 枚と RAM で大きな MoE モデルを動かす LLM サーバー)を、
Apptainer のイメージに入れて、Slurm のジョブとして各計算ノードで 1 つずつ常駐させるロールです。
OpenAI 互換の API(`http://<ノード>:<xestrata_port>/v1`)と Anthropic 互換の API(`/v1/messages`)を提供します。

## 仕組み

- **イメージ**: 公式の deb(SHA256 で照合)と cuBLAS を入れた Apptainer のイメージを、`xestrata_build_host` でビルドし、
  共有ディレクトリ(`xestrata_image_dir`)に置きます。OS には何も入れないので、削除はファイルを消すだけです。
- **ジョブ**: ノードごとに 1 つのジョブ(`<xestrata_job_name_prefix>-<ノード>`)で `xestrata --yes` を起動します。
  初回はモデルのダウンロードと準備のあとにサーバーを起動し、2 回目からは起動だけを行います。
  API が応答したら `xestrata_state_dir/prepared` を置きます。
- **再投入**: コントローラの systemd のタイマー(`xestrata-resubmit.timer`)が、ジョブが無いノードに投入し直します。
  `prepared` が無い間(初回の準備中)は、先頭のノードだけを投入します。共有のデータを 2 台で同時に準備しないためです。

## 前提

- 適用先は Slurm のコントローラ(`sbatch` を実行できるホスト)。
- `xestrata_base_dir` 以下は、コントローラと計算ノードから同じパスで見える共有ディレクトリ(NFS など)。
- 計算ノードに apptainer と NVIDIA のドライバーがあること。
- XeStrata は RAM に置くエキスパートを `mlock` で固定するため、ジョブのメモリロックの上限を無制限にしておくこと
  (`slurm_server` / `slurm_client` ロールの `slurm_propagate_resource_limits_except: "MEMLOCK"` など)。

## 主な変数

| 変数 | 既定値 | 説明 |
| :--- | :--- | :--- |
| `xestrata_state` | `present` | `absent` でタイマー、ジョブ、スクリプト、イメージを削除する |
| `xestrata_remove_data` | `false` | `absent` のとき、モデルのデータも削除する |
| `xestrata_version` | `0.2.2-1` | XeStrata のリリース。変えたら `xestrata_deb_sha256` も合わせる |
| `xestrata_nodes` | `[]` | XeStrata を動かす計算ノード(必須) |
| `xestrata_user` / `xestrata_group` | `""` | ジョブを実行するユーザー(必須)。モデルの設定はこのユーザーの `~/.config/xestrata` に置かれる |
| `xestrata_base_dir` | `/opt/xestrata` | イメージ、データ、スクリプトの置き場所(共有ディレクトリ) |
| `xestrata_host` / `xestrata_port` | `0.0.0.0` / `8095` | API の公開先 |
| `xestrata_api_key` | `""` | API キー。127.0.0.1 以外に公開するときは必須(Vault で暗号化する) |
| `xestrata_extra_args` | `[]` | `xestrata` に追加で渡すオプション(例: `["--context", "65536"]`) |
| `xestrata_slurm_partition` ほか | | ジョブのパーティション、GRES、CPU 数、メモリ、時間 |

## 使い方

```yaml
- name: Setup XeStrata
  hosts: slurm_controller
  roles:
    - role: xestrata_service
      vars:
        xestrata_nodes: [node-01, node-02]
        xestrata_user: alice
        xestrata_base_dir: /mnt/nfs/xestrata
        xestrata_api_key: "{{ vault_xestrata_api_key }}"
        xestrata_slurm_partition: llm
```

削除するときは `xestrata_state: absent` を指定して、もう一度適用します。

## 注意

- API キーは `xestrata` のコマンドラインで渡すため、ジョブが動いている計算ノードでは `ps` で見えます。
  計算ノードを XeStrata のジョブが占有する運用を前提にしています。
- 版を上げると新しいイメージをビルドしますが、動いているジョブは古いイメージのままです。
  `scancel` でジョブを止めると、タイマーが新しいイメージで投入し直します。古いイメージは残るので、不要なら消してください。
- 2 回目以降の起動では、共有ディレクトリから RAM にエキスパートを読み込みます(数十 GB)。
  共有ディレクトリが遅いと、起動に数分かかります。
