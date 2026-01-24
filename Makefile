.PHONY: add commit push secret-key fernet-key app-up app-down app-clean lint clear clear-ruff clear-pytest clear-pycache  ingestion-init  ingestion-up  ingestion-up-flower  ingestion-down  ingestion-restart  ingestion-clean  ingestion-reset  ingestion-health  ingestion-scale-workers

add:
	git add .

commit: add
	git commit -m "$(msg)"

push: commit
	git push

app-up:
	docker compose -f application-docker-compose.yaml down -v || true
	docker compose -f application-docker-compose.yaml up --build

app-down:
	docker compose -f application-docker-compose.yaml down -v || true

app-clean: app-down
	docker system prune -af --volumes
	docker image prune -af
	docker volume prune -af

lint:
	python3 -m ruff format .
	python3 -m ruff check .

clear-pycache:
	find . -type d -name '__pycache__' -exec rm -rf {} +

clear-ruff: clear-pycache
	find . -type d -name '.ruff_cache' -exec rm -rf {} +

clear-pytest: clear-ruff
	find . -type d -name '.pytest_cache' -exec rm -rf {} +

clear: clear-pytest
	clear

secret-key:
	python -c "import secrets; print(secrets.token_hex(32))"

fernet-key:
	python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

 ingestion-init:
	mkdir -p ./ingestion/dags ./ingestion/logs ./ingestion/plugins ./ingestion/config
	docker compose -f  ingestion-docker-compose.yaml up  airflow-init

 ingestion-up:  ingestion-init
	docker compose -f  ingestion-docker-compose.yaml up -d

 ingestion-up-flower:  ingestion-init
	docker compose -f  ingestion-docker-compose.yaml --profile flower up -d

 ingestion-down:
	docker compose -f  ingestion-docker-compose.yaml down

 ingestion-restart:  ingestion-down  ingestion-up

 ingestion-clean:
	docker compose -f  ingestion-docker-compose.yaml down -v --remove-orphans
	rm -rf ./ingestion/logs/*
	docker system prune -af --volumes
	docker image prune -af
	docker volume prune -af

 ingestion-reset:  ingestion-clean  ingestion-init  ingestion-up

 ingestion-health:
	docker compose -f  ingestion-docker-compose.yaml ps
	docker compose -f  ingestion-docker-compose.yaml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

 ingestion-scale-workers:
	docker compose -f  ingestion-docker-compose.yaml up -d --scale  ingestion-worker=$(n)