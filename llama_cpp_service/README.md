# `llama_cpp_service` ロール

2台の GPU 計算ノード（`asuka-z4-[01-02]`）上で `llama.cpp` の分散 RPC 機能を利用し、**Qwen3-Coder-30B-A3B-Instruct** などの大型 MoE モデルをパイプライン並列で常駐実行・管理する Ansible ロールです。

---

## 🌟 特徴

* **2台の GPU による分散パイプライン並列**:
  * ワーカーノードで `rpc-server`（ポート 50052）を起動
  * マスターノードで `llama-server`（ポート 8080）を起動し、ノード間でレイヤーを自動分割・協調推論
* **2.5Gbps イーサネット最適化**:
  * レイヤー境界のアクティベーションのみを送受信するため、一般的なイーサネット環境でも高速に動作
* **Slurm プリエンプション完全統合**:
  * 低優先度パーティション（`llm`）で 2 ノードを常時確保
  * 高優先度の GPU バッチジョブが投入された際は自動で一時退避（REQUEUE）し、バッチ完了後に自動復帰
* **OpenAI 互換 API**:
  * `http://asuka-z4-01:8080/v1` で OpenAI 互換エンドポイントを提供し、Aider や Continue.dev から直接利用可能

---

## 🔧 変数一覧 (`defaults/main.yml`)

| 変数名 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `llama_cpp_nfs_base_dir` | `/mnt/nfs1/llama_cpp` | 共有 NFS ベースディレクトリ |
| `llama_cpp_models_dir` | `{{ llama_cpp_nfs_base_dir }}/models` | GGUF モデル保存先 |
| `llama_cpp_sif_path` | `{{ llama_cpp_nfs_base_dir }}/sif/llama-cpp-cuda.sif` | Apptainer SIF パス |
| `llama_cpp_model_filename` | `Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf` | 使用するモデルファイル名 |
| `llama_cpp_model_url` | Hugging Face URL | モデルのダウンロード元 URL |
| `llama_cpp_api_port` | `8080` | OpenAI 互換 API ポート |
| `llama_cpp_rpc_port` | `50052` | ノード間 RPC 通信ポート |
| `llama_cpp_nodes` | `2` | 確保するノード数 |
| `llama_cpp_partition` | `llm` | 実行パーティション |
