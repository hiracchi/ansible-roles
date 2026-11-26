# strata_service

[Strata](https://github.com/Niko1221/Strata)(GPU 1 枚と RAM で大きな MoE モデルを動かす LLM サーバー)の Docker イメージを、
Apptainer で、Slurm のジョブとして各計算ノードに 1 つずつ常駐させるロールです。
OpenAI 互換の API(`http://<ノード>:<strata_port>/v1`)と Anthropic 互換の API(`/v1/messages`)を提供します。

## 仕組み

- **イメージ**: 本家の Docker イメージ(`ghcr.io/niko1221/strata:<版>-<flavor>`)を `apptainer pull` で SIF にして、
  共有ディレクトリ(`strata_image_dir`)に置きます。OS には何も入れないので、削除はファイルを消すだけです。
- **ジョブ**: ノードごとに 1 つのジョブ(`<strata_job_name_prefix>-<ノード>`)で `apptainer run --nv --containall` を起動します。
  API が応答したら `strata_state_dir/prepared` を置きます。
- **設定と状態はローカルディスク**: Strata が `/data` に書く設定と状態は、各ノードのローカル(`strata_local_dir`)に置きます。
  NFS に置くと、状態確認が失敗して起動の約 30 秒後に自分で終了したり、起動し直しが OSError で失敗したりします。
  モデルなどの重いデータ(`Strata-data`)だけを、共有ディレクトリのノードごとのディレクトリに置きます。
- **`--containall`**: コンテナの主プロセスが終わると、中のサーバーも一緒に終わります(付けないと、`scancel` してもサーバーが残ります)。
- **再投入**: コントローラの systemd のタイマー(`strata-resubmit.timer`)が、ジョブが無いノードに投入し直します。
  `strata_autosubmit: false` にすると、タイマーを停止・無効化します(手動で `strata-resubmit.sh` を実行する)。
  `prepared` が無い間(初回の準備中)は、先頭のノードだけを投入します。

## 前提

- 適用先は Slurm のコントローラ(`sbatch` を実行できるホスト)。
- `strata_base_dir` 以下は、コントローラと計算ノードから同じパスで見える共有ディレクトリ(NFS など)。
- 計算ノードに apptainer と NVIDIA のドライバー(580 以上、CUDA 13 の flavor の場合)があること。
- Strata は RAM に置くエキスパートを `mlock` で固定するため、ジョブのメモリロックの上限を無制限にしておくこと
  (`slurm_server` / `slurm_client` ロールの `slurm_propagate_resource_limits_except: "MEMLOCK"` など)。

## 主な変数

| 変数                               | 既定値                | 説明                                                                                       |
| :--------------------------------- | :-------------------- | :----------------------------------------------------------------------------------------- |
| `strata_state`                     | `present`             | `absent` でタイマー、ジョブ、スクリプト、イメージ、各ノードのローカルの状態を削除する      |
| `strata_remove_data`               | `false`               | `absent` のとき、モデルの変換データ(`strata_data_dir`)も削除する                           |
| `strata_version` / `strata_flavor` | `0.2.20` / `cuda13`   | Docker イメージのタグは `<版>-<flavor>`                                                    |
| `strata_nodes`                     | `[]`                  | Strata を動かす計算ノード(必須)                                                            |
| `strata_user` / `strata_group`     | `""`                  | ジョブを実行するユーザー(必須)                                                             |
| `strata_base_dir`                  | `/opt/strata`         | イメージ、データ、スクリプトの置き場所(共有ディレクトリ)                                   |
| `strata_local_dir`                 | `/var/lib/strata`     | 設定と状態の置き場所(各ノードのローカルディスク。NFS にしない)                             |
| `strata_models_dir`                | `""`                  | 取得済みの GGUF などのディレクトリ(読み取り専用で使う)。空ならダウンロードする            |
| `strata_family` / `strata_model`   | `qwen` / `IQ3_XXS`    | モデル                                                                                     |
| `strata_context` / `strata_vision` | `32k` / `off`         | コンテキストの長さ、画像入力(`off` / `on` / `gpu` / `cpu`)                                 |
| `strata_port`                      | `8080`                | API のポート(Apptainer はホストと同じネットワークを使う)                                   |
| `strata_api_key`                   | `""`                  | API キー(必須。Vault で暗号化する)                                                         |
| `strata_context_by_node`           | `{}`                  | ノードごとにコンテキストを変える(例: `{ node-02: 128k }`)。無いノードは `strata_context`    |
| `strata_extra_env`                 | `{}`                  | 追加で渡す環境変数(例: `{ STRATA_SET: "prefill=65536" }`)                                  |
| `strata_autosubmit`                | `true`                | `false` で再投入タイマーを停止・無効化する                                                 |
| `strata_slurm_partition` ほか      |                       | ジョブのパーティション、GRES、CPU 数、メモリ、時間                                         |

## 使い方

```yaml
- name: Setup Strata
  hosts: slurm_controller
  roles:
    - role: strata_service
      vars:
        strata_nodes: [node-01, node-02]
        strata_user: alice
        strata_base_dir: /mnt/nfs/strata
        strata_api_key: "{{ vault_strata_api_key }}"
        strata_slurm_partition: llm
```

削除するときは `strata_state: absent` を指定して、もう一度適用します。

## API キー

`strata_api_key` の値は、このロールが `<strata_secrets_dir>/api.key`(`0600`、ディレクトリは `0700`、`strata_user` の所有)に平文で置きます。

- ジョブスクリプトは `api.key` を読み、環境変数 `APPTAINERENV_API_KEY`(コンテナの中では `API_KEY`)で Strata に渡します。
  コマンドラインには出ないので、ほかのユーザーには `ps` で見えません。調査などで、キーをコマンドラインに書かないこと。
- Strata 自身が、`<strata_local_dir>/state/api-key` に平文のコピー(`600`)を保存します。起動ログにはキーの先頭 10 文字が出ます。
- **キーを変えたら、ジョブの再起動が必要です。** 再適用すると `api.key` は書き換わりますが、動いているサーバーは古いキーのままです。
  各ノードのジョブを `scancel -n <ジョブ名>` で 1 つずつ止めて、`strata-resubmit.sh` で起動し直すと、新しいキーで起動します。
  ノードの `state/api-key` に残った古いキーは、消してください。
- `strata_state: absent` は `api.key` と、各ノードの `strata_local_dir` を削除します。

## 注意

- Strata の Docker イメージは、Docker で動かす前提です(起動スクリプトが 10 秒ごとに状態を確認し、3 回続けて失敗すると、コンテナを終了します)。
  Apptainer では、状態の保存先が NFS だと、この確認が失敗します。
- 版を上げると新しいイメージを取得しますが、動いているジョブは古いイメージのままです。
  `scancel` でジョブを止めて、起動し直すと、新しいイメージで起動します。古いイメージは残るので、不要なら消してください。
- 2 回目以降の起動では、共有ディレクトリから RAM にエキスパートを読み込みます(数十 GB)。
  共有ディレクトリが遅いと、起動に数分かかります。
