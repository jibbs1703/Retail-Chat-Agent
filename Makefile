.PHONY: add commit push start-qdrant start-backend start-app clean-app clear-pycache clear-ruff clear-pytest

add:
	git add .

commit: add
	git commit -m "$(msg)"

push: commit
	git push

start-qdrant:
	cd qdrant
	docker build -t qdrant-custom:latest .
	docker run -d --name custom-qdrant-container -p 6333:6333 -p 6334:6334 -v qdrant_data:/qdrant/storage qdrant-custom:latest

start-backend:
	cd backend
	docker build -t retail-chat-agent:latest .
	docker run -p 8000:8000 retail-chat-agent:latest

start-app:
	docker compose down -v || true
	docker compose up --build

clean-app:
	docker compose down -v || true
	docker system prune -af --volumes
	docker image prune -af
	docker volume prune -af

clear-pycache:
	find . -type d -name '__pycache__' -exec rm -rf {} +

clear-ruff: clear-pycache
	find . -type d -name '.ruff_cache' -exec rm -rf {} +

clear-pytest: clear-ruff
	find . -type d -name '.pytest_cache' -exec rm -rf {} +

clear: clear-pytest
	clear
