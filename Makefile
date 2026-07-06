.PHONY: dev lint format test build download run clean

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

run:
	@if [ ! -d "upstream/jetbrainsmono" ] || [ ! -d "upstream/pretendard" ]; then \
		echo "Upstream font resources not found. Downloading..."; \
		$(MAKE) download; \
	fi
	uv run jetendard

clean:
	rm -rf fonts/ttf fonts/otf fonts/webfont fonts/specimens
