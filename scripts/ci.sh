#!/usr/bin/env bash
# ローカル CI: YAML 構文 → ansible-lint → 各ロールのテスト playbook の構文チェック
# 事前に `mise install` でツールを入れておくこと（make ci から呼ばれる想定）。
set -euo pipefail

cd "$(dirname "$0")/.."
export ANSIBLE_ROLES_PATH="${PWD}:${PWD}/_unsupported"
export ANSIBLE_NOCOWS=1

echo "==> yamllint"
yamllint .

echo "==> ansible-lint"
ansible-lint

echo "==> syntax-check (tests/test.yml)"
status=0
for play in */tests/test.yml _unsupported/*/tests/test.yml; do
  [ -f "$play" ] || continue
  dir="$(dirname "$(dirname "$play")")"
  echo "--- ${dir}"
  if ! ansible-playbook -i "${dir}/tests/inventory" --syntax-check "$play"; then
    status=1
  fi
done

if [ "$status" -ne 0 ]; then
  echo "CI FAILED: syntax-check" >&2
  exit 1
fi
echo "CI OK"
