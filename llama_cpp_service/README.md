# `llama_cpp_service` ロール

2台の GPU 計算ノード（`asuka-z4-[01-02]`）上で `llama.cpp` の分散 RPC 機能を利用し、**Qwen3-Coder-30B-A3B-Instruct** などの大型 MoE モデルをパイプライン並列で常駐実行・管理する Ansible ロールです。

---

## 🌟 特徴と実績

* **2台の GPU による分散パイプライン並列 (RPC)**:
  * **Master (`asuka-z4-01`)**: `llama-server`（ポート 8080）を起動
  * **Worker (`asuka-z4-02`)**: `ggml-rpc-server`（ポート 50052）を起動
  * 18.6GB の GGUF モデルを 2台の RTX 5070（各 12GB VRAM）に約 10.4GB / 11.0GB ずつ自動分割オフロード。
* **驚異的な推論速度 (MoE × パイプライン並列)**:
  * Qwen3-Coder-30B-A3B（総パラメータ 30.5B / 活性化 3.3B）において、2.5Gbps イーサネット環境下でも **約 176 tokens/sec** の高速生成を達成。
* **Slurm プリエンプション完全統合**:
  * 低優先度パーティション（`llm`）で 2 ノードを常時確保。
  * 高優先度の GPU バッチジョブが投入された際は自動で一時退避（REQUEUE）し、バッチ完了後にコントローラの systemd タイマー（`llama-cpp-resubmit.timer`）が自動再投入して常駐復帰。
* **ネイティブ CUDA 13.4 最適化**:
  * 公式リリースバイナリを共有 NFS（`/mnt/nfs1/llama_cpp/bin`）に配備し、コンテナオーバーヘッドなしで最高性能を発揮。
* **OpenAI 互換 API**:
  * `http://asuka-z4-01:8080/v1` でエンドポイントを提供し、Aider や Continue 等のコーディングエージェントから即座に利用可能。

---

## 🔧 変数一覧 (`defaults/main.yml`)

| 変数名 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `llama_cpp_nfs_base_dir` | `/mnt/nfs1/llama_cpp` | 共有 NFS ベースディレクトリ |
| `llama_cpp_bin_dir` | `{{ llama_cpp_nfs_base_dir }}/bin` | llama.cpp バイナリ配置先 |
| `llama_cpp_models_dir` | `{{ llama_cpp_nfs_base_dir }}/models` | GGUF モデル保存先 |
| `llama_cpp_version` | `b11193` | 使用する公式リリースバージョン |
| `llama_cpp_model_filename` | `Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf` | 使用するモデルファイル名 |
| `llama_cpp_model_url` | Hugging Face URL | モデルの自動ダウンロード元 URL |
| `llama_cpp_model_alias` | `qwen3-coder` | API エンドポイントで公開するモデルエイリアス |
| `llama_cpp_context_size` | `32768` | コンテキスト長（KV キャッシュサイズ） |
| `llama_cpp_api_port` | `8080` | OpenAI 互換 API ポート |
| `llama_cpp_rpc_port` | `50052` | ノード間 RPC 通信ポート |
| `llama_cpp_nodes` | `2` | 確保するノード数 |
| `llama_cpp_partition` | `llm` | 実行する Slurm パーティション |
| `llama_cpp_cluster_command_name` | `llm-cluster` | コントローラに配備する管理コマンド名 |
| `llama_cpp_cluster_nodes` | `""` | 対象 Slurm ノード名（例: `node-[01-02]`） |
| `llama_cpp_cluster_ssh_nodes` | `[]` | シャットダウン対象ホスト名リスト（SSH 用） |

---

## 🔄 モデルの変更・追加手順

### 方法 1: Ansible で恒久的に変更する（推奨）

IaC として構成を維持し、モデルの自動ダウンロードからジョブ更新まで一括で行う方法です。

1. **設定変数を変更**:
   `ansible-roles/llama_cpp_service/defaults/main.yml`（または各インベントリの `group_vars`）を編集します。
   ```yaml
   llama_cpp_model_filename: "新しいモデル名.gguf"
   llama_cpp_model_url: "https://huggingface.co/.../resolve/main/新しいモデル名.gguf"
   llama_cpp_model_alias: "my-model"       # API / Aider で指定する名前
   llama_cpp_context_size: 32768           # 必要に応じてコンテキスト長を調整
   ```

2. **Ansible Playbook を実行**:
   ```bash
   cd setup-asuka/ansible-asuka
   ./exec.sh slurm_cluster -t llama_cpp
   ```
   * 共有 NFS（`/mnt/nfs1/llama_cpp/models/`）へ自動ダウンロードされます。
   * ジョブスクリプトが新しいモデル指定で再生成されます。

