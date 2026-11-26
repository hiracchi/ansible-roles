# litellm_proxy

[LiteLLM Proxy](https://github.com/BerriAI/litellm) を、Docker の Compose(LiteLLM と PostgreSQL)で動かすロールです。
OpenAI 互換と Anthropic 互換の API の前段に置いて、人ごとの API キー、利用量の記録、上限(予算、1 分あたりの回数、同時実行数)を管理します。

## 仕組み

- `/opt/litellm-proxy`(`litellm_proxy_dir`)に、`docker-compose.yml`、`config.yaml`、`.env`(`0600`)を置き、
  systemd の `litellm-proxy.service` が `docker compose up -d` で起動します。
- 転送先(`litellm_proxy_models`)に、同じ `model_name` を複数並べると、`litellm_proxy_routing_strategy`(既定は `least-busy`)で振り分けます。
- 既定では、プロンプトと応答の中身は保存せず、利用量(人、日時、モデル、トークン数)だけを PostgreSQL に記録します。
- 自前のモデルには単価がなく、利用額が 0 のままで予算の上限が効かないので、仮の単価
  (`litellm_proxy_input_cost_per_token`、`litellm_proxy_output_cost_per_token`)を決めると、予算がトークン数の上限として働きます。
  (`0.000001` なら、予算 1 が 100 万トークン)

## 前提

- Docker と Docker Compose(`docker compose`)が入っていること(`docker` ロールなど)。
- 転送先のホストに、コンテナから届くこと(コンテナの DNS は `/etc/hosts` を見ないので、`api_base` には IP アドレスを書く)。

## 主な変数

| 変数                                     | 既定値                              | 説明                                                                         |
| :--------------------------------------- | :---------------------------------- | :--------------------------------------------------------------------------- |
| `litellm_proxy_state`                    | `present`                           | `absent` でコンテナと設定を削除する                                          |
| `litellm_proxy_remove_data`              | `false`                             | `absent` のとき、PostgreSQL のデータ(キーと利用量)も削除する                 |
| `litellm_proxy_image`                    | `ghcr.io/berriai/litellm:main-stable` | 再現したいときは、タグを版(例: `v1.111.0`)に固定する                         |
| `litellm_proxy_bind` / `_port`           | `0.0.0.0` / `4000`                  | 待ち受け。リバースプロキシを前に置くなら `127.0.0.1`                         |
| `litellm_proxy_master_key`               | `""`                                | 管理者のキー(必須。`sk-` で始まる文字列。Vault で暗号化する)                 |
| `litellm_proxy_salt_key`                 | `""`                                | 保存した認証情報の暗号化に使う(必須)。後から変えると、保存済みの値が読めない |
| `litellm_proxy_db_password`              | `""`                                | PostgreSQL のパスワード(必須)                                                |
| `litellm_proxy_models`                   | `[]`                                | 転送先の一覧(必須)。`model_name`、`api_base`、`api_key`、`max_parallel_requests` |
| `litellm_proxy_routing_strategy`         | `least-busy`                        | 振り分けの方式                                                               |
| `litellm_proxy_store_prompts`            | `false`                             | `true` でプロンプトと応答の中身も保存する                                    |

## 使い方

```yaml
- name: Setup LiteLLM proxy
  hosts: proxy_host
  roles:
    - role: litellm_proxy
      vars:
        litellm_proxy_master_key: "{{ vault_master_key }}"
        litellm_proxy_salt_key: "{{ vault_salt_key }}"
        litellm_proxy_db_password: "{{ vault_db_password }}"
        litellm_proxy_input_cost_per_token: 0.000001
        litellm_proxy_output_cost_per_token: 0.000001
        litellm_proxy_models:
          - model_name: my-model
            api_base: http://10.0.0.1:8095/v1
            api_key: "{{ vault_backend_key }}"
            max_parallel_requests: 1
```

キーの発行と失効は、管理者のキーで、LiteLLM の API(`/key/generate` など)を呼びます。

## 注意

- **起動に 10 分ほどかかります**(初回と、再起動のたび。データベースの移行の確認のため)。設定を変えて再適用すると、再起動が走ります。
- `litellm_proxy_salt_key` を変えないこと。変えると、保存した値が読めなくなります。
- 管理者のキーを、コマンドラインに直接書かないこと(`ps` に出ます)。
