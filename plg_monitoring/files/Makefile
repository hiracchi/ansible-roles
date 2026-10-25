.PHONY: start stop restart status logs clean help

export UID := $(shell id -u)
export GID := $(shell id -g)

## start: Docker Compose スタックをバックグラウンドで起動します
start:
	UID=$(UID) GID=$(GID) docker compose up -d

## stop: Docker Compose スタックを停止します
stop:
	UID=$(UID) GID=$(GID) docker compose stop

## restart: Docker Compose スタックを再起動します
restart:
	UID=$(UID) GID=$(GID) docker compose restart

## status: コンテナのステータスを確認します
status:
	UID=$(UID) GID=$(GID) docker compose ps

## logs: コンテナのログをリアルタイムで表示します
logs:
	UID=$(UID) GID=$(GID) docker compose logs -f

## clean: コンテナを停止・削除し、設定を残したまま生データ（./data）を削除します
clean:
	UID=$(UID) GID=$(GID) docker compose down
	rm -rf data
	mkdir -p data

## help: 利用可能なコマンド一覧を表示します
help:
	@echo "利用可能な Make ターゲット:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

