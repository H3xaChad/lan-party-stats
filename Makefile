.PHONY: help install run clean check web

help:
	@echo "make install        Install dependencies"
	@echo "make run            Run the Discord bot"
	@echo "make web            Run the web interface"

install:
	uv sync --extra web

run:
	uv run python main.py

web:
	uv run python web_main.py