3. **クラスタを再起動**:
   ```bash
   scancel -n llama-cpp-cluster
   ```
   * コントローラの常駐タイマー（`llama-cpp-resubmit.timer`）が数分以内に新設定でクラスタを自動起動します。
   * すぐに起動したい場合はコントローラで `/opt/llama_cpp/llama-cpp-resubmit.sh` を手動実行してください。

---

### 方法 2: 手動で即座に試す

Hugging Face 等から直接ダウンロードして素早く切り替える方法です。

1. **共有 NFS にモデルを配置**:
   ```bash
   cd /mnt/nfs1/llama_cpp/models
   wget -c "https://huggingface.co/.../resolve/main/xxx.gguf"
   ```
   * 共有 NFS に配置するため、Worker ノードへの個別コピーは不要です。

2. **ジョブスクリプトを編集**:
   コントローラの `/opt/llama_cpp/llama-cpp-cluster.sh` 内の `-m`（モデルパス）および `--alias`（エイリアス）を書き換えます。

3. **クラスタを再起動**:
   ```bash
   scancel -n llama-cpp-cluster
   /opt/llama_cpp/llama-cpp-resubmit.sh
   ```

---

## 💡 2台 RTX 5070（計 24GB VRAM）でのモデル選定ガイド

パイプライン並列により、**2ノード合計で約 21〜22GB までのモデル** を GPU フルオフロードで稼働できます。

| モデル種別 | 推奨モデル例 | ファイルサイズ | 特徴 |
| :--- | :--- | :--- | :--- |
| **MoE (現在構成)** | `Qwen3-Coder-30B-A3B-Instruct` (Q4_K_M) | 約 18.6 GB | **超高速（170+ tokens/sec）**、高いコード推論力 |
| **Dense 14B / 16B** | `Qwen2.5-Coder-14B-Instruct` (Q8_0 / Q4) | 約 9〜15 GB | 安定したコード生成、速度は 40〜60 tokens/sec 前後 |
| **軽量 MoE** | `DeepSeek-Coder-V2-Lite-Instruct` (Q4_K_M) | 約 10 GB | コード・数学に強く省メモリ |

---

## 💻 クライアント（Aider）からの利用

### 1. デフォルト利用
`/etc/profile.d/aider.sh` にクラスタの接続先が設定されているため、そのまま起動するだけで利用可能です。

```bash
aider
```

### 2. モデルエイリアスを指定して起動
異なるモデルエイリアスに接続したい場合は `--model` を指定します。

```bash
aider --model openai/qwen3-coder
```

---

## 🛠️ 運用・確認コマンド

* **Slurm ジョブ状態確認**:
  ```bash
  squeue
  ```
* **推論サーバーログ確認**:
  ```bash
  tail -f /var/log/llama_cpp/llama_cluster_<JOBID>.out
  tail -f /var/log/llama_cpp/llama_cluster_<JOBID>.err
  ```
* **両ノードの VRAM 使用率確認**:
  ```bash
  ssh asuka-z4-01 nvidia-smi
  ssh asuka-z4-02 nvidia-smi
  ```
* **API 疎通テスト**:
  ```bash
  curl -s http://asuka-z4-01:8080/v1/models | jq .
  ```

---

## ⏹️ 計算ノードの停止・メンテナンスと復帰手順

本ロールでは、コントローラノードにクラスタ管理コマンド（デフォルト: **`llm-cluster`**、変数 `llama_cpp_cluster_command_name` でカスタマイズ可能）を配備します。これを使用して 1 コマンドで安全に停止・再開・状態確認が可能です。

### 1. 停止手順（シャットダウン・メンテナンス）

```bash
# パターン A: ジョブを停止し、ノードを Drain（保守）状態にする
sudo llm-cluster stop

# パターン B: ジョブ停止・Drain に加え、対象計算ノードの電源オフまで実行
sudo llm-cluster stop --shutdown
```

* 内部で `llama-cpp-resubmit.timer` を停止した上でジョブをキャンセルするため、ジョブが勝手に再投入されるのを確実に防ぎます。

---

### 2. 復帰手順（起動・サービス再開）

ノードの電源を投入した後、以下のコマンドを実行します：

```bash
# ノードの Drain 解除、タイマー開始、ジョブの即時再投入を一括実行
sudo llm-cluster start
```

---

### 3. クラスタ状態の確認

```bash
# Slurm ジョブ、タイマー稼働状態、ノード状態を一括表示
llm-cluster status
```
