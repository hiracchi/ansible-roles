#!/bin/bash

# 指定した Slurm ノードを DOWN/DRAIN 状態から resume (IDLE) に戻すスクリプト
# slurmctld が動いているホスト (jarvis-01) で実行する。
# 予期しない再起動などで DOWN になったノードは、管理者が resume するまで戻らない。
# 例: sudo slurm-resume-node jarvis-x3-01
# 例: sudo slurm-resume-node jarvis-x3-01 jarvis-x3-02

if [ $# -eq 0 ]; then
    echo "Usage: $0 <nodename> [<nodename> ...]"
    echo "  e.g. $0 jarvis-x3-01"
    exit 1
fi

if ! command -v scontrol >/dev/null 2>&1; then
    echo "Error: scontrol が見つかりません (slurmctld のホストで実行してください)"
    exit 1
fi

status=0
for node in "$@"; do
    echo "== ${node}: 実行前の状態"
    sinfo -N -n "${node}" -o "%N %T %E" 2>&1 | tail -n +2 | sed 's/^/   /'

    if scontrol update nodename="${node}" state=resume; then
        echo "== ${node}: resume を要求しました"
    else
        echo "== ${node}: resume に失敗しました (権限またはノード名を確認してください)"
        status=1
        continue
    fi

    echo "== ${node}: 実行後の状態"
    sinfo -N -n "${node}" -o "%N %T %E" 2>&1 | tail -n +2 | sed 's/^/   /'
done
exit $status
