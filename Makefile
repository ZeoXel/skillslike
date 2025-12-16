# Makefile for SkillsLike

.PHONY: help install test lint format clean run

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make run        - Run the API server"

install:
	uv sync

test:
	uv run pytest tests/ -v --cov=skillslike --cov-report=term-missing

lint:
	uv run ruff check .
	uv run mypy skillslike/

format:
	uv run ruff format .
	uv run ruff check --fix .

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:
	uv run uvicorn skillslike.api.main:app --reload --host 0.0.0.0 --port 8000

dev:
	uv run uvicorn skillslike.api.main:app --reload
