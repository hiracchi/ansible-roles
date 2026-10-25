.PHONY: install ci lint

install:
	mise install

lint:
	mise exec -- yamllint .
	mise exec -- ansible-lint

ci: install
	mise exec -- ./scripts/ci.sh
