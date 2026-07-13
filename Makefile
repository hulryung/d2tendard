.PHONY: dev lint format test build download ensure-upstream run run-all run-minimal clean

dev:
	uv sync --all-groups

lint:
	uv run ruff format --check .
	uv run ruff check .

format:
	uv run ruff format .

test:
	uv run pytest

build:
	uv build

download:
	uv run python download_upstream.py

ensure-upstream:
	@if [ ! -d "upstream/jetbrainsmono" ] || [ ! -d "upstream/pretendard" ]; then \
		echo "Upstream font resources not found. Downloading..."; \
		$(MAKE) download; \
	fi

run: ensure-upstream
	uv run d2tendard --all

run-all: ensure-upstream
	uv run d2tendard --all

run-minimal: ensure-upstream
	uv run d2tendard --variants Regular Light Bold

clean:
	rm -rf fonts/ttf fonts/otf fonts/webfont fonts/specimens
