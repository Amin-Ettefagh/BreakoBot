.PHONY: install lint format test run docker-up docker-logs

install:
	python -m pip install -r requirements.txt

lint:
	ruff check .

format:
	ruff format .

test:
	pytest

run:
	python -m app.main

docker-up:
	docker compose up -d --build

docker-logs:
	docker compose logs -f bot
